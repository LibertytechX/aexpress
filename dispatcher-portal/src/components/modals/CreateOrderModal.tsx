import { useState } from "react";
import { OrderService } from "../../services/orderService";
import type { Rider, Merchant } from "../../types";
import { S } from "../common/theme";
import { I } from "../icons";

interface CreateOrderModalProps {
    riders: Rider[];
    merchants: Merchant[];
    onClose: () => void;
}

export function CreateOrderModal({ riders, merchants, onClose }: CreateOrderModalProps) {
    const [vehicle, setVehicle] = useState("Bike");
    const [codOn, setCodOn] = useState(false);

    // Form States
    const [merchantId, setMerchantId] = useState("");
    const [customerName, setCustomerName] = useState("");
    const [customerPhone, setCustomerPhone] = useState("");
    const [receiverName, setReceiverName] = useState(""); // Add receiver fields if needed, reusing customer for now as "Sender/Receiver" logic
    const [receiverPhone, setReceiverPhone] = useState("");
    const [pickup, setPickup] = useState("");
    const [dropoff, setDropoff] = useState("");
    const [pkgType, setPkgType] = useState("Box");
    const [codAmount, setCodAmount] = useState("");
    const [riderId, setRiderId] = useState("");
    const [price, setPrice] = useState("");
    const [loading, setLoading] = useState(false);

    const iSt = { width: "100%", border: `1.5px solid ${S.border}`, borderRadius: 10, padding: "0 14px", height: 42, fontSize: 13, fontFamily: "inherit", color: S.navy, background: "#fff" };
    const lSt = { display: "block", fontSize: 11, fontWeight: 600, color: S.textMuted, marginBottom: 5, textTransform: "uppercase", letterSpacing: "0.5px" };

    const handleSubmit = async () => {
        setLoading(true);
        // Map form to payload

        const payload = {
            merchantId, // Send selected merchant ID (6-char)
            pickup,
            dropoff,
            senderName: customerName || "Dispatcher",
            senderPhone: customerPhone || "0000000000",
            receiverName: receiverName || "Receiver", // We need inputs for receiver
            receiverPhone: receiverPhone || "0000000000",
            vehicle,
            packageType: pkgType,
            price: price ? parseFloat(price) : null,
            cod: codOn ? parseFloat(codAmount) : 0,
            riderId: riderId || ""
        };

        const success = await OrderService.createOrder(payload);
        setLoading(false);
        if (success) {
            onClose();
            window.location.reload(); // Simple reload to refresh data
        } else {
            alert("Failed to create order");
        }
    };

    return (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }} onClick={onClose}>
            <div onClick={e => e.stopPropagation()} style={{ background: S.card, borderRadius: 16, border: `1px solid ${S.border}`, width: 520, maxHeight: "85vh", overflowY: "auto", boxShadow: "0 24px 64px rgba(0,0,0,0.15)" }}>
                <div style={{ padding: "18px 24px", borderBottom: `1px solid ${S.border}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div><h2 style={{ fontSize: 18, fontWeight: 800, margin: 0 }}>Create Order</h2><p style={{ fontSize: 12, color: S.textMuted, margin: "2px 0 0" }}>Manual dispatch order</p></div>
                    <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", color: S.textMuted }}>{I.x}</button>
                </div>
                <div style={{ padding: "20px 24px" }}>
                    <div style={{ marginBottom: 16 }}><label style={lSt}>Merchant</label>
                        <select style={{ ...iSt, cursor: "pointer" }} value={merchantId} onChange={e => setMerchantId(e.target.value)}>
                            <option value="">Select merchant...</option>
                            {merchants.map(m => (
                                <option key={m.id} value={m.id}>{m.name || "Unknown"} — {m.phone || m.id}</option>
                            ))}
                        </select>
                    </div>
                    {/* Customer is Sender */}
                    <div style={{ marginBottom: 16 }}><label style={lSt}>Sender (Customer)</label><div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}><input placeholder="Name" style={iSt} value={customerName} onChange={e => setCustomerName(e.target.value)} /><input placeholder="Phone" style={iSt} value={customerPhone} onChange={e => setCustomerPhone(e.target.value)} /></div></div>

                    <div style={{ marginBottom: 16 }}><label style={lSt}>Pickup Address</label><input placeholder="Enter pickup address..." style={iSt} value={pickup} onChange={e => setPickup(e.target.value)} /></div>

                    {/* Receiver */}
                    <div style={{ marginBottom: 16 }}><label style={lSt}>Receiver</label><div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}><input placeholder="Name" style={iSt} value={receiverName} onChange={e => setReceiverName(e.target.value)} /><input placeholder="Phone" style={iSt} value={receiverPhone} onChange={e => setReceiverPhone(e.target.value)} /></div></div>

                    <div style={{ marginBottom: 16 }}><label style={lSt}>Dropoff Address</label><input placeholder="Enter delivery address..." style={iSt} value={dropoff} onChange={e => setDropoff(e.target.value)} /></div>

                    <div style={{ marginBottom: 16 }}><label style={lSt}>Vehicle Type</label>
                        <div style={{ display: "flex", gap: 8 }}>
                            {[{ id: "Bike", icon: "🏍️", p: "₦1,210" }, { id: "Car", icon: "🚗", p: "₦4,500" }, { id: "Van", icon: "🚐", p: "₦8,500" }].map(v => (<button key={v.id} onClick={() => setVehicle(v.id)} style={{ flex: 1, padding: 10, borderRadius: 10, cursor: "pointer", fontFamily: "inherit", border: vehicle === v.id ? `2px solid ${S.gold}` : `1px solid ${S.border}`, background: vehicle === v.id ? S.goldPale : S.borderLight, textAlign: "center" }}><div style={{ fontSize: 20 }}>{v.icon}</div><div style={{ fontSize: 12, fontWeight: 600, color: vehicle === v.id ? S.gold : S.text, marginTop: 2 }}>{v.id}</div><div style={{ fontSize: 10, color: S.textMuted, fontFamily: "'Space Mono',monospace" }}>{v.p}</div></button>))}
                        </div>
                    </div>

                    <div style={{ marginBottom: 16 }}><label style={lSt}>Package Type</label><select style={{ ...iSt, cursor: "pointer" }} value={pkgType} onChange={e => setPkgType(e.target.value)}>{["Box", "Envelope", "Document", "Food", "Fragile"].map(p => <option key={p}>{p}</option>)}</select></div>

                    <div style={{ marginBottom: 16, padding: "14px 16px", borderRadius: 10, border: codOn ? `2px solid ${S.green}` : `1px solid ${S.border}`, background: codOn ? S.greenBg : "transparent" }}>
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                            <div><div style={{ fontSize: 13, fontWeight: 600 }}>💵 Cash on Delivery</div><div style={{ fontSize: 11, color: S.textMuted }}>₦500 flat fee</div></div>
                            <div onClick={() => setCodOn(!codOn)} style={{ width: 40, height: 22, borderRadius: 11, cursor: "pointer", background: codOn ? S.green : S.border, position: "relative" }}><div style={{ width: 18, height: 18, borderRadius: "50%", background: "#fff", position: "absolute", top: 2, left: codOn ? 20 : 2, transition: "left 0.2s", boxShadow: "0 1px 3px rgba(0,0,0,0.2)" }} /></div>
                        </div>
                        {codOn && <div style={{ marginTop: 10 }}><input placeholder="COD amount (₦)" style={{ ...iSt, fontFamily: "'Space Mono',monospace", fontSize: 16, fontWeight: 700 }} value={codAmount} onChange={e => setCodAmount(e.target.value)} /></div>}
                    </div>

                    <div style={{ marginBottom: 16 }}><label style={lSt}>Assign Rider (Optional)</label>
                        <select style={{ ...iSt, cursor: "pointer" }} value={riderId} onChange={e => setRiderId(e.target.value)}>
                            <option value="">Auto-assign nearest rider</option>
                            {riders.filter(r => r.status === "online" && !r.currentOrder).map(r => (<option key={r.id} value={r.id}>{r.name} — {r.vehicle} • ⭐ {r.rating} • Available</option>))}
                            {riders.filter(r => r.status === "on_delivery").map(r => (<option key={r.id} value={r.id} disabled>{r.name} — {r.vehicle} • 📦 Busy ({r.currentOrder})</option>))}
                        </select>
                    </div>

                    <div style={{ marginBottom: 20 }}><label style={lSt}>Price Override</label><input placeholder="Leave blank for standard" style={{ ...iSt, fontFamily: "'Space Mono',monospace" }} value={price} onChange={e => setPrice(e.target.value)} /></div>

                    <div style={{ display: "flex", gap: 10 }}>
                        <button onClick={onClose} style={{ flex: 1, padding: "12px 0", borderRadius: 10, border: `1px solid ${S.border}`, background: "transparent", color: S.textDim, cursor: "pointer", fontFamily: "inherit", fontSize: 13, fontWeight: 600 }}>Cancel</button>
                        <button onClick={handleSubmit} disabled={loading} style={{ flex: 2, padding: "12px 0", borderRadius: 10, border: "none", cursor: "pointer", fontFamily: "inherit", background: `linear-gradient(135deg,${S.gold},${S.goldLight})`, color: S.navy, fontWeight: 800, fontSize: 14, opacity: loading ? 0.7 : 1 }}>
                            {loading ? "Creating..." : "Create Order"}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
