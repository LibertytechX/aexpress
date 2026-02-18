// React hooks will be available from the global React object
const { useState, useEffect, useRef } = React;

// ─── ICONS (inline SVG components) ──────────────────────────────
const Icons = {
  dashboard: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
    </svg>
  ),
  orders: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M16 16h6"/><path d="M19 13v6"/><path d="M21 10V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l2-1.14"/><path d="m7.5 4.27 9 5.15"/><polyline points="3.29 7 12 12 20.71 7"/><line x1="12" y1="22" x2="12" y2="12"/>
    </svg>
  ),
  wallet: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12V7H5a2 2 0 0 1 0-4h14v4"/><path d="M3 5v14a2 2 0 0 0 2 2h16v-5"/><path d="M18 12a2 2 0 0 0 0 4h4v-4Z"/>
    </svg>
  ),
  newOrder: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/><path d="M8 12h8"/><path d="M12 8v8"/>
    </svg>
  ),
  settings: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>
    </svg>
  ),
  support: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>
    </svg>
  ),
  logout: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
    </svg>
  ),
  menu: (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="4" y1="12" x2="20" y2="12"/><line x1="4" y1="6" x2="20" y2="6"/><line x1="4" y1="18" x2="20" y2="18"/>
    </svg>
  ),
  close: (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
    </svg>
  ),
  arrowUp: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="m18 15-6-6-6 6"/>
    </svg>
  ),
  arrowDown: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <path d="m6 9 6 6 6-6"/>
    </svg>
  ),
  bike: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="18.5" cy="17.5" r="3.5"/><circle cx="5.5" cy="17.5" r="3.5"/><circle cx="15" cy="5" r="1"/><path d="M12 17.5V14l-3-3 4-3 2 3h2"/>
    </svg>
  ),
  car: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2"/><circle cx="7" cy="17" r="2"/><path d="M9 17h6"/><circle cx="17" cy="17" r="2"/>
    </svg>
  ),
  van: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M14 18V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2v11a1 1 0 0 0 1 1h2"/><path d="M15 18h2"/><path d="M19 18h2a1 1 0 0 0 1-1v-3.65a1 1 0 0 0-.22-.624l-3.48-4.35A1 1 0 0 0 17.52 8H14"/><circle cx="7" cy="18" r="2"/><circle cx="19" cy="18" r="2"/>
    </svg>
  ),
  pin: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5c-1.38 0-2.5-1.12-2.5-2.5s1.12-2.5 2.5-2.5 2.5 1.12 2.5 2.5-1.12 2.5-2.5 2.5z"/>
    </svg>
  ),
  clock: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>
    </svg>
  ),
  check: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20 6 9 17 4 12"/>
    </svg>
  ),
  copy: (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
    </svg>
  ),
  search: (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
    </svg>
  ),
  mail: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>
    </svg>
  ),
  checkCircle: (
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>
    </svg>
  ),
  xCircle: (
    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
    </svg>
  ),
  bell: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>
    </svg>
  ),
  website: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/><path d="M2 12h20"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>
    </svg>
  ),
  webpos: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="3" width="20" height="14" rx="2"/><line x1="8" y1="21" x2="16" y2="21"/><line x1="12" y1="17" x2="12" y2="21"/><path d="M6 8h.01"/><path d="M10 8h.01"/><path d="M14 8h.01"/>
    </svg>
  ),
  loans: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M2 17a5 5 0 0 1 10 0c0 2.76-2.24 5-5 5s-5-2.24-5-5Z"/><path d="M12 17a5 5 0 0 1 10 0c0 2.76-2.24 5-5 5s-5-2.24-5-5Z"/><path d="M7 1v4"/><path d="M17 1v4"/><path d="M12 9V1"/>
    </svg>
  ),
  accounting: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="4" y="2" width="16" height="20" rx="2"/><line x1="8" y1="6" x2="16" y2="6"/><line x1="8" y1="10" x2="16" y2="10"/><line x1="8" y1="14" x2="12" y2="14"/><line x1="8" y1="18" x2="10" y2="18"/>
    </svg>
  ),
  lock: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>
    </svg>
  ),
  key: (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="m21 2-2 2m-7.61 7.61a5.5 5.5 0 1 1-7.778 7.778 5.5 5.5 0 0 1 7.777-7.777zm0 0L15.5 7.5m0 0 3 3L22 7l-3-3m-3.5 3.5L19 4"/>
    </svg>
  ),
};

// ─── MOCK DATA ──────────────────────────────────────────────────
const MOCK_ORDERS = [
  { id: "6158254", status: "Pending", pickup: "27A Idowu Martins St, Victoria Island", dropoff: "24 Harvey Rd, Sabo Yaba", amount: 1210, date: "Feb 14, 1:00 PM", vehicle: "Bike", merchant: "Vivid Print" },
  { id: "6158190", status: "Done", pickup: "15 Admiralty Way, Lekki Phase 1", dropoff: "42 Allen Avenue, Ikeja", amount: 2500, date: "Feb 13, 3:45 PM", vehicle: "Bike", merchant: "Vivid Print" },
  { id: "6158102", status: "Done", pickup: "24 Alara St, Iwaya", dropoff: "24 Harvey Rd, Sabo Yaba", amount: 1210, date: "Feb 10, 6:25 PM", vehicle: "Bike", merchant: "Vivid Print" },
  { id: "6157980", status: "CustomerCanceled", pickup: "12 Bourdillon Rd, Ikoyi", dropoff: "3 Broad St, Lagos Island", amount: 1800, date: "Feb 9, 11:20 AM", vehicle: "Car", merchant: "Vivid Print" },
  { id: "6157841", status: "Done", pickup: "Plot 1, Block A, Lekki", dropoff: "Ikota Shopping Complex", amount: 3200, date: "Feb 8, 2:15 PM", vehicle: "Bike", merchant: "Vivid Print" },
];

const MOCK_TRANSACTIONS = [
  { id: "TXN-001", type: "credit", amount: 10000, description: "Wallet Funding (Card)", date: "Feb 14, 12:30 PM", ref: "PSK_abc123", balance: 8790 },
  { id: "TXN-002", type: "debit", amount: 1210, description: "Order #6158254 — VI to Yaba", date: "Feb 14, 1:00 PM", ref: "ORD_6158254", balance: 8790 },
  { id: "TXN-003", type: "credit", amount: 5000, description: "Wallet Funding (Bank Transfer)", date: "Feb 12, 9:00 AM", ref: "PSK_def456", balance: 10000 },
  { id: "TXN-004", type: "debit", amount: 2500, description: "Order #6158190 — Lekki to Ikeja", date: "Feb 13, 3:45 PM", ref: "ORD_6158190", balance: 5000 },
  { id: "TXN-005", type: "debit", amount: 1210, description: "Order #6158102 — Iwaya to Yaba", date: "Feb 10, 6:25 PM", ref: "ORD_6158102", balance: 7500 },
  { id: "TXN-006", type: "credit", amount: 1800, description: "Refund — Order #6157980 (Canceled)", date: "Feb 9, 11:45 AM", ref: "REF_6157980", balance: 8710 },
];

const STATUS_COLORS = {
  Pending: { bg: "#FFF3E0", text: "#E65100", label: "Pending" },
  Assigned: { bg: "#E3F2FD", text: "#1565C0", label: "Assigned" },
  Started: { bg: "#E8F5E9", text: "#2E7D32", label: "In Transit" },
  PickedUp: { bg: "#E8F5E9", text: "#2E7D32", label: "Picked Up" },
  Done: { bg: "#E8F5E9", text: "#1B5E20", label: "Delivered" },
  CustomerCanceled: { bg: "#FFEBEE", text: "#C62828", label: "Canceled" },
  DriverCanceled: { bg: "#FFEBEE", text: "#C62828", label: "Canceled" },
  SupportCanceled: { bg: "#FFEBEE", text: "#C62828", label: "Canceled" },
  Unassigned: { bg: "#FFF8E1", text: "#F57F17", label: "Unassigned" },
};

// ─── STYLES ─────────────────────────────────────────────────────
const S = {
  // Colors
  navy: "#1B2A4A",
  navyLight: "#243656",
  gold: "#E8A838",
  goldLight: "#F5C563",
  goldPale: "#FFF8EC",
  dark: "#1a1a2e",
  gray: "#64748b",
  grayLight: "#94a3b8",
  grayBg: "#f1f5f9",
  white: "#ffffff",
  green: "#16a34a",
  greenBg: "#dcfce7",
  red: "#dc2626",
  redBg: "#fee2e2",
  blue: "#2563eb",
  blueBg: "#dbeafe",
};

// ─── MAIN APP ───────────────────────────────────────────────────
function MerchantPortal() {
  const [screen, setScreen] = useState("login");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [walletBalance, setWalletBalance] = useState(0);
  const [orders, setOrders] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [fundModal, setFundModal] = useState(false);
  const [bankTransferModal, setBankTransferModal] = useState(false);
  const [bankTransferAmount, setBankTransferAmount] = useState(0);
  const [orderDetailId, setOrderDetailId] = useState(null);
  const [notification, setNotification] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [loading, setLoading] = useState(false);
  const [verificationToken, setVerificationToken] = useState(null);
  const [passwordResetToken, setPasswordResetToken] = useState(null);

  const showNotif = (msg, type = "success") => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 3000);
  };

  // Check if user is logged in on mount and check for tokens in URL
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    const resetParam = urlParams.get('reset');

    if (token) {
      // If there's a 'reset' parameter or we're on a reset path, it's a password reset token
      if (resetParam === 'true' || window.location.pathname.includes('reset')) {
        setPasswordResetToken(token);
        setScreen("reset-password");
      } else {
        // Otherwise, it's an email verification token
        setVerificationToken(token);
        setScreen("verify-email");
      }
      return;
    }

    // Check if user is logged in
    const user = window.API?.Token?.getUser();
    if (user) {
      setCurrentUser(user);
      setScreen("dashboard");
    }
  }, []);

  // Load orders when dashboard is shown
  useEffect(() => {
    if (screen === "dashboard" && currentUser) {
      loadOrders();
      loadWalletBalance();
    }
  }, [screen, currentUser]);

  // Load wallet when wallet screen is shown
  useEffect(() => {
    if (screen === "wallet" && currentUser) {
      loadWalletBalance();
      loadTransactions();
    }
  }, [screen, currentUser]);

  const loadOrders = async () => {
    try {
      const response = await window.API.Orders.getOrders();
      if (response.success) {
        setOrders(transformOrders(response.orders));
      }
    } catch (error) {
      console.error('Failed to load orders:', error);
    }
  };

  const handleCancelOrder = async (orderNumber) => {
    setLoading(true);
    try {
      const response = await window.API.Orders.cancelOrder(orderNumber);
      if (response.success) {
        showNotif(response.message, 'success');
        if (response.refund.processed) {
          showNotif(`₦${response.refund.amount.toLocaleString()} refunded to wallet`, 'success');
        }
        await loadOrders();
        await loadWalletBalance();
        await loadTransactions();
        setOrderDetailId(null); // Go back to orders list
      } else {
        showNotif(response.error || 'Failed to cancel order', 'error');
      }
    } catch (error) {
      showNotif('Failed to cancel order', 'error');
      console.error('Cancel order error:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadWalletBalance = async () => {
    try {
      const response = await window.API.Wallet.getBalance();
      if (response.success) {
        setWalletBalance(parseFloat(response.data.balance));
      }
    } catch (error) {
      console.error('Failed to load wallet balance:', error);
    }
  };

  const loadTransactions = async () => {
    try {
      const response = await window.API.Wallet.getTransactions();
      if (response.success || response.results) {
        const txnData = response.results?.data || response.data || [];
        setTransactions(transformTransactions(txnData));
      }
    } catch (error) {
      console.error('Failed to load transactions:', error);
    }
  };

  // Transform API order data to frontend format
  const transformOrders = (apiOrders) => {
    return apiOrders.map(order => ({
      id: order.order_number,
      order_number: order.order_number,
      status: order.status,
      pickup: order.pickup_address,
      dropoff: order.deliveries[0]?.dropoff_address || '',
      amount: parseFloat(order.total_amount),
      date: formatDate(order.created_at),
      vehicle: order.vehicle_name,
      merchant: order.user_business_name,
      deliveries: order.deliveries,
      mode: order.mode,
      payment_method: order.payment_method
    }));
  };

  // Transform API transaction data to frontend format
  const transformTransactions = (apiTransactions) => {
    return apiTransactions.map(txn => ({
      id: txn.id,
      type: txn.type,
      amount: parseFloat(txn.amount),
      description: txn.description,
      date: formatDate(txn.created_at),
      ref: txn.reference,
      balance: parseFloat(txn.balance_after),
      status: txn.status
    }));
  };

  const formatDate = (isoString) => {
    const date = new Date(isoString);
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const month = months[date.getMonth()];
    const day = date.getDate();
    const hours = date.getHours();
    const minutes = date.getMinutes();
    const ampm = hours >= 12 ? 'PM' : 'AM';
    const displayHours = hours % 12 || 12;

    return `${month} ${day}, ${displayHours}:${minutes.toString().padStart(2, '0')} ${ampm}`;
  };

  const handleLogin = (user) => {
    setCurrentUser(user);
    setScreen("dashboard");
    showNotif("Welcome back!");
  };

  const handleSignup = (user) => {
    setCurrentUser(user);
    setScreen("dashboard");
    showNotif("Welcome to Assured Express! Please check your email to verify your account.");
  };

  const handleResendVerification = async () => {
    try {
      const accessToken = window.API?.Token?.getAccessToken();
      const response = await fetch('https://www.orders.axpress.net/api/auth/resend-verification/', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      });
      const data = await response.json();

      if (data.success) {
        showNotif(data.message || "Verification email sent! Please check your inbox.", "success");
      } else {
        showNotif(data.error || "Failed to send verification email", "error");
      }
    } catch (error) {
      showNotif("Network error. Please try again.", "error");
      console.error('Resend verification error:', error);
    }
  };

  const handleVerificationComplete = () => {
    // Refresh user data
    const user = window.API?.Token?.getUser();
    if (user) {
      setCurrentUser(user);
    }
    setScreen("dashboard");
    // Clear URL parameters
    window.history.replaceState({}, document.title, window.location.pathname);
  };

  const handleLogout = async () => {
    try {
      await window.API.Auth.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setCurrentUser(null);
      setOrders([]);
      setScreen("login");
      showNotif("Logged out successfully");
    }
  };

  if (screen === "login") return <LoginScreen onLogin={handleLogin} onSignup={() => setScreen("signup")} onForgotPassword={() => setScreen("forgot-password")} />;
  if (screen === "signup") return <SignupScreen onBack={() => setScreen("login")} onComplete={handleSignup} />;
  if (screen === "verify-email") return <VerifyEmailScreen token={verificationToken} onComplete={handleVerificationComplete} />;
  if (screen === "forgot-password") return <ForgotPasswordScreen onBack={() => setScreen("login")} />;
  if (screen === "reset-password") return <ResetPasswordScreen token={passwordResetToken} onComplete={() => setScreen("login")} />;

  const navItems = [
    { id: "dashboard", label: "Dashboard", icon: Icons.dashboard },
    { id: "newOrder", label: "New Order", icon: Icons.newOrder },
    { id: "orders", label: "Orders", icon: Icons.orders },
    { id: "wallet", label: "Wallet", icon: Icons.wallet },
    { id: "website", label: "My Website", icon: Icons.website, badge: "SOON" },
    { id: "webpos", label: "WebPOS", icon: Icons.webpos, badge: "SOON" },
    { id: "loans", label: "Business Loans", icon: Icons.loans, badge: "SOON" },
    { id: "accounting", label: "Accounting", icon: Icons.accounting, badge: "SOON" },
    { id: "support", label: "Support", icon: Icons.support, badge: "SOON" },
    { id: "settings", label: "Settings", icon: Icons.settings },
  ];

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: S.grayBg, fontFamily: "'DM Sans', 'Segoe UI', sans-serif" }}>
      {/* Google Font */}
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet" />

      {/* Notification Toast */}
      {notification && (
        <div style={{
          position: "fixed", top: 20, right: 20, zIndex: 9999, padding: "12px 20px", borderRadius: 10,
          background: notification.type === "success" ? S.green : S.red, color: "#fff",
          fontSize: 14, fontWeight: 500, boxShadow: "0 8px 24px rgba(0,0,0,0.15)",
          animation: "slideIn 0.3s ease"
        }}>
          {notification.msg}
        </div>
      )}

      {/* Fund Wallet Modal */}
      {fundModal && (
        <FundWalletModal
          onClose={() => setFundModal(false)}
          onBankTransfer={(amount) => {
            setBankTransferAmount(amount);
            setFundModal(false);
            setBankTransferModal(true);
          }}
          onFund={async (amount) => {
            try {
              setLoading(true);

              // Get Paystack public key
              const keyResponse = await window.API.Wallet.getPaystackKey();
              if (!keyResponse.success) {
                showNotif('Failed to load payment configuration', 'error');
                setLoading(false);
                return;
              }

              const publicKey = keyResponse.data.public_key;

              // Initialize payment
              const response = await window.API.Wallet.initializePayment(amount);

              if (response.success) {
                // Close modal
                setFundModal(false);

                const reference = response.data.reference;

                // Use Paystack Inline JS
                const handler = window.PaystackPop.setup({
                  key: publicKey,
                  email: currentUser?.email || 'user@example.com',
                  amount: amount * 100, // Convert to kobo
                  currency: 'NGN',
                  ref: reference,
                  onClose: function() {
                    showNotif('Payment cancelled', 'error');
                    setLoading(false);
                  },
                  callback: async function(response) {
                    // Payment successful
                    try {
                      const verifyResponse = await window.API.Wallet.verifyPayment(reference);
                      if (verifyResponse.success) {
                        showNotif(`₦${amount.toLocaleString()} added to wallet successfully!`);
                        loadWalletBalance();
                        loadTransactions();
                      } else {
                        showNotif('Payment verification failed', 'error');
                      }
                    } catch (error) {
                      console.error('Payment verification error:', error);
                      showNotif('Payment verification failed', 'error');
                    } finally {
                      setLoading(false);
                    }
                  }
                });

                handler.openIframe();
              } else {
                const errorMsg = response.errors?.detail?.[0] || 'Failed to initialize payment';
                showNotif(errorMsg, 'error');
                setLoading(false);
              }
            } catch (error) {
              console.error('Fund wallet error:', error);
              showNotif(error.message || 'Failed to fund wallet', 'error');
              setLoading(false);
            }
          }}
        />
      )}

      {/* Bank Transfer Modal */}
      {bankTransferModal && (
        <BankTransferModal
          amount={bankTransferAmount}
          onClose={() => setBankTransferModal(false)}
          onSuccess={() => {
            showNotif('Payment confirmation received! Your wallet will be credited once verified.', 'success');
            loadWalletBalance();
            loadTransactions();
          }}
        />
      )}

      {/* Mobile overlay */}
      {sidebarOpen && <div onClick={() => setSidebarOpen(false)} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)", zIndex: 40 }} />}

      {/* SIDEBAR */}
      <aside style={{
        width: 260, background: S.navy, display: "flex", flexDirection: "column", position: "fixed",
        top: 0, bottom: 0, left: sidebarOpen ? 0 : -260, zIndex: 50,
        transition: "left 0.3s ease",
        ...(window.innerWidth > 768 ? { left: 0, position: "relative" } : {})
      }}>
        {/* Logo */}
        <div style={{ padding: "24px 20px 20px", borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{
              width: 36, height: 36, borderRadius: 8, background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`,
              display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 800, fontSize: 16, color: S.navy,
              fontFamily: "'Space Mono', monospace"
            }}>AX</div>
            <div>
              <div style={{ color: "#fff", fontWeight: 700, fontSize: 15, letterSpacing: "0.5px" }}>ASSURED</div>
              <div style={{ color: S.gold, fontSize: 11, fontWeight: 600, letterSpacing: "2px", marginTop: -2 }}>XPRESS</div>
            </div>
          </div>
        </div>

        {/* Nav */}
        <nav style={{ flex: 1, padding: "12px 10px", display: "flex", flexDirection: "column", gap: 2 }}>
          {navItems.map(item => {
            const active = screen === item.id;
            return (
              <button key={item.id} onClick={() => { setScreen(item.id); setSidebarOpen(false); setOrderDetailId(null); }}
                style={{
                  display: "flex", alignItems: "center", gap: 12, padding: "11px 14px", borderRadius: 10, border: "none",
                  cursor: "pointer", fontSize: 14, fontWeight: active ? 600 : 400, fontFamily: "inherit",
                  background: active ? "rgba(232,168,56,0.12)" : "transparent",
                  color: active ? S.gold : "rgba(255,255,255,0.6)",
                  transition: "all 0.2s",
                }}>
                <span style={{ opacity: active ? 1 : 0.6 }}>{item.icon}</span>
                {item.label}
                {item.badge && (
                  <span style={{
                    marginLeft: "auto", background: item.badge === "FREE" ? S.green : item.badge === "SOON" ? "#8B5CF6" : S.gold, color: item.badge === "FREE" ? "#fff" : item.badge === "SOON" ? "#fff" : S.navy, fontSize: 10, fontWeight: 700,
                    padding: "2px 8px", borderRadius: 10
                  }}>{item.badge}</span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Wallet Quick View */}
        <div style={{ padding: "16px", borderTop: "1px solid rgba(255,255,255,0.08)" }}>
          <div style={{
            background: "rgba(255,255,255,0.05)", borderRadius: 12, padding: "14px 16px",
            border: "1px solid rgba(232,168,56,0.2)"
          }}>
            <div style={{ fontSize: 11, color: "rgba(255,255,255,0.5)", fontWeight: 500 }}>WALLET BALANCE</div>
            <div style={{ fontSize: 22, color: "#fff", fontWeight: 700, marginTop: 4, fontFamily: "'Space Mono', monospace" }}>
              ₦{walletBalance.toLocaleString()}
            </div>
            <button onClick={() => setFundModal(true)} style={{
              marginTop: 10, width: "100%", padding: "8px", border: "none", borderRadius: 8,
              background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy,
              fontWeight: 700, fontSize: 12, cursor: "pointer", fontFamily: "inherit"
            }}>+ Fund Wallet</button>
          </div>
        </div>

        {/* User */}
        <div style={{ padding: "12px 16px 20px", borderTop: "1px solid rgba(255,255,255,0.08)", display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 34, height: 34, borderRadius: "50%", background: "rgba(232,168,56,0.15)",
            display: "flex", alignItems: "center", justifyContent: "center", color: S.gold, fontWeight: 700, fontSize: 13
          }}>{currentUser?.business_name?.substring(0, 2).toUpperCase() || "AX"}</div>
          <div style={{ flex: 1 }}>
            <div style={{ color: "#fff", fontSize: 13, fontWeight: 600 }}>{currentUser?.business_name || "Business"}</div>
            <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 11 }}>{currentUser?.contact_name || "User"}</div>
          </div>
          <button onClick={() => setScreen("login")} style={{ background: "none", border: "none", cursor: "pointer", color: "rgba(255,255,255,0.3)" }}>
            {Icons.logout}
          </button>
        </div>
      </aside>

      {/* MAIN CONTENT */}
      <main style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        {/* Top Bar */}
        <header style={{
          background: "#fff", padding: "0 24px", height: 64, display: "flex", alignItems: "center", gap: 16,
          borderBottom: `1px solid ${S.grayBg}`, position: "sticky", top: 0, zIndex: 30
        }}>
          <button onClick={() => setSidebarOpen(true)} style={{
            background: "none", border: "none", cursor: "pointer", padding: 4, display: window.innerWidth > 768 ? "none" : "flex"
          }}>{Icons.menu}</button>

          <div style={{ flex: 1 }}>
            <h1 style={{ fontSize: 18, fontWeight: 700, color: S.navy, margin: 0 }}>
              {screen === "dashboard" ? "Dashboard" : screen === "newOrder" ? "New Delivery" : screen === "orders" ? "Orders" : screen === "wallet" ? "Wallet" : screen === "website" ? "My Website" : screen === "webpos" ? "WebPOS" : screen === "loans" ? "Business Loans" : screen === "accounting" ? "Accounting" : screen === "settings" ? "Settings" : screen === "support" ? "Support" : ""}
            </h1>
          </div>

          <button onClick={() => setFundModal(true)} style={{
            padding: "8px 16px", borderRadius: 8, border: "none", cursor: "pointer", fontFamily: "inherit",
            background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy,
            fontWeight: 700, fontSize: 13, display: "flex", alignItems: "center", gap: 6
          }}>
            <span style={{ fontSize: 16 }}>+</span> Fund Wallet
          </button>

          <div style={{ position: "relative" }}>
            <button style={{ background: "none", border: "none", cursor: "pointer", color: S.gray, padding: 4 }}>{Icons.bell}</button>
            <div style={{ position: "absolute", top: 2, right: 2, width: 8, height: 8, borderRadius: "50%", background: S.red }} />
          </div>
        </header>

        {/* Page Content */}
        <div style={{ flex: 1, padding: "24px", overflowY: "auto" }}>
          {screen === "dashboard" && (
            <DashboardScreen
              balance={walletBalance}
              orders={orders}
              onNewOrder={() => setScreen("newOrder")}
              onFund={() => setFundModal(true)}
              onViewOrder={(id) => { setOrderDetailId(id); setScreen("orders"); }}
              onGoOrders={() => setScreen("orders")}
              currentUser={currentUser}
              onResendVerification={handleResendVerification}
            />
          )}
          {screen === "newOrder" && (
            <NewOrderScreen
              balance={walletBalance}
              currentUser={currentUser}
              onPlaceOrder={async (orderData) => {
                try {
                  let response;

                  // Call appropriate API based on order mode
                  if (orderData.mode === 'quick') {
                    response = await window.API.Orders.createQuickSend({
                      pickup_address: orderData.pickup,
                      sender_name: orderData.senderName || currentUser?.contact_name || '',
                      sender_phone: orderData.senderPhone || currentUser?.phone || '',
                      dropoff_address: orderData.dropoff,
                      receiver_name: orderData.receiverName || '',
                      receiver_phone: orderData.receiverPhone || '',
                      vehicle: orderData.vehicle,
                      payment_method: orderData.payMethod,
                      package_type: orderData.packageType || 'Box',
                      notes: orderData.notes || '',
                      distance_km: orderData.distance_km || 0,
                      duration_minutes: orderData.duration_minutes || 0
                    });
                  } else if (orderData.mode === 'multi') {
                    response = await window.API.Orders.createMultiDrop({
                      pickup_address: orderData.pickup,
                      sender_name: orderData.senderName || currentUser?.contact_name || '',
                      sender_phone: orderData.senderPhone || currentUser?.phone || '',
                      vehicle: orderData.vehicle,
                      payment_method: orderData.payMethod,
                      deliveries: orderData.deliveries || [],
                      notes: orderData.notes || '',
                      distance_km: orderData.distance_km || 0,
                      duration_minutes: orderData.duration_minutes || 0
                    });
                  } else if (orderData.mode === 'bulk') {
                    response = await window.API.Orders.createBulkImport({
                      pickup_address: orderData.pickup,
                      sender_name: orderData.senderName || currentUser?.contact_name || '',
                      sender_phone: orderData.senderPhone || currentUser?.phone || '',
                      vehicle: orderData.vehicle,
                      payment_method: orderData.payMethod,
                      deliveries: orderData.deliveries || [],
                      notes: orderData.notes || '',
                      distance_km: orderData.distance_km || 0,
                      duration_minutes: orderData.duration_minutes || 0
                    });
                  }

                  if (response && response.success) {
                    // Reload orders from API
                    await loadOrders();

                    // Reload wallet balance if payment was made via wallet
                    if (orderData.payMethod === 'wallet') {
                      await loadWalletBalance();
                    }

                    setScreen("orders");
                    showNotif(response.message || `Order #${response.order?.order_number} created successfully!`);
                  }
                } catch (error) {
                  showNotif(error.message || 'Failed to create order', 'error');
                }
              }}
            />
          )}
          {screen === "orders" && (
            <OrdersScreen
              orders={orders}
              detailId={orderDetailId}
              onSelectOrder={setOrderDetailId}
              onBack={() => setOrderDetailId(null)}
              onCancelOrder={handleCancelOrder}
            />
          )}
          {screen === "wallet" && (
            <WalletScreen
              balance={walletBalance}
              transactions={transactions}
              onFund={() => setFundModal(true)}
            />
          )}
          {screen === "settings" && (
            <SettingsScreen
              currentUser={currentUser}
              onUpdateUser={(updatedUser) => setCurrentUser(updatedUser)}
              onShowNotif={showNotif}
            />
          )}
          {screen === "support" && <SupportScreen />}
          {screen === "website" && <WebsiteScreen onCreateDelivery={() => setScreen("newOrder")} />}
          {screen === "webpos" && <WebPOSScreen />}
          {screen === "loans" && <BusinessLoansScreen />}
          {screen === "accounting" && <AccountingScreen />}
        </div>
      </main>

      <style>{`
        @keyframes slideIn { from { transform: translateX(30px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        * { box-sizing: border-box; }
        button:hover { filter: brightness(1.05); }
        input:focus, select:focus, textarea:focus { outline: 2px solid ${S.gold}; outline-offset: -1px; }
        ::-webkit-scrollbar { width: 6px; } ::-webkit-scrollbar-track { background: transparent; } ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
      `}</style>
    </div>
  );
}

