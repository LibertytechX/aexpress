#!/usr/bin/env python
"""
Quick test script to verify authentication API endpoints.
Run this after starting the Django server.
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8000/api/auth"

def print_response(title, response):
    """Pretty print API response."""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")

def test_signup():
    """Test user signup endpoint."""
    data = {
        "business_name": "Test Logistics Ltd",
        "contact_name": "John Doe",
        "phone": "08012345678",
        "email": "test@testlogistics.com",
        "address": "123 Test Street, Lagos",
        "password": "testpass123",
        "confirm_password": "testpass123"
    }
    
    response = requests.post(f"{BASE_URL}/signup/", json=data)
    print_response("SIGNUP TEST", response)
    
    if response.status_code == 201:
        return response.json()
    return None

def test_login(phone, password):
    """Test user login endpoint."""
    data = {
        "phone": phone,
        "password": password
    }
    
    response = requests.post(f"{BASE_URL}/login/", json=data)
    print_response("LOGIN TEST", response)
    
    if response.status_code == 200:
        return response.json()
    return None

def test_get_profile(access_token):
    """Test get user profile endpoint."""
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    response = requests.get(f"{BASE_URL}/me/", headers=headers)
    print_response("GET PROFILE TEST", response)

def test_update_profile(access_token):
    """Test update user profile endpoint."""
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    data = {
        "business_name": "Updated Logistics Ltd",
        "address": "456 New Street, Lagos"
    }
    
    response = requests.put(f"{BASE_URL}/profile/", json=data, headers=headers)
    print_response("UPDATE PROFILE TEST", response)

def test_refresh_token(refresh_token):
    """Test token refresh endpoint."""
    data = {
        "refresh": refresh_token
    }
    
    response = requests.post(f"{BASE_URL}/refresh/", json=data)
    print_response("REFRESH TOKEN TEST", response)
    
    if response.status_code == 200:
        return response.json()
    return None

def test_logout(access_token, refresh_token):
    """Test logout endpoint."""
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    data = {
        "refresh_token": refresh_token
    }
    
    response = requests.post(f"{BASE_URL}/logout/", json=data, headers=headers)
    print_response("LOGOUT TEST", response)

if __name__ == "__main__":
    print("\n🚀 Starting Authentication API Tests...")
    print(f"Base URL: {BASE_URL}")
    
    # Test 1: Signup
    signup_result = test_signup()
    
    if signup_result and signup_result.get('success'):
        access_token = signup_result['tokens']['access']
        refresh_token = signup_result['tokens']['refresh']
        phone = signup_result['user']['phone']
        
        # Test 2: Get Profile
        test_get_profile(access_token)
        
        # Test 3: Update Profile
        test_update_profile(access_token)
        
        # Test 4: Refresh Token
        refresh_result = test_refresh_token(refresh_token)
        if refresh_result:
            new_access_token = refresh_result.get('access')
            print(f"\n✅ New access token obtained!")
        
        # Test 5: Logout
        test_logout(access_token, refresh_token)
        
        # Test 6: Login with created account
        test_login(phone, "testpass123")
        
        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("="*60)
    else:
        print("\n❌ Signup failed. Cannot proceed with other tests.")

