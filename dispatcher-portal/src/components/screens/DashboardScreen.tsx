import type { Order, Rider } from "../../types";
import { S } from "../common/theme";
import { StatCard } from "../common/StatCard";

interface DashboardScreenProps {
    orders: Order[];
    riders: Rider[];
    onViewOrder: (id: string) => void;
    onViewRider: (id: string) => void;
}

export function DashboardScreen({ orders, riders, onViewOrder, onViewRider }: DashboardScreenProps) {
    const today = orders.filter(o => o.created.includes("Feb 14"));
    const active = orders.filter(o => ["In Transit", "Picked Up", "Assigned"].includes(o.status));
    const delivered = today.filter(o => o.status === "Delivered");
    const revenue = today.reduce((s, o) => s + o.amount + o.codFee, 0);
    const codTotal = today.reduce((s, o) => s + o.cod, 0);

    // Mock events for dashboard
    const events = [
        { time: "4:05 PM", text: "AX-6158260 in transit — Musa heading to VI", color: S.gold, oid: "AX-6158260" },
        { time: "3:58 PM", text: "AX-6158260 picked up at Sabo Yaba", color: S.purple, oid: "AX-6158260" },
        { time: "3:44 PM", text: "AX-6158260 assigned to Musa Kabiru", color: S.blue, oid: "AX-6158260" },
        { time: "3:42 PM", text: "New order AX-6158260 from Vivid Print", color: S.gold, oid: "AX-6158260" },
        { time: "3:35 PM", text: "AX-6158261 picked up — Chinedu heading to VI", color: S.purple, oid: "AX-6158261" },
        { time: "3:28 PM", text: "New order AX-6158261 from Mama Nkechi", color: S.gold, oid: "AX-6158261" },
        { time: "3:15 PM", text: "AX-6158262 pending — no rider assigned", color: S.yellow, oid: "AX-6158262" },
        { time: "2:55 PM", text: "AX-6158263 in transit — Kola heading to Ikeja", color: S.gold, oid: "AX-6158263" },
        { time: "1:51 PM", text: "AX-6158257 delivered ✓ COD ₦36,000 settled", color: S.green, oid: "AX-6158257" },
        { time: "1:10 PM", text: "AX-6158256 delivered ✓ COD ₦125,000 settled", color: S.green, oid: "AX-6158256" },
    ];

    return (
        <div>
            <div style={{ display: "flex", gap: 12, marginBottom: 20 }}>
                <StatCard label="Today's Orders" value={today.length} sub={`${delivered.length} delivered`} />
                <StatCard label="Active Now" value={active.length} sub={`${orders.filter(o => o.status === "Pending").length} pending`} color={S.gold} />
                <StatCard label="Online Riders" value={riders.filter(r => r.status === "online").length} sub={`${riders.filter(r => r.status === "on_delivery").length} on delivery`} color={S.green} />
                <StatCard label="Revenue Today" value={`₦${(revenue / 1000).toFixed(0)}K`} sub={`₦${(codTotal / 1000).toFixed(0)}K COD collected`} color={S.gold} />
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 320px", gap: 16 }}>
                {/* Live feed */}
                <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, overflow: "hidden" }}>
                    <div style={{ padding: "14px 18px", borderBottom: `1px solid ${S.border}`, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}><div style={{ width: 8, height: 8, borderRadius: "50%", background: S.green, boxShadow: `0 0 8px ${S.green}` }} /><span style={{ fontSize: 13, fontWeight: 700 }}>Live Activity</span></div>
                        <span style={{ fontSize: 11, color: S.textMuted }}>{events.length} events</span>
                    </div>
                    <div style={{ maxHeight: 420, overflowY: "auto" }}>
                        {events.map((ev, i) => (
                            <div key={i} onClick={() => onViewOrder(ev.oid)} style={{ padding: "11px 18px", borderBottom: `1px solid ${S.borderLight}`, cursor: "pointer", display: "flex", alignItems: "flex-start", gap: 12, transition: "background 0.15s" }} onMouseEnter={e => e.currentTarget.style.background = S.borderLight} onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                                <div style={{ width: 8, height: 8, borderRadius: "50%", background: ev.color, marginTop: 5, flexShrink: 0 }} />
                                <div style={{ flex: 1, fontSize: 12, color: S.text, lineHeight: 1.4 }}>{ev.text}</div>
                                <span style={{ fontSize: 10, color: S.textMuted, fontFamily: "'Space Mono',monospace", flexShrink: 0 }}>{ev.time}</span>
                            </div>
                        ))}
                    </div>
                </div>
                {/* Right col */}
                <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                    <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}` }}>
                        <div style={{ padding: "12px 16px", borderBottom: `1px solid ${S.border}` }}><span style={{ fontSize: 13, fontWeight: 700, color: S.yellow }}>⏳ Pending Assignment</span></div>
                        {orders.filter(o => o.status === "Pending").map(o => (
                            <div key={o.id} onClick={() => onViewOrder(o.id)} style={{ padding: "10px 16px", borderBottom: `1px solid ${S.borderLight}`, cursor: "pointer", transition: "background 0.15s" }} onMouseEnter={e => e.currentTarget.style.background = S.borderLight} onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                                <div style={{ display: "flex", justifyContent: "space-between" }}><span style={{ fontSize: 12, fontWeight: 700, color: S.gold, fontFamily: "'Space Mono',monospace" }}>{o.id}</span><span style={{ fontSize: 11, color: S.textMuted }}>{o.vehicle}</span></div>
                                <div style={{ fontSize: 11, color: S.textDim, marginTop: 2 }}>{o.merchant} → {o.dropoff.split(",")[0]}</div>
                                {o.cod > 0 && <div style={{ fontSize: 10, color: S.green, marginTop: 2 }}>💵 COD ₦{o.cod.toLocaleString()}</div>}
                            </div>
                        ))}
                        {orders.filter(o => o.status === "Pending").length === 0 && <div style={{ padding: "20px 16px", textAlign: "center", fontSize: 12, color: S.textMuted }}>All orders assigned ✓</div>}
                    </div>
                    <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}` }}>
                        <div style={{ padding: "12px 16px", borderBottom: `1px solid ${S.border}` }}><span style={{ fontSize: 13, fontWeight: 700, color: S.green }}>🟢 Online Riders</span></div>
                        {riders.filter(r => r.status === "online" || r.status === "on_delivery").map(r => (
                            <div key={r.id} onClick={() => onViewRider(r.id)} style={{ padding: "10px 16px", borderBottom: `1px solid ${S.borderLight}`, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "space-between", transition: "background 0.15s" }} onMouseEnter={e => e.currentTarget.style.background = S.borderLight} onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                                    <div style={{ width: 8, height: 8, borderRadius: "50%", background: r.status === "on_delivery" ? S.purple : S.green }} />
                                    <div><div style={{ fontSize: 12, fontWeight: 600 }}>{r.name}</div><div style={{ fontSize: 10, color: S.textMuted }}>{r.vehicle} • {r.todayOrders} today</div></div>
                                </div>
                                {r.currentOrder ? <span style={{ fontSize: 10, fontWeight: 700, color: S.purple, fontFamily: "'Space Mono',monospace" }}>{r.currentOrder}</span> : <span style={{ fontSize: 10, fontWeight: 700, color: S.green }}>Available</span>}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
