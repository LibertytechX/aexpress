import logging
from typing import Any, Dict, Optional, Tuple
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
import requests
from sparky_utils.exceptions import ServiceException

logger = logging.getLogger(__name__)


class LibertyPayAccountEnquiryService:
    """
    Handles bank account name enquiry via LibertyPay management API.
    Replicated from the battle-tested pulse-backend integration.
    """

    def __init__(
        self,
        api_url: Optional[str] = None,
        timeout: int = 10,
    ) -> None:
        self.api_url: str = api_url or getattr(
            settings,
            "LIBERTYPAY_ACCOUNT_ENQUIRY_URL",
            "https://management.libertypayng.com/api/v1/sales/account_name_enquiry/",
        )
        self.timeout: int = timeout

    def verify_account(
        self, account_number: str, bank_code: str
    ) -> Optional[Dict[str, Any]]:
        """
        Verify an account number using its bank code via LibertyPay Account Enquiry API.

        Args:
            account_number: The 10-digit bank account number.
            bank_code: The bank code or 6-digit CBN/NIBSS institution code.

        Returns:
            Dict containing account_name, account_number, bank_code, currency_code, or None if failed.
        """
        from wallet.models import Bank

        code_to_use: str = str(bank_code).strip()

        # Attempt to resolve 6-digit CBN code from Bank model if available
        try:
            bank = Bank.objects.filter(
                Q(bank_code=code_to_use) | Q(cbn_code=code_to_use)
            ).first()
            if bank:
                if bank.bank_code and len(bank.bank_code) >= 6:
                    code_to_use = bank.bank_code
                elif bank.cbn_code and len(bank.cbn_code) >= 6:
                    code_to_use = bank.cbn_code
        except Exception as e:
            logger.warning(f"Failed to resolve bank code from Bank model: {e}")

        # NIBSS CBN institution codes are 6 digits; zero-pad if numeric and under 6 digits
        if code_to_use.isdigit() and len(code_to_use) < 6:
            code_to_use = code_to_use.zfill(6)

        payload: Dict[str, str] = {
            "account_number": str(account_number).strip(),
            "bank_code": code_to_use,
        }

        try:
            logger.info(
                f"Verifying account {account_number} with bank code {code_to_use} via LibertyPay Enquiry API"
            )
            response = requests.post(
                self.api_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=self.timeout,
            )

            if response.status_code == 200:
                res_data = response.json()
                if res_data.get("data") and res_data.get("status") in ("success", None):
                    raw_data = res_data["data"]
                    account_name = raw_data.get("account_name") or raw_data.get(
                        "accountName"
                    )
                    acc_num = (
                        raw_data.get("account_number")
                        or raw_data.get("accountNumber")
                        or str(account_number).strip()
                    )
                    currency_code = (
                        raw_data.get("currencyCode")
                        or raw_data.get("currency_code")
                        or "NGN"
                    )

                    if not account_name:
                        logger.error(
                            f"LibertyPay enquiry response missing account_name: {res_data}"
                        )
                        return None

                    return {
                        "account_number": acc_num,
                        "account_name": account_name,
                        "bank_code": bank_code,
                        "cbn_code": code_to_use,
                        "currency_code": currency_code,
                    }
                else:
                    err_msg = res_data.get("errors") or res_data.get("message")
                    logger.error(f"LibertyPay verify account unsuccessful: {err_msg}")
                    return None
            else:
                logger.error(
                    f"LibertyPay enquiry failed HTTP {response.status_code}: {response.text}"
                )
                return None

        except (requests.RequestException, ValueError, KeyError) as e:
            logger.error(f"Exception during LibertyPay verify_account: {e}")
            return None


class WemaCoreBankingPayoutSDK:
    """
    Handles funds disbursement to destination bank accounts via Wema CoreBanking.
    Replicated and hardened from GetLinkBackend/user_transaction.
    """

    def __init__(self, mode: Optional[str] = None) -> None:
        self.mode: str = mode or getattr(settings, "COREBANKING_MODE", "LIVE")
        self.email: str = getattr(settings, "COREBANKING_EMAIL", "")
        self.password: str = getattr(settings, "COREBANKING_PASSWORD", "")
        self.source_account: str = getattr(
            settings, "COREBANKING_WEMA_SOURCE_ACCOUNT", ""
        ) or getattr(settings, "COREBANKING_SOURCE_ACCOUNT", "")

        base_url = getattr(
            settings, "COREBANKING_BASE_URL", "https://banking.libertypayng.com"
        )
        if not base_url.endswith("/"):
            base_url += "/"
        self.base_url: str = base_url

    def login(self) -> Tuple[bool, str]:
        """
        Authenticate with CoreBanking API and retrieve cached bearer access token.
        """
        cache_key = "liberty_pay_corebanking_token"
        cached_token = cache.get(cache_key)
        if cached_token:
            return True, cached_token

        if not self.email or not self.password:
            logger.error("CoreBanking credentials missing in configuration.")
            return False, ""

        url = f"{self.base_url}api/v1/companies/auth/login/"
        payload = {"email": self.email, "password": self.password}

        try:
            response = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=15,
            )
            if response.status_code == 200:
                resp_json = response.json()
                access_token = (
                    resp_json.get("data", {}).get("access")
                    or resp_json.get("data", {}).get("token")
                    or resp_json.get("token")
                )
                if access_token:
                    cache.set(cache_key, access_token, 43200)  # 12 hours
                    return True, access_token
            logger.error(
                f"CoreBanking login failed: status {response.status_code}, response: {response.text}"
            )
            return False, ""
        except requests.RequestException as e:
            logger.error(f"Request exception during CoreBanking login: {e}")
            return False, ""

    def transfer_funds(
        self,
        amount: float,
        narration: str,
        account_name: str,
        account_number: str,
        bank_code: str,
        reference: str,
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Disburse funds to the specified bank account.

        Returns:
            Tuple[bool, Dict[str, Any]]: (success, response_payload)
        """
        url = f"{self.base_url}accounts/transfer_money/"
        payload = {
            "amount": float(amount),
            "narration": narration or "Rider Wallet Withdrawal",
            "account_name": account_name,
            "account_number": str(account_number).strip(),
            "bank_code": str(bank_code).strip(),
            "request_reference": reference,
            "mode": self.mode,
            "source_account": self.source_account,
        }

        success, token = self.login()
        if not success:
            logger.error(
                "Cannot transfer funds: CoreBanking login authentication failed."
            )
            return False, {"message": "Banking service authentication unavailable"}

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            logger.info(
                f"Initiating CoreBanking transfer of ₦{amount} to {account_number} ({bank_code}) ref={reference}"
            )
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            try:
                resp_data = response.json()
            except Exception:
                resp_data = {"text": response.text}

            logger.info(
                f"CoreBanking transfer response [{response.status_code}]: {resp_data}"
            )

            if response.status_code in (200, 201):
                return True, resp_data.get("data", resp_data)
            return False, resp_data

        except requests.RequestException as e:
            logger.error(f"Request exception during CoreBanking transfer: {e}")
            return False, {
                "error": str(e),
                "message": "Network timeout or connection error",
            }

    def verify_status(self, reference: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Verify transfer status by reference.
        """
        url = f"{self.base_url}accounts/verify_transfer?search={reference}"
        success, token = self.login()
        if not success:
            return False, {"message": "Banking service authentication unavailable"}

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                resp_data = response.json()
                return True, resp_data.get("data", resp_data)
            return False, response.json()
        except requests.RequestException as e:
            logger.error(f"Request exception during CoreBanking verify_status: {e}")
            return False, {"error": str(e)}
