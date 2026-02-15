# AX Merchant Portal - Backend Requirements & API Specification

## 📋 Executive Summary

Based on comprehensive analysis of the frontend (`MerchantPortal.jsx`), this document outlines the complete backend architecture needed to support the **Assured Express Merchant Portal** - a delivery management platform for Lagos-based merchants.

---

## 🎯 Core Features Identified

### 1. **Authentication & User Management**
- Merchant signup (3-step process)
- Login with phone + password
- JWT-based session management
- User profile management
- Business profile settings

### 2. **Wallet & Payment System**
- Wallet balance management
- Multiple funding methods:
  - Card payment (Paystack integration)
  - Bank transfer
  - USSD
  - LibertyPay (zero fee)
- Transaction history
- Wallet overdraft (future feature)
- Auto-debit for orders

### 3. **Order Management (Core Feature)**
Three delivery modes:
- **Quick Send**: Single pickup → single delivery
- **Multi-Drop**: Single pickup → multiple deliveries
- **Bulk Import**: Paste/upload/OCR → multiple deliveries

Order features:
- Real-time order creation
- Order tracking & status updates
- Order history & filtering
- Vehicle selection (Bike/Car/Van)
- Payment method selection (Wallet/Cash/Receiver Pays)
- Pricing calculation
- Order cancellation & refunds

### 4. **Instant Website Builder (My Website)**
- Create e-commerce sites (subdomain: `*.axpress.shop`)
- Product management
- Order pipeline integration
- Visitor analytics
- Revenue tracking
- Auto-create deliveries from website orders

### 5. **WebPOS Management Hub**
- Multi-branch POS instances
- Staff/clerk management with roles & permissions
- Sales tracking & reporting
- Payment method configuration
- Real-time sales monitoring
- Integration with delivery system

### 6. **Business Loans (Coming Soon)**
Three loan products:
- Merchant Line of Credit (revolving)
- Working Capital Loan (lump sum)
- Wallet Overdraft (auto-activate)
- Credit scoring based on merchant activity

### 7. **Accounting & Bookkeeping (Coming Soon)**
- Invoicing & billing
- Expense tracking
- Profit & loss reports
- Tax calculations
- Auto-import from AX deliveries, WebPOS, website orders

### 8. **Support & Help**
- FAQ system
- Support ticket creation
- Live chat integration
- Call support

---

## 🏗️ Backend Architecture Recommendation

### **Tech Stack Suggestion:**
- **Framework**: Node.js + Express.js OR Python + FastAPI/Django
- **Database**: PostgreSQL (relational data) + Redis (caching, sessions)
- **Payment**: Paystack API integration
- **Real-time**: Socket.io or WebSockets (order tracking)
- **File Storage**: AWS S3 or Cloudinary (bulk import files, receipts)
- **Authentication**: JWT + bcrypt
- **API Documentation**: Swagger/OpenAPI
- **Deployment**: Docker + AWS/GCP/Azure OR Vercel (serverless)

---

## 📡 API Endpoints Specification

### **1. Authentication & Users**

```
POST   /api/auth/signup              # Create merchant account
POST   /api/auth/login               # Login with phone + password
POST   /api/auth/logout              # Invalidate session
GET    /api/auth/me                  # Get current user profile
PUT    /api/auth/profile             # Update user profile
POST   /api/auth/reset-password      # Password reset
```

### **2. Wallet & Transactions**

```
GET    /api/wallet/balance           # Get current wallet balance
POST   /api/wallet/fund              # Initiate wallet funding
GET    /api/wallet/transactions      # Get transaction history
POST   /api/wallet/paystack-webhook  # Paystack payment webhook
GET    /api/wallet/funding-methods   # Get available funding methods
```

### **3. Orders (Core)**

```
POST   /api/orders                   # Create new order (quick/multi/bulk)
GET    /api/orders                   # List orders (with filters)
GET    /api/orders/:id               # Get order details
PUT    /api/orders/:id               # Update order
DELETE /api/orders/:id               # Cancel order
GET    /api/orders/:id/track         # Real-time tracking
POST   /api/orders/bulk-import       # Parse bulk delivery data
GET    /api/orders/pricing           # Calculate delivery price
```

### **4. Vehicles & Pricing**

