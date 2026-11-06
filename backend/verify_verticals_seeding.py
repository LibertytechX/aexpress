import os
import sys
import django

# Setup Django environment
sys.path.append("/home/ayo/Liberty/aexpress/backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ax_merchant_api.settings")
django.setup()

from dispatcher.models import Vertical, Zone

def verify_seeding():
    print("--- AXpress Vertical & Zone Verification ---")
    
    # Check Verticals
    vertical_count = Vertical.objects.count()
    print(f"Total Verticals: {vertical_count} (Expected: 4)")
    
    expected_leads = {
        "A": "Dennis",
        "B": "Seun",
        "C": "Mary",
        "D": "Erinfolami"
    }
    
    for code, lead in expected_leads.items():
        v = Vertical.objects.filter(code=code).first()
        if v and v.lead_name == lead:
            print(f"  [PASS] Vertical {code} lead is {lead}")
        else:
            print(f"  [FAIL] Vertical {code} lead mismatch or missing")

    # Check Zones
    zone_count = Zone.objects.count()
    print(f"Total Zones: {zone_count} (Expected: 20)")
    
    for code in expected_leads.keys():
        count = Zone.objects.filter(vertical__code=code).count()
        print(f"  Vertical {code} Zones: {count} (Expected: 5)")
        if count != 5:
            print(f"    [FAIL] Vertical {code} should have exactly 5 zones")
        else:
            print(f"    [PASS] Vertical {code} has 5 zones")

    # Sample Check: Ikeja
    ikeja = Zone.objects.filter(name="Ikeja").first()
    if ikeja and ikeja.vertical.code == "C" and abs(ikeja.center_lat - 6.6059) < 0.001:
        print(f"  [PASS] Ikeja zone verified (Vertical C, Lat 6.6059)")
    else:
        print(f"  [FAIL] Ikeja zone validation failed")

    print("--- Verification Finished ---")

if __name__ == "__main__":
    verify_seeding()
