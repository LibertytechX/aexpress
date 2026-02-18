'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { S } from '@/lib/theme';

export default function LoginScreen() {
  const [phone, setPhone] = useState("");
  const [pass, setPass] = useState("");
  const [error, setError] = useState("");
  const { login, loading } = useAuth();
  // We use local loading state to show loading on button, 
  // but the context loading is for initial auth check.
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleLogin = async () => {
    if (!phone || !pass) {
      setError("Please enter phone and password");
      return;
    }

    try {
      setIsSubmitting(true);
      setError("");
      await login(phone, pass);
    } catch (err) {
      setError(err.message || "Login failed. Please check your credentials.");
      setIsSubmitting(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleLogin();
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", fontFamily: "'DM Sans', sans-serif" }}>
      {/* Left Panel */}
      <div style={{
        flex: 1, background: `linear-gradient(145deg, ${S.navy} 0%, #0f1b33 100%)`,
        display: "flex", flexDirection: "column", justifyContent: "center", padding: "60px",
        position: "relative", overflow: "hidden", minHeight: "100vh"
      }}>
        {/* Decorative elements */}
        <div style={{ position: "absolute", top: -80, right: -80, width: 300, height: 300, borderRadius: "50%", background: "rgba(232,168,56,0.05)" }} />
        <div style={{ position: "absolute", bottom: -120, left: -60, width: 400, height: 400, borderRadius: "50%", background: "rgba(232,168,56,0.03)" }} />

        <div style={{ position: "relative", zIndex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 48 }}>
            <div style={{
              width: 44, height: 44, borderRadius: 10, background: `linear-gradient(135deg, ${S.gold}, #F5C563)`,
              display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 800, fontSize: 18, color: S.navy,
              fontFamily: "'Space Mono', monospace"
            }}>AX</div>
            <div>
              <div style={{ color: "#fff", fontWeight: 700, fontSize: 18, letterSpacing: "1px" }}>ASSURED XPRESS</div>
              <div style={{ color: S.gold, fontSize: 11, letterSpacing: "3px", fontWeight: 600 }}>MERCHANT PORTAL</div>
            </div>
          </div>

          <h1 style={{ color: "#fff", fontSize: 36, fontWeight: 700, lineHeight: 1.2, marginBottom: 16 }}>
            Deliver Anything,<br /><span style={{ color: S.gold }}>Anywhere in Lagos</span>
          </h1>
          <p style={{ color: "rgba(255,255,255,0.5)", fontSize: 16, lineHeight: 1.6, maxWidth: 400 }}>
            Fund your wallet. Create orders. Track deliveries. All from one powerful dashboard built for merchants.
          </p>

          <div style={{ display: "flex", gap: 32, marginTop: 48 }}>
            {[{ n: "40+", l: "Active Riders" }, { n: "21min", l: "Avg Delivery" }, { n: "₦1.2K", l: "From" }].map((s, i) => (
              <div key={i}>
                <div style={{ color: S.gold, fontSize: 28, fontWeight: 700, fontFamily: "'Space Mono', monospace" }}>{s.n}</div>
                <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 12, marginTop: 4 }}>{s.l}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right Panel - Login Form */}
      <div style={{ width: 480, background: "#fff", display: "flex", flexDirection: "column", justifyContent: "center", padding: "60px" }}>
        <h2 style={{ fontSize: 24, fontWeight: 700, color: S.navy, marginBottom: 8 }}>Welcome back</h2>
        <p style={{ color: "#64748b", fontSize: 14, marginBottom: 32 }}>Sign in to your merchant account</p>

        {error && (
          <div style={{ padding: "12px 16px", background: "#fee2e2", border: "1px solid #fecaca", borderRadius: 8, marginBottom: 20, color: "#dc2626", fontSize: 14 }}>
            {error}
          </div>
        )}

        <div style={{ marginBottom: 20 }}>
          <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: S.gray, marginBottom: 6 }}>Phone Number</label>
          <div style={{ display: "flex", alignItems: "center", border: "1.5px solid #e2e8f0", borderRadius: 10, overflow: "hidden" }}>
            <span style={{ padding: "0 12px", background: "#f8fafc", borderRight: "1px solid #e2e8f0", fontSize: 14, color: "#64748b", height: 46, display: "flex", alignItems: "center" }}>+234</span>
            <input value={phone} onChange={e => setPhone(e.target.value)} onKeyPress={handleKeyPress} placeholder="8099999999"
              style={{ flex: 1, border: "none", padding: "0 14px", height: 46, fontSize: 15, fontFamily: "inherit", background: "transparent" }} />
          </div>
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: S.gray, marginBottom: 6 }}>Password</label>
          <input type="password" value={pass} onChange={e => setPass(e.target.value)} onKeyPress={handleKeyPress} placeholder="Enter password"
            style={{ width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 14px", height: 46, fontSize: 15, fontFamily: "inherit" }} />
        </div>

        <div style={{ textAlign: "right", marginBottom: 24 }}>
          <Link href="/forgot-password" style={{ color: S.gold, fontWeight: 600, fontSize: 13, fontFamily: "inherit", textDecoration: "none" }}>
            Forgot Password?
          </Link>
        </div>

        <button onClick={handleLogin} disabled={isSubmitting} style={{
          width: "100%", height: 48, border: "none", borderRadius: 10, fontSize: 15, fontWeight: 700, cursor: isSubmitting ? "not-allowed" : "pointer",
          background: isSubmitting ? "#e2e8f0" : `linear-gradient(135deg, ${S.gold}, #F5C563)`, color: isSubmitting ? "#94a3b8" : S.navy, fontFamily: "inherit",
          boxShadow: isSubmitting ? "none" : "0 4px 12px rgba(232,168,56,0.3)"
        }}>{isSubmitting ? "Signing in..." : "Sign In"}</button>

        <div style={{ textAlign: "center", marginTop: 24 }}>
          <span style={{ color: "#64748b", fontSize: 14 }}>Don&apos;t have an account? </span>
          <Link href="/signup" style={{ color: S.gold, fontWeight: 700, fontSize: 14, fontFamily: "inherit", textDecoration: "none" }}>
            Sign Up
          </Link>
        </div>
      </div>
    </div>
  );
}
