import uuid
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager for User model."""

    def create_user(self, phone, email, password=None, **extra_fields):
        """Create and return a regular user."""
        if not phone:
            raise ValueError("Phone number is required")
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)
        user = self.model(phone=phone, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, email, password=None, **extra_fields):
        """Create and return a superuser."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")

        return self.create_user(phone, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model for AX Merchant Portal."""

    USER_TYPE_CHOICES = (
        ("Merchant", "Merchant"),
        ("Rider", "Rider"),
        ("Customer", "Customer"),
        ("Dispatcher", "Dispatcher"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usertype = models.CharField(
        max_length=20, choices=USER_TYPE_CHOICES, default="Merchant"
    )
    first_name = models.CharField(max_length=150, null=True, blank=True)
    last_name = models.CharField(max_length=150, null=True, blank=True)
    business_name = models.CharField(max_length=255, null=True, blank=True)
    contact_name = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=20, unique=True, db_index=True)
    email = models.EmailField(unique=True, db_index=True)
    address = models.TextField(null=True, blank=True)

    # Status fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)

    # Email verification
    email_verification_token = models.CharField(
        max_length=100, null=True, blank=True, unique=True
    )
    email_verification_token_created = models.DateTimeField(null=True, blank=True)

    # Password reset
    password_reset_token = models.CharField(
        max_length=100, null=True, blank=True, unique=True
    )
    password_reset_token_created = models.DateTimeField(null=True, blank=True)

    # OTP verification
    otp = models.CharField(max_length=6, null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["email", "business_name", "contact_name"]

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.business_name} ({self.phone})"

    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.contact_name or self.phone

    def get_short_name(self):
        return self.business_name


class Address(models.Model):
    """Model for storing multiple addresses per user."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="addresses")
    label = models.CharField(max_length=100, help_text="e.g., Office, Warehouse, Home")
    address = models.TextField(help_text="Full address text")
    is_default = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "addresses"
        verbose_name = "Address"
        verbose_name_plural = "Addresses"
        ordering = ["-is_default", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "label"], name="unique_user_address_label"
            )
        ]

    def __str__(self):
        default_marker = " (Default)" if self.is_default else ""
        return f"{self.user.business_name} - {self.label}{default_marker}"

    def save(self, *args, **kwargs):
        """Override save to ensure only one default address per user."""
        if self.is_default:
            # Unset other default addresses for this user
            Address.objects.filter(user=self.user, is_default=True).exclude(
                id=self.id
            ).update(is_default=False)

        # Validate max 3 addresses per user
        if not self.pk:  # New address
            existing_count = Address.objects.filter(user=self.user).count()
            if existing_count >= 3:
                from django.core.exceptions import ValidationError

                raise ValidationError("Maximum of 3 addresses allowed per user.")

        super().save(*args, **kwargs)
