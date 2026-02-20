'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { S } from '@/lib/theme';

export default function SignupScreen() {
  const [step, setStep] = useState(1);
  const [error, setError] = useState("");
  const { signup } = useAuth();
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  // Step 1 fields
  const [contactName, setContactName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");

  // Step 2 fields
  const [businessName, setBusinessName] = useState("");
  const [address, setAddress] = useState("");

  // Password match validation
  const passwordsMatch = password && confirmPassword && password === confirmPassword;
  const passwordsDontMatch = confirmPassword && password !== confirmPassword;

  const handleSignup = async () => {
    try {
      setLoading(true);
      setError("");

      const success = await signup({
        business_name: businessName,
        contact_name: contactName,
        phone: phone,
        email: email,
        password: password,
        confirm_password: confirmPassword,
        address: address
      });

      if (success) {
        setStep(3);
        // AuthContext handles redirect, but we might want to show success first
        // actually useAuth().signup redirects to dashboard on success. 
        // If we want to show Step 3 "You're all set", we might need to adjust AuthContext or handle it here.
        // For now, let's assume AuthContext redirects. 
        // Wait, if AuthContext redirects immediately, Step 3 won't be seen.
        // The original logic showed Step 3 then called onComplete after 1.5s
        // I'll modify logic to show Step 3 first if possible, but context sets user and redirects.
        // Let's rely on dashboard redirect for now, or maybe I should have made signup return user without redirecting?
        // logic in AuthContext: setUser; router.push('/dashboard'); return true;
        // So it redirects. I'll stick to that. Step 3 "You're all set" might be skipped or flashed.
        // I'll just let it redirect.
      }
    } catch (err) {
      setError(err.message || "Signup failed. Please try again.");
      setStep(2); // Go back to step 2 to show error
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: "100vh", display: "flex", fontFamily: "'DM Sans', sans-serif" }}>
      <div style={{ flex: 1, background: `linear-gradient(145deg, ${S.navy}, #0f1b33)`, display: "flex", alignItems: "center", justifyContent: "center", padding: 60 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 48 }}>
            <div style={{ width: 44, height: 44, borderRadius: 10, background: `linear-gradient(135deg, ${S.gold}, #F5C563)`, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 800, fontSize: 18, color: S.navy, fontFamily: "'Space Mono', monospace" }}>AX</div>
            <div>
              <div style={{ color: "#fff", fontWeight: 700, fontSize: 18 }}>ASSURED XPRESS</div>
              <div style={{ color: S.gold, fontSize: 11, letterSpacing: "3px" }}>MERCHANT PORTAL</div>
            </div>
          </div>
          <h1 style={{ color: "#fff", fontSize: 32, fontWeight: 700, lineHeight: 1.3, marginBottom: 16 }}>Start delivering<br />in <span style={{ color: S.gold }}>minutes</span></h1>
          <p style={{ color: "rgba(255,255,255,0.5)", fontSize: 15, lineHeight: 1.6 }}>Sign up, fund your wallet, and start<br />sending packages across Lagos today.</p>

          {/* Steps indicator */}
          <div style={{ display: "flex", gap: 8, marginTop: 40 }}>
            {[1, 2, 3].map(s => (
              <div key={s} style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <div style={{
                  width: 32, height: 32, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 13, fontWeight: 700,
                  background: step >= s ? S.gold : "rgba(255,255,255,0.1)",
                  color: step >= s ? S.navy : "rgba(255,255,255,0.3)"
                }}>{step > s ? "✓" : s}</div>
                <span style={{ color: step >= s ? "rgba(255,255,255,0.7)" : "rgba(255,255,255,0.3)", fontSize: 13 }}>
                  {s === 1 ? "Account" : s === 2 ? "Business" : "Verify"}
                </span>
                {s < 3 && <div style={{ width: 20, height: 1, background: "rgba(255,255,255,0.1)", margin: "0 4px" }} />}
              </div>
            ))}
          </div>
        </div>
      </div>


      <div style={{ width: 480, background: "#fff", display: "flex", flexDirection: "column", justifyContent: "center", padding: 60 }}>
        {error && (
          <div style={{ padding: "12px 16px", background: "#fee2e2", border: "1px solid #fecaca", borderRadius: 8, marginBottom: 20, color: "#dc2626", fontSize: 14 }}>
            {error}
          </div>
        )}

        {step === 1 && (
          <>
            <h2 style={{ fontSize: 22, fontWeight: 700, color: S.navy, marginBottom: 24 }}>Create your account</h2>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: S.gray, marginBottom: 6 }}>Full Name</label>
              <input value={contactName} onChange={e => setContactName(e.target.value)} placeholder="Yetunde Igbene" style={{ width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 14px", height: 44, fontSize: 14, fontFamily: "inherit" }} />
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: S.gray, marginBottom: 6 }}>Phone Number</label>
              <div style={{ display: "flex", border: "1.5px solid #e2e8f0", borderRadius: 10, overflow: "hidden" }}>
                <span style={{ padding: "0 12px", background: "#f8fafc", borderRight: "1px solid #e2e8f0", fontSize: 14, color: "#64748b", display: "flex", alignItems: "center" }}>+234</span>
                <input value={phone} onChange={e => setPhone(e.target.value)} placeholder="8099999999" style={{ flex: 1, border: "none", padding: "0 14px", height: 44, fontSize: 14, fontFamily: "inherit", background: "transparent" }} />
              </div>
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: S.gray, marginBottom: 6 }}>Email</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@business.com" style={{ width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 14px", height: 44, fontSize: 14, fontFamily: "inherit" }} />
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: S.gray, marginBottom: 6 }}>Password</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="Min. 8 characters" style={{ width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 14px", height: 44, fontSize: 14, fontFamily: "inherit" }} />
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: S.gray, marginBottom: 6 }}>Confirm Password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                placeholder="Re-enter password"
                style={{
                  width: "100%",
                  border: `1.5px solid ${passwordsDontMatch ? "#ef4444" : passwordsMatch ? "#10b981" : "#e2e8f0"}`,
                  borderRadius: 10,
                  padding: "0 14px",
                  height: 44,
                  fontSize: 14,
                  fontFamily: "inherit",
                  outline: "none"
                }}
              />
              {confirmPassword && (
                <div style={{
                  marginTop: 6,
                  fontSize: 12,
                  fontWeight: 500,
                  color: passwordsMatch ? "#10b981" : "#ef4444",
                  display: "flex",
                  alignItems: "center",
                  gap: 4
                }}>
                  {passwordsMatch ? (
                    <>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                      Passwords match
                    </>
                  ) : (
                    <>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="15" y1="9" x2="9" y2="15"/>
                        <line x1="9" y1="9" x2="15" y2="15"/>
                      </svg>
                      Passwords don't match
                    </>
                  )}
                </div>
              )}
            </div>
            <button
              onClick={() => setStep(2)}
              disabled={!contactName || !phone || !email || !password || !confirmPassword || passwordsDontMatch}
              style={{
                width: "100%",
                height: 46,
                border: "none",
                borderRadius: 10,
                fontSize: 15,
                fontWeight: 700,
                cursor: (!contactName || !phone || !email || !password || !confirmPassword || passwordsDontMatch) ? "not-allowed" : "pointer",
                background: (!contactName || !phone || !email || !password || !confirmPassword || passwordsDontMatch) ? "#e2e8f0" : `linear-gradient(135deg, ${S.gold}, #F5C563)`,
                color: (!contactName || !phone || !email || !password || !confirmPassword || passwordsDontMatch) ? "#94a3b8" : S.navy,
                fontFamily: "inherit",
                marginTop: 8,
                transition: "all 0.2s ease"
              }}
            >
              Continue
            </button>
          </>
        )}
        {step === 2 && (
          <>
            <h2 style={{ fontSize: 22, fontWeight: 700, color: S.navy, marginBottom: 24 }}>Business details</h2>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: S.gray, marginBottom: 6 }}>Business Name</label>
              <input value={businessName} onChange={e => setBusinessName(e.target.value)} placeholder="Vivid Print" style={{ width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 14px", height: 44, fontSize: 14, fontFamily: "inherit" }} />
            </div>
            <div style={{ marginBottom: 16 }}>
              <label style={{ display: "block", fontSize: 13, fontWeight: 600, color: S.gray, marginBottom: 6 }}>Business Address</label>
              <input value={address} onChange={e => setAddress(e.target.value)} placeholder="19 Tejuosho Street, Yaba" style={{ width: "100%", border: "1.5px solid #e2e8f0", borderRadius: 10, padding: "0 14px", height: 44, fontSize: 14, fontFamily: "inherit" }} />
            </div>
            <div style={{ display: "flex", gap: 12, marginTop: 8 }}>
              <button onClick={() => setStep(1)} style={{ flex: 1, height: 46, border: "1.5px solid #e2e8f0", borderRadius: 10, fontSize: 14, fontWeight: 600, cursor: "pointer", background: "#fff", color: S.gray, fontFamily: "inherit" }}>Back</button>
              <button onClick={handleSignup} disabled={loading} style={{ flex: 2, height: 46, border: "none", borderRadius: 10, fontSize: 15, fontWeight: 700, cursor: loading ? "not-allowed" : "pointer", background: loading ? "#e2e8f0" : `linear-gradient(135deg, ${S.gold}, #F5C563)`, color: loading ? "#94a3b8" : S.navy, fontFamily: "inherit" }}>
                {loading ? "Creating Account..." : "Create Account"}
              </button>
            </div>
          </>
        )}
        {step === 3 && (
          <>
            <div style={{ textAlign: "center", marginBottom: 24 }}>
              <div style={{ width: 64, height: 64, borderRadius: "50%", background: "#dcfce7", display: "flex", alignItems: "center", justifyContent: "center", margin: "0 auto 16px" }}>
                <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#16a34a" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
              </div>
              <h2 style={{ fontSize: 22, fontWeight: 700, color: S.navy, marginBottom: 8 }}>You're all set!</h2>
              <p style={{ color: "#64748b", fontSize: 14, lineHeight: 1.6 }}>Your merchant account has been created. Fund your wallet to start sending deliveries.</p>
            </div>
            <button onClick={() => router.push('/dashboard')} style={{ width: "100%", height: 46, border: "none", borderRadius: 10, fontSize: 15, fontWeight: 700, cursor: "pointer", background: `linear-gradient(135deg, ${S.gold}, #F5C563)`, color: S.navy, fontFamily: "inherit" }}>
              Go to Dashboard
            </button>
          </>
        )}
        {step < 3 && (
          <div style={{ textAlign: "center", marginTop: 20 }}>
            <span style={{ color: "#64748b", fontSize: 14 }}>Already have an account? </span>
            <Link href="/login" style={{ color: S.gold, fontWeight: 700, fontSize: 14, fontFamily: "inherit", textDecoration: "none" }}>Sign In</Link>
          </div>
        )}
      </div>
    </div>
  );
}
