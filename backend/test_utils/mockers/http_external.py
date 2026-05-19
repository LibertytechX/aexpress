import re

import pytest
import responses as responses_lib


def _register_paystack(rsps, base):
    # Initialize transaction
    rsps.add(
        responses_lib.POST,
        f"{base}/transaction/initialize",
        json={
            "status": True,
            "message": "Authorization URL created",
            "data": {
                "authorization_url": "https://checkout.paystack.com/mock-code",
                "access_code": "mock-code",
                "reference": "mock-reference-123"
            }
        },
        status=200,
    )
    # Verify transaction
    rsps.add(
        responses_lib.GET,
        re.compile(rf"^{re.escape(base)}/transaction/verify/.*"),
        json={
            "status": True,
            "message": "Verification successful",
            "data": {
                "id": 123456,
                "domain": "test",
                "status": "success",
                "reference": "mock-reference-123",
                "amount": 500000, # 5000 NGN in kobo
                "gateway_response": "Successful",
                "channel": "card",
                "currency": "NGN",
                "customer": {
                    "email": "customer@example.com"
                }
            }
        },
        status=200,
    )


@pytest.fixture(autouse=True)
def mock_external_http():
    """Single shared RequestsMock; intercepts external HTTP requests during tests."""
    paystack = "https://api.paystack.co"

    with responses_lib.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        _register_paystack(rsps, paystack)
        yield rsps
