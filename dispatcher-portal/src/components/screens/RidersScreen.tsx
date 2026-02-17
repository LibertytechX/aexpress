import { useState, useEffect } from "react";
import type { Rider, Order } from "../../types";
import { S } from "../common/theme";
import { I } from "../icons";
import { StatCard } from "../common/StatCard";
import { Badge } from "../common/Badge";
import { RiderService } from "../../services/riderService";

interface RidersScreenProps {
    riders: Rider[];
    orders: Order[];
    selectedId: string | null;
    onSelect: (id: string) => void;
    onBack: () => void;
    onViewOrder: (id: string) => void;
}

export function RidersScreen({ riders: initialRiders, orders, selectedId, onSelect, onBack, onViewOrder }: RidersScreenProps) {
    const [riders, setRiders] = useState<Rider[]>(initialRiders);
    const [filter, setFilter] = useState("All");
    const [search, setSearch] = useState("");
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchRiders = async () => {
            setLoading(true);
            const data = await RiderService.getRiders();
            if (data.length > 0) {
                setRiders(data);
            }
            setLoading(false);
        };
        fetchRiders();
    }, []);

    if (selectedId) {
        const rider = riders.find(r => r.id === selectedId);
        if (!rider) return <div style={{ color: S.textMuted }}>Rider not found</div>;
        const rOrders = orders.filter(o => o.riderId === rider.id);
        return (
            <div>
                <button onClick={onBack} style={{ display: "flex", alignItems: "center", gap: 6, padding: 0, background: "none", border: "none", cursor: "pointer", color: S.textDim, fontSize: 13, fontWeight: 600, fontFamily: "inherit", marginBottom: 16 }}>{I.back} Back to Riders</button>
                <div style={{ display: "grid", gridTemplateColumns: "300px 1fr", gap: 16 }}>
                    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                        <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, padding: 20, textAlign: "center" }}>
                            <div style={{ width: 64, height: 64, borderRadius: 16, margin: "0 auto 10px", background: S.goldPale, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22, fontWeight: 800, color: S.gold }}>{rider.name ? rider.name.split(" ").map(n => n[0]).join("") : "?"}</div>
                            <div style={{ fontSize: 18, fontWeight: 800 }}>{rider.name}</div>
                            <div style={{ fontSize: 12, color: S.textDim, fontFamily: "'Space Mono',monospace", marginTop: 2 }}>{rider.phone}</div>
                            <span style={{ display: "inline-block", marginTop: 8, fontSize: 10, fontWeight: 700, padding: "3px 10px", borderRadius: 6, background: rider.status === "online" ? S.greenBg : rider.status === "on_delivery" ? S.purpleBg : S.redBg, color: rider.status === "online" ? S.green : rider.status === "on_delivery" ? S.purple : S.red }}>{rider.status === "online" ? "ONLINE" : rider.status === "on_delivery" ? "ON DELIVERY" : "OFFLINE"}</span>
                            {rider.currentOrder && <div style={{ fontSize: 11, color: S.purple, fontWeight: 700, fontFamily: "'Space Mono',monospace", marginTop: 6 }}>📦 {rider.currentOrder}</div>}
                            <div style={{ display: "flex", gap: 6, marginTop: 12 }}>
                                <a href={`tel:${rider.phone}`} style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 5, padding: "8px 0", borderRadius: 8, background: S.goldPale, color: S.gold, fontSize: 11, fontWeight: 600, textDecoration: "none" }}>{I.phone} Call</a>
                                <a href={`https://wa.me/234${rider.phone.slice(1)}`} target="_blank" rel="noreferrer" style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 5, padding: "8px 0", borderRadius: 8, background: S.greenBg, color: S.green, fontSize: 11, fontWeight: 600, textDecoration: "none" }}>💬 WhatsApp</a>
                            </div>
                            <div style={{ marginTop: 14, paddingTop: 14, borderTop: `1px solid ${S.border}`, textAlign: "left" }}>
                                {[{ l: "Vehicle", v: rider.vehicle }, { l: "ID", v: rider.id }, { l: "Joined", v: rider.joined }].map(f => (
                                    <div key={f.l} style={{ display: "flex", justifyContent: "space-between", padding: "6px 0" }}><span style={{ fontSize: 12, color: S.textMuted }}>{f.l}</span><span style={{ fontSize: 12, fontWeight: 600 }}>{f.v}</span></div>
                                ))}
                            </div>
                        </div>
                        <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, padding: 16 }}>
                            <div style={{ fontSize: 10, fontWeight: 700, color: S.textMuted, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 12 }}>Performance</div>
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                                {[{ l: "Total Deliveries", v: rider.totalDeliveries.toLocaleString(), c: S.text }, { l: "Completion", v: `${rider.completionRate}%`, c: rider.completionRate >= 95 ? S.green : S.yellow }, { l: "Avg Time", v: rider.avgTime, c: S.text }, { l: "Rating", v: `⭐ ${rider.rating}`, c: S.gold }, { l: "Today Orders", v: rider.todayOrders, c: S.gold }, { l: "Today Earnings", v: `₦${rider.todayEarnings.toLocaleString()}`, c: S.green }].map(s => (
                                    <div key={s.l} style={{ padding: 10, background: S.borderLight, borderRadius: 8, textAlign: "center" }}><div style={{ fontSize: 16, fontWeight: 800, color: s.c, fontFamily: "'Space Mono',monospace" }}>{s.v}</div><div style={{ fontSize: 9, color: S.textMuted, marginTop: 2 }}>{s.l}</div></div>
                                ))}
                            </div>
                        </div>
                    </div>
                    <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, overflow: "hidden" }}>
                        <div style={{ padding: "14px 18px", borderBottom: `1px solid ${S.border}` }}><span style={{ fontSize: 13, fontWeight: 700 }}>Order History ({rOrders.length})</span></div>
                        <div style={{ display: "grid", gridTemplateColumns: "100px 1fr 1fr 80px 70px 70px", padding: "8px 16px", fontSize: 10, fontWeight: 700, color: S.textMuted, textTransform: "uppercase", letterSpacing: "0.5px", borderBottom: `1px solid ${S.border}` }}>
                            <span>ID</span><span>Merchant</span><span>Route</span><span>Amount</span><span>COD</span><span>Status</span>
                        </div>
                        <div style={{ maxHeight: 400, overflowY: "auto" }}>
                            {rOrders.map(o => (
                                <div key={o.id} onClick={() => onViewOrder(o.id)} style={{ display: "grid", gridTemplateColumns: "100px 1fr 1fr 80px 70px 70px", padding: "10px 16px", borderBottom: `1px solid ${S.borderLight}`, cursor: "pointer", alignItems: "center", transition: "background 0.12s" }} onMouseEnter={e => e.currentTarget.style.background = S.borderLight} onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                                    <span style={{ fontSize: 11, fontWeight: 700, color: S.gold, fontFamily: "'Space Mono',monospace" }}>{o.id}</span>
                                    <span style={{ fontSize: 11, color: S.textDim }}>{o.merchant}</span>
                                    <span style={{ fontSize: 11, color: S.textMuted, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{o.pickup.split(",")[0]} → {o.dropoff.split(",")[0]}</span>
                                    <span style={{ fontSize: 11, fontWeight: 600, fontFamily: "'Space Mono',monospace" }}>₦{o.amount.toLocaleString()}</span>
                                    <span style={{ fontSize: 11, color: o.cod > 0 ? S.green : S.textMuted, fontFamily: "'Space Mono',monospace" }}>{o.cod > 0 ? `₦${(o.cod / 1000).toFixed(0)}K` : "—"}</span>
                                    <Badge status={o.status} />
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    const sMap: Record<string, string> = { "Online": "online", "On Delivery": "on_delivery", "Offline": "offline" };
    const filtered = riders.filter(r => { if (filter !== "All" && r.status !== sMap[filter]) return false; if (search) { const s = search.toLowerCase(); return r.name.toLowerCase().includes(s) || r.phone.includes(s); } return true; });
    const sc = (s: string) => s === "online" ? S.green : s === "on_delivery" ? S.purple : S.textMuted;

    return (
        <div>
            <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
                <StatCard label="Total Riders" value={riders.length} />
                <StatCard label="Online" value={riders.filter(r => r.status === "online").length} color={S.green} />
                <StatCard label="On Delivery" value={riders.filter(r => r.status === "on_delivery").length} color={S.purple} />
                <StatCard label="Deliveries Today" value={riders.reduce((s, r) => s + r.todayOrders, 0)} color={S.gold} />
            </div>
            <div style={{ display: "flex", gap: 10, marginBottom: 14 }}>
                <div style={{ display: "flex", gap: 4 }}>
                    {["All", "Online", "On Delivery", "Offline"].map(f => (<button key={f} onClick={() => setFilter(f)} style={{ padding: "7px 14px", borderRadius: 8, border: `1px solid ${filter === f ? "transparent" : S.border}`, cursor: "pointer", fontFamily: "inherit", fontSize: 12, fontWeight: 600, background: filter === f ? S.goldPale : S.card, color: filter === f ? S.gold : S.textMuted }}>{f}</button>))}
                </div>
                <div style={{ flex: 1, background: S.card, borderRadius: 10, border: `1px solid ${S.border}`, display: "flex", alignItems: "center", gap: 8, padding: "0 12px" }}>
                    <span style={{ opacity: 0.4 }}>{I.search}</span>
                    <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search riders..." style={{ flex: 1, background: "transparent", border: "none", color: S.text, fontSize: 12, fontFamily: "inherit", height: 38, outline: "none" }} />
                </div>
            </div>
            <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, overflow: "hidden" }}>
                <div style={{ display: "grid", gridTemplateColumns: "60px 1fr 100px 80px 90px 110px 100px 70px", padding: "10px 16px", background: S.borderLight, fontSize: 10, fontWeight: 700, color: S.textMuted, textTransform: "uppercase", letterSpacing: "0.5px", borderBottom: `1px solid ${S.border}` }}>
                    <span>ID</span><span>Rider</span><span>Phone</span><span>Vehicle</span><span>Status</span><span>Current Order</span><span>Today</span><span>Rating</span>
                </div>
                <div style={{ maxHeight: "calc(100vh - 310px)", overflowY: "auto" }}>
                    {loading ? (
                        <div style={{ padding: 20, textAlign: "center", color: S.textMuted }}>Loading riders...</div>
                    ) : (
                        filtered.map(r => (
                            <div key={r.id} onClick={() => onSelect(r.id)} style={{ display: "grid", gridTemplateColumns: "60px 1fr 100px 80px 90px 110px 100px 70px", padding: "12px 16px", borderBottom: `1px solid ${S.borderLight}`, cursor: "pointer", transition: "background 0.12s", alignItems: "center" }} onMouseEnter={e => e.currentTarget.style.background = S.borderLight} onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                                <span style={{ fontSize: 11, fontWeight: 700, color: S.textDim, fontFamily: "'Space Mono',monospace" }}>{r.id}</span>
                                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                                    <div style={{ width: 32, height: 32, borderRadius: 8, background: `${sc(r.status)}12`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 11, fontWeight: 800, color: sc(r.status) }}>{r.name ? r.name.split(" ").map(n => n[0]).join("") : "?"}</div>
                                    <span style={{ fontSize: 12, fontWeight: 600 }}>{r.name}</span>
                                </div>
                                <span style={{ fontSize: 11, color: S.textDim, fontFamily: "'Space Mono',monospace" }}>{r.phone}</span>
                                <span style={{ fontSize: 11, color: S.textDim }}>{r.vehicle}</span>
                                <span style={{ fontSize: 10, fontWeight: 700, padding: "3px 8px", borderRadius: 6, background: `${sc(r.status)}12`, color: sc(r.status) }}>{r.status === "online" ? "Online" : r.status === "on_delivery" ? "On Delivery" : "Offline"}</span>
                                <span style={{ fontSize: 11, color: r.currentOrder ? S.purple : S.textMuted, fontWeight: r.currentOrder ? 700 : 400, fontFamily: "'Space Mono',monospace" }}>{r.currentOrder || "— Available"}</span>
                                <div><span style={{ fontSize: 12, fontWeight: 700 }}>{r.todayOrders} orders</span><div style={{ fontSize: 10, color: S.textMuted }}>₦{r.todayEarnings.toLocaleString()}</div></div>
                                <span style={{ fontSize: 12, color: S.gold }}>⭐ {r.rating}</span>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}
