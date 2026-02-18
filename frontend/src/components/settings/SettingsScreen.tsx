'use client';

import React, { useState } from 'react';
import { S } from '@/lib/theme';
import AddStaffModal from './AddStaffModal';

export default function SettingsScreen() {
  const [activeTab, setActiveTab] = useState('staff'); // staff, terminals, settings
  const [showAddStaff, setShowAddStaff] = useState(false);
  const [staff, setStaff] = useState([
    { id: 1, name: "Blessing Okonkwo", role: "Manager", branch: "Seeds & Pennies HQ", pin: "****", status: "active", sales: 12, revenue: 154000, lastLogin: "Online now" },
    { id: 2, name: "Emmanuel Ade", role: "Cashier", branch: "Seeds & Pennies Lekki", pin: "****", status: "active", sales: 45, revenue: 89000, lastLogin: "12m ago" },
    { id: 3, name: "Chioma Eze", role: "Supervisor", branch: "Liberty Assured Ikeja", pin: "****", status: "inactive", sales: 0, revenue: 0, lastLogin: "2d ago" },
  ]);

  const handleAddStaff = (newStaff) => {
    setStaff([...staff, { ...newStaff, id: Date.now(), status: 'active', sales: 0, revenue: 0, lastLogin: 'Never' }]);
  };

  return (
    <div style={{ animation: "fadeIn 0.3s ease" }}>
      {/* Tabs */}
      <div style={{ display: "flex", gap: 20, borderBottom: "1px solid #e2e8f0", marginBottom: 24 }}>
        {['staff', 'terminals', 'settings'].map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)} style={{
            padding: "0 0 12px", background: "none", border: "none", cursor: "pointer",
            fontSize: 14, fontWeight: 700, color: activeTab === tab ? S.navy : S.gray,
            borderBottom: activeTab === tab ? `2px solid ${S.gold}` : "2px solid transparent",
            textTransform: "capitalize", fontFamily: "inherit", transition: "all 0.2s"
          }}>
            {tab === 'settings' ? 'General Settings' : tab === 'staff' ? 'Staff Management' : 'POS Terminals'}
          </button>
        ))}
      </div>

      {/* STAFF TAB */}
      {activeTab === 'staff' && (
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
            <div>
              <div style={{ fontSize: 14, fontWeight: 700, color: S.navy }}>{staff.length} Staff Members</div>
              <div style={{ fontSize: 12, color: S.grayLight }}>{staff.filter(s => s.status === "active").length} active, {staff.filter(s => s.status === "inactive").length} inactive</div>
            </div>
            <button onClick={() => setShowAddStaff(true)} style={{
              padding: "10px 22px", borderRadius: 10, border: "none", cursor: "pointer", fontFamily: "inherit",
              background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy, fontWeight: 700, fontSize: 13,
              boxShadow: "0 4px 12px rgba(232,168,56,0.3)"
            }}>+ Add Staff</button>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {staff.map(s => (
              <div key={s.id} style={{
                background: "#fff", borderRadius: 12, border: "1px solid #e2e8f0", padding: "16px 20px",
                display: "flex", alignItems: "center", gap: 16, opacity: s.status === "inactive" ? 0.55 : 1
              }}>
                {/* Avatar */}
                <div style={{
                  width: 42, height: 42, borderRadius: "50%", background: s.role === "Manager" ? "#EFF6FF" : s.role === "Supervisor" ? "#FEF3C7" : S.goldPale,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 14, fontWeight: 800, color: s.role === "Manager" ? "#3B82F6" : s.role === "Supervisor" ? "#D97706" : S.gold
                }}>{s.name.split(" ").map(n => n[0]).join("")}</div>

                {/* Info */}
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ fontSize: 14, fontWeight: 700, color: S.navy }}>{s.name}</span>
                    <span style={{
                      fontSize: 10, fontWeight: 700, padding: "2px 8px", borderRadius: 6,
                      background: s.role === "Manager" ? "#EFF6FF" : s.role === "Supervisor" ? "#FEF3C7" : "#f1f5f9",
                      color: s.role === "Manager" ? "#3B82F6" : s.role === "Supervisor" ? "#D97706" : S.gray,
                    }}>{s.role}</span>
                    {s.lastLogin === "Online now" && (
                      <span style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 10, color: S.green, fontWeight: 600 }}>
                        <span style={{ width: 6, height: 6, borderRadius: "50%", background: S.green }} />Online
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 12, color: S.grayLight, marginTop: 2 }}>
                    {s.branch} Branch • PIN: {s.pin} • Last: {s.lastLogin}
                  </div>
                </div>

                {/* Today's stats */}
                <div style={{ textAlign: "right", minWidth: 100 }}>
                  {s.sales > 0 ? (
                    <>
                      <div style={{ fontSize: 14, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono', monospace" }}>₦{(s.revenue / 1000).toFixed(0)}K</div>
                      <div style={{ fontSize: 11, color: S.grayLight }}>{s.sales} sales today</div>
                    </>
                  ) : (
                    <div style={{ fontSize: 11, color: S.grayLight }}>No sales today</div>
                  )}
                </div>

                {/* Actions */}
                <div style={{ display: "flex", gap: 6 }}>
                  <button style={{ padding: "6px 12px", borderRadius: 8, border: "1px solid #e2e8f0", background: "#fff", cursor: "pointer", fontFamily: "inherit", fontSize: 11, fontWeight: 600, color: S.navy }}>Edit</button>
                  <button style={{ padding: "6px 12px", borderRadius: 8, border: "1px solid #e2e8f0", background: "#fff", cursor: "pointer", fontFamily: "inherit", fontSize: 11, fontWeight: 600, color: s.status === "active" ? S.red : S.green }}>
                    {s.status === "active" ? "Disable" : "Enable"}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TERMINALS TAB */}
      {activeTab === 'terminals' && (
        <div style={{ padding: 40, textAlign: "center", color: S.grayLight }}>
          <h3>POS Terminals Management</h3>
          <p>Manage your WebPOS instances here. (Coming Soon)</p>
        </div>
      )}

      {/* SETTINGS TAB */}
      {activeTab === 'settings' && (
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          {[
            {
              title: "Payment Methods", icon: "💳",
              items: [
                { label: "Cash", enabled: true }, { label: "Card (POS Terminal)", enabled: true },
                { label: "Bank Transfer", enabled: true }, { label: "Split Payment", enabled: true },
              ]
            },
            {
              title: "Receipt Settings", icon: "🧾",
              items: [
                { label: "Print receipt automatically", enabled: true },
                { label: "Send receipt via SMS", enabled: false },
                { label: "Send receipt via WhatsApp", enabled: true },
              ]
            },
          ].map(section => (
            <div key={section.title} style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: 20 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 16 }}>
                <span style={{ fontSize: 20 }}>{section.icon}</span>
                <h3 style={{ fontSize: 15, fontWeight: 700, color: S.navy, margin: 0 }}>{section.title}</h3>
              </div>
              {section.items.map(item => (
                <div key={item.label} style={{
                  display: "flex", alignItems: "center", justifyContent: "space-between",
                  padding: "10px 0", borderBottom: "1px solid #f8fafc"
                }}>
                  <span style={{ fontSize: 13, color: S.navy }}>{item.label}</span>
                  <div style={{
                    width: 40, height: 22, borderRadius: 11, cursor: "pointer",
                    background: item.enabled ? S.green : "#e2e8f0",
                    position: "relative", transition: "background 0.2s"
                  }}>
                    <div style={{
                      width: 18, height: 18, borderRadius: "50%", background: "#fff",
                      position: "absolute", top: 2, left: item.enabled ? 20 : 2,
                      transition: "left 0.2s", boxShadow: "0 1px 3px rgba(0,0,0,0.2)"
                    }} />
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      )}

      {showAddStaff && (
        <AddStaffModal
          onClose={() => setShowAddStaff(false)}
          onAdd={handleAddStaff}
        />
      )}
    </div>
  );
}
