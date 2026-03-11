'use client';

import React, { useState } from 'react';
import { S } from '@/lib/theme';

export default function RateRiderModal({ order, onClose, onSubmit }) {
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (rating === 0) return;
    setLoading(true);
    await onSubmit({ orderId: order.id, rating, comment });
    setLoading(false);
  };

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }} onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{ background: "#fff", borderRadius: 20, padding: 32, width: 400, boxShadow: "0 24px 48px rgba(0,0,0,0.15)", textAlign: "center" }}>
        <h2 style={{ fontSize: 20, fontWeight: 800, color: S.navy, margin: "0 0 8px" }}>Rate Delivery</h2>
        <p style={{ fontSize: 13, color: S.grayLight, margin: "0 0 24px" }}>How was your experience with this order?</p>

        <div style={{ display: "flex", justifyContent: "center", gap: 8, marginBottom: 24 }}>
          {[1, 2, 3, 4, 5].map(r => (
            <button key={r} onClick={() => setRating(r)} style={{
              background: "none", border: "none", fontSize: 32, cursor: "pointer",
              transition: "transform 0.1s", transform: rating >= r ? "scale(1.1)" : "scale(1)",
              color: rating >= r ? S.gold : "#e2e8f0"
            }}>★</button>
          ))}
        </div>

        <textarea
          placeholder="Optional comment..."
          value={comment}
          onChange={e => setComment(e.target.value)}
          style={{
            width: "100%", height: 80, border: "1.5px solid #e2e8f0", borderRadius: 12, padding: 12,
            fontSize: 13, fontFamily: "inherit", resize: "none", marginBottom: 24
          }}
        />

        <button onClick={handleSubmit} disabled={loading || rating === 0} style={{
          width: "100%", padding: "14px 0", borderRadius: 12, border: "none", cursor: rating > 0 ? "pointer" : "not-allowed",
          background: rating > 0 ? `linear-gradient(135deg, ${S.gold}, ${S.goldLight})` : "#e2e8f0",
          color: rating > 0 ? S.navy : S.gray, fontWeight: 700, fontSize: 15, fontFamily: "inherit"
        }}>
          {loading ? "Submitting..." : "Submit Review"}
        </button>
      </div>
    </div>
  );
}
