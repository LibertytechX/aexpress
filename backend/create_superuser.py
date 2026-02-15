#!/usr/bin/env python
"""
Script to create a superuser for Django admin access.
"""

import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ax_merchant_api.settings')
django.setup()

from authentication.models import User

def create_superuser():
    """Create a superuser if it doesn't exist."""
    
    # Superuser credentials
    phone = "08099999999"
    email = "admin@axpress.com"
    password = "admin123"
    business_name = "AX Express Admin"
    contact_name = "System Administrator"
    
    # Check if superuser already exists
    if User.objects.filter(phone=phone).exists():
        print(f"❌ Superuser with phone {phone} already exists!")
        user = User.objects.get(phone=phone)
        print(f"✅ Existing superuser: {user.business_name} ({user.email})")
        return
    
    # Create superuser
    try:
        user = User.objects.create_superuser(
            phone=phone,
            email=email,
            password=password,
            business_name=business_name,
            contact_name=contact_name
        )
        
        print("="*60)
        print("✅ SUPERUSER CREATED SUCCESSFULLY!")
        print("="*60)
        print(f"Phone: {phone}")
        print(f"Email: {email}")
        print(f"Password: {password}")
        print(f"Business Name: {business_name}")
        print(f"Contact Name: {contact_name}")
        print("="*60)
        print("\n🌐 Access Django Admin at: http://127.0.0.1:8000/admin/")
        print(f"   Login with phone: {phone}")
        print(f"   Password: {password}")
        print("="*60)
        
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")

if __name__ == "__main__":
    create_superuser()

