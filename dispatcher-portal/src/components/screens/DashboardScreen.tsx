"use client";
import type { Order, Rider } from "../../types";
import { S } from "../common/theme";
import { I } from "@/components/icons";

interface DashboardScreenProps {
    orders: Order[];
    riders: Rider[];
    activityFeed?: any[];
    onViewOrder: (id: string) => void;
    onViewRider: (id: string) => void;
}

export function DashboardScreen({ orders, riders, activityFeed = [], onViewOrder, onViewRider }: DashboardScreenProps) {
    const todayStr = new Date().toISOString().slice(0, 10);
    const today = orders.filter(o => o.created && (o.created.startsWith(todayStr) || o.created.includes(todayStr)));
    const displayOrders = today.length > 0 ? today : orders;

    const active = orders.filter(o => ["In Transit", "At Dropoff", "Picked Up", "Assigned"].includes(o.status));
    const pendingOrders = orders.filter(o => o.status === "Pending");
    const delivered = displayOrders.filter(o => o.status === "Delivered");
    const revenue = displayOrders.reduce((s, o) => s + o.amount + o.codFee, 0);

    // Status color mapping for the activity feed
    const colorMap: Record<string, string> = { gold: S.gold, green: S.green, red: S.red, blue: S.blue, purple: S.purple, yellow: S.yellow };

    const truncate = (str: string, n: number) => str && str.length > n ? str.slice(0, n - 1) + "…" : (str || "");
    const events = (activityFeed || []).map(item => ({
        id: item.id,
        time: item.created_at ? new Date(item.created_at).toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" }) : "",
        text: item.text,
        color: colorMap[item.color] || S.gold,
        oid: item.order_id,
        event_type: item.event_type,
        pickup: truncate(item.metadata?.pickup || "", 30),
        dropoff: truncate(item.metadata?.dropoff || "", 30),
    }));

    const cards = [
        { label: "Today's Orders", value: displayOrders.length, sub: `${delivered.length} delivered`, bg: S.navy, color: "#fff", icon: I.orders, subColor: "rgba(255,255,255,0.6)", labelColor: "rgba(255,255,255,0.7)" },
        { label: "Active Deliveries", value: active.length, sub: `${pendingOrders.length} pending assignment`, bg: "#fff", color: S.navy, icon: I.dashboard, subColor: S.textMuted, labelColor: S.navy },
        { label: "Online Riders", value: riders.filter(r => r.status === "online").length, sub: `${riders.filter(r => r.status === "on_delivery").length} on delivery`, bg: "#fff", color: S.navy, icon: I.riders, subColor: S.textMuted, labelColor: S.navy },
        { label: "Revenue Today", value: `₦${(revenue / 1000).toFixed(0)}K`, sub: `Daily earnings`, bg: "#fff", color: S.navy, icon: I.check, subColor: S.textMuted, labelColor: S.navy },
    ];

    return (
        <div style={{ animation: "fadeIn 0.3s ease" }}>
            {/* Header */}
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
                <div>
                    <h1 style={{ fontSize: 24, fontWeight: 700, color: S.navy, marginBottom: 4 }}>Dispatcher Dashboard 👋</h1>
                    <p style={{ color: S.textMuted, fontSize: 15, margin: 0 }}>Live overview of fleet operations.</p>
                </div>
                <button style={{
                    padding: "10px 20px", borderRadius: 10, border: "none", cursor: "pointer",
                    background: `linear-gradient(135deg, ${S.gold}, #FDCB6E)`, color: S.navy,
                    fontWeight: 700, fontSize: 14, fontFamily: "inherit", display: "flex", alignItems: "center", gap: 8,
                    boxShadow: "0 4px 12px rgba(232,168,56,0.25)"
                }}>
                    {I.dashboard} Map View
                </button>
            </div>

            {/* Stat Cards */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 20, marginBottom: 28 }}>
                {cards.map((c, i) => (
                    <div key={i} className="group transition-all duration-300 hover:-translate-y-1" style={{
                        background: c.bg, borderRadius: 20, padding: "24px", border: i === 0 ? "none" : `1px solid ${S.border}`,
                        boxShadow: i === 0 ? "0 10px 30px rgba(47, 55, 88, 0.15)" : "0 4px 6px rgba(0,0,0,0.02)",
                        position: "relative", overflow: "hidden"
                    }}>
                        {i === 0 && (
                            <>
                                <div style={{ position: "absolute", top: -20, right: -20, width: 120, height: 120, borderRadius: "50%", background: "rgba(255,255,255,0.05)" }} />
                                <div style={{ position: "absolute", bottom: -40, left: -20, width: 100, height: 100, borderRadius: "50%", background: "rgba(255,255,255,0.03)" }} />
                            </>
                        )}
                        {i > 0 && (
                            <>
                                <div style={{ position: "absolute", bottom: -30, right: -30, width: 120, height: 120, borderRadius: "50%", border: "16px solid #FBB12F", opacity: 0.04 }} />
                                <div className="group-hover:scale-110 transition-transform duration-300" style={{ position: 'absolute', top: 10, right: 10, opacity: 0.05, transform: 'rotate(15deg) scale(2.5)', pointerEvents: 'none' }}>
                                    {c.icon}
                                </div>
                            </>
                        )}
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
                            <div style={{ width: 40, height: 40, borderRadius: 12, background: i === 0 ? "rgba(255,255,255,0.1)" : S.bg, display: "flex", alignItems: "center", justifyContent: "center", color: i === 0 ? S.gold : S.navy }}>
                                {c.icon}
                            </div>
                        </div>
                        <div style={{ fontSize: 13, fontWeight: 600, color: c.labelColor, marginBottom: 4 }}>{c.label}</div>
                        <div style={{ fontSize: 28, fontWeight: 700, color: c.color, fontFamily: "'Outfit', sans-serif", marginBottom: 4 }}>{c.value}</div>
                        <div style={{ fontSize: 12, color: c.subColor }}>{c.sub}</div>
                    </div>
                ))}
            </div>

            {/* Split Content: Live Activity feed & Pending */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 340px", gap: 20 }}>
                {/* Left col: Live Activity */}
                <div style={{ background: "#fff", borderRadius: 20, border: `1px solid ${S.border}`, boxShadow: "0 4px 6px rgba(0,0,0,0.02)", overflow: "hidden" }}>
                    <div style={{ padding: "16px 20px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: `1px solid ${S.borderLight}` }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                            <div style={{ width: 10, height: 10, borderRadius: "50%", background: S.green, boxShadow: `0 0 10px ${S.green}` }} />
                            <h3 style={{ fontSize: 15, fontWeight: 700, color: S.navy, margin: 0 }}>Live Fleet Activity</h3>
                        </div>
                        <span style={{ fontSize: 13, color: S.textMuted }}>{events.length} events logged</span>
                    </div>
                    {events.length === 0 ? (
                        <div style={{ padding: "40px", textAlign: "center", color: S.textMuted }}>No fleet activity yet today.</div>
                    ) : (
                        <div style={{ maxHeight: "calc(100vh - 400px)", overflowY: "auto", padding: "10px 0" }}>
                            {events.map((ev, i) => (
                                <div key={ev.id || i} onClick={() => onViewOrder(ev.oid)} className="hover:bg-slate-50" style={{
                                    padding: "14px 20px", display: "flex", alignItems: "flex-start", gap: 14, cursor: "pointer",
                                    borderBottom: i < events.length - 1 ? `1px solid ${S.borderLight}` : "none",
                                    transition: "background 0.15s"
                                }}>
                                    <div style={{ width: 10, height: 10, borderRadius: "50%", background: ev.color, marginTop: 6, flexShrink: 0 }} />
                                    <div style={{ flex: 1, minWidth: 0 }}>
                                        <div style={{ fontSize: 14, color: S.navy, fontWeight: 600, lineHeight: 1.4, marginBottom: 4 }}>{ev.text}</div>
                                        {ev.event_type === "new_order" && ev.pickup && ev.dropoff && (
                                            <div style={{ fontSize: 12, color: S.textMuted, display: "flex", alignItems: "center", gap: 6, overflow: "hidden" }}>
                                                <span style={{ flexShrink: 0 }}>📍</span>
                                                <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{ev.pickup}</span>
                                                <span style={{ flexShrink: 0, color: S.gold }}>→</span>
                                                <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{ev.dropoff}</span>
                                            </div>
                                        )}
                                    </div>
                                    <span style={{ fontSize: 11, color: S.textMuted, fontFamily: "'Space Mono',monospace", flexShrink: 0, paddingTop: 2 }}>{ev.time}</span>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {/* Right col: Pending & Online Riders */}
                <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
                    {/* Pending Orders */}
                    <div style={{ background: "#fff", borderRadius: 20, border: `1px solid ${S.border}`, boxShadow: "0 4px 6px rgba(0,0,0,0.02)", overflow: "hidden" }}>
                        <div style={{ padding: "16px 20px", borderBottom: `1px solid ${S.borderLight}` }}>
                            <h3 style={{ fontSize: 14, fontWeight: 700, color: S.yellow, margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
                                <span style={{ fontSize: 16 }}>⏳</span> Pending Assignment
                            </h3>
                        </div>
                        <div style={{ maxHeight: 250, overflowY: "auto" }}>
                            {pendingOrders.length === 0 ? (
                                <div style={{ padding: "24px", textAlign: "center", color: S.textMuted, fontSize: 13 }}>All clear! No pending orders.</div>
                            ) : (
                                pendingOrders.map((o) => (
                                    <div key={o.id} onClick={() => onViewOrder(o.id)} className="hover:bg-slate-50" style={{ padding: "12px 20px", borderBottom: `1px solid ${S.borderLight}`, cursor: "pointer", transition: "background 0.15s" }}>
                                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
                                            <span style={{ fontSize: 13, fontWeight: 700, color: S.navy, fontFamily: "'Space Mono',monospace" }}>{o.id}</span>
                                            <span style={{ fontSize: 11, color: S.textMuted }}>{o.vehicle}</span>
                                        </div>
                                        <div style={{ fontSize: 12, color: S.textDim, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                                            {o.merchant} → {o.dropoff.split(",")[0]}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>

                    {/* Online Riders */}
                    <div style={{ background: "#fff", borderRadius: 20, border: `1px solid ${S.border}`, boxShadow: "0 4px 6px rgba(0,0,0,0.02)", overflow: "hidden" }}>
                        <div style={{ padding: "16px 20px", borderBottom: `1px solid ${S.borderLight}` }}>
                            <h3 style={{ fontSize: 14, fontWeight: 700, color: S.green, margin: 0, display: "flex", alignItems: "center", gap: 8 }}>
                                <div style={{ width: 8, height: 8, borderRadius: "50%", background: S.green }} /> Active Fleet
                            </h3>
                        </div>
                        <div style={{ maxHeight: 250, overflowY: "auto" }}>
                            {riders.filter(r => r.status === "online" || r.status === "on_delivery").length === 0 ? (
                                <div style={{ padding: "24px", textAlign: "center", color: S.textMuted, fontSize: 13 }}>No riders online.</div>
                            ) : (
                                riders.filter(r => r.status === "online" || r.status === "on_delivery").map(r => (
                                    <div key={r.id} onClick={() => onViewRider(r.id)} className="hover:bg-slate-50" style={{ padding: "12px 20px", borderBottom: `1px solid ${S.borderLight}`, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "space-between", transition: "background 0.15s" }}>
                                        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                                            <div style={{ width: 36, height: 36, borderRadius: 10, background: r.status === "on_delivery" ? S.purpleBg : S.greenBg, color: r.status === "on_delivery" ? S.purple : S.green, display: "flex", alignItems: "center", justifyContent: "center" }}>
                                                {I.riders}
                                            </div>
                                            <div>
                                                <div style={{ fontSize: 13, fontWeight: 700, color: S.navy }}>{r.name}</div>
                                                <div style={{ fontSize: 11, color: S.textDim }}>{r.vehicle} • {r.todayOrders} trips today</div>
                                            </div>
                                        </div>
                                        {r.currentOrder ? (
                                            <span style={{ fontSize: 11, fontWeight: 700, color: S.purple, fontFamily: "'Space Mono',monospace", background: S.purpleBg, padding: "2px 8px", borderRadius: 6 }}>{r.currentOrder}</span>
                                        ) : (
                                            <span style={{ fontSize: 11, fontWeight: 700, color: S.green, background: S.greenBg, padding: "2px 8px", borderRadius: 6 }}>Ready</span>
                                        )}
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
