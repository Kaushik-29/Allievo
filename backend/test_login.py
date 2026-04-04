import requests
import json

BASE_URL = "http://localhost:8000/api/v1/auth"

def test_login_flow():
    print("Testing Registration...")
    reg_data = {
        "username": "tester123",
        "password": "Password@123",
        "name": "Tester",
        "phone": "9876543210",
        "email": "tester@allievo.ai",
        "city": "Bengaluru",
        "aadhar_no": "123456781234",
        "pan_no": "ABCDE1234F",
        "primary_platform": "zomato",
        "work_location": "Koramanagala",
        "current_location": "HSR Layout",
        "working_proof": "Screenshot verified"
    }
    
    try:
        r = requests.post(f"{BASE_URL}/register", json=reg_data)
        if r.status_code == 200:
            print("Successfully Registered!")
        elif r.status_code == 400:
            print(f"User already exists? {r.json()['detail']}")
        else:
            print(f"Registration failed: {r.status_code} {r.text}")
            return
    except Exception as e:
        print(f"Error during registration: {e}")
        return

    print("\nTesting Login...")
    login_data = {
        "username": "tester123",
        "password": "Password@123"
    }
    
    try:
        r = requests.post(f"{BASE_URL}/login", json=login_data)
        if r.status_code == 200:
            print("Login SUCCESS!")
            print(f"Token: {r.json()['access_token'][:20]}...")
        else:
            print(f"Login FAILED: {r.status_code} {r.text}")
    except Exception as e:
        print(f"Error during login: {e}")

if __name__ == "__main__":
    test_login_flow()
