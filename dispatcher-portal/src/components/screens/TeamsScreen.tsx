"use client";
import { useState } from "react";
import { S } from "../common/theme";
import { I } from "../icons";
import { useDispatcher } from "@/contexts/DispatcherContext";
import { DispatchersAPI } from "@/lib/api";

export function TeamsScreen() {
    const { dispatchers } = useDispatcher();
    const [search, setSearch] = useState("");
    const [showAdd, setShowAdd] = useState(false);

    // Quick Add State
    const [newName, setNewName] = useState("");
    const [newPhone, setNewPhone] = useState("");
    const [newRole, setNewRole] = useState("dispatcher");
    const [addLoading, setAddLoading] = useState(false);
    const [addErr, setAddErr] = useState("");

    const displayTeams = dispatchers.filter(d =>
        (d.name || d.contact_name || "").toLowerCase().includes(search.toLowerCase()) ||
        (d.phone || "").includes(search)
    );

    const admins = displayTeams.filter(d => d.role === "admin");
    const ops = displayTeams.filter(d => d.role !== "admin");

    const handleInvite = async () => {
        if (!newName || !newPhone) return;
        setAddLoading(true);
        setAddErr("");
        try {
            await DispatchersAPI.create({ contact_name: newName, phone: newPhone, role: newRole, business_name: "AExpress Node " + Math.floor(Math.random() * 100) });
            setNewName("");
            setNewPhone("");
            setShowAdd(false);
            // In a real app we'd refresh the list here via context trigger
            alert("Dispatcher invited successfully");
        } catch (e: any) {
            setAddErr(e?.message || "Failed to invite");
        } finally {
            setAddLoading(false);
        }
    };

    return (
        <div style={{ animation: "fadeIn 0.2s ease-out" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", marginBottom: 24 }}>
                <div>
                    <h1 style={{ fontSize: 24, fontWeight: 800, color: S.navy, margin: "0 0 8px 0" }}>Team Directory</h1>
                    <div style={{ fontSize: 13, color: S.textDim }}>{dispatchers.length} active members</div>
                </div>
                <button onClick={() => setShowAdd(!showAdd)} style={{ padding: "10px 16px", borderRadius: 8, background: S.navy, color: "#fff", border: "none", fontSize: 13, fontWeight: 700, display: "flex", alignItems: "center", gap: 8, cursor: "pointer", transition: "all 0.2s" }}>
                    {showAdd ? "Cancel" : <>{I.plus} Invite Member</>}
                </button>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: showAdd ? "1fr 300px" : "1fr", gap: 20, alignItems: "start", transition: "all 0.3s" }}>

                <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                    <div style={{ position: "relative" }}>
                        <div style={{ position: "absolute", left: 16, top: "50%", transform: "translateY(-50%)", color: S.textMuted }}>{I.search}</div>
                        <input
                            type="text"
                            placeholder="Search by name or phone..."
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                            style={{ width: "100%", padding: "14px 16px 14px 44px", borderRadius: 12, border: `1px solid ${S.border}`, background: S.card, fontSize: 14, fontFamily: "inherit", outline: "none", boxShadow: "0 2px 8px rgba(0,0,0,0.02)" }}
                        />
                    </div>

                    {/* Admins Section */}
                    {admins.length > 0 && (
                        <div>
                            <div style={{ fontSize: 11, fontWeight: 800, color: S.textMuted, textTransform: "uppercase", letterSpacing: "1px", marginBottom: 10, marginLeft: 4 }}>Administrators</div>
                            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 12 }}>
                                {admins.map(d => (
                                    <div key={d.id} style={{ padding: 16, borderRadius: 12, border: `1px solid ${S.border}`, background: S.card, display: "flex", alignItems: "center", gap: 14 }}>
                                        <div style={{ width: 44, height: 44, borderRadius: "50%", background: S.blueBg, color: S.blue, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16, fontWeight: 800 }}>
                                            {(d.name || d.contact_name || "A")[0].toUpperCase()}
                                        </div>
                                        <div>
                                            <div style={{ fontSize: 15, fontWeight: 700, color: S.navy, display: "flex", alignItems: "center", gap: 6 }}>
                                                {d.name || d.contact_name}
                                                <div style={{ padding: "2px 6px", borderRadius: 4, background: S.blueBg, color: S.blue, fontSize: 9, fontWeight: 800, textTransform: "uppercase" }}>Admin</div>
                                            </div>
                                            <div style={{ fontSize: 12, color: S.textMuted, marginTop: 4, fontFamily: "'Space Mono',monospace" }}>{d.phone}</div>
                                            <div style={{ fontSize: 11, color: S.textDim, marginTop: 2 }}>{d.email || "No email"}</div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Dispatchers Section */}
                    {ops.length > 0 && (
                        <div style={{ marginTop: 8 }}>
                            <div style={{ fontSize: 11, fontWeight: 800, color: S.textMuted, textTransform: "uppercase", letterSpacing: "1px", marginBottom: 10, marginLeft: 4 }}>Operations / Dispatchers</div>
                            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 12 }}>
                                {ops.map(d => (
                                    <div key={d.id} style={{ padding: 16, borderRadius: 12, border: `1px solid ${S.border}`, background: S.card, display: "flex", alignItems: "center", gap: 14 }}>
                                        <div style={{ width: 44, height: 44, borderRadius: "50%", background: S.bg, color: S.textDim, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16, fontWeight: 800 }}>
                                            {(d.name || d.contact_name || "D")[0].toUpperCase()}
                                        </div>
                                        <div>
                                            <div style={{ fontSize: 15, fontWeight: 700, color: S.navy }}>{d.name || d.contact_name}</div>
                                            <div style={{ fontSize: 12, color: S.textMuted, marginTop: 4, fontFamily: "'Space Mono',monospace" }}>{d.phone}</div>
                                            <div style={{ fontSize: 11, color: S.textDim, marginTop: 2 }}>{d.email || "No email"}</div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {displayTeams.length === 0 && (
                        <div style={{ textAlign: "center", padding: "60px 20px", color: S.textMuted, background: S.card, borderRadius: 12, border: `1px dashed ${S.border}` }}>
                            <div style={{ fontSize: 32, marginBottom: 12 }}>👥</div>
                            <div style={{ fontSize: 14, fontWeight: 600 }}>No team members found</div>
                            <div style={{ fontSize: 13, color: S.textDim }}>Try adjusting your search criteria</div>
                        </div>
                    )}
                </div>

                {/* Add Member Panel */}
                {showAdd && (
                    <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, padding: 20, animation: "slideInRight 0.2s ease-out" }}>
                        <div style={{ fontSize: 14, fontWeight: 800, color: S.navy, marginBottom: 16, borderBottom: `1px solid ${S.borderLight}`, paddingBottom: 12 }}>Invite New Member</div>

                        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                            <div>
                                <div style={{ fontSize: 11, fontWeight: 600, color: S.textMuted, marginBottom: 6 }}>Full Name</div>
                                <input type="text" value={newName} onChange={e => setNewName(e.target.value)} placeholder="e.g. Jane Doe" style={{ width: "100%", padding: "10px 12px", borderRadius: 8, border: `1px solid ${S.border}`, fontSize: 13, outline: "none" }} />
                            </div>
                            <div>
                                <div style={{ fontSize: 11, fontWeight: 600, color: S.textMuted, marginBottom: 6 }}>Phone Number</div>
                                <input type="text" value={newPhone} onChange={e => setNewPhone(e.target.value)} placeholder="080..." style={{ width: "100%", padding: "10px 12px", borderRadius: 8, border: `1px solid ${S.border}`, fontSize: 13, fontFamily: "'Space Mono',monospace", outline: "none" }} />
                            </div>
                            <div>
                                <div style={{ fontSize: 11, fontWeight: 600, color: S.textMuted, marginBottom: 6 }}>Role</div>
                                <select value={newRole} onChange={e => setNewRole(e.target.value)} style={{ width: "100%", padding: "10px 12px", borderRadius: 8, border: `1px solid ${S.border}`, fontSize: 13, outline: "none", background: "#fff", cursor: "pointer" }}>
                                    <option value="dispatcher">Dispatcher</option>
                                    <option value="admin">Administrator</option>
                                </select>
                            </div>

                            {addErr && <div style={{ fontSize: 11, color: S.red, background: S.redBg, padding: 8, borderRadius: 6 }}>{addErr}</div>}

                            <button onClick={handleInvite} disabled={addLoading || !newName || !newPhone} style={{ width: "100%", padding: "12px", borderRadius: 8, background: S.navy, color: "#fff", border: "none", fontSize: 13, fontWeight: 700, cursor: addLoading || !newName || !newPhone ? "not-allowed" : "pointer", opacity: addLoading || !newName || !newPhone ? 0.6 : 1, marginTop: 8 }}>
                                {addLoading ? "Inviting..." : "Send Invite"}
                            </button>
                        </div>
                    </div>
                )}

            </div>
        </div>
    );
}
