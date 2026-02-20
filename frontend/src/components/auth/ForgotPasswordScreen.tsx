'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import Icons from '@/components/Icons';
import { S } from '@/lib/theme';

export default function ForgotPasswordScreen() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    if (!email) {
      setError("Please enter your email address");
      return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      setError("Please enter a valid email address");
      return;
    }

    try {
      setLoading(true);
      setError("");

      const response = await fetch('https://www.orders.axpress.net/api/auth/request-password-reset/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email })
      });

      const data = await response.json();

      if (data.success) {
        setSubmitted(true);
      } else {
        setError(data.error || "Failed to send reset link. Please try again.");
      }
    } catch (err) {
      setError("Network error. Please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !submitted) {
      handleSubmit();
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#f8fafc", fontFamily: "'DM Sans', sans-serif", padding: 20 }}>
      
      <div style={{ width: "100%", maxWidth: 440, background: "#fff", borderRadius: 18, boxShadow: "0 8px 32px rgba(0,0,0,0.08)", padding: 48 }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{
            width: 56, height: 56, borderRadius: 14, background: `linear-gradient(135deg, ${S.gold}, #F5C563)`,
            display: "inline-flex", alignItems: "center", justifyContent: "center", marginBottom: 16,
            boxShadow: "0 4px 16px rgba(232,168,56,0.25)"
          }}>
            <div style={{ color: S.navy }}>{Icons.lock}</div>
          </div>
          <h2 style={{ fontSize: 24, fontWeight: 700, color: S.navy, marginBottom: 8 }}>Forgot Password?</h2>
          <p style={{ color: "#64748b", fontSize: 14, lineHeight: 1.5 }}>
            {submitted ? "Check your email for reset instructions" : "Enter your email and we'll send you a reset link"}
          </p>
        </div>

        {!submitted ? (
          <>
            {error && (
              <div style={{ padding: "12px 16px", background: "#fee2e2", border: "1px solid #fecaca", borderRadius: 10, marginBottom: 20, color: "#dc2626", fontSize: 14 }}>
                {error}
              </div>
            )}

            <div style={{ marginBottom: 24 }}>
              <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: S.gray, marginBottom: 6 }}>Email Address</label>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="your@email.com"
                style={{ width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 14px", height: 46, fontSize: 15, fontFamily: "inherit" }}
              />
            </div>

            <button onClick={handleSubmit} disabled={loading} style={{
              width: "100%", height: 48, border: "none", borderRadius: 10, fontSize: 15, fontWeight: 700, cursor: loading ? "not-allowed" : "pointer",
              background: loading ? "#e2e8f0" : `linear-gradient(135deg, ${S.gold}, #F5C563)`, color: loading ? "#94a3b8" : S.navy, fontFamily: "inherit",
              boxShadow: loading ? "none" : "0 4px 12px rgba(232,168,56,0.3)", marginBottom: 16
            }}>
              {loading ? "Sending..." : "Send Reset Link"}
            </button>
          </>
        ) : (
          <div style={{ textAlign: "center", padding: "24px 0" }}>
            <div style={{ color: "#10b981", marginBottom: 16 }}>{Icons.checkCircle}</div>
            <p style={{ color: "#64748b", fontSize: 14, lineHeight: 1.6, marginBottom: 24 }}>
              If an account exists with <strong style={{ color: S.navy }}>{email}</strong>, you will receive a password reset link shortly. Please check your inbox and spam folder.
            </p>
          </div>
        )}

        <div style={{ textAlign: "center" }}>
          <Link href="/login" style={{ color: S.gold, fontWeight: 600, fontSize: 14, fontFamily: "inherit", textDecoration: "none" }}>
            ← Back to Login
          </Link>
        </div>
      </div>
    </div>
  );
}
