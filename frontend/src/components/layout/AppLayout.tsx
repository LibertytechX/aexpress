'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Sidebar from '@/components/layout/Sidebar';
import { S } from '@/lib/theme';
import { useAuth } from '@/contexts/AuthContext';
import Icons from '@/components/Icons';

export default function AppLayout({ children }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = useState(false); // Mobile
  const [collapsed, setCollapsed] = useState(false); // Desktop
  const [fundModal, setFundModal] = useState(false);

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: S.grayBg }}>
        <div style={{ fontSize: 16, fontWeight: 600, color: S.gray }}>Loading...</div>
      </div>
    );
  }

  if (!user) return null;

  const getTitle = () => {
    if (pathname === '/dashboard') return 'Dashboard';
    if (pathname === '/orders') return 'Orders';
    if (pathname === '/new-order') return 'New Delivery';
    if (pathname === '/wallet') return 'Wallet';
    if (pathname === '/settings') return 'Settings';
    if (pathname === '/support') return 'Support';
    return 'Assured Express';
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: S.grayBg, fontFamily: "'DM Sans', 'Segoe UI', sans-serif" }}>
      {/* Mobile overlay */}
      {sidebarOpen && <div onClick={() => setSidebarOpen(false)} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)", zIndex: 40 }} />}

      {/* Desktop Sidebar */}
      <aside
        style={{
          width: collapsed ? 80 : 260,
          transition: "width 0.3s ease",
          zIndex: 50
        }}
        className="fixed top-0 bottom-0 left-0 hidden md:block bg-white border-r border-slate-200 h-full"
      >
        <Sidebar collapsed={collapsed} />
      </aside>

      {/* Mobile Sidebar */}
      <aside
        style={{
          width: 260,
          transform: sidebarOpen ? 'translateX(0)' : 'translateX(-100%)',
          transition: 'transform 0.3s ease',
          zIndex: 50
        }}
        className="fixed top-0 bottom-0 left-0 md:hidden bg-white h-full shadow-xl"
      >
        <Sidebar collapsed={false} />
      </aside>

      {/* MAIN CONTENT */}
      <main style={{
        flex: 1,
        display: "flex",
        flexDirection: "column",
        minWidth: 0,
        marginLeft: 0,
        paddingLeft: 0, // Reset for mobile
      }} className={`transition-all duration-300 ${collapsed ? 'md:ml-[80px]' : 'md:ml-[260px]'}`}>

        {/* Top Bar */}
        <header style={{
          background: "#fff", padding: "0 24px", height: 64, display: "flex", alignItems: "center", gap: 16,
          borderBottom: `1px solid ${S.grayBg}`, position: "sticky", top: 0, zIndex: 30
        }}>
          {/* Mobile Toggle */}
          <button onClick={() => setSidebarOpen(true)} className="md:hidden" style={{
            background: "none", border: "none", cursor: "pointer", padding: 4, display: "flex", color: S.navy
          }}>{Icons.menu}</button>

          {/* Desktop Toggle (Collapsible) */}
          <button onClick={() => setCollapsed(!collapsed)} className="hidden md:flex" style={{
            background: "none", border: "none", cursor: "pointer", padding: 4, color: S.gray,
            transform: collapsed ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.3s"
          }}>
            {/* Simple arrow icon or menu icon */}
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
          </button>

          <div style={{ flex: 1 }}>
            <h1 style={{ fontSize: 18, fontWeight: 700, color: S.navy, margin: 0 }}>
              {getTitle()}
            </h1>
          </div>

          <button onClick={() => setFundModal(true)} style={{
            padding: "8px 16px", borderRadius: 8, border: "none", cursor: "pointer", fontFamily: "inherit",
            background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy,
            fontWeight: 700, fontSize: 13, display: "flex", alignItems: "center", gap: 6,
            whiteSpace: "nowrap"
          }}>
            <span style={{ fontSize: 16 }}>+</span> <span className="hidden sm:inline">Fund Wallet</span>
          </button>

          <div style={{ position: "relative" }}>
            <button style={{ background: "none", border: "none", cursor: "pointer", color: S.gray, padding: 4 }}>{Icons.bell}</button>
            <div style={{ position: "absolute", top: 2, right: 2, width: 8, height: 8, borderRadius: "50%", background: S.red }} />
          </div>
        </header>

        {/* Page Content */}
        <div style={{ flex: 1, padding: "24px", overflowY: "auto" }}>
          {children}
        </div>
      </main>

      {/* Fund Modal Placeholder - to be implemented */}
      {fundModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ background: 'white', padding: 20, borderRadius: 10 }}>
            <h3>Fund Wallet</h3>
            <p>Modal functionality to be implemented.</p>
            <button onClick={() => setFundModal(false)}>Close</button>
          </div>
        </div>
      )}
    </div>
  );
}
