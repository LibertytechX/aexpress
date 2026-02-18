"""
CoreBanking (LibertyPay Banking) service for virtual account management.

Uses a single Assured Express company account to create dedicated Wema Bank
virtual accounts for each merchant. Payments to these accounts are credited
to the merchant's wallet via webhook.
"""
import random
import logging

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

COREBANKING_TOKEN_CACHE_KEY = 'corebanking_access_token'
COREBANKING_TOKEN_TTL = 3600  # 1 hour


def login():
    """
    Authenticate with CoreBanking using the Assured Express company credentials
    and return an access token. Token is cached in Redis to avoid repeated logins.
    """
    cached_token = cache.get(COREBANKING_TOKEN_CACHE_KEY)
    if cached_token:
        return cached_token

    base_url = settings.COREBANKING_BASE_URL
    email = settings.COREBANKING_EMAIL
    password = settings.COREBANKING_PASSWORD

    try:
        response = requests.post(
            f'{base_url}/api/v1/companies/auth/login/',
            json={'email': email, 'password': password},
            timeout=30,
        )
        response_data = response.json()

        if response.status_code == 200 and response_data.get('status') == 'success':
            access_token = response_data['data']['access']
            cache.set(COREBANKING_TOKEN_CACHE_KEY, access_token, COREBANKING_TOKEN_TTL)
            return access_token

        logger.error('CoreBanking login failed: %s', response_data)
        raise Exception(
            f'CoreBanking authentication failed: {response_data.get("message", "Unknown error")}'
        )

    except requests.RequestException as e:
        logger.error('CoreBanking login request error: %s', e)
        raise Exception(f'CoreBanking connection error: {str(e)}')


def _do_create_virtual_account(base_url, access_token, payload):
    """Internal helper: POST virtual account creation to CoreBanking API."""
    return requests.post(
        f'{base_url}/api/v1/wema/virtual_accounts/',
        json=payload,
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        },
        timeout=30,
    )


def create_virtual_account(user):
    """
    Get or create a Wema Bank virtual account for the given merchant user.

    - Parses first/last name from user.contact_name
    - Uses fallback BVN (random 11 digits) and DOB (1990-01-01) if not available
    - Account name format: "{first_name} {last_name} AXPRESS"
    - Persists the virtual account in the VirtualAccount model
    """
    from .models import VirtualAccount  # avoid circular import at module level

    # Return existing account if already created
    try:
        return VirtualAccount.objects.get(user=user)
    except VirtualAccount.DoesNotExist:
        pass

    # Parse name
    parts = (user.contact_name or '').strip().split()
    if len(parts) >= 2:
        first_name = parts[0]
        last_name = ' '.join(parts[1:])
    elif len(parts) == 1:
        first_name = parts[0]
        last_name = parts[0]
    else:
        first_name = (user.business_name or 'Merchant')[:50]
        last_name = 'User'

    account_name = f"{first_name} {last_name} AXPRESS"

    # BVN fallback
    bvn = getattr(user, 'bvn', None) or ''.join(
        str(random.randint(0, 9)) for _ in range(11)
    )

    # Date of birth fallback
    dob = getattr(user, 'date_of_birth', None)
    date_of_birth = dob.strftime('%Y-%m-%d') if dob else '1990-01-01'

    # Normalise phone to international format (234XXXXXXXXXX)
    phone = (user.phone or '').strip()
    if phone.startswith('+'):
        phone = phone[1:]
    elif phone.startswith('0'):
        phone = '234' + phone[1:]
    elif not phone.startswith('234'):
        phone = '234' + phone

    payload = {
        'first_name': first_name,
        'middle_name': '',
        'last_name': last_name,
        'bvn': bvn,
        'email': user.email,
        'phone': phone,
        'date_of_birth': date_of_birth,
    }

    base_url = settings.COREBANKING_BASE_URL
    access_token = login()

    try:
        response = _do_create_virtual_account(base_url, access_token, payload)
        response_data = response.json()

        # Retry once on 401 (token expired)
        if response.status_code == 401:
            cache.delete(COREBANKING_TOKEN_CACHE_KEY)
            access_token = login()
            response = _do_create_virtual_account(base_url, access_token, payload)
            response_data = response.json()

        if response.status_code == 201 and response_data.get('status') == 'success':
            account_details = response_data['data']['account_details']
            virtual_account = VirtualAccount.objects.create(
                user=user,
                account_number=account_details['account_number'],
                account_name=account_name,
                bank_name='Wema Bank',
                bank_code='000017',
                corebanking_account_id=account_details['id'],
            )
            return virtual_account

        logger.error('CoreBanking virtual account creation failed: %s', response_data)
        raise Exception(
            f'Virtual account creation failed: {response_data.get("message", "Unknown error")}'
        )

    except requests.RequestException as e:
        logger.error('CoreBanking virtual account request error: %s', e)
        raise Exception(f'CoreBanking connection error: {str(e)}')

