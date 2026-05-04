# Changelog

All notable changes to the AXpress project are documented in this file.

---

## [2026-04-29] — Multiple Image Upload in Dispatcher Portal

### Frontend
#### Added
- **Multiple Image Selection**: Enhanced the "Create Order" modal to support selecting and uploading multiple images simultaneously.
- **Image Previews**: Added a grid view for uploaded images with the ability to remove individual files before submission.
- **Improved Order Details**: Updated the Order Details view to display all uploaded documents.

#### Changed
- **API Payload**: Updated the dispatcher create order payload to send `file_uploaded_urls` as a list of strings.

## [2026-04-23] — Partner Order Tracking & Management

### Frontend
#### Added
- **Partner Details View**: Integrated a premium partner information card in the Order Detail modal.
- **Document Preview**: Added high-fidelity preview for uploaded proof/waybill documents with full-size viewing support.
- **Processing Metrics Editing**: Enabled inline editing for `Rider Completed` and `Returned` counts for partner bulk orders.
- **Real-time Synchronization**: Added `useEffect` hooks to ensure partner metrics are correctly loaded and reset during order navigation.

### API
#### Added
- **Order Stats Update**: Added `PATCH /dispatch/orders/{order_number}/update-partner-stats/` to update partner processing counts.
- **Serializer Expansion**: Updated `OrderSerializer` to include `is_partner_order`, `partner_order_count`, `day_returned_count`, `rider_completed_count`, and `file_uploaded_url`.
- **Merchant Access Control**: Restricted `MerchantViewSet` list action to `IsDispatcher` permission and other actions to `IsDispatcherAdmin`.

---

## [2026-04-22] — ClickUp Task Logging Automation

### Chore
- **ClickUp Logger**: Implemented a Python script `scripts/clickup_logger.py` to automate task logging to ClickUp.
- **Session Tracking**: Added `.claude/session_log.json` to track and batch-log development tasks.
- **Auto-routing**: Implemented keyword-based routing to automatically assign tasks to the correct ClickUp Lists.

---

## [2026-04-16] — SmartParcel Toggle Fix

### Frontend
#### Fixed
- **SmartParcel Toggle**: Resolved a `TypeError` that occurred when toggling "Deliver to SmartParcel Locker" by ensuring that data fetched from the SmartParcel API is always treated as an array before mapping.
- **Robust Data Fetching**: Updated `useEffect` hooks to correctly extract lists (states, cities, boxes, sizes) from backend responses and added defensive array checks in the render logic.
---

## [2026-04-17] — SmartParcel Integration & Simulation

### API
#### Added
- **SmartParcel Simulation**: Added `simulate/drop/` and `simulate/collect/` endpoints to simulate locker state transitions in sandbox mode for end-to-end testing of the locker workflow.
- **SmartParcel Integration**: Implemented comprehensive suite of endpoints for SmartParcel locker integration:
  - `GET smart-parcel/states/`
  - `GET smart-parcel/states/{id}/cities/`
  - `GET smart-parcel/boxes/city/{id}/`
  - `GET smart-parcel/boxes/assigned/city/{id}/`
  - `GET smart-parcel/locker-sizes/`
  - `POST smart-parcel/parcels/`
  - `GET smart-parcel/parcels/pending-pickups/`
  - `GET smart-parcel/parcels/resolve-collect-code/{code}/`
  - `GET smart-parcel/parcels/{tracking}/`
  - `POST smart-parcel/parcels/{tracking}/cancel/`

### Frontend
#### Added
- **SmartParcel Locker Workflow**: Integrated SmartParcel locker selection and collect code resolution directly into the Order Creation flow in the dashboard.
- **Defensive guards**: Added defensive null guards for SmartParcel data arrays to prevent runtime crashes during API latency or failures.

## [2026-04-02] — Order Mode Redesign & Grouped Pricing Fix


### Frontend
#### Changed
- **Order Mode Selector**: Redesigned the "Quick vs Grouped" sub-mode selection from a standard dropdown to modern, interactive cards with icons and premium aesthetics.
- **Grouped Pricing Fix**: Resolved a bug where "Grouped Order" failed to trigger route calculation and estimation.
- **Payload Fix**: Ensured the `mode` field ("quick" or "grouped") is correctly included in the API payload when placing an order.
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
