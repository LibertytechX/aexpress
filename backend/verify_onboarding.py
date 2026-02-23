import requests
import sys


def verify_onboarding(token):
    url = "http://localhost:8000/api/dispatcher/riders/onboarding/"
    headers = {"Authorization": f"Bearer {token}"}

    data = {
        "email": "testdriver@example.com",
        "phone": "08012345678",
        "first_name": "Test",
        "last_name": "Driver",
        "bank_name": "Test Bank",
        "bank_account_number": "1234567890",
        "vehicle_model": "Yamaha 125",
        "vehicle_plate_number": "LAG-123-XY",
        "working_type": "freelancer",
        "team": "Verification Team",
    }

    # Note: For real testing, we should include files.
    # But for a basic check, we can just send data.

    try:
        response = requests.post(url, headers=headers, data=data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python verify_onboarding.py <auth_token>")
    else:
        verify_onboarding(sys.argv[1])
