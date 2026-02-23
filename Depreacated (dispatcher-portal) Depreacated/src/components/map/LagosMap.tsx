import { useState } from "react";
import { S } from "../common/theme";
import type { Order, Rider } from "../../types";

interface LagosMapProps {
    orders: Order[];
    riders: Rider[];
    highlightOrder?: string | null;
    small?: boolean;
    showZones?: boolean;
}

export function LagosMap({ orders, riders, highlightOrder, small, showZones }: LagosMapProps) {
    const [hoverPin, setHoverPin] = useState<string | null>(null);
    const [mapView, setMapView] = useState("live"); // live | zones | heatmap
    const h = small ? 140 : 320;

    // Lagos zones with real approximate positions
    const zones = [
        { id: "mainland-core", label: "Mainland Core", x: 32, y: 32, w: 22, h: 20, color: "rgba(59,130,246,0.08)", areas: "Ikeja · Maryland · Yaba · Surulere" },
        { id: "island", label: "Island", x: 50, y: 48, w: 22, h: 22, color: "rgba(232,168,56,0.08)", areas: "V.I. · Ikoyi · Lekki Phase 1" },
        { id: "lekki-ajah", label: "Lekki-Ajah", x: 74, y: 45, w: 20, h: 18, color: "rgba(139,92,246,0.08)", areas: "Lekki · Ajah · Sangotedo · VGC" },
        { id: "apapa", label: "Apapa/Wharf", x: 16, y: 55, w: 16, h: 16, color: "rgba(239,68,68,0.06)", areas: "Apapa · Tin Can · Wharf" },
        { id: "outer-north", label: "Outer Lagos", x: 10, y: 15, w: 24, h: 18, color: "rgba(16,185,129,0.06)", areas: "Ikorodu · Agbara · Ojo · Badagry" },
    ];

    /* 
       Ideally we would calculate pin positions based on lat/lng, 
       but for this mockup we will use hardcoded positions based on the order ID or similar,
       or just reuse the hardcoded pins from the original file if possible.
       
       The original file had 'pins' hardcoded. To make this dynamic based on the 'orders' prop,
       we need to map orders to coordinates. 
       For now, to strictly follow the migration, I will use a mapping strategy or fallback to the hardcoded logic if I can match IDs.
       
       Actually, looking at the original code, 'pins' variable was hardcoded. 
       However, the component receives 'orders'. 
       The original code logic was: `const pins = [...]`. It didn't seem to use the `orders` prop for positioning logic 
       except for filtering active ones. 
       Wait, in the original code, `pins` seems to be a hardcoded list of specific orders.
       If I want to support dynamic orders, I should map them.
       But to reproduce the exact visual, I will include the hardcoded pins logic but try to link it to the passed orders if they match.
    */

    // Hardcoded positions for the demo orders to match the original visual
    const DEMO_LOCATIONS: Record<string, { px: number, py: number, dx: number, dy: number, label: string }> = {
        "AX-6158260": { px: 36, py: 40, dx: 55, dy: 52, label: "Yaba→VI" },
        "AX-6158261": { px: 38, py: 48, dx: 56, dy: 56, label: "Surulere→VI" },
        "AX-6158262": { px: 30, py: 28, dx: 78, dy: 50, label: "Ikeja→Lekki" },
        "AX-6158263": { px: 26, py: 42, dx: 34, dy: 30, label: "Mushin→Ikeja" },
        "AX-6158258": { px: 55, py: 50, dx: 72, dy: 50, label: "VI→Lekki Ph1" },
        "AX-6158257": { px: 36, py: 40, dx: 54, dy: 52, label: "Yaba→VI" },
        "AX-6158255": { px: 72, py: 48, dx: 76, dy: 52, label: "Lekki→Lekki" },
    };

    const mapOrderToPin = (o: Order) => {
        const loc = DEMO_LOCATIONS[o.id] || { px: 50, py: 50, dx: 50, dy: 50, label: "Unknown" };
        let color = S.gold;
        if (o.status === "Assigned") color = S.blue;
        if (o.status === "Picked Up") color = S.purple;
        if (o.status === "Delivered") color = S.green;
        if (o.status === "Pending") color = S.yellow;

        return {
            id: o.id,
            px: loc.px, py: loc.py, dx: loc.dx, dy: loc.dy,
            label: loc.label,
            color,
            status: o.status,
            rider: o.rider
        };
    };

    const pins = orders.map(mapOrderToPin);

    // Rider positions (simulated mock)
    const riderDots = riders.map((r, i) => {
        // Hardcoded positions matching original riders
        const positions = [
            { x: 48, y: 46 }, { x: 58, y: 50 }, { x: 52, y: 52 }, { x: 10, y: 10 },
            { x: 28, y: 38 }, { x: 30, y: 36 }, { x: 70, y: 44 }, { x: 5, y: 5 }
        ];
        const pos = positions[i] || { x: 50, y: 50 };

        return {
            id: r.id,
            x: pos.x, y: pos.y,
            name: r.name,
            status: r.status,
            vehicle: r.vehicle === "Bike" ? "🏍️" : r.vehicle === "Car" ? "🚗" : "🚐"
        };
    });

    const activeOrders = pins.filter(p => !["Delivered", "Cancelled", "Failed"].includes(p.status));
    const displayPins = highlightOrder ? pins.filter(p => p.id === highlightOrder) : (mapView === "live" ? activeOrders : pins);

    // Helper for safe color usage
    const getPinColor = (p: any) => p.color || S.gold;

    return (
        <div style={{ position: "relative", width: "100%", height: h, borderRadius: 14, overflow: "hidden", border: `1px solid ${S.border}`, background: "#EEF2F7" }}>
            {/* Background map layers */}
            <svg width="100%" height="100%" style={{ position: "absolute", top: 0, left: 0 }} viewBox="0 0 100 100" preserveAspectRatio="none">
                {/* Lagos Lagoon */}
                <path d="M0,68 Q12,62 25,65 Q38,68 45,63 Q52,58 58,62 Q65,66 72,63 Q80,60 88,64 Q94,67 100,65 L100,78 Q88,74 75,77 Q62,80 50,76 Q38,72 25,75 Q12,78 0,75 Z" fill="rgba(59,130,246,0.12)" />
                {/* Atlantic Ocean */}
                <path d="M0,82 Q25,78 50,82 Q75,86 100,80 L100,100 L0,100 Z" fill="rgba(59,130,246,0.18)" />
                {/* Five Cowrie Creek */}
                <path d="M48,45 Q50,48 52,52 Q54,56 52,60 Q50,64 48,68" fill="none" stroke="rgba(59,130,246,0.15)" strokeWidth="1.2" />
                {/* Third Mainland Bridge */}
                <line x1="34" y1="38" x2="52" y2="55" stroke="rgba(232,168,56,0.35)" strokeWidth="0.8" strokeDasharray="2,1" />
                {/* Carter Bridge */}
                <line x1="28" y1="52" x2="42" y2="58" stroke="rgba(232,168,56,0.25)" strokeWidth="0.6" strokeDasharray="2,1" />
                {/* Lekki-Ikoyi Link Bridge */}
                <line x1="58" y1="52" x2="66" y2="48" stroke="rgba(232,168,56,0.25)" strokeWidth="0.6" strokeDasharray="2,1" />
                {/* Major roads */}
                <line x1="8" y1="35" x2="42" y2="35" stroke="rgba(0,0,0,0.05)" strokeWidth="0.6" />
                <line x1="30" y1="15" x2="30" y2="55" stroke="rgba(0,0,0,0.05)" strokeWidth="0.6" />
                <line x1="50" y1="50" x2="95" y2="50" stroke="rgba(0,0,0,0.05)" strokeWidth="0.6" />
                <line x1="30" y1="35" x2="50" y2="50" stroke="rgba(0,0,0,0.04)" strokeWidth="0.5" />
                {/* Express road */}
                <path d="M10,30 Q20,28 30,28 Q45,28 55,35 Q65,42 75,45 Q85,48 95,47" fill="none" stroke="rgba(0,0,0,0.06)" strokeWidth="0.7" />
            </svg>

            {/* Zone overlays */}
            {(mapView === "zones" || showZones) && zones.map(z => (
                <div key={z.id} style={{ position: "absolute", left: `${z.x}%`, top: `${z.y}%`, width: `${z.w}%`, height: `${z.h}%`, background: z.color, border: "1px dashed rgba(0,0,0,0.12)", borderRadius: 8, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", zIndex: 1 }}>
                    <div style={{ fontSize: 7, fontWeight: 800, color: S.navy, opacity: 0.5, textTransform: "uppercase", letterSpacing: "0.5px" }}>{z.label}</div>
                    <div style={{ fontSize: 6, color: S.textMuted, opacity: 0.6, textAlign: "center" }}>{z.areas}</div>
                </div>
            ))}

            {/* Area labels (when no zones) */}
            {mapView !== "zones" && !showZones && !small && <>
                <div style={{ position: "absolute", left: "6%", top: "18%", fontSize: 8, color: "rgba(27,42,74,0.2)", fontWeight: 800, letterSpacing: "1px" }}>IKORODU</div>
                <div style={{ position: "absolute", left: "26%", top: "22%", fontSize: 9, color: "rgba(27,42,74,0.3)", fontWeight: 800, letterSpacing: "1px" }}>IKEJA</div>
                <div style={{ position: "absolute", left: "38%", top: "32%", fontSize: 8, color: "rgba(27,42,74,0.25)", fontWeight: 700 }}>MARYLAND</div>
                <div style={{ position: "absolute", left: "32%", top: "42%", fontSize: 8, color: "rgba(27,42,74,0.2)", fontWeight: 700 }}>YABA</div>
                <div style={{ position: "absolute", left: "14%", top: "50%", fontSize: 8, color: "rgba(27,42,74,0.2)", fontWeight: 700 }}>APAPA</div>
                <div style={{ position: "absolute", left: "32%", top: "50%", fontSize: 8, color: "rgba(27,42,74,0.2)", fontWeight: 700 }}>SURULERE</div>
                <div style={{ position: "absolute", left: "50%", top: "44%", fontSize: 9, color: "rgba(232,168,56,0.5)", fontWeight: 800, letterSpacing: "1px" }}>V.I.</div>
                <div style={{ position: "absolute", left: "56%", top: "55%", fontSize: 8, color: "rgba(27,42,74,0.25)", fontWeight: 700 }}>IKOYI</div>
                <div style={{ position: "absolute", left: "68%", top: "40%", fontSize: 9, color: "rgba(139,92,246,0.4)", fontWeight: 800, letterSpacing: "1px" }}>LEKKI</div>
                <div style={{ position: "absolute", left: "82%", top: "48%", fontSize: 8, color: "rgba(27,42,74,0.2)", fontWeight: 700 }}>AJAH</div>
            </>}

            {/* Route lines */}
            <svg width="100%" height="100%" style={{ position: "absolute", top: 0, left: 0, pointerEvents: "none", zIndex: 4 }} viewBox="0 0 100 100" preserveAspectRatio="none">
                {displayPins.filter(p => !["Delivered", "Cancelled", "Failed"].includes(p.status)).map(p => (
                    <g key={p.id + "route"}>
                        <line x1={p.px} y1={p.py} x2={p.dx} y2={p.dy} stroke={getPinColor(p)} strokeWidth={highlightOrder === p.id ? "0.8" : "0.4"} strokeDasharray="2,2" opacity={highlightOrder === p.id ? 0.8 : 0.4} />
                        {/* Pickup dot */}
                        <circle cx={p.px} cy={p.py} r={highlightOrder === p.id ? 1.5 : 1} fill="#fff" stroke={getPinColor(p)} strokeWidth="0.5" />
                        {/* Dropoff dot */}
                        <circle cx={p.dx} cy={p.dy} r={highlightOrder === p.id ? 1.5 : 1} fill={getPinColor(p)} stroke="#fff" strokeWidth="0.4" />
                    </g>
                ))}
            </svg>

            {/* Order pins */}
            {displayPins.map(p => {
                const isH = highlightOrder === p.id || hoverPin === p.id;
                const cx = p.status === "Delivered" ? p.dx : p.status === "Pending" ? p.px : (p.px + p.dx) / 2;
                const cy = p.status === "Delivered" ? p.dy : p.status === "Pending" ? p.py : (p.py + p.dy) / 2;
                const col = getPinColor(p);

                return (
                    <div key={p.id} onMouseEnter={() => setHoverPin(p.id)} onMouseLeave={() => setHoverPin(null)}
                        style={{ position: "absolute", left: `${cx}%`, top: `${cy}%`, transform: "translate(-50%,-100%)", zIndex: isH ? 15 : 5, cursor: "pointer", transition: "transform 0.15s" }}>
                        <div style={{ width: isH ? 16 : 10, height: isH ? 16 : 10, borderRadius: "50% 50% 50% 0", transform: "rotate(-45deg)", background: col, border: "2px solid #fff", boxShadow: `0 2px 8px ${col}50`, transition: "all 0.15s" }} />
                        {isH && (
                            <div style={{ position: "absolute", top: -40, left: "50%", transform: "translateX(-50%)", background: "#fff", padding: "4px 8px", borderRadius: 6, boxShadow: "0 2px 12px rgba(0,0,0,0.15)", whiteSpace: "nowrap", zIndex: 20, border: `1px solid ${S.border}` }}>
                                <div style={{ fontSize: 9, fontWeight: 800, color: S.navy }}>{p.id.slice(-7)}</div>
                                <div style={{ fontSize: 8, color: col, fontWeight: 700 }}>{p.label}</div>
                                {p.rider && <div style={{ fontSize: 7, color: S.textMuted }}>🏍️ {p.rider}</div>}
                            </div>
                        )}
                        {!small && !isH && <div style={{ position: "absolute", top: -14, left: "50%", transform: "translateX(-50%)", fontSize: 7, fontWeight: 700, color: S.navy, whiteSpace: "nowrap", background: "rgba(255,255,255,0.9)", padding: "1px 4px", borderRadius: 3 }}>{p.id.slice(-3)}</div>}
                    </div>
                );
            })}

            {/* Rider dots */}
            {!highlightOrder && riderDots.map(r => (
                <div key={r.id} style={{ position: "absolute", left: `${r.x}%`, top: `${r.y + 3}%`, zIndex: 6 }}>
                    <div style={{ position: "relative" }}>
                        <div style={{ width: 10, height: 10, borderRadius: "50%", background: r.status === "online" ? S.green : S.gold, border: "2px solid #fff", boxShadow: "0 1px 6px rgba(0,0,0,0.2)" }} />
                        {r.status === "online" && <div style={{ position: "absolute", top: -1, left: -1, width: 12, height: 12, borderRadius: "50%", border: `2px solid ${S.green}`, animation: "pulse 2s infinite", opacity: 0.4 }} />}
                        {!small && <div style={{ position: "absolute", top: 12, left: "50%", transform: "translateX(-50%)", fontSize: 7, fontWeight: 600, color: S.navy, whiteSpace: "nowrap", background: "rgba(255,255,255,0.85)", padding: "1px 4px", borderRadius: 3 }}>{r.vehicle} {r.name}</div>}
                    </div>
                </div>
            ))}

            {/* Bridge labels */}
            {!small && <>
                <div style={{ position: "absolute", left: "40%", top: "45%", fontSize: 6, color: "rgba(232,168,56,0.6)", fontWeight: 700, transform: "rotate(-35deg)", whiteSpace: "nowrap" }}>3rd Mainland Bridge</div>
                <div style={{ position: "absolute", left: "60%", top: "49%", fontSize: 6, color: "rgba(232,168,56,0.5)", fontWeight: 600, whiteSpace: "nowrap" }}>Lekki-Ikoyi Bridge</div>
            </>}

            {/* Map controls */}
            {!small && (
                <div style={{ position: "absolute", top: 8, right: 8, display: "flex", gap: 4, zIndex: 20 }}>
                    {[{ id: "live", label: "Live", icon: "📡" }, { id: "zones", label: "Zones", icon: "🗺️" }, { id: "heatmap", label: "Heat", icon: "🔥" }].map(v => (
                        <button key={v.id} onClick={() => setMapView(v.id)} style={{
                            padding: "4px 8px", borderRadius: 6, border: `1px solid ${mapView === v.id ? S.gold : S.border}`,
                            background: mapView === v.id ? "rgba(232,168,56,0.12)" : "rgba(255,255,255,0.95)",
                            cursor: "pointer", fontSize: 8, fontWeight: 700, color: mapView === v.id ? S.gold : S.textMuted,
                            display: "flex", alignItems: "center", gap: 3, fontFamily: "inherit",
                        }}>{v.icon} {v.label}</button>
                    ))}
                </div>
            )}

            {/* Legend */}
            <div style={{ position: "absolute", bottom: 8, right: 8, display: "flex", gap: 8, background: "rgba(255,255,255,0.95)", padding: "5px 10px", borderRadius: 8, boxShadow: "0 1px 4px rgba(0,0,0,0.08)", zIndex: 10 }}>
                <span style={{ fontSize: 8, color: S.textMuted, display: "flex", alignItems: "center", gap: 3 }}><span style={{ width: 6, height: 6, borderRadius: "50%", background: S.gold }} /> Active</span>
                <span style={{ fontSize: 8, color: S.textMuted, display: "flex", alignItems: "center", gap: 3 }}><span style={{ width: 6, height: 6, borderRadius: "50%", background: S.green }} /> Rider</span>
                <span style={{ fontSize: 8, color: S.textMuted, display: "flex", alignItems: "center", gap: 3 }}><span style={{ width: 6, height: 6, borderRadius: "50% 50% 50% 0", transform: "rotate(-45deg)", background: S.yellow }} /> Pending</span>
                <span style={{ fontSize: 8, color: S.textMuted, display: "flex", alignItems: "center", gap: 3 }}><span style={{ width: 6, height: 6, borderRadius: "50% 50% 50% 0", transform: "rotate(-45deg)", background: S.purple }} /> In Progress</span>
            </div>

            {/* Live stats overlay */}
            {!small && mapView === "live" && (
                <div style={{ position: "absolute", bottom: 8, left: 8, background: "rgba(27,42,74,0.9)", padding: "6px 12px", borderRadius: 8, zIndex: 10 }}>
                    <div style={{ display: "flex", gap: 14 }}>
                        <div style={{ textAlign: "center" }}>
                            <div style={{ fontSize: 14, fontWeight: 800, color: S.gold, fontFamily: "'Space Mono',monospace" }}>{activeOrders.length}</div>
                            <div style={{ fontSize: 7, color: "rgba(255,255,255,0.5)", fontWeight: 600 }}>ACTIVE</div>
                        </div>
                        <div style={{ textAlign: "center" }}>
                            <div style={{ fontSize: 14, fontWeight: 800, color: S.green, fontFamily: "'Space Mono',monospace" }}>{riderDots.filter(r => r.status === "online").length}</div>
                            <div style={{ fontSize: 7, color: "rgba(255,255,255,0.5)", fontWeight: 600 }}>ONLINE</div>
                        </div>
                        <div style={{ textAlign: "center" }}>
                            <div style={{ fontSize: 14, fontWeight: 800, color: "#fff", fontFamily: "'Space Mono',monospace" }}>{riderDots.filter(r => r.status === "on_delivery").length}</div>
                            <div style={{ fontSize: 7, color: "rgba(255,255,255,0.5)", fontWeight: 600 }}>DELIVERING</div>
                        </div>
                    </div>
                </div>
            )}

            {/* Heatmap overlay */}
            {mapView === "heatmap" && !small && (
                <svg width="100%" height="100%" style={{ position: "absolute", top: 0, left: 0, pointerEvents: "none", zIndex: 3 }} viewBox="0 0 100 100" preserveAspectRatio="none">
                    <defs>
                        <radialGradient id="heat1"><stop offset="0%" stopColor="rgba(239,68,68,0.4)" /><stop offset="100%" stopColor="rgba(239,68,68,0)" /></radialGradient>
                        <radialGradient id="heat2"><stop offset="0%" stopColor="rgba(245,158,11,0.35)" /><stop offset="100%" stopColor="rgba(245,158,11,0)" /></radialGradient>
                        <radialGradient id="heat3"><stop offset="0%" stopColor="rgba(16,185,129,0.25)" /><stop offset="100%" stopColor="rgba(16,185,129,0)" /></radialGradient>
                    </defs>
                    <circle cx="53" cy="50" r="15" fill="url(#heat1)" />
                    <circle cx="32" cy="35" r="12" fill="url(#heat2)" />
                    <circle cx="72" cy="48" r="14" fill="url(#heat2)" />
                    <circle cx="20" cy="50" r="8" fill="url(#heat3)" />
                    <circle cx="85" cy="50" r="10" fill="url(#heat3)" />
                </svg>
            )}

            {/* Pulse animation */}
            <style>{`@keyframes pulse { 0%{transform:scale(1);opacity:0.4} 50%{transform:scale(1.8);opacity:0} 100%{transform:scale(1);opacity:0} }`}</style>
        </div>
    );
}
