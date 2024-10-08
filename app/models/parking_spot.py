from sqlmodel import SQLModel, Field, Relationship
from typing import Any, Optional,List
from datetime import datetime, timezone

class ParkingSpot(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    slot: int = Field(..., ge=1, le=20)  
    status: str = Field(default="available")
    vehicles: List["VehicleRegistration"] = Relationship(back_populates="parking_spot")

class VehicleRegistration(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    vehicle_number: str = Field(..., unique=True)  
    entry_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    exit_time: Optional[datetime] = None 
    parking_spot_id: Optional[int] = Field(foreign_key="parkingspot.id")  
    parking_spot: Optional[ParkingSpot] = Relationship(back_populates="vehicles") 

class ParkingSpotResponse(SQLModel):
    id: Optional[int]
    slot: int
    status: str

class VehicleRegistrationResponse(SQLModel):
    id: Optional[int]
    vehicle_number: str
    exit_time: Optional[str]  
    parking_fee: Optional[int]  
    entry_time: Optional[str]
    parking_spot: Optional[ParkingSpotResponse]

class VehicleExitRequest(SQLModel):
    vehicle_number: str
class GenericResponse(SQLModel):
    message: Optional[str] = None
    data: Optional[Any] = None    