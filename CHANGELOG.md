# Changelog

All notable changes to the AXpress project are documented in this file.

---

## [2026-04-02] — Order Mode Redesign & Grouped Pricing Fix

### Frontend
#### Changed
- **Order Mode Selector**: Redesigned the "Quick vs Grouped" sub-mode selection from a standard dropdown to modern, interactive cards with icons and premium aesthetics.
- **Grouped Pricing Fix**: Resolved a bug where "Grouped Order" failed to trigger route calculation and estimation.
- **Estimated Prices**: Optimized the dynamic pricing logic to correctly apply the 30% discount to both simple and tiered pricing models in "Grouped" mode.

---

## [2026-03-27] — Checkout Referral & Virtual Account Integration

### Frontend
#### Added
- **Signup Referral:** Added an optional "Referral Code" field to Step 1 of the merchant signup form.
- **Dynamic Wallet Funding:** Integrated `getVirtualAccount` API to fetch real bank details for wallet funding via bank transfer.
- **Subscription Management:** Added a new "Subscription" sidebar item and management screen for plan selection.
- **Subscription Enhancements:** Refactored sidebar to a nested "Subscription" menu with "Plan" and "Invoice" sub-items.
- **Postpaid Plans:** Added support for Postpaid subscription plans with a multi-tab interface in the Subscription screen.
- **Invoices Screen:** Implemented a dedicated screen for viewing and downloading subscription invoices.
- **API Wrapper:** Added `Wallet.getVirtualAccount()`, `SubscriptionAPI`, and Postpaid methods to `src/lib/api.ts`.

#### Changed
- Updated signup payload to include `referral_code`.
- Improved professional UI for referral input with a "Gift" icon.

### API
#### Added
- `GET /wallet/virtual-account/` — Retrieves or creates a dedicated virtual account for the merchant.
- `GET /subscriptions/plans/` — Retrieves available subscription plans.
- `POST /subscriptions/plans/{id}/subscribe/` — Subscribes a merchant to a plan.
- `GET /subscriptions/postpaid/plans/` — Retrieves available postpaid plans.
- `POST /subscriptions/postpaid/plans/{id}/activate/` — Activates a postpaid plan for a merchant.
- `GET /subscriptions/postpaid/active/` — Retrieves the current active postpaid subscription.
