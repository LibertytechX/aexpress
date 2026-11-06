'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import Icons from '@/components/Icons';
import { S } from '@/lib/theme';
import { STATUS_COLORS, getVehicleIcon, getModeBadge, UIOrder } from '@/lib/utils';
import EmailVerificationBanner from './EmailVerificationBanner';
import { User } from '@/lib/api';

interface DashboardScreenProps {
  balance: number;
  orders: UIOrder[];
  currentUser: User | null;
  onNewOrder?: () => void;
  onFund?: () => void;
  onViewOrder?: (id: string | number) => void;
  onGoOrders?: () => void;
  onResendVerification: () => Promise<void> | void;
}

export default function DashboardScreen({
  balance,
  orders,
  onNewOrder,
  onFund,
  onViewOrder,
  onGoOrders,
  currentUser,
  onResendVerification
}: DashboardScreenProps) {
  const router = useRouter();
  // Safe navigation handlers if props aren't provided
  const handleNewOrder = onNewOrder || (() => router.push('/new-order'));
  const handleFund = onFund || (() => console.log('Fund wallet clicked'));
  const handleGoOrders = onGoOrders || (() => router.push('/orders'));
  const handleViewOrder = onViewOrder || ((id) => router.push(`/orders?id=${id}`));

  const safeOrders = Array.isArray(orders) ? orders : [];
  const recentOrders = safeOrders.slice(0, 4);
  const delivered = safeOrders.filter(o => o.status === "Done").length;
  const pending = safeOrders.filter(o => o.status === "Pending" || o.status === "Assigned" || o.status === "Started").length;
  const totalSpent = safeOrders.reduce((s, o) => s + (o.amount || 0), 0);

  const cards = [
    { label: "Wallet Balance", value: `₦${balance.toLocaleString()}`, sub: "Available funds", bg: S.navy, color: "#fff", icon: Icons.wallet, action: "Fund", onAction: handleFund },
    { label: "Orders This Month", value: safeOrders.length.toString(), sub: `${delivered} delivered`, bg: "#fff", color: S.navy, icon: Icons.bike },
    { label: "Total Spent", value: `₦${totalSpent.toLocaleString()}`, sub: "This month", bg: "#fff", color: S.navy, icon: Icons.check },
    { label: "Avg. Delivery", value: delivered > 0 ? `₦${Math.round(totalSpent / delivered).toLocaleString()}` : "—", sub: "Per order", bg: "#fff", color: S.navy, icon: Icons.pin },
  ];

  return (
    <div style={{ animation: "fadeIn 0.3s ease" }}>
      {/* Welcome */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: S.navy, marginBottom: 4 }}>Welcome back, {currentUser?.business_name || "Merchant"} 👋</h1>
          <p style={{ color: S.gray, fontSize: 15 }}>Here&apos;s what&apos;s happening with your deliveries today.</p>
        </div>
        <button onClick={handleNewOrder} style={{
          padding: "10px 20px", borderRadius: 10, border: "none", cursor: "pointer",
          background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy,
          fontWeight: 700, fontSize: 14, fontFamily: "inherit", display: "flex", alignItems: "center", gap: 8,
          boxShadow: "0 4px 12px rgba(232,168,56,0.25)"
        }}>
          {Icons.newOrder} New Delivery
        </button>
      </div>

      {/* Email Verification Banner */}
      <EmailVerificationBanner
        currentUser={currentUser}
        onResend={onResendVerification}
        onDismiss={() => { }}
      />

      {/* Stat Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: 20, marginBottom: 32 }}>
        {cards.map((c, i) => (
          <div key={i} className="group transition-all duration-300 hover:-translate-y-1" style={{
            background: c.bg, borderRadius: 20, padding: "24px", border: i === 0 ? "none" : `1px solid #e2e8f0`,
            boxShadow: i === 0 ? "0 10px 30px rgba(47, 55, 88, 0.15)" : "0 4px 6px rgba(0,0,0,0.02)",
            position: "relative", overflow: "hidden"
          }}>
            {/* Decoration for first card (Wallet) */}
            {i === 0 && (
              <>
                <div style={{ position: "absolute", top: -20, right: -20, width: 120, height: 120, borderRadius: "50%", background: "rgba(255,255,255,0.05)" }} />
                <div style={{ position: "absolute", bottom: -40, left: -20, width: 100, height: 100, borderRadius: "50%", background: "rgba(255,255,255,0.03)" }} />
              </>
            )}

            {/* Decoration for other cards (Gold Pattern) */}
            {i > 0 && (
              <>
                <div style={{
                  position: "absolute", bottom: -30, right: -30, width: 120, height: 120,
                  borderRadius: "50%", border: "16px solid #FBB12F", opacity: 0.04
                }} />
                <div style={{
                  position: "absolute", bottom: -10, right: -10, width: 80, height: 80,
                  borderRadius: "50%", background: "#FBB12F", opacity: 0.08
                }} />
                <div style={{
                  position: "absolute", bottom: 25, right: 30, width: 20, height: 20,
                  borderRadius: "50%", background: "#FBB12F", opacity: 0.12
                }} />
                <div className="group-hover:scale-110 transition-transform duration-300" style={{
                  position: 'absolute', top: 10, right: 10, opacity: 0.05,
                  transform: 'rotate(15deg) scale(2.5)', pointerEvents: 'none'
                }}>
                  {c.icon}
                </div>
              </>
            )}

            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
              <div style={{
                width: 40, height: 40, borderRadius: 12,
                background: i === 0 ? "rgba(255,255,255,0.1)" : S.grayBg,
                display: "flex", alignItems: "center", justifyContent: "center",
                color: i === 0 ? S.gold : S.navy
              }}>
                {c.icon}
              </div>
              {i === 0 && (
                <div style={{
                  background: "rgba(0,182,122,0.2)", color: S.green, padding: "4px 8px",
                  borderRadius: 20, fontSize: 11, fontWeight: 700, display: "flex", alignItems: "center", gap: 4
                }}>
                  <span>↗</span> +12%
                </div>
              )}
            </div>

            <div style={{ fontSize: 13, fontWeight: 600, color: i === 0 ? "rgba(255,255,255,0.6)" : S.gray, marginBottom: 4 }}>{c.label}</div>
            <div style={{ fontSize: 28, fontWeight: 700, color: c.color, fontFamily: "'Outfit', sans-serif", marginBottom: 4 }}>{c.value}</div>
            <div style={{ fontSize: 12, color: i === 0 ? "rgba(255,255,255,0.4)" : S.grayLight }}>{c.sub}</div>

            {c.action && (
              <button onClick={c.onAction} style={{
                marginTop: 20, width: "100%", padding: "10px", borderRadius: 12, border: "none",
                background: S.gold, color: S.navy, fontWeight: 700, fontSize: 13, cursor: "pointer",
                boxShadow: "0 4px 12px rgba(251, 177, 47, 0.3)", fontFamily: "inherit"
              }}>
                + {c.action}
              </button>
            )}
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))", gap: 12, marginBottom: 28 }}>
        {[
          { label: "Send Package", icon: Icons.bike, action: handleNewOrder },
          { label: "Fund Wallet", icon: Icons.wallet, action: handleFund },
          { label: "Track Order", icon: Icons.search, action: handleGoOrders },
          { label: "Get Support", icon: Icons.support, action: () => router.push('/support') },
        ].map((a, i) => (
          <button key={i} onClick={a.action} className="group transition-all duration-200 hover:shadow-md hover:-translate-y-1" style={{
            background: "#fff", border: "1px solid #e2e8f0", borderRadius: 12, padding: "16px", cursor: "pointer",
            display: "flex", flexDirection: "column", alignItems: "center", gap: 8, fontFamily: "inherit",
          }}>
            <div className="group-hover:scale-110 transition-transform duration-200" style={{ color: S.gold }}>{a.icon}</div>
            <span style={{ fontSize: 13, fontWeight: 600, color: S.navy }}>{a.label}</span>
          </button>
        ))}
      </div>

      {/* Recent Orders */}
      <div style={{ background: "#fff", borderRadius: 20, border: `1px solid #e2e8f0`, boxShadow: "0 4px 6px rgba(0,0,0,0.02)", overflow: "hidden" }}>
        <div style={{ padding: "16px 20px", display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid #f1f5f9" }}>
          <h3 style={{ fontSize: 15, fontWeight: 700, color: S.navy, margin: 0 }}>Recent Orders</h3>
          <button onClick={handleGoOrders} style={{ background: "none", border: "none", color: S.gold, fontSize: 13, fontWeight: 600, cursor: "pointer", fontFamily: "inherit" }}>View All →</button>
        </div>
        {recentOrders.length === 0 ? (
          <div style={{ padding: "40px", textAlign: "center", color: S.gray }}>
            No orders found. Create your first order!
          </div>
        ) : (
          recentOrders.map((order, i) => {
            const st = STATUS_COLORS[order.status] || STATUS_COLORS.Pending;
            return (
              <div key={order.id || i} onClick={() => handleViewOrder(order.id)} style={{
                padding: "14px 20px", display: "flex", alignItems: "center", gap: 14, cursor: "pointer",
                borderBottom: i < recentOrders.length - 1 ? "1px solid #f8fafc" : "none",
                transition: "background 0.15s"
              }}>
                <div style={{ width: 40, height: 40, borderRadius: 10, background: S.goldPale, display: "flex", alignItems: "center", justifyContent: "center", color: S.gold }}>
                  {getVehicleIcon(order.vehicle)}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", gap: 6, marginBottom: 2 }}>
                    <span style={{ fontSize: 14, fontWeight: 600, color: S.navy }}>#{order.order_number || order.id}</span>
                    {order.mode && (() => {
                      const modeBadge = getModeBadge(order.mode);
                      return (
                        <span style={{ fontSize: 9, fontWeight: 600, padding: "2px 6px", borderRadius: 4, background: modeBadge.bg, color: modeBadge.color }}>
                          {modeBadge.label}
                        </span>
                      );
                    })()}
                    {order.deliveries && order.deliveries.length > 1 && (
                      <span style={{ fontSize: 9, fontWeight: 600, padding: "2px 6px", borderRadius: 4, background: "#f1f5f9", color: S.navy }}>
                        {order.deliveries.length} stops
                      </span>
                    )}
                  </div>
                  <div style={{ fontSize: 12, color: S.grayLight, marginTop: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {order.pickup} → {order.deliveries && order.deliveries.length > 1 ? `${order.deliveries.length} locations` : order.dropoff}
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: S.navy }}>₦{(order.amount || 0).toLocaleString()}</div>
                  <span style={{ fontSize: 11, fontWeight: 600, padding: "2px 8px", borderRadius: 6, background: st.bg, color: st.text }}>{st.label}</span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