// ─── LOGIN SCREEN ───────────────────────────────────────────────
function LoginScreen({ onLogin, onSignup, onForgotPassword }) {
  const [phone, setPhone] = useState("");
  const [pass, setPass] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async () => {
    if (!phone || !pass) {
      setError("Please enter phone and password");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const response = await window.API.Auth.login(phone, pass);

      if (response.success) {
        onLogin(response.user);
      }
    } catch (err) {
      setError(err.message || "Login failed. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleLogin();
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", fontFamily: "'DM Sans', sans-serif" }}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet" />

      {/* Left Panel */}
      <div style={{
        flex: 1, background: `linear-gradient(145deg, #1B2A4A 0%, #0f1b33 100%)`,
        display: "flex", flexDirection: "column", justifyContent: "center", padding: "60px",
        position: "relative", overflow: "hidden", minHeight: "100vh"
      }}>
        {/* Decorative elements */}
        <div style={{ position: "absolute", top: -80, right: -80, width: 300, height: 300, borderRadius: "50%", background: "rgba(232,168,56,0.05)" }} />
        <div style={{ position: "absolute", bottom: -120, left: -60, width: 400, height: 400, borderRadius: "50%", background: "rgba(232,168,56,0.03)" }} />

        <div style={{ position: "relative", zIndex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 48 }}>
            <div style={{
              width: 44, height: 44, borderRadius: 10, background: `linear-gradient(135deg, #E8A838, #F5C563)`,
              display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 800, fontSize: 18, color: "#1B2A4A",
              fontFamily: "'Space Mono', monospace"
            }}>AX</div>
            <div>
              <div style={{ color: "#fff", fontWeight: 700, fontSize: 18, letterSpacing: "1px" }}>ASSURED XPRESS</div>
              <div style={{ color: "#E8A838", fontSize: 11, letterSpacing: "3px", fontWeight: 600 }}>MERCHANT PORTAL</div>
            </div>
          </div>

          <h1 style={{ color: "#fff", fontSize: 36, fontWeight: 700, lineHeight: 1.2, marginBottom: 16 }}>
            Deliver Anything,<br /><span style={{ color: "#E8A838" }}>Anywhere in Lagos</span>
          </h1>
          <p style={{ color: "rgba(255,255,255,0.5)", fontSize: 16, lineHeight: 1.6, maxWidth: 400 }}>
            Fund your wallet. Create orders. Track deliveries. All from one powerful dashboard built for merchants.
          </p>

          <div style={{ display: "flex", gap: 32, marginTop: 48 }}>
            {[{ n: "40+", l: "Active Riders" }, { n: "21min", l: "Avg Delivery" }, { n: "₦1.2K", l: "From" }].map((s, i) => (
              <div key={i}>
                <div style={{ color: "#E8A838", fontSize: 28, fontWeight: 700, fontFamily: "'Space Mono', monospace" }}>{s.n}</div>
                <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 12, marginTop: 4 }}>{s.l}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right Panel - Login Form */}
      <div style={{ width: 480, background: "#fff", display: "flex", flexDirection: "column", justifyContent: "center", padding: "60px" }}>
        <h2 style={{ fontSize: 24, fontWeight: 700, color: "#1B2A4A", marginBottom: 8 }}>Welcome back</h2>
        <p style={{ color: "#64748b", fontSize: 14, marginBottom: 32 }}>Sign in to your merchant account</p>

        {error && (
          <div style={{ padding: "12px 16px", background: "#fee2e2", border: "1px solid #fecaca", borderRadius: 8, marginBottom: 20, color: "#dc2626", fontSize: 14 }}>
            {error}
          </div>
        )}

        <div style={{ marginBottom: 20 }}>
          <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#334155", marginBottom: 6 }}>Phone Number</label>
          <div style={{ display: "flex", alignItems: "center", border: "1.5px solid #e2e8f0", borderRadius: 10, overflow: "hidden" }}>
            <span style={{ padding: "0 12px", background: "#f8fafc", borderRight: "1px solid #e2e8f0", fontSize: 14, color: "#64748b", height: 46, display: "flex", alignItems: "center" }}>+234</span>
            <input value={phone} onChange={e => setPhone(e.target.value)} onKeyPress={handleKeyPress} placeholder="8099999999"
              style={{ flex: 1, border: "none", padding: "0 14px", height: 46, fontSize: 15, fontFamily: "inherit", background: "transparent" }} />
          </div>
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#334155", marginBottom: 6 }}>Password</label>
          <input type="password" value={pass} onChange={e => setPass(e.target.value)} onKeyPress={handleKeyPress} placeholder="Enter password"
            style={{ width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 14px", height: 46, fontSize: 15, fontFamily: "inherit" }} />
        </div>

        <div style={{ textAlign: "right", marginBottom: 24 }}>
          <button onClick={onForgotPassword} style={{ background: "none", border: "none", color: "#E8A838", fontWeight: 600, cursor: "pointer", fontSize: 13, fontFamily: "inherit", textDecoration: "none" }}>
            Forgot Password?
          </button>
        </div>

        <button onClick={handleLogin} disabled={loading} style={{
          width: "100%", height: 48, border: "none", borderRadius: 10, fontSize: 15, fontWeight: 700, cursor: loading ? "not-allowed" : "pointer",
          background: loading ? "#e2e8f0" : `linear-gradient(135deg, #E8A838, #F5C563)`, color: loading ? "#94a3b8" : "#1B2A4A", fontFamily: "inherit",
          boxShadow: loading ? "none" : "0 4px 12px rgba(232,168,56,0.3)"
        }}>{loading ? "Signing in..." : "Sign In"}</button>

        <div style={{ textAlign: "center", marginTop: 24 }}>
          <span style={{ color: "#64748b", fontSize: 14 }}>Don't have an account? </span>
          <button onClick={onSignup} style={{ background: "none", border: "none", color: "#E8A838", fontWeight: 700, cursor: "pointer", fontSize: 14, fontFamily: "inherit" }}>
            Sign Up
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── FORGOT PASSWORD SCREEN ─────────────────────────────────────
function ForgotPasswordScreen({ onBack }) {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    if (!email) {
      setError("Please enter your email address");
      return;
    }

    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError("Please enter a valid email address");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const response = await fetch('https://www.orders.axpress.net/api/auth/request-password-reset/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });

      const data = await response.json();

      if (data.success) {
        setSubmitted(true);
      } else {
        setError(data.error || "Failed to send reset link. Please try again.");
      }
    } catch (err) {
      setError("Network error. Please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !submitted) {
      handleSubmit();
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#f8fafc", fontFamily: "'DM Sans', sans-serif", padding: 20 }}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet" />

      <div style={{ width: "100%", maxWidth: 440, background: "#fff", borderRadius: 18, boxShadow: "0 8px 32px rgba(0,0,0,0.08)", padding: 48 }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{
            width: 56, height: 56, borderRadius: 14, background: `linear-gradient(135deg, #E8A838, #F5C563)`,
            display: "inline-flex", alignItems: "center", justifyContent: "center", marginBottom: 16,
            boxShadow: "0 4px 16px rgba(232,168,56,0.25)"
          }}>
            <div style={{ color: "#1B2A4A" }}>{Icons.lock}</div>
          </div>
          <h2 style={{ fontSize: 24, fontWeight: 700, color: "#1B2A4A", marginBottom: 8 }}>Forgot Password?</h2>
          <p style={{ color: "#64748b", fontSize: 14, lineHeight: 1.5 }}>
            {submitted ? "Check your email for reset instructions" : "Enter your email and we'll send you a reset link"}
          </p>
        </div>

        {!submitted ? (
          <>
            {error && (
              <div style={{ padding: "12px 16px", background: "#fee2e2", border: "1px solid #fecaca", borderRadius: 10, marginBottom: 20, color: "#dc2626", fontSize: 14 }}>
                {error}
              </div>
            )}

            <div style={{ marginBottom: 24 }}>
              <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#334155", marginBottom: 6 }}>Email Address</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="your@email.com"
                style={{ width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 14px", height: 46, fontSize: 15, fontFamily: "inherit" }}
              />
            </div>

            <button onClick={handleSubmit} disabled={loading} style={{
              width: "100%", height: 48, border: "none", borderRadius: 10, fontSize: 15, fontWeight: 700, cursor: loading ? "not-allowed" : "pointer",
              background: loading ? "#e2e8f0" : `linear-gradient(135deg, #E8A838, #F5C563)`, color: loading ? "#94a3b8" : "#1B2A4A", fontFamily: "inherit",
              boxShadow: loading ? "none" : "0 4px 12px rgba(232,168,56,0.3)", marginBottom: 16
            }}>
              {loading ? "Sending..." : "Send Reset Link"}
            </button>
          </>
        ) : (
          <div style={{ textAlign: "center", padding: "24px 0" }}>
            <div style={{ color: "#10b981", marginBottom: 16 }}>{Icons.checkCircle}</div>
            <p style={{ color: "#64748b", fontSize: 14, lineHeight: 1.6, marginBottom: 24 }}>
              If an account exists with <strong style={{ color: "#1B2A4A" }}>{email}</strong>, you will receive a password reset link shortly. Please check your inbox and spam folder.
            </p>
          </div>
        )}

        <div style={{ textAlign: "center" }}>
          <button onClick={onBack} style={{ background: "none", border: "none", color: "#E8A838", fontWeight: 600, cursor: "pointer", fontSize: 14, fontFamily: "inherit" }}>
            ← Back to Login
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── RESET PASSWORD SCREEN ──────────────────────────────────────
function ResetPasswordScreen({ token, onComplete }) {
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [status, setStatus] = useState("form"); // form, success, error
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  // Password validation states
  const [passwordFocused, setPasswordFocused] = useState(false);
  const hasMinLength = newPassword.length >= 6;
  const passwordsMatch = newPassword && confirmPassword && newPassword === confirmPassword;

  const handleSubmit = async () => {
    // Validate passwords
    if (!newPassword || !confirmPassword) {
      setMessage("Please fill in both password fields");
      return;
    }

    if (newPassword !== confirmPassword) {
      setMessage("Passwords do not match");
      return;
    }

    if (newPassword.length < 6) {
      setMessage("Password must be at least 6 characters long");
      return;
    }

    try {
      setLoading(true);
      setMessage("");

      const response = await fetch('https://www.orders.axpress.net/api/auth/reset-password/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token,
          new_password: newPassword,
          confirm_password: confirmPassword
        })
      });

      const data = await response.json();

      if (data.success) {
        setStatus("success");
        // Auto-redirect to login after 3 seconds
        setTimeout(() => onComplete(), 3000);
      } else {
        setStatus("error");
        setMessage(data.error || "Failed to reset password. Please try again.");
      }
    } catch (err) {
      setStatus("error");
      setMessage("Network error. Please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && status === "form") {
      handleSubmit();
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#f8fafc", fontFamily: "'DM Sans', sans-serif", padding: 20 }}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet" />

      <div style={{ width: "100%", maxWidth: 440, background: "#fff", borderRadius: 18, boxShadow: "0 8px 32px rgba(0,0,0,0.08)", padding: 48 }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{
            width: 56, height: 56, borderRadius: 14,
            background: status === "success" ? `linear-gradient(135deg, #10b981, #34d399)` : status === "error" ? `linear-gradient(135deg, #ef4444, #f87171)` : `linear-gradient(135deg, #E8A838, #F5C563)`,
            display: "inline-flex", alignItems: "center", justifyContent: "center", marginBottom: 16,
            boxShadow: status === "success" ? "0 4px 16px rgba(16,185,129,0.25)" : status === "error" ? "0 4px 16px rgba(239,68,68,0.25)" : "0 4px 16px rgba(232,168,56,0.25)"
          }}>
            <div style={{ color: status === "form" ? "#1B2A4A" : "#fff" }}>
              {status === "success" ? Icons.checkCircle : status === "error" ? Icons.xCircle : Icons.key}
            </div>
          </div>
          <h2 style={{ fontSize: 24, fontWeight: 700, color: "#1B2A4A", marginBottom: 8 }}>
            {status === "success" ? "Password Reset!" : status === "error" ? "Reset Failed" : "Create New Password"}
          </h2>
          <p style={{ color: "#64748b", fontSize: 14, lineHeight: 1.5 }}>
            {status === "success" ? "Redirecting you to login..." : status === "error" ? "There was a problem resetting your password" : "Enter your new password below"}
          </p>
        </div>

        {status === "form" && (
          <>
            {message && (
              <div style={{ padding: "12px 16px", background: "#fee2e2", border: "1px solid #fecaca", borderRadius: 10, marginBottom: 20, color: "#dc2626", fontSize: 14 }}>
                {message}
              </div>
            )}

            <div style={{ marginBottom: 20 }}>
              <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#334155", marginBottom: 6 }}>New Password</label>
              <input
                type="password"
                value={newPassword}
                onChange={e => setNewPassword(e.target.value)}
                onFocus={() => setPasswordFocused(true)}
                onBlur={() => setPasswordFocused(false)}
                onKeyPress={handleKeyPress}
                placeholder="Enter new password"
                style={{ width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 14px", height: 46, fontSize: 15, fontFamily: "inherit" }}
              />

              {/* Password strength indicator */}
              {(passwordFocused || newPassword) && (
                <div style={{ marginTop: 8, fontSize: 12 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6, color: hasMinLength ? "#10b981" : "#94a3b8" }}>
                    <span>{hasMinLength ? "✓" : "○"}</span>
                    <span>At least 6 characters</span>
                  </div>
                </div>
              )}
            </div>

            <div style={{ marginBottom: 24 }}>
              <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#334155", marginBottom: 6 }}>Confirm Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Confirm new password"
                style={{
                  width: "100%",
                  border: `1.5px solid ${confirmPassword && !passwordsMatch ? "#fecaca" : "#e2e8f0"}`,
                  borderRadius: 10,
                  padding: "0 14px",
                  height: 46,
                  fontSize: 15,
                  fontFamily: "inherit"
                }}
              />

              {confirmPassword && !passwordsMatch && (
                <div style={{ marginTop: 6, fontSize: 12, color: "#dc2626" }}>
                  Passwords do not match
                </div>
              )}
            </div>

            <button onClick={handleSubmit} disabled={loading} style={{
              width: "100%", height: 48, border: "none", borderRadius: 10, fontSize: 15, fontWeight: 700, cursor: loading ? "not-allowed" : "pointer",
              background: loading ? "#e2e8f0" : `linear-gradient(135deg, #E8A838, #F5C563)`, color: loading ? "#94a3b8" : "#1B2A4A", fontFamily: "inherit",
              boxShadow: loading ? "none" : "0 4px 12px rgba(232,168,56,0.3)"
            }}>
              {loading ? "Resetting Password..." : "Reset Password"}
            </button>
          </>
        )}

        {status === "success" && (
          <div style={{ textAlign: "center", padding: "24px 0" }}>
            <p style={{ color: "#64748b", fontSize: 14, lineHeight: 1.6 }}>
              Your password has been reset successfully! You can now login with your new password.
            </p>
          </div>
        )}

        {status === "error" && (
          <>
            <div style={{ padding: "12px 16px", background: "#fee2e2", border: "1px solid #fecaca", borderRadius: 10, marginBottom: 20, color: "#dc2626", fontSize: 14 }}>
              {message}
            </div>
            <div style={{ textAlign: "center" }}>
              <button onClick={onComplete} style={{ background: "none", border: "none", color: "#E8A838", fontWeight: 600, cursor: "pointer", fontSize: 14, fontFamily: "inherit" }}>
                ← Back to Login
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ─── SIGNUP SCREEN ──────────────────────────────────────────────
function SignupScreen({ onBack, onComplete }) {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Step 1 fields
  const [contactName, setContactName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  // Step 2 fields
  const [businessName, setBusinessName] = useState("");
  const [address, setAddress] = useState("");

  // Password match validation
  const passwordsMatch = password && confirmPassword && password === confirmPassword;
  const passwordsDontMatch = confirmPassword && password !== confirmPassword;

  const handleSignup = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await window.API.Auth.signup({
        business_name: businessName,
        contact_name: contactName,
        phone: phone,
        email: email,
        password: password,
        confirm_password: confirmPassword,
        address: address
      });

      if (response.success) {
        setStep(3);
        setTimeout(() => {
          onComplete(response.user);
        }, 1500);
      }
    } catch (err) {
      setError(err.message || "Signup failed. Please try again.");
      setStep(2); // Go back to step 2 to show error
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", fontFamily: "'DM Sans', sans-serif" }}>
      <link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet" />

      <div style={{ flex: 1, background: "linear-gradient(145deg, #1B2A4A, #0f1b33)", display: "flex", alignItems: "center", justifyContent: "center", padding: 60 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 48 }}>
            <div style={{ width: 44, height: 44, borderRadius: 10, background: "linear-gradient(135deg, #E8A838, #F5C563)", display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 800, fontSize: 18, color: "#1B2A4A", fontFamily: "'Space Mono', monospace" }}>AX</div>
            <div>
              <div style={{ color: "#fff", fontWeight: 700, fontSize: 18 }}>ASSURED XPRESS</div>
              <div style={{ color: "#E8A838", fontSize: 11, letterSpacing: "3px" }}>MERCHANT PORTAL</div>
            </div>
          </div>
          <h1 style={{ color: "#fff", fontSize: 32, fontWeight: 700, lineHeight: 1.3, marginBottom: 16 }}>Start delivering<br />in <span style={{ color: "#E8A838" }}>minutes</span></h1>
          <p style={{ color: "rgba(255,255,255,0.5)", fontSize: 15, lineHeight: 1.6 }}>Sign up, fund your wallet, and start<br />sending packages across Lagos today.</p>

          {/* Steps indicator */}
          <div style={{ display: "flex", gap: 8, marginTop: 40 }}>
            {[1, 2, 3].map(s => (
              <div key={s} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <div style={{
                  width: 32, height: 32, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 13, fontWeight: 700,
                  background: step >= s ? "#E8A838" : "rgba(255,255,255,0.1)",
                  color: step >= s ? "#1B2A4A" : "rgba(255,255,255,0.3)"
                }}>{step > s ? "✓" : s}</div>
                <span style={{ color: step >= s ? "rgba(255,255,255,0.7)" : "rgba(255,255,255,0.3)", fontSize: 13 }}>
                  {s === 1 ? "Account" : s === 2 ? "Business" : "Verify"}
                </span>
                {s < 3 && <div style={{ width: 20, height: 1, background: "rgba(255,255,255,0.1)", margin: "0 4px" }} />}
              </div>
            ))}
          </div>
        </div>
      </div>


      <div style={{ width: 480, background: "#fff", display: "flex", flexDirection: "column", justifyContent: "center", padding: 60 }}>
        {error && (
          <div style={{ padding: "12px 16px", background: "#fee2e2", border: "1px solid #fecaca", borderRadius: 8, marginBottom: 20, color: "#dc2626", fontSize: 14 }}>
            {error}
          </div>
        )}

        {step === 1 && (
          <>
            <h2 style={{ fontSize: 22, fontWeight: 700, color: "#1B2A4A", marginBottom: 24 }}>Create your account</h2>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#334155", marginBottom: 6 }}>Full Name</label>
              <input value={contactName} onChange={e => setContactName(e.target.value)} placeholder="Yetunde Igbene" style={{ width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 14px", height: 44, fontSize: 14, fontFamily: "inherit" }} />
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#334155", marginBottom: 6 }}>Phone Number</label>
              <div style={{ display: "flex", border: "1.5px solid #e2e8f0", borderRadius: 10, overflow: "hidden" }}>
                <span style={{ padding: "0 12px", background: "#f8fafc", borderRight: "1px solid #e2e8f0", fontSize: 14, color: "#64748b", display: "flex", alignItems: "center" }}>+234</span>
                <input value={phone} onChange={e => setPhone(e.target.value)} placeholder="8099999999" style={{ flex: 1, border: "none", padding: "0 14px", height: 44, fontSize: 14, fontFamily: "inherit", background: "transparent" }} />
              </div>
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#334155", marginBottom: 6 }}>Email</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@business.com" style={{ width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 14px", height: 44, fontSize: 14, fontFamily: "inherit" }} />
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#334155", marginBottom: 6 }}>Password</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Min. 8 characters" style={{ width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 14px", height: 44, fontSize: 14, fontFamily: "inherit" }} />
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#334155", marginBottom: 6 }}>Confirm Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                placeholder="Re-enter password"
                style={{
                  width: "100%",
                  border: `1.5px solid ${passwordsDontMatch ? "#ef4444" : passwordsMatch ? "#10b981" : "#e2e8f0"}`,
                  borderRadius: 10,
                  padding: "0 14px",
                  height: 44,
                  fontSize: 14,
                  fontFamily: "inherit",
                  outline: "none"
                }}
              />
              {confirmPassword && (
                <div style={{
                  marginTop: 6,
                  fontSize: 12,
                  fontWeight: 500,
                  color: passwordsMatch ? "#10b981" : "#ef4444",
                  display: "flex",
                  alignItems: "center",
                  gap: 4
                }}>
                  {passwordsMatch ? (
                    <>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                      Passwords match
                    </>
                  ) : (
                    <>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="15" y1="9" x2="9" y2="15"/>
                        <line x1="9" y1="9" x2="15" y2="15"/>
                      </svg>
                      Passwords don't match
                    </>
                  )}
                </div>
              )}
            </div>
            <button
              onClick={() => setStep(2)}
              disabled={!contactName || !phone || !email || !password || !confirmPassword || passwordsDontMatch}
              style={{
                width: "100%",
                height: 46,
                border: "none",
                borderRadius: 10,
                fontSize: 15,
                fontWeight: 700,
                cursor: (!contactName || !phone || !email || !password || !confirmPassword || passwordsDontMatch) ? "not-allowed" : "pointer",
                background: (!contactName || !phone || !email || !password || !confirmPassword || passwordsDontMatch) ? "#e2e8f0" : "linear-gradient(135deg, #E8A838, #F5C563)",
                color: (!contactName || !phone || !email || !password || !confirmPassword || passwordsDontMatch) ? "#94a3b8" : "#1B2A4A",
                fontFamily: "inherit",
                marginTop: 8,
                transition: "all 0.2s ease"
              }}
            >
              Continue
            </button>
          </>
        )}
        {step === 2 && (
          <>
            <h2 style={{ fontSize: 22, fontWeight: 700, color: "#1B2A4A", marginBottom: 24 }}>Business details</h2>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#334155", marginBottom: 6 }}>Business Name</label>
              <input value={businessName} onChange={e => setBusinessName(e.target.value)} placeholder="Vivid Print" style={{ width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 14px", height: 44, fontSize: 14, fontFamily: "inherit" }} />
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#334155", marginBottom: 6 }}>Business Address</label>
              <input value={address} onChange={e => setAddress(e.target.value)} placeholder="19 Tejuosho Street, Yaba" style={{ width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 14px", height: 44, fontSize: 14, fontFamily: "inherit" }} />
            </div>
            <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
              <button onClick={() => setStep(1)} style={{ flex: 1, height: 46, border: "1.5px solid #e2e8f0", borderRadius: 10, fontSize: 14, fontWeight: 600, cursor: "pointer", background: "#fff", color: "#334155", fontFamily: "inherit" }}>Back</button>
              <button onClick={handleSignup} disabled={loading} style={{ flex: 2, height: 46, border: "none", borderRadius: 10, fontSize: 15, fontWeight: 700, cursor: loading ? "not-allowed" : "pointer", background: loading ? "#e2e8f0" : "linear-gradient(135deg, #E8A838, #F5C563)", color: loading ? "#94a3b8" : "#1B2A4A", fontFamily: "inherit" }}>
                {loading ? "Creating Account..." : "Create Account"}
              </button>
            </div>
          </>
        )}
        {step === 3 && (
          <>
            <div style={{ textAlign: "center", marginBottom: 24 }}>
              <div style={{ width: 64, height: 64, borderRadius: "50%", background: "#dcfce7", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px" }}>
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#16a34a" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              </div>
              <h2 style={{ fontSize: 22, fontWeight: 700, color: "#1B2A4A", marginBottom: 8 }}>You're all set!</h2>
              <p style={{ color: "#64748b", fontSize: 14, lineHeight: 1.6 }}>Your merchant account has been created. Fund your wallet to start sending deliveries.</p>
            </div>
            <button onClick={onComplete} style={{ width: "100%", height: 46, border: "none", borderRadius: 10, fontSize: 15, fontWeight: 700, cursor: "pointer", background: "linear-gradient(135deg, #E8A838, #F5C563)", color: "#1B2A4A", fontFamily: "inherit" }}>
              Go to Dashboard
            </button>
          </>
        )}
        {step < 3 && (
          <div style={{ textAlign: "center", marginTop: 20 }}>
            <span style={{ color: "#64748b", fontSize: 14 }}>Already have an account? </span>
            <button onClick={onBack} style={{ background: "none", border: "none", color: "#E8A838", fontWeight: 700, cursor: "pointer", fontSize: 14, fontFamily: "inherit" }}>Sign In</button>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── EMAIL VERIFICATION BANNER ──────────────────────────────────
function EmailVerificationBanner({ currentUser, onResend, onDismiss }) {
  const [resending, setResending] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  // Don't show if email is verified or banner is dismissed
  if (!currentUser || currentUser.email_verified || dismissed) return null;

  const handleResend = async () => {
    setResending(true);
    await onResend();
    setResending(false);
  };

  return (
    <div style={{
      background: "linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%)",
      border: "1px solid #FCD34D",
      borderRadius: 12,
      padding: "16px 20px",
      marginBottom: 24,
      display: "flex",
      alignItems: "center",
      gap: 16,
      boxShadow: "0 2px 8px rgba(252, 211, 77, 0.2)"
    }}>
      <div style={{ color: "#92400E", fontSize: 24 }}>
        {Icons.mail}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: "#78350F", marginBottom: 4 }}>
          Verify Your Email Address
        </div>
        <div style={{ fontSize: 13, color: "#92400E", lineHeight: 1.5 }}>
          We sent a verification email to <strong>{currentUser.email}</strong>. Please check your inbox and click the verification link.
        </div>
      </div>
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <button
          onClick={handleResend}
          disabled={resending}
          style={{
            padding: "8px 16px",
            borderRadius: 8,
            border: "1px solid #D97706",
            background: "#fff",
            color: "#92400E",
            fontWeight: 600,
            fontSize: 13,
            cursor: resending ? "not-allowed" : "pointer",
            fontFamily: "inherit",
            opacity: resending ? 0.6 : 1,
            whiteSpace: "nowrap"
          }}
        >
          {resending ? "Sending..." : "Resend Email"}
        </button>
        <button
          onClick={() => setDismissed(true)}
          style={{
            background: "none",
            border: "none",
            color: "#92400E",
            cursor: "pointer",
            padding: 4,
            fontSize: 20,
            lineHeight: 1
          }}
        >
          ×
        </button>
      </div>
    </div>
  );
}

// ─── VERIFY EMAIL SCREEN ────────────────────────────────────────
function VerifyEmailScreen({ token, onComplete }) {
  const [status, setStatus] = useState("verifying"); // verifying, success, error
  const [message, setMessage] = useState("");

  useEffect(() => {
    verifyEmail();
  }, []);

  const verifyEmail = async () => {
    try {
      const response = await fetch(`https://www.orders.axpress.net/api/auth/verify-email/?token=${token}`);
      const data = await response.json();

      if (data.success) {
        setStatus("success");
        setMessage(data.message || "Email verified successfully!");

        // Update user in localStorage
        if (data.user) {
          window.API?.Token?.setUser(data.user);
        }

        // Redirect to dashboard after 3 seconds
        setTimeout(() => {
          onComplete();
        }, 3000);
      } else {
        setStatus("error");
        setMessage(data.error || "Verification failed. Please try again.");
      }
    } catch (error) {
      setStatus("error");
      setMessage("Network error. Please check your connection and try again.");
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: S.grayBg,
      padding: 24
    }}>
      <div style={{
        background: "#fff",
        borderRadius: 18,
        padding: "48px 40px",
        maxWidth: 480,
        width: "100%",
        textAlign: "center",
        boxShadow: "0 4px 24px rgba(0,0,0,0.08)"
      }}>
        {status === "verifying" && (
          <>
            <div style={{
              width: 48,
              height: 48,
              border: `4px solid ${S.goldPale}`,
              borderTop: `4px solid ${S.gold}`,
              borderRadius: "50%",
              margin: "0 auto 24px",
              animation: "spin 1s linear infinite"
            }} />
            <h2 style={{ fontSize: 22, fontWeight: 700, color: S.navy, margin: "0 0 12px" }}>
              Verifying Your Email
            </h2>
            <p style={{ fontSize: 14, color: S.gray, margin: 0 }}>
              Please wait while we verify your email address...
            </p>
          </>
        )}

        {status === "success" && (
          <>
            <div style={{ color: S.green, margin: "0 auto 24px" }}>
              {Icons.checkCircle}
            </div>
            <h2 style={{ fontSize: 22, fontWeight: 700, color: S.navy, margin: "0 0 12px" }}>
              Email Verified Successfully!
            </h2>
            <p style={{ fontSize: 14, color: S.gray, margin: "0 0 24px" }}>
              {message}
            </p>
            <p style={{ fontSize: 13, color: S.grayLight, margin: 0 }}>
              Redirecting to dashboard...
            </p>
          </>
        )}

        {status === "error" && (
          <>
            <div style={{ color: S.red, margin: "0 auto 24px" }}>
              {Icons.xCircle}
            </div>
            <h2 style={{ fontSize: 22, fontWeight: 700, color: S.navy, margin: "0 0 12px" }}>
              Verification Failed
            </h2>
            <p style={{ fontSize: 14, color: S.gray, margin: "0 0 32px" }}>
              {message}
            </p>
            <button
              onClick={onComplete}
              style={{
                padding: "12px 32px",
                borderRadius: 10,
                border: "none",
                background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`,
                color: S.navy,
                fontWeight: 700,
                fontSize: 14,
                cursor: "pointer",
                fontFamily: "inherit",
                boxShadow: "0 4px 12px rgba(232,168,56,0.3)"
              }}
            >
              Go to Dashboard
            </button>
          </>
        )}
      </div>

      {/* Add CSS animation for spinner */}
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}

// ─── DASHBOARD ──────────────────────────────────────────────────
function DashboardScreen({ balance, orders, onNewOrder, onFund, onViewOrder, onGoOrders, currentUser, onResendVerification }) {
  const recentOrders = orders.slice(0, 4);
  const delivered = orders.filter(o => o.status === "Done").length;
  const pending = orders.filter(o => o.status === "Pending" || o.status === "Assigned" || o.status === "Started").length;
  const totalSpent = orders.reduce((s, o) => s + o.amount, 0);

  // Helper function to get vehicle icon
  const getVehicleIcon = (vehicleName) => {
    if (!vehicleName) return Icons.bike;
    const vehicle = vehicleName.toLowerCase();
    if (vehicle.includes('car')) return Icons.car;
    if (vehicle.includes('van')) return Icons.van;
    return Icons.bike; // default to bike
  };

  // Helper function to get mode badge
  const getModeBadge = (mode) => {
    const badges = {
      quick: { label: "Quick Send", bg: "#dbeafe", color: "#1e40af" },
      multi: { label: "Multi-Drop", bg: "#fef3c7", color: "#92400e" },
      bulk: { label: "Bulk Import", bg: "#e0e7ff", color: "#3730a3" }
    };
    return badges[mode] || badges.quick;
  };

  const cards = [
    { label: "Wallet Balance", value: `₦${balance.toLocaleString()}`, sub: "Available funds", color: "#E8A838", bg: "linear-gradient(135deg, #1B2A4A, #243656)", textColor: "#fff", action: "Fund", onAction: onFund },
    { label: "Orders This Month", value: orders.length.toString(), sub: `${delivered} delivered, ${pending} active`, color: "#16a34a", bg: "#fff" },
    { label: "Total Spent", value: `₦${totalSpent.toLocaleString()}`, sub: "This month", color: "#2563eb", bg: "#fff" },
    { label: "Avg. Delivery Cost", value: delivered > 0 ? `₦${Math.round(totalSpent / delivered).toLocaleString()}` : "—", sub: "Per order", color: "#8b5cf6", bg: "#fff" },
  ];

  return (
    <div style={{ animation: "fadeIn 0.3s ease" }}>
      {/* Welcome */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <div>
          <h2 style={{ fontSize: 20, fontWeight: 700, color: S.navy, margin: 0 }}>Good afternoon, {currentUser?.contact_name?.split(' ')[0] || "User"}</h2>
          <p style={{ color: S.gray, fontSize: 14, margin: "4px 0 0" }}>Here's your delivery overview</p>
        </div>
        <button onClick={onNewOrder} style={{
          padding: "10px 20px", borderRadius: 10, border: "none", cursor: "pointer",
          background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy,
          fontWeight: 700, fontSize: 14, fontFamily: "inherit", display: "flex", alignItems: "center", gap: 8,
          boxShadow: "0 4px 12px rgba(232,168,56,0.25)"
        }}>
          {Icons.newOrder} New Delivery
        </button>
      </div>

      {/* Email Verification Banner */}
      <EmailVerificationBanner
        currentUser={currentUser}
        onResend={onResendVerification}
        onDismiss={() => {}}
      />

      {/* Stat Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: 16, marginBottom: 28 }}>
        {cards.map((c, i) => (
          <div key={i} style={{
            background: c.bg, borderRadius: 14, padding: "20px", border: i > 0 ? "1px solid #e2e8f0" : "none",
            boxShadow: i === 0 ? "0 8px 24px rgba(27,42,74,0.2)" : "0 1px 3px rgba(0,0,0,0.04)",
            position: "relative", overflow: "hidden"
          }}>
            {i === 0 && <div style={{ position: "absolute", top: -30, right: -30, width: 100, height: 100, borderRadius: "50%", background: "rgba(232,168,56,0.1)" }} />}
            <div style={{ fontSize: 12, fontWeight: 600, color: i === 0 ? "rgba(255,255,255,0.6)" : S.gray, textTransform: "uppercase", letterSpacing: "0.5px" }}>{c.label}</div>
            <div style={{ fontSize: 26, fontWeight: 800, color: i === 0 ? "#fff" : S.navy, marginTop: 8, fontFamily: "'Space Mono', monospace" }}>{c.value}</div>
            <div style={{ fontSize: 12, color: i === 0 ? "rgba(255,255,255,0.5)" : S.grayLight, marginTop: 4 }}>{c.sub}</div>
            {c.action && (
              <button onClick={c.onAction} style={{
                marginTop: 12, padding: "6px 14px", borderRadius: 6, border: "1px solid rgba(232,168,56,0.4)",
                background: "rgba(232,168,56,0.15)", color: S.gold, fontSize: 12, fontWeight: 700, cursor: "pointer", fontFamily: "inherit"
              }}>+ {c.action}</button>
            )}
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 28 }}>
        {[
          { label: "Send Package", icon: Icons.bike, action: onNewOrder },
          { label: "Fund Wallet", icon: Icons.wallet, action: onFund },
          { label: "Track Order", icon: Icons.search, action: onGoOrders },
          { label: "Get Support", icon: Icons.support, action: () => {} },
        ].map((a, i) => (
          <button key={i} onClick={a.action} style={{
            background: "#fff", border: "1px solid #e2e8f0", borderRadius: 12, padding: "16px", cursor: "pointer",
            display: "flex", flexDirection: "column", alignItems: "center", gap: 8, fontFamily: "inherit",
            transition: "all 0.2s"
          }}>
            <div style={{ color: S.gold }}>{a.icon}</div>
            <span style={{ fontSize: 13, fontWeight: 600, color: S.navy }}>{a.label}</span>
          </button>
        ))}
      </div>

      {/* Recent Orders */}
      <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", overflow: "hidden" }}>
        <div style={{ padding: "16px 20px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #f1f5f9" }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, color: S.navy, margin: 0 }}>Recent Orders</h3>
          <button onClick={onGoOrders} style={{ background: "none", border: "none", color: S.gold, fontSize: 13, fontWeight: 600, cursor: "pointer", fontFamily: "inherit" }}>View All →</button>
        </div>
        {recentOrders.map((order, i) => {
          const st = STATUS_COLORS[order.status] || STATUS_COLORS.Pending;
          return (
            <div key={order.id} onClick={() => onViewOrder(order.id)} style={{
              padding: "14px 20px", display: "flex", alignItems: "center", gap: 14, cursor: "pointer",
              borderBottom: i < recentOrders.length - 1 ? "1px solid #f8fafc" : "none",
              transition: "background 0.15s"
            }}>
              <div style={{ width: 40, height: 40, borderRadius: 10, background: S.goldPale, display: "flex", alignItems: "center", justifyContent: "center", color: S.gold }}>
                {getVehicleIcon(order.vehicle)}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
                  <span style={{ fontSize: 14, fontWeight: 600, color: S.navy }}>#{order.id}</span>
                  {order.mode && (() => {
                    const modeBadge = getModeBadge(order.mode);
                    return (
                      <span style={{ fontSize: 9, fontWeight: 600, padding: "2px 6px", borderRadius: 4, background: modeBadge.bg, color: modeBadge.color }}>
                        {modeBadge.label}
                      </span>
                    );
                  })()}
                  {order.deliveries && order.deliveries.length > 1 && (
                    <span style={{ fontSize: 9, fontWeight: 600, padding: "2px 6px", borderRadius: 4, background: "#f1f5f9", color: S.navy }}>
                      {order.deliveries.length} stops
                    </span>
                  )}
                </div>
                <div style={{ fontSize: 12, color: S.grayLight, marginTop: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                  {order.pickup} → {order.deliveries && order.deliveries.length > 1 ? `${order.deliveries.length} locations` : order.dropoff}
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 14, fontWeight: 700, color: S.navy, fontFamily: "'Space Mono', monospace" }}>₦{order.amount.toLocaleString()}</div>
                <span style={{ fontSize: 11, fontWeight: 600, padding: "2px 8px", borderRadius: 6, background: st.bg, color: st.text }}>{st.label}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── ADDRESS AUTOCOMPLETE INPUT COMPONENT ───────────────────────
function AddressAutocompleteInput({ value, onChange, placeholder, style, disabled }) {
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);
  const [error, setError] = useState(null);
  const inputRef = useRef(null);
  const dropdownRef = useRef(null);
  const debounceTimer = useRef(null);
  const autocompleteService = useRef(null);
  const placesService = useRef(null);

  // Initialize Google Maps services
  useEffect(() => {
    const initServices = () => {
      if (window.google && window.google.maps && window.google.maps.places) {
        autocompleteService.current = new window.google.maps.places.AutocompleteService();
        // Create a dummy div for PlacesService (required by Google Maps API)
        const dummyDiv = document.createElement('div');
        placesService.current = new window.google.maps.places.PlacesService(dummyDiv);
        setError(null);
      } else {
        setError('Google Maps not loaded');
      }
    };

    if (window.googleMapsLoaded) {
      initServices();
    } else {
      window.addEventListener('google-maps-loaded', initServices);
      return () => window.removeEventListener('google-maps-loaded', initServices);
    }
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target) &&
          inputRef.current && !inputRef.current.contains(e.target)) {
        setShowDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Fetch suggestions with debouncing
  const fetchSuggestions = (input) => {
    if (!input || input.length < 3) {
      setSuggestions([]);
      setShowDropdown(false);
      return;
    }

    if (!autocompleteService.current) {
      setError('Google Maps not ready');
      return;
    }

    setLoading(true);
    setError(null);

    // Debounce API calls
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    debounceTimer.current = setTimeout(() => {
      const request = {
        input: input,
        componentRestrictions: { country: 'ng' }, // Restrict to Nigeria
        types: ['address'], // Only addresses
        // Bias results to Lagos
        location: new window.google.maps.LatLng(6.5244, 3.3792), // Lagos coordinates
        radius: 50000, // 50km radius
      };

      autocompleteService.current.getPlacePredictions(request, (predictions, status) => {
        setLoading(false);

        if (status === window.google.maps.places.PlacesServiceStatus.OK && predictions) {
          // Filter to only Lagos addresses
          const lagosResults = predictions.filter(p =>
            p.description.toLowerCase().includes('lagos')
          );

          if (lagosResults.length === 0) {
            setError('No addresses found in Lagos');
            setSuggestions([]);
          } else {
            setSuggestions(lagosResults);
            setShowDropdown(true);
            setError(null);
          }
        } else if (status === window.google.maps.places.PlacesServiceStatus.ZERO_RESULTS) {
          setError('No addresses found in Lagos');
          setSuggestions([]);
        } else {
          setError('Failed to fetch suggestions');
          setSuggestions([]);
        }
      });
    }, 550); // 550ms debounce
  };

  const handleInputChange = (e) => {
    const newValue = e.target.value;
    onChange(newValue);
    fetchSuggestions(newValue);
  };

  const handleSelectSuggestion = (suggestion) => {
    onChange(suggestion.description);
    setSuggestions([]);
    setShowDropdown(false);
    setError(null);
  };

  return (
    <div style={{ position: 'relative', width: '100%' }}>
      <input
        ref={inputRef}
        value={value}
        onChange={handleInputChange}
        placeholder={placeholder}
        disabled={disabled}
        style={style}
      />

      {/* Loading indicator */}
      {loading && (
        <div style={{
          position: 'absolute',
          right: 12,
          top: '50%',
          transform: 'translateY(-50%)',
          fontSize: 12,
          color: '#94a3b8'
        }}>
          ⏳
        </div>
      )}

      {/* Dropdown with suggestions */}
      {showDropdown && suggestions.length > 0 && (
        <div
          ref={dropdownRef}
          style={{
            position: 'absolute',
            top: '100%',
            left: 0,
            right: 0,
            marginTop: 4,
            background: '#fff',
            border: '1px solid #e2e8f0',
            borderRadius: 10,
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            maxHeight: 240,
            overflowY: 'auto',
            zIndex: 1000
          }}
        >
          {suggestions.map((suggestion, idx) => (
            <div
              key={suggestion.place_id}
              onClick={() => handleSelectSuggestion(suggestion)}
              style={{
                padding: '10px 14px',
                cursor: 'pointer',
                borderBottom: idx < suggestions.length - 1 ? '1px solid #f1f5f9' : 'none',
                fontSize: 13,
                color: '#1e293b',
                transition: 'background 0.15s ease'
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = '#f8fafc'}
              onMouseLeave={(e) => e.currentTarget.style.background = '#fff'}
            >
              <div style={{ display: 'flex', alignItems: 'start', gap: 8 }}>
                <span style={{ color: '#f59e0b', marginTop: 2 }}>📍</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, marginBottom: 2 }}>
                    {suggestion.structured_formatting?.main_text || suggestion.description}
                  </div>
                  {suggestion.structured_formatting?.secondary_text && (
                    <div style={{ fontSize: 11, color: '#64748b' }}>
                      {suggestion.structured_formatting.secondary_text}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error message */}
      {error && value.length >= 3 && !loading && (
        <div style={{
          fontSize: 11,
          color: '#ef4444',
          marginTop: 4,
          paddingLeft: 4
        }}>
          {error} - You can still enter address manually
        </div>
      )}
    </div>
  );
}

// ─── DELIVERY MAP VIEW COMPONENT ────────────────────────────────
function DeliveryMapView({ pickupAddress, dropoffs, vehicle, totalDeliveries, totalCost, onRouteCalculated }) {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef([]);
  const directionsRendererRef = useRef(null);
  const animationIntervalRef = useRef(null);

  // State for route information
  const [routeDistance, setRouteDistance] = useState(null); // in kilometers
  const [routeDuration, setRouteDuration] = useState(null); // in minutes
  const [routeDurationInTraffic, setRouteDurationInTraffic] = useState(null); // in minutes

  // Helper function to format duration
  const formatDuration = (minutes) => {
    if (!minutes) return '';
    if (minutes < 60) {
      return `${minutes} min`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours} hr ${mins} min` : `${hours} hr`;
  };

  // Function to animate the pulse along the route
  const startPulseAnimation = () => {
    // Clear any existing animation
    if (animationIntervalRef.current) {
      clearInterval(animationIntervalRef.current);
    }

    let offset = 0;
    const speed = 2; // Pixels per frame (adjust for speed)

    animationIntervalRef.current = setInterval(() => {
      offset = (offset + speed) % 200; // Reset after 200px (2 complete cycles)

      if (directionsRendererRef.current) {
        const polylineOptions = directionsRendererRef.current.get('polylineOptions');
        if (polylineOptions && polylineOptions.icons) {
          // Update the offset of the pulse icon
          polylineOptions.icons[0].offset = offset + 'px';
          directionsRendererRef.current.setOptions({ polylineOptions });
        }
      }
    }, 50); // Update every 50ms for smooth animation (~20 fps)
  };

  useEffect(() => {
    // Wait for Google Maps to load
    if (!window.google || !window.google.maps) {
      console.error('Google Maps not loaded');
      return;
    }

    // Initialize map
    const initMap = () => {
      if (!mapRef.current) return;

      // Create map centered on Lagos
      const map = new window.google.maps.Map(mapRef.current, {
        center: { lat: 6.5244, lng: 3.3792 }, // Lagos, Nigeria
        zoom: 12,
        mapTypeControl: false,
        streetViewControl: false,
        fullscreenControl: true,
        zoomControl: true,
        styles: [
          {
            featureType: "poi",
            elementType: "labels",
            stylers: [{ visibility: "off" }]
          }
        ]
      });

      mapInstanceRef.current = map;

      // Initialize directions renderer with burnt orange color and animated pulse
      directionsRendererRef.current = new window.google.maps.DirectionsRenderer({
        map: map,
        suppressMarkers: true, // We'll add custom markers
        polylineOptions: {
          strokeColor: '#E8A838', // Burnt orange to match app theme (S.gold)
          strokeWeight: 4,
          strokeOpacity: 0.7,
          icons: [{
            icon: {
              path: window.google.maps.SymbolPath.CIRCLE,
              scale: 4,
              fillColor: '#ffffff',
              fillOpacity: 0.8,
              strokeColor: '#ffffff',
              strokeWeight: 2,
              strokeOpacity: 0.6
            },
            offset: '0%',
            repeat: '100px'
          }]
        }
      });
    };

    initMap();

    // Cleanup
    return () => {
      if (markersRef.current) {
        markersRef.current.forEach(marker => marker.setMap(null));
        markersRef.current = [];
      }
      if (directionsRendererRef.current) {
        directionsRendererRef.current.setMap(null);
      }
      if (animationIntervalRef.current) {
        clearInterval(animationIntervalRef.current);
      }
    };
  }, []);

  // Update markers and route when addresses change
  useEffect(() => {
    if (!mapInstanceRef.current || !window.google) return;

    const updateMapMarkersAndRoute = async () => {
      const map = mapInstanceRef.current;
      const geocoder = new window.google.maps.Geocoder();

      // Clear existing markers
      markersRef.current.forEach(marker => marker.setMap(null));
      markersRef.current = [];

      // Geocode pickup address
      const geocodeAddress = (address) => {
        return new Promise((resolve) => {
          geocoder.geocode({ address: address + ', Lagos, Nigeria' }, (results, status) => {
            if (status === 'OK' && results[0]) {
              resolve(results[0].geometry.location);
            } else {
              console.warn(`Geocoding failed for ${address}:`, status);
              resolve(null);
            }
          });
        });
      };

      try {
        // Geocode pickup
        const pickupLocation = await geocodeAddress(pickupAddress);

        if (pickupLocation) {
          // Add green pickup marker
          const pickupMarker = new window.google.maps.Marker({
            position: pickupLocation,
            map: map,
            title: 'Pickup: ' + pickupAddress,
            icon: {
              path: window.google.maps.SymbolPath.CIRCLE,
              scale: 10,
              fillColor: '#10b981',
              fillOpacity: 1,
              strokeColor: '#ffffff',
              strokeWeight: 3
            },
            label: {
              text: '📍',
              fontSize: '16px'
            }
          });
          markersRef.current.push(pickupMarker);
        }

        // Geocode dropoffs
        const dropoffLocations = [];
        for (let i = 0; i < dropoffs.length; i++) {
          const dropoff = dropoffs[i];
          const location = await geocodeAddress(dropoff.address);

          if (location) {
            dropoffLocations.push({ location, dropoff, index: i });

            // Add numbered gold marker for each dropoff
            const dropoffMarker = new window.google.maps.Marker({
              position: location,
              map: map,
              title: `Delivery ${i + 1}: ${dropoff.address}`,
              icon: {
                path: window.google.maps.SymbolPath.CIRCLE,
                scale: 12,
                fillColor: '#E8A838',
                fillOpacity: 1,
                strokeColor: '#ffffff',
                strokeWeight: 3
              },
              label: {
                text: String(i + 1),
                color: '#1B2A4A',
                fontSize: '12px',
                fontWeight: 'bold'
              }
            });
            markersRef.current.push(dropoffMarker);
          }
        }

        // Draw route if we have pickup and at least one dropoff
        if (pickupLocation && dropoffLocations.length > 0 && directionsRendererRef.current) {
          const directionsService = new window.google.maps.DirectionsService();

          // Prepare waypoints for multi-stop route
          const waypoints = dropoffLocations.slice(0, -1).map(d => ({
            location: d.location,
            stopover: true
          }));

          const request = {
            origin: pickupLocation,
            destination: dropoffLocations[dropoffLocations.length - 1].location,
            waypoints: waypoints,
            travelMode: window.google.maps.TravelMode.DRIVING,
            optimizeWaypoints: true
          };

          directionsService.route(request, (result, status) => {
            if (status === 'OK') {
              directionsRendererRef.current.setDirections(result);

              // Extract distance and duration from route
              if (result.routes && result.routes[0] && result.routes[0].legs) {
                let totalDistanceMeters = 0;
                let totalDurationSeconds = 0;
                let totalDurationInTrafficSeconds = 0;
                let hasTrafficData = false;

                // Sum up all legs (for multi-stop routes)
                result.routes[0].legs.forEach(leg => {
                  if (leg.distance && leg.distance.value) {
                    totalDistanceMeters += leg.distance.value;
                  }
                  if (leg.duration && leg.duration.value) {
                    totalDurationSeconds += leg.duration.value;
                  }
                  if (leg.duration_in_traffic && leg.duration_in_traffic.value) {
                    totalDurationInTrafficSeconds += leg.duration_in_traffic.value;
                    hasTrafficData = true;
                  }
                });

                // Convert to user-friendly units
                const distanceKm = (totalDistanceMeters / 1000).toFixed(1); // kilometers with 1 decimal
                const durationMin = Math.round(totalDurationSeconds / 60); // minutes
                const durationInTrafficMin = hasTrafficData ? Math.round(totalDurationInTrafficSeconds / 60) : null;

                // Update state
                setRouteDistance(parseFloat(distanceKm));
                setRouteDuration(durationMin);
                setRouteDurationInTraffic(durationInTrafficMin);

                // Notify parent component of route calculation
                if (onRouteCalculated) {
                  onRouteCalculated(parseFloat(distanceKm), durationMin);
                }
              }

              // Re-apply polyline options with icons after setDirections
              // (setDirections replaces the polyline, losing our custom icons)
              const polylineOptions = {
                strokeColor: '#E8A838',
                strokeWeight: 4,
                strokeOpacity: 0.7,
                icons: [{
                  icon: {
                    path: window.google.maps.SymbolPath.CIRCLE,
                    scale: 4,
                    fillColor: '#ffffff',
                    fillOpacity: 0.8,
                    strokeColor: '#ffffff',
                    strokeWeight: 2,
                    strokeOpacity: 0.6
                  },
                  offset: '0%',
                  repeat: '100px'
                }]
              };
              directionsRendererRef.current.setOptions({ polylineOptions });

              // Start animated pulse effect
              startPulseAnimation();
            } else {
              console.warn('Directions request failed:', status);
            }
          });
        }

        // Fit bounds to show all markers
        if (markersRef.current.length > 0) {
          const bounds = new window.google.maps.LatLngBounds();
          markersRef.current.forEach(marker => {
            bounds.extend(marker.getPosition());
          });
          map.fitBounds(bounds);

          // Add padding
          const padding = { top: 50, right: 50, bottom: 100, left: 50 };
          map.fitBounds(bounds, padding);
        }

      } catch (error) {
        console.error('Error updating map:', error);
      }
    };

    if (pickupAddress && dropoffs.length > 0) {
      updateMapMarkersAndRoute();
    }
  }, [pickupAddress, dropoffs]);

  return (
    <div style={{ flex: 1, minWidth: 0, minHeight: 520, borderRadius: 14, overflow: "hidden", position: "relative", border: "1px solid #e2e8f0" }}>
      {/* Google Map Container */}
      <div ref={mapRef} style={{ width: "100%", height: "100%", position: "absolute", inset: 0 }} />

      {/* Summary card on map */}
      <div style={{
        position: "absolute", bottom: 14, left: 14, right: 14, zIndex: 10,
        background: "rgba(255,255,255,0.95)", backdropFilter: "blur(8px)",
        borderRadius: 12, padding: "12px 16px", boxShadow: "0 2px 12px rgba(0,0,0,0.1)",
        display: "flex", alignItems: "center", justifyContent: "space-between"
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 36, height: 36, borderRadius: 8, background: S.goldPale, display: "flex", alignItems: "center", justifyContent: "center", color: S.gold }}>
            {vehicle === "Bike" ? Icons.bike : vehicle === "Car" ? Icons.car : Icons.van}
          </div>
          <div>
            <div style={{ fontSize: 13, fontWeight: 700, color: S.navy }}>{totalDeliveries} × {vehicle} Delivery</div>
            <div style={{ fontSize: 11, color: S.grayLight }}>from {pickupAddress.split(",")[0]}</div>
            {/* Distance and Duration Row */}
            {(routeDistance || routeDuration) && (
              <div style={{ fontSize: 11, color: S.gray, marginTop: 4, display: "flex", alignItems: "center", gap: 8 }}>
                {routeDistance && (
                  <span style={{ display: "flex", alignItems: "center", gap: 3 }}>
                    <span>📏</span>
                    <span>{routeDistance} km</span>
                  </span>
                )}
                {routeDistance && routeDuration && <span>•</span>}
                {routeDuration && (
                  <span style={{ display: "flex", alignItems: "center", gap: 3 }}>
                    <span>🕐</span>
                    <span>
                      {formatDuration(routeDuration)}
                      {routeDurationInTraffic && routeDurationInTraffic !== routeDuration && (
                        <span style={{ color: S.grayLight }}> ({formatDuration(routeDurationInTraffic)} in traffic)</span>
                      )}
                    </span>
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
        <div style={{ fontSize: 18, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono', monospace" }}>₦{totalCost.toLocaleString()}</div>
      </div>

      {/* Location badge */}
      <div style={{ position: "absolute", top: 10, right: 10, background: "rgba(255,255,255,0.85)", borderRadius: 6, padding: "4px 8px", fontSize: 10, color: S.grayLight, zIndex: 10 }}>
        🗺️ Lagos, Nigeria
      </div>
    </div>
  );
}

// ─── NEW ORDER SCREEN ───────────────────────────────────────────
function NewOrderScreen({ balance, onPlaceOrder, currentUser }) {
  // ─── Mode: "quick" | "multi" | "bulk" ───
  const [mode, setMode] = useState("quick");

  // ─── Shared state ───
  const [vehicle, setVehicle] = useState("Bike");
  const [payMethod, setPayMethod] = useState("wallet");
  const [step, setStep] = useState(1); // 1=form, 2=review

  // ─── Pickup (shared across modes) ───
  const [pickupAddress, setPickupAddress] = useState("");
  const [senderName, setSenderName] = useState(currentUser?.contact_name || "");
  const [senderPhone, setSenderPhone] = useState(currentUser?.phone || "");

  // ─── Load default address on mount ───
  useEffect(() => {
    const loadDefaultAddress = async () => {
      try {
        const response = await window.API.Auth.getAddresses();
        if (response.success && response.addresses) {
          const defaultAddress = response.addresses.find(addr => addr.is_default);
          if (defaultAddress && defaultAddress.address) {
            setPickupAddress(defaultAddress.address);
          }
        }
      } catch (error) {
        console.error('Failed to load default address:', error);
        // Silently fail - user can still enter address manually
      }
    };

    if (currentUser) {
      loadDefaultAddress();
    }
  }, [currentUser]);

  // ─── Quick Send state ───
  const [dropoffAddress, setDropoffAddress] = useState("");
  const [receiverName, setReceiverName] = useState("");
  const [receiverPhone, setReceiverPhone] = useState("");
  const [notes, setNotes] = useState("");
  const [estimatedCost, setEstimatedCost] = useState(null);

  // ─── Multi-Drop state ───
  const [drops, setDrops] = useState([
    { id: 1, address: "", name: "", phone: "", pkg: "Box", notes: "" },
  ]);
  const nextDropId = useRef(2);

  // ─── Route information state (for pricing) ───
  const [routeDistance, setRouteDistance] = useState(null); // in kilometers
  const [routeDuration, setRouteDuration] = useState(null); // in minutes

  const addDrop = () => {
    setDrops([...drops, { id: nextDropId.current++, address: "", name: "", phone: "", pkg: "Box", notes: "" }]);
  };
  const removeDrop = (id) => {
    if (drops.length > 1) setDrops(drops.filter(d => d.id !== id));
  };
  const updateDrop = (id, field, value) => {
    setDrops(drops.map(d => d.id === id ? { ...d, [field]: value } : d));
  };

  // ─── Bulk Import state ───
  const [bulkText, setBulkText] = useState("");
  const [bulkRows, setBulkRows] = useState([]);
  const [scanning, setScanning] = useState(false);
  const [scanPreview, setScanPreview] = useState(null);
  const fileRef = useRef(null);

  // Parse pasted/typed text into rows
  const parseBulkText = (text) => {
    const lines = text.trim().split("\n").filter(l => l.trim());
    return lines.map((line, i) => {
      // Support: "Address | Name | Phone" OR "Address, Name, Phone" OR tab-separated
      const parts = line.includes("|") ? line.split("|") : line.includes("\t") ? line.split("\t") : line.split(",");
      return {
        id: i + 1,
        address: (parts[0] || "").trim(),
        name: (parts[1] || "").trim(),
        phone: (parts[2] || "").trim(),
        pkg: "Box",
        valid: (parts[0] || "").trim().length > 5,
      };
    });
  };

  const handleParseBulk = () => {
    const rows = parseBulkText(bulkText);
    setBulkRows(rows);
  };

  // Simulate camera snap → OCR
  const handleSnap = () => {
    setScanning(true);
    setScanPreview("/mock-scan.jpg");
    // Simulate OCR processing delay
    setTimeout(() => {
      setScanning(false);
      const mockOCR = [
        { id: 1, address: "15 Awolowo Rd, Ikoyi", name: "Mrs. Adeyemi", phone: "08034567890", pkg: "Box", valid: true },
        { id: 2, address: "22 Bode Thomas St, Surulere", name: "Chinedu O.", phone: "09098765432", pkg: "Envelope", valid: true },
        { id: 3, address: "7 Allen Avenue, Ikeja", name: "Fatima B.", phone: "07011223344", pkg: "Box", valid: true },
        { id: 4, address: "3 Admiralty Way, Lekki Phase 1", name: "David Eze", phone: "08155667788", pkg: "Fragile", valid: true },
        { id: 5, address: "45 Herbert Macaulay, Yaba", name: "Blessing N.", phone: "09044332211", pkg: "Food", valid: true },
      ];
      setBulkRows(mockOCR);
      setBulkText(mockOCR.map(r => `${r.address} | ${r.name} | ${r.phone}`).join("\n"));
    }, 2200);
  };

  // Handle file upload (photo or CSV)
  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (!file) return;

    if (file.type.startsWith("image/")) {
      // Photo → simulate OCR
      const url = URL.createObjectURL(file);
      setScanPreview(url);
      setScanning(true);
      setTimeout(() => {
        setScanning(false);
        const mockOCR = [
          { id: 1, address: "10 Broad St, Lagos Island", name: "Kunle A.", phone: "08012345678", pkg: "Box", valid: true },
          { id: 2, address: "5 Apapa Rd, Ebute Metta", name: "Grace O.", phone: "07099887766", pkg: "Box", valid: true },
          { id: 3, address: "33 Opebi Rd, Ikeja", name: "Emeka C.", phone: "09012348765", pkg: "Envelope", valid: true },
        ];
        setBulkRows(mockOCR);
      }, 2500);
    } else {
      // CSV/text file
      const reader = new FileReader();
      reader.onload = (ev) => {
        const text = ev.target.result;
        setBulkText(text);
        setBulkRows(parseBulkText(text));
      };
      reader.readAsText(file);
    }
  };

  const removeBulkRow = (id) => {
    setBulkRows(bulkRows.filter(r => r.id !== id));
  };

  const updateBulkRow = (id, field, value) => {
    setBulkRows(bulkRows.map(r => r.id === id ? { ...r, [field]: value } : r));
  };

  // ─── Price calculation ───
  const costs = { Bike: 1210, Car: 4500, Van: 12000 };

  const getActiveDropoffs = () => {
    if (mode === "quick") return dropoffAddress ? [{ address: dropoffAddress, name: receiverName, phone: receiverPhone }] : [];
    if (mode === "multi") return drops.filter(d => d.address.trim());
    if (mode === "bulk") return bulkRows.filter(r => r.valid !== false && r.address.trim());
    return [];
  };

  const totalDeliveries = getActiveDropoffs().length;
  const unitCost = costs[vehicle] || 1210;
  const totalCost = totalDeliveries * unitCost;

  // ─── Review & Confirm ───
  const canProceed = pickupAddress && totalDeliveries > 0;

  const handleConfirmAll = () => {
    const deliveries = getActiveDropoffs();

    // Prepare order data based on mode
    const orderData = {
      mode: mode,
      pickup: pickupAddress,
      senderName: senderName,
      senderPhone: senderPhone,
      vehicle: vehicle,
      payMethod: payMethod,
      notes: notes,
      // Include route information for pricing calculation
      distance_km: routeDistance || 0,
      duration_minutes: routeDuration || 0
    };

    if (mode === 'quick') {
      // Quick Send - single delivery
      orderData.dropoff = dropoffAddress;
      orderData.receiverName = receiverName;
      orderData.receiverPhone = receiverPhone;
      orderData.packageType = drops[0]?.pkg || 'Box';
    } else if (mode === 'multi' || mode === 'bulk') {
      // Multi-Drop or Bulk Import - multiple deliveries
      orderData.deliveries = deliveries.map(d => ({
        dropoff_address: d.address,
        receiver_name: d.name,
        receiver_phone: d.phone,
        package_type: d.pkg || 'Box',
        notes: d.notes || ''
      }));
    }

    onPlaceOrder(orderData);
  };

  // ─── Saved addresses for quick pick ───
  const savedAddresses = [
    { label: "Office", address: "24 Harvey Rd, Sabo Yaba", icon: "🏢" },
    { label: "Warehouse", address: "15 Creek Rd, Apapa", icon: "📦" },
    { label: "Shop", address: "45 Adeniran Ogunsanya, Surulere", icon: "🏪" },
  ];

  const pkgTypes = ["Box", "Envelope", "Fragile", "Food", "Document"];

  const vehicles = [
    { id: "Bike", label: "Bike", icon: Icons.bike, desc: "Up to 10kg", from: "₦1,200" },
    { id: "Car", label: "Car", icon: Icons.car, desc: "Up to 70kg", from: "₦4,500" },
    { id: "Van", label: "Van", icon: Icons.van, desc: "Up to 600kg", from: "₦12,000" },
  ];

  const modeConfig = [
    { id: "quick", label: "Quick Send", icon: "⚡", desc: "Single delivery" },
    { id: "multi", label: "Multi-Drop", icon: "📍", desc: "One pickup, many deliveries" },
    { id: "bulk", label: "Bulk Import", icon: "📋", desc: "Paste, upload, or snap" },
  ];

  // ─── Shared input style ───
  const inputStyle = { width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 14px", height: 42, fontSize: 14, fontFamily: "inherit" };
  const labelStyle = { display: "block", fontSize: 12, fontWeight: 600, color: "#64748b", marginBottom: 5 };

  return (
    <div style={{ maxWidth: step === 2 ? "100%" : 780, margin: "0 auto", animation: "fadeIn 0.3s ease" }}>

      {/* ═══ STEP 1: MODE SELECT + FORM ═══ */}
      {step === 1 && (
        <>
          {/* Mode Selector */}
          <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
            {modeConfig.map(m => (
              <button key={m.id} onClick={() => setMode(m.id)} style={{
                flex: 1, padding: "14px 12px", borderRadius: 12, cursor: "pointer", fontFamily: "inherit",
                border: mode === m.id ? `2px solid ${S.gold}` : "2px solid #e2e8f0",
                background: mode === m.id ? S.goldPale : "#fff",
                transition: "all 0.2s"
              }}>
                <div style={{ fontSize: 22, marginBottom: 4 }}>{m.icon}</div>
                <div style={{ fontSize: 14, fontWeight: 700, color: S.navy }}>{m.label}</div>
                <div style={{ fontSize: 11, color: S.grayLight, marginTop: 2 }}>{m.desc}</div>
              </button>
            ))}
          </div>

          {/* ── Pickup (shared across all modes) ── */}
          <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: 20, marginBottom: 14 }}>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <div style={{ width: 10, height: 10, borderRadius: "50%", background: S.green }} />
                <h3 style={{ fontSize: 14, fontWeight: 700, color: S.navy, margin: 0 }}>Pickup Location</h3>
              </div>
              {/* Saved addresses quick pick */}
              <div style={{ display: "flex", gap: 6 }}>
                {savedAddresses.map(sa => (
                  <button key={sa.label} onClick={() => setPickupAddress(sa.address)} style={{
                    padding: "4px 10px", borderRadius: 8, border: "1px solid #e2e8f0", background: pickupAddress === sa.address ? S.goldPale : "#f8fafc",
                    cursor: "pointer", fontSize: 11, fontWeight: 600, color: S.navy, fontFamily: "inherit"
                  }}>
                    {sa.icon} {sa.label}
                  </button>
                ))}
              </div>
            </div>
            <AddressAutocompleteInput
              value={pickupAddress}
              onChange={setPickupAddress}
              placeholder="Enter pickup address in Lagos"
              style={{ ...inputStyle, marginBottom: 10 }}
            />
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
              <input value={senderName} onChange={e => setSenderName(e.target.value)} placeholder="Sender name" style={inputStyle} />
              <input value={senderPhone} onChange={e => setSenderPhone(e.target.value)} placeholder="Sender phone" style={inputStyle} />
            </div>
          </div>

          {/* ═══ QUICK SEND MODE ═══ */}
          {mode === "quick" && (
            <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: 20, marginBottom: 14 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
                <div style={{ width: 10, height: 10, borderRadius: "50%", background: S.gold }} />
                <h3 style={{ fontSize: 14, fontWeight: 700, color: S.navy, margin: 0 }}>Deliver To</h3>
              </div>
              <AddressAutocompleteInput
                value={dropoffAddress}
                onChange={setDropoffAddress}
                placeholder="Enter delivery address"
                style={{ ...inputStyle, marginBottom: 10 }}
              />
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 10 }}>
                <input value={receiverName} onChange={e => setReceiverName(e.target.value)} placeholder="Receiver name" style={inputStyle} />
                <input value={receiverPhone} onChange={e => setReceiverPhone(e.target.value)} placeholder="Receiver phone" style={inputStyle} />
              </div>
              <textarea value={notes} onChange={e => setNotes(e.target.value)} placeholder="Notes for driver (optional)"
                style={{ ...inputStyle, height: "auto", padding: "10px 14px", minHeight: 44, resize: "vertical" }} />
            </div>
          )}

          {/* ═══ MULTI-DROP MODE ═══ */}
          {mode === "multi" && (
            <>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div style={{ width: 10, height: 10, borderRadius: "50%", background: S.gold }} />
                  <h3 style={{ fontSize: 14, fontWeight: 700, color: S.navy, margin: 0 }}>Deliveries ({drops.length})</h3>
                </div>
                <button onClick={addDrop} style={{
                  padding: "6px 14px", borderRadius: 8, border: `1.5px solid ${S.gold}`, background: S.goldPale,
                  cursor: "pointer", fontSize: 13, fontWeight: 700, color: S.navy, fontFamily: "inherit"
                }}>+ Add Delivery</button>
              </div>

              <div style={{ maxHeight: 420, overflowY: "auto", paddingRight: 4 }}>
                {drops.map((drop, idx) => (
                  <div key={drop.id} style={{
                    background: "#fff", borderRadius: 12, border: "1px solid #e2e8f0", padding: 16, marginBottom: 10,
                    position: "relative"
                  }}>
                    {/* Drop number badge */}
                    <div style={{
                      position: "absolute", top: -8, left: 16, background: S.gold, color: S.navy,
                      fontSize: 11, fontWeight: 800, padding: "2px 10px", borderRadius: 10
                    }}>#{idx + 1}</div>

                    {drops.length > 1 && (
                      <button onClick={() => removeDrop(drop.id)} style={{
                        position: "absolute", top: 8, right: 8, background: "none", border: "none",
                        cursor: "pointer", color: S.red, fontSize: 18, lineHeight: 1
                      }}>×</button>
                    )}

                    <div style={{ marginTop: 6 }}>
                      <AddressAutocompleteInput
                        value={drop.address}
                        onChange={(value) => updateDrop(drop.id, "address", value)}
                        placeholder="Delivery address"
                        style={{ ...inputStyle, marginBottom: 8 }}
                      />
                      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 100px", gap: 8 }}>
                        <input value={drop.name} onChange={e => updateDrop(drop.id, "name", e.target.value)}
                          placeholder="Receiver name" style={inputStyle} />
                        <input value={drop.phone} onChange={e => updateDrop(drop.id, "phone", e.target.value)}
                          placeholder="Phone" style={inputStyle} />
                        <select value={drop.pkg} onChange={e => updateDrop(drop.id, "pkg", e.target.value)}
                          style={{ ...inputStyle, padding: "0 8px", background: "#f8fafc", cursor: "pointer" }}>
                          {pkgTypes.map(p => <option key={p} value={p}>{p}</option>)}
                        </select>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <button onClick={addDrop} style={{
                width: "100%", padding: "14px", borderRadius: 12, border: "2px dashed #e2e8f0",
                background: "transparent", cursor: "pointer", fontSize: 14, fontWeight: 600,
                color: S.grayLight, fontFamily: "inherit", marginBottom: 14,
                display: "flex", alignItems: "center", justifyContent: "center", gap: 8
              }}>
                <span style={{ fontSize: 20, lineHeight: 1 }}>+</span> Add another delivery
              </button>
            </>
          )}

          {/* ═══ BULK IMPORT MODE ═══ */}
          {mode === "bulk" && (
            <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: 20, marginBottom: 14 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
                <div style={{ width: 10, height: 10, borderRadius: "50%", background: S.gold }} />
                <h3 style={{ fontSize: 14, fontWeight: 700, color: S.navy, margin: 0 }}>Import Deliveries</h3>
              </div>

              {/* Action buttons: Snap, Upload, Paste */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10, marginBottom: 16 }}>
                <button onClick={handleSnap} style={{
                  padding: "20px 12px", borderRadius: 12, border: "2px dashed #e2e8f0",
                  background: scanning ? S.goldPale : "#fafbfc", cursor: "pointer", fontFamily: "inherit", textAlign: "center",
                  transition: "all 0.2s"
                }}>
                  <div style={{ fontSize: 28, marginBottom: 6 }}>📸</div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: S.navy }}>Snap & Send</div>
                  <div style={{ fontSize: 10, color: S.grayLight, marginTop: 2 }}>Photo a list → auto-parse</div>
                </button>

                <button onClick={() => fileRef.current?.click()} style={{
                  padding: "20px 12px", borderRadius: 12, border: "2px dashed #e2e8f0",
                  background: "#fafbfc", cursor: "pointer", fontFamily: "inherit", textAlign: "center"
                }}>
                  <div style={{ fontSize: 28, marginBottom: 6 }}>📄</div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: S.navy }}>Upload File</div>
                  <div style={{ fontSize: 10, color: S.grayLight, marginTop: 2 }}>CSV, Excel, or photo</div>
                </button>
                <input ref={fileRef} type="file" accept=".csv,.txt,.xlsx,image/*" onChange={handleFileUpload} style={{ display: "none" }} />

                <button onClick={() => { setBulkText(""); setBulkRows([]); }} style={{
                  padding: "20px 12px", borderRadius: 12, border: "2px dashed #e2e8f0",
                  background: bulkText ? S.goldPale : "#fafbfc", cursor: "pointer", fontFamily: "inherit", textAlign: "center"
                }}>
                  <div style={{ fontSize: 28, marginBottom: 6 }}>✏️</div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: S.navy }}>Type / Paste</div>
                  <div style={{ fontSize: 10, color: S.grayLight, marginTop: 2 }}>One delivery per line</div>
                </button>
              </div>

              {/* Scanning animation */}
              {scanning && (
                <div style={{
                  background: S.navy, borderRadius: 12, padding: 30, textAlign: "center", marginBottom: 16,
                  position: "relative", overflow: "hidden"
                }}>
                  <div style={{
                    position: "absolute", top: 0, left: 0, right: 0, height: 3, background: S.gold,
                    animation: "scanLine 1.5s ease-in-out infinite"
                  }} />
                  <div style={{ fontSize: 40, marginBottom: 10 }}>🔍</div>
                  <div style={{ color: "#fff", fontWeight: 700, fontSize: 15 }}>Scanning addresses...</div>
                  <div style={{ color: "rgba(255,255,255,0.5)", fontSize: 12, marginTop: 4 }}>Reading handwritten or printed text</div>
                  <style>{`@keyframes scanLine { 0%,100% { transform: translateY(0); } 50% { transform: translateY(120px); } }`}</style>
                </div>
              )}

              {/* Text area for paste/type */}
              {!scanning && (
                <>
                  <textarea
                    value={bulkText}
                    onChange={e => setBulkText(e.target.value)}
                    placeholder={"Paste or type your delivery list:\n\nFormat: Address | Receiver Name | Phone\n\nExample:\n15 Awolowo Rd, Ikoyi | Mrs. Adeyemi | 08034567890\n22 Bode Thomas, Surulere | Chinedu O. | 09098765432\n7 Allen Avenue, Ikeja | Fatima B. | 07011223344"}
                    style={{
                      width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "14px",
                      fontSize: 13, fontFamily: "'Space Mono', monospace", minHeight: 140, resize: "vertical",
                      lineHeight: 1.7, color: S.navy
                    }}
                  />
                  {bulkText && (
                    <button onClick={handleParseBulk} style={{
                      marginTop: 10, padding: "10px 24px", borderRadius: 10, border: "none",
                      background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy,
                      fontWeight: 700, fontSize: 14, cursor: "pointer", fontFamily: "inherit"
                    }}>
                      Parse {bulkText.trim().split("\n").filter(l => l.trim()).length} Deliveries
                    </button>
                  )}
                </>
              )}

              {/* Parsed results table */}
              {bulkRows.length > 0 && !scanning && (
                <div style={{ marginTop: 16 }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
                    <div style={{ fontSize: 13, fontWeight: 700, color: S.navy }}>
                      {bulkRows.length} deliveries parsed
                      <span style={{ color: S.green, marginLeft: 8 }}>✓</span>
                    </div>
                    <button onClick={() => { setBulkRows([]); setBulkText(""); }} style={{
                      background: "none", border: "none", cursor: "pointer", fontSize: 12, color: S.red, fontWeight: 600, fontFamily: "inherit"
                    }}>Clear all</button>
                  </div>

                  {/* Header */}
                  <div style={{
                    display: "grid", gridTemplateColumns: "28px 1fr 140px 120px 80px 28px", gap: 8,
                    padding: "8px 12px", background: "#f8fafc", borderRadius: "10px 10px 0 0",
                    fontSize: 11, fontWeight: 700, color: S.grayLight, textTransform: "uppercase"
                  }}>
                    <span>#</span><span>Address</span><span>Receiver</span><span>Phone</span><span>Type</span><span></span>
                  </div>

                  {/* Rows */}
                  <div style={{ maxHeight: 300, overflowY: "auto" }}>
                    {bulkRows.map((row, idx) => (
                      <div key={row.id} style={{
                        display: "grid", gridTemplateColumns: "28px 1fr 140px 120px 80px 28px", gap: 8,
                        padding: "10px 12px", borderBottom: "1px solid #f1f5f9", alignItems: "center",
                        background: row.valid === false ? "#FEF2F2" : "#fff"
                      }}>
                        <span style={{ fontSize: 12, fontWeight: 700, color: S.gold }}>{idx + 1}</span>
                        <AddressAutocompleteInput
                          value={row.address}
                          onChange={(value) => updateBulkRow(row.id, "address", value)}
                          placeholder="Address"
                          style={{ border: "none", fontSize: 13, color: S.navy, fontFamily: "inherit", background: "transparent", width: "100%" }}
                        />
                        <input value={row.name} onChange={e => updateBulkRow(row.id, "name", e.target.value)}
                          style={{ border: "none", fontSize: 13, color: S.gray, fontFamily: "inherit", background: "transparent", width: "100%" }} />
                        <input value={row.phone} onChange={e => updateBulkRow(row.id, "phone", e.target.value)}
                          style={{ border: "none", fontSize: 13, color: S.gray, fontFamily: "'Space Mono', monospace", background: "transparent", width: "100%" }} />
                        <select value={row.pkg || "Box"} onChange={e => updateBulkRow(row.id, "pkg", e.target.value)}
                          style={{ border: "none", fontSize: 11, background: "transparent", cursor: "pointer", fontFamily: "inherit", color: S.gray }}>
                          {pkgTypes.map(p => <option key={p} value={p}>{p}</option>)}
                        </select>
                        <button onClick={() => removeBulkRow(row.id)} style={{
                          background: "none", border: "none", cursor: "pointer", color: S.red, fontSize: 16
                        }}>×</button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── Vehicle Selection (shared) ── */}
          <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: 20, marginBottom: 14 }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: S.navy, margin: "0 0 12px" }}>Vehicle</h3>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8 }}>
              {vehicles.map(v => (
                <button key={v.id} onClick={() => setVehicle(v.id)} style={{
                  background: vehicle === v.id ? S.goldPale : "#f8fafc", border: vehicle === v.id ? `2px solid ${S.gold}` : "2px solid transparent",
                  borderRadius: 12, padding: "14px 10px", cursor: "pointer", textAlign: "center", fontFamily: "inherit",
                  transition: "all 0.2s"
                }}>
                  <div style={{ color: vehicle === v.id ? S.gold : S.gray, marginBottom: 4 }}>{v.icon}</div>
                  <div style={{ fontSize: 13, fontWeight: 700, color: S.navy }}>{v.label}</div>
                  <div style={{ fontSize: 11, color: S.grayLight }}>{v.desc}</div>
                  <div style={{ fontSize: 12, fontWeight: 700, color: S.gold, marginTop: 4 }}>{v.from}</div>
                </button>
              ))}
            </div>
          </div>

          {/* ── Sticky bottom: Summary + Continue ── */}
          <div style={{
            background: "#fff", borderRadius: 14, border: `2px solid ${canProceed ? S.gold : "#e2e8f0"}`,
            padding: "16px 20px", display: "flex", alignItems: "center", justifyContent: "space-between",
            transition: "all 0.3s"
          }}>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div style={{ fontSize: 13, color: S.gray }}>
                  <span style={{ fontWeight: 700, color: S.navy, fontSize: 20, fontFamily: "'Space Mono', monospace" }}>{totalDeliveries}</span>
                  <span style={{ marginLeft: 4 }}>{totalDeliveries === 1 ? "delivery" : "deliveries"}</span>
                </div>
                {totalDeliveries > 0 && (
                  <div style={{ width: 1, height: 24, background: "#e2e8f0" }} />
                )}
                {totalDeliveries > 0 && (
                  <div>
                    <div style={{ fontSize: 11, color: S.grayLight }}>Estimated Total</div>
                    <div style={{ fontSize: 20, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono', monospace" }}>
                      ₦{totalCost.toLocaleString()}
                    </div>
                  </div>
                )}
              </div>
              {totalDeliveries > 1 && (
                <div style={{ fontSize: 11, color: S.grayLight, marginTop: 2 }}>
                  ₦{unitCost.toLocaleString()} × {totalDeliveries} deliveries
                </div>
              )}
            </div>

            <button
              onClick={() => setStep(2)}
              disabled={!canProceed}
              style={{
                padding: "14px 32px", borderRadius: 12, border: "none", fontSize: 15, fontWeight: 700, cursor: canProceed ? "pointer" : "default",
                background: canProceed ? `linear-gradient(135deg, ${S.gold}, ${S.goldLight})` : "#e2e8f0",
                color: canProceed ? S.navy : "#94a3b8", fontFamily: "inherit",
                boxShadow: canProceed ? "0 4px 12px rgba(232,168,56,0.3)" : "none",
                transition: "all 0.2s"
              }}>
              Review & Pay →
            </button>
          </div>
        </>
      )}

      {/* ═══ STEP 2: REVIEW + MAP ═══ */}
      {step === 2 && (
        <div style={{ display: "flex", gap: 20, animation: "fadeIn 0.3s ease" }}>
          {/* LEFT — Order review */}
          <div style={{ flex: 1, minWidth: 0 }}>
            {/* Pickup summary */}
            <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: 20, marginBottom: 14 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                <div style={{ width: 10, height: 10, borderRadius: "50%", background: S.green }} />
                <span style={{ fontSize: 13, fontWeight: 700, color: S.navy }}>Pickup</span>
              </div>
              <div style={{ fontSize: 14, fontWeight: 600, color: S.navy }}>{pickupAddress}</div>
              <div style={{ fontSize: 12, color: S.gray, marginTop: 2 }}>{senderName} • {senderPhone}</div>
            </div>

            {/* Deliveries list */}
            <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: 20, marginBottom: 14 }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <div style={{ width: 10, height: 10, borderRadius: "50%", background: S.gold }} />
                  <span style={{ fontSize: 13, fontWeight: 700, color: S.navy }}>
                    {totalDeliveries} {totalDeliveries === 1 ? "Delivery" : "Deliveries"}
                  </span>
                </div>
                <span style={{ fontSize: 12, color: S.grayLight }}>{vehicle} • ₦{unitCost.toLocaleString()} each</span>
              </div>

              <div style={{ maxHeight: 300, overflowY: "auto" }}>
                {getActiveDropoffs().map((d, idx) => (
                  <div key={idx} style={{
                    display: "flex", alignItems: "center", gap: 12, padding: "10px 0",
                    borderBottom: idx < totalDeliveries - 1 ? "1px solid #f1f5f9" : "none"
                  }}>
                    <div style={{
                      width: 26, height: 26, borderRadius: "50%", background: S.goldPale,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontSize: 11, fontWeight: 800, color: S.gold, flexShrink: 0
                    }}>{idx + 1}</div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: S.navy, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>{d.address}</div>
                      <div style={{ fontSize: 11, color: S.grayLight }}>{d.name}{d.phone ? ` • ${d.phone}` : ""}</div>
                    </div>
                    <div style={{ fontSize: 13, fontWeight: 700, color: S.navy, fontFamily: "'Space Mono', monospace", flexShrink: 0 }}>
                      ₦{unitCost.toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>

              {/* Total */}
              <div style={{
                display: "flex", justifyContent: "space-between", padding: "14px 0 0", marginTop: 10,
                borderTop: "2px solid #f1f5f9"
              }}>
                <span style={{ fontSize: 16, fontWeight: 700, color: S.navy }}>Total</span>
                <span style={{ fontSize: 22, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono', monospace" }}>
                  ₦{totalCost.toLocaleString()}
                </span>
              </div>
            </div>

            {/* Payment */}
            <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: 20, marginBottom: 16 }}>
              <h3 style={{ fontSize: 13, fontWeight: 700, color: S.navy, margin: "0 0 12px" }}>Payment Method</h3>
              {[
                { id: "wallet", label: "Wallet", sub: `Balance: ₦${balance.toLocaleString()}`, disabled: balance < totalCost, tag: balance >= totalCost ? "RECOMMENDED" : "INSUFFICIENT" },
                { id: "cash_on_pickup", label: "Cash on Pickup", sub: "Pay the rider per delivery" },
                { id: "receiver_pays", label: "Receiver Pays", sub: "Each receiver pays on delivery" },
              ].map(pm => (
                <button key={pm.id} onClick={() => !pm.disabled && setPayMethod(pm.id)} style={{
                  width: "100%", display: "flex", alignItems: "center", gap: 12, padding: "12px 14px", marginBottom: 6,
                  border: payMethod === pm.id ? `2px solid ${S.gold}` : "2px solid #e2e8f0", borderRadius: 10,
                  background: payMethod === pm.id ? S.goldPale : pm.disabled ? "#f8fafc" : "#fff",
                  cursor: pm.disabled ? "not-allowed" : "pointer", fontFamily: "inherit", opacity: pm.disabled ? 0.5 : 1
                }}>
                  <div style={{
                    width: 18, height: 18, borderRadius: "50%", border: `2px solid ${payMethod === pm.id ? S.gold : "#cbd5e1"}`,
                    display: "flex", alignItems: "center", justifyContent: "center"
                  }}>
                    {payMethod === pm.id && <div style={{ width: 9, height: 9, borderRadius: "50%", background: S.gold }} />}
                  </div>
                  <div style={{ flex: 1, textAlign: "left" }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: S.navy }}>{pm.label}</div>
                    <div style={{ fontSize: 11, color: S.grayLight }}>{pm.sub}</div>
                  </div>
                  {pm.tag && (
                    <span style={{
                      fontSize: 9, fontWeight: 700, padding: "2px 8px", borderRadius: 6,
                      background: pm.tag === "RECOMMENDED" ? S.greenBg : S.redBg,
                      color: pm.tag === "RECOMMENDED" ? S.green : S.red
                    }}>{pm.tag}</span>
                  )}
                </button>
              ))}
            </div>

            {/* Action buttons */}
            <div style={{ display: "flex", gap: 10 }}>
              <button onClick={() => setStep(1)} style={{
                flex: 1, height: 48, border: "1.5px solid #e2e8f0", borderRadius: 12, fontSize: 14, fontWeight: 600,
                cursor: "pointer", background: "#fff", color: S.navy, fontFamily: "inherit"
              }}>← Back</button>
              <button onClick={handleConfirmAll} style={{
                flex: 2, height: 48, border: "none", borderRadius: 12, fontSize: 15, fontWeight: 700, cursor: "pointer",
                background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy, fontFamily: "inherit",
                boxShadow: "0 4px 12px rgba(232,168,56,0.3)"
              }}>
                {totalDeliveries === 1
                  ? `Create Order — ₦${totalCost.toLocaleString()}`
                  : `Create ${totalDeliveries} Orders — ₦${totalCost.toLocaleString()}`
                }
              </button>
            </div>
          </div>

          {/* RIGHT — Map */}
          <DeliveryMapView
            pickupAddress={pickupAddress}
            dropoffs={getActiveDropoffs()}
            vehicle={vehicle}
            totalDeliveries={totalDeliveries}
            totalCost={totalCost}
            onRouteCalculated={(distance, duration) => {
              setRouteDistance(distance);
              setRouteDuration(duration);
            }}
          />
        </div>
      )}
    </div>
  );
}

// ─── ORDERS SCREEN ──────────────────────────────────────────────
function OrdersScreen({ orders, detailId, onSelectOrder, onBack, onCancelOrder }) {
  const [filter, setFilter] = useState("all");

  // Helper function to get vehicle icon
  const getVehicleIcon = (vehicleName) => {
    if (!vehicleName) return Icons.bike;
    const vehicle = vehicleName.toLowerCase();
    if (vehicle.includes('car')) return Icons.car;
    if (vehicle.includes('van')) return Icons.van;
    return Icons.bike; // default to bike
  };

  // Helper function to get mode badge
  const getModeBadge = (mode) => {
    const badges = {
      quick: { label: "Quick Send", bg: "#dbeafe", color: "#1e40af" },
      multi: { label: "Multi-Drop", bg: "#fef3c7", color: "#92400e" },
      bulk: { label: "Bulk Import", bg: "#e0e7ff", color: "#3730a3" }
    };
    return badges[mode] || badges.quick;
  };

  const filtered = filter === "all" ? orders
    : filter === "active" ? orders.filter(o => ["Pending", "Assigned", "Started", "PickedUp"].includes(o.status))
    : filter === "completed" ? orders.filter(o => o.status === "Done")
    : orders.filter(o => o.status.includes("Canceled"));

  if (detailId) {
    const order = orders.find(o => o.id === detailId);
    if (!order) return null;
    const st = STATUS_COLORS[order.status] || STATUS_COLORS.Pending;

    return (
      <div style={{ maxWidth: 600, margin: "0 auto", animation: "fadeIn 0.3s ease" }}>
        <button onClick={onBack} style={{ background: "none", border: "none", color: S.gold, fontSize: 14, fontWeight: 600, cursor: "pointer", marginBottom: 16, fontFamily: "inherit", display: "flex", alignItems: "center", gap: 6 }}>
          ← Back to Orders
        </button>
        <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", overflow: "hidden" }}>
          <div style={{ padding: "20px 24px", borderBottom: "1px solid #f1f5f9", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <div>
              <div style={{ fontSize: 12, color: S.grayLight }}>Order</div>
              <div style={{ fontSize: 20, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono', monospace" }}>#{order.id}</div>
              {order.mode && (() => {
                const modeBadge = getModeBadge(order.mode);
                return (
                  <span style={{ fontSize: 11, fontWeight: 600, padding: "4px 10px", borderRadius: 6, background: modeBadge.bg, color: modeBadge.color, display: "inline-block", marginTop: 8 }}>
                    {modeBadge.label}
                  </span>
                );
              })()}
            </div>
            <span style={{ padding: "6px 14px", borderRadius: 8, background: st.bg, color: st.text, fontSize: 13, fontWeight: 700 }}>{st.label}</span>
          </div>

          <div style={{ padding: 24 }}>
            {/* Pickup Address */}
            <div style={{ marginBottom: 24 }}>
              <div style={{ display: "flex", gap: 12 }}>
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                  <div style={{ width: 12, height: 12, borderRadius: "50%", background: S.green }} />
                  {order.deliveries && order.deliveries.length > 0 && (
                    <div style={{ width: 2, flex: 1, background: "#e2e8f0", minHeight: 30 }} />
                  )}
                </div>
                <div style={{ flex: 1, paddingBottom: 12 }}>
                  <div style={{ fontSize: 11, color: S.grayLight, fontWeight: 600 }}>PICKUP</div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: S.navy }}>{order.pickup}</div>
                </div>
              </div>
            </div>

            {/* Deliveries */}
            {order.deliveries && order.deliveries.length > 0 ? (
              <div style={{ marginBottom: 24 }}>
                {order.deliveries.map((delivery, idx) => (
                  <div key={idx} style={{ display: "flex", gap: 12, marginBottom: idx < order.deliveries.length - 1 ? 20 : 0 }}>
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                      <div style={{ width: 12, height: 12, borderRadius: "50%", background: S.gold }} />
                      {idx < order.deliveries.length - 1 && (
                        <div style={{ width: 2, flex: 1, background: "#e2e8f0", minHeight: 30 }} />
                      )}
                    </div>
                    <div style={{ flex: 1, paddingBottom: idx < order.deliveries.length - 1 ? 12 : 0 }}>
                      <div style={{ fontSize: 11, color: S.grayLight, fontWeight: 600 }}>
                        DROPOFF {order.deliveries.length > 1 ? `#${idx + 1}` : ''}
                      </div>
                      <div style={{ fontSize: 14, fontWeight: 600, color: S.navy, marginBottom: 4 }}>
                        {delivery.dropoff_address}
                      </div>
                      <div style={{ fontSize: 12, color: S.gray }}>
                        {delivery.receiver_name} • {delivery.receiver_phone}
                      </div>
                      {delivery.package_type && (
                        <div style={{ fontSize: 11, color: S.grayLight, marginTop: 2 }}>
                          📦 {delivery.package_type}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
                <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                  <div style={{ width: 12, height: 12, borderRadius: "50%", background: S.gold }} />
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 11, color: S.grayLight, fontWeight: 600 }}>DROPOFF</div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: S.navy }}>{order.dropoff}</div>
                </div>
              </div>
            )}

            {[
              { l: "Vehicle", v: order.vehicle },
              { l: "Date", v: order.date },
              { l: "Amount", v: `₦${order.amount.toLocaleString()}` },
              { l: "Payment", v: "Wallet (Prepaid)" },
            ].map((r, i) => (
              <div key={i} style={{ display: "flex", justifyContent: "space-between", padding: "12px 0", borderTop: "1px solid #f8fafc" }}>
                <span style={{ fontSize: 13, color: S.gray }}>{r.l}</span>
                <span style={{ fontSize: 13, fontWeight: 600, color: S.navy }}>{r.v}</span>
              </div>
            ))}

            {/* Cancel Order Button */}
            {!['Delivered', 'Canceled'].includes(order.status) && (
              <div style={{ marginTop: 20, paddingTop: 20, borderTop: "1px solid #f1f5f9" }}>
                <button
                  onClick={() => {
                    if (confirm(`Are you sure you want to cancel order #${order.id}?\n\n${order.payment_method === 'wallet' ? 'Your wallet will be refunded automatically.' : ''}`)) {
                      onCancelOrder(order.order_number);
                    }
                  }}
                  style={{
                    width: '100%',
                    padding: '12px 20px',
                    background: '#fee2e2',
                    color: '#991b1b',
                    border: '1px solid #fecaca',
                    borderRadius: 8,
                    fontSize: 14,
                    fontWeight: 600,
                    cursor: 'pointer',
                    fontFamily: 'inherit',
                    transition: 'all 0.2s'
                  }}
                  onMouseOver={(e) => {
                    e.target.style.background = '#fecaca';
                    e.target.style.borderColor = '#fca5a5';
                  }}
                  onMouseOut={(e) => {
                    e.target.style.background = '#fee2e2';
                    e.target.style.borderColor = '#fecaca';
                  }}
                >
                  🚫 Cancel Order
                </button>
              </div>
            )}

            {/* Events Timeline */}
            <div style={{ marginTop: 20, paddingTop: 20, borderTop: "1px solid #f1f5f9" }}>
              <h4 style={{ fontSize: 14, fontWeight: 700, color: S.navy, marginBottom: 14 }}>Events</h4>
              {[
                { event: "Created", desc: "New order placed", time: "1:00 PM" },
                { event: "Dispatching", desc: "Finding nearest rider", time: "1:00 PM" },
                ...(order.status !== "Pending" ? [{ event: "Assigned", desc: "Rider assigned", time: "1:03 PM" }] : []),
                ...(order.status === "Done" ? [
                  { event: "Picked Up", desc: "Package collected", time: "1:15 PM" },
                  { event: "Delivered", desc: "Delivery complete", time: "1:36 PM" },
                ] : []),
              ].map((ev, i) => (
                <div key={i} style={{ display: "flex", gap: 12, marginBottom: 12 }}>
                  <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                    <div style={{ width: 8, height: 8, borderRadius: "50%", background: S.gold, marginTop: 4 }} />
                    {i < 2 && <div style={{ width: 1, height: 20, background: "#e2e8f0" }} />}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: S.navy }}>{ev.event}</div>
                    <div style={{ fontSize: 12, color: S.grayLight }}>{ev.desc} • {ev.time}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ animation: "fadeIn 0.3s ease" }}>
      {/* Filters */}
      <div style={{ display: "flex", gap: 8, marginBottom: 20 }}>
        {[
          { id: "all", label: "All Orders" },
          { id: "active", label: "Active" },
          { id: "completed", label: "Delivered" },
          { id: "canceled", label: "Canceled" },
        ].map(f => (
          <button key={f.id} onClick={() => setFilter(f.id)} style={{
            padding: "8px 16px", borderRadius: 8, border: "none", cursor: "pointer", fontFamily: "inherit",
            fontSize: 13, fontWeight: 600,
            background: filter === f.id ? S.navy : "#fff",
            color: filter === f.id ? "#fff" : S.gray,
            boxShadow: filter === f.id ? "none" : "0 1px 2px rgba(0,0,0,0.05)"
          }}>{f.label}</button>
        ))}
      </div>

      {/* Orders List */}
      <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", overflow: "hidden" }}>
        {filtered.length === 0 ? (
          <div style={{ padding: 40, textAlign: "center", color: S.grayLight }}>No orders found</div>
        ) : filtered.map((order, i) => {
          const st = STATUS_COLORS[order.status] || STATUS_COLORS.Pending;
          return (
            <div key={order.id} onClick={() => onSelectOrder(order.id)} style={{
              padding: "16px 20px", display: "flex", alignItems: "center", gap: 14, cursor: "pointer",
              borderBottom: i < filtered.length - 1 ? "1px solid #f8fafc" : "none",
            }}>
              <div style={{ width: 42, height: 42, borderRadius: 10, background: S.goldPale, display: "flex", alignItems: "center", justifyContent: "center", color: S.gold }}>
                {getVehicleIcon(order.vehicle)}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                  <span style={{ fontSize: 14, fontWeight: 700, color: S.navy }}>#{order.id}</span>
                  <span style={{ fontSize: 11, fontWeight: 600, padding: "2px 8px", borderRadius: 6, background: st.bg, color: st.text }}>{st.label}</span>
                  {order.mode && (() => {
                    const modeBadge = getModeBadge(order.mode);
                    return (
                      <span style={{ fontSize: 10, fontWeight: 600, padding: "2px 8px", borderRadius: 6, background: modeBadge.bg, color: modeBadge.color }}>
                        {modeBadge.label}
                      </span>
                    );
                  })()}
                  {order.deliveries && order.deliveries.length > 1 && (
                    <span style={{ fontSize: 10, fontWeight: 600, padding: "2px 8px", borderRadius: 6, background: "#f1f5f9", color: S.navy }}>
                      {order.deliveries.length} stops
                    </span>
                  )}
                </div>
                <div style={{ fontSize: 12, color: S.grayLight, marginTop: 4, display: "flex", alignItems: "center", gap: 4 }}>
                  <span style={{ color: S.green }}>{Icons.pin}</span> {order.pickup}
                  <span style={{ margin: "0 4px" }}>→</span>
                  <span style={{ color: S.gold }}>{Icons.pin}</span>
                  {order.deliveries && order.deliveries.length > 1
                    ? `${order.deliveries.length} locations`
                    : order.dropoff}
                </div>
              </div>
              <div style={{ textAlign: "right", flexShrink: 0 }}>
                <div style={{ fontSize: 15, fontWeight: 700, color: S.navy, fontFamily: "'Space Mono', monospace" }}>₦{order.amount.toLocaleString()}</div>
                <div style={{ fontSize: 11, color: S.grayLight, marginTop: 2, display: "flex", alignItems: "center", gap: 4, justifyContent: "flex-end" }}>
                  {Icons.clock} {order.date}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── WALLET SCREEN ──────────────────────────────────────────────
function WalletScreen({ balance, transactions, onFund }) {
  const [showAllTransactions, setShowAllTransactions] = useState(false);
  const [filterType, setFilterType] = useState('all'); // 'all', 'credit', 'debit'

  // Filter transactions
  const filteredTransactions = filterType === 'all'
    ? transactions
    : transactions.filter(txn => txn.type === filterType);

  // Show only recent 5 or all based on state
  const displayedTransactions = showAllTransactions
    ? filteredTransactions
    : filteredTransactions.slice(0, 5);

  return (
    <div style={{ animation: "fadeIn 0.3s ease" }}>
      {/* Balance Card */}
      <div style={{
        background: `linear-gradient(135deg, ${S.navy}, #0f1b33)`, borderRadius: 16, padding: "28px 32px",
        marginBottom: 24, position: "relative", overflow: "hidden",
        boxShadow: "0 12px 32px rgba(27,42,74,0.25)"
      }}>
        <div style={{ position: "absolute", top: -40, right: -40, width: 200, height: 200, borderRadius: "50%", background: "rgba(232,168,56,0.06)" }} />
        <div style={{ position: "absolute", bottom: -60, right: 80, width: 160, height: 160, borderRadius: "50%", background: "rgba(232,168,56,0.04)" }} />

        <div style={{ position: "relative" }}>
          <div style={{ fontSize: 13, color: "rgba(255,255,255,0.5)", fontWeight: 500, letterSpacing: "0.5px" }}>AVAILABLE BALANCE</div>
          <div style={{ fontSize: 38, fontWeight: 800, color: "#fff", marginTop: 8, fontFamily: "'Space Mono', monospace" }}>₦{balance.toLocaleString()}</div>
          <div style={{ display: "flex", gap: 10, marginTop: 20 }}>
            <button onClick={onFund} style={{
              padding: "10px 24px", borderRadius: 10, border: "none", cursor: "pointer",
              background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy,
              fontWeight: 700, fontSize: 14, fontFamily: "inherit"
            }}>+ Fund Wallet</button>
            <button style={{
              padding: "10px 24px", borderRadius: 10, border: "1px solid rgba(255,255,255,0.15)",
              cursor: "pointer", background: "rgba(255,255,255,0.05)", color: "rgba(255,255,255,0.7)",
              fontWeight: 600, fontSize: 14, fontFamily: "inherit"
            }}>Transaction History</button>
          </div>
        </div>
      </div>

      {/* Funding Methods */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 24 }}>
        {[
          { label: "Card", desc: "Visa / MC", emoji: "💳" },
          { label: "Transfer", desc: "Bank", emoji: "🏦" },
          { label: "USSD", desc: "*737#", emoji: "📱" },
          { label: "LibertyPay", desc: "Zero fee", emoji: "⚡" },
        ].map((m, i) => (
          <button key={i} onClick={onFund} style={{
            background: "#fff", border: "1px solid #e2e8f0", borderRadius: 12, padding: "16px 12px",
            cursor: "pointer", textAlign: "center", fontFamily: "inherit"
          }}>
            <div style={{ fontSize: 24, marginBottom: 6 }}>{m.emoji}</div>
            <div style={{ fontSize: 13, fontWeight: 700, color: S.navy }}>{m.label}</div>
            <div style={{ fontSize: 11, color: S.grayLight }}>{m.desc}</div>
          </button>
        ))}
      </div>

      {/* Transactions */}
      <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", overflow: "hidden" }}>
        {/* Header with filters */}
        <div style={{ padding: "16px 20px", borderBottom: "1px solid #f1f5f9" }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
            <h3 style={{ fontSize: 15, fontWeight: 700, color: S.navy, margin: 0 }}>
              {showAllTransactions ? 'Transaction History' : 'Recent Transactions'}
            </h3>
            <button
              onClick={() => setShowAllTransactions(!showAllTransactions)}
              style={{
                background: "transparent",
                border: "none",
                color: S.gold,
                fontSize: 13,
                fontWeight: 600,
                cursor: "pointer",
                fontFamily: "inherit"
              }}
            >
              {showAllTransactions ? '← Back' : 'View All →'}
            </button>
          </div>

          {/* Filter buttons */}
          {showAllTransactions && (
            <div style={{ display: "flex", gap: 8 }}>
              {[
                { value: 'all', label: 'All', icon: '📊' },
                { value: 'credit', label: 'Credits', icon: '💰' },
                { value: 'debit', label: 'Debits', icon: '💸' }
              ].map(filter => (
                <button
                  key={filter.value}
                  onClick={() => setFilterType(filter.value)}
                  style={{
                    padding: "6px 12px",
                    borderRadius: 8,
                    border: filterType === filter.value ? `2px solid ${S.gold}` : "1px solid #e2e8f0",
                    background: filterType === filter.value ? S.goldPale : "#fff",
                    color: filterType === filter.value ? S.gold : S.gray,
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: "pointer",
                    fontFamily: "inherit",
                    transition: "all 0.2s"
                  }}
                >
                  {filter.icon} {filter.label}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Transaction list */}
        {displayedTransactions.length === 0 ? (
          <div style={{ padding: 40, textAlign: "center", color: S.grayLight }}>
            <div style={{ fontSize: 40, marginBottom: 12 }}>📭</div>
            <div style={{ fontSize: 14, fontWeight: 600 }}>No transactions found</div>
            <div style={{ fontSize: 12, marginTop: 4 }}>Your transaction history will appear here</div>
          </div>
        ) : (
          <>
            {displayedTransactions.map((txn, i) => (
              <div key={txn.id} style={{
                padding: "14px 20px", display: "flex", alignItems: "center", gap: 14,
                borderBottom: i < displayedTransactions.length - 1 ? "1px solid #f8fafc" : "none",
                transition: "background 0.2s",
                cursor: "pointer"
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = "#f8fafc"}
              onMouseLeave={(e) => e.currentTarget.style.background = "transparent"}
              >
                <div style={{
                  width: 38, height: 38, borderRadius: 10, display: "flex", alignItems: "center", justifyContent: "center",
                  background: txn.type === "credit" ? S.greenBg : S.redBg,
                  color: txn.type === "credit" ? S.green : S.red
                }}>
                  {txn.type === "credit" ? Icons.arrowDown : Icons.arrowUp}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: S.navy }}>{txn.description}</div>
                  <div style={{ fontSize: 12, color: S.grayLight, marginTop: 2 }}>
                    {txn.date} • {txn.ref}
                    {txn.status && txn.status !== 'completed' && (
                      <span style={{
                        marginLeft: 8,
                        padding: "2px 6px",
                        borderRadius: 4,
                        fontSize: 10,
                        fontWeight: 700,
                        background: txn.status === 'pending' ? S.goldPale : S.redBg,
                        color: txn.status === 'pending' ? S.gold : S.red
                      }}>
                        {txn.status.toUpperCase()}
                      </span>
                    )}
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{
                    fontSize: 15, fontWeight: 700, fontFamily: "'Space Mono', monospace",
                    color: txn.type === "credit" ? S.green : S.red
                  }}>
                    {txn.type === "credit" ? "+" : "−"}₦{txn.amount.toLocaleString()}
                  </div>
                  <div style={{ fontSize: 11, color: S.grayLight }}>Bal: ₦{txn.balance.toLocaleString()}</div>
                </div>
              </div>
            ))}

            {/* Show count when viewing all */}
            {showAllTransactions && (
              <div style={{
                padding: "12px 20px",
                background: "#f8fafc",
                textAlign: "center",
                fontSize: 12,
                color: S.gray,
                fontWeight: 600
              }}>
                Showing {displayedTransactions.length} of {filteredTransactions.length} transactions
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}

// ─── FUND WALLET MODAL ──────────────────────────────────────────
function FundWalletModal({ onClose, onFund, onBankTransfer }) {
  const [amount, setAmount] = useState("");
  const [method, setMethod] = useState("card");

  const presets = [1000, 2000, 5000, 10000, 20000, 50000];

  const handlePay = () => {
    if (!amount) return;

    const amountValue = parseInt(amount);

    if (method === "transfer") {
      // Open bank transfer modal
      onBankTransfer(amountValue);
    } else if (method === "card") {
      // Use existing Paystack flow
      onFund(amountValue);
    } else {
      // Other payment methods (LibertyPay, etc.)
      alert(`${method} payment coming soon!`);
    }
  };

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 100, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'DM Sans', sans-serif" }}>
      <div onClick={onClose} style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.5)" }} />
      <div style={{ position: "relative", background: "#fff", borderRadius: 18, width: 420, maxHeight: "90vh", overflow: "auto", boxShadow: "0 20px 60px rgba(0,0,0,0.2)", animation: "fadeIn 0.3s ease" }}>
        <div style={{ padding: "20px 24px", borderBottom: "1px solid #f1f5f9", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3 style={{ fontSize: 18, fontWeight: 700, color: S.navy, margin: 0 }}>Fund Wallet</h3>
          <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", color: S.gray, padding: 4 }}>{Icons.close}</button>
        </div>
        <div style={{ padding: 24 }}>
          <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#334155", marginBottom: 8 }}>Amount (₦)</label>
          <input value={amount} onChange={e => setAmount(e.target.value.replace(/[^0-9]/g, ""))} placeholder="Enter amount"
            style={{ width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 14px", height: 48, fontSize: 20, fontWeight: 700, fontFamily: "'Space Mono', monospace", textAlign: "center" }} />

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8, marginTop: 12 }}>
            {presets.map(p => (
              <button key={p} onClick={() => setAmount(p.toString())} style={{
                padding: "8px", borderRadius: 8, border: amount === p.toString() ? `2px solid ${S.gold}` : "1.5px solid #e2e8f0",
                background: amount === p.toString() ? S.goldPale : "#fff", cursor: "pointer",
                fontSize: 14, fontWeight: 600, color: S.navy, fontFamily: "'Space Mono', monospace"
              }}>₦{p.toLocaleString()}</button>
            ))}
          </div>

          <div style={{ marginTop: 20 }}>
            <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#334155", marginBottom: 8 }}>Payment Method</label>
            {[
              { id: "card", label: "Card Payment", sub: "Visa, Mastercard, Verve" },
              { id: "transfer", label: "Bank Transfer", sub: "Instant confirmation" },
              { id: "liberty", label: "LibertyPay", sub: "Zero transaction fee" },
            ].map(m => (
              <button key={m.id} onClick={() => setMethod(m.id)} style={{
                width: "100%", display: "flex", alignItems: "center", gap: 12, padding: "12px 14px", marginBottom: 6,
                border: method === m.id ? `2px solid ${S.gold}` : "1.5px solid #e2e8f0", borderRadius: 10,
                background: method === m.id ? S.goldPale : "#fff", cursor: "pointer", fontFamily: "inherit"
              }}>
                <div style={{ width: 18, height: 18, borderRadius: "50%", border: `2px solid ${method === m.id ? S.gold : "#cbd5e1"}`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  {method === m.id && <div style={{ width: 9, height: 9, borderRadius: "50%", background: S.gold }} />}
                </div>
                <div style={{ textAlign: "left" }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: S.navy }}>{m.label}</div>
                  <div style={{ fontSize: 11, color: S.grayLight }}>{m.sub}</div>
                </div>
                {m.id === "liberty" && <span style={{ marginLeft: "auto", fontSize: 10, fontWeight: 700, padding: "2px 8px", borderRadius: 6, background: S.greenBg, color: S.green }}>FREE</span>}
              </button>
            ))}
          </div>

          <button onClick={handlePay} disabled={!amount}
            style={{
              width: "100%", height: 48, border: "none", borderRadius: 10, fontSize: 15, fontWeight: 700, cursor: amount ? "pointer" : "default",
              background: amount ? `linear-gradient(135deg, ${S.gold}, ${S.goldLight})` : "#e2e8f0",
              color: amount ? S.navy : "#94a3b8", fontFamily: "inherit", marginTop: 16,
              boxShadow: amount ? "0 4px 12px rgba(232,168,56,0.3)" : "none"
            }}>
            {amount ? `Pay ₦${parseInt(amount).toLocaleString()}` : "Enter Amount"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── BANK TRANSFER MODAL ────────────────────────────────────────
function BankTransferModal({ amount, onClose, onSuccess }) {
  const [state, setState] = useState('loading'); // 'loading', 'show-details', 'confirming', 'success'
  const [copied, setCopied] = useState(false);

  // Bank details
  const bankDetails = {
    bankName: "Wema Bank",
    accountNumber: "7924567890",
    accountName: "Assured Express Limited"
  };

  // Initial loading
  useEffect(() => {
    const timer = setTimeout(() => {
      setState('show-details');
    }, 2500);
    return () => clearTimeout(timer);
  }, []);

  const copyAccountNumber = () => {
    navigator.clipboard.writeText(bankDetails.accountNumber);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleConfirmPayment = () => {
    setState('confirming');
    setTimeout(() => {
      setState('success');
    }, 2500);
  };

  const handleClose = () => {
    if (state === 'success' && onSuccess) {
      onSuccess();
    }
    onClose();
  };

  // Loading Spinner Component
  const LoadingSpinner = () => (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "60px 40px" }}>
      <div style={{
        width: 60,
        height: 60,
        border: `4px solid ${S.goldPale}`,
        borderTop: `4px solid ${S.gold}`,
        borderRadius: "50%",
        animation: "spin 1s linear infinite"
      }} />
      <p style={{ marginTop: 24, fontSize: 15, fontWeight: 600, color: S.navy }}>
        {state === 'loading' ? 'Generating account details...' : 'Processing confirmation...'}
      </p>
      <p style={{ marginTop: 8, fontSize: 13, color: S.grayLight }}>Please wait</p>
    </div>
  );

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 100, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'DM Sans', sans-serif" }}>
      <div onClick={handleClose} style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.5)" }} />
      <div style={{ position: "relative", background: "#fff", borderRadius: 18, width: 440, maxHeight: "90vh", overflow: "auto", boxShadow: "0 20px 60px rgba(0,0,0,0.2)", animation: "fadeIn 0.3s ease" }}>

        {/* Header */}
        <div style={{ padding: "20px 24px", borderBottom: "1px solid #f1f5f9", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3 style={{ fontSize: 18, fontWeight: 700, color: S.navy, margin: 0 }}>
            {state === 'success' ? 'Payment Confirmed' : 'Bank Transfer'}
          </h3>
          <button onClick={handleClose} style={{ background: "none", border: "none", cursor: "pointer", color: S.gray, padding: 4 }}>
            {Icons.close}
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: 24 }}>
          {/* Loading State */}
          {(state === 'loading' || state === 'confirming') && <LoadingSpinner />}

          {/* Show Bank Details */}
          {state === 'show-details' && (
            <div>
              {/* Amount to Transfer */}
              <div style={{ background: S.goldPale, borderRadius: 12, padding: 20, marginBottom: 20, textAlign: "center" }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: S.grayLight, marginBottom: 6 }}>Amount to Transfer</div>
                <div style={{ fontSize: 32, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono', monospace" }}>
                  ₦{amount.toLocaleString()}
                </div>
              </div>

              {/* Bank Details */}
              <div style={{ background: "#f8fafc", borderRadius: 12, padding: 20, marginBottom: 20 }}>
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: S.grayLight, marginBottom: 4 }}>Bank Name</div>
                  <div style={{ fontSize: 16, fontWeight: 700, color: S.navy }}>{bankDetails.bankName}</div>
                </div>

                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: S.grayLight, marginBottom: 4 }}>Account Number</div>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <div style={{ fontSize: 20, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono', monospace", flex: 1 }}>
                      {bankDetails.accountNumber}
                    </div>
                    <button onClick={copyAccountNumber} style={{
                      padding: "6px 12px",
                      borderRadius: 8,
                      border: "none",
                      background: copied ? S.greenBg : S.goldPale,
                      color: copied ? S.green : S.gold,
                      fontSize: 12,
                      fontWeight: 700,
                      cursor: "pointer",
                      fontFamily: "inherit",
                      transition: "all 0.2s"
                    }}>
                      {copied ? '✓ Copied' : 'Copy'}
                    </button>
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: S.grayLight, marginBottom: 4 }}>Account Name</div>
                  <div style={{ fontSize: 16, fontWeight: 700, color: S.navy }}>{bankDetails.accountName}</div>
                </div>
              </div>

              {/* Instructions */}
              <div style={{ background: "#fffbeb", border: "1px solid #fef3c7", borderRadius: 10, padding: 16, marginBottom: 20 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: "#92400e", marginBottom: 8 }}>⚠️ Important Instructions</div>
                <ul style={{ margin: 0, paddingLeft: 20, fontSize: 12, color: "#78350f", lineHeight: 1.6 }}>
                  <li>Transfer exactly <strong>₦{amount.toLocaleString()}</strong> to the account above</li>
                  <li>Your wallet will be credited within 5-10 minutes after payment</li>
                  <li>Click "I have paid" only after completing the transfer</li>
                </ul>
              </div>

              {/* Confirm Button */}
              <button onClick={handleConfirmPayment} style={{
                width: "100%",
                height: 48,
                border: "none",
                borderRadius: 10,
                fontSize: 15,
                fontWeight: 700,
                cursor: "pointer",
                background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`,
                color: S.navy,
                fontFamily: "inherit",
                boxShadow: "0 4px 12px rgba(232,168,56,0.3)"
              }}>
                I have paid
              </button>
            </div>
          )}

          {/* Success State */}
          {state === 'success' && (
            <div style={{ textAlign: "center", padding: "40px 20px" }}>
              {/* Success Icon */}
              <div style={{
                width: 80,
                height: 80,
                borderRadius: "50%",
                background: S.greenBg,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                margin: "0 auto 24px",
                animation: "scaleIn 0.5s ease"
              }}>
                <div style={{ fontSize: 40, color: S.green }}>✓</div>
              </div>

              {/* Success Message */}
              <h3 style={{ fontSize: 20, fontWeight: 800, color: S.navy, margin: "0 0 12px" }}>
                Payment Confirmation Received!
              </h3>
              <p style={{ fontSize: 14, color: S.gray, lineHeight: 1.6, margin: "0 0 24px" }}>
                Your wallet will be credited once payment is verified. This usually takes 5-10 minutes.
              </p>

              {/* Transaction Details */}
              <div style={{ background: "#f8fafc", borderRadius: 10, padding: 16, marginBottom: 24, textAlign: "left" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                  <span style={{ fontSize: 13, color: S.grayLight }}>Amount</span>
                  <span style={{ fontSize: 13, fontWeight: 700, color: S.navy }}>₦{amount.toLocaleString()}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                  <span style={{ fontSize: 13, color: S.grayLight }}>Bank</span>
                  <span style={{ fontSize: 13, fontWeight: 700, color: S.navy }}>{bankDetails.bankName}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ fontSize: 13, color: S.grayLight }}>Status</span>
                  <span style={{ fontSize: 12, fontWeight: 700, padding: "2px 8px", borderRadius: 6, background: "#fef3c7", color: "#92400e" }}>
                    Pending Verification
                  </span>
                </div>
              </div>

              {/* Done Button */}
              <button onClick={handleClose} style={{
                width: "100%",
                height: 48,
                border: "none",
                borderRadius: 10,
                fontSize: 15,
                fontWeight: 700,
                cursor: "pointer",
                background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`,
                color: S.navy,
                fontFamily: "inherit",
                boxShadow: "0 4px 12px rgba(232,168,56,0.3)"
              }}>
                Done
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Add keyframe animations */}
      <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        @keyframes scaleIn {
          0% { transform: scale(0); }
          50% { transform: scale(1.1); }
          100% { transform: scale(1); }
        }
      `}</style>
    </div>
  );
}

// ─── SETTINGS SCREEN ────────────────────────────────────────────
function SettingsScreen({ currentUser, onUpdateUser, onShowNotif }) {
  const [businessName, setBusinessName] = useState(currentUser?.business_name || "");
  const [contactName, setContactName] = useState(currentUser?.contact_name || "");
  const [email, setEmail] = useState(currentUser?.email || "");
  const [address, setAddress] = useState(currentUser?.address || "");
  const [loading, setLoading] = useState(false);

  // Addresses state
  const [addresses, setAddresses] = useState([]);
  const [showAddAddress, setShowAddAddress] = useState(false);
  const [editingAddress, setEditingAddress] = useState(null);
  const [newAddressLabel, setNewAddressLabel] = useState("");
  const [newAddressText, setNewAddressText] = useState("");

  // Update state when currentUser changes
  useEffect(() => {
    if (currentUser) {
      setBusinessName(currentUser.business_name || "");
      setContactName(currentUser.contact_name || "");
      setEmail(currentUser.email || "");
      setAddress(currentUser.address || "");
      loadAddresses();
    }
  }, [currentUser]);

  const loadAddresses = async () => {
    try {
      const response = await window.API.Auth.getAddresses();
      if (response.success) {
        setAddresses(response.addresses || []);
      }
    } catch (error) {
      console.error('Failed to load addresses:', error);
    }
  };

  const handleSaveChanges = async () => {
    try {
      setLoading(true);

      const response = await window.API.Auth.updateProfile({
        business_name: businessName,
        contact_name: contactName,
        email: email,
        address: address,
      });

      if (response.success) {
        // Update user in localStorage
        window.API.Token.setUser(response.user);

        // Notify parent to update currentUser
        if (onUpdateUser) {
          onUpdateUser(response.user);
        }

        if (onShowNotif) {
          onShowNotif('Profile updated successfully!', 'success');
        }
      } else {
        const errorMsg = response.errors?.non_field_errors?.[0] || 'Failed to update profile';
        if (onShowNotif) {
          onShowNotif(errorMsg, 'error');
        }
      }
    } catch (error) {
      console.error('Update profile error:', error);
      if (onShowNotif) {
        onShowNotif(error.message || 'Failed to update profile', 'error');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSaveAddress = async () => {
    if (!newAddressLabel.trim() || !newAddressText.trim()) {
      if (onShowNotif) {
        onShowNotif('Please fill in all address fields', 'error');
      }
      return;
    }

    try {
      setLoading(true);
      const addressData = {
        label: newAddressLabel,
        address: newAddressText,
        is_default: addresses.length === 0 // First address is default
      };

      let response;
      if (editingAddress) {
        response = await window.API.Auth.updateAddress(editingAddress.id, addressData);
      } else {
        response = await window.API.Auth.createAddress(addressData);
      }

      if (response.success) {
        await loadAddresses();
        setShowAddAddress(false);
        setEditingAddress(null);
        setNewAddressLabel("");
        setNewAddressText("");
        if (onShowNotif) {
          onShowNotif(editingAddress ? 'Address updated!' : 'Address added!', 'success');
        }
      }
    } catch (error) {
      if (onShowNotif) {
        onShowNotif(error.message || 'Failed to save address', 'error');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleEditAddress = (addr) => {
    setEditingAddress(addr);
    setNewAddressLabel(addr.label);
    setNewAddressText(addr.address);
    setShowAddAddress(true);
  };

  const handleDeleteAddress = async (addressId) => {
    if (!confirm('Are you sure you want to delete this address?')) return;

    try {
      setLoading(true);
      const response = await window.API.Auth.deleteAddress(addressId);
      if (response.success) {
        await loadAddresses();
        if (onShowNotif) {
          onShowNotif('Address deleted!', 'success');
        }
      }
    } catch (error) {
      if (onShowNotif) {
        onShowNotif(error.message || 'Failed to delete address', 'error');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSetDefault = async (addressId) => {
    try {
      setLoading(true);
      const response = await window.API.Auth.setDefaultAddress(addressId);
      if (response.success) {
        await loadAddresses();
        if (onShowNotif) {
          onShowNotif('Default address updated!', 'success');
        }
      }
    } catch (error) {
      if (onShowNotif) {
        onShowNotif(error.message || 'Failed to set default address', 'error');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 600, margin: "0 auto", animation: "fadeIn 0.3s ease" }}>
      <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", overflow: "hidden" }}>
        <div style={{ padding: "20px 24px", borderBottom: "1px solid #f1f5f9" }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, color: S.navy, margin: 0 }}>Business Profile</h3>
        </div>
        <div style={{ padding: 24 }}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#334155", marginBottom: 6 }}>Business Name</label>
            <input
              value={businessName}
              onChange={(e) => setBusinessName(e.target.value)}
              placeholder="Enter business name"
              style={{ width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 14px", height: 44, fontSize: 14, fontFamily: "inherit" }}
            />
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#334155", marginBottom: 6 }}>Contact Name</label>
            <input
              value={contactName}
              onChange={(e) => setContactName(e.target.value)}
              placeholder="Enter contact name"
              style={{ width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 14px", height: 44, fontSize: 14, fontFamily: "inherit" }}
            />
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#334155", marginBottom: 6 }}>Phone</label>
            <input
              value={currentUser?.phone ? `+234 ${currentUser.phone}` : "N/A"}
              disabled
              style={{ width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 14px", height: 44, fontSize: 14, fontFamily: "inherit", background: "#f8fafc", color: "#94a3b8", cursor: "not-allowed" }}
            />
            <p style={{ fontSize: 12, color: "#64748b", marginTop: 4, marginBottom: 0 }}>Phone number cannot be changed</p>
          </div>

          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#334155", marginBottom: 6 }}>Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter email address"
              style={{ width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 14px", height: 44, fontSize: 14, fontFamily: "inherit" }}
            />
          </div>

          <div style={{ marginBottom: 24 }}>
            <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#334155", marginBottom: 6 }}>Address</label>
            <textarea
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Enter business address"
              rows={3}
              style={{ width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "12px 14px", fontSize: 14, fontFamily: "inherit", resize: "vertical" }}
            />
          </div>

          <button
            onClick={handleSaveChanges}
            disabled={loading}
            style={{
              padding: "10px 24px", borderRadius: 10, border: "none", cursor: loading ? "not-allowed" : "pointer",
              background: loading ? "#cbd5e1" : `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`,
              color: S.navy,
              fontWeight: 700, fontSize: 14, fontFamily: "inherit",
              opacity: loading ? 0.6 : 1
            }}
          >
            {loading ? "Saving..." : "Save Changes"}
          </button>
        </div>
      </div>

      {/* Saved Addresses */}
      <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", overflow: "hidden", marginTop: 16 }}>
        <div style={{ padding: "20px 24px", borderBottom: "1px solid #f1f5f9", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, color: S.navy, margin: 0 }}>Saved Addresses</h3>
          {addresses.length < 3 && !showAddAddress && (
            <button
              onClick={() => {
                setShowAddAddress(true);
                setEditingAddress(null);
                setNewAddressLabel("");
                setNewAddressText("");
              }}
              style={{
                padding: "6px 12px",
                borderRadius: 8,
                border: "none",
                background: S.goldPale,
                color: S.gold,
                fontSize: 12,
                fontWeight: 600,
                cursor: "pointer",
                fontFamily: "inherit"
              }}
            >
              + Add Address
            </button>
          )}
        </div>
        <div style={{ padding: 24 }}>
          {/* Add/Edit Address Form */}
          {showAddAddress && (
            <div style={{ marginBottom: 20, padding: 16, background: "#f8fafc", borderRadius: 10, border: "1px solid #e2e8f0" }}>
              <div style={{ marginBottom: 12 }}>
                <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#334155", marginBottom: 6 }}>
                  Label (e.g., Office, Warehouse, Home)
                </label>
                <input
                  value={newAddressLabel}
                  onChange={(e) => setNewAddressLabel(e.target.value)}
                  placeholder="Enter label"
                  style={{ width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 14px", height: 40, fontSize: 14, fontFamily: "inherit", background: "#fff" }}
                />
              </div>
              <div style={{ marginBottom: 12 }}>
                <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#334155", marginBottom: 6 }}>
                  Address
                </label>
                <AddressAutocompleteInput
                  value={newAddressText}
                  onChange={setNewAddressText}
                  placeholder="Enter full address (start typing for suggestions)"
                  style={{ width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 14px", height: 80, fontSize: 14, fontFamily: "inherit", background: "#fff" }}
                />
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  onClick={handleSaveAddress}
                  disabled={loading}
                  style={{
                    padding: "8px 16px",
                    borderRadius: 8,
                    border: "none",
                    background: loading ? "#cbd5e1" : S.gold,
                    color: S.navy,
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: loading ? "not-allowed" : "pointer",
                    fontFamily: "inherit"
                  }}
                >
                  {loading ? "Saving..." : (editingAddress ? "Update" : "Save")}
                </button>
                <button
                  onClick={() => {
                    setShowAddAddress(false);
                    setEditingAddress(null);
                    setNewAddressLabel("");
                    setNewAddressText("");
                  }}
                  style={{
                    padding: "8px 16px",
                    borderRadius: 8,
                    border: "1px solid #e2e8f0",
                    background: "#fff",
                    color: S.gray,
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: "pointer",
                    fontFamily: "inherit"
                  }}
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {/* Address List */}
          {addresses.length === 0 ? (
            <div style={{ textAlign: "center", padding: 20, color: S.grayLight }}>
              <div style={{ fontSize: 40, marginBottom: 8 }}>📍</div>
              <div style={{ fontSize: 14, fontWeight: 600 }}>No saved addresses</div>
              <div style={{ fontSize: 12, marginTop: 4 }}>Add up to 3 addresses for quick order placement</div>
            </div>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {addresses.map((addr) => (
                <div
                  key={addr.id}
                  style={{
                    padding: 14,
                    border: addr.is_default ? `2px solid ${S.gold}` : "1px solid #e2e8f0",
                    borderRadius: 10,
                    background: addr.is_default ? S.goldPale : "#fff",
                    position: "relative"
                  }}
                >
                  {addr.is_default && (
                    <div style={{
                      position: "absolute",
                      top: -8,
                      right: 12,
                      background: S.gold,
                      color: S.navy,
                      fontSize: 10,
                      fontWeight: 700,
                      padding: "2px 8px",
                      borderRadius: 6
                    }}>
                      ⭐ DEFAULT
                    </div>
                  )}
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start", marginBottom: 8 }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 14, fontWeight: 700, color: S.navy, marginBottom: 4 }}>
                        {addr.label}
                      </div>
                      <div style={{ fontSize: 13, color: S.gray, lineHeight: 1.5 }}>
                        {addr.address}
                      </div>
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                    {!addr.is_default && (
                      <button
                        onClick={() => handleSetDefault(addr.id)}
                        disabled={loading}
                        style={{
                          padding: "4px 10px",
                          borderRadius: 6,
                          border: "1px solid #e2e8f0",
                          background: "#fff",
                          color: S.gold,
                          fontSize: 11,
                          fontWeight: 600,
                          cursor: loading ? "not-allowed" : "pointer",
                          fontFamily: "inherit"
                        }}
                      >
                        Set as Default
                      </button>
                    )}
                    <button
                      onClick={() => handleEditAddress(addr)}
                      disabled={loading}
                      style={{
                        padding: "4px 10px",
                        borderRadius: 6,
                        border: "1px solid #e2e8f0",
                        background: "#fff",
                        color: S.navy,
                        fontSize: 11,
                        fontWeight: 600,
                        cursor: loading ? "not-allowed" : "pointer",
                        fontFamily: "inherit"
                      }}
                    >
                      ✏️ Edit
                    </button>
                    <button
                      onClick={() => handleDeleteAddress(addr.id)}
                      disabled={loading}
                      style={{
                        padding: "4px 10px",
                        borderRadius: 6,
                        border: "1px solid #fee",
                        background: "#fff",
                        color: S.red,
                        fontSize: 11,
                        fontWeight: 600,
                        cursor: loading ? "not-allowed" : "pointer",
                        fontFamily: "inherit"
                      }}
                    >
                      🗑️ Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {addresses.length >= 3 && (
            <div style={{ marginTop: 12, padding: 10, background: "#f8fafc", borderRadius: 8, textAlign: "center", fontSize: 12, color: S.gray }}>
              Maximum of 3 addresses reached
            </div>
          )}
        </div>
      </div>

      <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", overflow: "hidden", marginTop: 16 }}>
        <div style={{ padding: "20px 24px", borderBottom: "1px solid #f1f5f9" }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, color: S.navy, margin: 0 }}>Notifications</h3>
        </div>
        <div style={{ padding: 24 }}>
          {["Email notifications", "SMS alerts", "Push notifications"].map((n, i) => (
            <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 0", borderBottom: i < 2 ? "1px solid #f8fafc" : "none" }}>
              <span style={{ fontSize: 14, color: S.navy }}>{n}</span>
              <div style={{ width: 44, height: 24, borderRadius: 12, background: S.gold, padding: 2, cursor: "pointer" }}>
                <div style={{ width: 20, height: 20, borderRadius: "50%", background: "#fff", marginLeft: 20 }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── SUPPORT SCREEN ─────────────────────────────────────────────
function SupportScreen() {
  return (
    <div style={{ maxWidth: 600, margin: "0 auto", animation: "fadeIn 0.3s ease" }}>
      <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: 24, marginBottom: 16 }}>
        <h3 style={{ fontSize: 16, fontWeight: 700, color: S.navy, marginBottom: 8 }}>Need help?</h3>
        <p style={{ fontSize: 14, color: S.gray, lineHeight: 1.6 }}>Our support team is available 7am - 12am daily.</p>
        <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
          <button style={{
            flex: 1, padding: "14px", borderRadius: 12, border: "none", cursor: "pointer",
            background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy,
            fontWeight: 700, fontSize: 14, fontFamily: "inherit"
          }}>Call Support</button>
          <button style={{
            flex: 1, padding: "14px", borderRadius: 12, border: `1.5px solid ${S.navy}`,
            cursor: "pointer", background: "#fff", color: S.navy,
            fontWeight: 700, fontSize: 14, fontFamily: "inherit"
          }}>WhatsApp</button>
        </div>
      </div>

      <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", overflow: "hidden" }}>
        <div style={{ padding: "20px 24px", borderBottom: "1px solid #f1f5f9" }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, color: S.navy, margin: 0 }}>Frequently Asked Questions</h3>
        </div>
        {[
          { q: "How do I fund my wallet?", a: "Click 'Fund Wallet' and choose from card, bank transfer, USSD, or LibertyPay." },
          { q: "How long does delivery take?", a: "Same-day delivery across Lagos typically takes 30 minutes to 2 hours depending on distance and traffic." },
          { q: "What happens if my delivery fails?", a: "You'll receive a full refund to your wallet for any undelivered orders." },
          { q: "Can I schedule deliveries?", a: "Yes, select a future pickup time when creating your order." },
          { q: "What areas do you cover?", a: "We currently operate across all of Lagos including Island, Mainland, Lekki, and Ikeja." },
        ].map((faq, i) => (
          <details key={i} style={{ borderBottom: "1px solid #f8fafc" }}>
            <summary style={{ padding: "14px 20px", fontSize: 14, fontWeight: 600, color: S.navy, cursor: "pointer", listStyle: "none" }}>
              {faq.q}
            </summary>
            <div style={{ padding: "0 20px 14px", fontSize: 13, color: S.gray, lineHeight: 1.6 }}>{faq.a}</div>
          </details>
        ))}
      </div>
    </div>
  );
}

// ─── MY WEBSITE SCREEN (Instant Web) ────────────────────────────
function WebsiteScreen({ onCreateDelivery }) {
  const [activeTab, setActiveTab] = useState("sites");
  const [showCreate, setShowCreate] = useState(false);
  const [selectedSite, setSelectedSite] = useState(null);
  const [orderPipeline, setOrderPipeline] = useState("new");

  const demoSites = [
    { id: 1, name: "Vivid Print Main Store", domain: "vividprint.axpress.shop", status: "live", visitors: 342, orders: 18, revenue: 287400, products: 24, color: "#E8A838" },
    { id: 2, name: "Vivid Print Lekki Branch", domain: "vividprint-lekki.axpress.shop", status: "live", visitors: 156, orders: 7, revenue: 94500, products: 12, color: "#10B981" },
  ];

  const demoProducts = [
    { name: "Business Card (500 pcs)", price: 15000, stock: 50, img: "🪪" },
    { name: "Flyer A5 (1000 pcs)", price: 25000, stock: 30, img: "📄" },
    { name: "Banner 3x6ft", price: 18000, stock: 20, img: "🖼️" },
    { name: "Invoice Book (50 leaves)", price: 8000, stock: 100, img: "📒" },
    { name: "Letterhead (500 pcs)", price: 12000, stock: 45, img: "📃" },
    { name: "Sticker Roll (500 pcs)", price: 9500, stock: 60, img: "🏷️" },
  ];

  const pipelineStages = [
    { id: "new", label: "New Orders", count: 5, color: "#3B82F6", icon: "🔵" },
    { id: "processing", label: "Processing", count: 3, color: "#F59E0B", icon: "🟡" },
    { id: "ready", label: "Ready for Delivery", count: 2, color: "#8B5CF6", icon: "🟣" },
    { id: "dispatched", label: "Dispatched", count: 4, color: "#10B981", icon: "🟢" },
    { id: "completed", label: "Completed", count: 12, color: "#6B7280", icon: "✅" },
    { id: "canceled", label: "Canceled", count: 1, color: "#EF4444", icon: "🔴" },
  ];

  const pipelineOrders = {
    new: [
      { id: "WEB-1042", customer: "Adebayo Johnson", items: "Business Card x2, Flyer x1", total: 55000, time: "4 min ago", phone: "08034567890" },
      { id: "WEB-1041", customer: "Funke Adeyemi", items: "Banner 3x6ft x3", total: 54000, time: "12 min ago", phone: "09012345678" },
      { id: "WEB-1040", customer: "Chidi Obi", items: "Invoice Book x5", total: 40000, time: "28 min ago", phone: "07011223344" },
      { id: "WEB-1039", customer: "Blessing Nwosu", items: "Letterhead x2", total: 24000, time: "1 hr ago", phone: "08155667788" },
      { id: "WEB-1038", customer: "Emeka Eze", items: "Sticker Roll x10", total: 95000, time: "2 hrs ago", phone: "09044332211" },
    ],
    processing: [
      { id: "WEB-1037", customer: "Tunde Bakare", items: "Business Card x5", total: 75000, time: "30 min ago", phone: "08098765432" },
      { id: "WEB-1036", customer: "Aisha Mohammed", items: "Flyer x2, Banner x1", total: 68000, time: "1 hr ago", phone: "07055443322" },
      { id: "WEB-1035", customer: "David Okonkwo", items: "Invoice Book x10", total: 80000, time: "2 hrs ago", phone: "08133445566" },
    ],
    ready: [
      { id: "WEB-1034", customer: "Grace Okafor", items: "Sticker Roll x5, Letterhead x3", total: 83500, time: "15 min ago", phone: "09066778899" },
      { id: "WEB-1033", customer: "Yusuf Aliyu", items: "Business Card x10", total: 150000, time: "45 min ago", phone: "08022334455" },
    ],
    dispatched: [
      { id: "WEB-1032", customer: "Ngozi Ibe", items: "Banner x2", total: 36000, time: "1 hr ago", phone: "07088990011", rider: "Musa K." },
      { id: "WEB-1031", customer: "Kola Peters", items: "Flyer x5", total: 125000, time: "2 hrs ago", phone: "08144556677", rider: "Ahmed B." },
    ],
    completed: [
      { id: "WEB-1028", customer: "Sade Williams", items: "Business Card x3", total: 45000, time: "Yesterday", phone: "09011224433" },
    ],
    canceled: [
      { id: "WEB-1025", customer: "Paul Eze", items: "Banner x1", total: 18000, time: "2 days ago", phone: "08077665544", reason: "Customer changed mind" },
    ],
  };

  const webTransactions = [
    { id: "WT-001", order: "WEB-1028", customer: "Sade Williams", amount: 45000, method: "Card", status: "success", date: "Feb 14, 2:30 PM" },
    { id: "WT-002", order: "WEB-1031", customer: "Kola Peters", amount: 125000, method: "Transfer", status: "success", date: "Feb 14, 1:15 PM" },
    { id: "WT-003", order: "WEB-1032", customer: "Ngozi Ibe", amount: 36000, method: "Card", status: "success", date: "Feb 14, 12:00 PM" },
    { id: "WT-004", order: "WEB-1034", customer: "Grace Okafor", amount: 83500, method: "Transfer", status: "pending", date: "Feb 14, 11:30 AM" },
    { id: "WT-005", order: "WEB-1037", customer: "Tunde Bakare", amount: 75000, method: "Card", status: "success", date: "Feb 14, 10:45 AM" },
  ];

  const tabs = [
    { id: "sites", label: "My Sites" },
    { id: "products", label: "Products" },
    { id: "orders", label: "Orders" },
    { id: "transactions", label: "Transactions" },
    { id: "customize", label: "Customize" },
  ];

  const currentOrders = pipelineOrders[orderPipeline] || [];

  return (
    <div style={{ animation: "fadeIn 0.3s ease" }}>
      {/* Hero Banner */}
      <div style={{
        background: `linear-gradient(135deg, ${S.navy} 0%, #0f1b33 100%)`, borderRadius: 16, padding: "28px 32px",
        marginBottom: 20, position: "relative", overflow: "hidden"
      }}>
        <div style={{ position: "absolute", top: -20, right: -20, width: 120, height: 120, borderRadius: "50%", background: "rgba(232,168,56,0.08)" }} />
        <div style={{ position: "absolute", bottom: -30, right: 80, width: 80, height: 80, borderRadius: "50%", background: "rgba(232,168,56,0.05)" }} />
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", position: "relative", zIndex: 1 }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
              <span style={{ background: S.green, color: "#fff", fontSize: 10, fontWeight: 700, padding: "3px 10px", borderRadius: 10 }}>FREE WITH AX</span>
            </div>
            <h2 style={{ color: "#fff", fontSize: 22, fontWeight: 800, margin: "0 0 6px" }}>Instant Website for Your Business</h2>
            <p style={{ color: "rgba(255,255,255,0.5)", fontSize: 13, margin: 0, maxWidth: 480 }}>
              Create a professional storefront in minutes. Accept orders online. Auto-dispatch deliveries via AX.
            </p>
          </div>
          <button onClick={() => setShowCreate(true)} style={{
            padding: "12px 28px", borderRadius: 12, border: "none", cursor: "pointer", fontFamily: "inherit",
            background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy, fontWeight: 700, fontSize: 14,
            boxShadow: "0 4px 12px rgba(232,168,56,0.3)"
          }}>+ Create New Site</button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 4, marginBottom: 20, background: "#fff", borderRadius: 12, padding: 4, border: "1px solid #e2e8f0" }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setActiveTab(t.id)} style={{
            flex: 1, padding: "10px 0", borderRadius: 10, border: "none", cursor: "pointer", fontFamily: "inherit",
            fontSize: 13, fontWeight: 600, transition: "all 0.2s",
            background: activeTab === t.id ? S.navy : "transparent",
            color: activeTab === t.id ? "#fff" : S.gray,
          }}>{t.label}</button>
        ))}
      </div>

      {/* ── MY SITES TAB ── */}
      {activeTab === "sites" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          {demoSites.map(site => (
            <div key={site.id} onClick={() => setSelectedSite(site)} style={{
              background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: 20, cursor: "pointer",
              transition: "all 0.2s", borderLeft: `4px solid ${site.color}`
            }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
                <h3 style={{ fontSize: 15, fontWeight: 700, color: S.navy, margin: 0 }}>{site.name}</h3>
                <span style={{ fontSize: 10, fontWeight: 700, padding: "3px 10px", borderRadius: 10, background: S.greenBg, color: S.green }}>LIVE</span>
              </div>
              <div style={{ fontSize: 12, color: S.gold, fontWeight: 600, fontFamily: "'Space Mono', monospace", marginBottom: 14 }}>
                🔗 {site.domain}
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8 }}>
                {[
                  { label: "Visitors", value: site.visitors },
                  { label: "Orders", value: site.orders },
                  { label: "Revenue", value: `₦${(site.revenue/1000).toFixed(0)}K` },
                  { label: "Products", value: site.products },
                ].map(s => (
                  <div key={s.label} style={{ textAlign: "center", padding: "8px 0", background: "#f8fafc", borderRadius: 8 }}>
                    <div style={{ fontSize: 16, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono', monospace" }}>{s.value}</div>
                    <div style={{ fontSize: 10, color: S.grayLight }}>{s.label}</div>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {/* Add New Site Card */}
          <div onClick={() => setShowCreate(true)} style={{
            background: "#fafbfc", borderRadius: 14, border: "2px dashed #e2e8f0", padding: 20, cursor: "pointer",
            display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: 180,
            transition: "all 0.2s"
          }}>
            <div style={{ fontSize: 36, marginBottom: 8, opacity: 0.4 }}>+</div>
            <div style={{ fontSize: 14, fontWeight: 700, color: S.navy }}>Add Another Store</div>
            <div style={{ fontSize: 12, color: S.grayLight, marginTop: 4 }}>New location or brand</div>
          </div>
        </div>
      )}

      {/* ── PRODUCTS TAB ── */}
      {activeTab === "products" && (
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <div style={{ fontSize: 14, color: S.gray }}>{demoProducts.length} products</div>
            <button style={{
              padding: "8px 20px", borderRadius: 10, border: "none", cursor: "pointer", fontFamily: "inherit",
              background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy, fontWeight: 700, fontSize: 13,
            }}>+ Add Product</button>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
            {demoProducts.map((p, i) => (
              <div key={i} style={{ background: "#fff", borderRadius: 12, border: "1px solid #e2e8f0", padding: 16, transition: "all 0.2s" }}>
                <div style={{ fontSize: 40, textAlign: "center", marginBottom: 10, background: "#f8fafc", borderRadius: 10, padding: "12px 0" }}>{p.img}</div>
                <div style={{ fontSize: 13, fontWeight: 700, color: S.navy }}>{p.name}</div>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: 8 }}>
                  <div style={{ fontSize: 15, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono', monospace" }}>₦{p.price.toLocaleString()}</div>
                  <div style={{ fontSize: 11, color: S.grayLight }}>{p.stock} in stock</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── ORDERS TAB (Pipeline) ── */}
      {activeTab === "orders" && (
        <div>
          {/* Pipeline stages */}
          <div style={{ display: "flex", gap: 6, marginBottom: 18, overflowX: "auto" }}>
            {pipelineStages.map(stage => (
              <button key={stage.id} onClick={() => setOrderPipeline(stage.id)} style={{
                padding: "10px 16px", borderRadius: 10, border: "none", cursor: "pointer", fontFamily: "inherit",
                fontSize: 12, fontWeight: 700, whiteSpace: "nowrap", transition: "all 0.2s",
                background: orderPipeline === stage.id ? stage.color : "#f1f5f9",
                color: orderPipeline === stage.id ? "#fff" : S.gray,
              }}>
                {stage.icon} {stage.label} ({stage.count})
              </button>
            ))}
          </div>

          {/* Order cards */}
          <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
            {currentOrders.map(order => (
              <div key={order.id} style={{
                background: "#fff", borderRadius: 12, border: "1px solid #e2e8f0", padding: "16px 20px",
                display: "flex", alignItems: "center", justifyContent: "space-between"
              }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
                    <span style={{ fontWeight: 800, color: S.navy, fontSize: 14, fontFamily: "'Space Mono', monospace" }}>{order.id}</span>
                    <span style={{ fontSize: 11, color: S.grayLight }}>{order.time}</span>
                  </div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: S.navy }}>{order.customer}</div>
                  <div style={{ fontSize: 12, color: S.gray, marginTop: 2 }}>{order.items}</div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: 16, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono', monospace" }}>₦{order.total.toLocaleString()}</div>
                  <div style={{ display: "flex", gap: 6, marginTop: 8, justifyContent: "flex-end" }}>
                    {orderPipeline === "new" && (
                      <button style={{
                        padding: "5px 14px", borderRadius: 8, border: "none", cursor: "pointer", fontFamily: "inherit",
                        background: "#3B82F6", color: "#fff", fontSize: 11, fontWeight: 700
                      }}>Accept</button>
                    )}
                    {orderPipeline === "processing" && (
                      <button style={{
                        padding: "5px 14px", borderRadius: 8, border: "none", cursor: "pointer", fontFamily: "inherit",
                        background: "#8B5CF6", color: "#fff", fontSize: 11, fontWeight: 700
                      }}>Mark Ready</button>
                    )}
                    {orderPipeline === "ready" && (
                      <button onClick={onCreateDelivery} style={{
                        padding: "5px 14px", borderRadius: 8, border: "none", cursor: "pointer", fontFamily: "inherit",
                        background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy, fontSize: 11, fontWeight: 700,
                        display: "flex", alignItems: "center", gap: 4
                      }}>🚀 Dispatch via AX</button>
                    )}
                    {orderPipeline === "dispatched" && order.rider && (
                      <span style={{ fontSize: 11, color: S.green, fontWeight: 600 }}>🏍️ {order.rider}</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Pipeline config hint */}
          <div style={{
            marginTop: 16, background: S.goldPale, borderRadius: 12, padding: "14px 20px",
            display: "flex", alignItems: "center", gap: 12, border: `1px solid ${S.gold}20`
          }}>
            <span style={{ fontSize: 20 }}>⚙️</span>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: S.navy }}>Customise Your Pipeline</div>
              <div style={{ fontSize: 12, color: S.gray }}>Add, remove, or rename stages to match your workflow. Orders in "Ready for Delivery" auto-create AX dispatch requests.</div>
            </div>
          </div>
        </div>
      )}

      {/* ── TRANSACTIONS TAB ── */}
      {activeTab === "transactions" && (
        <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", overflow: "hidden" }}>
          <div style={{
            display: "grid", gridTemplateColumns: "80px 90px 1fr 100px 80px 80px 140px", gap: 8,
            padding: "12px 20px", background: "#f8fafc", fontSize: 11, fontWeight: 700, color: S.grayLight, textTransform: "uppercase"
          }}>
            <span>ID</span><span>Order</span><span>Customer</span><span>Amount</span><span>Method</span><span>Status</span><span>Date</span>
          </div>
          {webTransactions.map(tx => (
            <div key={tx.id} style={{
              display: "grid", gridTemplateColumns: "80px 90px 1fr 100px 80px 80px 140px", gap: 8,
              padding: "12px 20px", borderTop: "1px solid #f1f5f9", alignItems: "center"
            }}>
              <span style={{ fontSize: 12, fontFamily: "'Space Mono', monospace", color: S.grayLight }}>{tx.id}</span>
              <span style={{ fontSize: 12, fontWeight: 700, color: S.navy, fontFamily: "'Space Mono', monospace" }}>{tx.order}</span>
              <span style={{ fontSize: 13, color: S.navy }}>{tx.customer}</span>
              <span style={{ fontSize: 13, fontWeight: 700, color: S.navy, fontFamily: "'Space Mono', monospace" }}>₦{tx.amount.toLocaleString()}</span>
              <span style={{ fontSize: 11, color: S.gray }}>{tx.method}</span>
              <span style={{
                fontSize: 10, fontWeight: 700, padding: "2px 8px", borderRadius: 6, textAlign: "center",
                background: tx.status === "success" ? S.greenBg : S.goldPale,
                color: tx.status === "success" ? S.green : S.gold,
              }}>{tx.status === "success" ? "Paid" : "Pending"}</span>
              <span style={{ fontSize: 11, color: S.grayLight }}>{tx.date}</span>
            </div>
          ))}
        </div>
      )}

      {/* ── CUSTOMIZE TAB ── */}
      {activeTab === "customize" && (
        <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 20 }}>
          {/* Settings panel */}
          <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: 20 }}>
            <h3 style={{ fontSize: 15, fontWeight: 700, color: S.navy, margin: "0 0 16px" }}>Store Settings</h3>
            {[
              { label: "Store Name", value: "Vivid Print Main Store" },
              { label: "Tagline", value: "Quality printing, fast delivery" },
              { label: "WhatsApp", value: "08051832508" },
              { label: "Instagram", value: "@vividprintng" },
            ].map(f => (
              <div key={f.label} style={{ marginBottom: 12 }}>
                <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: S.grayLight, marginBottom: 4 }}>{f.label}</label>
                <input defaultValue={f.value} style={{
                  width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 8, padding: "0 12px", height: 38, fontSize: 13, fontFamily: "inherit"
                }} />
              </div>
            ))}

            <label style={{ display: "block", fontSize: 11, fontWeight: 600, color: S.grayLight, marginBottom: 4, marginTop: 8 }}>Brand Color</label>
            <div style={{ display: "flex", gap: 8 }}>
              {["#E8A838", "#3B82F6", "#10B981", "#EF4444", "#8B5CF6", "#1B2A4A"].map(c => (
                <div key={c} style={{
                  width: 32, height: 32, borderRadius: 8, background: c, cursor: "pointer",
                  border: c === "#E8A838" ? "3px solid #1B2A4A" : "3px solid transparent"
                }} />
              ))}
            </div>

            <button style={{
              marginTop: 16, width: "100%", padding: "10px 0", borderRadius: 10, border: "none", cursor: "pointer",
              background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy, fontWeight: 700, fontSize: 13, fontFamily: "inherit"
            }}>Save Changes</button>
          </div>

          {/* Live preview */}
          <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", overflow: "hidden" }}>
            <div style={{ padding: "10px 16px", background: "#f8fafc", borderBottom: "1px solid #e2e8f0", display: "flex", alignItems: "center", gap: 8 }}>
              <div style={{ display: "flex", gap: 4 }}>
                <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#EF4444" }} />
                <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#F59E0B" }} />
                <div style={{ width: 10, height: 10, borderRadius: "50%", background: "#10B981" }} />
              </div>
              <div style={{ flex: 1, background: "#fff", borderRadius: 6, padding: "5px 12px", fontSize: 11, color: S.grayLight, fontFamily: "'Space Mono', monospace" }}>
                vividprint.axpress.shop
              </div>
            </div>
            <div style={{ padding: 24 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
                <div style={{ width: 40, height: 40, borderRadius: 10, background: S.gold, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 18 }}>VP</div>
                <div>
                  <div style={{ fontSize: 16, fontWeight: 800, color: S.navy }}>Vivid Print</div>
                  <div style={{ fontSize: 11, color: S.grayLight }}>Quality printing, fast delivery</div>
                </div>
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 10 }}>
                {demoProducts.slice(0, 3).map((p, i) => (
                  <div key={i} style={{ border: "1px solid #e2e8f0", borderRadius: 10, padding: 12 }}>
                    <div style={{ fontSize: 28, textAlign: "center", padding: "8px 0", background: "#f8fafc", borderRadius: 8, marginBottom: 8 }}>{p.img}</div>
                    <div style={{ fontSize: 12, fontWeight: 600, color: S.navy }}>{p.name}</div>
                    <div style={{ fontSize: 13, fontWeight: 800, color: S.gold, marginTop: 4 }}>₦{p.price.toLocaleString()}</div>
                    <button style={{
                      width: "100%", marginTop: 8, padding: "6px 0", borderRadius: 8, border: "none",
                      background: S.navy, color: "#fff", fontSize: 11, fontWeight: 700, cursor: "pointer", fontFamily: "inherit"
                    }}>Add to Cart</button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── CREATE SITE MODAL ── */}
      {showCreate && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}
          onClick={() => setShowCreate(false)}>
          <div onClick={e => e.stopPropagation()} style={{
            background: "#fff", borderRadius: 20, padding: 32, width: 440, maxHeight: "80vh", overflowY: "auto",
            boxShadow: "0 24px 48px rgba(0,0,0,0.15)"
          }}>
            <h2 style={{ fontSize: 20, fontWeight: 800, color: S.navy, margin: "0 0 4px" }}>Create Your Store</h2>
            <p style={{ fontSize: 13, color: S.grayLight, margin: "0 0 20px" }}>Free forever with your AX merchant account</p>

            {["Store Name", "Subdomain", "Business Category", "WhatsApp Number"].map((f, i) => (
              <div key={f} style={{ marginBottom: 14 }}>
                <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: S.gray, marginBottom: 5 }}>{f}</label>
                {f === "Subdomain" ? (
                  <div style={{ display: "flex", border: "1.5px solid #e2e8f0", borderRadius: 10, overflow: "hidden" }}>
                    <input placeholder="yourstore" style={{ flex: 1, border: "none", padding: "0 12px", height: 40, fontSize: 13, fontFamily: "inherit" }} />
                    <span style={{ padding: "0 12px", background: "#f8fafc", borderLeft: "1px solid #e2e8f0", display: "flex", alignItems: "center", fontSize: 12, color: S.grayLight, fontFamily: "'Space Mono', monospace" }}>.axpress.shop</span>
                  </div>
                ) : f === "Business Category" ? (
                  <select style={{ width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 12px", height: 40, fontSize: 13, fontFamily: "inherit", background: "#fff" }}>
                    <option>Printing & Design</option><option>Fashion & Clothing</option><option>Electronics</option><option>Food & Beverage</option><option>Beauty & Cosmetics</option><option>General Retail</option><option>Services</option>
                  </select>
                ) : (
                  <input placeholder={f === "Store Name" ? "e.g. Vivid Print" : "e.g. 08051832508"} style={{
                    width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 12px", height: 40, fontSize: 13, fontFamily: "inherit"
                  }} />
                )}
              </div>
            ))}

            <button onClick={() => setShowCreate(false)} style={{
              width: "100%", padding: "14px 0", borderRadius: 12, border: "none", cursor: "pointer", fontFamily: "inherit",
              background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy, fontWeight: 700, fontSize: 15,
              boxShadow: "0 4px 12px rgba(232,168,56,0.3)", marginTop: 4
            }}>🚀 Launch My Store — Free</button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── WEBPOS SCREEN (Management Hub) ─────────────────────────────
function WebPOSScreen() {
  const [posTab, setPosTab] = useState("overview");
  const [showAddStaff, setShowAddStaff] = useState(false);
  const [showLaunch, setShowLaunch] = useState(false);

  // ─── Demo data ───
  const posInstances = [
    { id: 1, name: "Seeds & Pennies HQ", domain: "seedspennies-hq.paybox360.com", status: "online", clerks: 4, todaySales: 18, todayRevenue: 2340000, lastActive: "Just now", color: "#10B981" },
    { id: 2, name: "Seeds & Pennies Lekki", domain: "seedspennies-lekki.paybox360.com", status: "online", clerks: 2, todaySales: 7, todayRevenue: 945000, lastActive: "3 min ago", color: "#3B82F6" },
    { id: 3, name: "Liberty Assured Ikeja", domain: "liberty-ikeja.paybox360.com", status: "offline", clerks: 3, todaySales: 0, todayRevenue: 0, lastActive: "Yesterday", color: "#94a3b8" },
  ];

  const staff = [
    { id: 1, name: "Blessing Okonkwo", role: "Cashier", branch: "HQ", status: "active", pin: "••••", lastLogin: "Online now", sales: 8, revenue: 1120000 },
    { id: 2, name: "Ahmed Yusuf", role: "Cashier", branch: "HQ", status: "active", pin: "••••", lastLogin: "Online now", sales: 6, revenue: 874000 },
    { id: 3, name: "Chidi Nnamdi", role: "Supervisor", branch: "HQ", status: "active", pin: "••••", lastLogin: "Online now", sales: 4, revenue: 346000 },
    { id: 4, name: "Fatima Ibrahim", role: "Cashier", branch: "Lekki", status: "active", pin: "••••", lastLogin: "2 hrs ago", sales: 5, revenue: 632000 },
    { id: 5, name: "Emeka Obi", role: "Cashier", branch: "Lekki", status: "inactive", pin: "••••", lastLogin: "2 days ago", sales: 0, revenue: 0 },
    { id: 6, name: "Grace Adeyemi", role: "Cashier", branch: "Ikeja", status: "active", pin: "••••", lastLogin: "Yesterday 6:10 PM", sales: 12, revenue: 1580000 },
    { id: 7, name: "Tunde Bakare", role: "Manager", branch: "Ikeja", status: "active", pin: "••••", lastLogin: "Yesterday 6:15 PM", sales: 0, revenue: 0 },
  ];

  const salesHistory = [
    { id: "SAL-1050", branch: "HQ", clerk: "Blessing O.", items: 3, total: 506500, method: "Card", tag: "Table 1", date: "Feb 14, 3:45 PM", status: "completed" },
    { id: "SAL-1049", branch: "HQ", clerk: "Ahmed Y.", items: 1, total: 350000, method: "Transfer", tag: "Showroom", date: "Feb 14, 2:20 PM", status: "completed" },
    { id: "SAL-1048", branch: "Lekki", clerk: "Fatima I.", items: 5, total: 195000, method: "Cash", tag: "", date: "Feb 14, 1:10 PM", status: "completed" },
    { id: "SAL-1047", branch: "HQ", clerk: "Chidi N.", items: 2, total: 476000, method: "Split", tag: "VIP", date: "Feb 14, 11:45 AM", status: "completed" },
    { id: "SAL-1046", branch: "HQ", clerk: "Blessing O.", items: 1, total: 166490, method: "Cash", tag: "", date: "Feb 14, 10:30 AM", status: "completed" },
    { id: "SAL-1045", branch: "Lekki", clerk: "Fatima I.", items: 4, total: 73000, method: "Transfer", tag: "Bulk", date: "Feb 13, 5:00 PM", status: "completed" },
    { id: "SAL-1044", branch: "HQ", clerk: "Ahmed Y.", items: 2, total: 280000, method: "Card", tag: "", date: "Feb 13, 3:30 PM", status: "refunded" },
    { id: "SAL-1043", branch: "Ikeja", clerk: "Grace A.", items: 6, total: 1245000, method: "Transfer", tag: "Corporate", date: "Feb 13, 2:00 PM", status: "completed" },
    { id: "SAL-1042", branch: "Ikeja", clerk: "Grace A.", items: 1, total: 85000, method: "Cash", tag: "", date: "Feb 13, 12:15 PM", status: "completed" },
    { id: "SAL-1041", branch: "HQ", clerk: "Blessing O.", items: 3, total: 420000, method: "Card", tag: "Table 2", date: "Feb 13, 11:00 AM", status: "completed" },
  ];

  const summary = {
    todaySales: 25, todayRevenue: 3285000, weekRevenue: 18400000, avgTicket: 131400,
    topBranch: "HQ", topClerk: "Blessing O.", activeClerks: 4, totalClerks: 7
  };

  const revenueByBranch = [
    { branch: "HQ", revenue: 2340000, pct: 71 },
    { branch: "Lekki", revenue: 945000, pct: 29 },
  ];

  const tabs = [
    { id: "overview", label: "Overview" },
    { id: "sales", label: "Sales History" },
    { id: "staff", label: "Staff & Clerks" },
    { id: "terminals", label: "POS Terminals" },
    { id: "settings", label: "Settings" },
  ];

  return (
    <div style={{ animation: "fadeIn 0.3s ease" }}>
      {/* Hero Banner */}
      <div style={{
        background: `linear-gradient(135deg, ${S.navy} 0%, #0f1b33 100%)`, borderRadius: 16, padding: "28px 32px",
        marginBottom: 20, position: "relative", overflow: "hidden"
      }}>
        <div style={{ position: "absolute", top: -20, right: -20, width: 120, height: 120, borderRadius: "50%", background: "rgba(232,168,56,0.08)" }} />
        <div style={{ position: "absolute", bottom: -30, right: 100, width: 80, height: 80, borderRadius: "50%", background: "rgba(232,168,56,0.05)" }} />
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", position: "relative", zIndex: 1 }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
              <span style={{ fontSize: 11, fontWeight: 700, padding: "3px 10px", borderRadius: 10, background: "rgba(232,168,56,0.15)", color: S.gold }}>POWERED BY PAYBOX360</span>
              <span style={{ fontSize: 11, fontWeight: 700, padding: "3px 10px", borderRadius: 10, background: "rgba(16,185,129,0.15)", color: S.green }}>{summary.activeClerks} CLERKS ONLINE</span>
            </div>
            <h2 style={{ color: "#fff", fontSize: 22, fontWeight: 800, margin: "0 0 6px" }}>WebPOS — Sales Command Centre</h2>
            <p style={{ color: "rgba(255,255,255,0.5)", fontSize: 13, margin: 0, maxWidth: 520 }}>
              Launch POS terminals for your branches. Your clerks sell on Paybox360 — you monitor everything here.
            </p>
          </div>
          <button onClick={() => setShowLaunch(true)} style={{
            padding: "12px 28px", borderRadius: 12, border: "none", cursor: "pointer", fontFamily: "inherit",
            background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy, fontWeight: 700, fontSize: 14,
            boxShadow: "0 4px 12px rgba(232,168,56,0.3)"
          }}>+ Launch New POS</button>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: 4, marginBottom: 20, background: "#fff", borderRadius: 12, padding: 4, border: "1px solid #e2e8f0" }}>
        {tabs.map(t => (
          <button key={t.id} onClick={() => setPosTab(t.id)} style={{
            flex: 1, padding: "10px 0", borderRadius: 10, border: "none", cursor: "pointer", fontFamily: "inherit",
            fontSize: 13, fontWeight: 600, transition: "all 0.2s",
            background: posTab === t.id ? S.navy : "transparent",
            color: posTab === t.id ? "#fff" : S.gray,
          }}>{t.label}</button>
        ))}
      </div>

      {/* ═══ OVERVIEW TAB ═══ */}
      {posTab === "overview" && (
        <div>
          {/* Stats cards */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12, marginBottom: 20 }}>
            {[
              { label: "Today's Sales", value: summary.todaySales, sub: "transactions", icon: "🧾" },
              { label: "Today's Revenue", value: `₦${(summary.todayRevenue / 1000).toFixed(0)}K`, sub: "across all branches", icon: "💰" },
              { label: "This Week", value: `₦${(summary.weekRevenue / 1000000).toFixed(1)}M`, sub: "gross revenue", icon: "📈" },
              { label: "Avg Ticket", value: `₦${(summary.avgTicket / 1000).toFixed(0)}K`, sub: "per transaction", icon: "📊" },
            ].map(s => (
              <div key={s.label} style={{ background: "#fff", borderRadius: 12, border: "1px solid #e2e8f0", padding: 16, display: "flex", alignItems: "center", gap: 12 }}>
                <div style={{ width: 42, height: 42, borderRadius: 10, background: S.goldPale, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 20 }}>{s.icon}</div>
                <div>
                  <div style={{ fontSize: 11, color: S.grayLight, fontWeight: 600 }}>{s.label}</div>
                  <div style={{ fontSize: 20, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono', monospace" }}>{s.value}</div>
                  <div style={{ fontSize: 10, color: S.grayLight }}>{s.sub}</div>
                </div>
              </div>
            ))}
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 16 }}>
            {/* Live Feed */}
            <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: 20 }}>
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
                <h3 style={{ fontSize: 14, fontWeight: 700, color: S.navy, margin: 0 }}>Live Sales Feed</h3>
                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  <div style={{ width: 8, height: 8, borderRadius: "50%", background: S.green, animation: "pulse 2s infinite" }} />
                  <span style={{ fontSize: 11, color: S.green, fontWeight: 600 }}>Real-time</span>
                </div>
              </div>
              {salesHistory.slice(0, 6).map(sale => (
                <div key={sale.id} style={{
                  display: "flex", alignItems: "center", gap: 12, padding: "10px 0",
                  borderBottom: "1px solid #f8fafc"
                }}>
                  <div style={{
                    width: 34, height: 34, borderRadius: 8,
                    background: sale.branch === "HQ" ? "#EFF6FF" : sale.branch === "Lekki" ? "#F0FDF4" : "#FEF3C7",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    fontSize: 10, fontWeight: 800, color: sale.branch === "HQ" ? "#3B82F6" : sale.branch === "Lekki" ? "#16A34A" : "#D97706"
                  }}>{sale.branch === "HQ" ? "HQ" : sale.branch.slice(0, 2).toUpperCase()}</div>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                      <span style={{ fontSize: 13, fontWeight: 600, color: S.navy }}>{sale.clerk}</span>
                      <span style={{ fontSize: 11, color: S.grayLight }}>sold {sale.items} item{sale.items > 1 ? "s" : ""}</span>
                      {sale.status === "refunded" && <span style={{ fontSize: 9, fontWeight: 700, padding: "1px 6px", borderRadius: 4, background: S.redBg, color: S.red }}>REFUND</span>}
                    </div>
                    <div style={{ fontSize: 11, color: S.grayLight, marginTop: 1 }}>{sale.date.split(", ")[1]} • {sale.method}{sale.tag ? ` • ${sale.tag}` : ""}</div>
                  </div>
                  <div style={{ fontSize: 14, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono', monospace" }}>₦{sale.total.toLocaleString()}</div>
                </div>
              ))}
            </div>

            {/* Right Column */}
            <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
              {/* Revenue by Branch */}
              <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: 20 }}>
                <h3 style={{ fontSize: 14, fontWeight: 700, color: S.navy, margin: "0 0 14px" }}>Revenue by Branch</h3>
                {revenueByBranch.map(b => (
                  <div key={b.branch} style={{ marginBottom: 12 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                      <span style={{ fontSize: 13, fontWeight: 600, color: S.navy }}>{b.branch}</span>
                      <span style={{ fontSize: 13, fontWeight: 700, color: S.navy, fontFamily: "'Space Mono', monospace" }}>₦{(b.revenue / 1000).toFixed(0)}K</span>
                    </div>
                    <div style={{ height: 8, background: "#f1f5f9", borderRadius: 4, overflow: "hidden" }}>
                      <div style={{ height: "100%", width: `${b.pct}%`, background: `linear-gradient(90deg, ${S.gold}, ${S.goldLight})`, borderRadius: 4, transition: "width 0.5s" }} />
                    </div>
                    <div style={{ fontSize: 10, color: S.grayLight, marginTop: 2 }}>{b.pct}% of today</div>
                  </div>
                ))}
              </div>

              {/* Top Performers */}
              <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: 20 }}>
                <h3 style={{ fontSize: 14, fontWeight: 700, color: S.navy, margin: "0 0 14px" }}>Top Clerks Today</h3>
                {staff.filter(s => s.sales > 0).sort((a, b) => b.revenue - a.revenue).slice(0, 4).map((s, i) => (
                  <div key={s.id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "8px 0", borderBottom: i < 3 ? "1px solid #f8fafc" : "none" }}>
                    <div style={{
                      width: 26, height: 26, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
                      background: i === 0 ? S.goldPale : "#f1f5f9", fontSize: 11, fontWeight: 800,
                      color: i === 0 ? S.gold : S.grayLight
                    }}>{i + 1}</div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: S.navy }}>{s.name}</div>
                      <div style={{ fontSize: 11, color: S.grayLight }}>{s.branch} • {s.sales} sales</div>
                    </div>
                    <div style={{ fontSize: 13, fontWeight: 700, color: S.navy, fontFamily: "'Space Mono', monospace" }}>₦{(s.revenue / 1000).toFixed(0)}K</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ═══ SALES HISTORY TAB ═══ */}
      {posTab === "sales" && (
        <div>
          {/* Filters */}
          <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
            {["All Branches", "HQ", "Lekki", "Ikeja"].map(b => (
              <button key={b} style={{
                padding: "7px 16px", borderRadius: 8, border: "1.5px solid #e2e8f0", background: b === "All Branches" ? S.navy : "#fff",
                color: b === "All Branches" ? "#fff" : S.gray, fontSize: 12, fontWeight: 600, cursor: "pointer", fontFamily: "inherit"
              }}>{b}</button>
            ))}
            <div style={{ flex: 1 }} />
            <button style={{
              padding: "7px 16px", borderRadius: 8, border: "1.5px solid #e2e8f0", background: "#fff",
              color: S.gray, fontSize: 12, fontWeight: 600, cursor: "pointer", fontFamily: "inherit"
            }}>📅 Date Range</button>
            <button style={{
              padding: "7px 16px", borderRadius: 8, border: "1.5px solid #e2e8f0", background: "#fff",
              color: S.gray, fontSize: 12, fontWeight: 600, cursor: "pointer", fontFamily: "inherit"
            }}>⬇ Export CSV</button>
          </div>

          {/* Sales table */}
          <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", overflow: "hidden" }}>
            <div style={{
              display: "grid", gridTemplateColumns: "90px 70px 100px 60px 100px 70px 60px 80px 1fr", gap: 8,
              padding: "12px 20px", background: "#f8fafc", fontSize: 11, fontWeight: 700, color: S.grayLight, textTransform: "uppercase"
            }}>
              <span>Sale ID</span><span>Branch</span><span>Clerk</span><span>Items</span><span>Amount</span><span>Method</span><span>Tag</span><span>Status</span><span>Date</span>
            </div>
            {salesHistory.map(sale => (
              <div key={sale.id} style={{
                display: "grid", gridTemplateColumns: "90px 70px 100px 60px 100px 70px 60px 80px 1fr", gap: 8,
                padding: "12px 20px", borderTop: "1px solid #f1f5f9", alignItems: "center"
              }}>
                <span style={{ fontSize: 12, fontWeight: 700, color: S.navy, fontFamily: "'Space Mono', monospace" }}>{sale.id}</span>
                <span style={{
                  fontSize: 10, fontWeight: 700, padding: "3px 8px", borderRadius: 6, textAlign: "center",
                  background: sale.branch === "HQ" ? "#EFF6FF" : sale.branch === "Lekki" ? "#F0FDF4" : "#FEF3C7",
                  color: sale.branch === "HQ" ? "#3B82F6" : sale.branch === "Lekki" ? "#16A34A" : "#D97706",
                }}>{sale.branch}</span>
                <span style={{ fontSize: 12, color: S.navy, fontWeight: 500 }}>{sale.clerk}</span>
                <span style={{ fontSize: 12, color: S.gray, textAlign: "center" }}>{sale.items}</span>
                <span style={{ fontSize: 13, fontWeight: 700, color: S.navy, fontFamily: "'Space Mono', monospace" }}>₦{sale.total.toLocaleString()}</span>
                <span style={{ fontSize: 11, color: S.gray }}>{sale.method}</span>
                <span style={{ fontSize: 11, color: sale.tag ? S.navy : S.grayLight, fontWeight: sale.tag ? 600 : 400 }}>{sale.tag || "—"}</span>
                <span style={{
                  fontSize: 10, fontWeight: 700, padding: "2px 8px", borderRadius: 6, textAlign: "center",
                  background: sale.status === "completed" ? S.greenBg : S.redBg,
                  color: sale.status === "completed" ? S.green : S.red,
                }}>{sale.status === "completed" ? "Paid" : "Refund"}</span>
                <span style={{ fontSize: 11, color: S.grayLight }}>{sale.date}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ═══ STAFF & CLERKS TAB ═══ */}
      {posTab === "staff" && (
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: S.navy }}>{staff.length} Staff Members</div>
              <div style={{ fontSize: 12, color: S.grayLight }}>{staff.filter(s => s.status === "active").length} active, {staff.filter(s => s.status === "inactive").length} inactive</div>
            </div>
            <button onClick={() => setShowAddStaff(true)} style={{
              padding: "10px 22px", borderRadius: 10, border: "none", cursor: "pointer", fontFamily: "inherit",
              background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy, fontWeight: 700, fontSize: 13,
              boxShadow: "0 4px 12px rgba(232,168,56,0.3)"
            }}>+ Add Staff</button>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {staff.map(s => (
              <div key={s.id} style={{
                background: "#fff", borderRadius: 12, border: "1px solid #e2e8f0", padding: "16px 20px",
                display: "flex", alignItems: "center", gap: 16, opacity: s.status === "inactive" ? 0.55 : 1
              }}>
                {/* Avatar */}
                <div style={{
                  width: 42, height: 42, borderRadius: "50%", background: s.role === "Manager" ? "#EFF6FF" : s.role === "Supervisor" ? "#FEF3C7" : S.goldPale,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 14, fontWeight: 800, color: s.role === "Manager" ? "#3B82F6" : s.role === "Supervisor" ? "#D97706" : S.gold
                }}>{s.name.split(" ").map(n => n[0]).join("")}</div>

                {/* Info */}
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ fontSize: 14, fontWeight: 700, color: S.navy }}>{s.name}</span>
                    <span style={{
                      fontSize: 10, fontWeight: 700, padding: "2px 8px", borderRadius: 6,
                      background: s.role === "Manager" ? "#EFF6FF" : s.role === "Supervisor" ? "#FEF3C7" : "#f1f5f9",
                      color: s.role === "Manager" ? "#3B82F6" : s.role === "Supervisor" ? "#D97706" : S.gray,
                    }}>{s.role}</span>
                    {s.lastLogin === "Online now" && (
                      <span style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 10, color: S.green, fontWeight: 600 }}>
                        <span style={{ width: 6, height: 6, borderRadius: "50%", background: S.green }} />Online
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 12, color: S.grayLight, marginTop: 2 }}>
                    {s.branch} Branch • PIN: {s.pin} • Last: {s.lastLogin}
                  </div>
                </div>

                {/* Today's stats */}
                <div style={{ textAlign: "right", minWidth: 100 }}>
                  {s.sales > 0 ? (
                    <>
                      <div style={{ fontSize: 14, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono', monospace" }}>₦{(s.revenue / 1000).toFixed(0)}K</div>
                      <div style={{ fontSize: 11, color: S.grayLight }}>{s.sales} sales today</div>
                    </>
                  ) : (
                    <div style={{ fontSize: 11, color: S.grayLight }}>No sales today</div>
                  )}
                </div>

                {/* Actions */}
                <div style={{ display: "flex", gap: 6 }}>
                  <button style={{ padding: "6px 12px", borderRadius: 8, border: "1px solid #e2e8f0", background: "#fff", cursor: "pointer", fontFamily: "inherit", fontSize: 11, fontWeight: 600, color: S.navy }}>Edit</button>
                  <button style={{ padding: "6px 12px", borderRadius: 8, border: "1px solid #e2e8f0", background: "#fff", cursor: "pointer", fontFamily: "inherit", fontSize: 11, fontWeight: 600, color: s.status === "active" ? S.red : S.green }}>
                    {s.status === "active" ? "Disable" : "Enable"}
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Permissions hint */}
          <div style={{
            marginTop: 16, background: S.goldPale, borderRadius: 12, padding: "14px 20px",
            display: "flex", alignItems: "center", gap: 12, border: `1px solid ${S.gold}20`
          }}>
            <span style={{ fontSize: 20 }}>🔐</span>
            <div>
              <div style={{ fontSize: 13, fontWeight: 700, color: S.navy }}>Role Permissions</div>
              <div style={{ fontSize: 12, color: S.gray }}>
                <b>Cashier</b> — sell & process payments. <b>Supervisor</b> — sell, void, refund, apply discounts. <b>Manager</b> — full access including reports & settings.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ═══ POS TERMINALS TAB ═══ */}
      {posTab === "terminals" && (
        <div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
            {posInstances.map(pos => (
              <div key={pos.id} style={{
                background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: 20,
                borderLeft: `4px solid ${pos.color}`, transition: "all 0.2s"
              }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 14 }}>
                  <h3 style={{ fontSize: 15, fontWeight: 700, color: S.navy, margin: 0 }}>{pos.name}</h3>
                  <span style={{
                    fontSize: 10, fontWeight: 700, padding: "3px 10px", borderRadius: 10,
                    background: pos.status === "online" ? S.greenBg : "#f1f5f9",
                    color: pos.status === "online" ? S.green : S.grayLight,
                    display: "flex", alignItems: "center", gap: 4
                  }}>
                    <span style={{ width: 6, height: 6, borderRadius: "50%", background: pos.status === "online" ? S.green : S.grayLight }} />
                    {pos.status.toUpperCase()}
                  </span>
                </div>

                <div style={{ fontSize: 12, color: S.gold, fontWeight: 600, fontFamily: "'Space Mono', monospace", marginBottom: 14 }}>
                  🔗 {pos.domain}
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8, marginBottom: 14 }}>
                  {[
                    { label: "Today's Sales", value: pos.todaySales },
                    { label: "Revenue", value: pos.todayRevenue > 0 ? `₦${(pos.todayRevenue / 1000).toFixed(0)}K` : "—" },
                    { label: "Active Clerks", value: pos.clerks },
                    { label: "Last Active", value: pos.lastActive },
                  ].map(s => (
                    <div key={s.label} style={{ padding: "8px 10px", background: "#f8fafc", borderRadius: 8 }}>
                      <div style={{ fontSize: 15, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono', monospace" }}>{s.value}</div>
                      <div style={{ fontSize: 10, color: S.grayLight }}>{s.label}</div>
                    </div>
                  ))}
                </div>

                <div style={{ display: "flex", gap: 8 }}>
                  <a href={`https://${pos.domain}`} target="_blank" rel="noreferrer" style={{
                    flex: 1, padding: "10px 0", borderRadius: 10, border: "none", cursor: "pointer", fontFamily: "inherit",
                    background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy, fontWeight: 700, fontSize: 12,
                    textAlign: "center", textDecoration: "none", display: "block"
                  }}>Open POS →</a>
                  <button style={{
                    padding: "10px 14px", borderRadius: 10, border: "1px solid #e2e8f0", background: "#fff",
                    cursor: "pointer", fontFamily: "inherit", fontSize: 12, fontWeight: 600, color: S.navy
                  }}>⚙️</button>
                </div>
              </div>
            ))}

            {/* Add new terminal */}
            <div onClick={() => setShowLaunch(true)} style={{
              background: "#fafbfc", borderRadius: 14, border: "2px dashed #e2e8f0", padding: 20, cursor: "pointer",
              display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", minHeight: 200,
            }}>
              <div style={{ fontSize: 36, marginBottom: 8, opacity: 0.4 }}>+</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: S.navy }}>Launch New Terminal</div>
              <div style={{ fontSize: 12, color: S.grayLight, marginTop: 4 }}>For a new branch or location</div>
            </div>
          </div>
        </div>
      )}

      {/* ═══ SETTINGS TAB ═══ */}
      {posTab === "settings" && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          {[
            {
              title: "Payment Methods", icon: "💳",
              items: [
                { label: "Cash", enabled: true }, { label: "Card (POS Terminal)", enabled: true },
                { label: "Bank Transfer", enabled: true }, { label: "Split Payment", enabled: true },
                { label: "Credit / IOU", enabled: false }, { label: "USSD", enabled: false },
              ]
            },
            {
              title: "Tax & Charges", icon: "🧮",
              fields: [
                { label: "VAT Rate", value: "0%", hint: "Set to 7.5% if VAT registered" },
                { label: "Service Charge", value: "₦0", hint: "Applied per transaction" },
              ]
            },
            {
              title: "Receipt Settings", icon: "🧾",
              items: [
                { label: "Print receipt automatically", enabled: true },
                { label: "Send receipt via SMS", enabled: false },
                { label: "Send receipt via WhatsApp", enabled: true },
                { label: "Include business logo", enabled: true },
              ]
            },
            {
              title: "Inventory Alerts", icon: "📦",
              items: [
                { label: "Low stock warning (< 5 units)", enabled: true },
                { label: "Out of stock notification", enabled: true },
                { label: "Daily stock summary", enabled: false },
              ]
            },
          ].map(section => (
            <div key={section.title} style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: 20 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
                <span style={{ fontSize: 20 }}>{section.icon}</span>
                <h3 style={{ fontSize: 15, fontWeight: 700, color: S.navy, margin: 0 }}>{section.title}</h3>
              </div>
              {section.items && section.items.map(item => (
                <div key={item.label} style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                  padding: "10px 0", borderBottom: "1px solid #f8fafc"
                }}>
                  <span style={{ fontSize: 13, color: S.navy }}>{item.label}</span>
                  <div onClick={() => {}} style={{
                    width: 40, height: 22, borderRadius: 11, cursor: "pointer",
                    background: item.enabled ? S.green : "#e2e8f0",
                    position: "relative", transition: "background 0.2s"
                  }}>
                    <div style={{
                      width: 18, height: 18, borderRadius: "50%", background: "#fff",
                      position: "absolute", top: 2, left: item.enabled ? 20 : 2,
                      transition: "left 0.2s", boxShadow: "0 1px 3px rgba(0,0,0,0.2)"
                    }} />
                  </div>
                </div>
              ))}
              {section.fields && section.fields.map(f => (
                <div key={f.label} style={{ marginBottom: 12 }}>
                  <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: S.gray, marginBottom: 4 }}>{f.label}</label>
                  <input defaultValue={f.value} style={{
                    width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 8, padding: "0 12px",
                    height: 38, fontSize: 14, fontFamily: "'Space Mono', monospace"
                  }} />
                  <div style={{ fontSize: 11, color: S.grayLight, marginTop: 3 }}>{f.hint}</div>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {/* ═══ ADD STAFF MODAL ═══ */}
      {showAddStaff && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}
          onClick={() => setShowAddStaff(false)}>
          <div onClick={e => e.stopPropagation()} style={{
            background: "#fff", borderRadius: 20, padding: 32, width: 440,
            boxShadow: "0 24px 48px rgba(0,0,0,0.15)"
          }}>
            <h2 style={{ fontSize: 20, fontWeight: 800, color: S.navy, margin: "0 0 4px" }}>Add New Staff</h2>
            <p style={{ fontSize: 13, color: S.grayLight, margin: "0 0 20px" }}>They'll login to the POS with their PIN</p>

            {[
              { label: "Full Name", placeholder: "e.g. Blessing Okonkwo" },
              { label: "Phone Number", placeholder: "e.g. 08034567890" },
              { label: "4-Digit PIN", placeholder: "e.g. 1234", type: "password" },
            ].map(f => (
              <div key={f.label} style={{ marginBottom: 14 }}>
                <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: S.gray, marginBottom: 5 }}>{f.label}</label>
                <input placeholder={f.placeholder} type={f.type || "text"} style={{
                  width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 12px",
                  height: 42, fontSize: 13, fontFamily: f.type === "password" ? "'Space Mono', monospace" : "inherit"
                }} />
              </div>
            ))}

            <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: S.gray, marginBottom: 5 }}>Role</label>
            <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
              {["Cashier", "Supervisor", "Manager"].map(r => (
                <button key={r} style={{
                  flex: 1, padding: "10px 0", borderRadius: 10, border: r === "Cashier" ? `2px solid ${S.gold}` : "1.5px solid #e2e8f0",
                  background: r === "Cashier" ? S.goldPale : "#fff", cursor: "pointer", fontFamily: "inherit",
                  fontSize: 13, fontWeight: 600, color: S.navy
                }}>{r}</button>
              ))}
            </div>

            <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: S.gray, marginBottom: 5 }}>Assign to Branch</label>
            <select style={{
              width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 12px",
              height: 42, fontSize: 13, fontFamily: "inherit", background: "#fff", marginBottom: 18
            }}>
              <option>Seeds & Pennies HQ</option>
              <option>Seeds & Pennies Lekki</option>
              <option>Liberty Assured Ikeja</option>
            </select>

            <button onClick={() => setShowAddStaff(false)} style={{
              width: "100%", padding: "14px 0", borderRadius: 12, border: "none", cursor: "pointer", fontFamily: "inherit",
              background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy, fontWeight: 700, fontSize: 15,
              boxShadow: "0 4px 12px rgba(232,168,56,0.3)"
            }}>Create Staff Account</button>
          </div>
        </div>
      )}

      {/* ═══ LAUNCH POS MODAL ═══ */}
      {showLaunch && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}
          onClick={() => setShowLaunch(false)}>
          <div onClick={e => e.stopPropagation()} style={{
            background: "#fff", borderRadius: 20, padding: 32, width: 440,
            boxShadow: "0 24px 48px rgba(0,0,0,0.15)"
          }}>
            <h2 style={{ fontSize: 20, fontWeight: 800, color: S.navy, margin: "0 0 4px" }}>Launch New POS Terminal</h2>
            <p style={{ fontSize: 13, color: S.grayLight, margin: "0 0 20px" }}>Create a WebPOS for a branch. Clerks access it via browser.</p>

            {[
              { label: "Terminal / Branch Name", placeholder: "e.g. Liberty Assured Victoria Island" },
            ].map(f => (
              <div key={f.label} style={{ marginBottom: 14 }}>
                <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: S.gray, marginBottom: 5 }}>{f.label}</label>
                <input placeholder={f.placeholder} style={{
                  width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 12px", height: 42, fontSize: 13, fontFamily: "inherit"
                }} />
              </div>
            ))}

            <div style={{ marginBottom: 14 }}>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: S.gray, marginBottom: 5 }}>POS URL</label>
              <div style={{ display: "flex", border: "1.5px solid #e2e8f0", borderRadius: 10, overflow: "hidden" }}>
                <input placeholder="liberty-vi" style={{ flex: 1, border: "none", padding: "0 12px", height: 40, fontSize: 13, fontFamily: "inherit" }} />
                <span style={{ padding: "0 12px", background: "#f8fafc", borderLeft: "1px solid #e2e8f0", display: "flex", alignItems: "center", fontSize: 12, color: S.grayLight, fontFamily: "'Space Mono', monospace" }}>.paybox360.com</span>
              </div>
            </div>

            <div style={{ marginBottom: 18 }}>
              <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: S.gray, marginBottom: 5 }}>Branch Address</label>
              <input placeholder="e.g. 15 Akin Adesola St, Victoria Island" style={{
                width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 12px", height: 42, fontSize: 13, fontFamily: "inherit"
              }} />
            </div>

            <div style={{
              background: "#F0FDF4", borderRadius: 10, padding: "12px 16px", marginBottom: 18,
              display: "flex", alignItems: "center", gap: 10
            }}>
              <span style={{ fontSize: 20 }}>💡</span>
              <div style={{ fontSize: 12, color: "#16A34A", lineHeight: 1.5 }}>
                Your clerks will access <b>liberty-vi.paybox360.com</b> from any browser or tablet. They login with their name + PIN.
              </div>
            </div>

            <button onClick={() => setShowLaunch(false)} style={{
              width: "100%", padding: "14px 0", borderRadius: 12, border: "none", cursor: "pointer", fontFamily: "inherit",
              background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy, fontWeight: 700, fontSize: 15,
              boxShadow: "0 4px 12px rgba(232,168,56,0.3)"
            }}>🚀 Launch POS Terminal</button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── BUSINESS LOANS SCREEN (Coming Soon) ────────────────────────
function BusinessLoansScreen() {
  const [selectedProduct, setSelectedProduct] = useState(null);

  const products = [
    {
      id: "loc",
      title: "Merchant Line of Credit",
      icon: "💳",
      tagline: "Revolving credit that grows with your business",
      color: "#3B82F6",
      colorBg: "#EFF6FF",
      limit: "Up to ₦10M",
      rate: "From 2.5%/mo",
      tenure: "Revolving",
      features: [
        "Pre-approved credit limit based on your AX transaction history",
        "Draw funds anytime — only pay interest on what you use",
        "Auto-repay from daily sales or wallet balance",
        "Credit limit increases as your delivery volume grows",
        "No collateral required for limits under ₦2M",
        "Instant disbursement to your AX wallet or bank account",
      ],
      howItWorks: [
        { step: "1", title: "Get Pre-Qualified", desc: "We analyse your AX delivery history, wallet activity, and payment patterns" },
        { step: "2", title: "Accept Your Limit", desc: "View your approved credit limit and terms — no paperwork" },
        { step: "3", title: "Draw Funds Instantly", desc: "Pull funds into your wallet or bank account whenever you need" },
        { step: "4", title: "Repay Flexibly", desc: "Auto-debit from sales, manual payment, or scheduled repayments" },
      ],
      idealFor: "Merchants who need flexible, on-demand access to capital for inventory purchases, marketing spend, or managing cash flow gaps between orders."
    },
    {
      id: "wc",
      title: "Working Capital Loan",
      icon: "🏦",
      tagline: "Lump sum funding to stock up and scale up",
      color: "#10B981",
      colorBg: "#F0FDF4",
      limit: "₦500K – ₦25M",
      rate: "From 3%/mo",
      tenure: "3 – 12 months",
      features: [
        "Fixed lump sum disbursed upfront to your bank account",
        "Predictable fixed monthly or weekly repayments",
        "Use for bulk inventory, equipment, or branch expansion",
        "Approval based on AX merchant activity + business profile",
        "Early repayment discounts available",
        "Top-up eligible after 50% repayment",
      ],
      howItWorks: [
        { step: "1", title: "Apply in 2 Minutes", desc: "Tell us how much you need and what it's for — right from this portal" },
        { step: "2", title: "Quick Assessment", desc: "We review your AX history, WebPOS sales, and business documents" },
        { step: "3", title: "Get Funded", desc: "Approved loans disbursed within 24–48 hours to your bank account" },
        { step: "4", title: "Repay & Grow", desc: "Fixed repayment schedule with auto-debit option from your AX wallet" },
      ],
      idealFor: "Merchants planning a big purchase — bulk stock, new equipment, seasonal inventory, or opening a new branch location."
    },
    {
      id: "od",
      title: "Wallet Overdraft",
      icon: "⚡",
      tagline: "Never miss a delivery because your wallet is low",
      color: "#E8A838",
      colorBg: "#FEF3C7",
      limit: "Up to ₦1M",
      rate: "From 0.1%/day",
      tenure: "7 – 30 days",
      features: [
        "Spend beyond your wallet balance — no order interruptions",
        "Auto-activates when your wallet hits zero during an order",
        "Tiny daily interest only on the overdrawn amount",
        "Auto-repays when you next fund your wallet",
        "Overdraft limit tied to your average daily delivery volume",
        "No application needed — pre-approved for active merchants",
      ],
      howItWorks: [
        { step: "1", title: "Stay Active", desc: "Maintain consistent delivery activity on AX for automatic eligibility" },
        { step: "2", title: "Overdraft Activates", desc: "When your wallet can't cover an order, overdraft kicks in seamlessly" },
        { step: "3", title: "Keep Delivering", desc: "Your orders go through without interruption — riders get dispatched" },
        { step: "4", title: "Auto-Repay", desc: "Next wallet funding automatically clears your overdraft balance first" },
      ],
      idealFor: "High-volume merchants who can't afford delivery downtime. Perfect for e-commerce sellers, food businesses, and logistics-heavy operations."
    },
  ];

  const selected = products.find(p => p.id === selectedProduct);

  return (
    <div style={{ animation: "fadeIn 0.3s ease" }}>
      {/* Hero */}
      <div style={{
        background: `linear-gradient(135deg, ${S.navy} 0%, #0f1b33 100%)`, borderRadius: 16, padding: "32px 36px",
        marginBottom: 24, position: "relative", overflow: "hidden"
      }}>
        <div style={{ position: "absolute", top: -30, right: -10, width: 140, height: 140, borderRadius: "50%", background: "rgba(232,168,56,0.06)" }} />
        <div style={{ position: "absolute", bottom: -40, right: 120, width: 100, height: 100, borderRadius: "50%", background: "rgba(139,92,246,0.06)" }} />
        <div style={{ position: "relative", zIndex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
            <span style={{ background: "#8B5CF6", color: "#fff", fontSize: 10, fontWeight: 700, padding: "4px 12px", borderRadius: 10 }}>COMING SOON</span>
            <span style={{ background: "rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.5)", fontSize: 10, fontWeight: 700, padding: "4px 12px", borderRadius: 10 }}>POWERED BY LIBERTY ASSURED</span>
          </div>
          <h2 style={{ color: "#fff", fontSize: 24, fontWeight: 800, margin: "0 0 8px" }}>Business Loans for AX Merchants</h2>
          <p style={{ color: "rgba(255,255,255,0.5)", fontSize: 14, margin: 0, maxWidth: 560, lineHeight: 1.6 }}>
            Access credit tailored to your delivery business. Your AX activity builds your credit profile — the more you ship, the more you can borrow.
          </p>
        </div>
      </div>

      {/* Product cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginBottom: 24 }}>
        {products.map(p => (
          <div key={p.id} onClick={() => setSelectedProduct(selectedProduct === p.id ? null : p.id)} style={{
            background: "#fff", borderRadius: 16, border: selectedProduct === p.id ? `2px solid ${p.color}` : "1px solid #e2e8f0",
            padding: 24, cursor: "pointer", transition: "all 0.25s",
            boxShadow: selectedProduct === p.id ? `0 8px 24px ${p.color}20` : "none",
            transform: selectedProduct === p.id ? "translateY(-2px)" : "none"
          }}>
            <div style={{
              width: 52, height: 52, borderRadius: 14, background: p.colorBg,
              display: "flex", alignItems: "center", justifyContent: "center", fontSize: 26, marginBottom: 16
            }}>{p.icon}</div>

            <h3 style={{ fontSize: 17, fontWeight: 800, color: S.navy, margin: "0 0 6px" }}>{p.title}</h3>
            <p style={{ fontSize: 13, color: S.grayLight, margin: "0 0 18px", lineHeight: 1.5 }}>{p.tagline}</p>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginBottom: 18 }}>
              {[
                { label: "Limit", value: p.limit },
                { label: "Rate", value: p.rate },
                { label: "Tenure", value: p.tenure },
              ].map(s => (
                <div key={s.label} style={{ padding: "10px 8px", background: "#f8fafc", borderRadius: 10, textAlign: "center" }}>
                  <div style={{ fontSize: 12, fontWeight: 800, color: S.navy }}>{s.value}</div>
                  <div style={{ fontSize: 10, color: S.grayLight, marginTop: 2 }}>{s.label}</div>
                </div>
              ))}
            </div>

            <button style={{
              width: "100%", padding: "12px 0", borderRadius: 10, border: "none", cursor: "pointer", fontFamily: "inherit",
              background: selectedProduct === p.id ? p.color : "#f1f5f9",
              color: selectedProduct === p.id ? "#fff" : S.gray,
              fontWeight: 700, fontSize: 13, transition: "all 0.2s"
            }}>
              {selectedProduct === p.id ? "Hide Details ↑" : "Learn More ↓"}
            </button>
          </div>
        ))}
      </div>

      {/* Expanded detail */}
      {selected && (
        <div style={{ animation: "fadeIn 0.3s ease", marginBottom: 24 }}>
          <div style={{ background: "#fff", borderRadius: 16, border: "1px solid #e2e8f0", padding: 28, borderTop: `4px solid ${selected.color}` }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
              <div style={{
                width: 42, height: 42, borderRadius: 12, background: selected.colorBg,
                display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22
              }}>{selected.icon}</div>
              <div>
                <h3 style={{ fontSize: 18, fontWeight: 800, color: S.navy, margin: 0 }}>{selected.title}</h3>
                <p style={{ fontSize: 13, color: S.grayLight, margin: 0 }}>{selected.tagline}</p>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
              {/* Features */}
              <div>
                <h4 style={{ fontSize: 14, fontWeight: 700, color: S.navy, margin: "0 0 12px" }}>What You Get</h4>
                {selected.features.map((f, i) => (
                  <div key={i} style={{ display: "flex", gap: 10, padding: "8px 0" }}>
                    <div style={{
                      width: 20, height: 20, borderRadius: "50%", background: selected.colorBg, flexShrink: 0, marginTop: 1,
                      display: "flex", alignItems: "center", justifyContent: "center"
                    }}>
                      <span style={{ color: selected.color, fontSize: 11, fontWeight: 800 }}>✓</span>
                    </div>
                    <span style={{ fontSize: 13, color: S.gray, lineHeight: 1.5 }}>{f}</span>
                  </div>
                ))}
              </div>

              {/* How it works */}
              <div>
                <h4 style={{ fontSize: 14, fontWeight: 700, color: S.navy, margin: "0 0 12px" }}>How It Works</h4>
                {selected.howItWorks.map((hw, i) => (
                  <div key={i} style={{ display: "flex", gap: 12, padding: "10px 0", position: "relative" }}>
                    {i < selected.howItWorks.length - 1 && (
                      <div style={{ position: "absolute", left: 15, top: 36, bottom: -2, width: 2, background: "#f1f5f9" }} />
                    )}
                    <div style={{
                      width: 32, height: 32, borderRadius: "50%", background: selected.color, flexShrink: 0,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontSize: 13, fontWeight: 800, color: "#fff", position: "relative", zIndex: 1
                    }}>{hw.step}</div>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 700, color: S.navy }}>{hw.title}</div>
                      <div style={{ fontSize: 12, color: S.grayLight, marginTop: 2, lineHeight: 1.5 }}>{hw.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Ideal for */}
            <div style={{
              marginTop: 20, padding: "16px 20px", background: selected.colorBg, borderRadius: 12,
              display: "flex", alignItems: "flex-start", gap: 12
            }}>
              <span style={{ fontSize: 18, marginTop: 1 }}>🎯</span>
              <div>
                <div style={{ fontSize: 12, fontWeight: 700, color: selected.color, marginBottom: 4 }}>IDEAL FOR</div>
                <div style={{ fontSize: 13, color: S.navy, lineHeight: 1.6 }}>{selected.idealFor}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Waitlist CTA */}
      <div style={{
        background: `linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%)`, borderRadius: 16, padding: "28px 32px",
        display: "flex", alignItems: "center", justifyContent: "space-between"
      }}>
        <div>
          <h3 style={{ color: "#fff", fontSize: 18, fontWeight: 800, margin: "0 0 6px" }}>Get Early Access</h3>
          <p style={{ color: "rgba(255,255,255,0.6)", fontSize: 13, margin: 0 }}>
            Join the waitlist. Active AX merchants will be first to get approved.
          </p>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <input placeholder="Enter your email" style={{
            border: "2px solid rgba(255,255,255,0.2)", borderRadius: 10, padding: "0 16px", height: 44,
            fontSize: 13, fontFamily: "inherit", background: "rgba(255,255,255,0.1)", color: "#fff", width: 240
          }} />
          <button style={{
            padding: "0 28px", height: 44, borderRadius: 10, border: "none", cursor: "pointer", fontFamily: "inherit",
            background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy, fontWeight: 700, fontSize: 14,
            boxShadow: "0 4px 12px rgba(232,168,56,0.3)"
          }}>Join Waitlist</button>
        </div>
      </div>

      {/* AX Credit Score teaser */}
      <div style={{
        marginTop: 16, background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: "20px 24px",
        display: "flex", alignItems: "center", gap: 20
      }}>
        <div style={{
          width: 80, height: 80, borderRadius: "50%", position: "relative",
          background: `conic-gradient(${S.green} 0% 72%, #f1f5f9 72% 100%)`
        }}>
          <div style={{
            position: "absolute", inset: 8, borderRadius: "50%", background: "#fff",
            display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column"
          }}>
            <div style={{ fontSize: 20, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono', monospace", lineHeight: 1 }}>720</div>
            <div style={{ fontSize: 8, color: S.grayLight, fontWeight: 600 }}>AX SCORE</div>
          </div>
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ fontSize: 15, fontWeight: 700, color: S.navy, marginBottom: 4 }}>Your AX Credit Score is Building</div>
          <div style={{ fontSize: 13, color: S.gray, lineHeight: 1.5 }}>
            Every delivery, every wallet transaction, every on-time payment builds your merchant credit profile.
            When Business Loans launches, your score determines your limit and rate.
          </div>
        </div>
        <div style={{ textAlign: "right", flexShrink: 0 }}>
          <div style={{ fontSize: 11, color: S.green, fontWeight: 700 }}>EXCELLENT</div>
          <div style={{ fontSize: 11, color: S.grayLight, marginTop: 2 }}>Top 15% of merchants</div>
        </div>
      </div>
    </div>
  );
}

// ─── ACCOUNTING SCREEN (Coming Soon) ────────────────────────────
function AccountingScreen() {
  const [selectedModule, setSelectedModule] = useState(null);

  const modules = [
    {
      id: "invoicing",
      title: "Invoicing & Billing",
      icon: "🧾",
      tagline: "Create, send, and track professional invoices",
      color: "#3B82F6",
      colorBg: "#EFF6FF",
      features: [
        "Generate branded invoices with your logo and business details",
        "Auto-create invoices from WebPOS sales or website orders",
        "Send invoices via WhatsApp, SMS, or email in one click",
        "Track paid, pending, and overdue invoices in real-time",
        "Set up recurring invoices for regular clients",
        "Accept partial payments and deposits on invoices",
      ],
      preview: [
        { label: "INV-0024", customer: "Dangote Industries", amount: "₦2.4M", status: "Paid", color: "#10B981" },
        { label: "INV-0023", customer: "GTBank Procurement", amount: "₦890K", status: "Pending", color: "#F59E0B" },
        { label: "INV-0022", customer: "Flour Mills Plc", amount: "₦1.1M", status: "Overdue", color: "#EF4444" },
      ]
    },
    {
      id: "expenses",
      title: "Expense Tracking",
      icon: "📊",
      tagline: "Capture every naira going out of your business",
      color: "#EF4444",
      colorBg: "#FEF2F2",
      features: [
        "Log expenses by category — fuel, inventory, salaries, rent, marketing",
        "Snap receipts with your phone camera for instant logging",
        "Auto-import delivery costs from your AX order history",
        "Set budget limits per category with overspend alerts",
        "Track vendor payments and outstanding balances",
        "Monthly expense breakdown with visual charts",
      ],
      preview: [
        { label: "Inventory", amount: "₦1.8M", pct: 45 },
        { label: "Delivery (AX)", amount: "₦420K", pct: 11 },
        { label: "Salaries", amount: "₦650K", pct: 16 },
        { label: "Rent & Utilities", amount: "₦380K", pct: 10 },
        { label: "Marketing", amount: "₦280K", pct: 7 },
        { label: "Other", amount: "₦470K", pct: 11 },
      ]
    },
    {
      id: "pnl",
      title: "Profit & Loss",
      icon: "📈",
      tagline: "Know your real numbers — revenue, costs, and profit",
      color: "#10B981",
      colorBg: "#F0FDF4",
      features: [
        "Auto-generated P&L from your sales, expenses, and delivery costs",
        "Daily, weekly, monthly, and annual profit views",
        "Revenue breakdown by channel — WebPOS, Website, Walk-in",
        "Cost of goods sold (COGS) tracking tied to inventory",
        "Gross margin and net margin calculations",
        "Compare periods — this month vs last month, YoY trends",
      ],
      preview: [
        { label: "Revenue", value: "₦4.2M", delta: "+18%", positive: true },
        { label: "COGS", value: "₦2.1M", delta: "+12%", positive: false },
        { label: "Gross Profit", value: "₦2.1M", delta: "+24%", positive: true },
        { label: "Expenses", value: "₦1.3M", delta: "+8%", positive: false },
        { label: "Net Profit", value: "₦800K", delta: "+41%", positive: true },
      ]
    },
    {
      id: "tax",
      title: "Tax & Compliance",
      icon: "🏛️",
      tagline: "Stay compliant with automated tax calculations",
      color: "#8B5CF6",
      colorBg: "#F5F3FF",
      features: [
        "Auto-calculate VAT (7.5%) on eligible transactions",
        "Withholding tax tracking for corporate clients",
        "Generate tax-ready reports for FIRS filing",
        "TIN verification and management",
        "Quarterly and annual tax summaries",
        "Export data in formats accepted by Nigerian tax authorities",
      ],
      preview: [
        { label: "VAT Collected", amount: "₦315K" },
        { label: "VAT Paid (Input)", amount: "₦135K" },
        { label: "Net VAT Payable", amount: "₦180K" },
        { label: "WHT Deducted", amount: "₦42K" },
      ]
    },
    {
      id: "reports",
      title: "Financial Reports",
      icon: "📑",
      tagline: "Bank-ready reports generated automatically",
      color: "#F59E0B",
      colorBg: "#FEF3C7",
      features: [
        "Balance sheet, income statement, and cash flow statement",
        "Aged receivables and payables reports",
        "Bank reconciliation with connected accounts",
        "Custom report builder — filter by date, branch, category",
        "Export as PDF or Excel for bank loan applications",
        "Share reports with your accountant via secure link",
      ],
      preview: [
        { label: "Balance Sheet", icon: "📋" },
        { label: "Income Statement", icon: "📊" },
        { label: "Cash Flow", icon: "💧" },
        { label: "Aged Receivables", icon: "⏰" },
      ]
    },
    {
      id: "payroll",
      title: "Payroll & Staff Pay",
      icon: "👥",
      tagline: "Pay your team on time, every time",
      color: "#06B6D4",
      colorBg: "#ECFEFF",
      features: [
        "Set up monthly or bi-weekly salary schedules",
        "Auto-calculate deductions — tax, pension, NHF, loans",
        "Bulk pay all staff in one click via bank transfer",
        "Track commissions for sales clerks from WebPOS data",
        "Generate payslips and send via WhatsApp",
        "Leave tracking and overtime calculations",
      ],
      preview: [
        { label: "Monthly Payroll", amount: "₦2.8M", staff: 12 },
        { label: "Next Run", amount: "Feb 28", staff: null },
      ]
    },
  ];

  const selected = modules.find(m => m.id === selectedModule);

  return (
    <div style={{ animation: "fadeIn 0.3s ease" }}>
      {/* Hero */}
      <div style={{
        background: `linear-gradient(135deg, ${S.navy} 0%, #0f1b33 100%)`, borderRadius: 16, padding: "32px 36px",
        marginBottom: 24, position: "relative", overflow: "hidden"
      }}>
        <div style={{ position: "absolute", top: -30, right: -10, width: 140, height: 140, borderRadius: "50%", background: "rgba(232,168,56,0.06)" }} />
        <div style={{ position: "relative", zIndex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
            <span style={{ background: "#8B5CF6", color: "#fff", fontSize: 10, fontWeight: 700, padding: "4px 12px", borderRadius: 10 }}>COMING SOON</span>
            <span style={{ background: "rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.5)", fontSize: 10, fontWeight: 700, padding: "4px 12px", borderRadius: 10 }}>ALL-IN-ONE BUSINESS SUITE</span>
          </div>
          <h2 style={{ color: "#fff", fontSize: 24, fontWeight: 800, margin: "0 0 8px" }}>Accounting & Financial Management</h2>
          <p style={{ color: "rgba(255,255,255,0.5)", fontSize: 14, margin: 0, maxWidth: 580, lineHeight: 1.6 }}>
            Your books, automated. Every sale from WebPOS, every order from your website, every delivery via AX — captured, categorised, and reconciled automatically.
          </p>
        </div>
      </div>

      {/* Module grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 14, marginBottom: 24 }}>
        {modules.map(m => (
          <div key={m.id} onClick={() => setSelectedModule(selectedModule === m.id ? null : m.id)} style={{
            background: "#fff", borderRadius: 14, border: selectedModule === m.id ? `2px solid ${m.color}` : "1px solid #e2e8f0",
            padding: 20, cursor: "pointer", transition: "all 0.25s",
            boxShadow: selectedModule === m.id ? `0 6px 20px ${m.color}15` : "none",
            transform: selectedModule === m.id ? "translateY(-2px)" : "none"
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
              <div style={{
                width: 44, height: 44, borderRadius: 12, background: m.colorBg,
                display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22
              }}>{m.icon}</div>
              <div>
                <h3 style={{ fontSize: 14, fontWeight: 800, color: S.navy, margin: 0 }}>{m.title}</h3>
                <p style={{ fontSize: 11, color: S.grayLight, margin: "2px 0 0" }}>{m.tagline}</p>
              </div>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
              {m.features.slice(0, 3).map((f, i) => (
                <span key={i} style={{
                  fontSize: 10, padding: "3px 8px", borderRadius: 6, background: "#f8fafc", color: S.gray
                }}>{f.split(" ").slice(0, 4).join(" ")}...</span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Expanded detail */}
      {selected && (
        <div style={{ animation: "fadeIn 0.3s ease", marginBottom: 24 }}>
          <div style={{ background: "#fff", borderRadius: 16, border: "1px solid #e2e8f0", padding: 28, borderTop: `4px solid ${selected.color}` }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
              <div style={{
                width: 42, height: 42, borderRadius: 12, background: selected.colorBg,
                display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22
              }}>{selected.icon}</div>
              <div>
                <h3 style={{ fontSize: 18, fontWeight: 800, color: S.navy, margin: 0 }}>{selected.title}</h3>
                <p style={{ fontSize: 13, color: S.grayLight, margin: 0 }}>{selected.tagline}</p>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
              {/* Features */}
              <div>
                <h4 style={{ fontSize: 14, fontWeight: 700, color: S.navy, margin: "0 0 12px" }}>Features</h4>
                {selected.features.map((f, i) => (
                  <div key={i} style={{ display: "flex", gap: 10, padding: "7px 0" }}>
                    <div style={{
                      width: 20, height: 20, borderRadius: "50%", background: selected.colorBg, flexShrink: 0, marginTop: 1,
                      display: "flex", alignItems: "center", justifyContent: "center"
                    }}>
                      <span style={{ color: selected.color, fontSize: 11, fontWeight: 800 }}>✓</span>
                    </div>
                    <span style={{ fontSize: 13, color: S.gray, lineHeight: 1.5 }}>{f}</span>
                  </div>
                ))}
              </div>

              {/* Preview */}
              <div>
                <h4 style={{ fontSize: 14, fontWeight: 700, color: S.navy, margin: "0 0 12px" }}>Preview</h4>
                <div style={{ background: "#f8fafc", borderRadius: 12, padding: 16 }}>
                  {/* Invoicing preview */}
                  {selected.id === "invoicing" && selected.preview.map((inv, i) => (
                    <div key={i} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 0", borderBottom: i < 2 ? "1px solid #e2e8f0" : "none" }}>
                      <div>
                        <span style={{ fontSize: 12, fontWeight: 700, color: S.navy, fontFamily: "'Space Mono', monospace" }}>{inv.label}</span>
                        <span style={{ fontSize: 12, color: S.grayLight, marginLeft: 8 }}>{inv.customer}</span>
                      </div>
                      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <span style={{ fontSize: 13, fontWeight: 700, color: S.navy, fontFamily: "'Space Mono', monospace" }}>{inv.amount}</span>
                        <span style={{ fontSize: 10, fontWeight: 700, padding: "2px 8px", borderRadius: 6, background: `${inv.color}15`, color: inv.color }}>{inv.status}</span>
                      </div>
                    </div>
                  ))}

                  {/* Expenses preview */}
                  {selected.id === "expenses" && selected.preview.map((exp, i) => (
                    <div key={i} style={{ marginBottom: 10 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 3 }}>
                        <span style={{ fontSize: 12, fontWeight: 600, color: S.navy }}>{exp.label}</span>
                        <span style={{ fontSize: 12, fontWeight: 700, color: S.navy, fontFamily: "'Space Mono', monospace" }}>{exp.amount}</span>
                      </div>
                      <div style={{ height: 6, background: "#e2e8f0", borderRadius: 3, overflow: "hidden" }}>
                        <div style={{ height: "100%", width: `${exp.pct}%`, background: selected.color, borderRadius: 3 }} />
                      </div>
                    </div>
                  ))}

                  {/* P&L preview */}
                  {selected.id === "pnl" && selected.preview.map((row, i) => (
                    <div key={i} style={{
                      display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 0",
                      borderBottom: i < selected.preview.length - 1 ? "1px solid #e2e8f0" : "none",
                      fontWeight: row.label === "Net Profit" || row.label === "Gross Profit" ? 700 : 400
                    }}>
                      <span style={{ fontSize: 13, color: S.navy }}>{row.label}</span>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <span style={{ fontSize: 14, fontWeight: 700, color: S.navy, fontFamily: "'Space Mono', monospace" }}>{row.value}</span>
                        <span style={{ fontSize: 10, fontWeight: 700, color: row.positive ? S.green : S.red }}>{row.delta}</span>
                      </div>
                    </div>
                  ))}

                  {/* Tax preview */}
                  {selected.id === "tax" && selected.preview.map((t, i) => (
                    <div key={i} style={{
                      display: "flex", justifyContent: "space-between", padding: "10px 0",
                      borderBottom: i < selected.preview.length - 1 ? "1px solid #e2e8f0" : "none"
                    }}>
                      <span style={{ fontSize: 13, color: S.navy }}>{t.label}</span>
                      <span style={{ fontSize: 14, fontWeight: 700, color: S.navy, fontFamily: "'Space Mono', monospace" }}>{t.amount}</span>
                    </div>
                  ))}

                  {/* Reports preview */}
                  {selected.id === "reports" && (
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                      {selected.preview.map((r, i) => (
                        <div key={i} style={{ padding: "14px 12px", background: "#fff", borderRadius: 10, border: "1px solid #e2e8f0", textAlign: "center" }}>
                          <div style={{ fontSize: 22, marginBottom: 4 }}>{r.icon}</div>
                          <div style={{ fontSize: 12, fontWeight: 600, color: S.navy }}>{r.label}</div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Payroll preview */}
                  {selected.id === "payroll" && selected.preview.map((p, i) => (
                    <div key={i} style={{
                      display: "flex", justifyContent: "space-between", alignItems: "center", padding: "12px 0",
                      borderBottom: i < selected.preview.length - 1 ? "1px solid #e2e8f0" : "none"
                    }}>
                      <span style={{ fontSize: 13, fontWeight: 600, color: S.navy }}>{p.label}</span>
                      <div style={{ textAlign: "right" }}>
                        <div style={{ fontSize: 16, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono', monospace" }}>{p.amount}</div>
                        {p.staff && <div style={{ fontSize: 10, color: S.grayLight }}>{p.staff} staff members</div>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Integration callout */}
      <div style={{
        background: `linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%)`, borderRadius: 16, padding: "28px 32px",
        display: "flex", alignItems: "center", justifyContent: "space-between"
      }}>
        <div>
          <h3 style={{ color: "#fff", fontSize: 18, fontWeight: 800, margin: "0 0 6px" }}>Everything Connected. Zero Manual Entry.</h3>
          <p style={{ color: "rgba(255,255,255,0.6)", fontSize: 13, margin: 0, maxWidth: 440, lineHeight: 1.5 }}>
            Your AX deliveries, WebPOS sales, website orders, and wallet transactions all flow into one ledger automatically.
          </p>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <input placeholder="Enter your email" style={{
            border: "2px solid rgba(255,255,255,0.2)", borderRadius: 10, padding: "0 16px", height: 44,
            fontSize: 13, fontFamily: "inherit", background: "rgba(255,255,255,0.1)", color: "#fff", width: 240
          }} />
          <button style={{
            padding: "0 28px", height: 44, borderRadius: 10, border: "none", cursor: "pointer", fontFamily: "inherit",
            background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy, fontWeight: 700, fontSize: 14,
            boxShadow: "0 4px 12px rgba(232,168,56,0.3)"
          }}>Join Waitlist</button>
        </div>
      </div>

      {/* Auto-sync teaser */}
      <div style={{
        marginTop: 16, background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: "20px 24px",
        display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12
      }}>
        {[
          { label: "AX Deliveries", icon: "🚀", desc: "Delivery costs auto-logged", color: S.gold },
          { label: "WebPOS Sales", icon: "💻", desc: "Every sale auto-recorded", color: "#3B82F6" },
          { label: "Website Orders", icon: "🌐", desc: "Online revenue tracked", color: "#10B981" },
          { label: "Wallet Flows", icon: "💰", desc: "Funding & debits reconciled", color: "#8B5CF6" },
        ].map(s => (
          <div key={s.label} style={{
            padding: "16px 14px", borderRadius: 12, border: "1px solid #f1f5f9",
            textAlign: "center"
          }}>
            <div style={{ fontSize: 28, marginBottom: 6 }}>{s.icon}</div>
            <div style={{ fontSize: 13, fontWeight: 700, color: S.navy, marginBottom: 2 }}>{s.label}</div>
            <div style={{ fontSize: 11, color: S.grayLight }}>{s.desc}</div>
            <div style={{ width: 24, height: 3, borderRadius: 2, background: s.color, margin: "8px auto 0" }} />
          </div>
        ))}
      </div>
    </div>
  );
}
