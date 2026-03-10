"use client";
import { useState, useMemo, useEffect, useRef } from "react";
import { S } from "../common/theme";
import { I } from "../icons";
import { useDispatcher } from "@/contexts/DispatcherContext";
import { StatCard } from "../common/StatCard";
import { VehicleAssetsAPI } from "@/lib/api";

export function VehiclesScreen() {
    const { vehicleAssets, riders } = useDispatcher();
    const vehicles = vehicleAssets || [];

    const [filter, setFilter] = useState("All");
    const [search, setSearch] = useState("");
    const [showCreateVehicle, setShowCreateVehicle] = useState(false);
    const [detailVehicleId, setDetailVehicleId] = useState<string | null>(null);

    const detailVehicle = detailVehicleId ? vehicles.find((v: any) => v.id === detailVehicleId) : null;

    const typeMap: Record<string, string> = { "Bike": "bike", "Car": "car", "Van": "van" };
    const filtered = vehicles.filter((v: any) => {
        if (filter === "Active" && !v.is_active) return false;
        if (filter === "Inactive" && v.is_active) return false;
        if (filter !== "All" && filter !== "Active" && filter !== "Inactive" && (v.vehicle_type || '').toLowerCase() !== typeMap[filter]) return false;
        if (search) {
            const s = search.toLowerCase();
            return (v.plate_number || '').toLowerCase().includes(s) || (v.asset_id || '').toLowerCase().includes(s) || (v.make || '').toLowerCase().includes(s) || (v.model || '').toLowerCase().includes(s);
        }
        return true;
    });

    const ec = (s: string) => s === "on" ? S.green : s === "idle" ? S.yellow : s === "off" ? S.red : S.textMuted;
    const gridCols = "80px 100px 60px minmax(80px, 1fr) minmax(80px, 1fr) 80px 80px 110px 110px 90px 120px 80px";

    const fmtDistance = (raw: any, unit: any) => {
        if (raw === null || raw === undefined || raw === "") return "—";
        const n = (typeof raw === "number") ? raw : parseFloat(raw);
        if (!Number.isFinite(n)) return "—";
        const u = String(unit || "").trim();
        return u ? `${n.toFixed(2)} ${u}` : n.toFixed(2);
    };

    return (
        <div style={{ animation: "fadeIn 0.2s ease-out" }}>
            <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
                <StatCard label="Total Vehicles" value={vehicles.length} />
                <StatCard label="Active" value={vehicles.filter((v: any) => v.is_active).length} color={S.green} />
                <StatCard label="Engine On" value={vehicles.filter((v: any) => v.engine_status === "on").length} color={S.green} />
                <StatCard label="With GPS" value={vehicles.filter((v: any) => v.latitude && v.longitude).length} color={S.gold} />
            </div>

            <div style={{ display: "flex", gap: 16, alignItems: "flex-start", height: "calc(100vh - 200px)" }}>
                <div style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column", height: "100%" }}>
                    <div style={{ display: "flex", gap: 10, marginBottom: 14, flexShrink: 0 }}>
                        <div style={{ display: "flex", gap: 4 }}>
                            {["All", "Active", "Inactive", "Bike", "Car", "Van"].map(f => (<button key={f} onClick={() => setFilter(f)} style={{ padding: "7px 14px", borderRadius: 8, border: `1px solid ${filter === f ? "transparent" : S.border}`, cursor: "pointer", fontFamily: "inherit", fontSize: 12, fontWeight: 600, background: filter === f ? S.goldPale : S.card, color: filter === f ? S.gold : S.textMuted }}>{f}</button>))}
                        </div>
                        <div style={{ flex: 1, background: S.card, borderRadius: 10, border: `1px solid ${S.border}`, display: "flex", alignItems: "center", gap: 8, padding: "0 12px" }}>
                            <span style={{ opacity: 0.4 }}>{I.search}</span>
                            <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search vehicles..." style={{ flex: 1, background: "transparent", border: "none", color: S.text, fontSize: 12, fontFamily: "inherit", height: 38, outline: "none" }} />
                        </div>
                        <button onClick={() => setShowCreateVehicle(true)} style={{ display: "flex", alignItems: "center", gap: 6, padding: "0 16px", borderRadius: 10, border: "none", cursor: "pointer", fontFamily: "inherit", fontWeight: 700, fontSize: 12, background: `linear-gradient(135deg,${S.gold},${S.goldLight})`, color: S.navy, whiteSpace: "nowrap", flexShrink: 0 }}>
                            {I.plus} Add Vehicle
                        </button>
                    </div>
                    <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, overflowX: "auto", overflowY: "hidden", flex: 1, display: "flex", flexDirection: "column" }}>
                        <div style={{ display: "grid", gridTemplateColumns: gridCols, padding: "10px 16px", background: S.borderLight, fontSize: 10, fontWeight: 700, color: S.textMuted, textTransform: "uppercase", letterSpacing: "0.5px", borderBottom: `1px solid ${S.border}`, flexShrink: 0 }}>
                            <span>Asset ID</span><span>Plate</span><span>Type</span><span>Make</span><span>Model</span><span>Engine</span><span>Speed</span><span>Total Dist</span><span>Dist Today</span><span>Orders Today</span><span>Rider</span><span>Status</span>
                        </div>
                        <div style={{ overflowY: "auto", flex: 1 }}>
                            {filtered.map((v: any) => (
                                <div key={v.id} onClick={() => setDetailVehicleId(v.id)} style={{ display: "grid", gridTemplateColumns: gridCols, padding: "12px 16px", borderBottom: `1px solid ${S.borderLight}`, cursor: "pointer", transition: "background 0.12s", alignItems: "center", minWidth: 1000 }} onMouseEnter={e => e.currentTarget.style.background = S.borderLight} onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                                    <span style={{ fontSize: 11, fontWeight: 700, color: S.gold, fontFamily: "'Space Mono',monospace" }}>{v.asset_id || v.id.substring(0, 8)}</span>
                                    <span style={{ fontSize: 11, fontWeight: 600 }}>{v.plate_number || v.plateNumber}</span>
                                    <span style={{ fontSize: 12 }}>{(v.vehicle_type || v.type || '').toLowerCase() === 'bike' ? '🏍️' : (v.vehicle_type || v.type || '').toLowerCase() === 'car' ? '🚗' : '🚐'}</span>
                                    <span style={{ fontSize: 11, color: S.textDim }}>{v.make || '—'}</span>
                                    <span style={{ fontSize: 11, color: S.textDim }}>{v.model || '—'}</span>
                                    <span style={{ fontSize: 10, fontWeight: 700, padding: "3px 8px", borderRadius: 6, background: `${ec(v.engine_status)}18`, color: ec(v.engine_status), justifySelf: "start" }}>{(v.engine_status || 'unknown').toUpperCase()}</span>
                                    <span style={{ fontSize: 11, fontFamily: "'Space Mono',monospace", color: S.textDim }}>{v.speed || 0} km/h</span>
                                    <span style={{ fontSize: 11, fontFamily: "'Space Mono',monospace", color: S.textDim }}>{fmtDistance(v.total_distance, v.unit_of_distance)}</span>
                                    <span style={{ fontSize: 11, fontFamily: "'Space Mono',monospace", color: S.textDim }}>{fmtDistance(v.distance_today, v.unit_of_distance)}</span>
                                    <span style={{ fontSize: 11, fontFamily: "'Space Mono',monospace", color: S.textDim }}>{(v.orders_today === null || v.orders_today === undefined) ? "—" : v.orders_today}</span>
                                    <span style={{ fontSize: 11, color: v.assigned_rider ? S.purple : S.textMuted, fontWeight: v.assigned_rider ? 600 : 400 }}>{v.assigned_rider ? (v.assigned_rider.name || v.assigned_rider) : '— None'}</span>
                                    <span style={{ fontSize: 10, fontWeight: 700, padding: "3px 8px", borderRadius: 6, background: v.is_active ? S.greenBg : S.redBg, color: v.is_active ? S.green : S.red, justifySelf: "start" }}>{v.is_active ? "Active" : "Inactive"}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                <div style={{ flex: 1, minWidth: 0, height: "100%" }}>
                    <VehiclesLocationMap vehicles={vehicles} />
                </div>
            </div>

            {showCreateVehicle && (
                <CreateVehicleModal
                    onClose={() => setShowCreateVehicle(false)}
                    onVehicleCreated={() => { setShowCreateVehicle(false); window.location.reload(); }}
                />
            )}
            {detailVehicle && (
                <VehicleDetailModal
                    vehicle={detailVehicle}
                    onClose={() => setDetailVehicleId(null)}
                    onVehicleUpdated={() => { window.location.reload(); }}
                />
            )}
        </div>
    );
}

// ─── VEHICLE DETAIL MODAL ───────────────────────────────────────
function VehicleDetailModal({ vehicle, onClose, onVehicleUpdated }: { vehicle: any, onClose: () => void, onVehicleUpdated: () => void }) {
    const [editing, setEditing] = useState(false);
    const [form, setForm] = useState({
        plate_number: vehicle.plate_number || vehicle.plateNumber || "",
        vehicle_type: vehicle.vehicle_type || vehicle.type || "bike",
        make: vehicle.make || "",
        model: vehicle.model || "",
        year: vehicle.year ? String(vehicle.year) : "",
        color: vehicle.color || "",
        vin: vehicle.vin || "",
        insurance_expiry: vehicle.insurance_expiry || "",
        registration_expiry: vehicle.registration_expiry || "",
        road_worthiness_expiry: vehicle.road_worthiness_expiry || "",
        is_active: vehicle.is_active,
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const set = (k: string, v: any) => setForm(f => ({ ...f, [k]: v }));

    const cancelEdit = () => {
        setEditing(false); setError(null);
        setForm({ plate_number: vehicle.plate_number || vehicle.plateNumber || "", vehicle_type: vehicle.vehicle_type || vehicle.type || "bike", make: vehicle.make || "", model: vehicle.model || "", year: vehicle.year ? String(vehicle.year) : "", color: vehicle.color || "", vin: vehicle.vin || "", insurance_expiry: vehicle.insurance_expiry || "", registration_expiry: vehicle.registration_expiry || "", road_worthiness_expiry: vehicle.road_worthiness_expiry || "", is_active: vehicle.is_active });
    };

    const handleSave = async () => {
        setLoading(true); setError(null);
        try {
            const payload: any = { ...form };
            if (payload.year) payload.year = parseInt(payload.year, 10); else delete payload.year;
            Object.keys(payload).forEach(k => { if (payload[k] === "" && k !== "plate_number" && k !== "vehicle_type" && k !== "is_active") delete payload[k]; });
            await VehicleAssetsAPI.update(vehicle.id, payload);
            if (onVehicleUpdated) onVehicleUpdated();
            setEditing(false);
        } catch (err: any) {
            const msg = err?.plate_number?.[0] || err?.non_field_errors?.[0] || err?.detail || "Failed to save changes.";
            setError(msg);
        } finally { setLoading(false); }
    };

    const typeIcon = (vehicle.vehicle_type || vehicle.type || "").toLowerCase() === 'bike' ? '🏍️' : (vehicle.vehicle_type || vehicle.type || "").toLowerCase() === 'car' ? '🚗' : '🚐';
    const ec = vehicle.engine_status === 'on' ? S.green : vehicle.engine_status === 'idle' ? S.yellow : vehicle.engine_status === 'off' ? S.red : S.textMuted;
    const iSt = { width: "100%", padding: "8px 10px", border: `1px solid ${S.border}`, borderRadius: 6, fontSize: 12, background: S.bg, color: S.text, fontFamily: "inherit", boxSizing: "border-box" as const };
    const lSt = { display: "block", fontSize: 11, fontWeight: 600, color: S.textMuted, marginBottom: 4 };

    const fmtDistance = (raw: any, unit: any) => {
        if (raw === null || raw === undefined || raw === "") return "—";
        const n = (typeof raw === "number") ? raw : parseFloat(raw);
        if (!Number.isFinite(n)) return "—";
        const u = String(unit || "").trim();
        return u ? `${n.toFixed(2)} ${u}` : n.toFixed(2);
    };
    const totalDistanceStr = fmtDistance(vehicle.total_distance, vehicle.unit_of_distance);
    const distanceTodayStr = fmtDistance(vehicle.distance_today, vehicle.unit_of_distance);

    return (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.55)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }} onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
            <div style={{ background: S.card, borderRadius: 16, width: 660, maxHeight: "90vh", overflowY: "auto", boxShadow: "0 20px 60px rgba(0,0,0,0.3)", display: "flex", flexDirection: "column" }}>

                {/* ── Header ── */}
                <div style={{ padding: "18px 24px", borderBottom: `1px solid ${S.border}`, display: "flex", alignItems: "center", gap: 14, flexShrink: 0 }}>
                    <div style={{ width: 46, height: 46, borderRadius: 12, background: S.goldPale, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 24 }}>{typeIcon}</div>
                    <div style={{ flex: 1 }}>
                        <div style={{ fontSize: 17, fontWeight: 800, color: S.navy }}>{vehicle.plate_number || vehicle.plateNumber}</div>
                        <div style={{ fontSize: 11, color: S.textMuted, fontFamily: "'Space Mono',monospace" }}>{vehicle.asset_id || vehicle.id.substring(0, 8)}</div>
                    </div>
                    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        {editing ? (
                            <>
                                <button onClick={cancelEdit} style={{ padding: "7px 14px", borderRadius: 8, border: `1px solid ${S.border}`, cursor: "pointer", fontFamily: "inherit", fontWeight: 600, fontSize: 12, background: S.card, color: S.textDim }}>Cancel</button>
                                <button onClick={handleSave} disabled={loading} style={{ padding: "7px 18px", borderRadius: 8, border: "none", cursor: loading ? "not-allowed" : "pointer", fontFamily: "inherit", fontWeight: 700, fontSize: 12, background: `linear-gradient(135deg,${S.gold},${S.goldLight})`, color: S.navy, opacity: loading ? 0.7 : 1 }}>{loading ? "Saving…" : "Save Changes"}</button>
                            </>
                        ) : (
                            <button onClick={() => setEditing(true)} style={{ padding: "7px 16px", borderRadius: 8, border: `1px solid ${S.border}`, cursor: "pointer", fontFamily: "inherit", fontWeight: 600, fontSize: 12, background: S.card, color: S.text, display: "flex", alignItems: "center", gap: 6 }}>✏️ Edit</button>
                        )}
                        <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", color: S.textMuted, padding: 4 }}>{I.x}</button>
                    </div>
                </div>

                {error && <div style={{ margin: "12px 24px 0", padding: "10px 14px", background: S.redBg, color: S.red, borderRadius: 8, fontSize: 12, fontWeight: 600 }}>{error}</div>}

                <div style={{ padding: "20px 24px", display: "flex", flexDirection: "column", gap: 22 }}>

                    <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
                        {editing ? (
                            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                                <label style={{ fontSize: 12, fontWeight: 600, color: S.textDim }}>Status:</label>
                                <select value={form.is_active ? "active" : "inactive"} onChange={e => set("is_active", e.target.value === "active")} style={{ ...iSt, width: "auto", padding: "6px 10px" }}>
                                    <option value="active">Active</option>
                                    <option value="inactive">Inactive</option>
                                </select>
                            </div>
                        ) : (
                            <>
                                <span style={{ fontSize: 11, fontWeight: 700, padding: "4px 12px", borderRadius: 8, background: vehicle.is_active ? S.greenBg : S.redBg, color: vehicle.is_active ? S.green : S.red }}>{vehicle.is_active ? "ACTIVE" : "INACTIVE"}</span>
                                <span style={{ fontSize: 11, fontWeight: 700, padding: "4px 12px", borderRadius: 8, background: `${ec}18`, color: ec }}>{(vehicle.engine_status || 'unknown').toUpperCase()}</span>
                            </>
                        )}
                    </div>

                    <div>
                        <div style={{ fontSize: 10, fontWeight: 700, color: S.textMuted, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 12 }}>Vehicle Info</div>
                        {editing ? (
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                                <div><label style={lSt}>Plate Number *</label><input value={form.plate_number} onChange={e => set("plate_number", e.target.value)} style={iSt} /></div>
                                <div><label style={lSt}>Type</label><select value={form.vehicle_type} onChange={e => set("vehicle_type", e.target.value)} style={iSt}><option value="bike">Bike</option><option value="car">Car</option><option value="van">Van</option></select></div>
                                <div><label style={lSt}>Make</label><input value={form.make} onChange={e => set("make", e.target.value)} style={iSt} placeholder="Honda" /></div>
                                <div><label style={lSt}>Model</label><input value={form.model} onChange={e => set("model", e.target.value)} style={iSt} placeholder="ACE 125" /></div>
                                <div><label style={lSt}>Year</label><input type="number" value={form.year} onChange={e => set("year", e.target.value)} style={iSt} placeholder="2024" /></div>
                                <div><label style={lSt}>Color</label><input value={form.color} onChange={e => set("color", e.target.value)} style={iSt} placeholder="Red" /></div>
                                <div style={{ gridColumn: "1/-1" }}><label style={lSt}>VIN</label><input value={form.vin} onChange={e => set("vin", e.target.value)} style={iSt} placeholder="Vehicle Identification Number" /></div>
                            </div>
                        ) : (
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0 24px" }}>
                                {[{ l: "Asset ID", v: vehicle.asset_id || vehicle.id.substring(0, 8) }, { l: "Plate Number", v: vehicle.plate_number || vehicle.plateNumber }, { l: "Type", v: (vehicle.vehicle_type || vehicle.type || '').toUpperCase() }, { l: "Make", v: vehicle.make || '—' }, { l: "Model", v: vehicle.model || '—' }, { l: "Year", v: vehicle.year || '—' }, { l: "Color", v: vehicle.color || '—' }, { l: "VIN", v: vehicle.vin || '—' }].map(f => (
                                    <div key={f.l} style={{ display: "flex", justifyContent: "space-between", padding: "7px 0", borderBottom: `1px solid ${S.borderLight}` }}><span style={{ fontSize: 12, color: S.textMuted }}>{f.l}</span><span style={{ fontSize: 12, fontWeight: 600 }}>{f.v}</span></div>
                                ))}
                            </div>
                        )}
                    </div>

                    <div>
                        <div style={{ fontSize: 10, fontWeight: 700, color: S.textMuted, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 12 }}>Telemetry <span style={{ fontWeight: 400, fontSize: 9 }}>(read-only)</span></div>
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 10 }}>
                            {[{ l: "Speed", v: `${vehicle.speed || 0} km/h`, c: S.text }, { l: "Heading", v: `${vehicle.course || 0}°`, c: S.text }, { l: "Engine", v: (vehicle.engine_status || 'unknown').toUpperCase(), c: ec }, { l: "GPS", v: vehicle.latitude ? '📍 Active' : 'No Data', c: vehicle.latitude ? S.green : S.textMuted }].map(s => (
                                <div key={s.l} style={{ padding: 10, background: S.borderLight, borderRadius: 8, textAlign: "center" }}><div style={{ fontSize: 13, fontWeight: 800, color: s.c, fontFamily: "'Space Mono',monospace" }}>{s.v}</div><div style={{ fontSize: 9, color: S.textMuted, marginTop: 2 }}>{s.l}</div></div>
                            ))}
                        </div>
                        <div style={{ marginTop: 8, display: 'flex', gap: 14, flexWrap: 'wrap', fontSize: 11, color: S.textMuted, fontFamily: "'Space Mono',monospace" }}>
                            <span><span style={{ fontWeight: 700, color: S.textDim }}>Total:</span> {totalDistanceStr}</span>
                            <span><span style={{ fontWeight: 700, color: S.textDim }}>Today:</span> {distanceTodayStr}</span>
                        </div>
                        {vehicle.latitude && vehicle.longitude && (
                            <div style={{ marginTop: 8, fontSize: 11, color: S.textMuted, fontFamily: "'Space Mono',monospace" }}>
                                📍 {parseFloat(vehicle.latitude).toFixed(6)}, {parseFloat(vehicle.longitude).toFixed(6)}
                            </div>
                        )}
                    </div>

                    <div>
                        <div style={{ fontSize: 10, fontWeight: 700, color: S.textMuted, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 12 }}>Documents</div>
                        {editing ? (
                            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                                <div><label style={lSt}>Insurance Expiry</label><input type="date" value={form.insurance_expiry} onChange={e => set("insurance_expiry", e.target.value)} style={iSt} /></div>
                                <div><label style={lSt}>Registration Expiry</label><input type="date" value={form.registration_expiry} onChange={e => set("registration_expiry", e.target.value)} style={iSt} /></div>
                                <div><label style={lSt}>Road Worthiness Expiry</label><input type="date" value={form.road_worthiness_expiry} onChange={e => set("road_worthiness_expiry", e.target.value)} style={iSt} /></div>
                            </div>
                        ) : (
                            <div>
                                {[{ l: "Insurance Expiry", v: vehicle.insurance_expiry || '—' }, { l: "Registration Expiry", v: vehicle.registration_expiry || '—' }, { l: "Road Worthiness Expiry", v: vehicle.road_worthiness_expiry || '—' }].map(f => (
                                    <div key={f.l} style={{ display: "flex", justifyContent: "space-between", padding: "7px 0", borderBottom: `1px solid ${S.borderLight}` }}><span style={{ fontSize: 12, color: S.textMuted }}>{f.l}</span><span style={{ fontSize: 12, fontWeight: 600 }}>{f.v}</span></div>
                                ))}
                            </div>
                        )}
                    </div>

                    <div>
                        <div style={{ fontSize: 10, fontWeight: 700, color: S.textMuted, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 12 }}>Assigned Rider</div>
                        {vehicle.assigned_rider || vehicle.assignedRider ? (
                            <div style={{ display: "flex", alignItems: "center", gap: 12, padding: 12, background: S.borderLight, borderRadius: 10 }}>
                                <div style={{ width: 40, height: 40, borderRadius: 10, background: S.goldPale, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, fontWeight: 800, color: S.gold }}>{(vehicle.assigned_rider?.name || vehicle.assignedRider || "R").split(" ").map((n: string) => n[0]).join("")}</div>
                                <div><div style={{ fontSize: 14, fontWeight: 700 }}>{vehicle.assigned_rider?.name || vehicle.assignedRider}</div>
                                    {vehicle.assigned_rider?.rider_id && <div style={{ fontSize: 11, color: S.textDim, fontFamily: "'Space Mono',monospace" }}>{vehicle.assigned_rider.rider_id} • {vehicle.assigned_rider.phone}</div>}</div>
                            </div>
                        ) : (
                            <div style={{ color: S.textMuted, fontSize: 12, padding: "6px 0" }}>No rider assigned to this vehicle</div>
                        )}
                    </div>

                </div>
            </div>
        </div>
    );
}

