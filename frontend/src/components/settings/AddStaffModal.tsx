'use client';

import React, { useState } from 'react';
import { S } from '@/lib/theme';

export default function AddStaffModal({ onClose, onAdd }) {
  const [formData, setFormData] = useState({
      name: '',
      phone: '',
      pin: '',
      role: 'Cashier',
      branch: 'Seeds & Pennies HQ' // Default
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
      if(!formData.name || !formData.phone || !formData.pin) return;
      setLoading(true);
      await onAdd(formData);
      setLoading(false);
      onClose();
  };

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}
      onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{
        background: "#fff", borderRadius: 20, padding: 32, width: 440,
        boxShadow: "0 24px 48px rgba(0,0,0,0.15)"
      }}>
        <h2 style={{ fontSize: 20, fontWeight: 800, color: S.navy, margin: "0 0 4px" }}>Add New Staff</h2>
        <p style={{ fontSize: 13, color: S.grayLight, margin: "0 0 20px" }}>They'll login to the POS with their PIN</p>

        {[
          { key: "name", label: "Full Name", placeholder: "e.g. Blessing Okonkwo" },
          { key: "phone", label: "Phone Number", placeholder: "e.g. 08034567890" },
          { key: "pin", label: "4-Digit PIN", placeholder: "e.g. 1234", type: "password" },
        ].map(f => (
          <div key={f.key} style={{ marginBottom: 14 }}>
            <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: S.gray, marginBottom: 5 }}>{f.label}</label>
            <input 
              placeholder={f.placeholder} 
              type={f.type || "text"}
              value={formData[f.key]}
              onChange={e => setFormData({...formData, [f.key]: e.target.value})}
              style={{
                width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 12px",
                height: 42, fontSize: 13, fontFamily: f.type === "password" ? "'Space Mono', monospace" : "inherit"
              }} 
            />
          </div>
        ))}

        <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: S.gray, marginBottom: 5 }}>Role</label>
        <div style={{ display: "flex", gap: 8, marginBottom: 14 }}>
          {["Cashier", "Supervisor", "Manager"].map(r => (
            <button key={r} onClick={() => setFormData({...formData, role: r})} style={{
              flex: 1, padding: "10px 0", borderRadius: 10, border: formData.role === r ? `2px solid ${S.gold}` : "1.5px solid #e2e8f0",
              background: formData.role === r ? S.goldPale : "#fff", cursor: "pointer", fontFamily: "inherit",
              fontSize: 13, fontWeight: 600, color: S.navy
            }}>{r}</button>
          ))}
        </div>

        <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: S.gray, marginBottom: 5 }}>Assign to Branch</label>
        <select 
          value={formData.branch}
          onChange={e => setFormData({...formData, branch: e.target.value})}
          style={{
            width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 12px",
            height: 42, fontSize: 13, fontFamily: "inherit", background: "#fff", marginBottom: 18
        }}>
          <option>Seeds & Pennies HQ</option>
          <option>Seeds & Pennies Lekki</option>
          <option>Liberty Assured Ikeja</option>
        </select>

        <button onClick={handleSubmit} disabled={loading} style={{
          width: "100%", padding: "14px 0", borderRadius: 12, border: "none", cursor: "pointer", fontFamily: "inherit",
          background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy, fontWeight: 700, fontSize: 15,
          boxShadow: "0 4px 12px rgba(232,168,56,0.3)"
        }}>{loading ? "Creating..." : "Create Staff Account"}</button>
      </div>
    </div>
  );
}
