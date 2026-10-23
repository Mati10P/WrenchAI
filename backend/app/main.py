from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from .database import database_url, session_factory
from .models import Incident, Measurement, Message, Vehicle
from .schemas import (
    IncidentDetail,
    IncidentInput,
    IncidentOut,
    IncidentUpdate,
    MeasurementInput,
    MeasurementOut,
    MessageInput,
    MessageOut,
    Status,
    TaskInput,
    TaskState,
    VehicleInput,
    VehicleOut,
    WorkInput,
)


def create_app(url=None):
    @asynccontextmanager
    async def lifespan(app):
        engine, factory = session_factory(url or database_url())
        app.state.session_factory = factory
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(title="WrenchAI", version="0.1.0", lifespan=lifespan)

    def session():
        with app.state.session_factory() as db:
            yield db

    DB = Annotated[Session, Depends(session)]
    Limit = Annotated[int, Query(ge=1, le=100)]
    Offset = Annotated[int, Query(ge=0)]

    def get(db, model, identifier):
        obj = db.get(model, identifier)
        if obj is None:
            raise HTTPException(404, "Resource not found")
        return obj

    def save(db):
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            raise HTTPException(
                409, "Operation conflicts with existing records"
            ) from None

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/ready")
    def ready(db: DB):
        try:
            db.execute(text("SELECT id FROM vehicles LIMIT 0"))
        except SQLAlchemyError:
            raise HTTPException(
                503, "Database unavailable or migrations pending"
            ) from None
        return {"status": "ready"}

    @app.post("/vehicles", response_model=VehicleOut, status_code=201)
    def create_vehicle(payload: VehicleInput, db: DB):
        obj = Vehicle(**payload.model_dump())
        db.add(obj)
        save(db)
        return obj

    @app.get("/vehicles", response_model=list[VehicleOut])
    def vehicles(db: DB, limit: Limit = 50, offset: Offset = 0):
        return db.scalars(
            select(Vehicle)
            .order_by(Vehicle.created_at, Vehicle.id)
            .limit(limit)
            .offset(offset)
        ).all()

    @app.get("/vehicles/{vehicle_id}", response_model=VehicleOut)
    def vehicle(vehicle_id: UUID, db: DB):
        return get(db, Vehicle, vehicle_id)

    @app.put("/vehicles/{vehicle_id}", response_model=VehicleOut)
    def update_vehicle(vehicle_id: UUID, payload: VehicleInput, db: DB):
        obj = get(db, Vehicle, vehicle_id)
        for key, value in payload.model_dump().items():
            setattr(obj, key, value)
        save(db)
        return obj

    @app.delete("/vehicles/{vehicle_id}", status_code=204)
    def delete_vehicle(vehicle_id: UUID, db: DB):
        db.delete(get(db, Vehicle, vehicle_id))
        save(db)
        return Response(status_code=204)

    @app.post(
        "/vehicles/{vehicle_id}/incidents", response_model=IncidentOut, status_code=201
    )
    def create_incident(vehicle_id: UUID, payload: IncidentInput, db: DB):
        get(db, Vehicle, vehicle_id)
        obj = Incident(vehicle_id=vehicle_id, **payload.model_dump())
        db.add(obj)
        save(db)
        return obj

    @app.get("/vehicles/{vehicle_id}/incidents", response_model=list[IncidentOut])
    def incidents(
        vehicle_id: UUID,
        db: DB,
        status: Status | None = None,
        limit: Limit = 50,
        offset: Offset = 0,
    ):
        get(db, Vehicle, vehicle_id)
        query = select(Incident).where(Incident.vehicle_id == vehicle_id)
        if status:
            query = query.where(Incident.status == status.value)
        return db.scalars(
            query.order_by(Incident.created_at.desc(), Incident.id)
            .limit(limit)
            .offset(offset)
        ).all()

    @app.get("/incidents/{incident_id}", response_model=IncidentDetail)
    def incident(incident_id: UUID, db: DB):
        return get(db, Incident, incident_id)

    @app.put("/incidents/{incident_id}", response_model=IncidentOut)
    def update_incident(incident_id: UUID, payload: IncidentUpdate, db: DB):
        obj = get(db, Incident, incident_id)
        if obj.status == Status.RESOLVED.value and payload.status != Status.RESOLVED:
            raise HTTPException(
                409, "Resolved incidents cannot be reopened in this version"
            )
        for key, value in payload.model_dump(mode="python").items():
            setattr(obj, key, value.value if isinstance(value, Status) else value)
        if payload.status == Status.RESOLVED:
            obj.work_notes = payload.resolution
        if payload.status == Status.RESOLVED and obj.resolved_at is None:
            obj.resolved_at = datetime.now(UTC)
        save(db)
        return obj

    @app.delete("/incidents/{incident_id}", status_code=204)
    def delete_incident(incident_id: UUID, db: DB):
        db.delete(get(db, Incident, incident_id))
        save(db)
        return Response(status_code=204)

    @app.post(
        "/incidents/{incident_id}/measurements",
        response_model=MeasurementOut,
        status_code=201,
    )
    def add_measurement(incident_id: UUID, payload: MeasurementInput, db: DB):
        get(db, Incident, incident_id)
        obj = Measurement(incident_id=incident_id, **payload.model_dump())
        db.add(obj)
        save(db)
        return obj

    def existing_message(db, payload, vehicle_id=None, incident_id=None):
        message = db.get(Message, payload.id)
        if message is None:
            return None
        parent = get(db, Incident, message.incident_id)
        if (
            message.content != payload.content
            or (vehicle_id is not None and parent.vehicle_id != vehicle_id)
            or (incident_id is not None and parent.id != incident_id)
        ):
            raise HTTPException(
                409, "Message ID already used for different content or context"
            )
        return message

    def save_message(db, payload, **context):
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            # A concurrent retry may already have committed this exact message.
            existing = existing_message(db, payload, **context)
            if existing is not None:
                return existing
            raise HTTPException(409, "Message could not be saved") from None
        return db.get(Message, payload.id)

    @app.post(
        "/vehicles/{vehicle_id}/chats", response_model=MessageOut, status_code=201
    )
    def start_chat(vehicle_id: UUID, payload: MessageInput, db: DB):
        vehicle = get(db, Vehicle, vehicle_id)
        existing = existing_message(db, payload, vehicle_id=vehicle_id)
        if existing is not None:
            return existing
        incident = Incident(
            vehicle_id=vehicle_id,
            title=payload.content[:160],
            description=payload.content,
            mileage=vehicle.mileage,
        )
        db.add(incident)
        db.flush()
        db.add(Message(id=payload.id, incident_id=incident.id, content=payload.content))
        return save_message(db, payload, vehicle_id=vehicle_id)

    @app.post(
        "/incidents/{incident_id}/messages", response_model=MessageOut, status_code=201
    )
    def add_message(incident_id: UUID, payload: MessageInput, db: DB):
        get(db, Incident, incident_id)
        existing = existing_message(db, payload, incident_id=incident_id)
        if existing is not None:
            return existing
        db.add(Message(id=payload.id, incident_id=incident_id, content=payload.content))
        return save_message(db, payload, incident_id=incident_id)

    @app.get("/incidents/{incident_id}/messages", response_model=list[MessageOut])
    def messages(incident_id: UUID, db: DB, limit: Limit = 50, offset: Offset = 0):
        get(db, Incident, incident_id)
        return db.scalars(
            select(Message)
            .where(Message.incident_id == incident_id)
            .order_by(Message.created_at, Message.id)
            .limit(limit)
            .offset(offset)
        ).all()

    @app.post(
        "/vehicles/{vehicle_id}/work", response_model=IncidentOut, status_code=201
    )
    def record_work(vehicle_id: UUID, payload: WorkInput, db: DB):
        vehicle = get(db, Vehicle, vehicle_id)
        incident = Incident(
            vehicle_id=vehicle_id,
            title=payload.description[:160],
            description=payload.description,
            mileage=vehicle.mileage,
            status="RESOLVED",
            resolution=payload.description,
            work_notes=payload.description,
            resolved_at=datetime.now(UTC),
        )
        db.add(incident)
        save(db)
        return incident

    def apply_task_state(obj, completed):
        if completed:
            if not obj.work_notes:
                raise HTTPException(422, "Add work notes before completing this task")
            obj.status = "RESOLVED"
            obj.resolution = obj.work_notes
            obj.resolved_at = obj.resolved_at or datetime.now(UTC)
        else:
            # Keep previous work details when putting a task back on the list.
            obj.work_notes = obj.work_notes or obj.resolution
            obj.status = "OPEN"
            obj.resolution = None
            obj.resolved_at = None

    @app.post(
        "/vehicles/{vehicle_id}/tasks", response_model=IncidentOut, status_code=201
    )
    def create_task(vehicle_id: UUID, payload: TaskInput, db: DB):
        vehicle = get(db, Vehicle, vehicle_id)
        obj = Incident(
            vehicle_id=vehicle_id,
            mileage=vehicle.mileage,
            **payload.model_dump(exclude={"completed"}),
        )
        apply_task_state(obj, payload.completed)
        db.add(obj)
        save(db)
        return obj

    @app.put("/incidents/{incident_id}/task", response_model=IncidentOut)
    def edit_task(incident_id: UUID, payload: TaskInput, db: DB):
        obj = get(db, Incident, incident_id)
        for key, value in payload.model_dump(exclude={"completed"}).items():
            setattr(obj, key, value)
        apply_task_state(obj, payload.completed)
        save(db)
        return obj

    @app.patch("/incidents/{incident_id}/task-state", response_model=IncidentOut)
    def toggle_task(incident_id: UUID, payload: TaskState, db: DB):
        obj = get(db, Incident, incident_id)
        apply_task_state(obj, payload.completed)
        save(db)
        return obj

    return app


app = create_app()
