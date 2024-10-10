from app.config import Config

def test_create_parking_spot():
    response = Config.client.post("/parking/", json={"slot": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["slot"] == 5
    assert data["status"] == "available"


def test_create_vehicle_registration():
    # REGISTER A VEHICLE IN THE AVAILABLE SPOT
    response = Config.client.post("/vehicle-registration", json={"vehicle_number": "KMM222", "parking_spot_id": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["vehicle_number"] == "KMM222"

def test_exit_vehicle():
    # EXIT A REGISTER VEHICLE
    response = Config.client.post("/vehicle-exit", json={"vehicle_number": "KLL111"})
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Vehicle registration in slot 3 has been deleted."
    assert data["data"]["vehicle_number"] == "KLL111"
