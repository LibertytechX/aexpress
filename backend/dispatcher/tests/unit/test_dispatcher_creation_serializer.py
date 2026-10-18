import pytest
from rest_framework.exceptions import ValidationError
from authentication.models import User
from dispatcher.models import DispatcherProfile
from dispatcher.serializers import DispatcherCreateSerializer


@pytest.mark.django_db
class TestDispatcherCreateSerializer:
    def test_create_dispatcher_default_admin_role(self):
        data = {
            "first_name": "Alice",
            "last_name": "Dispatcher",
            "phone": "+2348011223344",
            "email": "alice.dispatcher@example.com",
            "password": "securepassword123",
        }
        serializer = DispatcherCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        profile = serializer.save()

        assert profile.user.phone == "+2348011223344"
        assert profile.user.email == "alice.dispatcher@example.com"
        assert profile.user.usertype == "Dispatcher"
        assert profile.role == DispatcherProfile.Role.ADMIN
        assert DispatcherProfile.objects.filter(user=profile.user).count() == 1

    def test_create_dispatcher_hub_captain_generates_affiliation_code(self):
        data = {
            "first_name": "Bob",
            "last_name": "Captain",
            "phone": "+2348022334455",
            "email": "bob.captain@example.com",
            "password": "securepassword123",
            "role": DispatcherProfile.Role.HUB_CAPTAIN,
        }
        serializer = DispatcherCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        profile = serializer.save()

        assert profile.user.phone == "+2348022334455"
        assert profile.role == DispatcherProfile.Role.HUB_CAPTAIN
        assert profile.affiliation_code is not None
        assert len(profile.affiliation_code) > 0
        assert DispatcherProfile.objects.filter(user=profile.user).count() == 1

    def test_create_dispatcher_zone_lead_generates_affiliation_code(self):
        data = {
            "first_name": "Charlie",
            "last_name": "Lead",
            "phone": "+2348033445566",
            "email": "charlie.lead@example.com",
            "password": "securepassword123",
            "role": DispatcherProfile.Role.ZONE_LEAD,
        }
        serializer = DispatcherCreateSerializer(data=data)
        assert serializer.is_valid(), serializer.errors
        profile = serializer.save()

        assert profile.user.phone == "+2348033445566"
        assert profile.role == DispatcherProfile.Role.ZONE_LEAD
        assert profile.affiliation_code is not None
        assert len(profile.affiliation_code) > 0
        assert DispatcherProfile.objects.filter(user=profile.user).count() == 1

    def test_duplicate_phone_validation(self):
        User.objects.create_user(
            phone="+2348099999999",
            email="existing@example.com",
            password="password123",
            usertype="Dispatcher",
        )
        data = {
            "first_name": "Duplicate",
            "last_name": "User",
            "phone": "+2348099999999",
            "email": "new@example.com",
            "password": "securepassword123",
        }
        serializer = DispatcherCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "phone" in serializer.errors

    def test_duplicate_email_validation(self):
        User.objects.create_user(
            phone="+2348088888888",
            email="existing_email@example.com",
            password="password123",
            usertype="Dispatcher",
        )
        data = {
            "first_name": "Duplicate",
            "last_name": "User",
            "phone": "+2348077777777",
            "email": "existing_email@example.com",
            "password": "securepassword123",
        }
        serializer = DispatcherCreateSerializer(data=data)
        assert not serializer.is_valid()
        assert "email" in serializer.errors
