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

**Last Updated:** March 4, 2026
**Version:** 1.0
**Document Type:** API Reference Documentation

For more information, refer to individual view implementations in the source files listed above.
