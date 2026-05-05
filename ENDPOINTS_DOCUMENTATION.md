# Assured Express - Complete API & Endpoint Documentation

**Generated:** March 4, 2026
**Project:** Assured Express
**Integration:** ONRO Platform

---

## Table of Contents
1. [ONRO Integration Webhooks (Receive Data)](#onro-webhooks-receive-data)
2. [ONRO POST Endpoints (Send Data)](#onro-post-endpoints-send-data)
3. [ONRO Support & Management Endpoints](#onro-support--management-endpoints)
4. [Dashboard Endpoints](#dashboard-endpoints)
5. [Dashboard Analytics Endpoints](#dashboard-analytics-endpoints)
6. [Key Configuration Files](#key-configuration-files)
7. [Wallet Endpoints](#wallet-endpoints)
8. [Auth & Signup Endpoints](#auth--signup-endpoints)
9. [Subscription Endpoints](#subscription-endpoints)
10. [SmartParcel Locker Integration](#smartparcel-locker-integration)
11. [Dispatcher Orders](#dispatcher-orders)

---

## WALLET ENDPOINTS

### 1. Get Virtual Account
```
GET /wallet/virtual-account/
Description: Retrieves or creates a dedicated virtual account for the merchant to fund their wallet via bank transfer.
Authentication: Required (Merchant)
Response:
  {
    "success": true,
    "data": {
      "account_number": "7924567890",
      "account_name": "AXPRESS/JOHN DOE",
      "bank_name": "Wema Bank"
    }
  }
```

---

## AUTH & SIGNUP ENDPOINTS

### 1. Merchant Signup
```
POST /api/auth/signup/
Description: Register a new merchant account.
Request Body:
  {
    "email": "user@example.com",
    "password": "password123",
    "business_name": "My Business",
    "referral_code": "OPTIONAL_CODE"
  }
```

---

## SUBSCRIPTION ENDPOINTS

### 1. Get Subscription Plans
```
GET /subscriptions/plans/
Description: Retrieves all available subscription plans (Starter, Growth, Enterprise).
Authentication: Required (Merchant)
Response:
  {
    "status": "success",
    "data": [
      {
        "id": "uuid",
        "name": "Enterprise",
        "price": "75000.00",
        "free_orders_limit": 400,
        "overage_fee": "300.00",
        "has_dedicated_rider": true
      },
      ...
    ]
  }
```

### 2. Subscribe to a Plan
```
POST /subscriptions/plans/{plan_id}/subscribe/
Description: Subscribes the merchant to a specific plan.
Authentication: Required (Merchant)
Response:
  {
    "status": "success",
    "data": {
      "id": "uuid",
      "plan": { ... },
      "start_date": "...",
      "end_date": "...",
      "status": "active"
    }
  }
```

### 3. Get Postpaid Plans
```
GET /subscriptions/postpaid/plans/
Description: Retrieves all available postpaid subscription plans.
Authentication: Required (Merchant)
Response:
  {
    "status": "success",
    "data": [
      {
        "id": "uuid",
        "name": "Monthly Postpaid",
        "plan_type": "monthly",
        "is_active": true
      },
      ...
    ]
  }
```

### 4. Activate Postpaid Plan
```
POST /subscriptions/postpaid/plans/{plan_id}/activate/
Description: Activates a postpaid plan for the merchant.
Authentication: Required (Merchant)
Response:
  {
    "status": "success",
    "message": "Plan activated successfully"
  }
```

### 5. Get Active Postpaid Subscription
```
GET /subscriptions/postpaid/active/
Description: Retrieves the current active postpaid subscription details.
Authentication: Required (Merchant)
Response:
  {
    "status": "success",
    "data": {
       "id": "uuid",
       "name": "Monthly Postpaid",
       "status": "active"
    }
  }
```

### 3. Get Active Subscription
```
GET /subscriptions/active/
Description: Retrieves the merchant's current active subscription.
Authentication: Required (Merchant)
Response:
  {
    "status": "success",
    "data": {
      "subscriptions": [ ... ],
      "current_active": {
        "id": "uuid",
        "plan": { ... },
        "status": "active",
        "end_date": "..."
      }
    }
  }
```

---

## ONRO WEBHOOKS (RECEIVE DATA)

These endpoints receive real-time data from the ONRO platform:

### 1. Pickup & Delivery Orders Webhook
```
POST /onro/webhooks/pd-orders/
Handler: OnroUniversalWebhookView
File: onro_integration/webhook_handlers.py
Authentication: CSRF-exempt
Description: Receives pickup and delivery order events from ONRO
Data Storage: OnroOrder, OnroOrderDetail tables
```

### 2. On-Demand Orders Webhook
```
POST /onro/webhooks/ondemand-orders/
Handler: OnroUniversalWebhookView
File: onro_integration/webhook_handlers.py
Authentication: CSRF-exempt
Description: Receives on-demand order events from ONRO
Data Storage: OnroOrder, OnroOnDemandOrder tables
```

### 3. Driver Webhooks
```
POST /onro/webhooks/drivers/
Handler: OnroUniversalWebhookView
File: onro_integration/webhook_handlers.py
Authentication: CSRF-exempt
Description: Receives driver-related events from ONRO
```

### 4. Merchant Webhooks
```
POST /onro/webhooks/merchants/
Handler: OnroMerchantWebhookView
File: onro_integration/merchant_webhooks.py
Authentication: CSRF-exempt
Description: Receives merchant events from ONRO
Event Types:
  - Registered (New merchant registration)
  - Send password reset url
  - Send verification code
  - New withdraw request
  - Complete withdraw request
  - Reject withdraw request
```

### 5. Driver Location Webhook
```
POST /onro/driver-location-webhook/
Handler: OnroDriverLocationWebhookView
File: onro_integration/driver_tracking.py
Authentication: None (allows real-time location updates)
Description: Receives real-time driver location updates for active orders
```

---

## ONRO POST ENDPOINTS (SEND DATA)

These endpoints send operations to ONRO platform:

### Pickup & Delivery Orders

```
POST /onro/pd-orders/create/
Handler: File - onro_integration/order_views.py
Description: Create a new pickup and delivery order
Request Body: Order details (pickup location, delivery location, etc.)

POST /onro/pd-orders/draft/
Description: Save order as draft without confirming

POST /onro/pd-orders/confirm/
Description: Confirm a drafted order

POST /onro/pd-orders/calculate-price/
Description: Calculate order price before confirmation
Response: Estimated cost breakdown

POST /onro/pd-orders/cancel/
Description: Cancel an existing P&D order
Request Body: Order ID, cancellation reason

POST /onro/pd-orders/sync/
Description: Sync order data with ONRO
Response: Updated order status and details
```

### On-Demand Orders

```
POST /onro/ondemand-orders/create/
Handler: File - onro_integration/ondemand_views.py
Description: Create a new on-demand order
Request Body: Order details

POST /onro/ondemand-orders/calculate-price/
Description: Calculate on-demand order price

POST /onro/ondemand-orders/cancel/
Description: Cancel on-demand order

POST /onro/ondemand-orders/sync/
Description: Sync on-demand orders with ONRO
Response: All on-demand orders and their current status
```

---

## ONRO SUPPORT & MANAGEMENT ENDPOINTS

### Webhook & Sync Management

```
GET /onro/webhook-logs/
Description: View all webhook logs received from ONRO
Response: Paginated list of webhook events with timestamps and payloads

GET /onro/sync/logs/
Description: View sync operation logs
Response: History of sync operations, timestamps, statuses

POST /onro/sync/full/
Description: Trigger a complete data sync with ONRO
Response: Sync job ID, status, and statistics

POST /onro/cancellation-reasons/sync/
Description: Sync cancellation reasons from ONRO
Response: Updated list of available cancellation reasons

POST /onro/track-driver/
Description: Get real-time driver location
Request Body: Driver ID or Order ID
Response: Current GPS coordinates, last update time
```

---

## DASHBOARD ENDPOINTS

All dashboard endpoints return JSON responses with comprehensive analytics and metrics.

### Main Dashboard Views

```
GET /onro_integration/dashboard/
Handler: OnroDashboardView
Description: Basic dashboard overview
Response: Summary widgets and key metrics
```

### Order Dashboard

```
GET /onro_integration/order-dashboard/
Handler: OrderDashboardView
Description: Complete order pipeline and metrics
Response:
  - Total orders by status (pending, confirmed, in-transit, delivered, cancelled)
  - Order pipeline visualization
  - Average delivery time
  - Zone-wise order distribution
  - Order trends (hourly, daily, weekly)
Query Parameters:
  - date_filter: today, last_7_days, monthly, biannual, annual, custom_range
  - start_date / end_date: For custom date ranges
```

### Management Dashboard

```
GET /onro_integration/management-dashboard/
Handler: ManagementDashboardView
Description: Executive-level dashboard with comprehensive metrics
Response:
  - Revenue trends
  - Cost analysis
  - Profitability metrics
  - Key performance indicators
  - Team performance
```

### Rider Dashboard

```
GET /onro_integration/rider-dashboard/
Handler: RiderDashboardView
Description: Rider/driver management and performance
Response:
  - Rider tier distribution
  - GPS sync status
  - Performance metrics
  - Active vs inactive riders
  - Earnings summary
Query Parameters:
  - tier: Filter by rider tier
  - activity: Filter by activity status
  - page, page_size: For pagination
```

### Merchant Dashboard

```
GET /onro_integration/merchant-dashboard/
Handler: MerchantDashboardView
Description: Merchant analytics and intelligence
Response:
  - Merchant activity metrics
  - Credit score analysis
  - Transaction history
  - Merchant growth trends
```

### COD Dashboard

```
GET /onro_integration/cod-dashboard/
Handler: CODDashboardView
Description: Cash on Delivery tracking and reconciliation
Response:
  - COD collection status
  - Settlement details
  - Pending reconciliations
  - Dispute logs
```

### Financial P&L Dashboard

```
GET /onro_integration/financial-pl-dashboard/
Handler: FinancialPLDashboardView
Description: Financial Profit & Loss analysis
Response:
  - Revenue breakdown by source
  - Cost categories
  - Profit/Loss trends
  - Monthly P&L statements
Query Parameters:
  - tab: revenue, expenses, profit, summary
  - date_filter: Time period filter
```

### Fleet Management Dashboard

```
GET /onro_integration/fleet-management-dashboard/
Handler: FleetManagementDashboardView
Description: Fleet and vehicle management with GPS tracking
Response:
  - Fleet status overview
  - Vehicle maintenance schedule
  - GPS real-time tracking
  - Bike utilization rates
  - Fuel consumption analysis
```

### Fraud Alert Dashboard

```
GET /onro_integration/fraud-alert-dashboard/
Handler: FraudAlertDashboardView
Description: Fraud detection and alert management
Response:
  - Active fraud alerts
  - Risk assessment scores
  - Triggering metrics
  - Alert history
  - Recommended actions
```

### On-Demand Order Dashboard

```
GET /onro_integration/ondemand-orders/dashboard/
Handler: OnDemandOrderDashboardView
Description: On-demand specific order metrics
Response: On-demand order analytics and pipeline
```

---

## DASHBOARD ANALYTICS ENDPOINTS

Advanced analytics endpoints for super admin:

### Analytics API

```
POST /onro_integration/admin-dashboard/analytics/
Handler: AnalyticsAPIView
Description: Flexible custom analytics based on parameters
Request Body:
  {
    "metric": "revenue|orders|drivers|merchants",
    "date_range": "today|week|month|custom",
    "start_date": "2026-03-01",
    "end_date": "2026-03-04",
    "group_by": "daily|weekly|monthly|zone",
    "status_filter": "all|completed|pending|cancelled"
  }
Response: Custom analytics data formatted as requested
Example Response:
  {
    "total": 15000,
    "average": 500,
    "trend": "increasing",
    "data_points": [...],
    "summary": {...}
  }
```

### Chart Data API

```
POST /onro_integration/admin-dashboard/charts/
Handler: ChartDataAPIView
Description: Pre-formatted chart data for frontend visualization
Request Body:
  {
    "chart_type": "pie|bar|line",
    "metric": "orders|revenue|riders",
    "period": "month|week|day"
  }
Response: Chart-ready data with labels, values, colors
Supported Formats:
  - Pie Charts: Category distribution
  - Bar Charts: Comparative metrics
  - Line Charts: Trends over time
```

### Real-Time Data API

```
GET /onro_integration/admin-dashboard/realtime/
Handler: RealTimeDataAPIView
Description: Real-time dashboard updates
Query Parameters:
  - last_update: Timestamp to get updates since
Response:
  {
    "last_update": "2026-03-04T10:30:00Z",
    "active_orders": 250,
    "active_drivers": 45,
    "online_merchants": 127,
    "current_revenue": 5500,
    "updates": [...]
  }
```

### Export Data API

```
POST /onro_integration/admin-dashboard/export/
Handler: ExportDataAPIView
Description: Export dashboard data as CSV or JSON
Request Body:
  {
    "format": "csv|json",
    "report_type": "orders|riders|merchants|financial",
    "date_range": "custom",
    "start_date": "2026-03-01",
    "end_date": "2026-03-04"
  }
Response: File download with report data
File Format: CSV with headers or JSON structure
```

### Health Check API

```
GET /onro_integration/admin-dashboard/health/
Handler: DashboardHealthAPIView
Description: System health status and diagnostics
No Parameters Required
Response:
  {
    "status": "healthy|warning|error",
    "database": {
      "connected": true,
      "response_time_ms": 45
    },
    "cache": {
      "status": "active",
      "hit_rate": 0.87
    },
    "uptime_seconds": 1234567,
    "last_sync": "2026-03-04T10:25:00Z",
    "webhook_queue": 0
  }
```

---

## Common Query Parameters

These parameters are supported across most dashboard endpoints:

| Parameter | Values | Description |
|-----------|--------|-------------|
| `date_filter` | today, last_7_days, monthly, biannual, annual, custom_range | Time period to filter data |
| `start_date` | YYYY-MM-DD | Start date for custom range |
| `end_date` | YYYY-MM-DD | End date for custom range |
| `page` | Integer | Pagination page number (starts from 1) |
| `page_size` | Integer | Number of items per page |
| `status` | Specific values | Filter by status (pending, completed, cancelled, etc.) |
| `tier` | Specific values | Filter by tier/category |
| `activity` | active, inactive | Filter by activity status |
| `tab` | Specific values | For multi-tab dashboards (revenue, expenses, etc.) |

---

## Key Configuration Files

### Backend Files (Python/Django)

```
onro_integration/
├── webhook_handlers.py
│   └── OnroUniversalWebhookView, OnroWebhookEventListener
├── merchant_webhooks.py
│   └── OnroMerchantWebhookView
├── driver_tracking.py
│   └── OnroDriverLocationWebhookView
├── order_views.py
│   └── P&D order CRUD endpoints
├── ondemand_views.py
│   └── On-demand order endpoints
├── dashboard_views.py (3,133 lines)
│   ├── SuperAdminDashboardView
│   ├── OrderDashboardView
│   ├── RiderDashboardView
│   ├── MerchantDashboardView
│   ├── ManagementDashboardView
│   ├── CODDashboardView
│   ├── FinancialPLDashboardView
│   ├── FleetManagementDashboardView
│   ├── FraudAlertDashboardView
│   ├── AnalyticsAPIView
│   ├── ChartDataAPIView
│   ├── RealTimeDataAPIView
│   ├── ExportDataAPIView
│   └── DashboardHealthAPIView
├── dashboard_serializers.py
│   └── Data validation and serialization
├── dashboard_utils.py
│   └── Analytics calculation utilities
├── dashboard_tasks.py
│   └── Celery async tasks
└── urls.py
    └── All route definitions (lines 126-143 for dashboards)
```

### Frontend Files (TypeScript/React)

```
frontend/pages/
├── scheduler/dashboard.tsx
│   └── Scheduler dashboard UI
└── dispatcher/dashboard.tsx
    └── Dispatcher dashboard UI
```

---

## Authentication & Security

**CSRF Settings:**
- All webhook endpoints: `csrf_exempt = True` (allows ONRO to POST without CSRF token)
- Dashboard endpoints: Protected by Django session authentication
- API endpoints: May require authentication tokens or session cookies

**Rate Limiting:**
- Webhook endpoints: No rate limiting (to ensure no data loss)
- Dashboard endpoints: Standard Django rate limiting
- Export endpoints: May have concurrent request limits

---

## Response Format

All endpoints return JSON responses. Standard response format:

### Success Response
```json
{
  "status": "success",
  "data": { /* endpoint-specific data */ },
  "timestamp": "2026-03-04T10:30:00Z",
  "message": "Optional success message"
}
```

### Error Response
```json
{
  "status": "error",
  "error": "Error code or message",
  "details": "Detailed error description",
  "timestamp": "2026-03-04T10:30:00Z"
}
```

---

## Testing Webhooks

To test webhook integration:

1. **Merchant Webhook Test:**
   ```
   POST /onro/webhooks/merchants/
   Content-Type: application/json

   {
     "event_type": "Registered",
     "merchant_id": "MERCHANT_123",
     "timestamp": "2026-03-04T10:30:00Z"
   }
   ```

2. **Order Webhook Test:**
   ```
   POST /onro/webhooks/pd-orders/
   Content-Type: application/json

   {
     "event_type": "order_created",
     "order_id": "ORD_123",
     "timestamp": "2026-03-04T10:30:00Z"
   }
   ```

---

## Performance Optimization Tips

1. **Dashboard Caching:** Most dashboard data is cached for 5 minutes for better performance
2. **Pagination:** Use `page` and `page_size` parameters to limit data volume
3. **Date Filtering:** Always specify `date_filter` to reduce query load
4. **Async Tasks:** Use Celery tasks for heavy data export operations
5. **Real-time Updates:** Use the `/realtime/` endpoint for incremental updates instead of full dashboard refreshes

---

## Support & Troubleshooting

**Webhook Issues:**
- Check `/onro/webhook-logs/` for recent webhook events
- Verify ONRO server can reach your endpoint
- Check firewall/NAT rules

**Dashboard Performance:**
- Check `/admin-dashboard/health/` for system status
- Review database response times
- Clear cache if data seems stale

**Data Sync Issues:**
- Use `POST /onro/sync/full/` to trigger full sync
- Check `/onro/sync/logs/` for sync history
- Verify API credentials in ONRO settings

---

**Last Updated:** March 28, 2026
**Version:** 1.1
**Recent Changes:** Added "Rider Earning" to Order Admin and fixed tiered pricing calculation logic in the merchant frontend to support 4+ tiers.
**Document Type:** API Reference Documentation

For more information, refer to individual view implementations in the source files listed above.

---

## SMARTPARCEL LOCKER INTEGRATION

This suite of endpoints manages integration with the SmartParcel locker network.

### 1. List States
```
GET /api/orders/smart-parcel/states/
Description: Retrieves all states where SmartParcel operates.
Authentication: Required (Merchant)
```

### 2. List Cities by State
```
GET /api/orders/smart-parcel/states/{state_id}/cities/
Description: Retrieves all cities for a specific SmartParcel state.
Authentication: Required (Merchant)
```

### 3. List Boxes by City
```
GET /api/orders/smart-parcel/boxes/city/{city_id}/
Description: Retrieves all available SmartParcel boxes in a city.
Authentication: Required (Merchant)
```

### 4. List Assigned Boxes by City
```
GET /api/orders/smart-parcel/boxes/assigned/city/{city_id}/
Description: Retrieves SmartParcel boxes assigned to the merchant in a city.
Authentication: Required (Merchant)
```

### 5. Get Box Details
```
GET /api/orders/smart-parcel/boxes/{box_id}/
Description: Retrieves details for a specific SmartParcel box.
Authentication: Required (Merchant)
```

### 6. List Locker Sizes
```
GET /api/orders/smart-parcel/locker-sizes/
Description: Retrieves all available locker sizes on the network.
Authentication: Required (Merchant)
```

### 7. Create Parcel
```
POST /api/orders/smart-parcel/parcels/
Description: Create a new SmartParcel parcel for locker pickup/delivery.
Authentication: Required (Merchant)
```

### 8. List Pending Pickups
GET /api/orders/smart-parcel/parcels/pending-pickups/
Description: Retrieves SmartParcel parcels awaiting pickup.
Authentication: Required (Merchant)

---

## MERCHANT ORDERS

### 1. Cancel Order
```
POST /api/orders/cancel/{order_number}/
Description: Cancels an active order and processes refunds if applicable.
Authentication: Required (Merchant)
Request Body:
  {
    "reason": "Customer requested cancellation" (Optional)
  }
Response:
  {
    "status": "success",
    "message": "Order 6158001 has been canceled",
    "data": {
      "order": {
        "order_number": "6158001",
        "old_status": "Pending",
        "new_status": "CustomerCanceled",
        "payment_method": "wallet",
        "total_amount": 2500.00,
        "canceled_at": "2026-05-04T15:00:00Z"
      },
      "refund": {
        "processed": true,
        "amount": 2500.00,
        "reason": "Customer requested cancellation"
      }
    }
  }
```

---

## DISPATCHER ORDERS

### 1. Create Order
```
POST /dispatch/orders/
Description: Creates a new order manually from the dispatcher portal.
Authentication: Required (Dispatcher)
Request Body:
  {
    "pickup": "Pickup Address",
    "dropoff": "Dropoff Address",
    "senderName": "Sender Name",
    "senderPhone": "08012345678",
    "receiverName": "Receiver Name",
    "receiverPhone": "08087654321",
    "vehicle": "Bike",
    "packageType": "Box",
    "price": 2500.00,
    "cod": 0.00,
    "riderId": "RIDER_UUID",
    "merchantId": "MERCHANT_UUID",
    "is_partner_order": true,
    "partner_order_count": 10,
    "file_uploaded_urls": [
      "https://example.com/image1.jpg",
      "https://example.com/image2.jpg"
    ]
  }
Response: Created Order object.
```

### 2. Update Partner Stats
```
PATCH /dispatch/orders/{order_number}/update-partner-stats/
Description: Updates processing metrics for a partner bulk order.
Authentication: Required (Dispatcher)
Request Body:
  {
    "rider_completed_count": 50,
    "day_returned_count": 2
  }
Response: Updated Order object.
```

### 3. Update Order Status
```
POST /dispatch/orders/{order_number}/update_status/
Description: Updates the status of an order (e.g., In Transit, Delivered, Cancelled).
Authentication: Required (Dispatcher)
Request Body:
  {
    "status": "Cancelled",
    "reason": "Customer changed their mind" (Optional, used for cancellation)
  }
Response:
  {
    "status": "success",
    "message": "Order status updated to CustomerCanceled",
    "data": {
      "id": "6158001",
      "status": "CustomerCanceled",
      "cancellation_reason": "Customer changed their mind",
      ...
    }
  }
```
```
GET /api/orders/smart-parcel/parcels/pending-pickups/
Description: Retrieves all pending parcels ready for pickup from the SmartParcel network.
Authentication: Required (Merchant)
```

### 9. Resolve Collect Code
```
GET /api/orders/smart-parcel/parcels/resolve-collect-code/{collect_code}/
Description: Resolves a collect code to a pending parcel for pickup.
Authentication: Required (Merchant)
```

### 10. Get Parcel Details
```
GET /api/orders/smart-parcel/parcels/{tracking_number}/
Description: Retrieves full details for a SmartParcel parcel.
Authentication: Required (Merchant)
```

### 11. Cancel Parcel
```
POST /api/orders/smart-parcel/parcels/{tracking_number}/cancel/
Description: Cancels an existing SmartParcel parcel.
Authentication: Required (Merchant)
```

### 12. Simulate Drop Parcel (Sandbox Only)
```
POST /api/orders/smart-parcel/locker/simulate/drop/
Description: Triggers a simulated "dropped" state for a parcel in sandbox mode.
Authentication: Required (Merchant)
Request Body:
  {
    "box_id": "14",
    "unlock_code": "CJ95"
  }
```

### 13. Simulate Collect Parcel (Sandbox Only)
```
POST /api/orders/smart-parcel/locker/simulate/collect/
Description: Triggers a simulated "collected" state for a parcel in sandbox mode.
Authentication: Required (Merchant)
Request Body:
  {
    "box_id": "14",
    "unlock_code": "J6E7"
  }
```

---

## DISPATCHER MERCHANTS

### 1. List Merchants
```
GET /merchants/
Description: Retrieves a list of all merchants.
Authentication: Required (Dispatcher)
Response: Paginated list of Merchant objects.
```

### 2. Deactivate Merchant
```
DELETE /merchants/{id}/
Description: Soft-deactivates a merchant account.
Authentication: Required (Dispatcher Admin)
Response:
  {
    "status": "success",
    "message": "Merchant deactivated successfully."
  }
```
