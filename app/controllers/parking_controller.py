from datetime import datetime, timezone
from sqlmodel import Session
from fastapi import HTTPException
from sqlalchemy import text
from app.database import redis_client
from app.models.parking_models import ParkingSpot,VehicleRegistration
from app.schemas.parking_schemas import ParkingSpotResponse,VehicleRegistrationResponse,GenericResponse
from app.utils.calculation import calculate_parking_fee_and_time

class ParkingController:
    @staticmethod
    def create_parking_spot(parking_spot: ParkingSpot,db:Session):
        try:
            if parking_spot.slot > 20 or parking_spot.slot < 1:
                raise HTTPException(status_code=400, detail="Slot number must be between 1 and 20.")

            query = text("SELECT id FROM parkingspot WHERE slot = :slot")
            existing_spot = db.execute(query, {'slot': parking_spot.slot}).fetchone()

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
            raise HTTPException(status_code=500,detail=f"Internal server error while creating parking spot:{e}")

    @staticmethod
    def read_parking_spots(db:Session):
        try:
            query = text("SELECT id,slot,status FROM parkingspot")
            parking_spots = db.execute(query).fetchall()
            return parking_spots
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"An error occured in read_parking_spots:{e} ")
    
    
class VehicleRegistrationController:    
    @staticmethod
    def create_vehicle_registration(vehicle_registration: VehicleRegistration,db:Session):
        try:
            query_vehicle = text("SELECT id FROM vehicleregistration WHERE vehicle_number = :vehicle_number")
            existing_vehicle = db.execute(query_vehicle, {"vehicle_number": vehicle_registration.vehicle_number}).fetchone()    
            if existing_vehicle:
                raise HTTPException(status_code=400, detail="Vehicle is already registered.")
           
            query_spot = text("SELECT id, status FROM parkingspot WHERE id = :parking_spot_id")
            requested_spot = db.execute(query_spot, {"parking_spot_id": vehicle_registration.parking_spot_id}).fetchone()

            if not requested_spot:
                raise HTTPException(status_code=404, detail="Parking spot does not exist.")
            
            if requested_spot.status != "available":
                # If the requested spot is not available, add the vehicle to the Redis queue
                redis_client.rpush("vehicle_queue", vehicle_registration.vehicle_number)
                raise HTTPException(status_code=400, detail="Parking full. Your vehicle has been added to the queue.")
            
            update_spot_status = text("UPDATE parkingspot SET status ='occupied' WHERE id = :spot_id")
            db.execute(update_spot_status,{"spot_id":requested_spot.id})

            query_insert_vehicle = text('''
            INSERT INTO vehicleregistration (vehicle_number,parking_spot_id,entry_time)
            VALUES (:vehicle_number,:parking_spot_id,:entry_time)
            RETURNING id    
                ''')
        
            vehicle_id = db.execute(query_insert_vehicle, {
                "vehicle_number": vehicle_registration.vehicle_number,
                "parking_spot_id": requested_spot.id,
                "entry_time": vehicle_registration.entry_time
            }).fetchone()[0]    

            db.commit()
            return {"id": vehicle_id, "vehicle_number": vehicle_registration.vehicle_number}
        
        except HTTPException as http_exc:
            raise http_exc
        
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"Internal server error while registering vehicle: {e}")

    @staticmethod
    def read_vehicle_registrations(db:Session):
        try:
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

            vehicle_registrations = []
            for row in results:
                formatted_entry_time, formatted_exit_time, parking_fee = calculate_parking_fee_and_time(row.entry_time, row.exit_time)

                vehicle_registration = {
                    "id": row.vehicle_id,
                    "vehicle_number": row.vehicle_number,
                    "entry_time": formatted_entry_time,
                    "exit_time": formatted_exit_time,
                    "parking_fee": parking_fee,
                    "parking_spot": {
                        "id": row.spot_id,
                        "slot": row.slot,
                        "status": row.status 
                    }
                }
                vehicle_registrations.append(vehicle_registration)

            return vehicle_registrations
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"An error occured  in read_vehicle_registrations{e}")

         
    @staticmethod
    def post_vehicle_exit(vehicle_number: str, db:Session, rate_per_hour: int = 50) -> VehicleRegistrationResponse:
        try:
            query_vehicle = text("SELECT * FROM vehicleregistration WHERE vehicle_number = :vehicle_number")
            vehicle = db.execute(query_vehicle, {"vehicle_number": vehicle_number}).fetchone()

            if not vehicle:
                raise HTTPException(status_code=404, detail=f"Vehicle with number '{vehicle_number}' was not found in the system. Please check the vehicle number and try again.")
            
            query_parking_spot = text("SELECT * FROM parkingspot WHERE id = :parking_spot_id")
            parking_spot = db.execute(query_parking_spot, {"parking_spot_id": vehicle.parking_spot_id}).fetchone()
      
            if not parking_spot:
                raise HTTPException(status_code=404, detail=f"Parking spot with ID '{vehicle.parking_spot_id}' does not exist. Please contact support if this issue persists.")    
            
            if parking_spot.status != "occupied":
                raise HTTPException(status_code=404, detail=f"Parking spot {parking_spot.slot} is currently not occupied.")

            exit_time_aware = datetime.now(timezone.utc)
            formatted_entry_time, formatted_exit_time, parking_fee =  calculate_parking_fee_and_time(vehicle.entry_time,exit_time_aware)    

            update_vehicle_exit_time = text("UPDATE vehicleregistration SET exit_time = :exit_time WHERE id = :vehicle_id")
            db.execute(update_vehicle_exit_time, {"exit_time": exit_time_aware, "vehicle_id": vehicle.id})

            update_spot_status = text("UPDATE parkingspot SET status = 'available' WHERE id = :spot_id")
            db.execute(update_spot_status, {"spot_id": parking_spot.id})

            db.commit()

            # Check for vehicles in the queue
            next_vehicle = redis_client.lpop("vehicle_queue")
            if next_vehicle:
                next_vehicle_registration = VehicleRegistration(
                    vehicle_number=next_vehicle.decode('utf-8'),  # Decode from bytes
                    parking_spot_id=parking_spot.id,
                    entry_time=exit_time_aware
                )
                VehicleRegistrationController.create_vehicle_registration(next_vehicle_registration, db)

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


            return GenericResponse(
            message= f"Vehicle with number '{vehicle.vehicle_number}' has successfully exited from slot {parking_spot.slot}. The parking fee is {parking_fee} Rs.",
            data= vehicle_response
            )
        
        except HTTPException as http_exc:
            raise http_exc
        
        except Exception as e:
            raise HTTPException(status_code=500,detail=f"An error occured {e}")