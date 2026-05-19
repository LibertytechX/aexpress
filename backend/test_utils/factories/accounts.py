import factory
from django.contrib.auth import get_user_model
from test_utils.factories.base import LibertyBaseFactory

User = get_user_model()


class UserFactory(LibertyBaseFactory):
    """
    Factory for authentication.User.

    Usage:
        user = UserFactory()
        merchant = UserFactory(usertype="Merchant")
        rider = UserFactory(usertype="Rider")
    """

    class Meta:
        model = User
        django_get_or_create = ("phone", "email")

    phone = factory.Sequence(lambda n: f"+234803{n:07d}")
    email = factory.Sequence(lambda n: f"user_{n}@aexpress-test.com")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    business_name = factory.Faker("company")
    contact_name = factory.LazyAttribute(lambda o: f"{o.first_name} {o.last_name}")
    usertype = "Merchant"
    is_active = True
    is_staff = False
    email_verified = True
    phone_verified = True
    password = factory.PostGenerationMethodCall("set_password", "Liberty@1234!")
