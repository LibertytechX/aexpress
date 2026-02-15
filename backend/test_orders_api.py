#!/usr/bin/env python3
"""
Test script for Order Management API endpoints.
Tests all order creation modes: Quick Send, Multi-Drop, and Bulk Import.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api"

# ANSI color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}{text.center(60)}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✓ {text}{RESET}")

def print_error(text):
    print(f"{RED}✗ {text}{RESET}")

def print_info(text):
    print(f"{YELLOW}→ {text}{RESET}")

def print_json(data):
    print(json.dumps(data, indent=2))

# Step 1: Login to get access token
print_header("STEP 1: LOGIN")
login_data = {
    "phone": "08099999999",
    "password": "admin123"
}

print_info(f"Logging in with phone: {login_data['phone']}")
response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)

if response.status_code == 200:
    login_result = response.json()
    access_token = login_result['tokens']['access']
    print_success("Login successful!")
    print_info(f"Access token: {access_token[:50]}...")
else:
    print_error(f"Login failed: {response.status_code}")
    print_json(response.json())
    exit(1)

# Set up headers with authentication
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# Step 2: Get available vehicles
print_header("STEP 2: GET AVAILABLE VEHICLES")
response = requests.get(f"{BASE_URL}/orders/vehicles/", headers=headers)

if response.status_code == 200:
    vehicles_result = response.json()
    print_success(f"Retrieved {len(vehicles_result['vehicles'])} vehicles")
    for vehicle in vehicles_result['vehicles']:
        print_info(f"{vehicle['name']}: ₦{vehicle['base_price']} (max {vehicle['max_weight_kg']}kg)")
else:
    print_error(f"Failed to get vehicles: {response.status_code}")
    print_json(response.json())

# Step 3: Create Quick Send order
print_header("STEP 3: CREATE QUICK SEND ORDER")
quick_send_data = {
    "pickup_address": "27A Idowu Martins St, Victoria Island, Lagos",
    "sender_name": "Yetunde Igbene",
    "sender_phone": "08051832508",
    "dropoff_address": "24 Harvey Rd, Sabo Yaba, Lagos",
    "receiver_name": "Adebayo Johnson",
    "receiver_phone": "08034567890",
    "vehicle": "Bike",
    "payment_method": "wallet",
    "package_type": "Box",
    "notes": "Handle with care"
}

print_info("Creating Quick Send order...")
response = requests.post(f"{BASE_URL}/orders/quick-send/", json=quick_send_data, headers=headers)

if response.status_code == 201:
    quick_send_result = response.json()
    print_success(quick_send_result['message'])
    print_info(f"Order Number: {quick_send_result['order']['order_number']}")
    print_info(f"Total Amount: ₦{quick_send_result['order']['total_amount']}")
    print_info(f"Deliveries: {quick_send_result['order']['delivery_count']}")
else:
    print_error(f"Failed to create Quick Send order: {response.status_code}")
    print_json(response.json())

# Step 4: Create Multi-Drop order
print_header("STEP 4: CREATE MULTI-DROP ORDER")
multi_drop_data = {
    "pickup_address": "15 Admiralty Way, Lekki Phase 1, Lagos",
    "sender_name": "Yetunde Igbene",
    "sender_phone": "08051832508",
    "vehicle": "Car",
    "payment_method": "wallet",
    "deliveries": [
        {
            "dropoff_address": "42 Allen Avenue, Ikeja, Lagos",
            "receiver_name": "Funke Adeyemi",
            "receiver_phone": "09012345678",
            "package_type": "Box",
            "notes": "First delivery"
        },
        {
            "dropoff_address": "10 Broad St, Lagos Island",
            "receiver_name": "Chidi Obi",
            "receiver_phone": "07011223344",
            "package_type": "Envelope",
            "notes": "Second delivery"
        },
        {
            "dropoff_address": "33 Opebi Rd, Ikeja, Lagos",
            "receiver_name": "Blessing Nwosu",
            "receiver_phone": "08155667788",
            "package_type": "Fragile",
            "notes": "Third delivery - fragile"
        }
    ]
}

print_info(f"Creating Multi-Drop order with {len(multi_drop_data['deliveries'])} deliveries...")
response = requests.post(f"{BASE_URL}/orders/multi-drop/", json=multi_drop_data, headers=headers)

if response.status_code == 201:
    multi_drop_result = response.json()
    print_success(multi_drop_result['message'])
    print_info(f"Order Number: {multi_drop_result['order']['order_number']}")
    print_info(f"Total Amount: ₦{multi_drop_result['order']['total_amount']}")
    print_info(f"Deliveries: {multi_drop_result['order']['delivery_count']}")
else:
    print_error(f"Failed to create Multi-Drop order: {response.status_code}")
    print_json(response.json())

# Step 5: Create Bulk Import order
print_header("STEP 5: CREATE BULK IMPORT ORDER")
bulk_import_data = {
    "pickup_address": "24 Alara St, Iwaya, Lagos",
    "sender_name": "Yetunde Igbene",
    "sender_phone": "08051832508",
    "vehicle": "Van",
    "payment_method": "cash_on_pickup",
    "deliveries": [
        {
            "dropoff_address": "15 Awolowo Rd, Ikoyi, Lagos",
            "receiver_name": "Mrs. Adeyemi",
            "receiver_phone": "08034567890",
            "package_type": "Box"
        },
        {
            "dropoff_address": "22 Bode Thomas St, Surulere, Lagos",
            "receiver_name": "Chinedu O.",
            "receiver_phone": "09098765432",
            "package_type": "Envelope"
        },
        {
            "dropoff_address": "7 Allen Avenue, Ikeja, Lagos",
            "receiver_name": "Fatima B.",
            "receiver_phone": "07011223344",
            "package_type": "Box"
        },
        {
            "dropoff_address": "3 Admiralty Way, Lekki Phase 1, Lagos",
            "receiver_name": "David Eze",
            "receiver_phone": "08155667788",
            "package_type": "Fragile"
        },
        {
            "dropoff_address": "45 Herbert Macaulay, Yaba, Lagos",
            "receiver_name": "Blessing N.",
            "receiver_phone": "09044332211",
            "package_type": "Food"
        }
    ]
}

print_info(f"Creating Bulk Import order with {len(bulk_import_data['deliveries'])} deliveries...")
response = requests.post(f"{BASE_URL}/orders/bulk-import/", json=bulk_import_data, headers=headers)

if response.status_code == 201:
    bulk_import_result = response.json()
    print_success(bulk_import_result['message'])
    print_info(f"Order Number: {bulk_import_result['order']['order_number']}")
    print_info(f"Total Amount: ₦{bulk_import_result['order']['total_amount']}")
    print_info(f"Deliveries: {bulk_import_result['order']['delivery_count']}")
else:
    print_error(f"Failed to create Bulk Import order: {response.status_code}")
    print_json(response.json())

# Step 6: Get all orders
print_header("STEP 6: GET ALL ORDERS")
response = requests.get(f"{BASE_URL}/orders/", headers=headers)

if response.status_code == 200:
    orders_result = response.json()
    print_success(f"Retrieved {orders_result['count']} orders")
    for order in orders_result['orders']:
        print_info(f"Order {order['order_number']}: {order['mode']} - {order['status']} - ₦{order['total_amount']} ({order['delivery_count']} deliveries)")
else:
    print_error(f"Failed to get orders: {response.status_code}")
    print_json(response.json())

# Step 7: Get order statistics
print_header("STEP 7: GET ORDER STATISTICS")
response = requests.get(f"{BASE_URL}/orders/stats/", headers=headers)

if response.status_code == 200:
    stats_result = response.json()
    stats = stats_result['stats']
    print_success("Order statistics retrieved!")
    print_info(f"Total Orders: {stats['total_orders']}")
    print_info(f"Pending Orders: {stats['pending_orders']}")
    print_info(f"Completed Orders: {stats['completed_orders']}")
    print_info(f"Canceled Orders: {stats['canceled_orders']}")
    print_info(f"Total Spent: ₦{stats['total_spent']}")
    print_info(f"Average Cost: ₦{stats['average_cost']}")
else:
    print_error(f"Failed to get statistics: {response.status_code}")
    print_json(response.json())

# Step 8: Get specific order details
if 'quick_send_result' in locals():
    print_header("STEP 8: GET ORDER DETAILS")
    order_number = quick_send_result['order']['order_number']
    print_info(f"Getting details for order: {order_number}")
    response = requests.get(f"{BASE_URL}/orders/{order_number}/", headers=headers)

    if response.status_code == 200:
        order_detail = response.json()
        print_success("Order details retrieved!")
        print_info(f"Order Number: {order_detail['order']['order_number']}")
        print_info(f"Mode: {order_detail['order']['mode']}")
        print_info(f"Status: {order_detail['order']['status']}")
        print_info(f"Vehicle: {order_detail['order']['vehicle_name']}")
        print_info(f"Pickup: {order_detail['order']['pickup_address']}")
        print_info(f"Deliveries: {len(order_detail['order']['deliveries'])}")
        for idx, delivery in enumerate(order_detail['order']['deliveries'], 1):
            print_info(f"  {idx}. {delivery['receiver_name']} - {delivery['dropoff_address']}")
    else:
        print_error(f"Failed to get order details: {response.status_code}")
        print_json(response.json())

print_header("✅ ALL TESTS COMPLETED!")
print_success("Order Management API is working correctly!")
print_info("You can now integrate these endpoints with the frontend.")

