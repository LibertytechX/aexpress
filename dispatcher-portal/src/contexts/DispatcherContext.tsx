/* eslint-disable react-refresh/only-export-components */
'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import type { Order, LogEvent, User, Rider, Merchant } from '@/types';
import { AuthService } from '@/services/authService';
import { RidersAPI, OrdersAPI, MerchantsAPI, ActivityFeedAPI, DispatchersAPI, VehicleAssetsAPI } from '@/lib/api';
import { playNewOrderChime, playStartedChime, playDeliveredChime } from '@/components/common/sounds';
import { Realtime } from 'ably';

interface DispatcherContextType {
    user: User | null;
    authState: "loading" | "login" | "signup" | "authenticated";
    setUser: React.Dispatch<React.SetStateAction<User | null>>;
    setAuthState: React.Dispatch<React.SetStateAction<"loading" | "login" | "signup" | "authenticated">>;
    orders: Order[];
    riders: Rider[];
    merchants: Merchant[];
    dispatchers: any[];
    vehicleAssets: any[];
    activityFeed: any[];
    selectedOrderId: string | null;
    setSelectedOrderId: (id: string | null) => void;
    selectedRiderId: string | null;
    setSelectedRiderId: (id: string | null) => void;
    selectedMerchantId: string | null;
    setSelectedMerchantId: (id: string | null) => void;
    eventLogs: Record<string, LogEvent[]>;
    addLog: (oid: string, text: string, type?: string) => void;
    handleUpdateOrder: (oid: string, field: string, val: any) => void;
    setOrders: React.Dispatch<React.SetStateAction<Order[]>>;
    setRiders: React.Dispatch<React.SetStateAction<Rider[]>>;
    handleStatusChange: (oid: string, status: any) => void;
    handleAssign: (oid: string, rid: string) => Promise<void>;
    handleLoginSuccess: (userData: User) => void;
    handleLogout: () => void;
}

const DispatcherContext = createContext<DispatcherContextType | undefined>(undefined);

