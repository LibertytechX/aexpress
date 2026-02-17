import { useState } from "react";
import { S } from "../common/theme";

export function SettingsScreen() {
    const [baseFare, setBaseFare] = useState("1210");
    const [perKm, setPerKm] = useState("135");
    const [surge, setSurge] = useState(1);
    const [autoDispatch, setAutoDispatch] = useState(true);
    const [maxRadius, setMaxRadius] = useState("15");
    const [settingsTab, setSettingsTab] = useState("pricing");
    const [testDist, setTestDist] = useState("12");
    const [zP, setZP] = useState({ island: 500, mainland: 0, lekki: 800, apapa: 1000 });

    const calcPrice = (dist: number) => {
        const base = parseInt(baseFare);
        const km = parseInt(perKm);
        return (base + (dist * km)) * surge;
    };

    const iSt = { width: "100%", border: `1px solid ${S.border}`, borderRadius: 8, padding: "0 12px", height: 38, fontSize: 13, color: S.navy, background: S.bg, fontWeight: 600, fontFamily: "'Space Mono',monospace" };
    const lSt = { display: "block", fontSize: 11, fontWeight: 600, color: S.textMuted, marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.5px" };
    const tBtn = (id: string, l: string) => (<button onClick={() => setSettingsTab(id)} style={{ flex: 1, padding: "10px 0", borderBottom: settingsTab === id ? `2px solid ${S.gold}` : "2px solid transparent", background: "transparent", color: settingsTab === id ? S.gold : S.textMuted, fontWeight: 700, cursor: "pointer", fontSize: 12, fontFamily: "inherit" }}>{l}</button>);

    return (
        <div style={{ maxWidth: 900 }}>
            <div style={{ display: "flex", borderBottom: `1px solid ${S.border}`, marginBottom: 24 }}>
                {tBtn("pricing", "Pricing & Fares")}{tBtn("zones", "Zone Surcharges")}{tBtn("dispatch", "Dispatch Rules")}{tBtn("notif", "Notifications")}{tBtn("api", "API & Integrations")}
            </div>
            {settingsTab === "pricing" && (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 30 }}>
                    <div>
                        <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, padding: 20, marginBottom: 20 }}>
                            <div style={{ fontSize: 14, fontWeight: 800, marginBottom: 16 }}>Base Pricing Model</div>
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>
                                <div><label style={lSt}>Base Fare (₦)</label><input value={baseFare} onChange={e => setBaseFare(e.target.value)} style={iSt} /></div>
                                <div><label style={lSt}>Per KM Rate (₦)</label><input value={perKm} onChange={e => setPerKm(e.target.value)} style={iSt} /></div>
                            </div>
                            <div style={{ marginBottom: 16 }}><label style={lSt}>Surge Multiplier (x)</label><div style={{ display: "flex", alignItems: "center", gap: 10 }}><input type="range" min="1" max="3" step="0.1" value={surge} onChange={e => setSurge(parseFloat(e.target.value))} style={{ flex: 1 }} /><span style={{ fontSize: 16, fontWeight: 800, color: S.gold, fontFamily: "'Space Mono',monospace" }}>{surge}x</span></div></div>
                            <div style={{ display: "flex", justifyContent: "flex-end" }}><button style={{ padding: "10px 20px", borderRadius: 8, background: S.navy, color: "#fff", fontWeight: 700, fontSize: 13, border: "none", cursor: "pointer" }}>Save Changes</button></div>
                        </div>
                        <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, padding: 20 }}>
                            <div style={{ fontSize: 14, fontWeight: 800, marginBottom: 16 }}>Price Simulator</div>
                            <div style={{ display: "flex", gap: 16, alignItems: "flex-end" }}>
                                <div style={{ flex: 1 }}><label style={lSt}>Distance (KM)</label><input value={testDist} onChange={e => setTestDist(e.target.value)} style={iSt} /></div>
                                <div style={{ fontSize: 24, fontWeight: 800, color: S.green, fontFamily: "'Space Mono',monospace", marginBottom: 4 }}>₦{calcPrice(parseInt(testDist || "0")).toLocaleString()}</div>
                            </div>
                        </div>
                    </div>
                    <div>
                        <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, padding: 20 }}>
                            <div style={{ fontSize: 14, fontWeight: 800, marginBottom: 16 }}>Vehicle Multipliers</div>
                            {[{ l: "Bike", v: "1.0x" }, { l: "Car", v: "1.5x" }, { l: "Van", v: "2.2x" }].map(v => (
                                <div key={v.l} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12, borderBottom: `1px solid ${S.borderLight}`, paddingBottom: 12 }}>
                                    <span style={{ fontWeight: 600 }}>{v.l}</span>
                                    <input defaultValue={v.v} style={{ ...iSt, width: 80, textAlign: "center" }} />
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
            {settingsTab === "zones" && (
                <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, padding: 20 }}>
                    <div style={{ fontSize: 14, fontWeight: 800, marginBottom: 16 }}>Regional Surcharges (₦)</div>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
                        {Object.keys(zP).map(z => (
                            <div key={z}><label style={lSt}>{z.toUpperCase()} EXTRA FEE</label><input type="number" value={zP[z as keyof typeof zP]} onChange={(e: any) => setZP({ ...zP, [z]: parseInt(e.target.value) })} style={iSt} /></div>
                        ))}
                    </div>
                    <div style={{ marginTop: 20, fontSize: 12, color: S.textMuted }}>* These fees are added on top of the base fare for pickups originating in these zones.</div>
                </div>
            )}
            {settingsTab === "dispatch" && (
                <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, padding: 20 }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20, paddingBottom: 20, borderBottom: `1px solid ${S.borderLight}` }}>
                        <div><div style={{ fontSize: 14, fontWeight: 800 }}>Auto-Assign Orders</div><div style={{ fontSize: 12, color: S.textMuted }}>System automatically assigns nearest rider</div></div>
                        <div onClick={() => setAutoDispatch(!autoDispatch)} style={{ width: 46, height: 26, borderRadius: 13, background: autoDispatch ? S.green : S.border, position: "relative", cursor: "pointer", transition: "background 0.2s" }}><div style={{ width: 20, height: 20, borderRadius: "50%", background: "#fff", position: "absolute", top: 3, left: autoDispatch ? 23 : 3, transition: "left 0.2s", boxShadow: "0 1px 3px rgba(0,0,0,0.2)" }} /></div>
                    </div>
                    <div><label style={lSt}>Max Dispatch Radius (KM)</label><input value={maxRadius} onChange={e => setMaxRadius(e.target.value)} style={{ ...iSt, width: 120 }} /><div style={{ fontSize: 11, color: S.textMuted, marginTop: 6 }}>Riders must be within this range to receive requests.</div></div>
                </div>
            )}
            {settingsTab === "notif" && (
                <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, padding: 20 }}>
                    <div style={{ fontSize: 14, fontWeight: 800, marginBottom: 16 }}>Notification Preferences</div>
                    {[
                        { l: "Push Notifications", d: "Receive real-time alerts for new orders" },
                        { l: "Email Alerts", d: "Daily summaries and critical system alerts" },
                        { l: "SMS Updates", d: "Urgent status changes and rider messages" }
                    ].map(n => (
                        <div key={n.l} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16, paddingBottom: 16, borderBottom: `1px solid ${S.borderLight}` }}>
                            <div>
                                <div style={{ fontSize: 13, fontWeight: 600 }}>{n.l}</div>
                                <div style={{ fontSize: 11, color: S.textMuted }}>{n.d}</div>
                            </div>
                            <div style={{ width: 40, height: 22, borderRadius: 11, background: S.green, position: "relative", cursor: "pointer" }}>
                                <div style={{ width: 18, height: 18, borderRadius: "50%", background: "#fff", position: "absolute", top: 2, right: 2, boxShadow: "0 1px 2px rgba(0,0,0,0.1)" }} />
                            </div>
                        </div>
                    ))}
                </div>
            )}
            {settingsTab === "api" && (
                <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, padding: 20 }}>
                    <div style={{ fontSize: 14, fontWeight: 800, marginBottom: 16 }}>API Configuration</div>
                    <div style={{ marginBottom: 20 }}>
                        <label style={lSt}>WEBHOOK URL</label>
                        <input defaultValue="https://api.aexpress.ng/v1/webhooks/dispatch" style={iSt} />
                        <div style={{ fontSize: 11, color: S.textMuted, marginTop: 6 }}>Events will be pushed to this URL</div>
                    </div>
                    <div>
                        <label style={lSt}>API KEY</label>
                        <div style={{ display: "flex", gap: 10 }}>
                            <input value="pk_test_57283948273948..." readOnly style={{ ...iSt, fontFamily: "'Space Mono',monospace", color: S.textMuted }} />
                            <button style={{ padding: "0 16px", borderRadius: 8, border: `1px solid ${S.border}`, background: S.bg, cursor: "pointer", fontWeight: 700, fontSize: 12 }}>Regenerate</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
