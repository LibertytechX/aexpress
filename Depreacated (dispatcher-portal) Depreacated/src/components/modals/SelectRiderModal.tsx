import { useState } from "react";
import type { Rider } from "../../types";
import { S } from "../common/theme";
import { I } from "../icons";

interface SelectRiderModalProps {
    riders: Rider[];
    onClose: () => void;
    onSelect: (riderId: string) => void;
}

export function SelectRiderModal({ riders, onClose, onSelect }: SelectRiderModalProps) {
    const [search, setSearch] = useState("");
    const [filter, setFilter] = useState("all"); // all, online, active

    const filtered = riders.filter(r => {
        if (filter === "online" && r.status !== "online") return false;
        if (filter === "active" && r.currentOrder) return false;
        if (search) {
            const s = search.toLowerCase();
            return r.name.toLowerCase().includes(s) || r.vehicle.toLowerCase().includes(s);
        }
        return true;
    });

    return (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 2000 }} onClick={onClose}>
            <div onClick={e => e.stopPropagation()} style={{ background: S.card, borderRadius: 16, border: `1px solid ${S.border}`, width: 440, maxHeight: "80vh", display: "flex", flexDirection: "column", boxShadow: "0 24px 64px rgba(0,0,0,0.15)" }}>
                <div style={{ padding: "16px 20px", borderBottom: `1px solid ${S.border}`, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <h3 style={{ fontSize: 16, fontWeight: 700, margin: 0 }}>Select Rider</h3>
                    <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", color: S.textMuted }}>{I.x}</button>
                </div>

                <div style={{ padding: "12px 20px", borderBottom: `1px solid ${S.border}`, display: "flex", gap: 10 }}>
                    <input autoFocus placeholder="Search riders..." value={search} onChange={e => setSearch(e.target.value)} style={{ flex: 1, padding: "8px 12px", borderRadius: 8, border: `1px solid ${S.border}`, background: S.bg, color: S.text, fontSize: 13 }} />
                    <select value={filter} onChange={e => setFilter(e.target.value)} style={{ padding: "8px", borderRadius: 8, border: `1px solid ${S.border}`, background: S.bg, color: S.text, fontSize: 13 }}>
                        <option value="all">All Riders</option>
                        <option value="online">Online</option>
                        <option value="active">Available (Online & Free)</option>
                    </select>
                </div>

                <div style={{ flex: 1, overflowY: "auto", padding: "8px 0" }}>
                    {filtered.map(r => (
                        <div key={r.id} onClick={() => onSelect(r.id)} style={{ padding: "10px 20px", borderBottom: `1px solid ${S.borderLight}`, cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "space-between", transition: "background 0.1s" }} onMouseEnter={e => e.currentTarget.style.background = S.borderLight} onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                                <div style={{ width: 36, height: 36, borderRadius: 8, background: S.goldPale, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, fontWeight: 700, color: S.gold }}>{r.name.charAt(0)}</div>
                                <div>
                                    <div style={{ fontSize: 13, fontWeight: 600 }}>{r.name}</div>
                                    <div style={{ fontSize: 11, color: S.textMuted }}>{r.vehicle} • {r.phone}</div>
                                </div>
                            </div>
                            <div style={{ textAlign: "right" }}>
                                <div style={{ fontSize: 11, fontWeight: 600, color: r.status === "online" ? S.green : S.textMuted }}>{r.status}</div>
                                {r.currentOrder && <div style={{ fontSize: 10, color: S.gold }}>Busy</div>}
                            </div>
                        </div>
                    ))}
                    {filtered.length === 0 && <div style={{ padding: 40, textAlign: "center", fontSize: 13, color: S.textMuted }}>No riders found</div>}
                </div>
            </div>
        </div>
    );
}
