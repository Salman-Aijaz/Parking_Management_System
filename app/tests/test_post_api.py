import pytest
from fastapi.testclient import TestClient
from app.main import app 

client = TestClient(app)

@pytest.mark.parametrize("slot,expected_status, expected_message",[
    (5,200,None),
    (-1,400,"Slot number must be between 1 and 20."),
    (21, 400, "Slot number must be between 1 and 20.")
])
def test_create_parking_spot(slot,expected_status,expected_message):
    response = client.post("/parking/", json={"slot": slot})

    assert response.status_code == expected_status
    
    if expected_message:
        data=response.json()
        assert data["detail"]==expected_message
    else:
        data= response.json()
        assert data["slot"]==slot
        assert data["status"] == "available"    


def test_create_vehicle_registration():

    # REGISTER A VEHICLE IN THE AVAILABLE SPOT
    response = client.post("/vehicle-registration", json={"vehicle_number": "KMM222", "parking_spot_id": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["vehicle_number"] == "KMM222"

def test_exit_vehicle():
    # EXIT A REGISTER VEHICLE
    response = client.post("/vehicle-exit", json={"vehicle_number": "KLL111"})
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Vehicle registration in slot 3 has been deleted."
    assert data["data"]["vehicle_number"] == "KLL111"