// ─── CREATE VEHICLE MODAL ───────────────────────────────────────
function CreateVehicleModal({ onClose, onVehicleCreated }: { onClose: () => void, onVehicleCreated: () => void }) {
    const [form, setForm] = useState({ plate_number: "", vehicle_type: "bike", make: "", model: "", year: "", color: "", vin: "" });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const set = (k: string, v: any) => setForm(f => ({ ...f, [k]: v }));

    const handleSubmit = async (e: any) => {
        e.preventDefault();
        setLoading(true); setError(null);
        try {
            const payload: any = { ...form };
            if (payload.year) payload.year = parseInt(payload.year, 10);
            else delete payload.year;
            Object.keys(payload).forEach(k => { if (!payload[k]) delete payload[k]; });
            payload.plate_number = form.plate_number; // always required
            payload.vehicle_type = form.vehicle_type;
            await VehicleAssetsAPI.create(payload);
            onVehicleCreated();
            onClose();
        } catch (err: any) {
            const msg = err?.plate_number?.[0] || err?.non_field_errors?.[0] || err?.detail || "Failed to create vehicle.";
            setError(msg);
        } finally { setLoading(false); }
    };

    const iSt = { width: "100%", padding: "10px 12px", border: `1px solid ${S.border}`, borderRadius: 8, fontSize: 13, background: S.bg, color: S.text, fontFamily: "inherit", boxSizing: "border-box" as const };
    const lSt = { display: "block", fontSize: 12, fontWeight: 600, color: S.textDim, marginBottom: 5 };
    const row = { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, marginBottom: 14 };

    return (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.55)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }} onClick={e => { if (e.target === e.currentTarget) onClose(); }}>
            <div style={{ background: S.card, borderRadius: 16, padding: 28, width: 480, maxHeight: "90vh", overflowY: "auto", boxShadow: "0 20px 60px rgba(0,0,0,0.3)" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 22 }}>
                    <div><div style={{ fontSize: 17, fontWeight: 800, color: S.navy }}>Add New Vehicle</div><div style={{ fontSize: 12, color: S.textMuted, marginTop: 2 }}>Register a new vehicle asset</div></div>
                    <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", color: S.textMuted }}>{I.x}</button>
                </div>
                {error && <div style={{ padding: "10px 14px", background: S.redBg, color: S.red, borderRadius: 8, fontSize: 12, fontWeight: 600, marginBottom: 14 }}>{error}</div>}
                <form onSubmit={handleSubmit}>
                    <div style={row}>
                        <div><label style={lSt}>Plate Number *</label><input required value={form.plate_number} onChange={e => set("plate_number", e.target.value)} style={iSt} placeholder="LAG-123-AB" /></div>
                        <div><label style={lSt}>Type *</label><select value={form.vehicle_type} onChange={e => set("vehicle_type", e.target.value)} style={iSt}><option value="bike">Bike</option><option value="car">Car</option><option value="van">Van</option></select></div>
                    </div>
                    <div style={row}>
                        <div><label style={lSt}>Make</label><input value={form.make} onChange={e => set("make", e.target.value)} style={iSt} placeholder="Honda" /></div>
                        <div><label style={lSt}>Model</label><input value={form.model} onChange={e => set("model", e.target.value)} style={iSt} placeholder="ACE 125" /></div>
                    </div>
                    <div style={row}>
                        <div><label style={lSt}>Year</label><input value={form.year} onChange={e => set("year", e.target.value)} style={iSt} placeholder="2024" type="number" /></div>
                        <div><label style={lSt}>Color</label><input value={form.color} onChange={e => set("color", e.target.value)} style={iSt} placeholder="Red" /></div>
                    </div>
                    <div style={{ marginBottom: 14 }}><label style={lSt}>VIN (Optional)</label><input value={form.vin} onChange={e => set("vin", e.target.value)} style={iSt} placeholder="Vehicle Identification Number" /></div>
                    <button type="submit" disabled={loading} style={{ width: "100%", padding: "12px 0", borderRadius: 10, border: "none", cursor: loading ? "not-allowed" : "pointer", fontFamily: "inherit", fontWeight: 800, fontSize: 14, background: `linear-gradient(135deg,${S.gold},${S.goldLight})`, color: S.navy, opacity: loading ? 0.7 : 1 }}>{loading ? "Creating…" : "Create Vehicle"}</button>
                </form>
            </div>
        </div>
    );
}

