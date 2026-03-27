# Changelog

All notable changes to the AXpress project are documented in this file.

---

## [2026-03-27] — Checkout Referral & Virtual Account Integration

### Frontend
#### Added
- **Signup Referral:** Added an optional "Referral Code" field to Step 1 of the merchant signup form.
- **Dynamic Wallet Funding:** Integrated `getVirtualAccount` API to fetch real bank details for wallet funding via bank transfer.
- **BankTransferModal:** Updated to fetch and display dynamic virtual account details (bank name, account number, account name) instead of hardcoded placeholders.
- **API Wrapper:** Added `Wallet.getVirtualAccount()` to `src/lib/api.ts`.

#### Changed
- Updated signup payload to include `referral_code`.
- Improved professional UI for referral input with a "Gift" icon.

### API
#### Added
- `GET /wallet/virtual-account/` — Retrieves or creates a dedicated virtual account for the merchant.
