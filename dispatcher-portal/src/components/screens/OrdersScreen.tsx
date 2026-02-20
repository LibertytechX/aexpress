import { useState } from "react";
import type { Order, Rider, LogEvent } from "../../types";
import { S } from "../common/theme";
import { I } from "../icons";
import { OrderDetail } from "./OrderDetail";
import { Badge } from "../common/Badge";
import { StatCard } from "../common/StatCard";

interface OrdersScreenProps {
    orders: Order[];
    riders: Rider[];
    selectedId: string | null;
    onSelect: (id: string) => void;
    onBack: () => void;
    onViewRider: (id: string) => void;
    onAssign: (oid: string, rid: string) => void;
    onChangeStatus: (oid: string, s: any) => void;
    onUpdateOrder: (oid: string, field: string, val: any) => void;
    addLog: (oid: string, text: string, type?: string) => void;
    eventLogs: Record<string, LogEvent[]>;
}

export function OrdersScreen({ orders, riders, selectedId, onSelect, onBack, onViewRider, onAssign, onChangeStatus, onUpdateOrder, addLog, eventLogs }: OrdersScreenProps) {
    const [statusFilter, setStatusFilter] = useState("All");
    const [search, setSearch] = useState("");

    if (selectedId) {
        const order = orders.find(o => o.id === selectedId);
        if (!order) return <div style={{ color: S.textMuted }}>Order not found</div>;
        return <OrderDetail order={order} riders={riders} onBack={onBack} onViewRider={onViewRider} onAssign={onAssign} onChangeStatus={onChangeStatus} onUpdateOrder={onUpdateOrder} addLog={addLog} logs={eventLogs[order.id] || []} />
    }

    const filtered = orders.filter(o => {
        if (statusFilter !== "All" && o.status !== statusFilter) return false;
        if (search) {
            const s = search.toLowerCase();
            return o.id.toLowerCase().includes(s) || o.customer.toLowerCase().includes(s) || o.merchant.toLowerCase().includes(s);
        }
        return true;
    });

    return (
        <div>
            <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
                <StatCard label="Total Orders" value={orders.length} />
                <StatCard label="Pending" value={orders.filter(o => o.status === "Pending").length} color={S.yellow} />
                <StatCard label="In Transit" value={orders.filter(o => ["Picked Up", "In Transit"].includes(o.status)).length} color={S.gold} />
                <StatCard label="Completed" value={orders.filter(o => o.status === "Delivered").length} color={S.green} />
            </div>
            <div style={{ display: "flex", gap: 10, marginBottom: 14 }}>
                <div style={{ display: "flex", gap: 4, overflowX: "auto" }}>
                    {["All", "Pending", "Assigned", "Picked Up", "In Transit", "Delivered", "Cancelled"].map(f => (<button key={f} onClick={() => setStatusFilter(f)} style={{ padding: "7px 14px", borderRadius: 8, border: `1px solid ${statusFilter === f ? "transparent" : S.border}`, cursor: "pointer", fontFamily: "inherit", fontSize: 12, fontWeight: 600, background: statusFilter === f ? S.goldPale : S.card, color: statusFilter === f ? S.gold : S.textMuted, whiteSpace: "nowrap" }}>{f}</button>))}
                </div>
                <div style={{ flex: 1, background: S.card, borderRadius: 10, border: `1px solid ${S.border}`, display: "flex", alignItems: "center", gap: 8, padding: "0 12px" }}>
                    <span style={{ opacity: 0.4 }}>{I.search}</span>
                    <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search orders..." style={{ flex: 1, background: "transparent", border: "none", color: S.text, fontSize: 12, fontFamily: "inherit", height: 38, outline: "none" }} />
                </div>
                <button style={{ display: "flex", alignItems: "center", gap: 6, padding: "0 14px", borderRadius: 10, border: `1px solid ${S.border}`, background: S.card, color: S.textDim, cursor: "pointer", fontSize: 12, fontFamily: "inherit" }}>{I.download} Export CSV</button>
            </div>
            <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, overflow: "hidden" }}>
                <div style={{ display: "grid", gridTemplateColumns: "100px 1fr 1fr 1fr 1fr 100px 70px 70px", padding: "10px 16px", background: S.borderLight, fontSize: 10, fontWeight: 700, color: S.textMuted, textTransform: "uppercase", letterSpacing: "0.5px", borderBottom: `1px solid ${S.border}` }}>
                    <span>ID</span><span>Customer</span><span>Merchant</span><span>Route</span><span>Rider</span><span>Amount</span><span>COD</span><span>Status</span>
                </div>
                <div style={{ maxHeight: "calc(100vh - 310px)", overflowY: "auto" }}>
                    {filtered.map(o => (
                        <div key={o.id} onClick={() => onSelect(o.id)} style={{ display: "grid", gridTemplateColumns: "100px 1fr 1fr 1fr 1fr 100px 70px 70px", padding: "12px 16px", borderBottom: `1px solid ${S.borderLight}`, cursor: "pointer", alignItems: "center", transition: "background 0.12s" }} onMouseEnter={e => e.currentTarget.style.background = S.borderLight} onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                            <span style={{ fontSize: 11, fontWeight: 700, color: S.gold, fontFamily: "'Space Mono',monospace" }}>{o.id}</span>
                            <div><div style={{ fontSize: 12, fontWeight: 600 }}>{o.customer}</div><div style={{ fontSize: 10, color: S.textMuted }}>{o.customerPhone}</div></div>
                            <span style={{ fontSize: 11, color: S.textDim }}>{o.merchant}</span>
                            <span style={{ fontSize: 11, color: S.textMuted, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{o.pickup.split(",")[0]} → {o.dropoff.split(",")[0]}</span>
                            <div style={{ fontSize: 11, color: o.rider ? S.text : S.red, fontStyle: o.rider ? "normal" : "italic" }}>{o.rider || "Unassigned"}</div>
                            <span style={{ fontSize: 12, fontWeight: 600, fontFamily: "'Space Mono',monospace" }}>₦{o.amount.toLocaleString()}</span>
                            <span style={{ fontSize: 11, color: o.cod > 0 ? S.green : S.textMuted, fontFamily: "'Space Mono',monospace" }}>{o.cod > 0 ? `₦${(o.cod / 1000).toFixed(0)}K` : "—"}</span>
                            <Badge status={o.status} />
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
