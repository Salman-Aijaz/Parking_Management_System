from fastapi import APIRouter,Depends
from app.controllers.parking_controller import ParkingController,VehicleRegistrationController
from typing import List
from sqlmodel import Session
from app.database import get_db
from app.models.parking_models import ParkingSpot,VehicleRegistration
from app.schemas.parking_schemas import VehicleRegistrationResponse,GenericResponse,VehicleExitRequest


router = APIRouter()

@router.get("/")
def hello():
    return {"message": "Parking System Management"}

@router.get("/parking/", response_model=List[ParkingSpot])
def read_parking_spots(db:Session = Depends(get_db)):
    return ParkingController.read_parking_spots(db)

@router.post("/parking/", response_model=ParkingSpot)
def create_parking_spot(parking_spot: ParkingSpot,db:Session = Depends(get_db)):
    return ParkingController.create_parking_spot(parking_spot,db)



# VEHICLE REGISTRATION

@router.post("/vehicle-registration", response_model=VehicleRegistration)
def create_vehicle_registration(vehicle_registration: VehicleRegistration,db:Session = Depends(get_db)):
    return VehicleRegistrationController.create_vehicle_registration(vehicle_registration,db)

@router.get("/vehicle-registration", response_model=List[VehicleRegistrationResponse])
def get_vehicle_registrations(db:Session = Depends(get_db)):
    return VehicleRegistrationController.read_vehicle_registrations(db)

@router.post("/vehicle-exit", response_model=GenericResponse)
def post_vehicle_exit(request: VehicleExitRequest, db: Session = Depends(get_db), rate_per_hour: int = 50):
    vehicle_exit_response = VehicleRegistrationController.post_vehicle_exit(request.vehicle_number, db, rate_per_hour)
    return vehicle_exit_response

