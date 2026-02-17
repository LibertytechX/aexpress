import { useState } from "react";
import type { Merchant } from "../../types";
import { S } from "../common/theme";
import { I } from "../icons";
import { StatCard } from "../common/StatCard";

export function MerchantsScreen({ data }: { data: Merchant[] }) {
    const [search, setSearch] = useState("");
    const f = data.filter(m => !search || m.name.toLowerCase().includes(search.toLowerCase()) || m.contact.toLowerCase().includes(search.toLowerCase()));
    return (
        <div>
            <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
                <StatCard label="Total Merchants" value={data.length} />
                <StatCard label="Active" value={data.filter(m => m.status === "Active").length} color={S.green} />
                <StatCard label="This Month" value={data.reduce((s, m) => s + m.monthOrders, 0)} color={S.gold} />
                <StatCard label="Wallet Balance" value={`₦${(data.reduce((s, m) => s + m.walletBalance, 0) / 1000).toFixed(0)}K`} color={S.gold} />
            </div>
            <div style={{ marginBottom: 14, background: S.card, borderRadius: 10, border: `1px solid ${S.border}`, display: "flex", alignItems: "center", gap: 8, padding: "0 12px" }}>
                <span style={{ opacity: 0.4 }}>{I.search}</span>
                <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search merchants..." style={{ flex: 1, background: "transparent", border: "none", color: S.text, fontSize: 12, fontFamily: "inherit", height: 38, outline: "none" }} />
            </div>
            <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, overflow: "hidden" }}>
                <div style={{ display: "grid", gridTemplateColumns: "60px 1fr 1fr 90px 70px 70px 100px 70px 80px", padding: "10px 16px", background: S.borderLight, fontSize: 10, fontWeight: 700, color: S.textMuted, textTransform: "uppercase", letterSpacing: "0.5px", borderBottom: `1px solid ${S.border}` }}>
                    <span>ID</span><span>Business</span><span>Contact</span><span>Category</span><span>Total</span><span>Month</span><span>Wallet</span><span>Status</span><span>Joined</span>
                </div>
                {f.map(m => (<div key={m.id} style={{ display: "grid", gridTemplateColumns: "60px 1fr 1fr 90px 70px 70px 100px 70px 80px", padding: "12px 16px", borderBottom: `1px solid ${S.borderLight}`, alignItems: "center", cursor: "pointer", transition: "background 0.12s" }} onMouseEnter={e => e.currentTarget.style.background = S.borderLight} onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                    <span style={{ fontSize: 11, color: S.textMuted, fontFamily: "'Space Mono',monospace" }}>{m.id}</span>
                    <span style={{ fontSize: 12, fontWeight: 700 }}>{m.name}</span>
                    <div><div style={{ fontSize: 12 }}>{m.contact}</div><div style={{ fontSize: 10, color: S.textMuted, fontFamily: "'Space Mono',monospace" }}>{m.phone}</div></div>
                    <span style={{ fontSize: 11, padding: "2px 8px", borderRadius: 4, background: S.borderLight, color: S.textDim }}>{m.category}</span>
                    <span style={{ fontSize: 12, fontWeight: 600 }}>{m.totalOrders}</span>
                    <span style={{ fontSize: 12, fontWeight: 700, color: S.gold }}>{m.monthOrders}</span>
                    <span style={{ fontSize: 12, fontWeight: 600, color: S.gold, fontFamily: "'Space Mono',monospace" }}>₦{m.walletBalance.toLocaleString()}</span>
                    <span style={{ fontSize: 10, fontWeight: 700, padding: "3px 8px", borderRadius: 6, background: m.status === "Active" ? S.greenBg : S.redBg, color: m.status === "Active" ? S.green : S.red }}>{m.status}</span>
                    <span style={{ fontSize: 11, color: S.textMuted }}>{m.joined}</span>
                </div>))}
            </div>
        </div>
    );
}
