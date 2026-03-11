'use client';

import React, { useState } from 'react';
import Icons from '@/components/Icons';

export default function EmailVerificationBanner({ currentUser, onResend, onDismiss }) {
  const [resending, setResending] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  // Don't show if email is verified or banner is dismissed
  if (!currentUser || currentUser.email_verified || dismissed) return null;

  const handleResend = async () => {
    setResending(true);
    await onResend();
    setResending(false);
  };

  return (
    <div style={{
      background: "linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%)",
      border: "1px solid #FCD34D",
      borderRadius: 12,
      padding: "16px 20px",
      marginBottom: 24,
      display: "flex",
      alignItems: "center",
      gap: 16,
      boxShadow: "0 2px 8px rgba(252, 211, 77, 0.2)"
    }}>
      <div style={{ color: "#92400E", fontSize: 24 }}>
        {Icons.mail}
      </div>
      <div style={{ flex: 1 }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: "#78350F", marginBottom: 4 }}>
          Verify Your Email Address
        </div>
        <div style={{ fontSize: 13, color: "#92400E", lineHeight: 1.5 }}>
          We sent a verification email to <strong>{currentUser.email}</strong>. Please check your inbox and click the verification link.
        </div>
      </div>
      <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
        <button
          onClick={handleResend}
          disabled={resending}
          style={{
            padding: "8px 16px",
            borderRadius: 8,
            border: "1px solid #D97706",
            background: "#fff",
            color: "#92400E",
            fontWeight: 600,
            fontSize: 13,
            cursor: resending ? "not-allowed" : "pointer",
            fontFamily: "inherit",
            opacity: resending ? 0.6 : 1,
            whiteSpace: "nowrap"
          }}
        >
          {resending ? "Sending..." : "Resend Email"}
        </button>
        <button
          onClick={() => setDismissed(true)}
          style={{
            background: "none",
            border: "none",
            color: "#92400E",
            cursor: "pointer",
            padding: 4,
            fontSize: 20,
            lineHeight: 1
          }}
        >
          ×
        </button>
      </div>
    </div>
  );
}