```
GET    /api/vehicles                 # List available vehicles
GET    /api/pricing/calculate        # Calculate delivery cost
```

### **5. Website Builder**

```
POST   /api/websites                 # Create new website
GET    /api/websites                 # List merchant websites
GET    /api/websites/:id             # Get website details
PUT    /api/websites/:id             # Update website
DELETE /api/websites/:id             # Delete website
POST   /api/websites/:id/products    # Add product
GET    /api/websites/:id/analytics   # Get analytics
POST   /api/websites/:id/orders      # Create delivery from website order
```

### **6. WebPOS**

```
POST   /api/webpos/instances         # Create POS instance
GET    /api/webpos/instances         # List POS instances
POST   /api/webpos/staff             # Add staff member
GET    /api/webpos/sales             # Get sales data
GET    /api/webpos/reports           # Generate reports
```

### **7. Business Loans (Future)**

```
GET    /api/loans/products           # List loan products
POST   /api/loans/apply              # Apply for loan
GET    /api/loans/applications       # Get loan applications
GET    /api/loans/credit-score       # Get merchant credit score
```

### **8. Accounting (Future)**

```
POST   /api/accounting/invoices      # Create invoice
GET    /api/accounting/invoices      # List invoices
POST   /api/accounting/expenses      # Log expense
GET    /api/accounting/reports       # Generate P&L, tax reports
```

### **9. Support**

```
POST   /api/support/tickets          # Create support ticket
GET    /api/support/tickets          # List tickets
GET    /api/support/faq              # Get FAQs
```

---

## 🗄️ Database Schema (PostgreSQL)

### **Core Tables:**

#### **1. users (merchants)**
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  business_name VARCHAR(255) NOT NULL,
  contact_name VARCHAR(255) NOT NULL,
  phone VARCHAR(20) UNIQUE NOT NULL,
  email VARCHAR(255) UNIQUE NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  address TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  is_active BOOLEAN DEFAULT true,
  email_verified BOOLEAN DEFAULT false,
  phone_verified BOOLEAN DEFAULT false
);
```

#### **2. wallets**
```sql
CREATE TABLE wallets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  balance DECIMAL(12, 2) DEFAULT 0.00,
  currency VARCHAR(3) DEFAULT 'NGN',
  overdraft_limit DECIMAL(12, 2) DEFAULT 0.00,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id)
);
```

#### **3. transactions**
```sql
CREATE TABLE transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  wallet_id UUID REFERENCES wallets(id) ON DELETE CASCADE,
  type VARCHAR(20) NOT NULL, -- 'credit' or 'debit'
  amount DECIMAL(12, 2) NOT NULL,
  description TEXT,
  reference VARCHAR(100) UNIQUE,
  payment_method VARCHAR(50), -- 'card', 'transfer', 'ussd', 'liberty'
  status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'completed', 'failed'
  metadata JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### **4. orders**
```sql
CREATE TABLE orders (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_number VARCHAR(50) UNIQUE NOT NULL,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,

  -- Delivery mode
  mode VARCHAR(20) NOT NULL, -- 'quick', 'multi', 'bulk'

  -- Pickup details
  pickup_address TEXT NOT NULL,
  sender_name VARCHAR(255) NOT NULL,
  sender_phone VARCHAR(20) NOT NULL,

  -- Vehicle & pricing
  vehicle VARCHAR(20) NOT NULL, -- 'Bike', 'Car', 'Van'
  total_amount DECIMAL(10, 2) NOT NULL,

  -- Payment
  payment_method VARCHAR(20) NOT NULL, -- 'wallet', 'cash', 'receiver'
  payment_status VARCHAR(20) DEFAULT 'pending',

  -- Status tracking
  status VARCHAR(30) DEFAULT 'Pending',
  -- Pending, Assigned, Started, PickedUp, Done, CustomerCanceled, DriverCanceled, SupportCanceled

  -- Timestamps
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  scheduled_pickup TIMESTAMP,
  completed_at TIMESTAMP
);
```

