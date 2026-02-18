import { useState } from "react";
import type { Merchant } from "../../types";
import { S } from "../common/theme";
import { I } from "../icons";


// Helper function simplified from MerchantPortal
const getMerchantInitials = (name: string) => {
    return name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .substring(0, 2)
        .toUpperCase();
};

interface MerchantsScreenProps {
    data: Merchant[];
}

export function MerchantsScreen({ data }: MerchantsScreenProps) {
    const [searchTerm, setSearchTerm] = useState("");

    const filtered = data.filter(m =>
        m.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        m.phone.includes(searchTerm) ||
        (m.id && m.id.toLowerCase().includes(searchTerm.toLowerCase()))
    );



    return (
        <div style={{ animation: "fadeIn 0.3s ease" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
                <div>
                    <h2 style={{ fontSize: 24, fontWeight: 700, color: S.navy, margin: 0 }}>Merchants</h2>
                    <p style={{ color: S.textMuted, fontSize: 14, margin: "4px 0 0" }}>Manage registered businesses</p>
                </div>
                <div style={{ position: "relative" }}>
                    <input
                        placeholder="Search merchants..."
                        style={{
                            padding: "10px 16px 10px 40px",
                            borderRadius: 10,
                            border: `1px solid ${S.border}`,
                            width: 280,
                            fontFamily: "inherit",
                            fontSize: 14
                        }}
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                    />
                    <div style={{ position: "absolute", left: 14, top: 11, color: S.textMuted }}>{I.search}</div>
                </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))", gap: 20 }}>
                {filtered.map(m => (
                    <div key={m.id} style={{
                        background: "#fff",
                        borderRadius: 14,
                        border: `1px solid ${S.border}`,
                        padding: 20,
                        display: "flex",
                        flexDirection: "column",
                        gap: 16
                    }}>
                        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start" }}>
                            <div style={{ display: "flex", gap: 12 }}>
                                <div style={{
                                    width: 48, height: 48, borderRadius: 12,
                                    background: `linear-gradient(135deg, ${S.navy}, ${S.navyLight})`,
                                    color: S.gold, display: "flex", alignItems: "center", justifyContent: "center",
                                    fontSize: 18, fontWeight: 700
                                }}>
                                    {getMerchantInitials(m.name)}
                                </div>
                                <div>
                                    <div style={{ fontSize: 15, fontWeight: 700, color: S.navy }}>{m.name}</div>
                                    <div style={{ fontSize: 12, color: S.textMuted, marginTop: 2 }}>{m.category || "General"}</div>
                                </div>
                            </div>
                            <div style={{
                                fontSize: 10, fontWeight: 700, padding: "4px 8px", borderRadius: 6,
                                background: m.status === "Active" ? S.greenBg : S.redBg,
                                color: m.status === "Active" ? S.green : S.red
                            }}>
                                {m.status.toUpperCase()}
                            </div>
                        </div>

                        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12, paddingTop: 16, borderTop: `1px solid ${S.borderLight}` }}>
                            <div>
                                <div style={{ fontSize: 11, color: S.textMuted, marginBottom: 4 }}>TOTAL ORDERS</div>
                                <div style={{ fontSize: 16, fontWeight: 700, color: S.navy, fontFamily: "'Space Mono', monospace" }}>{m.totalOrders}</div>
                            </div>
                            <div>
                                <div style={{ fontSize: 11, color: S.textMuted, marginBottom: 4 }}>WALLET</div>
                                <div style={{ fontSize: 16, fontWeight: 700, color: S.navy, fontFamily: "'Space Mono', monospace" }}>₦{m.walletBalance?.toLocaleString()}</div>
                            </div>
                        </div>

                        <div style={{ fontSize: 12, color: S.textDim, display: "flex", flexDirection: "column", gap: 6, paddingTop: 12, borderTop: `1px solid ${S.borderLight}` }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                <span>📱</span> {m.phone}
                            </div>
                            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                <span>🆔</span> {m.id}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
