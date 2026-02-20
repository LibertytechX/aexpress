/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { I } from '@/components/icons';
import { S } from '@/components/common/theme';
import { useDispatcher } from '@/contexts/DispatcherContext';
import { CreateOrderModal } from '@/components/modals/CreateOrderModal';
import {
    //  CUSTOMERS_DATA, 
    MSG_RIDER,
    MSG_CUSTOMER
} from '@/data/mockData';

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    const { user, authState, orders, riders, merchants, handleLogout } = useDispatcher();
    const pathname = usePathname() || '';
    const router = useRouter();

    const [showCreateModal, setShowCreateModal] = useState(false);
    const [sidebarOpen, setSidebarOpen] = useState(false);
    const [collapsed, setCollapsed] = useState(false);
    const [profileOpen, setProfileOpen] = useState(false);

    React.useEffect(() => {
        if (authState === "login" || authState === "signup") {
            router.replace(`/${authState}`);
        }
    }, [authState, router]);

    if (authState !== "authenticated") return null;

    const navItems = [
        { id: "Dashboard", href: "/dashboard", icon: I.dashboard },
        { id: "Orders", href: "/orders", icon: I.orders },
        { id: "Riders", href: "/riders", icon: I.riders },
        { id: "Merchants", href: "/merchants", icon: I.merchants },
        { id: "Customers", href: "/customers", icon: I.customers },
        { id: "Messaging", href: "/messaging", icon: I.messaging },
        { id: "Settings", href: "/settings", icon: I.settings },
    ];

    const activeMenu = navItems.find(m => m.href === pathname || (pathname.startsWith(m.href) && m.href !== "/dashboard")) || navItems[0];

    return (
        <div className='flex h-screen w-full p-2 gap-2 overflow-hidden font-sans' style={{ background: S.navy }}>
            <style jsx global>{`
                .no-scrollbar::-webkit-scrollbar {
                  display: none;
                }
                .no-scrollbar {
                  -ms-overflow-style: none;
                  scrollbar-width: none;
                }
                @keyframes slideIn { from { transform: translateX(30px); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
                @keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
                @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
                ::-webkit-scrollbar { width: 6px; } ::-webkit-scrollbar-track { background: transparent; } ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 3px; }
            `}</style>

            {/* Mobile overlay */}
            {sidebarOpen && <div onClick={() => setSidebarOpen(false)} style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)", zIndex: 40 }} />}

            {/* SIDEBAR */}
            <aside
                className={`shrink-0 fixed inset-y-0 md:relative md:inset-auto z-50 flex flex-col transition-[width,left] duration-300 ${sidebarOpen ? "left-0" : "-left-[260px]"} md:left-0 shadow-2xl overflow-y-auto no-scrollbar md:rounded-[30px]`}
                style={{
                    width: collapsed ? 80 : 260,
                    background: S.navy,
                }}
            >
                {/* Sidebar corner accents */}
                <div className="absolute bottom-0 left-0 pointer-events-none z-0 overflow-hidden w-28 h-28">
                    <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" className="absolute bottom-0 left-0 w-full h-full opacity-[0.05]">
                        <circle cx="0" cy="200" r="60" fill="none" stroke="#fff" strokeWidth="24" />
                        <circle cx="0" cy="200" r="100" fill="none" stroke="#FBB12F" strokeWidth="14" />
                        <circle cx="0" cy="200" r="140" fill="none" stroke="#fff" strokeWidth="8" />
                    </svg>
                </div>
                <div className="absolute bottom-0 right-0 pointer-events-none z-0 overflow-hidden w-28 h-28">
                    <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" className="absolute bottom-0 right-0 w-full h-full opacity-[0.05]">
                        <circle cx="200" cy="200" r="60" fill="none" stroke="#FBB12F" strokeWidth="24" />
                        <circle cx="200" cy="200" r="100" fill="none" stroke="#fff" strokeWidth="14" />
                        <circle cx="200" cy="200" r="140" fill="none" stroke="#FBB12F" strokeWidth="8" />
                    </svg>
                </div>

                {/* Logo */}
                <div style={{ padding: "24px 20px 20px", position: "relative", zIndex: 10 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, justifyContent: collapsed ? "center" : "flex-start" }}>
                        <div style={{
                            width: 36, height: 36, borderRadius: 10, background: S.gold,
                            display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 800, fontSize: 16, color: S.navy,
                            fontFamily: "'Outfit', sans-serif", boxShadow: "0 4px 10px rgba(251, 177, 47, 0.3)"
                        }}>AX</div>
                        {!collapsed && (
                            <div>
                                <div style={{ color: "#fff", fontWeight: 700, fontSize: 18, letterSpacing: "-0.5px", fontFamily: "'Outfit', sans-serif" }}>AX DISPATCH</div>
                                <div style={{ color: "rgba(255,255,255,0.6)", fontSize: 11, fontWeight: 500, marginTop: -2, letterSpacing: "2px", textTransform: "uppercase" }}>PORTAL v2.0</div>
                            </div>
                        )}
                    </div>
                </div>

                {/* KPI Overview (Uncollapsed only) */}
                {!collapsed && (
                    <div style={{ padding: "0 14px 12px", display: "flex", gap: 8, position: "relative", zIndex: 10 }}>
                        {[
                            { v: orders.filter((o: any) => ["In Transit", "Picked Up", "Assigned"].includes(o.status)).length, l: "ACTIVE", c: S.gold, bg: "rgba(232,168,56,0.12)" },
                            { v: riders.filter((r: any) => r.status === "online").length, l: "ONLINE", c: S.green, bg: "rgba(22,163,74,0.12)" },
                            { v: orders.filter((o: any) => o.status === "Pending").length, l: "PENDING", c: S.yellow, bg: "rgba(245,158,11,0.12)" }
                        ].map(s => (
                            <div key={s.l} style={{ flex: 1, padding: '8px 4px', borderRadius: 8, background: s.bg, textAlign: "center" }}>
                                <div style={{ fontSize: 14, fontWeight: 800, color: s.c, fontFamily: "'Space Mono',monospace" }}>{s.v}</div>
                                <div style={{ fontSize: 8, color: "rgba(255,255,255,0.5)", fontWeight: 700, marginTop: 2 }}>{s.l}</div>
                            </div>
                        ))}
                    </div>
                )}


                {/* Nav */}
                <nav style={{ flex: 1, padding: "12px 16px", display: "flex", flexDirection: "column", gap: 4, position: "relative", zIndex: 10 }}>
                    {navItems.map(item => {
                        const active = item.id === activeMenu.id;
                        let count = 0;
                        if (item.id === "Orders") count = orders.filter((o: any) => o.status === "Pending").length;
                        if (item.id === "Riders") count = riders.filter((r: any) => r.status === "online").length;
                        if (item.id === "Messaging") count = MSG_RIDER.reduce((s: number, msg: any) => s + msg.unread, 0) + MSG_CUSTOMER.reduce((s: number, msg: any) => s + msg.unread, 0);

                        return (
                            <Link key={item.id} href={item.href}
                                onClick={() => setSidebarOpen(false)}
                                title={collapsed ? item.id : ""}
                                className={`relative group flex items-center gap-3 rounded-xl transition-all duration-200 ${collapsed ? "justify-center py-3" : "px-4 py-3"}`}
                                style={{
                                    background: active ? S.gold : "transparent",
                                    color: active ? S.navy : "rgba(255,255,255,0.7)",
                                    fontWeight: active ? 600 : 500,
                                    textDecoration: "none",
                                    boxShadow: active ? "0 4px 12px rgba(251, 177, 47, 0.25)" : "none"
                                }}
                            >
                                <span style={{
                                    color: active ? S.navy : "rgba(255,255,255,0.7)",
                                    transition: "color 0.2s",
                                    transform: active ? "scale(1.05)" : "scale(1)"
                                }} className="group-hover:text-white">
                                    {React.cloneElement(item.icon as React.ReactElement<any>, {
                                        strokeWidth: active ? 2.5 : 2,
                                        stroke: "currentColor",
                                        width: 20, height: 20
                                    })}
                                </span>

                                {!collapsed && (
                                    <>
                                        <span style={{ fontFamily: "'Outfit', sans-serif" }} className={`text-[13px] ${!active && 'group-hover:text-white'} transition-colors`}>{item.id}</span>
                                        {(count > 0 || item.id === "Riders") && (
                                            <span style={{
                                                marginLeft: "auto",
                                                background: active ? S.navy : "rgba(255,255,255,0.1)",
                                                color: active ? "#ffffff" : "#ffffff",
                                                fontSize: 10, fontWeight: 700,
                                                padding: "2px 8px", borderRadius: 20
                                            }}>{count > 0 ? count : (item.id === "Riders" ? 0 : "")}</span>
                                        )}
                                    </>
                                )}
                            </Link>
                        );
                    })}
                </nav>

                <div style={{ marginTop: "auto", position: "relative", zIndex: 10 }}>
                    {!collapsed && (
                        <div style={{ padding: "12px 14px", borderTop: "1px solid rgba(255,255,255,0.08)", marginBottom: 10 }}>
                            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                                <div style={{ width: 32, height: 32, borderRadius: "50%", background: "rgba(232,168,56,0.15)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 800, color: S.gold }}>
                                    {user?.name?.slice(0, 2).toUpperCase() || "CN"}
                                </div>
                                <div>
                                    <div style={{ fontSize: 12, fontWeight: 600, color: "#fff" }}>{user?.name || "Dispatcher"}</div>
                                    <div style={{ fontSize: 10, color: "rgba(255,255,255,0.4)" }}>Dispatcher</div>
                                </div>
                            </div>
                        </div>
                    )}

                    <div style={{ padding: "0 14px 20px" }}>
                        <button onClick={handleLogout} className="w-full flex justify-center items-center gap-2 p-2.5 rounded-xl hover:bg-red-500/10 transition-colors group cursor-pointer border-none bg-transparent">
                            <span style={{ color: "#EF4444" }}>{I.logout}</span>
                            {!collapsed && <span style={{ fontSize: 13, fontWeight: 600, color: "#EF4444" }}>Log Out</span>}
                        </button>
                    </div>
                </div>
            </aside>

            {/* MAIN CONTENT */}
            <main className="flex-1 flex flex-col min-w-0 bg-[#F8FAFC] shadow-2xl overflow-hidden relative md:rounded-[30px]">
                {/* Corner accent patterns */}
                <div className="absolute bottom-0 left-0 pointer-events-none z-0 overflow-hidden w-52 h-52">
                    <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" className="absolute bottom-0 left-0 w-full h-full opacity-[0.03]">
                        <circle cx="0" cy="200" r="60" fill="none" stroke="#2F3758" strokeWidth="20" />
                        <circle cx="0" cy="200" r="100" fill="none" stroke="#FBB12F" strokeWidth="12" />
                        <circle cx="0" cy="200" r="140" fill="none" stroke="#2F3758" strokeWidth="8" />
                        <circle cx="0" cy="200" r="175" fill="none" stroke="#FBB12F" strokeWidth="5" />
                    </svg>
                </div>
                <div className="absolute bottom-0 right-0 pointer-events-none z-0 overflow-hidden w-52 h-52">
                    <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" className="absolute bottom-0 right-0 w-full h-full opacity-[0.03]">
                        <circle cx="200" cy="200" r="60" fill="none" stroke="#FBB12F" strokeWidth="20" />
                        <circle cx="200" cy="200" r="100" fill="none" stroke="#2F3758" strokeWidth="12" />
                        <circle cx="200" cy="200" r="140" fill="none" stroke="#FBB12F" strokeWidth="8" />
                        <circle cx="200" cy="200" r="175" fill="none" stroke="#2F3758" strokeWidth="5" />
                    </svg>
                </div>

                {/* Top Bar */}
                <header className="bg-white/80 backdrop-blur-md sticky top-0 z-30 flex items-center h-16 px-4 md:px-6 border-b border-slate-100/50 transition-all">
                    <button onClick={() => setSidebarOpen(true)} className="md:hidden flex items-center justify-center p-2 mr-2 text-[#2F3758] rounded-full hover:bg-slate-100 transition-colors bg-transparent border-none cursor-pointer">
                        {I.menu}
                    </button>

                    <button onClick={() => setCollapsed(!collapsed)} className="hidden md:flex items-center justify-center p-2 mr-4 text-[#2F3758] rounded-full hover:bg-slate-100 transition-colors bg-transparent border-none cursor-pointer">
                        {collapsed ? I.menu : I.back}
                    </button>

                    <div className="flex-1 min-w-0">
                        <h1 className="text-lg md:text-xl font-bold text-[#2F3758] truncate font-['Outfit']">
                            {activeMenu.id}
                        </h1>
                    </div>

                    <div className="flex items-center gap-3 md:gap-4 pl-2">
                        <div className="relative">
                            <button
                                onClick={() => setProfileOpen(!profileOpen)}
                                className="flex items-center gap-2 md:gap-3 pl-1 pr-1 md:pr-3 py-1 rounded-full hover:bg-slate-50 transition-all border border-transparent hover:border-slate-100 cursor-pointer bg-transparent"
                            >
                                <div className="hidden md:block text-right">
                                    <div className="text-[13px] font-bold text-[#2F3758] leading-tight max-w-[150px] truncate">
                                        {user?.name || "Edmund Giwa"}
                                    </div>
                                    <div className="text-[10px] text-slate-400 font-medium text-right">Admin</div>
                                </div>
                                <div className="w-9 h-9 md:w-10 md:h-10 rounded-full bg-[#e2e8f0] flex items-center justify-center shadow-sm">
                                </div>
                            </button>

                            {/* Dropdown Backdrop */}
                            {profileOpen && (
                                <div style={{ position: "fixed", inset: 0, zIndex: 40 }} onClick={() => setProfileOpen(false)} />
                            )}

                            {/* Dropdown content */}
                            {profileOpen && (
                                <div style={{
                                    position: "absolute", top: "120%", right: 0, width: 220,
                                    background: "#fff", borderRadius: 16,
                                    boxShadow: "0 10px 40px rgba(0,0,0,0.1), 0 2px 10px rgba(0,0,0,0.05)",
                                    border: "1px solid #f1f5f9", overflow: "hidden", zIndex: 50,
                                    animation: "fadeIn 0.2s ease"
                                }}>
                                    <div style={{ padding: "16px", background: "#f8fafc", borderBottom: "1px solid #f1f5f9" }}>
                                        <div style={{ fontSize: 14, fontWeight: 700, color: S.navy }}>{user?.name}</div>
                                        <div style={{ fontSize: 11, color: S.textMuted, marginTop: 2 }}>{user?.email || "admin@aexpress.com"}</div>
                                    </div>
                                    <div style={{ borderTop: "1px solid #f1f5f9", padding: 6 }}>
                                        <button onClick={handleLogout} className="flex items-center gap-3 w-full p-3 rounded-xl hover:bg-red-50 transition-colors text-left group cursor-pointer border-none bg-transparent">
                                            <span style={{ color: "#EF4444", fontSize: 16 }}>{I.logout}</span>
                                            <span style={{ fontSize: 13, fontWeight: 600, color: "#EF4444" }}>Log Out</span>
                                        </button>
                                    </div>
                                </div>
                            )}
                        </div>

                        <button
                            onClick={() => setShowCreateModal(true)}
                            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-[#2F3758] text-white font-bold text-sm shadow-md hover:shadow-lg transition-all cursor-pointer border-none"
                        >
                            <span className="text-sm">+</span> New Order
                        </button>
                    </div>
                </header>

                {/* Scrollable Page Content */}
                <div className="no-scrollbar relative z-10" style={{ flex: 1, padding: "24px", overflowY: "auto" }}>
                    {children}
                </div>
            </main>

            {showCreateModal && <CreateOrderModal riders={riders} merchants={merchants} onClose={() => setShowCreateModal(false)} />}
        </div>
    );
}
