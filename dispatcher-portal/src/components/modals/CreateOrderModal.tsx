import { useState, useEffect } from "react";
import { OrderService } from "../../services/orderService";
import type { Rider, Merchant, Vehicle } from "../../types";
import { S } from "../common/theme";
import { I } from "../icons";
import { AddressAutocompleteInput } from "../common/AddressAutocompleteInput";

interface CreateOrderModalProps {
    riders: Rider[];
    merchants: Merchant[];
    onClose: () => void;
}

export function CreateOrderModal({ riders, merchants, onClose }: CreateOrderModalProps) {
    const [vehicle, setVehicle] = useState("Bike");
    const [vehicles, setVehicles] = useState<Vehicle[]>([]);
    const [codOn, setCodOn] = useState(false);

    // Form States
    const [merchantId, setMerchantId] = useState("");
    const [customerName, setCustomerName] = useState("");
    const [customerPhone, setCustomerPhone] = useState("");
    const [receiverName, setReceiverName] = useState("");
    const [receiverPhone, setReceiverPhone] = useState("");
    const [pickup, setPickup] = useState("");
    const [dropoff, setDropoff] = useState("");
    const [pkgType, setPkgType] = useState("Box");
    const [codAmount, setCodAmount] = useState("");
    const [riderId, setRiderId] = useState("");
    const [price, setPrice] = useState("");
    const [loading, setLoading] = useState(false);

    // Route info
    const [distanceKm, setDistanceKm] = useState(0);
    const [durationMinutes, setDurationMinutes] = useState(0);

    const iSt = { width: "100%", border: `1.5px solid ${S.border}`, borderRadius: 10, padding: "0 14px", height: 42, fontSize: 13, fontFamily: "inherit", color: S.navy, background: "#fff" };
    const lSt = { display: "block", fontSize: 11, fontWeight: 600, color: S.textMuted, marginBottom: 5, textTransform: "uppercase", letterSpacing: "0.5px" };

    useEffect(() => {
        loadVehicles();
    }, []);

    // Calculate route when addresses change
    useEffect(() => {
        const timer = setTimeout(() => {
            if (pickup && dropoff && window.google) {
                calculateRoute();
            }
        }, 1000);
        return () => clearTimeout(timer);
    }, [pickup, dropoff]);

    const loadVehicles = async () => {
        const data = await OrderService.getVehicles();
        setVehicles(data);
        if (data.length > 0) setVehicle(data[0].name);
    };

    const calculateRoute = () => {
        const directionsService = new window.google.maps.DirectionsService();
        directionsService.route(
            {
                origin: pickup,
                destination: dropoff,
                travelMode: window.google.maps.TravelMode.DRIVING,
            },
            (result: any, status: any) => {
                if (status === window.google.maps.DirectionsStatus.OK && result) {
                    const route = result.routes[0].legs[0];
                    const km = (route.distance?.value || 0) / 1000;
                    const mins = Math.ceil((route.duration?.value || 0) / 60);
                    setDistanceKm(km);
                    setDurationMinutes(mins);
                    console.log(`Route Calculated: ${km}km, ${mins}mins`);
                }
            }
        );
    };

    const handleSubmit = async () => {
        setLoading(true);

        // Determine price: Manual override > Calculated > null
        let finalPrice = price ? parseFloat(price) : null;

        if (finalPrice === null && distanceKm > 0) {
            const selectedVehicle = vehicles.find(v => v.name === vehicle);
            if (selectedVehicle) {
                finalPrice = OrderService.calculatePrice(selectedVehicle, distanceKm, durationMinutes);
            }
        }

        const payload = {
            merchantId,
            pickup,
            dropoff,
            senderName: customerName || "Dispatcher",
            senderPhone: customerPhone || "0000000000",
            receiverName: receiverName || "Receiver",
            receiverPhone: receiverPhone || "0000000000",
            vehicle,
            packageType: pkgType,
            price: finalPrice,
            cod: codOn ? parseFloat(codAmount) : 0,
            riderId: riderId || "",
            distance_km: distanceKm,
            duration_minutes: durationMinutes
        };

        const success = await OrderService.createOrder(payload);
        setLoading(false);
        if (success) {
            onClose();
            window.location.reload();
        } else {
            alert("Failed to create order");
        }
    };

    const getVehicleIcon = (name: string) => {
        if (name.toLowerCase().includes("bike")) return "🏍️";
        if (name.toLowerCase().includes("car")) return "🚗";
        if (name.toLowerCase().includes("van") || name.toLowerCase().includes("truck")) return "🚐";
        return "🚚";
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

                    <div style={{ marginBottom: 16 }}><label style={lSt}>Sender (Customer)</label><div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}><input placeholder="Name" style={iSt} value={customerName} onChange={e => setCustomerName(e.target.value)} /><input placeholder="Phone" style={iSt} value={customerPhone} onChange={e => setCustomerPhone(e.target.value)} /></div></div>

                    <div style={{ marginBottom: 16 }}>
                        <label style={lSt}>Pickup Address</label>
                        <AddressAutocompleteInput
                            placeholder="Enter pickup address..."
                            value={pickup}
                            onChange={setPickup}
                            style={iSt}
                        />
                    </div>

                    <div style={{ marginBottom: 16 }}><label style={lSt}>Receiver</label><div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}><input placeholder="Name" style={iSt} value={receiverName} onChange={e => setReceiverName(e.target.value)} /><input placeholder="Phone" style={iSt} value={receiverPhone} onChange={e => setReceiverPhone(e.target.value)} /></div></div>

                    <div style={{ marginBottom: 16 }}>
                        <label style={lSt}>Dropoff Address</label>
                        <AddressAutocompleteInput
                            placeholder="Enter delivery address..."
                            value={dropoff}
                            onChange={setDropoff}
                            style={iSt}
                        />
                    </div>

                    {/* Route Stats */}
                    {(distanceKm > 0) && (
                        <div style={{ marginBottom: 16, padding: "8px 12px", background: S.blueBg, borderRadius: 8, fontSize: 12, color: S.blue, display: "flex", gap: 12, fontWeight: 600 }}>
                            <span>📏 {distanceKm.toFixed(1)} km</span>
                            <span>⏱️ {durationMinutes} mins</span>
                        </div>
                    )}

                    <div style={{ marginBottom: 16 }}><label style={lSt}>Vehicle Type</label>
                        {vehicles.length === 0 ? (
                            <div style={{ fontSize: 13, color: S.textMuted }}>Loading vehicles...</div>
                        ) : (
                            <div style={{ display: "flex", gap: 8, overflowX: "auto", paddingBottom: 4 }}>
                                {vehicles.map(v => {
                                    const estimatedPrice = OrderService.calculatePrice(v, distanceKm, durationMinutes);
                                    const isSelected = vehicle === v.name;
                                    return (
                                        <button key={v.id} onClick={() => setVehicle(v.name)} style={{ flex: 1, minWidth: 80, padding: 10, borderRadius: 10, cursor: "pointer", fontFamily: "inherit", border: isSelected ? `2px solid ${S.gold}` : `1px solid ${S.border}`, background: isSelected ? S.goldPale : S.borderLight, textAlign: "center" }}>
                                            <div style={{ fontSize: 20 }}>{getVehicleIcon(v.name)}</div>
                                            <div style={{ fontSize: 12, fontWeight: 600, color: isSelected ? S.gold : S.text, marginTop: 2 }}>{v.name}</div>
                                            <div style={{ fontSize: 10, color: S.textMuted, fontFamily: "'Space Mono',monospace" }}>₦{estimatedPrice.toLocaleString()}</div>
                                        </button>
                                    );
                                })}
                            </div>
                        )}
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
