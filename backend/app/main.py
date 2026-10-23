from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import Depends, FastAPI, HTTPException, Query, Response
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from .database import database_url, session_factory
from .models import Incident, Measurement, Vehicle
from .schemas import (
    IncidentDetail,
    IncidentInput,
    IncidentOut,
    IncidentUpdate,
    MeasurementInput,
    MeasurementOut,
    Status,
    VehicleInput,
    VehicleOut,
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
        if payload.status == Status.RESOLVED and obj.resolved_at is None:
            obj.resolved_at = datetime.now(timezone.utc)
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

    return app


app = create_app()
