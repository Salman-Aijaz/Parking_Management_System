from app.config import Config

def test_read_vehicle_registrations():
    # FETCH THE LIST OF VEHICLE REGISTRATIONS
    response = Config.client.get("/vehicle-registration")
    assert response.status_code == 200

    # CHECK THAT THE RESPONSE IS A LIST AND CONTAINS THE EXPECTED FIELDS
    data = response.json()
    assert isinstance(data, list)
    
    # VALIDATE THE FIRST REGISTRATION IN THE RESPONSE IF ANY EXIST
    if data:
        assert "id" in data[0]
        assert "vehicle_number" in data[0]
        assert "entry_time" in data[0]
        assert "exit_time" in data[0]  # IF VEHICLE IS PARKED SO IT IS NONE
        assert "parking_fee" in data[0]
        assert "parking_spot" in data[0]
        assert "id" in data[0]["parking_spot"]
        assert "slot" in data[0]["parking_spot"]
        assert "status" in data[0]["parking_spot"]



def test_read_parking_spots():
    # FETCH THE LIST OF PARKING SPOTS
    response = Config.client.get("/parking/")
    assert response.status_code == 200
    
    # CHECK THAT THE RESPONSE IS A LIST AND CONTAINS THE EXPECTED FIELDS
    data = response.json()
    assert isinstance(data, list)
    
    if data:
        assert "id" in data[0]
        assert "slot" in data[0]
        assert "status" in data[0]