export function DispatcherProvider({ children }: { children: React.ReactNode }) {
    const [user, setUser] = useState<User | null>(null);
    const [authState, setAuthState] = useState<"loading" | "login" | "signup" | "authenticated">("loading");

    const [orders, setOrders] = useState<Order[]>([]);
    const [riders, setRiders] = useState<Rider[]>([]);
    const [merchants, setMerchants] = useState<Merchant[]>([]);
    const [dispatchers, setDispatchers] = useState<any[]>([]);
    const [vehicleAssets, setVehicleAssets] = useState<any[]>([]);
    const [activityFeed, setActivityFeed] = useState<any[]>([]);

    const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);
    const [selectedRiderId, setSelectedRiderId] = useState<string | null>(null);
    const [selectedMerchantId, setSelectedMerchantId] = useState<string | null>(null);
    const [eventLogs, setEventLogs] = useState<Record<string, LogEvent[]>>({});

    useEffect(() => {
        if (AuthService.isAuthenticated()) {
            setUser({ id: "cached", name: "Dispatcher", phone: "" });
            setAuthState("authenticated");
        } else {
            setAuthState("login");
        }
    }, []);

    // Initial data fetch
    useEffect(() => {
        if (authState === "authenticated") {
            const fetchData = async () => {
                try {
                    const [ridersData, ordersData, merchantsData, feedData, dispatchersData, vehicleAssetsData] = await Promise.all([
                        RidersAPI.getAll().catch(() => []),
                        OrdersAPI.getAll().catch(() => []),
                        MerchantsAPI.getAll().catch(() => []),
                        ActivityFeedAPI.getRecent(50).catch(() => []),
                        DispatchersAPI.getAll().catch(() => []),
                        VehicleAssetsAPI.getAll().catch(() => []),
                    ]);
                    setRiders(ridersData || []);
                    setOrders(ordersData || []);
                    setMerchants(merchantsData || []);
                    setActivityFeed(feedData || []);
                    setDispatchers(dispatchersData || []);
                    setVehicleAssets(vehicleAssetsData || []);
                } catch (error) {
                    console.error("Failed to load data", error);
                }
            };
            fetchData();
        }
    }, [authState]);

    // Setup Ably Realtime
    useEffect(() => {
        if (authState !== "authenticated") return;

        let cancelled = false;
        let localAbly: any = null;
        let pollInterval: ReturnType<typeof setInterval> | null = null;

        const setupRealtime = async () => {
            // Load recent feed from REST API first
            try {
                const feedData = await ActivityFeedAPI.getRecent(50);
                if (!cancelled && feedData.length > 0) setActivityFeed(feedData);
            } catch (_) { /* ignore */ }

            let ablyActive = false;
            try {
                if (cancelled) return;
                console.log('[Ably] Initializing Realtime client with token auth...');
                const ably = new Realtime({
                    authCallback: async (_: any, callback: (err: any, token: any) => void) => {
                        console.log('[Ably] authCallback — fetching token from backend...');
                        try {
                            const raw = await ActivityFeedAPI.getAblyToken();
                            console.log('[Ably] Raw token response:', JSON.stringify(raw));

                            // Normalize — backends wrap token in different shapes.
                            // Ably accepts: plain string, TokenDetails { token, expires, ... },
                            // or TokenRequest { keyName, timestamp, nonce, mac, ... }
                            let tokenData: any = raw;

                            if (typeof raw === 'string') {
                                // Already a plain token string
                                tokenData = raw;
                            } else if (raw && typeof raw === 'object') {
                                // Unwrap common backend envelope shapes
                                if (raw.token_request) tokenData = raw.token_request;
                                else if (raw.tokenRequest) tokenData = raw.tokenRequest;
                                else if (raw.token && typeof raw.token === 'object') tokenData = raw.token;
                                else if (raw.token && typeof raw.token === 'string') tokenData = raw.token;
                                // else: use raw directly (already a TokenDetails or TokenRequest)
                            }

                            console.log('[Ably] Passing to callback:', JSON.stringify(tokenData));
                            callback(null, tokenData);
                        } catch (e) {
                            console.error('[Ably] authCallback error:', e);
                            callback(e, null);
                        }
                    }
                });
                localAbly = ably;

                // Log connection state changes
                ably.connection.on('connecting', () => console.log('[Ably] Connecting...'));
                ably.connection.on('connected', () => console.log('[Ably] Connected ✅'));
                ably.connection.on('disconnected', (s: any) => console.warn('[Ably] Disconnected:', s?.reason?.message));
                ably.connection.on('failed', (s: any) => {
                    console.error('[Ably] FAILED:', s?.reason?.message);
                    // Fall back to polling if Ably connection fails
                    if (!pollInterval) {
                        console.log('[Ably] Falling back to 10s polling.');
                        pollInterval = setInterval(async () => {
                            try {
                                const feedData = await ActivityFeedAPI.getRecent(50);
                                if (feedData.length > 0) setActivityFeed(feedData);
                            } catch (_) { /* ignore */ }
                        }, 10000);
                    }
                });

                // 1) Activity Feed channel
                const activityChannel = ably.channels.get('dispatch-feed');
                await activityChannel.subscribe('activity', (msg: any) => {
                    const data = msg.data;
                    setActivityFeed(prev => {
                        if (!data) return prev;
                        if (data.id && prev.some((x: any) => x.id === data.id)) return prev;
                        return [data, ...prev].slice(0, 100);
                    });

                    if (data && data.order_id) {
                        const statusEventMap: Record<string, string> = {
                            cancelled: 'Cancelled', delivered: 'Delivered',
                            in_transit: 'In Transit', assigned: 'Assigned',
                            unassigned: 'Pending', failed: 'Failed',
                        };
                        const newStatus = statusEventMap[data.event_type];
                        if (newStatus) {
                            handleUpdateOrder(data.order_id, 'status', newStatus);
                        }
                        if (data.event_type === 'new_order') {
                            playNewOrderChime();
                            // Auto-refetch orders so new orders appear instantly
                            OrdersAPI.getAll().then(fresh => {
                                if (!cancelled && fresh) setOrders(prev => mergeOrders(fresh, prev));
                            }).catch(() => { });
                        } else if (data.event_type === 'in_transit') {
                            playStartedChime();
                        } else if (data.event_type === 'delivered') {
                            playDeliveredChime();
                        }
                    }
                });
                console.log('[Ably] Subscribed to dispatch-feed ✅');

                // 2) Vehicle Telemetry channel
                const telemetryChannel = ably.channels.get('vehicle-telemetry');
                await telemetryChannel.subscribe('telemetry_update', (msg: any) => {
                    const incoming = msg.data;
                    if (!Array.isArray(incoming) || incoming.length === 0) return;
                    console.log(`[Ably] 🏍️ Received telemetry for ${incoming.length} vehicle(s)`);
                    setVehicleAssets(prev => {
                        const map: Record<string, any> = {};
                        prev.forEach(v => { map[v.id] = v; });
                        incoming.forEach((v: any) => { map[v.id] = v; });
                        return Object.values(map);
                    });
                });
                console.log('[Ably] Subscribed to vehicle-telemetry ✅');

                ablyActive = true;
            } catch (err) {
                console.error('[Ably] Setup failed, falling back to polling:', err);
            }

            // Polling fallback if Ably setup failed entirely
            if (!ablyActive && !pollInterval) {
                console.log('[Ably] Using 10s polling fallback from the start.');
                pollInterval = setInterval(async () => {
                    try {
                        const feedData = await ActivityFeedAPI.getRecent(50);
                        if (feedData.length > 0) setActivityFeed(feedData);
                    } catch (_) { /* ignore */ }
                }, 10000);
            }
        };

        // Merge relay legs from existing state when backend returns empty legs
        const mergeOrders = (fresh: Order[], prev: Order[]): Order[] =>
            fresh.map(o => {
                const existing = prev.find(e => e.id === o.id);
                if (existing && (!(o as any).relayLegs || (o as any).relayLegs.length === 0) && (existing as any).relayLegs?.length > 0) {
                    return { ...o, relayLegs: (existing as any).relayLegs };
                }
                return o;
            });

        setupRealtime();

        // 60s periodic order refresh so merchant-portal orders stay in sync
        const ordersInterval = setInterval(async () => {
            try {
                const data = await OrdersAPI.getAll().catch(() => null);
                if (data && !cancelled) setOrders(prev => mergeOrders(data, prev));
            } catch (_) { /* ignore */ }
        }, 60000);

        return () => {
            cancelled = true;
            if (localAbly) { localAbly.close(); localAbly = null; }
            if (pollInterval) clearInterval(pollInterval);
            clearInterval(ordersInterval);
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [authState]); // Intentionally runs once on auth

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
                await OrdersAPI.assignRider(oid, "");
                handleUpdateOrder(oid, "riderId", null);
                handleUpdateOrder(oid, "rider", null);
                handleStatusChange(oid, "Pending");
                addLog(oid, "Rider unassigned", "issue");
            } else {
                await OrdersAPI.assignRider(oid, rid);
                const r = riders.find((rx) => rx.id === rid);
                if (r) {
                    handleUpdateOrder(oid, "riderId", rid);
                    handleUpdateOrder(oid, "rider", r.name);
                    handleStatusChange(oid, "Assigned");
                    addLog(oid, `Assigned to ${r.name} (${r.vehicle})`);
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
        dispatchers,
        vehicleAssets,
        activityFeed,
        setOrders,
        setRiders,
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
