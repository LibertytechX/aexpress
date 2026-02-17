import { useState } from "react";
import { S } from "../common/theme";
import { LagosMap } from "../map/LagosMap";

export function SettingsScreen() {
    // ─── PRICING STATE (Research-based Lagos defaults) ───
    const [bikeBase, setBikeBase] = useState(500);
    const [bikePerKm, setBikePerKm] = useState(150);
    const [bikeMinKm, setBikeMinKm] = useState(3);
    const [bikeMin, setBikeMin] = useState(1200);
    const [carBase, setCarBase] = useState(1000);
    const [carPerKm, setCarPerKm] = useState(250);
    const [carMinKm, setCarMinKm] = useState(3);
    const [carMin, setCarMin] = useState(2500);
    const [vanBase, setVanBase] = useState(2000);
    const [vanPerKm, setVanPerKm] = useState(400);
    const [vanMinKm, setVanMinKm] = useState(3);
    const [vanMin, setVanMin] = useState(5000);
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
    const [simKm, setSimKm] = useState(8);
    const [simVehicle, setSimVehicle] = useState<"bike" | "car" | "van">("bike");
    const [simZone, setSimZone] = useState("same");
    const [simWeight, setSimWeight] = useState(3);
    const [simSurge, setSimSurge] = useState(false);

    const calcPrice = (base: number, perKm: number, minKm: number, minFee: number, km: number, zone: string, weight: number) => {
        let price;
        if (km <= minKm) { price = minFee; }
        else {
            price = base + (km * perKm);
            if (tierEnabled && km >= tier2Km) price = price * (1 - tier2Discount / 100);
            else if (tierEnabled && km >= tier1Km) price = price * (1 - tier1Discount / 100);
            price = Math.max(minFee, Math.round(price));
        }
        if (zone === "bridge") price += bridgeSurcharge;
        if (zone === "outer") price += outerZoneSurcharge;
        if (zone === "island") price += islandPremium;
        if (weight > weightThreshold) price += Math.ceil((weight - weightThreshold) / weightUnit) * weightSurcharge;
        return Math.round(price);
    };

    const getVC = () => ({
        bike: { base: bikeBase, perKm: bikePerKm, minKm: bikeMinKm, min: bikeMin },
        car: { base: carBase, perKm: carPerKm, minKm: carMinKm, min: carMin },
        van: { base: vanBase, perKm: vanPerKm, minKm: vanMinKm, min: vanMin },
    });

    const simC = getVC()[simVehicle];
    const simPrice = calcPrice(simC.base, simC.perKm, simC.minKm, simC.min, simKm, simZone, simWeight);
    const simFinal = simSurge ? Math.round(simPrice * surgeMultiplier) : simPrice;

    const handleSave = () => { setSaved(true); setTimeout(() => setSaved(false), 2500); };
    const handleReset = () => {
        setBikeBase(500); setBikePerKm(150); setBikeMinKm(3); setBikeMin(1200);
        setCarBase(1000); setCarPerKm(250); setCarMinKm(3); setCarMin(2500);
        setVanBase(2000); setVanPerKm(400); setVanMinKm(3); setVanMin(5000);
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

                {[{ label: "Bike", emoji: "🏍️", color: "#10B981", base: bikeBase, setBase: setBikeBase, perKm: bikePerKm, setPerKm: setBikePerKm, minKm: bikeMinKm, setMinKm: setBikeMinKm, min: bikeMin, setMin: setBikeMin, desc: "Small packages, documents, food. Max 25kg.", mr: "₦100–₦200/km" },
                { label: "Car", emoji: "🚗", color: "#3B82F6", base: carBase, setBase: setCarBase, perKm: carPerKm, setPerKm: setCarPerKm, minKm: carMinKm, setMinKm: setCarMinKm, min: carMin, setMin: setCarMin, desc: "Medium packages, electronics, fragile. Max 100kg.", mr: "₦200–₦350/km" },
                { label: "Van", emoji: "🚐", color: "#8B5CF6", base: vanBase, setBase: setVanBase, perKm: vanPerKm, setPerKm: setVanPerKm, minKm: vanMinKm, setMinKm: setVanMinKm, min: vanMin, setMin: setVanMin, desc: "Bulk orders, furniture, large cargo. Max 500kg.", mr: "₦350–₦500/km" }
                ].map(v => (<div key={v.label} style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, marginBottom: 14, overflow: "hidden" }}>
                    <div style={{ padding: "14px 20px", borderBottom: `1px solid ${S.border}`, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 10 }}><span style={{ fontSize: 22 }}>{v.emoji}</span><div><div style={{ fontSize: 15, fontWeight: 700, color: S.navy }}>{v.label} Delivery</div><div style={{ fontSize: 11, color: S.textMuted }}>{v.desc}</div></div></div>
                        <div style={{ display: "flex", alignItems: "center", gap: 8 }}><div style={{ background: "#f8fafc", padding: "4px 10px", borderRadius: 6, fontSize: 10, color: S.textMuted }}>Market: {v.mr}</div><div style={{ background: `${v.color}12`, padding: "6px 14px", borderRadius: 8 }}><span style={{ fontSize: 11, fontWeight: 700, color: v.color }}>MIN ₦{v.min.toLocaleString()}</span></div></div>
                    </div>
                    <div style={{ padding: 20 }}>
                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 14, marginBottom: 16 }}>
                            <div><label style={labelStyle}>Base Fee (₦)</label><input value={v.base} onChange={e => v.setBase(Number(e.target.value) || 0)} style={inputStyle} /><div style={{ fontSize: 10, color: S.textMuted, marginTop: 3 }}>Flat charge per order</div></div>
                            <div><label style={labelStyle}>Per KM Rate (₦)</label><input value={v.perKm} onChange={e => v.setPerKm(Number(e.target.value) || 0)} style={inputStyle} /><div style={{ fontSize: 10, color: S.textMuted, marginTop: 3 }}>Charged after min distance</div></div>
                            <div><label style={labelStyle}>Min Distance (KM)</label><input value={v.minKm} onChange={e => v.setMinKm(Number(e.target.value) || 0)} style={inputStyle} /><div style={{ fontSize: 10, color: S.textMuted, marginTop: 3 }}>Covered by minimum fee</div></div>
                            <div><label style={labelStyle}>Minimum Fee (₦)</label><input value={v.min} onChange={e => v.setMin(Number(e.target.value) || 0)} style={{ ...inputStyle, color: v.color, borderColor: `${v.color}40` }} /><div style={{ fontSize: 10, color: S.textMuted, marginTop: 3 }}>Floor price for ≤{v.minKm}km</div></div>
                        </div>
                        <div style={{ background: "#f8fafc", borderRadius: 10, padding: "12px 16px" }}>
                            <div style={{ fontSize: 11, fontWeight: 700, color: S.textMuted, marginBottom: 8 }}>PRICE PREVIEW (base — no zone/weight surcharges)</div>
                            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
                                {[1, 3, 5, 8, 12, 20, 30].map(km => { const price = calcPrice(v.base, v.perKm, v.minKm, v.min, km, "same", 0); return (<div key={km} style={{ padding: "8px 10px", background: "#fff", borderRadius: 8, border: `1px solid ${km <= v.minKm ? `${v.color}30` : S.border}`, textAlign: "center", minWidth: 68, flex: 1 }}><div style={{ fontSize: 10, color: S.textMuted, fontWeight: 600 }}>{km} KM</div><div style={{ fontSize: 14, fontWeight: 800, color: v.color, fontFamily: "'Space Mono',monospace" }}>₦{price.toLocaleString()}</div>{km <= v.minKm && <div style={{ fontSize: 8, color: v.color, fontWeight: 700 }}>MIN RATE</div>}{tierEnabled && km >= tier1Km && <div style={{ fontSize: 8, color: S.green, fontWeight: 700 }}>−{km >= tier2Km ? tier2Discount : tier1Discount}%</div>}</div>); })}
                            </div>
                            <div style={{ marginTop: 8, fontSize: 10, color: S.textMuted, lineHeight: 1.5 }}>Formula: If ≤{v.minKm}km → ₦{v.min.toLocaleString()}. Otherwise: ₦{v.base.toLocaleString()} + (km × ₦{v.perKm}){tierEnabled ? `, ${tier1Discount}% off >${tier1Km}km, ${tier2Discount}% off >${tier2Km}km` : ""}. Plus zone + weight surcharges.</div>
                        </div>
                    </div>
                </div>))}

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
                            {[{ l: "Same Zone", z: "same", d: "Ikeja→Ikeja", i: "🏠" }, { l: "Bridge", z: "bridge", d: "Yaba→V.I.", i: "🌉" }, { l: "Island", z: "island", d: "V.I.→Lekki", i: "🏝️" }, { l: "Outer", z: "outer", d: "Ikeja→Ikorodu", i: "🛤️" }].map(z => { const p = calcPrice(bikeBase, bikePerKm, bikeMinKm, bikeMin, 10, z.z, 3); return (<div key={z.z} style={{ textAlign: "center", padding: "10px 8px", background: "#fff", borderRadius: 8, border: `1px solid ${S.border}` }}><div style={{ fontSize: 16 }}>{z.i}</div><div style={{ fontSize: 10, fontWeight: 700, color: S.navy, marginTop: 2 }}>{z.l}</div><div style={{ fontSize: 16, fontWeight: 800, color: S.gold, fontFamily: "'Space Mono',monospace", margin: "4px 0" }}>₦{p.toLocaleString()}</div><div style={{ fontSize: 9, color: S.textMuted }}>{z.d}</div></div>); })}
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
                                <div style={{ display: "flex", gap: 8 }}>{[{ id: "bike", l: "Bike", i: "🏍️" }, { id: "car", l: "Car", i: "🚗" }, { id: "van", l: "Van", i: "🚐" }].map(v => (<button key={v.id} onClick={() => setSimVehicle(v.id as any)} style={{ flex: 1, padding: "10px 0", borderRadius: 10, cursor: "pointer", fontFamily: "inherit", border: simVehicle === v.id ? `2px solid ${S.gold}` : `1px solid ${S.border}`, background: simVehicle === v.id ? S.goldPale : "#fff", textAlign: "center" }}><div style={{ fontSize: 18 }}>{v.i}</div><div style={{ fontSize: 11, fontWeight: 600, color: simVehicle === v.id ? S.gold : S.text }}>{v.l}</div></button>))}</div>
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
                                {[{ l: "Base fee", a: simC.base, s: simKm > simC.minKm }, { l: "Distance (" + simKm + "km)", a: simKm > simC.minKm ? simKm * simC.perKm : 0, s: simKm > simC.minKm }, { l: "Minimum fee applied", a: simC.min, s: simKm <= simC.minKm }, { l: "Zone surcharge", a: simZone === "bridge" ? bridgeSurcharge : simZone === "island" ? islandPremium : simZone === "outer" ? outerZoneSurcharge : 0, s: simZone !== "same" }, { l: "Weight surcharge", a: simWeight > weightThreshold ? Math.ceil((simWeight - weightThreshold) / weightUnit) * weightSurcharge : 0, s: simWeight > weightThreshold }].filter(x => x.s).map((item, idx) => (<div key={idx} style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", borderBottom: "1px solid " + S.borderLight }}><span style={{ fontSize: 12, color: item.a < 0 ? S.green : S.text }}>{item.l}</span><span style={{ fontSize: 13, fontWeight: 700, color: item.a < 0 ? S.green : S.navy, fontFamily: "'Space Mono',monospace" }}>₦{Math.abs(item.a).toLocaleString()}</span></div>))}
                                {simSurge && (<div style={{ display: "flex", justifyContent: "space-between", padding: "8px 0", marginTop: 4 }}><span style={{ fontSize: 12, color: S.red }}>⚡ Surge ({surgeMultiplier}x)</span><span style={{ fontSize: 13, fontWeight: 700, color: S.red, fontFamily: "'Space Mono',monospace" }}>+₦{(simFinal - simPrice).toLocaleString()}</span></div>)}
                            </div>
                            <div style={{ marginTop: 16, padding: "16px 18px", background: `linear-gradient(135deg, ${S.navy}, ${S.navyLight})`, borderRadius: 12, textAlign: "center" }}>
                                <div style={{ fontSize: 11, color: "rgba(255,255,255,0.5)", fontWeight: 600, marginBottom: 4 }}>CUSTOMER PAYS</div>
                                <div style={{ fontSize: 32, fontWeight: 900, color: S.gold, fontFamily: "'Space Mono',monospace" }}>₦{simFinal.toLocaleString()}</div>
                                <div style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", marginTop: 4 }}>{simVehicle.toUpperCase()} • {simKm}km • {simZone === "bridge" ? "Bridge" : simZone === "island" ? "Island" : simZone === "outer" ? "Outer" : "Local"} • {simWeight}kg{simSurge ? " • SURGE" : ""}</div>
                            </div>
                            <div style={{ marginTop: 12, background: "#f8fafc", borderRadius: 8, padding: "10px 14px" }}>
                                <div style={{ fontSize: 10, fontWeight: 700, color: S.textMuted, marginBottom: 6 }}>COMPARE ALL VEHICLES</div>
                                <div style={{ display: "flex", gap: 8 }}>{[{ id: "bike", i: "🏍️" }, { id: "car", i: "🚗" }, { id: "van", i: "🚐" }].map(v => { const c = getVC()[v.id as "bike" | "car" | "van"]; const p = calcPrice(c.base, c.perKm, c.minKm, c.min, simKm, simZone, simWeight); const f = simSurge ? Math.round(p * surgeMultiplier) : p; return (<div key={v.id} style={{ flex: 1, textAlign: "center", padding: 6, borderRadius: 6, background: simVehicle === v.id ? "rgba(232,168,56,0.1)" : "transparent", border: simVehicle === v.id ? `1px solid ${S.gold}` : "1px solid transparent" }}><div style={{ fontSize: 14 }}>{v.i}</div><div style={{ fontSize: 14, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono',monospace" }}>₦{f.toLocaleString()}</div></div>); })}</div>
                            </div>
                        </div>
                    </div>
                </div>

                <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, marginTop: 14, overflow: "hidden" }}>
                    <div style={{ padding: "14px 20px", borderBottom: `1px solid ${S.border}` }}><div style={{ fontSize: 14, fontWeight: 700, color: S.navy }}>🚀 Common Lagos Routes — Quick Reference</div></div>
                    <div style={{ padding: 16, overflowX: "auto" }}>
                        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 12 }}>
                            <thead><tr style={{ borderBottom: `2px solid ${S.border}` }}>{["Route", "KM", "Zone", "🏍️ Bike", "🚗 Car", "🚐 Van"].map(h => (<th key={h} style={{ padding: "8px 10px", textAlign: "left", fontSize: 10, fontWeight: 700, color: S.textMuted, textTransform: "uppercase" }}>{h}</th>))}</tr></thead>
                            <tbody>{[{ r: "Ikeja → Allen Ave", km: 3, z: "same", d: "Local" }, { r: "Yaba → V.I.", km: 12, z: "bridge", d: "Bridge" }, { r: "Surulere → Lekki Ph1", km: 18, z: "bridge", d: "Bridge" }, { r: "V.I. → Lekki", km: 8, z: "island", d: "Island" }, { r: "Ikeja → Ikorodu", km: 28, z: "outer", d: "Outer" }, { r: "Maryland → Ajah", km: 32, z: "bridge", d: "Bridge" }, { r: "Apapa → Ojo", km: 15, z: "outer", d: "Outer" }, { r: "V.I. → Ajah", km: 22, z: "island", d: "Island" }].map((r, i) => (<tr key={i} style={{ borderBottom: `1px solid ${S.borderLight}` }}><td style={{ padding: "8px 10px", fontWeight: 600 }}>{r.r}</td><td style={{ padding: "8px 10px", fontFamily: "'Space Mono',monospace", fontWeight: 700 }}>{r.km}</td><td style={{ padding: "8px 10px" }}><span style={{ fontSize: 10, padding: "2px 8px", borderRadius: 4, background: r.z === "bridge" ? "rgba(232,168,56,0.1)" : r.z === "island" ? "rgba(139,92,246,0.08)" : r.z === "outer" ? "rgba(16,185,129,0.08)" : "#f1f5f9", color: r.z === "bridge" ? S.gold : r.z === "island" ? "#8B5CF6" : r.z === "outer" ? S.green : S.textMuted, fontWeight: 700 }}>{r.d}</span></td>{["bike", "car", "van"].map(v => { const c = getVC()[v as "bike" | "car" | "van"]; return <td key={v} style={{ padding: "8px 10px", fontFamily: "'Space Mono',monospace", fontWeight: 700, color: S.navy }}>₦{calcPrice(c.base, c.perKm, c.minKm, c.min, r.km, r.z, 3).toLocaleString()}</td>; })}</tr>))}</tbody>
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
