import { useState } from "react";
import { S } from "../common/theme";

// ─── LAGOS MAP COMPONENT (Enhanced with zones & routes) ─────────
export function LagosMap({ orders, riders, highlightOrder, small, showZones, relayNodes, zones, mode }: any) {
    const [hoverPin, setHoverPin] = useState<string | null>(null);
    const [mapView, setMapView] = useState("live"); // live | zones | heatmap
    const h = small ? 140 : 320;

    const isRelayMode = mode === "relay";

    // Lagos bounding box: lat 6.38–6.70, lng 3.10–3.75
    const latMin = 6.38, latMax = 6.70, lngMin = 3.10, lngMax = 3.75;
    const toPct = (lat: number, lng: number) => {
        const xPct = ((lng - lngMin) / (lngMax - lngMin)) * 100;
        const yPct = ((latMax - lat) / (latMax - latMin)) * 100;
        return { xPct, yPct };
    };
    const kmToPctRadius = (km: number, atLat: number) => {
        const latDeg = km / 111;
        const cos = Math.cos((parseFloat(atLat as any) || 0) * Math.PI / 180) || 0.00001;
        const lngDeg = km / (111 * cos);
        const rx = (lngDeg / (lngMax - lngMin)) * 100;
        const ry = (latDeg / (latMax - latMin)) * 100;
        return { rx, ry };
    };

    // Mock zones (used in legacy/non-relay views)
    const mockZones = [
        { id: "mainland-core", label: "Mainland Core", x: 32, y: 32, w: 22, h: 20, color: "rgba(59,130,246,0.08)", areas: "Ikeja · Maryland · Yaba · Surulere" },
        { id: "island", label: "Island", x: 50, y: 48, w: 22, h: 22, color: "rgba(232,168,56,0.08)", areas: "V.I. · Ikoyi · Lekki Phase 1" },
        { id: "lekki-ajah", label: "Lekki-Ajah", x: 74, y: 45, w: 20, h: 18, color: "rgba(139,92,246,0.08)", areas: "Lekki · Ajah · Sangotedo · VGC" },
        { id: "apapa", label: "Apapa/Wharf", x: 16, y: 55, w: 16, h: 16, color: "rgba(239,68,68,0.06)", areas: "Apapa · Tin Can · Wharf" },
        { id: "outer-north", label: "Outer Lagos", x: 10, y: 15, w: 24, h: 18, color: "rgba(16,185,129,0.06)", areas: "Ikorodu · Agbara · Ojo · Badagry" },
    ];

    // Mock order pins (used in legacy/non-relay views)
    const mockPins = [
        { id: "AX-6158260", px: 36, py: 40, dx: 55, dy: 52, label: "Yaba→VI", color: S.gold, status: "In Transit", rider: "Musa K." },
        { id: "AX-6158261", px: 38, py: 48, dx: 56, dy: 56, label: "Surulere→VI", color: S.purple, status: "Picked Up", rider: "Chinedu O." },
        { id: "AX-6158262", px: 30, py: 28, dx: 78, dy: 50, label: "Ikeja→Lekki", color: S.yellow, status: "Pending", rider: null },
        { id: "AX-6158263", px: 26, py: 42, dx: 34, dy: 30, label: "Mushin→Ikeja", color: S.blue, status: "Assigned", rider: "Kola A." },
        { id: "AX-6158258", px: 55, py: 50, dx: 72, dy: 50, label: "VI→Lekki Ph1", color: S.gold, status: "Assigned", rider: "Ahmed B." },
        { id: "AX-6158257", px: 36, py: 40, dx: 54, dy: 52, label: "Yaba→VI", color: S.green, status: "Delivered", rider: "Musa K." },
        { id: "AX-6158255", px: 72, py: 48, dx: 76, dy: 52, label: "Lekki→Lekki", color: S.green, status: "Delivered", rider: "Emeka N." },
    ];
    const mockRiderDots = [
        { id: "R001", x: 48, y: 46, name: "Musa K.", status: "on_delivery", vehicle: "🏍️" },
        { id: "R002", x: 58, y: 50, name: "Ahmed B.", status: "on_delivery", vehicle: "🏍️" },
        { id: "R003", x: 52, y: 52, name: "Chinedu O.", status: "on_delivery", vehicle: "🚗" },
        { id: "R005", x: 28, y: 38, name: "Ibrahim S.", status: "online", vehicle: "🏍️" },
        { id: "R006", x: 30, y: 36, name: "Kola A.", status: "on_delivery", vehicle: "🚗" },
        { id: "R007", x: 70, y: 44, name: "Emeka N.", status: "online", vehicle: "🏍️" },
    ];

    // In relay mode we do not show mock orders/riders at all.
    const pins = isRelayMode ? [] : mockPins;
    const riderDots = isRelayMode ? [] : mockRiderDots;
    const zonesToRender = isRelayMode ? (Array.isArray(zones) ? zones : []) : mockZones;

    const activeOrders = pins.filter(p => !["Delivered", "Cancelled", "Failed"].includes(p.status));
    const displayPins = highlightOrder ? pins.filter(p => p.id === highlightOrder) : (mapView === "live" ? activeOrders : pins);

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
            {(mapView === "zones" || showZones) && !isRelayMode && zonesToRender.map((z: any) => (
                <div key={z.id} style={{ position: "absolute", left: `${z.x}%`, top: `${z.y}%`, width: `${z.w}%`, height: `${z.h}%`, background: z.color, border: "1px dashed rgba(0,0,0,0.12)", borderRadius: 8, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", zIndex: 1 }}>
                    <div style={{ fontSize: 7, fontWeight: 800, color: S.navy, opacity: 0.5, textTransform: "uppercase", letterSpacing: "0.5px" }}>{z.label}</div>
                    <div style={{ fontSize: 6, color: S.textMuted, opacity: 0.6, textAlign: "center" }}>{z.areas}</div>
                </div>
            ))}
            {(mapView === "zones" || showZones) && isRelayMode && zonesToRender.length > 0 && (
                <svg width="100%" height="100%" style={{ position: "absolute", top: 0, left: 0, pointerEvents: "none", zIndex: 2 }} viewBox="0 0 100 100" preserveAspectRatio="none">
                    {zonesToRender.map((z: any, idx: number) => {
                        const lat = parseFloat(z.center_lat);
                        const lng = parseFloat(z.center_lng);
                        const rkm = parseFloat(z.radius_km);
                        if ([lat, lng, rkm].some(n => isNaN(n))) return null;
                        const { xPct, yPct } = toPct(lat, lng);
                        const { rx, ry } = kmToPctRadius(rkm, lat);
                        const fill = ["rgba(59,130,246,0.10)", "rgba(232,168,56,0.10)", "rgba(16,185,129,0.10)", "rgba(139,92,246,0.10)", "rgba(239,68,68,0.08)"][idx % 5];
                        const stroke = ["rgba(59,130,246,0.40)", "rgba(232,168,56,0.45)", "rgba(16,185,129,0.40)", "rgba(139,92,246,0.40)", "rgba(239,68,68,0.35)"][idx % 5];
                        return (
                            <g key={z.id || z.name || idx}>
                                <ellipse cx={xPct} cy={yPct} rx={rx} ry={ry} fill={fill} stroke={stroke} strokeWidth="0.6" strokeDasharray="2,2" />
                                <circle cx={xPct} cy={yPct} r="0.8" fill={stroke} opacity="0.7" />
                                {!small && <text x={xPct} y={yPct} textAnchor="middle" dominantBaseline="central" fontSize="2.6" fill={stroke} style={{ fontWeight: 800 }}>{(z.name || "").slice(0, 18)}</text>}
                            </g>
                        );
                    })}
                </svg>
            )}

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

            {/* Route lines (pickup → current position for active, or pickup → dropoff) */}
            {!isRelayMode && (
                <svg width="100%" height="100%" style={{ position: "absolute", top: 0, left: 0, pointerEvents: "none", zIndex: 4 }} viewBox="0 0 100 100" preserveAspectRatio="none">
                    {displayPins.filter((p: any) => !["Delivered", "Cancelled", "Failed"].includes(p.status)).map((p: any) => (
                        <g key={p.id + "route"}>
                            <line x1={p.px} y1={p.py} x2={p.dx} y2={p.dy} stroke={p.color} strokeWidth={highlightOrder === p.id ? "0.8" : "0.4"} strokeDasharray="2,2" opacity={highlightOrder === p.id ? 0.8 : 0.4} />
                            {/* Pickup dot */}
                            <circle cx={p.px} cy={p.py} r={highlightOrder === p.id ? 1.5 : 1} fill="#fff" stroke={p.color} strokeWidth="0.5" />
                            {/* Dropoff dot */}
                            <circle cx={p.dx} cy={p.dy} r={highlightOrder === p.id ? 1.5 : 1} fill={p.color} stroke="#fff" strokeWidth="0.4" />
                        </g>
                    ))}
                </svg>
            )}

            {/* Order pins */}
            {!isRelayMode && displayPins.map((p: any) => {
                const isH = highlightOrder === p.id || hoverPin === p.id;
                const cx = p.status === "Delivered" ? p.dx : p.status === "Pending" ? p.px : (p.px + p.dx) / 2;
                const cy = p.status === "Delivered" ? p.dy : p.status === "Pending" ? p.py : (p.py + p.dy) / 2;
                return (
                    <div key={p.id} onMouseEnter={() => setHoverPin(p.id)} onMouseLeave={() => setHoverPin(null)}
                        style={{ position: "absolute", left: `${cx}%`, top: `${cy}%`, transform: "translate(-50%,-100%)", zIndex: isH ? 15 : 5, cursor: "pointer", transition: "transform 0.15s" }}>
                        <div style={{ width: isH ? 16 : 10, height: isH ? 16 : 10, borderRadius: "50% 50% 50% 0", transform: "rotate(-45deg)", background: p.color, border: "2px solid #fff", boxShadow: `0 2px 8px ${p.color}50`, transition: "all 0.15s" }} />
                        {isH && (
                            <div style={{ position: "absolute", top: -40, left: "50%", transform: "translateX(-50%)", background: "#fff", padding: "4px 8px", borderRadius: 6, boxShadow: "0 2px 12px rgba(0,0,0,0.15)", whiteSpace: "nowrap", zIndex: 20, border: `1px solid ${S.border}` }}>
                                <div style={{ fontSize: 9, fontWeight: 800, color: S.navy }}>{p.id.slice(-7)}</div>
                                <div style={{ fontSize: 8, color: p.color, fontWeight: 700 }}>{p.label}</div>
                                {p.rider && <div style={{ fontSize: 7, color: S.textMuted }}>🏍️ {p.rider}</div>}
                            </div>
                        )}
                        {!small && !isH && <div style={{ position: "absolute", top: -14, left: "50%", transform: "translateX(-50%)", fontSize: 7, fontWeight: 700, color: S.navy, whiteSpace: "nowrap", background: "rgba(255,255,255,0.9)", padding: "1px 4px", borderRadius: 3 }}>{p.id.slice(-3)}</div>}
                    </div>
                );
            })}

            {/* Rider dots */}
            {!isRelayMode && !highlightOrder && riderDots.map((r: any) => (
                <div key={r.id} style={{ position: "absolute", left: `${r.x}%`, top: `${r.y + 3}%`, zIndex: 6 }}>
                    <div style={{ position: "relative" }}>
                        <div style={{ width: 10, height: 10, borderRadius: "50%", background: r.status === "online" ? S.green : S.gold, border: "2px solid #fff", boxShadow: "0 1px 6px rgba(0,0,0,0.2)" }} />
                        {r.status === "online" && <div style={{ position: "absolute", top: -1, left: -1, width: 12, height: 12, borderRadius: "50%", border: `2px solid ${S.green}`, animation: "pulse 2s infinite", opacity: 0.4 }} />}
                        {!small && <div style={{ position: "absolute", top: 12, left: "50%", transform: "translateX(-50%)", fontSize: 7, fontWeight: 600, color: S.navy, whiteSpace: "nowrap", background: "rgba(255,255,255,0.85)", padding: "1px 4px", borderRadius: 3 }}>{r.vehicle} {r.name}</div>}
                    </div>
                </div>
            ))}

            {/* Relay node pins */}
            {relayNodes && relayNodes.map((nd: any) => {
                // Map real Lagos lat/lng to approximate SVG viewport coordinates.
                const { xPct, yPct } = toPct(nd.latitude, nd.longitude);
                return (
                    <div key={nd.id} style={{ position: "absolute", left: `${xPct}%`, top: `${yPct}%`, transform: "translate(-50%,-50%)", zIndex: 12 }}>
                        <div title={`${nd.name}\n${nd.address || ""}`} style={{ width: 14, height: 14, borderRadius: "50%", background: "#8B5CF6", border: "2.5px solid #fff", boxShadow: "0 2px 6px rgba(139,92,246,0.6)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 7, color: "#fff", fontWeight: 800 }}>⬡</div>
                        {!small && <div style={{ position: "absolute", top: 15, left: "50%", transform: "translateX(-50%)", fontSize: 6, fontWeight: 700, color: "#8B5CF6", whiteSpace: "nowrap", background: "rgba(255,255,255,0.9)", padding: "1px 4px", borderRadius: 3, maxWidth: 60, overflow: "hidden", textOverflow: "ellipsis" }}>{nd.name}</div>}
                    </div>
                );
            })}

            {/* Bridge labels */}
            {!small && <>
                <div style={{ position: "absolute", left: "40%", top: "45%", fontSize: 6, color: "rgba(232,168,56,0.6)", fontWeight: 700, transform: "rotate(-35deg)", whiteSpace: "nowrap" }}>3rd Mainland Bridge</div>
                <div style={{ position: "absolute", left: "60%", top: "49%", fontSize: 6, color: "rgba(232,168,56,0.5)", fontWeight: 600, whiteSpace: "nowrap" }}>Lekki-Ikoyi Bridge</div>
            </>}

            {/* Map controls */}
            {!isRelayMode && !small && (
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
                {!isRelayMode && <>
                    <span style={{ fontSize: 8, color: S.textMuted, display: "flex", alignItems: "center", gap: 3 }}><span style={{ width: 6, height: 6, borderRadius: "50%", background: S.gold }} /> Active</span>
                    <span style={{ fontSize: 8, color: S.textMuted, display: "flex", alignItems: "center", gap: 3 }}><span style={{ width: 6, height: 6, borderRadius: "50%", background: S.green }} /> Rider</span>
                    <span style={{ fontSize: 8, color: S.textMuted, display: "flex", alignItems: "center", gap: 3 }}><span style={{ width: 6, height: 6, borderRadius: "50% 50% 50% 0", transform: "rotate(-45deg)", background: S.yellow }} /> Pending</span>
                    <span style={{ fontSize: 8, color: S.textMuted, display: "flex", alignItems: "center", gap: 3 }}><span style={{ width: 6, height: 6, borderRadius: "50% 50% 50% 0", transform: "rotate(-45deg)", background: S.purple }} /> In Progress</span>
                </>}
                {isRelayMode && zonesToRender.length > 0 && <span style={{ fontSize: 8, color: S.textMuted, display: "flex", alignItems: "center", gap: 3 }}><span style={{ width: 10, height: 6, borderRadius: 6, border: "1px dashed rgba(59,130,246,0.55)", background: "rgba(59,130,246,0.10)" }} /> Zone</span>}
                {relayNodes && relayNodes.length > 0 && <span style={{ fontSize: 8, color: S.textMuted, display: "flex", alignItems: "center", gap: 3 }}><span style={{ width: 6, height: 6, borderRadius: "50%", background: "#8B5CF6" }} /> Relay Hub</span>}
            </div>

            {/* Live stats overlay */}
            {!isRelayMode && !small && mapView === "live" && (
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
            {!isRelayMode && mapView === "heatmap" && !small && (
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
