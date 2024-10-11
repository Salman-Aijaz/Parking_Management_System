from sqlmodel import SQLModel
from typing import Optional, Any

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
