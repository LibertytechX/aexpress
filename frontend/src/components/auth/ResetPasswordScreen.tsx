'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import Icons from '@/components/Icons';
import { S } from '@/lib/theme';

export default function ResetPasswordScreen({ token }) {
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [status, setStatus] = useState("form"); // form, success, error
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);

  // Password validation states
  const [passwordFocused, setPasswordFocused] = useState(false);
  const hasMinLength = newPassword.length >= 6;
  const passwordsMatch = newPassword && confirmPassword && newPassword === confirmPassword;

  const handleSubmit = async () => {
    // Validate passwords
    if (!newPassword || !confirmPassword) {
      setMessage("Please fill in both password fields");
      return;
    }

    if (newPassword !== confirmPassword) {
      setMessage("Passwords do not match");
      return;
    }

    if (newPassword.length < 6) {
      setMessage("Password must be at least 6 characters long");
      return;
    }

    try {
      setLoading(true);
      setMessage("");

      const response = await fetch('https://www.orders.axpress.net/api/auth/reset-password/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token,
          new_password: newPassword,
          confirm_password: confirmPassword
        })
      });

      const data = await response.json();

      if (data.success) {
        setStatus("success");
      } else {
        setStatus("error");
        setMessage(data.error || "Failed to reset password. Please try again.");
      }
    } catch (err) {
      setStatus("error");
      setMessage("Network error. Please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && status === "form") {
      handleSubmit();
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#f8fafc", fontFamily: "'DM Sans', sans-serif", padding: 20 }}>
      <div style={{ width: "100%", maxWidth: 440, background: "#fff", borderRadius: 18, boxShadow: "0 8px 32px rgba(0,0,0,0.08)", padding: 48 }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{
            width: 56, height: 56, borderRadius: 14,
            background: status === "success" ? `linear-gradient(135deg, #10b981, #34d399)` : status === "error" ? `linear-gradient(135deg, #ef4444, #f87171)` : `linear-gradient(135deg, ${S.gold}, #F5C563)`,
            display: "inline-flex", alignItems: "center", justifyContent: "center", marginBottom: 16,
            boxShadow: status === "success" ? "0 4px 16px rgba(16,185,129,0.25)" : status === "error" ? "0 4px 16px rgba(239,68,68,0.25)" : "0 4px 16px rgba(232,168,56,0.25)"
          }}>
            <div style={{ color: status === "form" ? S.navy : "#fff" }}>
              {status === "success" ? Icons.checkCircle : status === "error" ? Icons.xCircle : Icons.key}
            </div>
          </div>
          <h2 style={{ fontSize: 24, fontWeight: 700, color: S.navy, marginBottom: 8 }}>
            {status === "success" ? "Password Reset!" : status === "error" ? "Reset Failed" : "Create New Password"}
          </h2>
          <p style={{ color: "#64748b", fontSize: 14, lineHeight: 1.5 }}>
            {status === "success" ? "Redirecting you to login..." : status === "error" ? "There was a problem resetting your password" : "Enter your new password below"}
          </p>
        </div>

        {status === "form" && (
          <>
            {message && (
              <div style={{ padding: "12px 16px", background: "#fee2e2", border: "1px solid #fecaca", borderRadius: 10, marginBottom: 20, color: "#dc2626", fontSize: 14 }}>
                {message}
              </div>
            )}

            <div style={{ marginBottom: 20 }}>
              <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: S.gray, marginBottom: 6 }}>New Password</label>
              <input
                type="password"
                value={newPassword}
                onChange={e => setNewPassword(e.target.value)}
                onFocus={() => setPasswordFocused(true)}
                onBlur={() => setPasswordFocused(false)}
                onKeyPress={handleKeyPress}
                placeholder="Enter new password"
                style={{ width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 14px", height: 46, fontSize: 15, fontFamily: "inherit" }}
              />

              {/* Password strength indicator */}
              {(passwordFocused || newPassword) && (
                <div style={{ marginTop: 8, fontSize: 12 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6, color: hasMinLength ? "#10b981" : "#94a3b8" }}>
                    <span>{hasMinLength ? "✓" : "○"}</span>
                    <span>At least 6 characters</span>
                  </div>
                </div>
              )}
            </div>

            <div style={{ marginBottom: 24 }}>
              <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: S.gray, marginBottom: 6 }}>Confirm Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Confirm new password"
                style={{
                  width: "100%",
                  border: `1.5px solid ${confirmPassword && !passwordsMatch ? "#fecaca" : "#e2e8f0"}`,
                  borderRadius: 10,
                  padding: "0 14px",
                  height: 46,
                  fontSize: 15,
                  fontFamily: "inherit"
                }}
              />

              {confirmPassword && !passwordsMatch && (
                <div style={{ marginTop: 6, fontSize: 12, color: "#dc2626" }}>
                  Passwords do not match
                </div>
              )}
            </div>

            <button onClick={handleSubmit} disabled={loading} style={{
              width: "100%", height: 48, border: "none", borderRadius: 10, fontSize: 15, fontWeight: 700, cursor: loading ? "not-allowed" : "pointer",
              background: loading ? "#e2e8f0" : `linear-gradient(135deg, ${S.gold}, #F5C563)`, color: loading ? "#94a3b8" : S.navy, fontFamily: "inherit",
              boxShadow: loading ? "none" : "0 4px 12px rgba(232,168,56,0.3)"
            }}>
              {loading ? "Resetting Password..." : "Reset Password"}
            </button>
          </>
        )}

        {status === "success" && (
          <div style={{ textAlign: "center", padding: "24px 0" }}>
            <p style={{ color: "#64748b", fontSize: 14, lineHeight: 1.6 }}>
              Your password has been reset successfully! You can now login with your new password.
            </p>
            <div style={{ textAlign: "center", marginTop: 20 }}>
                <Link href="/login" style={{ color: S.gold, fontWeight: 600, fontSize: 14, fontFamily: "inherit", textDecoration: "none" }}>
                    Go to Login
                </Link>
            </div>
          </div>
        )}

        {status === "error" && (
          <>
            <div style={{ padding: "12px 16px", background: "#fee2e2", border: "1px solid #fecaca", borderRadius: 10, marginBottom: 20, color: "#dc2626", fontSize: 14 }}>
              {message}
            </div>
            <div style={{ textAlign: "center" }}>
              <Link href="/login" style={{ color: S.gold, fontWeight: 600, fontSize: 14, fontFamily: "inherit", textDecoration: "none" }}>
                ← Back to Login
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
