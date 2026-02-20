import { useState } from "react";
import type { Customer } from "../../types";
import { S } from "../common/theme";
import { I } from "../icons";
import { StatCard } from "../common/StatCard";

export function CustomersScreen({ data }: { data: Customer[] }) {
    const [search, setSearch] = useState("");
    const f = data.filter(c => !search || c.name.toLowerCase().includes(search.toLowerCase()) || c.phone.includes(search) || c.email.toLowerCase().includes(search.toLowerCase()));
    return (
        <div>
            <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
                <StatCard label="Total Customers" value={data.length} />
                <StatCard label="Total Orders" value={data.reduce((s, c) => s + c.totalOrders, 0)} color={S.gold} />
                <StatCard label="Revenue" value={`₦${(data.reduce((s, c) => s + c.totalSpent, 0) / 1e6).toFixed(1)}M`} color={S.gold} />
                <StatCard label="Avg Orders" value={(data.reduce((s, c) => s + c.totalOrders, 0) / data.length).toFixed(1)} color={S.green} />
            </div>
            <div style={{ display: "flex", gap: 10, marginBottom: 14 }}>
                <div style={{ flex: 1, background: S.card, borderRadius: 10, border: `1px solid ${S.border}`, display: "flex", alignItems: "center", gap: 8, padding: "0 12px" }}>
                    <span style={{ opacity: 0.4 }}>{I.search}</span>
                    <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by name, phone, email..." style={{ flex: 1, background: "transparent", border: "none", color: S.text, fontSize: 12, fontFamily: "inherit", height: 38, outline: "none" }} />
                </div>
                <button style={{ display: "flex", alignItems: "center", gap: 6, padding: "0 14px", borderRadius: 10, border: `1px solid ${S.border}`, background: S.card, color: S.textDim, cursor: "pointer", fontSize: 12, fontFamily: "inherit" }}>{I.download} Export</button>
            </div>
            <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, overflow: "hidden" }}>
                <div style={{ display: "grid", gridTemplateColumns: "60px 1fr 110px 1fr 70px 70px 100px 1fr", padding: "10px 16px", background: S.borderLight, fontSize: 10, fontWeight: 700, color: S.textMuted, textTransform: "uppercase", letterSpacing: "0.5px", borderBottom: `1px solid ${S.border}` }}>
                    <span>ID</span><span>Name</span><span>Phone</span><span>Email</span><span>Orders</span><span>Last</span><span>Spent</span><span>Fav Merchant</span>
                </div>
                {f.map(c => (<div key={c.id} style={{ display: "grid", gridTemplateColumns: "60px 1fr 110px 1fr 70px 70px 100px 1fr", padding: "12px 16px", borderBottom: `1px solid ${S.borderLight}`, alignItems: "center", cursor: "pointer", transition: "background 0.12s" }} onMouseEnter={e => e.currentTarget.style.background = S.borderLight} onMouseLeave={e => e.currentTarget.style.background = "transparent"}>
                    <span style={{ fontSize: 11, color: S.textMuted, fontFamily: "'Space Mono',monospace" }}>{c.id}</span>
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <div style={{ width: 30, height: 30, borderRadius: 8, background: S.goldPale, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 10, fontWeight: 800, color: S.gold }}>{c.name.split(" ").map(n => n[0]).join("")}</div>
                        <span style={{ fontSize: 12, fontWeight: 600 }}>{c.name}</span>
                    </div>
                    <span style={{ fontSize: 11, color: S.textDim, fontFamily: "'Space Mono',monospace" }}>{c.phone}</span>
                    <span style={{ fontSize: 11, color: S.textDim }}>{c.email}</span>
                    <span style={{ fontSize: 12, fontWeight: 700, color: S.gold }}>{c.totalOrders}</span>
                    <span style={{ fontSize: 11, color: S.textMuted }}>{c.lastOrder}</span>
                    <span style={{ fontSize: 12, fontWeight: 700, color: S.gold, fontFamily: "'Space Mono',monospace" }}>₦{c.totalSpent.toLocaleString()}</span>
                    <span style={{ fontSize: 11, color: S.textDim }}>{c.favMerchant}</span>
                </div>))}
            </div>
        </div>
    );
}
