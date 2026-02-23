import { useState } from "react";
import { MSG_RIDER, MSG_CUSTOMER } from "../../data/mockData";
import { S } from "../common/theme";
import { I } from "../icons";

export function MessagingScreen() {
    const [tab, setTab] = useState("riders");
    const [activeId, setActiveId] = useState<string | null>(null);
    const [input, setInput] = useState("");
    const chats = tab === "riders" ? MSG_RIDER : MSG_CUSTOMER;
    const active = activeId ? chats.find(c => c.id === activeId) : null;
    const templates = ["Your order has been picked up. Rider is on the way.", "Rider is ~10 minutes away.", "Slight delay, we apologize.", "Delivered successfully. Thank you!", "Please confirm delivery address."];

    return (
        <div style={{ display: "grid", gridTemplateColumns: "280px 1fr", gap: 0, height: "calc(100vh - 130px)", background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, overflow: "hidden" }}>
            <div style={{ borderRight: `1px solid ${S.border}`, display: "flex", flexDirection: "column" }}>
                <div style={{ display: "flex", borderBottom: `1px solid ${S.border}` }}>
                    {[{ id: "riders", l: "Riders", c: MSG_RIDER.reduce((s, m) => s + m.unread, 0) }, { id: "customers", l: "Customers", c: MSG_CUSTOMER.reduce((s, m) => s + m.unread, 0) }].map(t => (<button key={t.id} onClick={() => { setTab(t.id); setActiveId(null); }} style={{ flex: 1, padding: "12px 0", border: "none", cursor: "pointer", fontFamily: "inherit", fontSize: 12, fontWeight: 600, borderBottom: tab === t.id ? `2px solid ${S.gold}` : "2px solid transparent", color: tab === t.id ? S.gold : S.textMuted, background: "transparent" }}>{t.l}{t.c > 0 && <span style={{ marginLeft: 6, fontSize: 10, padding: "1px 6px", borderRadius: 6, background: S.gold, color: "#fff", fontWeight: 700 }}>{t.c}</span>}</button>))}
                </div>
                <div style={{ flex: 1, overflowY: "auto" }}>
                    {chats.map(ch => (<div key={ch.id} onClick={() => setActiveId(ch.id)} style={{ padding: "12px 14px", borderBottom: `1px solid ${S.borderLight}`, cursor: "pointer", background: activeId === ch.id ? S.goldPale : "transparent", transition: "background 0.12s" }} onMouseEnter={e => { if (activeId !== ch.id) e.currentTarget.style.background = S.borderLight; }} onMouseLeave={e => { if (activeId !== ch.id) e.currentTarget.style.background = "transparent"; }}>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}><span style={{ fontSize: 13, fontWeight: ch.unread ? 700 : 500 }}>{ch.name}</span><span style={{ fontSize: 10, color: S.textMuted }}>{ch.lastTime}</span></div>
                        <div style={{ display: "flex", justifyContent: "space-between" }}><span style={{ fontSize: 11, color: ch.unread ? S.text : S.textMuted, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: 180 }}>{ch.lastMsg}</span>{ch.unread > 0 && <span style={{ fontSize: 9, fontWeight: 700, padding: "2px 6px", borderRadius: 8, background: S.gold, color: "#fff", minWidth: 16, textAlign: "center" }}>{ch.unread}</span>}</div>
                    </div>))}
                </div>
            </div>
            {active ? (<div style={{ display: "flex", flexDirection: "column" }}>
                <div style={{ padding: "12px 18px", borderBottom: `1px solid ${S.border}`, display: "flex", alignItems: "center", gap: 10 }}>
                    <div style={{ width: 34, height: 34, borderRadius: 10, background: S.goldPale, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 800, color: S.gold }}>{active.name.split(" ").map(n => n[0]).join("")}</div>
                    <div><div style={{ fontSize: 14, fontWeight: 700 }}>{active.name}</div><div style={{ fontSize: 10, color: S.textMuted }}>{tab === "riders" ? "Rider" : "Customer"} • {active.id}</div></div>
                </div>
                <div style={{ flex: 1, overflowY: "auto", padding: "14px 18px", display: "flex", flexDirection: "column", gap: 8 }}>
                    {active.messages.map((m, i) => { const d = m.from === "dispatch"; return (<div key={i} style={{ display: "flex", justifyContent: d ? "flex-end" : "flex-start" }}><div style={{ maxWidth: "65%", padding: "10px 14px", borderRadius: 12, borderBottomRightRadius: d ? 4 : 12, borderBottomLeftRadius: d ? 12 : 4, background: d ? S.goldPale : S.borderLight, fontSize: 12, lineHeight: 1.5 }}><div>{m.text}</div><div style={{ fontSize: 9, color: S.textMuted, marginTop: 4, textAlign: d ? "right" : "left" }}>{m.time}</div></div></div>); })}
                </div>
                <div style={{ padding: "8px 18px", borderTop: `1px solid ${S.border}`, display: "flex", gap: 6, overflowX: "auto" }}>
                    {templates.slice(0, 3).map((t, i) => (<button key={i} onClick={() => setInput(t)} style={{ padding: "5px 10px", borderRadius: 6, border: `1px solid ${S.border}`, background: S.borderLight, color: S.textDim, cursor: "pointer", fontFamily: "inherit", fontSize: 10, whiteSpace: "nowrap" }}>{t.substring(0, 30)}...</button>))}
                </div>
                <div style={{ padding: "10px 18px", borderTop: `1px solid ${S.border}`, display: "flex", gap: 8 }}>
                    <input value={input} onChange={e => setInput(e.target.value)} placeholder="Type a message..." style={{ flex: 1, background: S.borderLight, border: `1px solid ${S.border}`, borderRadius: 8, padding: "0 14px", height: 40, color: S.text, fontSize: 12, fontFamily: "inherit", outline: "none" }} />
                    <button style={{ width: 40, height: 40, borderRadius: 8, border: "none", cursor: "pointer", background: `linear-gradient(135deg,${S.gold},${S.goldLight})`, color: S.navy, display: "flex", alignItems: "center", justifyContent: "center" }}>{I.send}</button>
                </div>
            </div>) : (<div style={{ display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column", gap: 8 }}><div style={{ fontSize: 40, opacity: 0.2 }}>💬</div><div style={{ fontSize: 14, color: S.textMuted }}>Select a conversation</div></div>)}
        </div>
    );
}
