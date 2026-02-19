import { useState } from "react";
import type { Order, Rider, LogEvent } from "../../types";
import { S } from "../common/theme";
import { I } from "../icons";
import { LagosMap } from "../map/LagosMap";
import { Badge } from "../common/Badge";
import { SelectRiderModal } from "../modals/SelectRiderModal";

interface OrderDetailProps {
    order: Order;
    riders: Rider[];
    onBack: () => void;
    onViewRider: (id: string) => void;
    onAssign: (oid: string, rid: string) => void;
    onChangeStatus: (oid: string, s: any) => void;
    onUpdateOrder: (oid: string, field: string, val: any) => void;
    addLog: (oid: string, text: string, type?: string) => void;
    logs: LogEvent[];
}

export function OrderDetail({ order, riders, onBack, onViewRider, onAssign, onChangeStatus, onUpdateOrder, addLog, logs }: OrderDetailProps) {
    const [showAssign, setShowAssign] = useState(false);
    const [editPrice, setEditPrice] = useState(false);
    const [editPickup, setEditPickup] = useState(false);
    const [newPrice, setNewPrice] = useState(order.amount.toString());
    const [newPickup, setNewPickup] = useState(order.pickup);

    const rider = order.riderId ? riders.find(r => r.id === order.riderId) : null;
    const isTerminal = ["Delivered", "Cancelled", "Failed"].includes(order.status);

    const handleSavePrice = () => {
        onUpdateOrder(order.id, "amount", parseFloat(newPrice));
        setEditPrice(false);
        addLog(order.id, `Price updated to ₦${parseFloat(newPrice).toLocaleString()}`, "info");
    };

    const handleSavePickup = () => {
        onUpdateOrder(order.id, "pickup", newPickup);
        setEditPickup(false);
        addLog(order.id, `Pickup address updated to ${newPickup}`, "info");
    };

    return (
        <div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
                <button onClick={onBack} style={{ display: "flex", alignItems: "center", gap: 6, padding: 0, background: "none", border: "none", cursor: "pointer", color: S.textDim, fontSize: 13, fontWeight: 600, fontFamily: "inherit" }}>{I.back} Back to Orders</button>
                <div style={{ display: "flex", gap: 8 }}>
                    {order.status === "Pending" && <button onClick={() => onChangeStatus(order.id, "Cancelled")} style={{ padding: "8px 14px", borderRadius: 8, border: `1px solid ${S.red}`, background: S.redBg, color: S.red, fontSize: 11, fontWeight: 700, cursor: "pointer", fontFamily: "inherit" }}>CANCEL ORDER</button>}
                    {["Assigned", "Picked Up", "In Transit"].includes(order.status) && <button onClick={() => onChangeStatus(order.id, "Failed")} style={{ padding: "8px 14px", borderRadius: 8, border: `1px solid ${S.red}`, background: S.redBg, color: S.red, fontSize: 11, fontWeight: 700, cursor: "pointer", fontFamily: "inherit" }}>MARK FAILED</button>}
                </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: 20 }}>
                {/* Left Col */}
                <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                    {/* Header Card */}
                    <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, padding: 20 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
                            <div>
                                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                                    <div style={{ fontSize: 24, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono',monospace" }}>{order.id}</div>
                                    <Badge status={order.status} />
                                </div>
                                <div style={{ fontSize: 12, color: S.textMuted, marginTop: 4 }}>Created on {order.created} • {order.vehicle} • {order.pkg}</div>
                            </div>
                            <div style={{ textAlign: "right" }}>
                                <div style={{ fontSize: 11, color: S.textMuted, textTransform: "uppercase", letterSpacing: "0.5px", fontWeight: 700 }}>Total Amount</div>
                                {editPrice ? (
                                    <div style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: 4 }}>
                                        <input value={newPrice} onChange={e => setNewPrice(e.target.value)} style={{ width: 80, textAlign: "right", fontFamily: "'Space Mono',monospace", fontSize: 18, fontWeight: 700, border: `1px solid ${S.border}`, borderRadius: 4 }} />
                                        <button onClick={handleSavePrice} style={{ padding: 4, background: S.green, color: "#fff", border: "none", borderRadius: 4, cursor: "pointer" }}>{I.check}</button>
                                    </div>
                                ) : (
                                    <div style={{ display: "flex", alignItems: "center", gap: 6, justifyContent: "flex-end" }}>
                                        <div style={{ fontSize: 24, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono',monospace" }}>₦{order.amount.toLocaleString()}</div>
                                        {!isTerminal && <button onClick={() => setEditPrice(true)} style={{ padding: 4, background: "transparent", border: "none", cursor: "pointer", color: S.textMuted }} title="Edit Price">{I.edit}</button>}
                                    </div>
                                )}
                                <div style={{ fontSize: 11, color: order.cod > 0 ? S.green : S.textMuted, fontWeight: 600 }}>{order.cod > 0 ? `Includes ₦${order.cod.toLocaleString()} COD` : "Prepaid"}</div>
                            </div>
                        </div>

                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, paddingTop: 16, borderTop: `1px solid ${S.border}` }}>
                            <div>
                                <div style={{ fontSize: 11, fontWeight: 700, color: S.textMuted, textTransform: "uppercase", marginBottom: 8 }}>Pickup Details</div>
                                <div style={{ fontSize: 13, fontWeight: 700 }}>{order.merchant}</div>
                                {editPickup ? (
                                    <div style={{ display: "flex", alignItems: "center", gap: 4, marginTop: 4 }}>
                                        <input value={newPickup} onChange={e => setNewPickup(e.target.value)} style={{ flex: 1, fontSize: 12, padding: 4, border: `1px solid ${S.border}`, borderRadius: 4 }} />
                                        <button onClick={handleSavePickup} style={{ padding: 4, background: S.green, color: "#fff", border: "none", borderRadius: 4, cursor: "pointer" }}>{I.check}</button>
                                    </div>
                                ) : (
                                    <div style={{ fontSize: 12, color: S.textDim, marginTop: 4, lineHeight: 1.4 }}>
                                        {order.pickup}
                                        {!isTerminal && <button onClick={() => setEditPickup(true)} style={{ padding: 0, marginLeft: 6, background: "none", border: "none", cursor: "pointer", color: S.textMuted, verticalAlign: "middle" }}>{I.edit}</button>}
                                    </div>
                                )}
                                <div style={{ fontSize: 11, fontWeight: 700, color: S.textMuted, textTransform: "uppercase", marginBottom: 8, marginTop: 16 }}>Customer Details</div>
                                <div style={{ fontSize: 13, fontWeight: 700 }}>{order.customer}</div>
                                <div style={{ fontSize: 12, color: S.textDim, fontFamily: "'Space Mono',monospace", marginTop: 4 }}>{order.customerPhone}</div>
                            </div>
                            <div style={{ paddingLeft: 20, borderLeft: `1px solid ${S.borderLight}` }}>
                                <div style={{ fontSize: 11, fontWeight: 700, color: S.textMuted, textTransform: "uppercase", marginBottom: 8 }}>Delivery Details</div>
                                <div style={{ fontSize: 13, fontWeight: 700, color: S.textDim }}>Dropoff Location</div>
                                <div style={{ fontSize: 12, color: S.textDim, marginTop: 4, lineHeight: 1.4 }}>{order.dropoff}</div>

                                {/* Rider Assignment Section */}
                                <div style={{ marginTop: 16, padding: "10px 14px", background: S.bg, borderRadius: 10, border: `1px solid ${S.border}` }}>
                                    <div style={{ fontSize: 11, fontWeight: 700, color: S.textMuted, textTransform: "uppercase", marginBottom: 6 }}>Assigned Rider</div>
                                    {rider ? (
                                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                                            <div style={{ display: "flex", alignItems: "center", gap: 8, cursor: "pointer" }} onClick={() => onViewRider(rider.id)}>
                                                <div style={{ width: 24, height: 24, borderRadius: 6, background: S.goldPale, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 10, fontWeight: 800, color: S.gold }}>{rider.name.split(" ").map(n => n[0]).join("")}</div>
                                                <div><div style={{ fontSize: 12, fontWeight: 700 }}>{rider.name}</div><div style={{ fontSize: 10, color: S.textMuted }}>{rider.vehicle} • {rider.phone}</div></div>
                                            </div>
                                            {!isTerminal && <button onClick={() => onAssign(order.id, "")} style={{ fontSize: 10, color: S.red, background: "transparent", border: "none", cursor: "pointer", fontWeight: 600 }}>Unassign</button>}
                                        </div>
                                    ) : (
                                        <div>
                                            <button onClick={() => setShowAssign(true)} style={{ width: "100%", padding: "6px 0", background: S.navy, color: "#fff", border: "none", borderRadius: 6, fontSize: 11, fontWeight: 600, cursor: "pointer" }}>+ Assign Rider</button>
                                            {showAssign && (
                                                <SelectRiderModal
                                                    riders={riders}
                                                    onClose={() => setShowAssign(false)}
                                                    onSelect={(rid) => { onAssign(order.id, rid); setShowAssign(false); }}
                                                />
                                            )}
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Action Bar */}
                        {!isTerminal && (
                            <div style={{ marginTop: 16, paddingTop: 16, borderTop: `1px solid ${S.border}`, display: "flex", gap: 10 }}>
                                {order.status === "Assigned" && <button onClick={() => onChangeStatus(order.id, "Picked Up")} style={{ flex: 1, padding: 10, borderRadius: 8, background: S.purpleBg, color: S.purple, border: "none", fontSize: 12, fontWeight: 700, cursor: "pointer" }}>Confirm Pickup</button>}
                                {order.status === "Picked Up" && <button onClick={() => onChangeStatus(order.id, "In Transit")} style={{ flex: 1, padding: 10, borderRadius: 8, background: "rgba(232,168,56,0.15)", color: S.gold, border: "none", fontSize: 12, fontWeight: 700, cursor: "pointer" }}>Start Delivery</button>}
                                {order.status === "In Transit" && <button onClick={() => onChangeStatus(order.id, "Delivered")} style={{ flex: 1, padding: 10, borderRadius: 8, background: S.greenBg, color: S.green, border: "none", fontSize: 12, fontWeight: 700, cursor: "pointer" }}>Confirm Delivery</button>}
                            </div>
                        )}
                    </div>

                    {/* Map */}
                    <LagosMap orders={[order]} riders={rider ? [rider] : []} highlightOrder={order.id} showZones={false} />
                </div>

                {/* Right Col: Timeline & Activity */}
                <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, display: "flex", flexDirection: "column", overflow: "hidden" }}>
                    <div style={{ padding: "14px 18px", borderBottom: `1px solid ${S.border}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ fontSize: 13, fontWeight: 700 }}>Order Timeline</span>
                        <button style={{ background: "none", border: "none", color: S.blue, fontSize: 11, fontWeight: 600, cursor: "pointer" }}>+ Add Note</button>
                    </div>
                    <div style={{ flex: 1, padding: "14px 18px", overflowY: "auto", maxHeight: 600 }}>
                        {logs.map((l, i) => (
                            <div key={i} style={{ display: "flex", gap: 10, marginBottom: 16, position: "relative" }}>
                                {i < logs.length - 1 && <div style={{ position: "absolute", left: 4, top: 10, bottom: -20, width: 1, background: S.borderLight }} />}
                                <div style={{ width: 9, height: 9, borderRadius: "50%", background: l.type === "status" ? S.gold : l.type === "issue" ? S.red : S.textMuted, marginTop: 4, flexShrink: 0 }} />
                                <div>
                                    <div style={{ fontSize: 12, color: S.text, lineHeight: 1.3 }}>{l.event}</div>
                                    <div style={{ fontSize: 10, color: S.textMuted, marginTop: 2 }}>{l.time} • <span style={{ fontWeight: 600 }}>{l.by}</span></div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}