// ─── VEHICLES LOCATION MAP ──────────────────────────────────────
function VehiclesLocationMap({ vehicles }: { vehicles: any[] }) {
    const mapRef = useRef<HTMLDivElement>(null);
    const mapInstanceRef = useRef<any>(null);
    const markersByIdRef = useRef<Record<string, any>>({});
    const overlaysByIdRef = useRef<Record<string, any>>({});
    const latestVehiclesByIdRef = useRef<Record<string, any>>({});
    const vehiclesRef = useRef<any[]>([]);
    const infoWindowRef = useRef<any>(null);
    const [mapReady, setMapReady] = useState(false);

    // Camera control
    const didInitialFitRef = useRef(false);
    const userInteractedRef = useRef(false);
    const programmaticMoveRef = useRef(false);

    const safeVehicleKey = (v: any) => {
        // Prefer stable backend id; fall back to other identifiers.
        return (v && (v.id ?? v.asset_id ?? v.plate_number)) ?? null;
    };

    const parseVehicleLatLng = (v: any) => {
        if (!v || v.latitude == null || v.longitude == null) return null;
        const lat = parseFloat(v.latitude);
        const lng = parseFloat(v.longitude);
        if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;
        if (Math.abs(lat) > 90 || Math.abs(lng) > 180) return null;
        // Treat (0,0) as bad telemetry for this app (prevents world-zoom).
        if (Math.abs(lat) < 1e-9 && Math.abs(lng) < 1e-9) return null;
        return { lat, lng };
    };

    const fmtDistance = (raw: any, unit: any) => {
        if (raw === null || raw === undefined || raw === "") return "—";
        const n = (typeof raw === "number") ? raw : parseFloat(raw);
        if (!Number.isFinite(n)) return "—";
        const u = String(unit || "").trim();
        return u ? `${n.toFixed(2)} ${u}` : n.toFixed(2);
    };

    const median = (arr: number[]) => {
        if (!arr || arr.length === 0) return null;
        const s = [...arr].sort((a, b) => a - b);
        const mid = Math.floor(s.length / 2);
        return (s.length % 2 === 1) ? s[mid] : (s[mid - 1] + s[mid]) / 2;
    };

    // Haversine distance in km.
    const haversineKm = (a: any, b: any) => {
        const R = 6371;
        const toRad = (d: number) => (d * Math.PI) / 180;
        const dLat = toRad(b.lat - a.lat);
        const dLng = toRad(b.lng - a.lng);
        const lat1 = toRad(a.lat);
        const lat2 = toRad(b.lat);
        const sin1 = Math.sin(dLat / 2);
        const sin2 = Math.sin(dLng / 2);
        const h = sin1 * sin1 + Math.cos(lat1) * Math.cos(lat2) * sin2 * sin2;
        return 2 * R * Math.asin(Math.min(1, Math.sqrt(h)));
    };

    const computeClusterInliers = (points: any[], { keepPercentile = 0.9, madFactor = 6 } = {}) => {
        if (!Array.isArray(points) || points.length <= 2) return points || [];

        const medLat = median(points.map(p => p.lat));
        const medLng = median(points.map(p => p.lng));
        if (medLat == null || medLng == null) return points;
        const center = { lat: medLat, lng: medLng };

        const withD = points.map(p => ({ p, d: haversineKm(center, p) }));
        const dists = withD.map(x => x.d);
        const medD = median(dists);
        if (medD == null) return points;
        const absDev = dists.map(d => Math.abs(d - medD));
        const mad = median(absDev) ?? 0;

        const sorted = [...withD].sort((a, b) => a.d - b.d);
        const pctIdx = Math.max(0, Math.min(sorted.length - 1, Math.floor(keepPercentile * (sorted.length - 1))));
        const pctCutoff = sorted[pctIdx]?.d ?? sorted[sorted.length - 1]?.d ?? 0;

        const madCutoff = (mad > 0) ? (medD + madFactor * mad) : pctCutoff;
        let cutoff = Math.min(pctCutoff, madCutoff);
        if (!Number.isFinite(cutoff) || cutoff <= 0) cutoff = pctCutoff;

        let inliers = withD.filter(x => x.d <= cutoff).map(x => x.p);
        if (inliers.length < Math.min(3, points.length)) inliers = points;
        return inliers;
    };

    const fitMapToVehicles = (vehiclesList: any[]) => {
        const map = mapInstanceRef.current;
        if (!map || !(window as any).google || !(window as any).google.maps) return false;

        const pts = (vehiclesList || [])
            .map(v => parseVehicleLatLng(v))
            .filter(Boolean);

        if (pts.length === 0) return false;

        const inliers = computeClusterInliers(pts, { keepPercentile: 0.9, madFactor: 6 });

        programmaticMoveRef.current = true;

        if (inliers.length === 1) {
            map.setCenter(inliers[0]);
            map.setZoom(15);
        } else {
            const bounds = new (window as any).google.maps.LatLngBounds();
            inliers.forEach(p => bounds.extend(p));
            map.fitBounds(bounds, { padding: 60 });
            const z = map.getZoom?.();
            if (typeof z === 'number' && z > 16) map.setZoom(16);
        }

        didInitialFitRef.current = true;
        return true;
    };

    useEffect(() => {
        const init = () => {
            if (!mapRef.current || mapInstanceRef.current) return;
            if (!(window as any).google || !(window as any).google.maps) return;
            const map = new (window as any).google.maps.Map(mapRef.current, {
                center: { lat: 6.5244, lng: 3.3792 }, zoom: 11,
                mapTypeControl: false, streetViewControl: false, fullscreenControl: true, zoomControl: true,
                styles: [{ featureType: "poi", elementType: "labels", stylers: [{ visibility: "off" }] }]
            });
            mapInstanceRef.current = map;
            infoWindowRef.current = new (window as any).google.maps.InfoWindow();

            map.addListener('dragstart', () => { userInteractedRef.current = true; });
            map.addListener('zoom_changed', () => {
                if (!programmaticMoveRef.current) userInteractedRef.current = true;
            });
            map.addListener('idle', () => {
                if (programmaticMoveRef.current) programmaticMoveRef.current = false;
            });

            setMapReady(true);
        };
        let unsub: any = null;
        if ((window as any).google && (window as any).google.maps) { init(); }
        else { window.addEventListener('google-maps-loaded', init); unsub = () => window.removeEventListener('google-maps-loaded', init); }
        return () => {
            if (unsub) unsub();
            Object.values(markersByIdRef.current).forEach((m: any) => {
                try {
                    if (m?._labelOverlay) m._labelOverlay.setMap(null);
                    m?.setMap?.(null);
                } catch { }
            });
            markersByIdRef.current = {};
            overlaysByIdRef.current = {};
            if (infoWindowRef.current) { infoWindowRef.current.close(); infoWindowRef.current = null; }
            mapInstanceRef.current = null;
        };
    }, []);

    useEffect(() => {
        if (!mapReady || !mapInstanceRef.current || !(window as any).google) return;
        const map = mapInstanceRef.current;
        vehiclesRef.current = vehicles || [];

        const buildVehicleIcon = (emoji: string, rotation: number, borderColor: string) => {
            const size = 40;
            const canvas = document.createElement('canvas');
            canvas.width = size; canvas.height = size;
            const ctx = canvas.getContext('2d');
            if (!ctx) return null;
            ctx.translate(size / 2, size / 2);
            ctx.rotate((Math.PI / 180) * (rotation || 0));
            ctx.beginPath();
            ctx.arc(0, 0, size / 2 - 2, 0, 2 * Math.PI);
            ctx.fillStyle = 'rgba(255,255,255,0.85)';
            ctx.fill();
            ctx.lineWidth = 3;
            ctx.strokeStyle = borderColor;
            ctx.stroke();
            ctx.font = '20px serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = '#000';
            ctx.fillText(emoji, 0, 1);
            return { url: canvas.toDataURL(), scaledSize: new (window as any).google.maps.Size(size, size), anchor: new (window as any).google.maps.Point(size / 2, size / 2) };
        };

        const LabelOverlayCtor = class extends (window as any).google.maps.OverlayView {
            latLng: any;
            div: any;
            constructor(latLng: any, div: any) {
                super();
                this.latLng = latLng;
                this.div = div;
            }
            onAdd() {
                (this.getPanes().floatPane || this.getPanes().overlayLayer).appendChild(this.div);
            }
            draw() {
                const proj = this.getProjection();
                if (!proj || !this.latLng) return;
                const pos = proj.fromLatLngToDivPixel(this.latLng);
                if (!pos) return;
                this.div.style.left = (pos.x - this.div.offsetWidth / 2) + 'px';
                this.div.style.top = (pos.y - 32) + 'px';
            }
            onRemove() {
                if (this.div?.parentNode) this.div.parentNode.removeChild(this.div);
            }
            setPosition(latLng: any) {
                this.latLng = latLng;
                this.draw();
            }
        };

        const nextKeys = new Set();

        (vehicles || []).forEach(v => {
            const key = safeVehicleKey(v);
            if (!key) return;
            const ll = parseVehicleLatLng(v);
            if (!ll) return;
            nextKeys.add(String(key));
            latestVehiclesByIdRef.current[String(key)] = v;

            const color = v.engine_status === 'on' ? '#22c55e' : v.engine_status === 'idle' ? '#F59E0B' : v.engine_status === 'off' ? '#EF4444' : '#6b7280';
            const typeIcon = (v.vehicle_type || '').toLowerCase() === 'bike' ? '🏍️' : (v.vehicle_type || '').toLowerCase() === 'car' ? '🚗' : '🚐';
            const rotation = parseFloat(v.course) || 0;

            const riderName = v.assigned_rider ? v.assigned_rider.name : '';
            const speedStr = v.speed > 0 ? `${v.speed} km/h` : '';
            const labelParts = [v.plate_number, riderName, speedStr].filter(Boolean);

            let marker = markersByIdRef.current[String(key)];
            if (!marker) {
                marker = new (window as any).google.maps.Marker({
                    position: ll,
                    map,
                    title: v.plate_number,
                    icon: buildVehicleIcon(typeIcon, rotation, color),
                    zIndex: v.engine_status === 'on' ? 10 : 5,
                });
                markersByIdRef.current[String(key)] = marker;

                marker.addListener('click', () => {
                    const latest = latestVehiclesByIdRef.current[String(key)] || v;
                    const latestColor = latest.engine_status === 'on' ? '#22c55e' : latest.engine_status === 'idle' ? '#F59E0B' : latest.engine_status === 'off' ? '#EF4444' : '#6b7280';
                    const latestStatus = latest.engine_status === 'on' ? 'Engine On' : latest.engine_status === 'idle' ? 'Idle' : latest.engine_status === 'off' ? 'Engine Off' : 'Unknown';
                    const latestIcon = (latest.vehicle_type || '').toLowerCase() === 'bike' ? '🏍️' : (latest.vehicle_type || '').toLowerCase() === 'car' ? '🚗' : '🚐';
                    const totalDistanceStr = fmtDistance(latest.total_distance, latest.unit_of_distance);
                    const distanceTodayStr = fmtDistance(latest.distance_today, latest.unit_of_distance);
                    infoWindowRef.current.setContent(
                        `<div style="font-family:sans-serif;padding:6px 2px;min-width:160px;">` +
                        `<div style="font-weight:700;font-size:13px;margin-bottom:4px;">${latestIcon} ${latest.plate_number}</div>` +
                        `<div style="color:${latestColor};font-weight:600;font-size:11px;">${latestStatus}</div>` +
                        `<div style="color:#555;font-size:11px;margin-top:4px;">${latest.asset_id} • ${(latest.vehicle_type || '').toUpperCase()}</div>` +
                        (latest.make || latest.model ? `<div style="color:#888;font-size:10px;">${latest.make || ''} ${latest.model || ''}</div>` : '') +
                        (latest.speed > 0 ? `<div style="color:#555;font-size:10px;margin-top:3px;">🏎️ ${latest.speed} km/h</div>` : '') +
                        `<div style="color:#555;font-size:10px;margin-top:6px;display:flex;gap:10px;flex-wrap:wrap;">` +
                        `<span><span style="color:#888;font-weight:700;">Total:</span> ${totalDistanceStr}</span>` +
                        `<span><span style="color:#888;font-weight:700;">Today:</span> ${distanceTodayStr}</span>` +
                        `</div>` +
                        (latest.assigned_rider ? `<div style="color:#a855f7;font-size:10px;margin-top:3px;">👤 ${latest.assigned_rider.name}</div>` : '<div style="color:#aaa;font-size:10px;margin-top:3px;">Unassigned</div>') +
                        `</div>`
                    );
                    infoWindowRef.current.open(map, marker);
                });

                const labelDiv = document.createElement('div');
                labelDiv.style.cssText = 'position:absolute;pointer-events:none;user-select:none;white-space:nowrap;' +
                    'background:rgba(255,255,255,0.92);border:1px solid rgba(15,23,42,0.12);border-radius:999px;' +
                    'padding:3px 8px;box-shadow:0 2px 6px rgba(0,0,0,0.16);backdrop-filter:blur(2px);' +
                    'font-family:sans-serif;font-size:10px;font-weight:700;color:#1B2A4A;line-height:1.2;letter-spacing:0.1px;max-width:220px;overflow:hidden;text-overflow:ellipsis;';
                labelDiv.textContent = labelParts.join(' · ');
                const overlay = new LabelOverlayCtor(new (window as any).google.maps.LatLng(ll.lat, ll.lng), labelDiv);
                overlay.setMap(map);
                overlaysByIdRef.current[String(key)] = overlay;
                marker._labelOverlay = overlay;
            } else {
                marker.setPosition(ll);
                marker.setIcon(buildVehicleIcon(typeIcon, rotation, color));
                marker.setZIndex(v.engine_status === 'on' ? 10 : 5);

                const overlay = overlaysByIdRef.current[String(key)];
                if (overlay) overlay.setPosition(new (window as any).google.maps.LatLng(ll.lat, ll.lng));
                const div = overlay?.div;
                if (div) {
                    const nextText = labelParts.join(' · ');
                    if (div.textContent !== nextText) div.textContent = nextText;
                    overlay?.draw?.();
                }
            }
        });

        Object.keys(markersByIdRef.current).forEach(k => {
            if (nextKeys.has(k)) return;
            const m = markersByIdRef.current[k];
            try {
                if (m?._labelOverlay) m._labelOverlay.setMap(null);
                m?.setMap?.(null);
            } catch { }
            delete markersByIdRef.current[k];
            delete overlaysByIdRef.current[k];
            delete latestVehiclesByIdRef.current[k];
        });

        if (!didInitialFitRef.current && !userInteractedRef.current) {
            fitMapToVehicles(vehicles);
        }

    }, [mapReady, vehicles]);

    const withLocation = (vehicles || []).map(v => parseVehicleLatLng(v)).filter(Boolean).length;

    return (
        <div style={{ position: 'relative', height: '100%', borderRadius: 14, overflow: 'hidden', border: `1px solid ${S.border}`, background: S.card, display: 'flex', flexDirection: 'column' }}>
            <div style={{ padding: '10px 14px', borderBottom: `1px solid ${S.border}`, fontSize: 12, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span>🗺️ Vehicle Locations</span>
                    <button
                        type="button"
                        onClick={() => fitMapToVehicles(vehiclesRef.current)}
                        disabled={!mapReady || withLocation === 0}
                        title="Recenter to the main cluster (ignores outliers like 0,0)"
                        style={{
                            padding: '5px 9px',
                            borderRadius: 10,
                            border: `1px solid ${S.border}`,
                            background: S.borderLight,
                            color: S.navy,
                            fontSize: 10,
                            fontWeight: 800,
                            cursor: (!mapReady || withLocation === 0) ? 'not-allowed' : 'pointer',
                            opacity: (!mapReady || withLocation === 0) ? 0.6 : 1,
                        }}
                    >
                        Recenter / Fit
                    </button>
                </div>
                <span style={{ fontSize: 10, color: S.textMuted, fontWeight: 400 }}>{withLocation} of {(vehicles || []).length} vehicles with GPS</span>
            </div>
            <div style={{ flex: 1, position: 'relative' }}>
                <div ref={mapRef} style={{ height: '100%', width: '100%' }} />
                {withLocation === 0 && mapReady && (
                    <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(0,0,0,0.03)' }}>
                        <div style={{ textAlign: 'center', color: S.textMuted }}>
                            <div style={{ fontSize: 32, marginBottom: 8 }}>📍</div>
                            <div style={{ fontSize: 12, fontWeight: 600 }}>No GPS data available</div>
                            <div style={{ fontSize: 11, marginTop: 4 }}>Vehicles will appear here when telemetry is received</div>
                        </div>
                    </div>
                )}
            </div>
            <div style={{ padding: '6px 12px', borderTop: `1px solid ${S.border}`, fontSize: 10, color: S.textMuted, display: 'flex', gap: 12, flexShrink: 0 }}>
                <span>🏍️ Bike  🚗 Car  🚐 Van</span>
                <span style={{ marginLeft: 4 }}>|</span>
                <span><span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: '#22c55e', marginRight: 3, verticalAlign: 'middle' }} /> Engine On</span>
                <span><span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: '#F59E0B', marginRight: 3, verticalAlign: 'middle' }} /> Idle</span>
                <span><span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: '#EF4444', marginRight: 3, verticalAlign: 'middle' }} /> Engine Off</span>
                <span><span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: '#6b7280', marginRight: 3, verticalAlign: 'middle' }} /> Unknown</span>
                <span style={{ marginLeft: 'auto', fontStyle: 'italic' }}>Click a marker for details</span>
            </div>
        </div>
    );
}
