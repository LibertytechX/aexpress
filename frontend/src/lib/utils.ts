import Icons from '@/components/Icons';
import { S } from './theme';

export interface UIOrder {
  id: string; // Transformed from order_number
  order_number: string;
  status: string;
  pickup: string;
  dropoff: string;
  amount: number;
  date: string;
  vehicle: string;
  merchant: string;
  deliveries: any[];
  mode: string;
  payment_method: string;
}

export interface UITransaction {
  id: number;
  type: string;
  amount: number;
  description: string;
  date: string;
  ref: string;
  balance: number;
  status: string;
}

export const STATUS_COLORS: Record<string, { bg: string; text: string; label: string }> = {
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

export const formatDate = (isoString: string) => {
  if (!isoString) return '';
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

export const getVehicleIcon = (vehicle: string) => {
  const v = (vehicle || "").toLowerCase();
  if (v.includes("bike")) return Icons.bike;
  if (v.includes("car")) return Icons.car;
  if (v.includes("van") || v.includes("truck")) return Icons.van;
  return Icons.bike;
};

export const getModeBadge = (mode: string) => {
  if (mode === 'express') return { label: 'EXPRESS', bg: '#fee2e2', color: '#dc2626' };
  if (mode === 'pool') return { label: 'POOL', bg: '#dbeafe', color: '#2563eb' };
  return { label: 'STD', bg: '#f1f5f9', color: '#64748b' };
};

export const transformOrders = (apiOrders: any[]): UIOrder[] => {
  if (!Array.isArray(apiOrders)) return [];
  return apiOrders.map(order => ({
    id: order.order_number,
    order_number: order.order_number,
    status: order.status,
    pickup: order.pickup_address,
    dropoff: order.deliveries?.[0]?.dropoff_address || '',
    amount: parseFloat(order.total_amount),
    date: formatDate(order.created_at),
    vehicle: order.vehicle_name,
    merchant: order.user_business_name,
    deliveries: order.deliveries,
    mode: order.mode,
    payment_method: order.payment_method
  }));
};

export const transformTransactions = (apiTransactions: any[]): UITransaction[] => {
  if (!Array.isArray(apiTransactions)) return [];
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
