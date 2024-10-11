import pytest
from app.config import Config

@pytest.mark.parametrize("slot,expected_status, expected_message",[
    (5,200,None),
    (-1,400,"value_error.number.not_ge"),
    (21, 400, "value_error.number.not_le")
])
def test_create_parking_spot(slot,expected_status,expected_message):

    response = Config.client.post("/parking/", json={"slot": slot})

    assert response.status_code == expected_status
    
    if expected_message:
        data = response.json()
        assert data["detail"][0]["type"] == expected_message
    else:
        data = response.json()
        assert data["slot"] == slot
        assert data["status"] == "available"


@pytest.mark.parametrize(
    "vehicle_data, expected_status_code, expected_message",
    [
        # Case 1: Successful vehicle registration
        ({"vehicle_number": "KII444", "parking_spot_id": 1}, 200, "Vehicle registered successfully"),

        # Case 2: Parking spot is full (no available spots)
        ({"vehicle_number": "KBB555", "parking_spot_id": 1}, 400, "Parking full. Your vehicle has been added to the queue."),

        # Case 3: Vehicle is already registered
        ({"vehicle_number": "KII555", "parking_spot_id": 2}, 400, "Vehicle is already registered.")
    ]
)
def test_create_vehicle_registration(vehicle_data, expected_status_code, expected_message):

    # REGISTER A VEHICLE IN THE AVAILABLE SPOT
    response = Config.client.post("/vehicle-registration", json=vehicle_data)
    assert response.status_code == expected_status_code

    data = response.json()

    if expected_status_code == 200:
        assert data["vehicle_number"]==expected_message
    else:    
        assert expected_message in data["detail"]

@pytest.mark.parametrize(
    "vehicle_number, expected_status_code, expected_message",
    [
        # Case 1: Vehicle not found (non-existent vehicle number)
        ("ABC999", 400, "Vehicle was not found in the system. Please check the vehicle number and try again."),

        # Case 2: Vehicle exists and successfully exits
        ("KII222", 200, "Vehicle  has successfully exited from slot")
    ]
)
def test_exit_vehicle(vehicle_number, expected_status_code, expected_message):
    # EXIT A REGISTER VEHICLE
    response = Config.client.post("/vehicle-exit", json={"vehicle_number": vehicle_number})
    assert response.status_code == 200

    data = response.json()

    if expected_status_code == 200:
        assert expected_message in data["message"]
        assert data["data"]["vehicle_number"] == vehicle_number
    else:    
        assert expected_message in data["detail"]
