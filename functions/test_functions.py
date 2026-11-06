import os
import sys

# Add packages to path for importing
sys.path.append(os.path.join(os.path.dirname(__file__), "packages"))

from routing.calculate_single.__main__ import main as single_main
from routing.calculate_multiple.__main__ import main as multiple_main


def test_single():
    print("Testing calculate_single...")
    args = {
        "origin": {"lat": 6.5244, "lng": 3.3792},  # Lagos
        "destination": {"lat": 6.4698, "lng": 3.5852},  # Lekki
    }
    result = single_main(args)
    print("Single result:", result)


def test_multiple():
    print("\nTesting calculate_multiple...")
    args = {
        "origin": {"lat": 6.5244, "lng": 3.3792},  # Lagos
        "destinations": [
            {"lat": 6.4698, "lng": 3.5852},  # Lekki
            {"lat": 6.6018, "lng": 3.3515},  # Ikeja
        ],
    }
    result = multiple_main(args)
    print("Multiple result:", result)


if __name__ == "__main__":
    if "GOOGLE_MAPS_API_KEY" not in os.environ:
        print(
            "Warning: GOOGLE_MAPS_API_KEY environment variable not set. Function may return an error but that is expected formatting."
        )

    test_single()
    test_multiple()
