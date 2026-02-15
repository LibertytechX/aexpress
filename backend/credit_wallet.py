#!/usr/bin/env python
"""
Script to manually credit a user's wallet for testing
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ax_merchant_api.settings')
django.setup()

from authentication.models import User
from wallet.models import Wallet
from decimal import Decimal

def credit_wallet(phone, amount):
    """Credit a user's wallet"""
    try:
        user = User.objects.get(phone=phone)
        wallet, created = Wallet.objects.get_or_create(user=user)
        
        print(f"\n📊 Wallet Info:")
        print(f"   User: {user.business_name}")
        print(f"   Phone: {user.phone}")
        print(f"   Current Balance: ₦{wallet.balance}")
        
        # Credit wallet
        new_balance = wallet.credit(
            amount=Decimal(str(amount)),
            description="Manual wallet funding for testing",
            reference=f"TEST-CREDIT-{wallet.id}"
        )
        
        print(f"\n✅ Wallet credited successfully!")
        print(f"   Amount Credited: ₦{amount}")
        print(f"   New Balance: ₦{new_balance}")
        
        # Show recent transactions
        transactions = wallet.transactions.all()[:5]
        print(f"\n📝 Recent Transactions:")
        for txn in transactions:
            print(f"   - {txn.type.upper()}: ₦{txn.amount} | {txn.description} | {txn.status}")
        
    except User.DoesNotExist:
        print(f"❌ User with phone {phone} not found!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    # Credit the admin user's wallet with ₦10,000
    credit_wallet("08099999999", 10000)

