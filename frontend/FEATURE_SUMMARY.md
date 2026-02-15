# AX Merchant Portal - Feature Summary

## 🎯 Overview

The **Assured Express Merchant Portal** is a comprehensive delivery management platform for Lagos-based merchants. Based on analysis of the frontend (`MerchantPortal.jsx` - 3,472 lines), here's a complete breakdown of all features.

---

## ✅ Core Features (MVP - Ready for Backend)

### 1. **Authentication & User Management**
- **Signup Flow**: 3-step process
  - Step 1: Business details (name, phone, email, password)
  - Step 2: Business address
  - Step 3: Confirmation & welcome
- **Login**: Phone + password authentication
- **Profile Management**: Update business info, contact details
- **Session Management**: JWT-based authentication

**Frontend Components:**
- `LoginScreen` (lines 437-521)
- `SignupScreen` (lines 524-637)
- `SettingsScreen` (lines 1741-1786)

---

### 2. **Wallet System** ⭐ CRITICAL

**Features:**
- Real-time balance display
- Multiple funding methods:
  - 💳 Card (Paystack)
  - 🏦 Bank Transfer
  - 📱 USSD (*737#)
  - ⚡ LibertyPay (zero fee)
- Transaction history with filters
- Quick-fund presets (₦1K, ₦2K, ₦5K, ₦10K, ₦20K, ₦50K)
- Auto-debit for wallet-paid orders

**Payment Flow:**
1. User selects amount & method
2. Backend initializes Paystack transaction
3. User completes payment on Paystack
4. Webhook updates wallet balance
5. Transaction recorded in history

**Frontend Components:**
- `WalletScreen` (lines 1585-1669)
- `FundWalletModal` (lines 1672-1737)

**Mock Data:**
- Initial balance: ₦8,790
- 6 sample transactions (lines 137-144)

---

### 3. **Order Management** ⭐ CRITICAL

**Three Delivery Modes:**

#### **A. Quick Send** (Single Delivery)
- One pickup → one dropoff
- Simple form: pickup address, dropoff address, receiver details
- Notes field for driver instructions

#### **B. Multi-Drop** (One-to-Many)
- One pickup → multiple dropoffs
- Add/remove deliveries dynamically
- Numbered sequence for delivery order
- Each delivery has: address, receiver name, phone, notes

#### **C. Bulk Import** (Batch Processing)
- Three input methods:
  - 📸 **Snap & Send**: Camera OCR (simulated)
  - 📄 **Upload File**: CSV/Excel/photo
  - ✏️ **Type/Paste**: Text parser
- Editable table view of parsed deliveries
- Format: `Address | Name | Phone | Notes`

**Shared Features:**
- Pickup location presets (🏢 Office, 📦 Warehouse, 🏪 Shop)
- Vehicle selection (Bike/Car/Van) with pricing
- Payment method:
  - Wallet (prepaid)
  - Cash on Pickup
  - Receiver Pays
- Two-step flow: Form → Review & Confirm
- Real-time cost calculation
- Sticky bottom summary

**Order Tracking:**
- Order list with filters (All, Active, Completed, Canceled)
- Order detail view with status timeline
- Status badges with color coding
- Copy order ID functionality

**Frontend Components:**
- `NewOrderScreen` (lines 748-1434)
- `OrdersScreen` (lines 1437-1582)

**Mock Data:**
- 5 sample orders (lines 129-135)
- Status types: Pending, Assigned, Started, PickedUp, Done, Canceled

**Pricing:**
- Bike: ₦1,200 (up to 10kg)
- Car: ₦4,500 (up to 70kg)
- Van: ₦12,000 (up to 600kg)

---

### 4. **Dashboard**

**Metrics Cards:**
- Wallet Balance (with Fund button)
- Orders This Month (total, delivered, active)
- Total Spent
- Average Delivery Cost

**Quick Actions:**
- Send Package
- Fund Wallet
- Track Order
- Get Support

**Recent Orders:**
- Last 4 orders with status
- Click to view details

**Frontend Component:**
- `DashboardScreen` (lines 640-745)

---

## 🚀 Advanced Features (Phase 2)

### 5. **My Website** (Instant E-commerce)

**Features:**
- Create instant e-commerce sites
- Subdomain: `businessname.axpress.shop`
- Product management (add, edit, delete)
- Order pipeline integration
- Analytics dashboard:
  - Visitors
  - Orders
  - Revenue
  - Products count
- Auto-create deliveries from website orders
- Theme customization (color picker)

**Frontend Component:**
- `WebsiteScreen` (lines 1833-2239)

**Mock Data:**
- 2 demo sites (Vivid Print Main, Vivid Print Lekki)
- 4 demo products (Business Cards, Flyers, Banners, Invoice Books)

---

### 6. **WebPOS** (Point of Sale Management)

**Features:**
- Multi-branch POS instances
- Subdomain: `businessname.paybox360.com`
- Staff/clerk management:
  - Roles: Cashier, Supervisor, Manager
  - PIN-based access
  - Permission levels
- Sales tracking & reporting:
  - Today's sales & revenue
  - Weekly revenue
  - Top performers
- Payment methods:
  - Cash, Card, Transfer, Split Payment
- Real-time status (online/offline)
- Transaction history

**Frontend Component:**
- `WebPOSScreen` (lines 2242-2833)

**Mock Data:**
- 3 POS instances (Seeds & Pennies HQ, Lekki, Liberty Ikeja)
- 4 staff members
- 8 recent sales

---

## 🔮 Future Features (Coming Soon)

### 7. **Business Loans**

**Three Loan Products:**

#### **A. Merchant Line of Credit**
- Revolving credit up to ₦10M
- Rate: From 2.5%/month
- Pre-approved based on AX transaction history
- Draw funds anytime, pay interest only on usage
- Auto-repay from sales or wallet

#### **B. Working Capital Loan**
- Lump sum: ₦500K – ₦25M
- Rate: From 3%/month
- Tenure: 3-12 months
- Fixed monthly/weekly repayments
- For inventory, equipment, expansion

#### **C. Wallet Overdraft**
- Up to ₦1M
- Rate: From 0.1%/day
- Auto-activates when wallet hits zero
- Auto-repays on next wallet funding
- No application needed

**Credit Scoring:**
- Based on delivery volume
- Wallet transaction history
- Payment patterns
- On-time repayments

**Frontend Component:**
- `BusinessLoansScreen` (lines 2836-3109)

---

### 8. **Accounting & Bookkeeping**

**Modules:**

#### **A. Invoicing & Billing**
- Create branded invoices
- Auto-create from WebPOS/website orders
- Send via WhatsApp, SMS, email
- Track paid, pending, overdue
- Recurring invoices
- Partial payments

#### **B. Expense Tracking**
- Categorized expenses
- Receipt scanning (camera)
- Auto-import AX delivery costs
- Budget limits & alerts
- Vendor payment tracking
- Monthly breakdown with charts

#### **C. Profit & Loss Reports**
- Revenue tracking
- Expense categorization
- Tax calculations
- Visual charts & graphs

#### **D. Auto-Integration**
- AX deliveries → expense log
- WebPOS sales → revenue
- Website orders → revenue
- Wallet transactions → reconciliation

**Frontend Component:**
- `AccountingScreen` (lines 3112-3471)

---

## 🎨 UI/UX Highlights

**Design System:**
- **Colors**: Navy (#1B2A4A), Gold (#E8A838), Green, Red, Blue
- **Typography**: DM Sans (body), Space Mono (numbers)
- **Components**: Cards, modals, badges, buttons
- **Animations**: Fade-in transitions, hover effects
- **Responsive**: Mobile sidebar, desktop layout

**Key UI Patterns:**
- Sticky bottom summary (order creation)
- Modal overlays (fund wallet)
- Status badges with color coding
- Quick-pick presets (addresses, amounts)
- Inline editing (bulk import table)
- Real-time validation
- Toast notifications

---

## 📊 Data Requirements

**User Data:**
- Business name, contact name, phone, email, address
- Hardcoded example: "Vivid Print" / "Yetunde Igbene" / "08051832508"

**Order Data:**
- Order ID, status, pickup, dropoff, amount, date, vehicle, merchant
- Delivery details: address, receiver name, phone, notes

**Transaction Data:**
- ID, type (credit/debit), amount, description, reference, date, balance

**Vehicle Data:**
- Name, max weight, base price

---

## 🔗 Integration Points

**Required External Services:**
1. **Paystack** - Payment processing (CRITICAL)
2. **SMS Provider** - Order notifications
3. **Email Service** - Invoices, receipts
4. **Google Maps API** - Address validation, distance calculation
5. **File Storage** - Bulk import files, receipts, product images
6. **WebSocket Server** - Real-time order updates

---

## 📱 Support Features

**Help & Support:**
- FAQ section (5 common questions)
- Call support button
- WhatsApp support
- Support ticket creation (future)

**Frontend Component:**
- `SupportScreen` (lines 1789-1830)

---

## 🎯 Priority Ranking for Backend Development

### **Phase 1: MVP (Must Have)**
1. ✅ Authentication (signup, login, JWT)
2. ✅ Wallet system + Paystack integration
3. ✅ Quick Send order creation
4. ✅ Order listing & tracking
5. ✅ Dashboard metrics

### **Phase 2: Core Features**
6. ✅ Multi-Drop mode
7. ✅ Bulk Import with CSV parsing
8. ✅ Transaction history
9. ✅ Order cancellation & refunds

### **Phase 3: Ecosystem**
10. ✅ Website Builder
11. ✅ WebPOS integration
12. ✅ Analytics & reporting

### **Phase 4: Financial Services**
13. ⏳ Business Loans
14. ⏳ Accounting module
15. ⏳ Credit scoring

---

## 📈 Success Metrics

**Key Performance Indicators:**
- Daily active merchants
- Orders created per day
- Wallet funding volume
- Average order value
- Delivery completion rate
- Customer satisfaction score

---

**Total Lines of Code**: 3,472 lines  
**Total Screens**: 10 main screens  
**Total Features**: 8 major feature sets  
**Mock Orders**: 5 sample orders  
**Mock Transactions**: 6 sample transactions

