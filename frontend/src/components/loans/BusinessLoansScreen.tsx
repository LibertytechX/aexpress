'use client';

import React, { useState } from 'react';
import { S } from '@/lib/theme';

export default function BusinessLoansScreen() {
  const [selectedProduct, setSelectedProduct] = useState(null);

  const products = [
    {
      id: "loc",
      title: "Merchant Line of Credit",
      icon: "💳",
      tagline: "Revolving credit that grows with your business",
      color: "#3B82F6",
      colorBg: "#EFF6FF",
      limit: "Up to ₦10M",
      rate: "From 2.5%/mo",
      tenure: "Revolving",
      features: [
        "Pre-approved credit limit based on your AX transaction history",
        "Draw funds anytime — only pay interest on what you use",
        "Auto-repay from daily sales or wallet balance",
        "Credit limit increases as your delivery volume grows",
        "No collateral required for limits under ₦2M",
        "Instant disbursement to your AX wallet or bank account",
      ],
      howItWorks: [
        { step: "1", title: "Get Pre-Qualified", desc: "We analyse your AX delivery history, wallet activity, and payment patterns" },
        { step: "2", title: "Accept Your Limit", desc: "View your approved credit limit and terms — no paperwork" },
        { step: "3", title: "Draw Funds Instantly", desc: "Pull funds into your wallet or bank account whenever you need" },
        { step: "4", title: "Repay Flexibly", desc: "Auto-debit from sales, manual payment, or scheduled repayments" },
      ],
      idealFor: "Merchants who need flexible, on-demand access to capital for inventory purchases, marketing spend, or managing cash flow gaps between orders."
    },
    {
      id: "wc",
      title: "Working Capital Loan",
      icon: "🏦",
      tagline: "Lump sum funding to stock up and scale up",
      color: "#10B981",
      colorBg: "#F0FDF4",
      limit: "₦500K – ₦25M",
      rate: "From 3%/mo",
      tenure: "3 – 12 months",
      features: [
        "Fixed lump sum disbursed upfront to your bank account",
        "Predictable fixed monthly or weekly repayments",
        "Use for bulk inventory, equipment, or branch expansion",
        "Approval based on AX merchant activity + business profile",
        "Early repayment discounts available",
        "Top-up eligible after 50% repayment",
      ],
      howItWorks: [
        { step: "1", title: "Apply in 2 Minutes", desc: "Tell us how much you need and what it's for — right from this portal" },
        { step: "2", title: "Quick Assessment", desc: "We review your AX history, WebPOS sales, and business documents" },
        { step: "3", title: "Get Funded", desc: "Approved loans disbursed within 24–48 hours to your bank account" },
        { step: "4", title: "Repay & Grow", desc: "Fixed repayment schedule with auto-debit option from your AX wallet" },
      ],
      idealFor: "Merchants planning a big purchase — bulk stock, new equipment, seasonal inventory, or opening a new branch location."
    },
    {
      id: "od",
      title: "Wallet Overdraft",
      icon: "⚡",
      tagline: "Never miss a delivery because your wallet is low",
      color: "#E8A838",
      colorBg: "#FEF3C7",
      limit: "Up to ₦1M",
      rate: "From 0.1%/day",
      tenure: "7 – 30 days",
      features: [
        "Spend beyond your wallet balance — no order interruptions",
        "Auto-activates when your wallet hits zero during an order",
        "Tiny daily interest only on the overdrawn amount",
        "Auto-repays when you next fund your wallet",
        "Overdraft limit tied to your average daily delivery volume",
        "No application needed — pre-approved for active merchants",
      ],
      howItWorks: [
        { step: "1", title: "Stay Active", desc: "Maintain consistent delivery activity on AX for automatic eligibility" },
        { step: "2", title: "Overdraft Activates", desc: "When your wallet can't cover an order, overdraft kicks in seamlessly" },
        { step: "3", title: "Keep Delivering", desc: "Your orders go through without interruption — riders get dispatched" },
        { step: "4", title: "Auto-Repay", desc: "Next wallet funding automatically clears your overdraft balance first" },
      ],
      idealFor: "High-volume merchants who can't afford delivery downtime. Perfect for e-commerce sellers, food businesses, and logistics-heavy operations."
    },
  ];

  const selected = products.find(p => p.id === selectedProduct);

  return (
    <div style={{ animation: "fadeIn 0.3s ease" }}>
      {/* Hero */}
      <div style={{
        background: `linear-gradient(135deg, ${S.navy} 0%, #0f1b33 100%)`, borderRadius: 16, padding: "32px 36px",
        marginBottom: 24, position: "relative", overflow: "hidden"
      }}>
        <div style={{ position: "absolute", top: -30, right: -10, width: 140, height: 140, borderRadius: "50%", background: "rgba(232,168,56,0.06)" }} />
        <div style={{ position: "absolute", bottom: -40, right: 120, width: 100, height: 100, borderRadius: "50%", background: "rgba(139,92,246,0.06)" }} />
        <div style={{ position: "relative", zIndex: 1 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
            <span style={{ background: "#8B5CF6", color: "#fff", fontSize: 10, fontWeight: 700, padding: "4px 12px", borderRadius: 10 }}>COMING SOON</span>
            <span style={{ background: "rgba(255,255,255,0.08)", color: "rgba(255,255,255,0.5)", fontSize: 10, fontWeight: 700, padding: "4px 12px", borderRadius: 10 }}>POWERED BY LIBERTY ASSURED</span>
          </div>
          <h2 style={{ color: "#fff", fontSize: 24, fontWeight: 800, margin: "0 0 8px" }}>Business Loans for AX Merchants</h2>
          <p style={{ color: "rgba(255,255,255,0.5)", fontSize: 14, margin: 0, maxWidth: 560, lineHeight: 1.6 }}>
            Access credit tailored to your delivery business. Your AX activity builds your credit profile — the more you ship, the more you can borrow.
          </p>
        </div>
      </div>

      {/* Product cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 16, marginBottom: 24 }}>
        {products.map(p => (
          <div key={p.id} onClick={() => setSelectedProduct(selectedProduct === p.id ? null : p.id)} style={{
            background: "#fff", borderRadius: 16, border: selectedProduct === p.id ? `2px solid ${p.color}` : "1px solid #e2e8f0",
            padding: 24, cursor: "pointer", transition: "all 0.25s",
            boxShadow: selectedProduct === p.id ? `0 8px 24px ${p.color}20` : "none",
            transform: selectedProduct === p.id ? "translateY(-2px)" : "none"
          }}>
            <div style={{
              width: 52, height: 52, borderRadius: 14, background: p.colorBg,
              display: "flex", alignItems: "center", justifyContent: "center", fontSize: 26, marginBottom: 16
            }}>{p.icon}</div>

            <h3 style={{ fontSize: 17, fontWeight: 800, color: S.navy, margin: "0 0 6px" }}>{p.title}</h3>
            <p style={{ fontSize: 13, color: S.grayLight, margin: "0 0 18px", lineHeight: 1.5 }}>{p.tagline}</p>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8, marginBottom: 18 }}>
              {[
                { label: "Limit", value: p.limit },
                { label: "Rate", value: p.rate },
                { label: "Tenure", value: p.tenure },
              ].map(s => (
                <div key={s.label} style={{ padding: "10px 8px", background: "#f8fafc", borderRadius: 10, textAlign: "center" }}>
                  <div style={{ fontSize: 12, fontWeight: 800, color: S.navy }}>{s.value}</div>
                  <div style={{ fontSize: 10, color: S.grayLight, marginTop: 2 }}>{s.label}</div>
                </div>
              ))}
            </div>

            <button style={{
              width: "100%", padding: "12px 0", borderRadius: 10, border: "none", cursor: "pointer", fontFamily: "inherit",
              background: selectedProduct === p.id ? p.color : "#f1f5f9",
              color: selectedProduct === p.id ? "#fff" : S.gray,
              fontWeight: 700, fontSize: 13, transition: "all 0.2s"
            }}>
              {selectedProduct === p.id ? "Hide Details ↑" : "Learn More ↓"}
            </button>
          </div>
        ))}
      </div>

      {/* Expanded detail */}
      {selected && (
        <div style={{ animation: "fadeIn 0.3s ease", marginBottom: 24 }}>
          <div style={{ background: "#fff", borderRadius: 16, border: "1px solid #e2e8f0", padding: 28, borderTop: `4px solid ${selected.color}` }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
              <div style={{
                width: 42, height: 42, borderRadius: 12, background: selected.colorBg,
                display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22
              }}>{selected.icon}</div>
              <div>
                <h3 style={{ fontSize: 18, fontWeight: 800, color: S.navy, margin: 0 }}>{selected.title}</h3>
                <p style={{ fontSize: 13, color: S.grayLight, margin: 0 }}>{selected.tagline}</p>
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 24 }}>
              {/* Features */}
              <div>
                <h4 style={{ fontSize: 14, fontWeight: 700, color: S.navy, margin: "0 0 12px" }}>What You Get</h4>
                {selected.features.map((f, i) => (
                  <div key={i} style={{ display: "flex", gap: 10, padding: "8px 0" }}>
                    <div style={{
                      width: 20, height: 20, borderRadius: "50%", background: selected.colorBg, flexShrink: 0, marginTop: 1,
                      display: "flex", alignItems: "center", justifyContent: "center"
                    }}>
                      <span style={{ color: selected.color, fontSize: 11, fontWeight: 800 }}>✓</span>
                    </div>
                    <span style={{ fontSize: 13, color: S.gray, lineHeight: 1.5 }}>{f}</span>
                  </div>
                ))}
              </div>

              {/* How it works */}
              <div>
                <h4 style={{ fontSize: 14, fontWeight: 700, color: S.navy, margin: "0 0 12px" }}>How It Works</h4>
                {selected.howItWorks.map((hw, i) => (
                  <div key={i} style={{ display: "flex", gap: 12, padding: "10px 0", position: "relative" }}>
                    {i < selected.howItWorks.length - 1 && (
                      <div style={{ position: "absolute", left: 15, top: 36, bottom: -2, width: 2, background: "#f1f5f9" }} />
                    )}
                    <div style={{
                      width: 32, height: 32, borderRadius: "50%", background: selected.color, flexShrink: 0,
                      display: "flex", alignItems: "center", justifyContent: "center",
                      fontSize: 13, fontWeight: 800, color: "#fff", position: "relative", zIndex: 1
                    }}>{hw.step}</div>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 700, color: S.navy }}>{hw.title}</div>
                      <div style={{ fontSize: 12, color: S.grayLight, marginTop: 2, lineHeight: 1.5 }}>{hw.desc}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Ideal for */}
            <div style={{
              marginTop: 20, padding: "16px 20px", background: selected.colorBg, borderRadius: 12,
              display: "flex", alignItems: "flex-start", gap: 12
            }}>
              <span style={{ fontSize: 18, marginTop: 1 }}>🎯</span>
              <div>
                <div style={{ fontSize: 12, fontWeight: 700, color: selected.color, marginBottom: 4 }}>IDEAL FOR</div>
                <div style={{ fontSize: 13, color: S.navy, lineHeight: 1.6 }}>{selected.idealFor}</div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Waitlist CTA */}
      <div style={{
        background: `linear-gradient(135deg, #8B5CF6 0%, #6D28D9 100%)`, borderRadius: 16, padding: "28px 32px",
        display: "flex", alignItems: "center", justifyContent: "space-between"
      }}>
        <div>
          <h3 style={{ color: "#fff", fontSize: 18, fontWeight: 800, margin: "0 0 6px" }}>Get Early Access</h3>
          <p style={{ color: "rgba(255,255,255,0.6)", fontSize: 13, margin: 0 }}>
            Join the waitlist. Active AX merchants will be first to get approved.
          </p>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <input placeholder="Enter your email" style={{
            border: "2px solid rgba(255,255,255,0.2)", borderRadius: 10, padding: "0 16px", height: 44,
            fontSize: 13, fontFamily: "inherit", background: "rgba(255,255,255,0.1)", color: "#fff", width: 240
          }} />
          <button style={{
            padding: "0 28px", height: 44, borderRadius: 10, border: "none", cursor: "pointer", fontFamily: "inherit",
            background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy, fontWeight: 700, fontSize: 14,
            boxShadow: "0 4px 12px rgba(232,168,56,0.3)"
          }}>Join Waitlist</button>
        </div>
      </div>

      {/* AX Credit Score teaser */}
      <div style={{
        marginTop: 16, background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", padding: "20px 24px",
        display: "flex", alignItems: "center", gap: 20
      }}>
        <div style={{
          width: 80, height: 80, borderRadius: "50%", position: "relative",
          background: `conic-gradient(${S.green} 0% 72%, #f1f5f9 72% 100%)`
        }}>
          <div style={{
            position: "absolute", inset: 8, borderRadius: "50%", background: "#fff",
            display: "flex", alignItems: "center", justifyContent: "center", flexDirection: "column"
          }}>
            <div style={{ fontSize: 20, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono', monospace", lineHeight: 1 }}>720</div>
            <div style={{ fontSize: 8, color: S.grayLight, fontWeight: 600 }}>AX SCORE</div>
          </div>
        </div>
        <div>
           <div style={{ fontSize: 16, fontWeight: 700, color: S.navy }}>Healthy Credit Profile</div>
           <div style={{ fontSize: 13, color: S.gray, marginTop: 4 }}>You Are in the top 15% of merchants. Qualified for Level 2 financing.</div>
        </div>
      </div>
    </div>
  );
}
