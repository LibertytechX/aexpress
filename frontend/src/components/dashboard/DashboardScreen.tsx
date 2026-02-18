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
  const handleFund = onFund || (() => console.log('Fund wallet clicked')); // Fallback to be handled by layout/modal
  const handleGoOrders = onGoOrders || (() => router.push('/orders'));
  const handleViewOrder = onViewOrder || ((id) => router.push(`/orders?id=${id}`));

  const recentOrders = Array.isArray(orders) ? orders.slice(0, 5) : [];
  // Calculate stats
  const pending = Array.isArray(orders) ? orders.filter(o => o.status === 'Pending' || o.status === 'Assigned' || o.status === 'Started').length : 0;
  const delivered = Array.isArray(orders) ? orders.filter(o => o.status === 'Done').length : 0;
  const totalSpent = Array.isArray(orders) ? orders.reduce((sum, o) => sum + (o.amount || 0), 0) : 0;

  const cards = [
    { label: "Wallet Balance", value: `₦${balance.toLocaleString()}`, sub: "Available funds", color: "#E8A838", bg: `linear-gradient(135deg, ${S.navy}, #243656)`, textColor: "#fff", action: "Fund", onAction: handleFund },
    { label: "Orders This Month", value: (orders?.length || 0).toString(), sub: `${delivered} delivered, ${pending} active`, color: "#16a34a", bg: "#fff" },
    { label: "Total Spent", value: `₦${totalSpent.toLocaleString()}`, sub: "This month", color: "#2563eb", bg: "#fff" },
    { label: "Avg. Delivery Cost", value: delivered > 0 ? `₦${Math.round(totalSpent / delivered).toLocaleString()}` : "—", sub: "Per order", color: "#8b5cf6", bg: "#fff" },
  ];

  return (
    <div style={{ animation: "fadeIn 0.3s ease" }}>
      {/* Welcome */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <div>
          <h2 style={{ fontSize: 20, fontWeight: 700, color: S.navy, margin: 0 }}>Good afternoon, {currentUser?.contact_name?.split(' ')[0] || "User"}</h2>
          <p style={{ color: S.gray, fontSize: 14, margin: "4px 0 0" }}>Here's your delivery overview</p>
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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-7">
        {cards.map((c, i) => (
          <div key={i} className="transition-all duration-300 hover:transform hover:-translate-y-1" style={{
            background: c.bg, borderRadius: 14, padding: "20px", border: i > 0 ? "1px solid #e2e8f0" : "none",
            boxShadow: i === 0 ? "0 10px 30px -10px rgba(27,42,74,0.3)" : "0 2px 10px rgba(0,0,0,0.03)",
            position: "relative", overflow: "hidden"
          }}>
            {i === 0 && <div style={{ position: "absolute", top: -30, right: -30, width: 100, height: 100, borderRadius: "50%", background: "rgba(232,168,56,0.1)" }} />}
            <div style={{ fontSize: 12, fontWeight: 600, color: i === 0 ? "rgba(255,255,255,0.6)" : S.gray, textTransform: "uppercase", letterSpacing: "0.5px" }}>{c.label}</div>
            <div style={{ fontSize: 26, fontWeight: 800, color: i === 0 ? "#fff" : S.navy, marginTop: 8, fontFamily: "'Space Mono', monospace" }}>{c.value}</div>
            <div style={{ fontSize: 12, color: i === 0 ? "rgba(255,255,255,0.5)" : S.grayLight, marginTop: 4 }}>{c.sub}</div>
            {c.action && (
              <button onClick={c.onAction} style={{
                marginTop: 12, padding: "6px 14px", borderRadius: 6, border: "1px solid rgba(232,168,56,0.4)",
                background: "rgba(232,168,56,0.15)", color: S.gold, fontSize: 12, fontWeight: 700, cursor: "pointer", fontFamily: "inherit"
              }}>+ {c.action}</button>
            )}
          </div>
        ))}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-7">
        {[
          { label: "Send Package", icon: Icons.bike, action: handleNewOrder },
          { label: "Fund Wallet", icon: Icons.wallet, action: handleFund },
          { label: "Track Order", icon: Icons.search, action: handleGoOrders },
          { label: "Get Support", icon: Icons.support, action: () => router.push('/support') },
        ].map((a, i) => (
          <button key={i} onClick={a.action} className="group transition-all duration-200 hover:shadow-md" style={{
            background: "#fff", border: "1px solid #e2e8f0", borderRadius: 12, padding: "16px", cursor: "pointer",
            display: "flex", flexDirection: "column", alignItems: "center", gap: 8, fontFamily: "inherit",
          }}>
            <div className="group-hover:scale-110 transition-transform duration-200" style={{ color: S.gold }}>{a.icon}</div>
            <span style={{ fontSize: 13, fontWeight: 600, color: S.navy }}>{a.label}</span>
          </button>
        ))}
      </div>

      {/* Recent Orders */}
      <div style={{ background: "#fff", borderRadius: 14, border: "1px solid #e2e8f0", overflow: "hidden" }}>
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
                  </div>
                  <div style={{ fontSize: 13, color: S.gray, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {order.pickup || 'No pickup address'}
                  </div>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: S.navy, fontFamily: "'Space Mono', monospace" }}>₦{(order.amount || 0).toLocaleString()}</div>
                  <span style={{
                    fontSize: 11, fontWeight: 600, padding: "2px 8px", borderRadius: 10,
                    background: st.bg, color: st.text, display: "inline-block", marginTop: 4
                  }}>
                    {st.label}
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
