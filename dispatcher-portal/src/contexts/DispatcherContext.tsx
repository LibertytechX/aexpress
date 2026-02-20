/* eslint-disable react-refresh/only-export-components */
'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import type { Order, LogEvent, User, Rider, Merchant } from '@/types';
import { AuthService } from '@/services/authService';
import { OrderService } from '@/services/orderService';
import { RiderService } from '@/services/riderService';
import { MerchantService } from '@/services/merchantService';

interface DispatcherContextType {
    user: User | null;
    authState: "login" | "signup" | "authenticated";
    setUser: React.Dispatch<React.SetStateAction<User | null>>;
    setAuthState: React.Dispatch<React.SetStateAction<"login" | "signup" | "authenticated">>;
    orders: Order[];
    riders: Rider[];
    merchants: Merchant[];
    selectedOrderId: string | null;
    setSelectedOrderId: (id: string | null) => void;
    selectedRiderId: string | null;
    setSelectedRiderId: (id: string | null) => void;
    selectedMerchantId: string | null;
    setSelectedMerchantId: (id: string | null) => void;
    eventLogs: Record<string, LogEvent[]>;
    addLog: (oid: string, text: string, type?: string) => void;
    handleUpdateOrder: (oid: string, field: string, val: any) => void;
    handleStatusChange: (oid: string, status: any) => void;
    handleAssign: (oid: string, rid: string) => Promise<void>;
    handleLoginSuccess: (userData: User) => void;
    handleLogout: () => void;
}

const DispatcherContext = createContext<DispatcherContextType | undefined>(undefined);

export function DispatcherProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [authState, setAuthState] = useState<"login" | "signup" | "authenticated">("login");

    const [orders, setOrders] = useState<Order[]>([]);
    const [riders, setRiders] = useState<Rider[]>([]);
    const [merchants, setMerchants] = useState<Merchant[]>([]);

    const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);
    const [selectedRiderId, setSelectedRiderId] = useState<string | null>(null);
    const [selectedMerchantId, setSelectedMerchantId] = useState<string | null>(null);
    const [eventLogs, setEventLogs] = useState<Record<string, LogEvent[]>>({});

    useEffect(() => {
        if (AuthService.isAuthenticated()) {
            setUser({ id: "cached", name: "Dispatcher", phone: "" });
            setAuthState("authenticated");
        }
    }, []);

    useEffect(() => {
        if (authState === "authenticated") {
            const fetchData = async () => {
                try {
                    const [ridersData, ordersData, merchantsData] = await Promise.all([
                        RiderService.getRiders(),
                        OrderService.getOrders(),
                        MerchantService.getMerchants()
                    ]);
                    setRiders(ridersData || []);
                    setOrders(ordersData || []);
                    setMerchants(merchantsData || []);
                } catch (error) {
                    console.error("Failed to load data", error);
                }
            };
            fetchData();
        }
    }, [authState]);

    const handleLoginSuccess = (userData: User) => {
        setUser(userData);
        setAuthState("authenticated");
    };

    const handleLogout = () => {
        AuthService.logout();
        setUser(null);
        setAuthState("login");
    };

    const addLog = (oid: string, text: string, type: string = "status") => {
        const log: LogEvent = { time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }), event: text, by: "Dispatcher", type };
        setEventLogs((prev) => ({ ...prev, [oid]: [log, ...(prev[oid] || [])] }));
    };

    const handleUpdateOrder = (oid: string, field: string, val: any) => {
        setOrders((prev) => prev.map((o) => (o.id === oid ? { ...o, [field]: val } : o)));
    };

    const handleStatusChange = (oid: string, status: any) => {
        handleUpdateOrder(oid, "status", status);
        addLog(oid, `Status changed to ${status}`);
    };

    const handleAssign = async (oid: string, rid: string) => {
        try {
            if (!rid) {
                await OrderService.assignRider(oid, "");
                handleUpdateOrder(oid, "riderId", null);
                handleUpdateOrder(oid, "rider", null);
                handleStatusChange(oid, "Pending");
                addLog(oid, "Rider unassigned", "issue");
            } else {
                const success = await OrderService.assignRider(oid, rid);
                if (success) {
                    const r = riders.find((rx) => rx.id === rid);
                    if (r) {
                        handleUpdateOrder(oid, "riderId", rid);
                        handleUpdateOrder(oid, "rider", r.name);
                        handleStatusChange(oid, "Assigned");
                        addLog(oid, `Assigned to ${r.name} (${r.vehicle})`);
                    }
                } else {
                    alert("Failed to assign rider");
                }
            }
        } catch (e) {
            console.error("Assign Error", e);
            alert("Error assigning rider");
        }
    };

    const value = {
        user,
        setUser,
        authState,
        setAuthState,
        orders,
        riders,
        merchants,
        selectedOrderId,
        setSelectedOrderId,
        selectedRiderId,
        setSelectedRiderId,
        selectedMerchantId,
        setSelectedMerchantId,
        eventLogs,
        addLog,
        handleUpdateOrder,
        handleStatusChange,
        handleAssign,
        handleLoginSuccess,
        handleLogout,
    };

    return <DispatcherContext.Provider value={value}>{children}</DispatcherContext.Provider>;
}

export function useDispatcher() {
    const context = useContext(DispatcherContext);
    if (context === undefined) {
        throw new Error('useDispatcher must be used within a DispatcherProvider');
    }
    return context;
}
