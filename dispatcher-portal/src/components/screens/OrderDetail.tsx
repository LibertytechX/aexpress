"use client";
import { useState } from "react";
import type { Order, Rider, LogEvent } from "../../types";
import { S } from "../common/theme";
import { I } from "../icons";
import { LagosMap } from "../map/LagosMap";
import { DeliveryRouteMap } from "../map/DeliveryRouteMap";
import { RelayRouteMap } from "../map/RelayRouteMap";
import { Badge } from "../common/Badge";
import { SelectRiderModal } from "../modals/SelectRiderModal";
import { OrdersAPI } from "@/lib/api";

const STS: Record<string, { bg: string; text: string }> = {
    Pending: { bg: S.yellowBg, text: S.yellow },
    Assigned: { bg: S.blueBg, text: S.blue },
    "Picked Up": { bg: S.purpleBg, text: S.purple },
    "In Transit": { bg: "rgba(232,168,56,0.1)", text: S.gold },
    "At Dropoff": { bg: "rgba(249,115,22,0.12)", text: "#F97316" },
    Delivered: { bg: S.greenBg, text: S.green },
    Cancelled: { bg: S.redBg, text: S.red },
    Failed: { bg: S.redBg, text: "#F87171" }
};

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
    const [editPickup, setEditPickup] = useState(false);
    const [editDropoff, setEditDropoff] = useState(false);
    const [pickupVal, setPickupVal] = useState(order.pickup || "");
    const [dropoffVal, setDropoffVal] = useState(order.dropoff || "");
    const [editPrice, setEditPrice] = useState(false);
    const [priceVal, setPriceVal] = useState(String(order.amount || 0));
    const [showStatusMenu, setShowStatusMenu] = useState(false);
    const [relayLoading, setRelayLoading] = useState(false);
    const [relayError, setRelayError] = useState("");
    const [priceSaving, setPriceSaving] = useState(false);
    const [priceError, setPriceError] = useState("");

    const rider = order.riderId ? riders.find(r => r.id === order.riderId) : null;
    const isTerminal = ["Delivered", "Cancelled", "Failed"].includes(order.status);
    const isRelay = !!((order as any).relayLegs && (order as any).relayLegs.length > 0);
    const showDeliveryMap = !isRelay && order.pickup && order.dropoff;

    // Status flow for progression
    const nextStatuses = () => {
        const flow = ["Pending", "Assigned", "Picked Up", "In Transit", "At Dropoff", "Delivered"];
        const idx = flow.indexOf(order.status);
        const opts = [];
        if (idx >= 0 && idx < flow.length - 1) opts.push(flow[idx + 1]);
        if (!isTerminal) { opts.push("Cancelled"); opts.push("Failed"); }
        return opts;
    };

    const savePickup = () => { onUpdateOrder(order.id, "pickup", pickupVal); addLog(order.id, `Pickup address changed to: ${pickupVal}`, "edit"); setEditPickup(false); };
    const saveDropoff = () => { onUpdateOrder(order.id, "dropoff", dropoffVal); addLog(order.id, `Dropoff address changed to: ${dropoffVal}`, "edit"); setEditDropoff(false); };
    const savePrice = async () => {
        const n = Number(priceVal);
        const next = Number.isFinite(n) && n >= 0 ? n : order.amount;
        setPriceSaving(true);
        setPriceError("");
        try {
            const updated = await OrdersAPI.updatePrice(order.id, next);
            onUpdateOrder(order.id, "amount", updated.amount);
            addLog(order.id, `Price changed to ₦${updated.amount.toLocaleString()}`, "edit");
            setEditPrice(false);
        } catch (e: any) {
            setPriceError(e?.error || e?.detail || e?.message || "Failed to update price");
        } finally {
            setPriceSaving(false);
        }
    };

    const handleGenerateRelayRoute = async (force = false) => {
        setRelayLoading(true);
        setRelayError("");
        try {
            const updated: any = await OrdersAPI.generateRelayRoute(order.id, force);
            onUpdateOrder(order.id, "isRelayOrder", updated.isRelayOrder);
            onUpdateOrder(order.id, "routingStatus", updated.routingStatus);
            onUpdateOrder(order.id, "routingError", updated.routingError);
            onUpdateOrder(order.id, "relayLegsCount", updated.relayLegsCount);
            onUpdateOrder(order.id, "relayLegs", updated.relayLegs);
            onUpdateOrder(order.id, "suggestedRiderId", updated.suggestedRiderId);
        } catch (e: any) {
            setRelayError(e?.error || e?.message || "Failed to generate relay route");
        } finally {
            setRelayLoading(false);
        }
    };

    const logColors: Record<string, string> = { create: S.gold, payment: S.blue, assign: S.green, status: S.textDim, pickup: S.purple, transit: S.gold, cod: S.green, delivered: S.green, settlement: S.gold, cancel: S.red, fail: S.red, edit: S.blue };

    const iStyle: any = { width: "100%", border: `1.5px solid ${S.border}`, borderRadius: 8, padding: "8px 12px", fontSize: 13, fontFamily: "inherit", color: S.navy, background: "#fff", outline: "none", resize: "none" };

    return (
        <div style={{ animation: "fadeIn 0.2s ease-out" }}>
            <button onClick={onBack} style={{ display: "flex", alignItems: "center", gap: 6, padding: 0, background: "none", border: "none", cursor: "pointer", color: S.textDim, fontSize: 13, fontWeight: 600, fontFamily: "inherit", marginBottom: 16 }}>{I.back} Back to Orders</button>

            {/* Top bar */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, padding: "14px 20px", marginBottom: 16 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap" }}>
                    <span style={{ fontSize: 18, fontWeight: 800, color: S.gold, fontFamily: "'Space Mono',monospace" }}>{order.id}</span>
                    <Badge status={order.status} />
                    <span style={{ fontSize: 12, color: S.textMuted }}>{order.created}</span>
                    <span style={{ fontSize: 10, padding: "3px 8px", borderRadius: 6, background: order.vehicle === "Bike" ? S.goldPale : order.vehicle === "Car" ? S.blueBg : S.purpleBg, color: order.vehicle === "Bike" ? S.gold : order.vehicle === "Car" ? S.blue : S.purple, fontWeight: 700 }}>{order.vehicle}</span>
                    {order.cod > 0 && <span style={{ fontSize: 10, padding: "3px 8px", borderRadius: 6, background: S.greenBg, color: S.green, fontWeight: 700 }}>💵 COD ₦{order.cod.toLocaleString()}</span>}
                </div>
                <div style={{ display: "flex", gap: 8 }}>
                    <button style={{ display: "flex", alignItems: "center", gap: 5, padding: "7px 14px", borderRadius: 8, border: `1px solid ${S.border}`, background: S.card, color: S.textDim, cursor: "pointer", fontSize: 11, fontWeight: 600, fontFamily: "inherit" }}>{I.print} Label</button>
                    {order.status === "Pending" && <button onClick={() => onChangeStatus(order.id, "Cancelled")} style={{ padding: "7px 14px", borderRadius: 8, border: "none", background: S.redBg, color: S.red, cursor: "pointer", fontSize: 11, fontWeight: 700, fontFamily: "inherit" }}>Cancel</button>}
                </div>
            </div>

            {/* STATUS PROGRESSION BAR */}
            {!isTerminal && (
                <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, padding: "14px 20px", marginBottom: 16 }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 10 }}>
                        <span style={{ fontSize: 11, fontWeight: 700, color: S.textMuted, textTransform: "uppercase", letterSpacing: "0.5px" }}>Status Progression</span>
                        <div style={{ position: "relative" }}>
                            <button onClick={() => setShowStatusMenu(!showStatusMenu)} style={{ padding: "6px 14px", borderRadius: 8, border: `1px solid ${S.border}`, background: S.card, color: S.textDim, cursor: "pointer", fontSize: 11, fontWeight: 600, fontFamily: "inherit" }}>Change Status ▾</button>
                            {showStatusMenu && (
                                <div style={{ position: "absolute", right: 0, top: "100%", marginTop: 4, background: S.card, border: `1px solid ${S.border}`, borderRadius: 10, boxShadow: "0 8px 24px rgba(0,0,0,0.12)", zIndex: 10, minWidth: 180, overflow: "hidden" }}>
                                    {nextStatuses().map(ns => (
                                        <button key={ns} onClick={() => { onChangeStatus(order.id, ns); setShowStatusMenu(false); }} style={{ display: "block", width: "100%", padding: "10px 16px", border: "none", background: "transparent", cursor: "pointer", fontSize: 12, fontWeight: 600, fontFamily: "inherit", textAlign: "left", color: STS[ns] ? STS[ns].text : S.text, transition: "background 0.12s" }} onMouseEnter={e => e.currentTarget.style.background = S.borderLight} onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                                            → {ns}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 0 }}>
                        {["Pending", "Assigned", "In Transit", "At Dropoff", "Delivered"].map((st, i, arr) => {
                            // "Picked Up" is a transient state — treat it as "In Transit" on the bar
                            const barStatus = order.status === "Picked Up" ? "In Transit" : order.status;
                            const idx = arr.indexOf(barStatus);
                            const done = i <= idx;
                            const current = i === idx;
                            return (
                                <div key={st} style={{ display: "flex", alignItems: "center", flex: 1 }}>
                                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", flex: 0 }}>
                                        <div style={{ width: current ? 28 : 22, height: current ? 28 : 22, borderRadius: "50%", background: done ? (STS[st] ? STS[st].bg : "#eee") : "#f1f5f9", border: `2px solid ${done ? (STS[st] ? STS[st].text : S.gold) : S.border}`, display: "flex", alignItems: "center", justifyContent: "center", transition: "all 0.2s" }}>
                                            {done && i < idx ? <span style={{ color: STS[st] ? STS[st].text : S.green }}>{I.check}</span> : current ? <div style={{ width: 8, height: 8, borderRadius: "50%", background: STS[st] ? STS[st].text : S.gold }} /> : null}
                                        </div>
                                        <span style={{ fontSize: 9, fontWeight: done ? 700 : 500, color: done ? (STS[st] ? STS[st].text : S.gold) : S.textMuted, marginTop: 4, whiteSpace: "nowrap" }}>{st}</span>
                                    </div>
                                    {i < arr.length - 1 && <div style={{ flex: 1, height: 2, background: done && i < idx ? S.green : S.border, margin: "0 4px 16px 4px", transition: "background 0.3s" }} />}
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            <div style={{ display: "grid", gridTemplateColumns: "1fr 360px", gap: 16 }}>
                {/* LEFT */}
                <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                    {/* Customer + Merchant */}
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                        <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, padding: 16 }}>
                            <div style={{ fontSize: 10, fontWeight: 700, color: S.textMuted, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 10 }}>Customer</div>
                            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 2 }}>{order.customer}</div>
                            <div style={{ fontSize: 12, color: S.textDim, fontFamily: "'Space Mono',monospace", marginBottom: 8 }}>{order.customerPhone}</div>
                            <div style={{ display: "flex", gap: 6 }}>
                                <a href={`tel:${order.customerPhone}`} style={{ display: "flex", alignItems: "center", gap: 4, padding: "5px 10px", borderRadius: 6, background: S.goldPale, color: S.gold, fontSize: 10, fontWeight: 600, textDecoration: "none" }}>{I.phone} Call</a>
                                <a href={`https://wa.me/234${order.customerPhone?.slice(1)}`} target="_blank" rel="noreferrer" style={{ display: "flex", alignItems: "center", gap: 4, padding: "5px 10px", borderRadius: 6, background: S.greenBg, color: S.green, fontSize: 10, fontWeight: 600, textDecoration: "none" }}>💬 WhatsApp</a>
                            </div>
                        </div>

                        <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, padding: 16 }}>
                            <div style={{ fontSize: 10, fontWeight: 700, color: S.textMuted, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 10 }}>Merchant</div>
                            <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 2 }}>{order.merchant}</div>
                            <div style={{ fontSize: 12, color: S.textDim, fontFamily: "'Space Mono',monospace", marginBottom: 8 }}>{order.merchantPhone || "N/A"}</div>
                            <div style={{ display: "flex", gap: 6 }}>
                                {order.merchantPhone && <a href={`tel:${order.merchantPhone}`} style={{ display: "flex", alignItems: "center", gap: 4, padding: "5px 10px", borderRadius: 6, background: S.goldPale, color: S.gold, fontSize: 10, fontWeight: 600, textDecoration: "none" }}>{I.phone} Call</a>}
                            </div>
                        </div>
                    </div>

                    {/* Order Details & Pricing */}
                    <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, padding: 16 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
                            <div style={{ fontSize: 12, fontWeight: 700, color: S.navy }}>Package Details</div>
                            <div style={{ fontSize: 11, color: S.textDim }}>{order.pkg || "Standard Box"} • ₦{(order.amount || 0).toLocaleString()}</div>
                        </div>

                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                            {/* Pickup */}
                            <div style={{ position: "relative" }}>
                                <div style={{ fontSize: 10, fontWeight: 700, color: S.textMuted, textTransform: "uppercase", marginBottom: 4 }}>Pickup Address</div>
                                {editPickup ? (
                                    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                                        <textarea value={pickupVal} onChange={e => setPickupVal(e.target.value)} rows={3} style={iStyle} />
                                        <div style={{ display: "flex", gap: 4 }}>
                                            <button onClick={savePickup} style={{ flex: 1, padding: "6px", background: S.navy, color: "#fff", border: "none", borderRadius: 6, fontSize: 11, fontWeight: 700, cursor: "pointer" }}>Save</button>
                                            <button onClick={() => { setEditPickup(false); setPickupVal(order.pickup || ""); }} style={{ flex: 1, padding: "6px", background: S.bg, color: S.textDim, border: "none", borderRadius: 6, fontSize: 11, fontWeight: 700, cursor: "pointer" }}>Cancel</button>
                                        </div>
                                    </div>
                                ) : (
                                    <div style={{ fontSize: 12, color: S.text, lineHeight: 1.4, padding: "8px 10px", background: S.borderLight, borderRadius: 6, position: "relative" }}>
                                        {order.pickup}
                                        {!isTerminal && <button onClick={() => setEditPickup(true)} style={{ position: "absolute", top: 4, right: 4, background: "none", border: "none", cursor: "pointer", color: S.textMuted, padding: 2 }}>{I.edit}</button>}
                                    </div>
                                )}
                            </div>

                            {/* Dropoff */}
                            <div style={{ position: "relative" }}>
                                <div style={{ fontSize: 10, fontWeight: 700, color: S.textMuted, textTransform: "uppercase", marginBottom: 4 }}>Delivery Address</div>
                                {editDropoff ? (
                                    <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
                                        <textarea value={dropoffVal} onChange={e => setDropoffVal(e.target.value)} rows={3} style={iStyle} />
                                        <div style={{ display: "flex", gap: 4 }}>
                                            <button onClick={saveDropoff} style={{ flex: 1, padding: "6px", background: S.navy, color: "#fff", border: "none", borderRadius: 6, fontSize: 11, fontWeight: 700, cursor: "pointer" }}>Save</button>
                                            <button onClick={() => { setEditDropoff(false); setDropoffVal(order.dropoff || ""); }} style={{ flex: 1, padding: "6px", background: S.bg, color: S.textDim, border: "none", borderRadius: 6, fontSize: 11, fontWeight: 700, cursor: "pointer" }}>Cancel</button>
                                        </div>
                                    </div>
                                ) : (
                                    <div style={{ fontSize: 12, color: S.text, lineHeight: 1.4, padding: "8px 10px", background: S.borderLight, borderRadius: 6, position: "relative" }}>
                                        {order.dropoff}
                                        {!isTerminal && <button onClick={() => setEditDropoff(true)} style={{ position: "absolute", top: 4, right: 4, background: "none", border: "none", cursor: "pointer", color: S.textMuted, padding: 2 }}>{I.edit}</button>}
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Price Management line */}
                        <div style={{ marginTop: 16, paddingTop: 12, borderTop: `1px dashed ${S.border}`, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                            <div style={{ fontSize: 11, color: S.textDim }}>Delivery Fee</div>
                            {editPrice ? (
                                <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                                    <span style={{ fontSize: 12, fontWeight: 700 }}>₦</span>
                                    <input type="number" value={priceVal} onChange={e => setPriceVal(e.target.value)} style={{ width: 80, padding: 4, borderRadius: 4, border: `1px solid ${S.border}`, outline: "none", fontFamily: "'Space Mono',monospace", fontSize: 13, fontWeight: 700 }} />
                                    <button onClick={savePrice} disabled={priceSaving} style={{ padding: "4px 10px", background: S.navy, color: "#fff", border: "none", borderRadius: 4, fontSize: 11, fontWeight: 600, cursor: priceSaving ? "wait" : "pointer" }}>Save</button>
                                    <button onClick={() => { setEditPrice(false); setPriceVal(String(order.amount)); }} style={{ padding: "4px 10px", background: S.bg, border: "none", borderRadius: 4, fontSize: 11, cursor: "pointer" }}>X</button>
                                </div>
                            ) : (
                                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                    <div style={{ fontSize: 16, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono',monospace" }}>₦{(order.amount || 0).toLocaleString()}</div>
                                    {!isTerminal && <button onClick={() => setEditPrice(true)} style={{ padding: 4, background: S.bg, border: "none", borderRadius: 4, cursor: "pointer", color: S.textMuted }}>{I.edit}</button>}
                                </div>
                            )}
                        </div>
                        {priceError && <div style={{ fontSize: 11, color: S.red, marginTop: 4, textAlign: "right" }}>{priceError}</div>}
                    </div>

                    {/* Rider / Relay section */}
                    <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, padding: 16 }}>
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
                            <div style={{ fontSize: 12, fontWeight: 700, color: S.navy }}>Assigned Rider</div>
                            {isRelay && <span style={{ fontSize: 9, padding: "3px 8px", borderRadius: 6, background: S.purpleBg, color: S.purple, fontWeight: 800 }}>RELAY LEGS</span>}
                        </div>

                        {rider ? (
                            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", background: S.bg, padding: "10px 14px", borderRadius: 10 }}>
                                <div style={{ display: "flex", alignItems: "center", gap: 12, cursor: "pointer" }} onClick={() => onViewRider(rider.id)}>
                                    <div style={{ width: 32, height: 32, borderRadius: 8, background: S.goldPale, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 13, fontWeight: 800, color: S.gold }}>{rider.name.split(" ").map(n => n[0]).join("")}</div>
                                    <div>
                                        <div style={{ fontSize: 13, fontWeight: 700, color: S.navy }}>{rider.name}</div>
                                        <div style={{ fontSize: 11, color: S.textMuted, marginTop: 2 }}>{rider.vehicle} • {rider.phone}</div>
                                    </div>
                                </div>
                                {!isTerminal && (
                                    <button onClick={() => onAssign(order.id, "")} style={{ fontSize: 11, padding: "6px 12px", color: S.red, background: S.redBg, borderRadius: 6, border: "none", cursor: "pointer", fontWeight: 700 }}>Unassign</button>
                                )}
                            </div>
                        ) : (
                            <div style={{ background: S.bg, padding: "16px", borderRadius: 10, textAlign: "center" }}>
                                <div style={{ fontSize: 12, color: S.textMuted, marginBottom: 12 }}>No rider assigned yet</div>
                                <button onClick={() => setShowAssign(true)} style={{ padding: "8px 16px", background: S.navy, color: "#fff", border: "none", borderRadius: 8, fontSize: 12, fontWeight: 700, cursor: "pointer", display: "inline-flex", alignItems: "center", gap: 6 }}>{I.plus} Assign Rider</button>
                                {showAssign && (
                                    <SelectRiderModal
                                        riders={riders}
                                        onClose={() => setShowAssign(false)}
                                        onSelect={(rid) => { onAssign(order.id, rid); setShowAssign(false); }}
                                    />
                                )}
                            </div>
                        )}

                        {/* Relay route tooling */}
                        {!isTerminal && (
                            <div style={{ marginTop: 16, paddingTop: 16, borderTop: `1px solid ${S.borderLight}` }}>
                                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                                    <span style={{ fontSize: 11, fontWeight: 600, color: S.textDim }}>{(order as any).isRelayOrder ? "Hub Routing Active" : "Direct Routing"}</span>
                                    <button onClick={() => handleGenerateRelayRoute((order as any).isRelayOrder)} disabled={relayLoading} style={{ fontSize: 10, padding: "4px 10px", borderRadius: 6, background: S.blueBg, color: S.blue, border: "none", cursor: relayLoading ? "wait" : "pointer", fontWeight: 700 }}>
                                        {relayLoading ? "Computing..." : ((order as any).isRelayOrder ? "Recalculate Route" : "Generate Relay Route")}
                                    </button>
                                </div>
                                {relayError && <div style={{ fontSize: 11, color: S.red, marginTop: 6 }}>{relayError}</div>}
                            </div>
                        )}
                    </div>

                    {/* One-click fast status advancement buttons */}
                    {!isTerminal && (
                        <div style={{ display: "flex", gap: 8 }}>
                            {order.status === "Assigned" && <button onClick={() => onChangeStatus(order.id, "Picked Up")} style={{ flex: 1, padding: 12, borderRadius: 10, background: S.purpleBg, color: S.purple, border: "none", fontSize: 12, fontWeight: 800, cursor: "pointer" }}>Confirm Pickup</button>}
                            {order.status === "Picked Up" && <button onClick={() => onChangeStatus(order.id, "In Transit")} style={{ flex: 1, padding: 12, borderRadius: 10, background: "rgba(232,168,56,0.15)", color: S.gold, border: "none", fontSize: 12, fontWeight: 800, cursor: "pointer" }}>Start Delivery</button>}
                            {order.status === "In Transit" && <button onClick={() => onChangeStatus(order.id, "At Dropoff")} style={{ flex: 1, padding: 12, borderRadius: 10, background: S.blueBg, color: S.blue, border: "none", fontSize: 12, fontWeight: 800, cursor: "pointer" }}>Arrived at Dropoff</button>}
                            {order.status === "At Dropoff" && <button onClick={() => onChangeStatus(order.id, "Delivered")} style={{ flex: 1, padding: 12, borderRadius: 10, background: S.greenBg, color: S.green, border: "none", fontSize: 12, fontWeight: 800, cursor: "pointer" }}>Confirm Delivery</button>}
                        </div>
                    )}
                </div>

                {/* RIGHT: MAP & TIMELINE */}
                <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                    <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, padding: 16 }}>
                        <div style={{ fontSize: 12, fontWeight: 700, color: S.navy, marginBottom: 12 }}>Live Location</div>
                        {isRelay ? (
                            <RelayRouteMap order={order} riders={riders} />
                        ) : showDeliveryMap ? (
                            <DeliveryRouteMap order={order} rider={rider} />
                        ) : (
                            <LagosMap orders={[order]} riders={rider ? [rider] : []} highlightOrder={order.id} small={false} showZones={false} relayNodes={[]} zones={[]} mode="live" />
                        )}
                    </div>

                    <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, display: "flex", flexDirection: "column", flex: 1, minHeight: 300 }}>
                        <div style={{ padding: "14px 16px", borderBottom: `1px solid ${S.borderLight}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                            <span style={{ fontSize: 12, fontWeight: 700, color: S.navy }}>Activity Timeline</span>
                            <button style={{ background: "none", border: "none", color: S.blue, fontSize: 11, fontWeight: 700, cursor: "pointer" }}>+ Note</button>
                        </div>
                        <div style={{ flex: 1, padding: "20px 16px", overflowY: "auto" }}>
                            {logs && logs.length > 0 ? logs.map((l, i) => (
                                <div key={i} style={{ display: "flex", gap: 12, marginBottom: i < logs.length - 1 ? 20 : 0, position: "relative" }}>
                                    {i < logs.length - 1 && <div style={{ position: "absolute", left: 5, top: 14, bottom: -24, width: 2, background: S.borderLight }} />}
                                    <div style={{ width: 12, height: 12, borderRadius: "50%", background: logColors[l.type || "status"] || S.textMuted, marginTop: 2, flexShrink: 0, border: "2px solid #fff", boxShadow: "0 0 0 1px " + S.border }} />
                                    <div>
                                        <div style={{ fontSize: 12, color: S.navy, fontWeight: 600, lineHeight: 1.4 }}>{l.event}</div>
                                        <div style={{ fontSize: 10, color: S.textMuted, marginTop: 4, fontFamily: "'Space Mono',monospace" }}>{l.time} • <span style={{ fontWeight: 600 }}>{l.by}</span></div>
                                    </div>
                                </div>
                            )) : (
                                <div style={{ textAlign: "center", fontSize: 12, color: S.textMuted, marginTop: 20 }}>No activity logged yet</div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
