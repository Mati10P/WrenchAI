from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

Name = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)
]
Description = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=10000)
]


class Schema(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class VehicleInput(Schema):
    name: Name
    make: (
        Annotated[
            str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)
        ]
        | None
    ) = None
    model: (
        Annotated[
            str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)
        ]
        | None
    ) = None
    year: Annotated[int, Field(strict=True, ge=1886, le=2100)] | None = None
    fuel: (
        Annotated[
            str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)
        ]
        | None
    ) = None
    engine_code: (
        Annotated[
            str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)
        ]
        | None
    ) = None
    market: (
        Annotated[
            str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)
        ]
        | None
    ) = None
    notes: Description | None = None
    mileage: Annotated[int, Field(strict=True, ge=0, le=10000000)] | None = None
    modifications: Description | None = None


class VehicleOut(VehicleInput):
    id: UUID
    created_at: datetime


class Status(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"


class IncidentInput(Schema):
    title: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)
    ]
    description: Description
    symptoms: Annotated[list[Name], Field(max_length=30)] = Field(default_factory=list)
    mileage: Annotated[int, Field(strict=True, ge=0, le=10000000)] | None = None


class IncidentUpdate(IncidentInput):
    status: Status
    resolution: Description | None = None

    @model_validator(mode="after")
    def resolution_matches_status(self):
        if (self.status == Status.RESOLVED) != (self.resolution is not None):
            raise ValueError(
                "RESOLVED requires a resolution; other states must not have one"
            )
        return self


class MeasurementInput(Schema):
    name: Name
    value: Annotated[
        Decimal, Field(max_digits=14, decimal_places=4, allow_inf_nan=False)
    ]
    unit: Annotated[
        str, StringConstraints(strip_whitespace=True, min_length=1, max_length=30)
    ]
    conditions: Description | None = None


class MeasurementOut(MeasurementInput):
    id: UUID
    incident_id: UUID
    observed_at: datetime


class IncidentOut(IncidentInput):
    id: UUID
    vehicle_id: UUID
    status: Status
    resolution: str | None
    created_at: datetime
    resolved_at: datetime | None


class IncidentDetail(IncidentOut):
    measurements: list[MeasurementOut]


class MessageInput(Schema):
    id: UUID
    content: Description


class MessageOut(MessageInput):
    incident_id: UUID
    created_at: datetime


class WorkInput(Schema):
    description: Description
