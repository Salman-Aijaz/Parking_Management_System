import math
from datetime import datetime, timezone
from sqlmodel import Session, select
from fastapi import HTTPException,Depends
from app.models.parking_spot import ParkingSpot,VehicleRegistration,ParkingSpotResponse,VehicleRegistrationResponse
from app.database import get_db
from collections import deque
from sqlalchemy import text
from zoneinfo import ZoneInfo

PST = ZoneInfo('Asia/Karachi')

class ParkingController:
    @staticmethod
    def create_parking_spot(parking_spot: ParkingSpot,db:Session):
        try:
            if parking_spot.slot > 20:
                raise HTTPException(status_code=400, detail="Slot number cannot exceed 20.")
            
            if parking_spot.slot <1:
                raise HTTPException(status_code=400,detail="Slot value will not be in negative")

            query = text("SELECT id FROM parkingspot WHERE slot = :slot")
            existing_spot = db.execute(query, {'slot': parking_spot.slot}).fetchone()
            # existing_spot = db.exec(select(ParkingSpot).where(ParkingSpot.slot == parking_spot.slot)).first()
            if existing_spot:
                raise HTTPException(status_code=400,detail="Slot is already filled.")
            
            new_spot = ParkingSpot(slot=parking_spot.slot, status="available")
            db.add(new_spot)
            db.commit()
            db.refresh(new_spot)
            return new_spot
        
        # THIS EXCEPT BLOCK RERAISED HTTPException LIKE (Slot is already filled.) 
        except HTTPException as http_exc:
            raise http_exc
        
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"An error occured in creating parking spot:{e}")

    @staticmethod
    def read_parking_spots(db:Session):
        try:
            query = text("SELECT id,slot,status FROM parkingspot")
            parking_spots = db.execute(query).fetchall()
            # parking_spots = db.exec(select(ParkingSpot)).all()
            return parking_spots
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"An error occured in read_parking_spots:{e} ")
    
    
class VehicleRegistrationController:
    waiting_queue=deque()
    
    @staticmethod
    def create_vehicle_registration(vehicle_registration: VehicleRegistration,db:Session):
        try:
            # existing_vehicle = db.exec(
            # select(VehicleRegistration).where(VehicleRegistration.vehicle_number == vehicle_registration.vehicle_number)
            # ).first()
            query_vehicle = text("SELECT id FROM vehicleregistration WHERE vehicle_number = :vehicle_number")
            existing_vehicle = db.execute(query_vehicle, {"vehicle_number": vehicle_registration.vehicle_number}).fetchone()    
            if existing_vehicle:
                raise HTTPException(status_code=400, detail="Vehicle is already registered.")

            # available_spot = db.exec(
            # select(ParkingSpot).where(ParkingSpot.status == "available")
            # ).first()    
            
            query_spot = text("SELECT id,slot,status FROM parkingspot WHERE status = 'available' LIMIT 1")
            available_spot = db.execute(query_spot).fetchone()

            if not available_spot:
                VehicleRegistrationController.waiting_queue.append(vehicle_registration)
                raise HTTPException(status_code=400, detail="All slots are full. Your vehicle are added to the queue.")
            
            update_spot_status = text("UPDATE parkingspot SET status ='occupied' WHERE id = :spot_id")
            db.execute(update_spot_status,{"spot_id":available_spot.id})
            # available_spot.status="occupied"
            # vehicle_registration.parking_spot_id = available_spot.id

            query_insert_vehicle = text('''
            INSERT INTO vehicleregistration (vehicle_number,parking_spot_id,entry_time)
            VALUES (:vehicle_number,:parking_spot_id,:entry_time)
            RETURNING id    
                ''')
        
            vehicle_id = db.execute(query_insert_vehicle, {
                "vehicle_number": vehicle_registration.vehicle_number,
                "parking_spot_id": available_spot.id,
                "entry_time": vehicle_registration.entry_time
            }).fetchone()[0]    

            # db.add(vehicle_registration)
            db.commit()
            # db.refresh(vehicle_registration)
            # return vehicle_registration
            return {"id": vehicle_id, "vehicle_number": vehicle_registration.vehicle_number}
        
        
        except HTTPException as http_exc:
            raise http_exc
        
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"An error occured {e}")

    @staticmethod
    def read_vehicle_registrations(db:Session):
        try:
            # statement = select(VehicleRegistration, ParkingSpot).join(ParkingSpot, VehicleRegistration.parking_spot_id == ParkingSpot.id)
            # results = db.exec(statement).all()
            query = text("""
                SELECT 
                    v.id AS vehicle_id, v.vehicle_number, v.entry_time, v.exit_time, 
                    p.id AS spot_id, p.slot, p.status
                FROM 
                    vehicleregistration v
                JOIN 
                    parkingspot p 
                ON 
                    v.parking_spot_id = p.id
            """)
            results = db.execute(query).fetchall()

            parking_fee=50
            vehicle_registrations = []
            for row in results:
                vehicle_id = row.vehicle_id
                vehicle_number = row.vehicle_number
                entry_time = row.entry_time
                exit_time = row.exit_time
                spot_id = row.spot_id
                slot = row.slot
                spot_status = row.status
            
                if entry_time and exit_time:
                    duration = exit_time - entry_time
                    hours_parked = math.ceil(duration.total_seconds() // 3600)
                    parking_fee = int(hours_parked * 50)  

                formatted_entry_time = entry_time.strftime("%I:%M %p") if entry_time else None
                formatted_exit_time = exit_time.strftime("%I:%M %p")   if exit_time else None

                vehicle_registration = {
                    "id": vehicle_id,
                    "vehicle_number": vehicle_number,
                    "entry_time": formatted_entry_time,
                    "exit_time": formatted_exit_time,
                    "parking_fee": parking_fee,
                    "parking_spot": {
                        "id": spot_id,
                        "slot": slot,
                        "status": spot_status 
                    }
                }
                vehicle_registrations.append(vehicle_registration)

            return vehicle_registrations
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"An error occured {e}")

         
    @staticmethod
    def post_vehicle_exit(vehicle_number: str, db:Session,rate_per_hour: int = 50) -> VehicleRegistrationResponse:
        try:
            vehicle = db.exec(select(VehicleRegistration).where(VehicleRegistration.vehicle_number == vehicle_number)).first()

            if not vehicle:
                raise HTTPException(status_code=404, detail="Vehicle registration not found.")
            
            parking_spot = db.exec(select(ParkingSpot).where(ParkingSpot.id == vehicle.parking_spot_id)).first()
            print("PARKING SPOT------------------------>",parking_spot)

            if not parking_spot:
                raise HTTPException(status_code=404, detail="Parking spot does not exist.")    
            
            if parking_spot.status != "occupied":
                raise HTTPException(status_code=404, detail="Parking spot is not occupied or the status is incorrect.")

            vehicle.exit_time = datetime.now(timezone.utc)
            entry_time_aware = vehicle.entry_time if vehicle.entry_time.tzinfo else vehicle.entry_time.replace(tzinfo=timezone.utc)
            exit_time_aware = vehicle.exit_time
             
            if exit_time_aware and entry_time_aware:
                duration = exit_time_aware - entry_time_aware
                hours_parked = math.ceil(duration.total_seconds() // 3600)
                parking_fee = int(hours_parked * rate_per_hour)
            else:
                parking_fee = 50

            entry_time_pst = entry_time_aware.astimezone(PST) if vehicle.entry_time else None
            exit_time_pst = exit_time_aware.astimezone(PST) if vehicle.exit_time else None
            formatted_entry_time = entry_time_pst.strftime("%I:%M %p") if entry_time_pst else None
            formatted_exit_time = exit_time_pst.strftime("%I:%M %p") if exit_time_pst else None


            # parking_spot.status = "available"
            db.add(parking_spot)
            # db.delete(vehicle)
            db.commit()

            vehicle_response = VehicleRegistrationResponse(
                id=vehicle.id,
                vehicle_number=vehicle.vehicle_number,
                entry_time=formatted_entry_time,
                exit_time=formatted_exit_time,
                parking_fee=parking_fee,
                parking_spot=ParkingSpotResponse(
                    id=parking_spot.id,
                    slot=parking_spot.slot,
                    status=parking_spot.status
                )
            )

            return {
            "message": f"Vehicle registration in slot {parking_spot.slot} has been deleted.",
            "vehicle_details": vehicle_response
            }
        
        except HTTPException as http_exc:
            raise http_exc
        
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"An error occured {e}")

    
    @staticmethod
    def get_all_vehicle_records(db: Session):
        try:
            statement = select(VehicleRegistration, ParkingSpot).join(ParkingSpot, VehicleRegistration.parking_spot_id == ParkingSpot.id)
            results = db.exec(statement).all()

            vehicle_records = []

            for vehicle, spot in results:
                entry_time = vehicle.entry_time
                exit_time = vehicle.exit_time

                if vehicle.entry_time and exit_time:
                    duration = exit_time - vehicle.entry_time
                    hours_parked = math.ceil(duration.total_seconds() // 3600)
                    parking_fee = int(hours_parked * 50)
                else:
                    parking_fee = 50

                formatted_entry_time = entry_time.strftime("%I:%M %p") if entry_time else None
                formatted_exit_time = exit_time.strftime("%I:%M %p") if exit_time else None

                vehicle_record = {
                    "id": vehicle.id,
                    "vehicle_number": vehicle.vehicle_number,
                    "entry_time": formatted_entry_time,
                    "exit_time": formatted_exit_time,
                    "parking_fee": parking_fee,
                    "status": "exited" if exit_time else "parked",
                    "parking_spot": {
                        "id": spot.id,
                        "slot": spot.slot,
                        "status": spot.status
                    }
                }
                vehicle_records.append(vehicle_record)

            for vehicle in VehicleRegistrationController.waiting_queue:
                vehicle_record = {
                    "vehicle_number": vehicle.vehicle_number,
                    "status": "in queue",
                    "entry_time": None,
                    "exit_time": None,
                    "parking_spot": None,
                    "parking_fee": None
                }
                vehicle_records.append(vehicle_record)

            return vehicle_records  
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {e}")