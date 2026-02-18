export interface Order {
    id: string;
    customer: string;
    customerPhone: string;
    merchant: string;
    pickup: string;
    dropoff: string;
    rider: string | null;
    riderId: string | null;
    status: "Pending" | "Assigned" | "Picked Up" | "In Transit" | "Delivered" | "Cancelled" | "Failed";
    amount: number;
    cod: number;
    codFee: number;
    vehicle: "Bike" | "Car" | "Van";
    created: string;
    pkg: string;
}

export interface Rider {
    id: string;
    name: string;
    phone: string;
    vehicle: "Bike" | "Car" | "Van";
    status: "online" | "on_delivery" | "offline";
    currentOrder: string | null;
    todayOrders: number;
    todayEarnings: number;
    rating: number;
    totalDeliveries: number;
    completionRate: number;
    avgTime: string;
    joined: string;
}

export interface Merchant {
    id: string; // This will now be the 6-char external ID
    userId: string; // The UUID
    name: string;
    contact: string;
    phone: string;
    category: string;
    totalOrders: number;
    monthOrders: number;
    walletBalance: number;
    status: "Active" | "Inactive";
    joined: string;
}

export interface Customer {
    id: string;
    name: string;
    phone: string;
    email: string;
    totalOrders: number;
    lastOrder: string;
    totalSpent: number;
    favMerchant: string;
}

export interface Message {
    from: "dispatch" | "rider" | "customer";
    text: string;
    time: string;
}

export interface Chat {
    id: string;
    name: string;
    unread: number;
    lastMsg: string;
    lastTime: string;
    messages: Message[];
}

export interface LogEvent {
    time: string;
    event: string;
    by: string;
    type: string;
}

export interface User {
    id: string;
    name: string;
    phone: string;
    email?: string;
    token?: string;
}
