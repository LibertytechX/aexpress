import os
import django
import sys

sys.path.append("/Users/ayo/Liberty/aexpress/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ax_merchant_api.settings")
django.setup()

from django.contrib.auth import get_user_model
from dispatcher.models import Merchant

User = get_user_model()
merchants = User.objects.filter(usertype="Merchant")

print(f"Found {merchants.count()} merchants.")

for m in merchants:
    try:
        if not hasattr(m, "merchant_profile"):
            print(f"Creating profile for {m.email}")
            Merchant.objects.create(user=m)
        else:
            print(f"Profile exists for {m.email}")
    except Exception as e:
        print(f"Error for {m.email}: {e}")
