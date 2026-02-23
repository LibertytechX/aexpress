import os
import django
import sys

# Setup Django environment
sys.path.append("/Users/ayo/Liberty/aexpress/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ax_merchant_api.settings")

try:
    django.setup()
except Exception as e:
    print(f"Error setting up Django: {e}")
    sys.exit(1)

from authentication.models import User
from dispatcher.models import DispatcherProfile
from rest_framework.test import APIRequestFactory
from dispatcher.views import RiderViewSet


def verify_dispatcher_auth():
    print("Verifying Dispatcher Auth Flow...")

    phone = "+2349000000009"
    email = "dispatcher.test@example.com"
    password = "password123"

    # 1. Cleanup existing user
    try:
        user = User.objects.get(phone=phone)
        print(f"User {phone} exists. Deleting...")
        user.delete()
    except User.DoesNotExist:
        pass

    # 2. Test Signup
    print("Testing Signup...")
    factory = APIRequestFactory()
    # Using existing auth endpoints (assuming they are standard DRF or custom views in authentication app)
    # We need to import the views from authentication app to test them directly with factory
    from authentication.views import SignupView, LoginView

    signup_view = SignupView.as_view()

    data = {
        "phone": phone,
        "email": email,
        "password": password,
        "confirm_password": password,
        "contact_name": "Test Dispatcher",
        "business_name": "Dispatch Co",
        "usertype": "Dispatcher",
    }

    request = factory.post("/api/auth/signup/", data, format="json")
    response = signup_view(request)

    if response.status_code == 201:
        print("SUCCESS: Signup successful.")

        # Check Profile Creation
        try:
            user = User.objects.get(phone=phone)
            profile = DispatcherProfile.objects.get(user=user)
            print(f"SUCCESS: DispatcherProfile created for user {user.phone}.")
            if user.usertype != "Dispatcher":
                print(f"FAILURE: User type is {user.usertype}, expected Dispatcher.")
        except DispatcherProfile.DoesNotExist:
            print("FAILURE: DispatcherProfile NOT created.")
            return
    else:
        print(
            f"FAILURE: Signup failed. Status: {response.status_code}, Data: {response.data}"
        )
        return

    # 3. Test Login
    print("Testing Login...")
    login_view = LoginView.as_view()

    login_data = {"phone": phone, "password": password}

    request = factory.post("/api/auth/login/", login_data, format="json")
    response = login_view(request)

    if response.status_code == 200:
        if "access" in response.data and "refresh" in response.data:
            print("SUCCESS: Login successful. Tokens received.")
        else:
            print("FAILURE: Login successful but tokens missing.")
    else:
        print(
            f"FAILURE: Login failed. Status: {response.status_code}, Data: {response.data}"
        )

    # Cleanup
    print("Cleaning up...")
    user.delete()


if __name__ == "__main__":
    verify_dispatcher_auth()
