import os
import django
import sys
from unittest.mock import patch, MagicMock

# Set up Django environment
sys.path.append('/Users/mac/Liberty/aexpress/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ax_merchant_api.settings')
django.setup()

from dispatcher.utils import find_closest_zone
from django.conf import settings

def test_closest_zone_custom_routing():
    print("Testing find_closest_zone with Custom Routing (Table API)...")
    
    # Mock Zone model
    class MockZone:
        def __init__(self, name, lat, lng):
            self.name = name
            self.center_lat = lat
            self.center_lng = lng

    zones = [
        MockZone("Zone A", 6.5200, 3.3900),
        MockZone("Zone B", 6.5873, 3.3785),
    ]

    # Mock settings
    with patch.object(settings, 'ROUTING_PROVIDER', 'custom'):
        with patch.object(settings, 'ROUTING_SERVICE_URL', 'http://localhost:8071/api/v1/directions'):
            with patch.object(settings, 'ROUTING_SERVICE_API_KEY', 'test_key'):
                
                # Mock Zone.objects.filter
                with patch('dispatcher.models.Zone.objects.filter') as mock_filter:
                    mock_filter.return_value = MagicMock(is_active=True)
                    # When converted to list, it should return our mock zones
                    mock_filter.return_value.__iter__.return_value = zones
                    
                    # Mock requests.get for the Table API
                    with patch('requests.get') as mock_get:
                        mock_response = MagicMock()
                        mock_response.status_code = 200
                        # OSRM Table response format
                        mock_response.json.return_value = {
                            "status": "success",
                            "data": {
                                "distances": [
                                    [1200.5, 4500.2]  # distance from origin to Zone A and Zone B
                                ]
                            }
                        }
                        mock_get.return_value = mock_response
                        
                        closest_zone = find_closest_zone(6.5069541, 3.3830028)
                        
                        # Verify calls
                        mock_get.assert_called_once()
                        args, kwargs = mock_get.call_args
                        
                        print(f"URL called: {args[0]}")
                        assert "/table" in args[0]
                        print(f"Params: {kwargs['params']}")
                        
                        # Verify coordinate swap (lng,lat)
                        assert kwargs['params']['origin'] == "3.3830028,6.5069541"
                        
                        print(f"Closest Zone: {closest_zone.name if closest_zone else 'None'}")
                        assert closest_zone.name == "Zone A"
                        
    print("Test Passed! ✅")

if __name__ == "__main__":
    test_closest_zone_custom_routing()