#### **5. deliveries (for multi-drop & bulk)**
```sql
CREATE TABLE deliveries (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  order_id UUID REFERENCES orders(id) ON DELETE CASCADE,

  -- Delivery details
  dropoff_address TEXT NOT NULL,
  receiver_name VARCHAR(255) NOT NULL,
  receiver_phone VARCHAR(20) NOT NULL,
  notes TEXT,

  -- Status
  status VARCHAR(30) DEFAULT 'Pending',

  -- Sequence (for multi-drop)
  sequence_number INT,

  created_at TIMESTAMP DEFAULT NOW(),
  delivered_at TIMESTAMP
);
```

#### **6. vehicles**
```sql
CREATE TABLE vehicles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name VARCHAR(50) NOT NULL,
  max_weight_kg INT NOT NULL,
  base_price DECIMAL(10, 2) NOT NULL,
  price_per_km DECIMAL(10, 2),
  is_active BOOLEAN DEFAULT true
);

-- Seed data
INSERT INTO vehicles (name, max_weight_kg, base_price) VALUES
  ('Bike', 10, 1200),
  ('Car', 70, 4500),
  ('Van', 600, 12000);
```

#### **7. websites (Instant Web)**
```sql
CREATE TABLE websites (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  domain VARCHAR(255) UNIQUE NOT NULL, -- subdomain.axpress.shop
  status VARCHAR(20) DEFAULT 'draft', -- 'draft', 'live', 'suspended'
  theme_color VARCHAR(7) DEFAULT '#E8A838',
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### **8. products**
```sql
CREATE TABLE products (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  website_id UUID REFERENCES websites(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  price DECIMAL(10, 2) NOT NULL,
  stock INT DEFAULT 0,
  image_url TEXT,
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### **9. webpos_instances**
```sql
CREATE TABLE webpos_instances (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  domain VARCHAR(255) UNIQUE NOT NULL, -- subdomain.paybox360.com
  status VARCHAR(20) DEFAULT 'offline', -- 'online', 'offline'
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### **10. webpos_staff**
```sql
CREATE TABLE webpos_staff (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  instance_id UUID REFERENCES webpos_instances(id) ON DELETE CASCADE,
  name VARCHAR(255) NOT NULL,
  role VARCHAR(50) NOT NULL, -- 'Cashier', 'Supervisor', 'Manager'
  pin_hash VARCHAR(255) NOT NULL,
  status VARCHAR(20) DEFAULT 'active',
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🔐 Security Requirements

1. **Authentication**
   - JWT tokens with 24-hour expiry
   - Refresh tokens for extended sessions
   - Password hashing with bcrypt (10+ rounds)
   - Rate limiting on login attempts

2. **API Security**
   - HTTPS only in production
   - CORS configuration
   - Input validation & sanitization
   - SQL injection prevention (parameterized queries)
   - XSS protection

3. **Payment Security**
   - Paystack webhook signature verification
   - PCI DSS compliance (no card storage)
   - Transaction idempotency
   - Fraud detection

4. **Data Privacy**
   - GDPR/NDPR compliance
   - User data encryption at rest
   - Audit logs for sensitive operations

---

## 💳 Paystack Integration

### **Wallet Funding Flow:**

1. **Frontend**: User clicks "Fund Wallet" → selects amount & method
2. **Backend**:
   ```javascript
   POST /api/wallet/fund
   {
     "amount": 10000,
     "method": "card",
     "email": "merchant@example.com"
   }
   ```
3. **Backend** → **Paystack**: Initialize transaction
   ```javascript
   const response = await paystack.transaction.initialize({
     email: user.email,
     amount: amount * 100, // Convert to kobo
     callback_url: `${FRONTEND_URL}/wallet/verify`,
     metadata: {
       user_id: user.id,
       wallet_id: wallet.id
     }
   });
   ```
4. **Backend** → **Frontend**: Return authorization URL
5. **User** completes payment on Paystack
6. **Paystack** → **Backend**: Webhook notification
   ```javascript
   POST /api/wallet/paystack-webhook
   // Verify signature, update wallet balance, create transaction record
   ```

### **Webhook Handler:**
```javascript
app.post('/api/wallet/paystack-webhook', async (req, res) => {
  const hash = crypto
    .createHmac('sha512', PAYSTACK_SECRET_KEY)
    .update(JSON.stringify(req.body))
    .digest('hex');

  if (hash === req.headers['x-paystack-signature']) {
    const event = req.body;

    if (event.event === 'charge.success') {
      const { user_id, wallet_id } = event.data.metadata;
      const amount = event.data.amount / 100; // Convert from kobo

      // Update wallet balance
      await updateWalletBalance(wallet_id, amount);

      // Create transaction record
      await createTransaction({
        wallet_id,
        type: 'credit',
        amount,
        reference: event.data.reference,
        status: 'completed'
      });
    }
  }

  res.sendStatus(200);
});
```

---

## 📊 Real-Time Features (WebSockets)

### **Order Tracking:**
- Emit status updates to merchant when order status changes
- Driver location updates (if driver tracking implemented)
- Delivery completion notifications

### **Implementation:**
```javascript
// Server-side (Socket.io)
io.on('connection', (socket) => {
  socket.on('subscribe_order', (orderId) => {
    socket.join(`order_${orderId}`);
  });
});

// When order status changes
io.to(`order_${orderId}`).emit('order_update', {
  orderId,
  status: 'PickedUp',
  timestamp: new Date()
});
```

---

## 🚀 Deployment Checklist

### **Environment Variables:**
```env
# Database
DATABASE_URL=postgresql://user:pass@host:5432/axmerchant
REDIS_URL=redis://localhost:6379

# JWT
JWT_SECRET=your-secret-key
JWT_EXPIRY=24h

# Paystack
PAYSTACK_SECRET_KEY=sk_live_xxx
PAYSTACK_PUBLIC_KEY=pk_live_xxx

# Frontend URL
FRONTEND_URL=https://merchant.assuredexpress.com

# AWS S3 (for file uploads)
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx
AWS_S3_BUCKET=ax-merchant-uploads
```

### **Production Setup:**
1. Set up PostgreSQL database
2. Run migrations
3. Seed initial data (vehicles, FAQs)
4. Configure Paystack webhooks
5. Set up SSL certificates
6. Configure CORS for frontend domain
7. Set up monitoring (Sentry, LogRocket)
8. Configure backup strategy

---

## 📈 Scalability Considerations

1. **Database Optimization**
   - Index on frequently queried fields (user_id, order_number, status)
   - Partition large tables (orders, transactions) by date
   - Read replicas for analytics queries

2. **Caching Strategy**
   - Redis for session storage
   - Cache wallet balances (invalidate on transaction)
   - Cache vehicle pricing

3. **Queue System**
   - Bull/BullMQ for background jobs
   - Email notifications
   - Webhook retries
   - Report generation

4. **Rate Limiting**
   - API rate limits per user
   - Prevent abuse on order creation
   - Throttle wallet funding attempts

---

## 🧪 Testing Requirements

1. **Unit Tests**: All business logic functions
2. **Integration Tests**: API endpoints
3. **E2E Tests**: Critical user flows (signup, order creation, wallet funding)
4. **Load Tests**: Order creation under high load
5. **Security Tests**: Penetration testing, vulnerability scanning

---

## 📝 Next Steps

### **Phase 1: MVP (4-6 weeks)**
- [ ] Authentication & user management
- [ ] Wallet system with Paystack integration
- [ ] Quick Send order creation
- [ ] Order listing & tracking
- [ ] Basic dashboard

### **Phase 2: Advanced Orders (2-3 weeks)**
- [ ] Multi-Drop mode
- [ ] Bulk Import with CSV parsing
- [ ] Order cancellation & refunds
- [ ] Advanced filtering

### **Phase 3: Ecosystem (4-6 weeks)**
- [ ] Website Builder
- [ ] WebPOS integration
- [ ] Analytics & reporting

### **Phase 4: Financial Services (Future)**
- [ ] Business Loans
- [ ] Accounting module
- [ ] Credit scoring

---

## 🤝 Integration Points

### **External Services:**
1. **Paystack** - Payment processing
2. **Twilio/Termii** - SMS notifications
3. **SendGrid/Mailgun** - Email notifications
4. **Google Maps API** - Address validation, distance calculation
5. **Cloudinary/AWS S3** - File storage
6. **Sentry** - Error tracking
7. **Mixpanel/Amplitude** - Analytics

---

## 📞 Support & Documentation

- API Documentation: Swagger UI at `/api/docs`
- Postman Collection: Export for testing
- Developer Guide: Setup instructions
- Changelog: Version history

---

**Document Version**: 1.0
**Last Updated**: February 14, 2026
**Author**: Backend Planning Team

