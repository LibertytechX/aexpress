import os
import django
import sys
from unittest.mock import patch, MagicMock

# Set up Django environment
sys.path.append('/Users/mac/Liberty/aexpress/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ax_merchant_api.settings')
django.setup()

from orders.utils import calculate_route
from django.conf import settings

def test_custom_routing_integration():
    print("Testing Custom Routing Integration...")
    
    # Mock settings
    with patch.object(settings, 'ROUTING_PROVIDER', 'custom'):
        with patch.object(settings, 'ROUTING_SERVICE_URL', 'http://localhost:8071/api/v1/directions'):
            with patch.object(settings, 'ROUTING_SERVICE_API_KEY', 'test_key'):
                
                # Mock coordinates
                origin = {"lat": 6.5069541, "lng": 3.3830028}
                destinations = [{"lat": 6.5200, "lng": 3.3900}]
                
                # Mock requests.get
                with patch('requests.get') as mock_get:
                    mock_response = MagicMock()
                    mock_response.status_code = 200
                    mock_response.json.return_value = {
                        "status": "success",
                        "data": [
                            {
                                "distance": 2232.6,
                                "duration": 239.8
                            }
                        ]
                    }
                    mock_get.return_value = mock_response
                    
                    result = calculate_route(origin, destinations)
                    
                    # Verify calls
                    mock_get.assert_called_once()
                    args, kwargs = mock_get.call_args
                    
                    print(f"URL called: {args[0]}")
                    print(f"Params: {kwargs['params']}")
                    print(f"Headers: {kwargs['headers']}")
                    
                    assert kwargs['headers']['X-API-Key'] == 'test_key'
                    # Verify coordinate swap (lng,lat)
                    assert kwargs['params']['origin'] == "3.3830028,6.5069541"
                    
                    print(f"Result: {result}")
                    assert result['distance_km'] == 2.23
                    assert result['duration_minutes'] == 4
                    
    print("Test Passed! ✅")

if __name__ == "__main__":
    test_custom_routing_integration()
