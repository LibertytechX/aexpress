import { useState, useEffect } from "react";
import { S } from "../common/theme";
import { LagosMap } from "../map/LagosMap";
import { VehicleService, type Vehicle } from "../../services/vehicleService";
import { SettingsService } from "../../services/settingsService";

export function SettingsScreen() {
    // ─── PRICING STATE ───
    const [vehicles, setVehicles] = useState<Vehicle[]>([]);
    const [loading, setLoading] = useState(true);

    // Global Settings State
    const [codFee, setCodFee] = useState(500);
    const [codPct, setCodPct] = useState(1.5);
    const [bridgeSurcharge, setBridgeSurcharge] = useState(500);
    const [outerZoneSurcharge, setOuterZoneSurcharge] = useState(800);
    const [islandPremium, setIslandPremium] = useState(300);
    const [weightThreshold, setWeightThreshold] = useState(5);
    const [weightSurcharge, setWeightSurcharge] = useState(200);
    const [weightUnit, setWeightUnit] = useState(5);
    const [surgeEnabled, setSurgeEnabled] = useState(true);
    const [surgeMultiplier, setSurgeMultiplier] = useState(1.5);
    const [surgeMorningStart, setSurgeMorningStart] = useState("07:00");
    const [surgeMorningEnd, setSurgeMorningEnd] = useState("09:30");
    const [surgeEveningStart, setSurgeEveningStart] = useState("17:00");
    const [surgeEveningEnd, setSurgeEveningEnd] = useState("20:00");
    const [rainSurge, setRainSurge] = useState(true);
    const [rainMultiplier, setRainMultiplier] = useState(1.3);
    const [tierEnabled, setTierEnabled] = useState(true);
    const [tier1Km, setTier1Km] = useState(15);
    const [tier1Discount, setTier1Discount] = useState(10);
    const [tier2Km, setTier2Km] = useState(25);
    const [tier2Discount, setTier2Discount] = useState(15);
    const [autoAssign, setAutoAssign] = useState(true);
    const [assignRadius, setAssignRadius] = useState(5);
    const [acceptTimeout, setAcceptTimeout] = useState(120);
    const [maxBike, setMaxBike] = useState(2);
    const [maxCar, setMaxCar] = useState(1);
    const [maxVan, setMaxVan] = useState(1);
    const [notifNew, setNotifNew] = useState(true);
    const [notifUnassigned, setNotifUnassigned] = useState(true);
    const [notifComplete, setNotifComplete] = useState(true);
    const [notifCod, setNotifCod] = useState(true);

    const [settingsTab, setSettingsTab] = useState("pricing");
    const [saved, setSaved] = useState(false);

    // Calculator State
    const [simKm, setSimKm] = useState(8);
    const [simVehicleId, setSimVehicleId] = useState<number | null>(null);
    const [simZone, setSimZone] = useState("same");
    const [simWeight, setSimWeight] = useState(3);
    const [simSurge, setSimSurge] = useState(false);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        const [vData, sData] = await Promise.all([
            VehicleService.getVehicles(),
            SettingsService.getSettings()
        ]);

        if (vData) {
            setVehicles(vData);
            if (vData.length > 0) setSimVehicleId(vData[0].id);
        }
        setLoading(false);

        if (sData) {
            setBridgeSurcharge(Number(sData.bridge_surcharge));
            setOuterZoneSurcharge(Number(sData.outer_zone_surcharge));
            setIslandPremium(Number(sData.island_premium));
            setWeightThreshold(sData.weight_threshold_kg);
            setWeightSurcharge(Number(sData.weight_surcharge_per_unit));
            setWeightUnit(sData.weight_unit_kg);
            setSurgeEnabled(sData.surge_enabled);
            setSurgeMultiplier(Number(sData.surge_multiplier));
            setSurgeMorningStart(sData.surge_morning_start?.slice(0, 5) || "07:00");
            setSurgeMorningEnd(sData.surge_morning_end?.slice(0, 5) || "09:30");
            setSurgeEveningStart(sData.surge_evening_start?.slice(0, 5) || "17:00");
            setSurgeEveningEnd(sData.surge_evening_end?.slice(0, 5) || "20:00");
            setRainSurge(sData.rain_surge_enabled);
            setRainMultiplier(Number(sData.rain_surge_multiplier));
            setTierEnabled(sData.tier_enabled);
            setTier1Km(sData.tier1_km);
            setTier1Discount(sData.tier1_discount_pct);
            setTier2Km(sData.tier2_km);
            setTier2Discount(sData.tier2_discount_pct);
            setAutoAssign(sData.auto_assign_enabled);
            setAssignRadius(sData.auto_assign_radius_km);
            setAcceptTimeout(sData.accept_timeout_sec);
            setMaxBike(sData.max_concurrent_bike);
            setMaxCar(sData.max_concurrent_car);
            setMaxVan(sData.max_concurrent_van);
            setCodFee(Number(sData.cod_flat_fee));
            setCodPct(Number(sData.cod_pct_fee));
            setNotifNew(sData.notif_new_order);
            setNotifUnassigned(sData.notif_unassigned);
            setNotifComplete(sData.notif_completed);
            setNotifCod(sData.notif_cod_settled);
        }
    };

    const updateLocalVehicle = (id: number, field: keyof Vehicle, value: string) => {
        setVehicles(prev => prev.map(v => v.id === id ? { ...v, [field]: value } : v));
    };

    const getEstDuration = (km: number, vehicleName: string): number => {
        // Estimate duration based on vehicle type average speeds in Lagos
        // Bike: ~30km/h, Car: ~25km/h (traffic), Van: ~20km/h
        const name = vehicleName.toLowerCase();
        let speed = 30;
        if (name.includes('bike') || name.includes('motorcycle')) speed = 35;
        else if (name.includes('car')) speed = 25;
        else if (name.includes('van') || name.includes('truck')) speed = 20;

        // Time = Distance / Speed * 60 min
        return Math.ceil((km / speed) * 60);
    };

    const calcPrice = (vehicle: Vehicle, km: number, zone: string, weight: number) => {
        const base = parseFloat(vehicle.base_fare);
        const perKm = parseFloat(vehicle.rate_per_km);
        const perMin = parseFloat(vehicle.rate_per_minute);
        const minKm = parseFloat(vehicle.min_distance_km);
        const minFee = parseFloat(vehicle.min_fee);

        const duration = getEstDuration(km, vehicle.name);

        // Backend Logic:
        // distance_cost = distance * rate_per_km
        // time_cost = duration * rate_per_minute
        // total = base + distance_cost + time_cost

        let price = base + (km * perKm) + (duration * perMin);

        // Apply min fee logic
        if (km <= minKm) {
            price = Math.max(price, minFee);
        }

        // Ensure total is at least min_fee
        price = Math.max(price, minFee);

        // Frontend-specific discounts/surcharges (applied on top of base calculation)
        if (tierEnabled && km >= tier2Km) price = price * (1 - tier2Discount / 100);
        else if (tierEnabled && km >= tier1Km) price = price * (1 - tier1Discount / 100);

        if (zone === "bridge") price += bridgeSurcharge;
        if (zone === "outer") price += outerZoneSurcharge;
        if (zone === "island") price += islandPremium;
        if (weight > weightThreshold) price += Math.ceil((weight - weightThreshold) / weightUnit) * weightSurcharge;

        return { price: Math.round(price), duration };
    };

    const selectedVehicle = vehicles.find(v => v.id === simVehicleId) || vehicles[0];
    const { price: simPrice, duration: simDuration } = selectedVehicle
        ? calcPrice(selectedVehicle, simKm, simZone, simWeight)
        : { price: 0, duration: 0 };

    const simFinal = simSurge ? Math.round(simPrice * surgeMultiplier) : simPrice;

    const handleSave = async () => {
        // Update vehicles in backend
        // Update vehicles in backend
        const vehiclePromises = vehicles.map(v => {
            return VehicleService.updateVehicle(v.id, {
                base_fare: v.base_fare,
                rate_per_km: v.rate_per_km,
                rate_per_minute: v.rate_per_minute,
                min_distance_km: v.min_distance_km,
                min_fee: v.min_fee
            });
        });

        // Update Global Settings
        const settingsPromise = SettingsService.updateSettings({
            bridge_surcharge: bridgeSurcharge,
            outer_zone_surcharge: outerZoneSurcharge,
            island_premium: islandPremium,
            weight_threshold_kg: weightThreshold,
            weight_surcharge_per_unit: weightSurcharge,
            weight_unit_kg: weightUnit,
            surge_enabled: surgeEnabled,
            surge_multiplier: surgeMultiplier,
            surge_morning_start: surgeMorningStart,
            surge_morning_end: surgeMorningEnd,
            surge_evening_start: surgeEveningStart,
            surge_evening_end: surgeEveningEnd,
            rain_surge_enabled: rainSurge,
            rain_surge_multiplier: rainMultiplier,
            tier_enabled: tierEnabled,
            tier1_km: tier1Km,
            tier1_discount_pct: tier1Discount,
            tier2_km: tier2Km,
            tier2_discount_pct: tier2Discount,
            auto_assign_enabled: autoAssign,
            auto_assign_radius_km: assignRadius,
            accept_timeout_sec: acceptTimeout,
            max_concurrent_bike: maxBike,
            max_concurrent_car: maxCar,
            max_concurrent_van: maxVan,
            cod_flat_fee: codFee,
            cod_pct_fee: codPct,
            notif_new_order: notifNew,
            notif_unassigned: notifUnassigned,
            notif_completed: notifComplete,
            notif_cod_settled: notifCod
        });

        await Promise.all([...vehiclePromises, settingsPromise]);

        setSaved(true);
        setTimeout(() => setSaved(false), 2500);
    };
    const handleReset = async () => {
        // Re-fetch original data to reset changes
        setLoading(true);
        await fetchData();
        setCodFee(500); setCodPct(1.5); setBridgeSurcharge(500); setOuterZoneSurcharge(800); setIslandPremium(300);
    };

    const inputStyle = { width: "100%", border: `1.5px solid ${S.border}`, borderRadius: 10, padding: "0 12px", height: 40, fontSize: 14, fontFamily: "'Space Mono',monospace", fontWeight: 700, color: S.navy, outline: "none" };
    const labelStyle = { display: "block", fontSize: 11, fontWeight: 600, color: S.textMuted, marginBottom: 4, textTransform: "uppercase" as const, letterSpacing: "0.3px" };

    const Toggle = ({ on, setOn, size }: { on: boolean, setOn: (v: boolean) => void, size?: string }) => {
        const w = size === "sm" ? 36 : 44;
        const d = size === "sm" ? 16 : 20;
        return (
            <div onClick={() => setOn(!on)} style={{ width: w, height: Math.round(w / 1.83), borderRadius: w / 2, cursor: "pointer", background: on ? S.green : S.border, position: "relative", transition: "background 0.2s", flexShrink: 0 }}>
                <div style={{ width: d, height: d, borderRadius: "50%", background: "#fff", position: "absolute", top: Math.round((w / 1.83 - d) / 2), left: on ? w - d - Math.round((w / 1.83 - d) / 2) : Math.round((w / 1.83 - d) / 2), transition: "left 0.2s", boxShadow: "0 1px 3px rgba(0,0,0,0.2)" }} />
            </div>
        )
    };

    const SC = ({ children, title, icon, desc, right }: any) => (
        <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, marginBottom: 14, overflow: "hidden" }}>
            <div style={{ padding: "14px 20px", borderBottom: `1px solid ${S.border}`, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <span style={{ fontSize: 20 }}>{icon}</span>
                    <div>
                        <div style={{ fontSize: 15, fontWeight: 700, color: S.navy }}>{title}</div>
                        {desc && <div style={{ fontSize: 11, color: S.textMuted }}>{desc}</div>}
                    </div>
                </div>
                {right}
            </div>
            <div style={{ padding: 20 }}>{children}</div>
        </div>
    );

    const tabs = [
        { id: "pricing", label: "Pricing & Fees", icon: "💰" },
        { id: "zones", label: "Zones & Surcharges", icon: "🗺️" },
        { id: "simulator", label: "Price Calculator", icon: "🧮" },
        { id: "dispatch", label: "Dispatch Rules", icon: "⚙️" },
        { id: "notifications", label: "Notifications", icon: "🔔" },
        { id: "integrations", label: "API & Integrations", icon: "🔌" }
    ];

    return (
        <div style={{ maxWidth: 900 }}>
            <div style={{ display: "flex", gap: 4, marginBottom: 20, background: S.card, borderRadius: 12, padding: 4, border: `1px solid ${S.border}`, overflowX: "auto" }}>
                {tabs.map(t => (
                    <button key={t.id} onClick={() => setSettingsTab(t.id)} style={{ flex: 1, padding: "10px 0", borderRadius: 10, border: "none", cursor: "pointer", fontFamily: "inherit", fontSize: 12, fontWeight: 600, transition: "all 0.2s", display: "flex", alignItems: "center", justifyContent: "center", gap: 5, whiteSpace: "nowrap", background: settingsTab === t.id ? S.navy : "transparent", color: settingsTab === t.id ? "#fff" : S.textDim }}>{t.icon} {t.label}</button>
                ))}
            </div>

            {/* ═══ PRICING TAB ═══ */}
            {settingsTab === "pricing" && (<div style={{ animation: "fadeIn 0.3s ease" }}>
                <div style={{ background: `linear-gradient(135deg, ${S.navy} 0%, ${S.navyLight} 100%)`, borderRadius: 14, padding: "18px 22px", marginBottom: 18 }}>
                    <div style={{ display: "flex", alignItems: "flex-start", gap: 14 }}>
                        <span style={{ fontSize: 24, marginTop: 2 }}>💡</span>
                        <div style={{ flex: 1 }}>
                            <div style={{ fontSize: 14, fontWeight: 700, color: "#fff", marginBottom: 6 }}>Lagos Delivery Market Research — Recommended Pricing</div>
                            <div style={{ fontSize: 12, color: "rgba(255,255,255,0.55)", lineHeight: 1.7, marginBottom: 12 }}>Based on analysis of Kwik, Gokada, GIG Logistics, and 50+ independent dispatch riders across Lagos. Defaults below are calibrated for competitive positioning while maintaining healthy margins.</div>
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10 }}>
                                {[{ label: "Same Area", range: "₦1,200 – ₦3,000", desc: "Within Ikeja, Lekki, etc.", km: "1–5 km" }, { label: "Mainland↔Island", range: "₦3,000 – ₦7,000", desc: "Bridge crossing required", km: "10–25 km" }, { label: "Outer Lagos", range: "₦5,000 – ₦12,000", desc: "Ikorodu, Ojo, Badagry", km: "20–40 km" }].map(r => (<div key={r.label} style={{ background: "rgba(255,255,255,0.08)", borderRadius: 10, padding: "10px 12px" }}><div style={{ fontSize: 10, fontWeight: 700, color: S.gold, marginBottom: 3 }}>{r.label}</div><div style={{ fontSize: 14, fontWeight: 800, color: "#fff", fontFamily: "'Space Mono',monospace" }}>{r.range}</div><div style={{ fontSize: 9, color: "rgba(255,255,255,0.4)", marginTop: 3 }}>{r.desc} • ~{r.km}</div></div>))}
                            </div>
                        </div>
                    </div>
                </div>

                {vehicles.map(v => {
                    const name = v.name.toLowerCase();
                    const emoji = name.includes('bike') ? "🏍️" : name.includes('car') ? "🚗" : name.includes('van') ? "🚐" : "🚚";
                    const color = name.includes('bike') ? "#10B981" : name.includes('car') ? "#3B82F6" : "#8B5CF6";

                    return (
                        <div key={v.id} style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, marginBottom: 14, overflow: "hidden" }}>
                            <div style={{ padding: "14px 20px", borderBottom: `1px solid ${S.border}`, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                                    <span style={{ fontSize: 22 }}>{emoji}</span>
                                    <div>
                                        <div style={{ fontSize: 15, fontWeight: 700, color: S.navy }}>{v.name}</div>
                                        <div style={{ fontSize: 11, color: S.textMuted }}>{v.description || "Delivery vehicle"}</div>
                                    </div>
                                </div>
                                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                    <div style={{ background: `${color}12`, padding: "6px 14px", borderRadius: 8 }}>
                                        <span style={{ fontSize: 11, fontWeight: 700, color: color }}>MIN ₦{parseFloat(v.min_fee).toLocaleString()}</span>
                                    </div>
                                </div>
                            </div>
                            <div style={{ padding: 20 }}>
                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr 1fr", gap: 14, marginBottom: 16 }}>
                                    <div>
                                        <label style={labelStyle}>Base Fare (₦)</label>
                                        <input
                                            value={v.base_fare}
                                            onChange={e => updateLocalVehicle(v.id, 'base_fare', e.target.value)}
                                            style={inputStyle}
                                            type="number"
                                        />
                                    </div>
                                    <div>
                                        <label style={labelStyle}>Per KM (₦)</label>
                                        <input
                                            value={v.rate_per_km}
                                            onChange={e => updateLocalVehicle(v.id, 'rate_per_km', e.target.value)}
                                            style={inputStyle}
                                            type="number"
                                        />
                                    </div>
                                    <div>
                                        <label style={labelStyle}>Per Min (₦)</label>
                                        <input
                                            value={v.rate_per_minute}
                                            onChange={e => updateLocalVehicle(v.id, 'rate_per_minute', e.target.value)}
                                            style={inputStyle}
                                            type="number"
                                        />
                                    </div>
                                    <div>
                                        <label style={labelStyle}>Min KM</label>
                                        <input
                                            value={v.min_distance_km}
                                            onChange={e => updateLocalVehicle(v.id, 'min_distance_km', e.target.value)}
                                            style={inputStyle}
                                            type="number"
                                        />
                                    </div>
                                    <div>
                                        <label style={labelStyle}>Min Fee (₦)</label>
                                        <input
                                            value={v.min_fee}
                                            onChange={e => updateLocalVehicle(v.id, 'min_fee', e.target.value)}
                                            style={{ ...inputStyle, color: color, borderColor: `${color}40` }}
                                            type="number"
                                        />
                                    </div>
                                </div>
                                <div style={{ background: "#f8fafc", borderRadius: 10, padding: "12px 16px" }}>
                                    <div style={{ fontSize: 11, fontWeight: 700, color: S.textMuted, marginBottom: 8 }}>PRICE PREVIEW (base — no zone/weight surcharges)</div>
                                    <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                                        {[1, 3, 5, 8, 12, 20, 30].map(km => {
                                            const { price } = calcPrice(v, km, "same", 0);
                                            const minKm = parseFloat(v.min_distance_km);
                                            return (
                                                <div key={km} style={{ padding: "8px 10px", background: "#fff", borderRadius: 8, border: `1px solid ${km <= minKm ? `${color}30` : S.border}`, textAlign: "center", minWidth: 68, flex: 1 }}>
                                                    <div style={{ fontSize: 10, color: S.textMuted, fontWeight: 600 }}>{km} KM</div>
                                                    <div style={{ fontSize: 14, fontWeight: 800, color: color, fontFamily: "'Space Mono',monospace" }}>₦{price.toLocaleString()}</div>
                                                    {km <= minKm && <div style={{ fontSize: 8, color: color, fontWeight: 700 }}>MIN RATE</div>}
                                                    {tierEnabled && km >= tier1Km && <div style={{ fontSize: 8, color: S.green, fontWeight: 700 }}>−{km >= tier2Km ? tier2Discount : tier1Discount}%</div>}
                                                </div>
                                            );
                                        })}
                                    </div>
                                    <div style={{ marginTop: 8, fontSize: 10, color: S.textMuted, lineHeight: 1.5 }}>
                                        Formula: Base ₦{v.base_fare} + (Km × ₦{v.rate_per_km}) + (Time × ₦{v.rate_per_minute}). Min Fee: ₦{v.min_fee} for ≤{v.min_distance_km}km.
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                })}

                <SC title="Cash on Delivery (COD) Fee" icon="💵" desc="Deducted from COD amount before merchant settlement">
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                        <div><label style={labelStyle}>Flat Fee per COD (₦)</label><input value={codFee} onChange={e => setCodFee(Number(e.target.value) || 0)} style={inputStyle} /><div style={{ fontSize: 10, color: S.textMuted, marginTop: 3 }}>Fixed charge per COD collection. Market: ₦300–₦500</div></div>
                        <div><label style={labelStyle}>Percentage Fee (%)</label><input value={codPct} onChange={e => setCodPct(Number(e.target.value) || 0)} step="0.1" type="number" style={inputStyle} /><div style={{ fontSize: 10, color: S.textMuted, marginTop: 3 }}>On top of flat fee. 1.5% on ₦50,000 = ₦750</div></div>
                    </div>
                    <div style={{ marginTop: 14, background: S.greenBg, borderRadius: 10, padding: "12px 16px" }}>
                        <div style={{ fontSize: 11, fontWeight: 700, color: S.green, marginBottom: 6 }}>COD SETTLEMENT PREVIEW</div>
                        <div style={{ display: "flex", gap: 14 }}>
                            {[10000, 50000, 150000, 500000].map(amt => { const fee = codFee + Math.round(amt * (codPct / 100)); return (<div key={amt} style={{ flex: 1, textAlign: "center" }}><div style={{ fontSize: 10, color: S.textMuted }}>₦{amt.toLocaleString()}</div><div style={{ fontSize: 12, fontWeight: 700, color: S.red, fontFamily: "'Space Mono',monospace" }}>−₦{fee.toLocaleString()}</div><div style={{ fontSize: 12, fontWeight: 700, color: S.green, fontFamily: "'Space Mono',monospace" }}>→₦{(amt - fee).toLocaleString()}</div><div style={{ fontSize: 8, color: S.textMuted }}>({((fee / amt) * 100).toFixed(1)}%)</div></div>); })}
                        </div>
                    </div>
                </SC>

                <SC title="Distance Tier Discounts" icon="📏" desc="Reduce per-km rate for longer distances" right={<Toggle on={tierEnabled} setOn={setTierEnabled} />}>
                    {tierEnabled ? (<div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 14 }}>
                        <div><label style={labelStyle}>Tier 1 From (KM)</label><input value={tier1Km} onChange={e => setTier1Km(Number(e.target.value) || 0)} style={inputStyle} /></div>
                        <div><label style={labelStyle}>Tier 1 Discount (%)</label><input value={tier1Discount} onChange={e => setTier1Discount(Number(e.target.value) || 0)} style={inputStyle} /></div>
                        <div><label style={labelStyle}>Tier 2 From (KM)</label><input value={tier2Km} onChange={e => setTier2Km(Number(e.target.value) || 0)} style={inputStyle} /></div>
                        <div><label style={labelStyle}>Tier 2 Discount (%)</label><input value={tier2Discount} onChange={e => setTier2Discount(Number(e.target.value) || 0)} style={inputStyle} /></div>
                    </div>) : (<div style={{ fontSize: 12, color: S.textMuted, textAlign: "center", padding: 10 }}>Disabled — flat per-km rate applies</div>)}
                </SC>

                <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 8 }}>
                    <button onClick={handleReset} style={{ padding: "10px 24px", borderRadius: 10, border: `1px solid ${S.border}`, background: S.card, cursor: "pointer", fontFamily: "inherit", fontSize: 13, fontWeight: 600, color: S.textDim }}>Reset Defaults</button>
                    <button onClick={handleSave} style={{ padding: "10px 32px", borderRadius: 10, border: "none", cursor: "pointer", fontFamily: "inherit", fontSize: 13, fontWeight: 700, background: `linear-gradient(135deg,${S.gold},${S.goldLight})`, color: S.navy, boxShadow: "0 2px 8px rgba(232,168,56,0.25)" }}>{saved ? "✓ Saved!" : "Save Pricing"}</button>
                </div>
            </div>)}

            {/* ═══ ZONES & SURCHARGES TAB ═══ */}
            {settingsTab === "zones" && (<div style={{ animation: "fadeIn 0.3s ease" }}>
                <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, marginBottom: 14, overflow: "hidden" }}>
                    <div style={{ padding: "14px 20px", borderBottom: `1px solid ${S.border}` }}><div style={{ fontSize: 15, fontWeight: 700, color: S.navy }}>🗺️ Lagos Delivery Zones</div><div style={{ fontSize: 11, color: S.textMuted }}>Zone surcharges added on top of base distance pricing</div></div>
                    {/* Pass empty arrays to small map since it is just for visualization */}
                    <div style={{ padding: 20 }}><LagosMap orders={[]} riders={[]} small={false} showZones={true} /></div>
                </div>
                <SC title="Zone-Based Surcharges" icon="📍" desc="Additional fees based on delivery route type">
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14, marginBottom: 16 }}>
                        <div style={{ background: "rgba(232,168,56,0.06)", borderRadius: 10, padding: 14, border: "1px solid rgba(232,168,56,0.15)" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}><span style={{ fontSize: 16 }}>🌉</span><div style={{ fontSize: 13, fontWeight: 700, color: S.navy }}>Bridge Crossing</div></div>
                            <label style={labelStyle}>Surcharge (₦)</label><input value={bridgeSurcharge} onChange={e => setBridgeSurcharge(Number(e.target.value) || 0)} style={inputStyle} />
                            <div style={{ fontSize: 10, color: S.textMuted, marginTop: 4 }}>Mainland ↔ Island via 3rd Mainland, Carter, or Eko Bridge</div>
                        </div>
                        <div style={{ background: "rgba(139,92,246,0.05)", borderRadius: 10, padding: 14, border: "1px solid rgba(139,92,246,0.12)" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}><span style={{ fontSize: 16 }}>🏝️</span><div style={{ fontSize: 13, fontWeight: 700, color: S.navy }}>Island Premium</div></div>
                            <label style={labelStyle}>Surcharge (₦)</label><input value={islandPremium} onChange={e => setIslandPremium(Number(e.target.value) || 0)} style={inputStyle} />
                            <div style={{ fontSize: 10, color: S.textMuted, marginTop: 4 }}>Both pickup & dropoff on Island (VI, Ikoyi, Lekki)</div>
                        </div>
                        <div style={{ background: "rgba(16,185,129,0.05)", borderRadius: 10, padding: 14, border: "1px solid rgba(16,185,129,0.12)" }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 8 }}><span style={{ fontSize: 16 }}>🛤️</span><div style={{ fontSize: 13, fontWeight: 700, color: S.navy }}>Outer Lagos</div></div>
                            <label style={labelStyle}>Surcharge (₦)</label><input value={outerZoneSurcharge} onChange={e => setOuterZoneSurcharge(Number(e.target.value) || 0)} style={inputStyle} />
                            <div style={{ fontSize: 10, color: S.textMuted, marginTop: 4 }}>Ikorodu, Ojo, Badagry, Epe, Agbara</div>
                        </div>
                    </div>
                    <div style={{ background: "#f8fafc", borderRadius: 10, padding: "14px 16px" }}>
                        <div style={{ fontSize: 11, fontWeight: 700, color: S.textMuted, marginBottom: 10 }}>ZONE EXAMPLES (BIKE, 10KM)</div>
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 10 }}>
                            {[{ l: "Same Zone", z: "same", d: "Ikeja→Ikeja", i: "🏠" }, { l: "Bridge", z: "bridge", d: "Yaba→V.I.", i: "🌉" }, { l: "Island", z: "island", d: "V.I.→Lekki", i: "🏝️" }, { l: "Outer", z: "outer", d: "Ikeja→Ikorodu", i: "🛤️" }].map(z => {
                                const refVehicle = vehicles.find(v => v.name.toLowerCase().includes('bike')) || vehicles[0];
                                if (!refVehicle) return null;
                                const { price } = calcPrice(refVehicle, 10, z.z, 3);
                                return (<div key={z.z} style={{ textAlign: "center", padding: "10px 8px", background: "#fff", borderRadius: 8, border: `1px solid ${S.border}` }}><div style={{ fontSize: 16 }}>{z.i}</div><div style={{ fontSize: 10, fontWeight: 700, color: S.navy, marginTop: 2 }}>{z.l}</div><div style={{ fontSize: 16, fontWeight: 800, color: S.gold, fontFamily: "'Space Mono',monospace", margin: "4px 0" }}>₦{price.toLocaleString()}</div><div style={{ fontSize: 9, color: S.textMuted }}>{z.d}</div></div>);
                            })}
                        </div>
                    </div>
                </SC>

                <SC title="Weight-Based Surcharges" icon="⚖️" desc="Extra charge for heavy packages">
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14 }}>
                        <div><label style={labelStyle}>Free Weight Limit (KG)</label><input value={weightThreshold} onChange={e => setWeightThreshold(Number(e.target.value) || 0)} style={inputStyle} /><div style={{ fontSize: 10, color: S.textMuted, marginTop: 3 }}>No surcharge below this</div></div>
                        <div><label style={labelStyle}>Surcharge per Unit (₦)</label><input value={weightSurcharge} onChange={e => setWeightSurcharge(Number(e.target.value) || 0)} style={inputStyle} /></div>
                        <div><label style={labelStyle}>Weight Unit (KG)</label><input value={weightUnit} onChange={e => setWeightUnit(Number(e.target.value) || 1)} style={inputStyle} /><div style={{ fontSize: 10, color: S.textMuted, marginTop: 3 }}>Each extra {weightUnit}kg = ₦{weightSurcharge}</div></div>
                    </div>
                    <div style={{ marginTop: 12, background: "#f8fafc", borderRadius: 8, padding: "10px 14px", display: "flex", gap: 12 }}>
                        {[2, 5, 10, 15, 25].map(w => { const e = w > weightThreshold ? Math.ceil((w - weightThreshold) / weightUnit) * weightSurcharge : 0; return (<div key={w} style={{ flex: 1, textAlign: "center" }}><div style={{ fontSize: 10, color: S.textMuted, fontWeight: 600 }}>{w}kg</div><div style={{ fontSize: 12, fontWeight: 700, color: e > 0 ? S.red : S.green, fontFamily: "'Space Mono',monospace" }}>{e > 0 ? `+₦${e.toLocaleString()}` : "FREE"}</div></div>); })}
                    </div>
                </SC>

                <SC title="Surge / Peak Hour Pricing" icon="⚡" desc="Higher rates during peak traffic" right={<Toggle on={surgeEnabled} setOn={setSurgeEnabled} />}>
                    {surgeEnabled ? (<div>
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr 1fr", gap: 12, marginBottom: 14 }}>
                            <div><label style={labelStyle}>Multiplier</label><input value={surgeMultiplier} onChange={e => setSurgeMultiplier(Number(e.target.value) || 1)} step="0.1" type="number" style={inputStyle} /></div>
                            <div><label style={labelStyle}>AM Start</label><input value={surgeMorningStart} onChange={e => setSurgeMorningStart(e.target.value)} type="time" style={inputStyle} /></div>
                            <div><label style={labelStyle}>AM End</label><input value={surgeMorningEnd} onChange={e => setSurgeMorningEnd(e.target.value)} type="time" style={inputStyle} /></div>
                            <div><label style={labelStyle}>PM Start</label><input value={surgeEveningStart} onChange={e => setSurgeEveningStart(e.target.value)} type="time" style={inputStyle} /></div>
                            <div><label style={labelStyle}>PM End</label><input value={surgeEveningEnd} onChange={e => setSurgeEveningEnd(e.target.value)} type="time" style={inputStyle} /></div>
                        </div>
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 16px", background: "rgba(59,130,246,0.04)", borderRadius: 10, marginBottom: 10 }}>
                            <div><div style={{ fontSize: 13, fontWeight: 600 }}>🌧️ Rain Surge</div><div style={{ fontSize: 11, color: S.textMuted }}>Auto-apply during rainfall</div></div>
                            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>{rainSurge && <input value={rainMultiplier} onChange={e => setRainMultiplier(Number(e.target.value) || 1)} step="0.1" type="number" style={{ ...inputStyle, width: 80, textAlign: "center" }} />}<Toggle on={rainSurge} setOn={setRainSurge} size="sm" /></div>
                        </div>
                        <div style={{ padding: "10px 14px", background: S.yellowBg, borderRadius: 8, display: "flex", alignItems: "center", gap: 8 }}><span style={{ fontSize: 14 }}>⚠️</span><span style={{ fontSize: 11, color: S.yellow, fontWeight: 600 }}>During {surgeMorningStart}–{surgeMorningEnd} & {surgeEveningStart}–{surgeEveningEnd}, prices × {surgeMultiplier}. ₦1,200 → ₦{Math.round(1200 * surgeMultiplier).toLocaleString()}.</span></div>
                    </div>) : (<div style={{ fontSize: 12, color: S.textMuted, textAlign: "center", padding: 10 }}>Surge pricing disabled — flat rates 24/7</div>)}
                </SC>

                <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 8 }}>
                    <button onClick={handleReset} style={{ padding: "10px 24px", borderRadius: 10, border: `1px solid ${S.border}`, background: S.card, cursor: "pointer", fontFamily: "inherit", fontSize: 13, fontWeight: 600, color: S.textDim }}>Reset Defaults</button>
                    <button onClick={handleSave} style={{ padding: "10px 32px", borderRadius: 10, border: "none", cursor: "pointer", fontFamily: "inherit", fontSize: 13, fontWeight: 700, background: `linear-gradient(135deg,${S.gold},${S.goldLight})`, color: S.navy, boxShadow: "0 2px 8px rgba(232,168,56,0.25)" }}>{saved ? "✓ Saved!" : "Save Zone Settings"}</button>
                </div>
            </div>)}

            {/* ═══ PRICE CALCULATOR TAB ═══ */}
            {settingsTab === "simulator" && (<div style={{ animation: "fadeIn 0.3s ease" }}>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
                    <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, overflow: "hidden" }}>
                        <div style={{ padding: "14px 20px", borderBottom: `1px solid ${S.border}` }}><div style={{ fontSize: 15, fontWeight: 700, color: S.navy }}>🧮 Price Calculator</div><div style={{ fontSize: 11, color: S.textMuted }}>Simulate delivery pricing for any route</div></div>
                        <div style={{ padding: 20 }}>
                            <div style={{ marginBottom: 16 }}><label style={labelStyle}>Vehicle Type</label>
                                <div style={{ display: "flex", gap: 8 }}>
                                    {vehicles.map(v => {
                                        const emoji = v.name.toLowerCase().includes('bike') ? "🏍️" : v.name.toLowerCase().includes('car') ? "🚗" : "🚐";
                                        return (
                                            <button key={v.id} onClick={() => setSimVehicleId(v.id)} style={{ flex: 1, padding: "10px 0", borderRadius: 10, cursor: "pointer", fontFamily: "inherit", border: simVehicleId === v.id ? `2px solid ${S.gold}` : `1px solid ${S.border}`, background: simVehicleId === v.id ? S.goldPale : "#fff", textAlign: "center" }}>
                                                <div style={{ fontSize: 18 }}>{emoji}</div>
                                                <div style={{ fontSize: 11, fontWeight: 600, color: simVehicleId === v.id ? S.gold : S.text }}>{v.name}</div>
                                            </button>
                                        );
                                    })}
                                </div>
                            </div>
                            <div style={{ marginBottom: 16 }}><label style={labelStyle}>Distance: <span style={{ color: S.gold, fontFamily: "'Space Mono',monospace" }}>{simKm} km</span></label><input type="range" min="1" max="50" value={simKm} onChange={e => setSimKm(Number(e.target.value))} style={{ width: "100%", accentColor: S.gold }} /><div style={{ display: "flex", justifyContent: "space-between", fontSize: 9, color: S.textMuted }}><span>1km</span><span>5km</span><span>15km</span><span>50km</span></div></div>
                            <div style={{ marginBottom: 16 }}><label style={labelStyle}>Delivery Zone</label>
                                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>{[{ id: "same", l: "Same Area", i: "🏠" }, { id: "bridge", l: "Bridge Cross", i: "🌉" }, { id: "island", l: "Island Only", i: "🏝️" }, { id: "outer", l: "Outer Lagos", i: "🛤️" }].map(z => (<button key={z.id} onClick={() => setSimZone(z.id)} style={{ padding: "8px 10px", borderRadius: 8, cursor: "pointer", fontFamily: "inherit", border: simZone === z.id ? `2px solid ${S.gold}` : `1px solid ${S.border}`, background: simZone === z.id ? S.goldPale : "#fff", fontSize: 11, fontWeight: 600, display: "flex", alignItems: "center", gap: 6 }}><span>{z.i}</span>{z.l}</button>))}</div>
                            </div>
                            <div style={{ marginBottom: 16 }}><label style={labelStyle}>Weight: <span style={{ color: S.gold, fontFamily: "'Space Mono',monospace" }}>{simWeight} kg</span></label><input type="range" min="1" max="30" value={simWeight} onChange={e => setSimWeight(Number(e.target.value))} style={{ width: "100%", accentColor: S.gold }} /></div>
                            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 14px", borderRadius: 8, border: `1px solid ${S.border}` }}><div style={{ fontSize: 12, fontWeight: 600 }}>⚡ Surge ({surgeMultiplier}x)</div><Toggle on={simSurge} setOn={setSimSurge} size="sm" /></div>
                        </div>
                    </div>
                    <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, overflow: "hidden", display: "flex", flexDirection: "column" }}>
                        <div style={{ padding: "14px 20px", borderBottom: `1px solid ${S.border}` }}><div style={{ fontSize: 15, fontWeight: 700, color: S.navy }}>💰 Price Breakdown</div></div>
                        <div style={{ padding: 20, flex: 1, display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
                            <div>
                                {selectedVehicle && (() => {
                                    const base = parseFloat(selectedVehicle.base_fare);
                                    const perKm = parseFloat(selectedVehicle.rate_per_km);
                                    const perMin = parseFloat(selectedVehicle.rate_per_minute);
                                    const minKm = parseFloat(selectedVehicle.min_distance_km);
                                    const minFee = parseFloat(selectedVehicle.min_fee);

                                    const distCost = simKm * perKm;
                                    const timeCost = simDuration * perMin;
                                    const rawTotal = base + distCost + timeCost;
                                    const isMinApplied = rawTotal < minFee || simKm <= minKm;

                                    return (
                                        <>
                                            <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: `1px solid ${S.borderLight}` }}>
                                                <span style={{ fontSize: 12, color: S.text }}>Base fee</span>
                                                <span style={{ fontSize: 13, fontWeight: 700, color: S.navy, fontFamily: "'Space Mono',monospace" }}>₦{base.toLocaleString()}</span>
                                            </div>
                                            {!isMinApplied && (
                                                <>
                                                    <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: `1px solid ${S.borderLight}` }}>
                                                        <span style={{ fontSize: 12, color: S.text }}>Distance ({simKm}km @ ₦{perKm}/km)</span>
                                                        <span style={{ fontSize: 13, fontWeight: 700, color: S.navy, fontFamily: "'Space Mono',monospace" }}>₦{distCost.toLocaleString()}</span>
                                                    </div>
                                                    <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: `1px solid ${S.borderLight}` }}>
                                                        <span style={{ fontSize: 12, color: S.text }}>Time (~{simDuration}min @ ₦{perMin}/min)</span>
                                                        <span style={{ fontSize: 13, fontWeight: 700, color: S.navy, fontFamily: "'Space Mono',monospace" }}>₦{timeCost.toLocaleString()}</span>
                                                    </div>
                                                </>
                                            )}
                                            {isMinApplied && (
                                                <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: `1px solid ${S.borderLight}` }}>
                                                    <span style={{ fontSize: 12, color: S.green }}>Minimum fee applied</span>
                                                    <span style={{ fontSize: 13, fontWeight: 700, color: S.green, fontFamily: "'Space Mono',monospace" }}>₦{minFee.toLocaleString()}</span>
                                                </div>
                                            )}
                                            {simZone === "bridge" && <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: `1px solid ${S.borderLight}` }}><span style={{ fontSize: 12 }}>Zone: Bridge</span><span style={{ fontSize: 13, fontWeight: 700 }}>+₦{bridgeSurcharge.toLocaleString()}</span></div>}
                                            {simZone === "outer" && <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: `1px solid ${S.borderLight}` }}><span style={{ fontSize: 12 }}>Zone: Outer</span><span style={{ fontSize: 13, fontWeight: 700 }}>+₦{outerZoneSurcharge.toLocaleString()}</span></div>}
                                            {simZone === "island" && <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: `1px solid ${S.borderLight}` }}><span style={{ fontSize: 12 }}>Zone: Island</span><span style={{ fontSize: 13, fontWeight: 700 }}>+₦{islandPremium.toLocaleString()}</span></div>}
                                            {simWeight > weightThreshold && <div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: `1px solid ${S.borderLight}` }}><span style={{ fontSize: 12 }}>Weight Surcharge</span><span style={{ fontSize: 13, fontWeight: 700 }}>+₦{(Math.ceil((simWeight - weightThreshold) / weightUnit) * weightSurcharge).toLocaleString()}</span></div>}

                                            {simSurge && (<div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", marginTop: 4 }}><span style={{ fontSize: 12, color: S.red }}>⚡ Surge ({surgeMultiplier}x)</span><span style={{ fontSize: 13, fontWeight: 700, color: S.red, fontFamily: "'Space Mono',monospace" }}>+₦{(simFinal - simPrice).toLocaleString()}</span></div>)}
                                        </>
                                    );
                                })()}
                            </div>
                            <div style={{ marginTop: 16, padding: "16px 18px", background: `linear-gradient(135deg, ${S.navy}, ${S.navyLight})`, borderRadius: 12, textAlign: "center" }}>
                                <div style={{ fontSize: 11, color: "rgba(255,255,255,0.5)", fontWeight: 600, marginBottom: 4 }}>CUSTOMER PAYS</div>
                                <div style={{ fontSize: 32, fontWeight: 900, color: S.gold, fontFamily: "'Space Mono',monospace" }}>₦{simFinal.toLocaleString()}</div>
                                <div style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", marginTop: 4 }}>{selectedVehicle?.name?.toUpperCase()} • {simKm}km (~{simDuration}min) • {simZone === "bridge" ? "Bridge" : simZone === "island" ? "Island" : simZone === "outer" ? "Outer" : "Local"} • {simWeight}kg{simSurge ? " • SURGE" : ""}</div>
                            </div>
                            <div style={{ marginTop: 12, background: "#f8fafc", borderRadius: 8, padding: "10px 14px" }}>
                                <div style={{ fontSize: 10, fontWeight: 700, color: S.textMuted, marginBottom: 6 }}>COMPARE ALL VEHICLES</div>
                                <div style={{ display: "flex", gap: 8 }}>
                                    {vehicles.map(v => {
                                        const { price } = calcPrice(v, simKm, simZone, simWeight);
                                        const f = simSurge ? Math.round(price * surgeMultiplier) : price;
                                        const emoji = v.name.toLowerCase().includes('bike') ? "🏍️" : v.name.toLowerCase().includes('car') ? "🚗" : "🚐";

                                        return (
                                            <div key={v.id} style={{ flex: 1, textAlign: "center", padding: 6, borderRadius: 6, background: simVehicleId === v.id ? "rgba(232,168,56,0.1)" : "transparent", border: simVehicleId === v.id ? `1px solid ${S.gold}` : "1px solid transparent" }}>
                                                <div style={{ fontSize: 14 }}>{emoji}</div>
                                                <div style={{ fontSize: 14, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono',monospace" }}>₦{f.toLocaleString()}</div>
                                            </div>
                                        );
                                    })}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, marginTop: 14, overflow: "hidden" }}>
                    <div style={{ padding: "14px 20px", borderBottom: `1px solid ${S.border}` }}><div style={{ fontSize: 14, fontWeight: 700, color: S.navy }}>🚀 Common Lagos Routes — Quick Reference</div></div>
                    <div style={{ padding: 16, overflowX: "auto" }}>
                        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                            <thead><tr style={{ borderBottom: `2px solid ${S.border}` }}>
                                {["Route", "KM", "Zone", ...vehicles.map(v => v.name)].map(h => (<th key={h} style={{ padding: "8px 10px", textAlign: "left", fontSize: 10, fontWeight: 700, color: S.textMuted, textTransform: "uppercase" }}>{h}</th>))}
                            </tr></thead>
                            <tbody>{[{ r: "Ikeja → Allen Ave", km: 3, z: "same", d: "Local" }, { r: "Yaba → V.I.", km: 12, z: "bridge", d: "Bridge" }, { r: "Surulere → Lekki Ph1", km: 18, z: "bridge", d: "Bridge" }, { r: "V.I. → Lekki", km: 8, z: "island", d: "Island" }, { r: "Ikeja → Ikorodu", km: 28, z: "outer", d: "Outer" }, { r: "Maryland → Ajah", km: 32, z: "bridge", d: "Bridge" }, { r: "Apapa → Ojo", km: 15, z: "outer", d: "Outer" }, { r: "V.I. → Ajah", km: 22, z: "island", d: "Island" }].map((r, i) => (
                                <tr key={i} style={{ borderBottom: `1px solid ${S.borderLight}` }}>
                                    <td style={{ padding: "8px 10px", fontWeight: 600 }}>{r.r}</td>
                                    <td style={{ padding: "8px 10px", fontFamily: "'Space Mono',monospace", fontWeight: 700 }}>{r.km}</td>
                                    <td style={{ padding: "8px 10px" }}><span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 4, background: r.z === "bridge" ? "rgba(232,168,56,0.1)" : r.z === "island" ? "rgba(139,92,246,0.08)" : r.z === "outer" ? "rgba(16,185,129,0.08)" : "#f1f5f9", color: r.z === "bridge" ? S.gold : r.z === "island" ? "#8B5CF6" : r.z === "outer" ? S.green : S.textMuted, fontWeight: 700 }}>{r.d}</span></td>
                                    {vehicles.map(v => {
                                        const { price } = calcPrice(v, r.km, r.z, 3);
                                        return <td key={v.id} style={{ padding: "8px 10px", fontFamily: "'Space Mono',monospace", fontWeight: 700, color: S.navy }}>₦{price.toLocaleString()}</td>;
                                    })}
                                </tr>
                            ))}</tbody>
                        </table>
                    </div>
                </div>
            </div>)}

            {/* ═══ DISPATCH RULES TAB ═══ */}
            {settingsTab === "dispatch" && (<div style={{ animation: "fadeIn 0.3s ease" }}>
                <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, marginBottom: 14, overflow: "hidden" }}>
                    <div style={{ padding: "14px 20px", borderBottom: `1px solid ${S.border}` }}><span style={{ fontSize: 14, fontWeight: 700 }}>Auto-Assignment</span></div>
                    <div style={{ padding: 20 }}>
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 }}><div><div style={{ fontSize: 13, fontWeight: 600 }}>Auto-assign nearest rider</div><div style={{ fontSize: 11, color: S.textMuted, marginTop: 2 }}>Automatically assigns closest available rider</div></div><Toggle on={autoAssign} setOn={setAutoAssign} /></div>
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14 }}>
                            <div><label style={labelStyle}>Assignment Radius (KM)</label><input value={assignRadius} onChange={e => setAssignRadius(Number(e.target.value) || 0)} style={inputStyle} /></div>
                            <div><label style={labelStyle}>Acceptance Timeout (sec)</label><input value={acceptTimeout} onChange={e => setAcceptTimeout(Number(e.target.value) || 0)} style={inputStyle} /></div>
                            <div><label style={labelStyle}>Retry Attempts</label><input value={3} readOnly style={{ ...inputStyle, background: "#f8fafc", color: S.textMuted }} /></div>
                        </div>
                    </div>
                </div>
                <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, marginBottom: 14, overflow: "hidden" }}>
                    <div style={{ padding: "14px 20px", borderBottom: `1px solid ${S.border}` }}><span style={{ fontSize: 14, fontWeight: 700 }}>Concurrent Orders per Rider</span></div>
                    <div style={{ padding: 20 }}>
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14 }}>
                            <div><label style={labelStyle}>🏍️ Bike Max</label><input value={maxBike} onChange={e => setMaxBike(Number(e.target.value) || 0)} style={inputStyle} /></div>
                            <div><label style={labelStyle}>🚗 Car Max</label><input value={maxCar} onChange={e => setMaxCar(Number(e.target.value) || 0)} style={inputStyle} /></div>
                            <div><label style={labelStyle}>🚐 Van Max</label><input value={maxVan} onChange={e => setMaxVan(Number(e.target.value) || 0)} style={inputStyle} /></div>
                        </div>
                    </div>
                </div>
                <div style={{ display: "flex", justifyContent: "flex-end", gap: 10, marginTop: 8 }}><button onClick={handleSave} style={{ padding: "10px 32px", borderRadius: 10, border: "none", cursor: "pointer", fontFamily: "inherit", fontSize: 13, fontWeight: 700, background: `linear-gradient(135deg,${S.gold},${S.goldLight})`, color: S.navy, boxShadow: "0 2px 8px rgba(232,168,56,0.25)" }}>{saved ? "✓ Saved!" : "Save Settings"}</button></div>
            </div>)}

            {/* ═══ NOTIFICATIONS TAB ═══ */}
            {settingsTab === "notifications" && (<div style={{ animation: "fadeIn 0.3s ease" }}>
                <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, overflow: "hidden" }}>
                    {[{ label: "New order alert", desc: "Sound + desktop notification when a new order arrives", on: notifNew, set: setNotifNew }, { label: "Unassigned order warning", desc: "Alert if an order is unassigned for more than 3 minutes", on: notifUnassigned, set: setNotifUnassigned }, { label: "Delivery completion", desc: "Notification when a rider confirms delivery", on: notifComplete, set: setNotifComplete }, { label: "COD settlement", desc: "Notification when COD is collected and settled to merchant wallet", on: notifCod, set: setNotifCod }].map((n, i, arr) => (<div key={n.label} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px 20px", borderBottom: i < arr.length - 1 ? `1px solid ${S.borderLight}` : "none" }}><div><div style={{ fontSize: 13, fontWeight: 600 }}>{n.label}</div><div style={{ fontSize: 11, color: S.textMuted, marginTop: 2 }}>{n.desc}</div></div><Toggle on={n.on} setOn={n.set} /></div>))}
                </div>
            </div>)}

            {/* ═══ INTEGRATIONS TAB ═══ */}
            {settingsTab === "integrations" && (<div style={{ animation: "fadeIn 0.3s ease" }}>
                <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, overflow: "hidden" }}>
                    {[{ label: "Onro API", desc: "Connected — Last sync: 2 min ago", status: "connected" }, { label: "LibertyPay", desc: "Connected — Payment processing active", status: "connected" }, { label: "WhatsApp Business API", desc: "Not connected", status: "disconnected" }, { label: "Google Maps Distance Matrix", desc: "Connected — For accurate KM calculations", status: "connected" }].map((item, i, arr) => (<div key={item.label} style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "16px 20px", borderBottom: i < arr.length - 1 ? `1px solid ${S.borderLight}` : "none" }}><div><div style={{ fontSize: 13, fontWeight: 600 }}>{item.label}</div><div style={{ fontSize: 11, color: S.textMuted, marginTop: 2 }}>{item.desc}</div></div><span style={{ fontSize: 10, fontWeight: 700, padding: "4px 10px", borderRadius: 6, background: item.status === "connected" ? S.greenBg : S.redBg, color: item.status === "connected" ? S.green : S.red }}>{item.status === "connected" ? "CONNECTED" : "NOT CONNECTED"}</span></div>))}
                </div>
                <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, marginTop: 14, padding: 20 }}>
                    <label style={labelStyle}>Webhook URL</label><input defaultValue="https://api.axpress.ng/webhooks/onro" style={{ ...inputStyle, fontFamily: "'Space Mono',monospace", fontSize: 12, fontWeight: 500 }} /><div style={{ fontSize: 10, color: S.textMuted, marginTop: 4 }}>Receives real-time order status updates from Onro</div>
                </div>
            </div>)}
        </div>
    );
}
