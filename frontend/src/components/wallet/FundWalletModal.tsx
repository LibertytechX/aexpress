'use client';

import React, { useState } from 'react';
import Icons from '@/components/Icons';
import { S } from '@/lib/theme';

export default function FundWalletModal({ onClose, onFund, onBankTransfer }) {
  const [amount, setAmount] = useState("");
  const [method, setMethod] = useState("card");

  const presets = [1000, 2000, 5000, 10000, 20000, 50000];

  const handlePay = () => {
    if (!amount) return;

    const amountValue = parseInt(amount);

    if (method === "transfer") {
      // Open bank transfer modal
      onBankTransfer(amountValue);
    } else if (method === "card") {
      // Use existing Paystack flow
      onFund(amountValue);
    } else {
      // Other payment methods (LibertyPay, etc.)
      alert(`${method} payment coming soon!`);
    }
  };

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 100, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'DM Sans', sans-serif" }}>
      <div onClick={onClose} style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.5)" }} />
      <div style={{ position: "relative", background: "#fff", borderRadius: 18, width: 420, maxHeight: "90vh", overflow: "auto", boxShadow: "0 20px 60px rgba(0,0,0,0.2)", animation: "fadeIn 0.3s ease" }}>
        <div style={{ padding: "20px 24px", borderBottom: "1px solid #f1f5f9", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3 style={{ fontSize: 18, fontWeight: 700, color: S.navy, margin: 0 }}>Fund Wallet</h3>
          <button onClick={onClose} style={{ background: "none", border: "none", cursor: "pointer", color: S.gray, padding: 4 }}>
            {Icons.close || '×'}
          </button>
        </div>
        <div style={{ padding: 24 }}>
          <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#334155", marginBottom: 8 }}>Amount (₦)</label>
          <input value={amount} onChange={e => setAmount(e.target.value.replace(/[^0-9]/g, ""))} placeholder="Enter amount"
            style={{ width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 14px", height: 48, fontSize: 20, fontWeight: 700, fontFamily: "'Space Mono', monospace", textAlign: "center" }} />

          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 8, marginTop: 12 }}>
            {presets.map(p => (
              <button key={p} onClick={() => setAmount(p.toString())} style={{
                padding: "8px", borderRadius: 8, border: amount === p.toString() ? `2px solid ${S.gold}` : "1.5px solid #e2e8f0",
                background: amount === p.toString() ? S.goldPale : "#fff", cursor: "pointer",
                fontSize: 14, fontWeight: 600, color: S.navy, fontFamily: "'Space Mono', monospace"
              }}>₦{p.toLocaleString()}</button>
            ))}
          </div>

          <div style={{ marginTop: 20 }}>
            <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: "#334155", marginBottom: 8 }}>Payment Method</label>
            {[
              { id: "card", label: "Card Payment", sub: "Visa, Mastercard, Verve" },
              { id: "transfer", label: "Bank Transfer", sub: "Instant confirmation" },
              { id: "liberty", label: "LibertyPay", sub: "Zero transaction fee" },
            ].map(m => (
              <button key={m.id} onClick={() => setMethod(m.id)} style={{
                width: "100%", display: "flex", alignItems: "center", gap: 12, padding: "12px 14px", marginBottom: 6,
                border: method === m.id ? `2px solid ${S.gold}` : "1.5px solid #e2e8f0", borderRadius: 10,
                background: method === m.id ? S.goldPale : "#fff", cursor: "pointer", fontFamily: "inherit"
              }}>
                <div style={{ width: 18, height: 18, borderRadius: "50%", border: `2px solid ${method === m.id ? S.gold : "#cbd5e1"}`, display: "flex", alignItems: "center", justifyContent: "center" }}>
                  {method === m.id && <div style={{ width: 9, height: 9, borderRadius: "50%", background: S.gold }} />}
                </div>
                <div style={{ textAlign: "left" }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: S.navy }}>{m.label}</div>
                  <div style={{ fontSize: 11, color: S.grayLight }}>{m.sub}</div>
                </div>
                {m.id === "liberty" && <span style={{ marginLeft: "auto", fontSize: 10, fontWeight: 700, padding: "2px 8px", borderRadius: 6, background: S.greenBg, color: S.green }}>FREE</span>}
              </button>
            ))}
          </div>

          <button onClick={handlePay} disabled={!amount}
            style={{
              width: "100%", height: 48, border: "none", borderRadius: 10, fontSize: 15, fontWeight: 700, cursor: amount ? "pointer" : "default",
              background: amount ? `linear-gradient(135deg, ${S.gold}, ${S.goldLight})` : "#e2e8f0",
              color: amount ? S.navy : "#94a3b8", fontFamily: "inherit", marginTop: 16,
              boxShadow: amount ? "0 4px 12px rgba(232,168,56,0.3)" : "none"
            }}>
            {amount ? `Pay ₦${parseInt(amount).toLocaleString()}` : "Enter Amount"}
          </button>
        </div>
      </div>
    </div>
  );
}
