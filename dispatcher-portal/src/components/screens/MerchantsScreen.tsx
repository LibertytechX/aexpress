import { useState } from "react";
import type { Merchant, Order } from "../../types";
import { S } from "../common/theme";
import { I } from "../icons";
import { MerchantDetails } from "./MerchantDetails";

interface MerchantsScreenProps {
    data: Merchant[];
    orders?: Order[];
    selectedId?: string | null;
    onSelect?: (id: string) => void;
    onBack?: () => void;
}

export function MerchantsScreen({ data, orders = [], selectedId, onSelect, onBack }: MerchantsScreenProps) {
    const [searchTerm, setSearchTerm] = useState("");

    if (selectedId && onBack) {
        const selected = data.find(m => m.id === selectedId);
        if (selected) {
            return <MerchantDetails merchant={selected} orders={orders} onBack={onBack} />;
        }
    }

    const filtered = data.filter(m =>
        m.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        m.phone.includes(searchTerm) ||
        (m.id && m.id.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    // Calculate Stats
    const totalMerchants = data.length;
    const activeMerchants = data.filter(m => m.status === "Active").length;

    // Calculate This Month Orders (GLOBAL)
    const now = new Date();
    const currentMonth = now.getMonth();
    const currentYear = now.getFullYear();
    const thisMonthOrders = orders.filter(o => {
        const d = new Date(o.created);
        return d.getMonth() === currentMonth && d.getFullYear() === currentYear;
    }).length;

    // Calculate Total Wallet Balance
    const totalWallet = data.reduce((sum, m) => sum + (Number(m.walletBalance) || 0), 0);

    // Helper to get monthly orders per merchant
    const getMerchantMonthOrders = (mid: string) => {
        return orders.filter(o => {
            const d = new Date(o.created);
            return o.merchant === mid && d.getMonth() === currentMonth && d.getFullYear() === currentYear;
        }).length;
    };

    const thSt = { padding: "12px 16px", textAlign: "left" as const, fontSize: 11, color: S.textMuted, textTransform: "uppercase" as const, letterSpacing: "0.5px", fontWeight: 600 };
    const tdSt = { padding: "14px 16px", fontSize: 13, borderBottom: `1px solid ${S.borderLight}`, color: S.navy };

    return (
        <div style={{ animation: "fadeIn 0.3s ease", paddingBottom: 40 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
                <h2 style={{ fontSize: 24, fontWeight: 800, color: S.navy, margin: 0 }}>Merchants</h2>
                <button style={{ display: "flex", alignItems: "center", gap: 6, padding: "10px 18px", background: S.gold, color: S.navy, border: "none", borderRadius: 10, fontSize: 12, fontWeight: 800, cursor: "pointer" }}>
                    {I.plus} New Order
                </button>
            </div>

            {/* Stats Cards */}
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 30 }}>
                {[
                    { l: "TOTAL MERCHANTS", v: totalMerchants, c: S.navy },
                    { l: "ACTIVE", v: activeMerchants, c: S.green },
                    { l: "THIS MONTH", v: thisMonthOrders, c: S.gold },
                    { l: "WALLET BALANCE", v: `₦${totalWallet.toLocaleString()}`, c: S.gold }
                ].map((s, i) => (
                    <div key={i} style={{ background: "#fff", padding: "20px 24px", borderRadius: 14, border: `1px solid ${S.border}`, boxShadow: "0 2px 4px rgba(0,0,0,0.02)" }}>
                        <div style={{ fontSize: 11, fontWeight: 600, color: S.textMuted, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 6 }}>{s.l}</div>
                        <div style={{ fontSize: 24, fontWeight: 800, color: s.c, fontFamily: typeof s.v === 'string' && s.v.startsWith("₦") ? "'Space Mono', monospace" : "inherit" }}>{s.v}</div>
                    </div>
                ))}
            </div>

            {/* Search */}
            <div style={{ position: "relative", marginBottom: 20 }}>
                <input
                    placeholder="Search merchants..."
                    style={{
                        width: "100%",
                        padding: "14px 16px 14px 44px",
                        borderRadius: 12,
                        border: `1px solid ${S.border}`,
                        fontFamily: "inherit",
                        fontSize: 14,
                        background: "#fff"
                    }}
                    value={searchTerm}
                    onChange={e => setSearchTerm(e.target.value)}
                />
                <div style={{ position: "absolute", left: 16, top: 15, color: S.textMuted }}>{I.search}</div>
            </div>

            {/* Table */}
            <div style={{ background: "#fff", borderRadius: 16, border: `1px solid ${S.border}`, overflow: "hidden", boxShadow: "0 4px 12px rgba(0,0,0,0.03)" }}>
                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                    <thead style={{ background: S.bg }}>
                        <tr>
                            <th style={thSt}>ID</th>
                            <th style={thSt}>BUSINESS</th>
                            <th style={thSt}>CONTACT</th>
                            <th style={thSt}>CATEGORY</th>
                            <th style={thSt}>TOTAL</th>
                            <th style={thSt}>MONTH</th>
                            <th style={thSt}>WALLET</th>
                            <th style={thSt}>STATUS</th>
                            <th style={thSt}>JOINED</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filtered.map(m => (
                            <tr key={m.id} onClick={() => onSelect && onSelect(m.id)} style={{ cursor: "pointer", transition: "background 0.1s" }} onMouseEnter={e => e.currentTarget.style.background = S.bg} onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                                <td style={{ ...tdSt, fontFamily: "'Space Mono', monospace", fontWeight: 600, color: S.textMuted }}>{m.id}</td>
                                <td style={tdSt}>
                                    <div style={{ fontWeight: 700 }}>{m.name}</div>
                                </td>
                                <td style={tdSt}>
                                    <div style={{ fontWeight: 600 }}>{m.contact || m.name.split(" ")[0]}</div>
                                    <div style={{ fontSize: 11, color: S.textMuted }}>{m.phone}</div>
                                </td>
                                <td style={tdSt}>
                                    <span style={{ padding: "4px 10px", borderRadius: 6, background: S.bg, fontSize: 11, fontWeight: 600, color: S.textDim }}>{m.category || "General"}</span>
                                </td>
                                <td style={{ ...tdSt, fontFamily: "'Space Mono', monospace", fontWeight: 700 }}>{m.totalOrders}</td>
                                <td style={{ ...tdSt, fontFamily: "'Space Mono', monospace", fontWeight: 700, color: S.gold }}>{getMerchantMonthOrders(m.id)}</td>
                                <td style={{ ...tdSt, fontFamily: "'Space Mono', monospace", fontWeight: 700, color: S.gold }}>₦{m.walletBalance?.toLocaleString()}</td>
                                <td style={tdSt}>
                                    <span style={{
                                        padding: "4px 8px", borderRadius: 6, fontSize: 11, fontWeight: 700,
                                        background: m.status === "Active" ? S.greenBg : S.redBg,
                                        color: m.status === "Active" ? S.green : S.red
                                    }}>
                                        {m.status.toUpperCase()}
                                    </span>
                                </td>
                                <td style={{ ...tdSt, color: S.textMuted, fontSize: 12 }}>{new Date(m.joined).toLocaleDateString([], { month: 'short', year: 'numeric' })}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {filtered.length === 0 && <div style={{ padding: 40, textAlign: "center", color: S.textMuted }}>No merchants found matching "{searchTerm}"</div>}
            </div>
        </div>
    );
}
