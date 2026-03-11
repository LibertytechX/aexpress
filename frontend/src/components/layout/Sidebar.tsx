'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import Icons from '@/components/Icons';
import { S } from '@/lib/theme';
import { useAuth } from '@/contexts/AuthContext';

export default function Sidebar({ collapsed = false }) {
  const pathname = usePathname();
  const { logout } = useAuth();

  const menuItems = [
    { id: 'dashboard', label: 'Dashboard', icon: Icons.dashboard, path: '/dashboard' },
    { id: 'orders', label: 'Orders', icon: Icons.orders, path: '/orders' },
    { id: 'wallet', label: 'Wallet', icon: Icons.wallet, path: '/wallet' },
    { id: 'new-order', label: 'New Order', icon: Icons.newOrder, path: '/new-order' },
    { id: 'webpos', label: 'WebPOS', icon: Icons.webpos, path: '/webpos' },
    { id: 'website', label: 'Website', icon: Icons.website, path: '/website' },
    { id: 'settings', label: 'Settings', icon: Icons.settings, path: '/settings' },
    { id: 'support', label: 'Support', icon: Icons.support, path: '/support' },
  ];

  return (
    <div style={{
      width: collapsed ? 80 : 260,
      background: "#fff",
      borderRight: "1px solid #e2e8f0",
      display: "flex",
      flexDirection: "column",
      height: "100%",
      transition: "width 0.3s ease",
      overflow: "hidden"
    }}>
      {/* Brand */}
      <div style={{
        height: 80,
        display: "flex",
        alignItems: "center",
        padding: collapsed ? "0 24px" : "0 24px",
        justifyContent: collapsed ? "center" : "flex-start",
        whiteSpace: "nowrap"
      }}>
        <div style={{
          width: 32, height: 32, borderRadius: 8,
          background: `linear-gradient(135deg, ${S.gold}, #F5C563)`,
          display: "flex", alignItems: "center", justifyContent: "center",
          fontWeight: 800, fontSize: 13, color: S.navy,
          flexShrink: 0,
          fontFamily: "'Space Mono', monospace"
        }}>AX</div>
        {!collapsed && (
          <div style={{
            marginLeft: 10, fontSize: 18, fontWeight: 800, color: S.navy, letterSpacing: "-0.5px",
            opacity: 1, transition: "opacity 0.2s"
          }}>MERCHANT</div>
        )}
      </div>

      {/* Menu */}
      <div style={{ flex: 1, padding: "12px", display: "flex", flexDirection: "column", gap: 4 }}>
        {menuItems.map(item => {
          const isActive = pathname === item.path || pathname.startsWith(item.path + '/');

          return (
            <Link key={item.id} href={item.path} title={collapsed ? item.label : ""} style={{
              display: "flex",
              alignItems: "center",
              justifyContent: collapsed ? "center" : "flex-start",
              padding: collapsed ? "12px 0" : "12px 16px",
              height: 48,
              borderRadius: 10,
              cursor: "pointer",
              transition: "all 0.2s ease",
              textDecoration: "none",
              background: isActive ? S.goldPale : "transparent",
              color: isActive ? S.gold : S.gray,
            }}>
              <div style={{
                color: isActive ? S.gold : "#94a3b8",
                transition: "color 0.2s",
                display: "flex", alignItems: "center", justifyContent: "center"
              }}>
                {item.icon}
              </div>
              {!collapsed && (
                <span style={{ marginLeft: 12, fontSize: 14, fontWeight: isActive ? 700 : 500, whiteSpace: "nowrap" }}>
                  {item.label}
                </span>
              )}
            </Link>
          );
        })}
      </div>

      {/* Footer / Logout */}
      <div style={{ padding: 12, borderTop: "1px solid #f1f5f9" }}>
        <button onClick={logout} title={collapsed ? "Sign Out" : ""} style={{
          width: "100%",
          display: "flex",
          alignItems: "center",
          justifyContent: collapsed ? "center" : "flex-start",
          padding: collapsed ? "12px 0" : "12px 16px",
          height: 48,
          borderRadius: 10,
          cursor: "pointer",
          background: "transparent",
          border: "none",
          color: S.red,
          fontFamily: "inherit",
          transition: "background 0.2s"
        }}>
          <div style={{ opacity: 0.8 }}>{Icons.logout}</div>
          {!collapsed && <span style={{ marginLeft: 12, fontSize: 14, fontWeight: 600, whiteSpace: "nowrap" }}>Sign Out</span>}
        </button>
      </div>
    </div>
  );
}
