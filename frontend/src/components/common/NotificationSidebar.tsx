import React from 'react';
import { Icons } from '../Icons';

interface NotificationSidebarProps {
    isOpen: boolean;
    onClose: () => void;
}

// ─── STYLES ─────────────────────────────────────────────────────
const S = {
    navy: "#2F3758",
    navyLight: "#3E4C70",
    gold: "#FBB12F",
    goldLight: "#FDCB6E",
    goldPale: "#FFF8E1",
    green: "#00B67A",
    greenBg: "#E0F7EF",
    red: "#EF4444",
    redBg: "#FEE2E2",
    white: "#ffffff",
    gray: "#64748b",
    grayLight: "#94a3b8",
    grayBg: "#F8FAFC",
    border: "#E2E8F0",
};

// ─── MOCK DATA ──────────────────────────────────────────────────
const NOTIFICATIONS = [
    {
        id: 1,
        type: 'order',
        title: 'Order Delivered',
        message: 'Your order #6158190 has been successfully delivered.',
        time: '2 hours ago',
        read: false,
        icon: (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" /><polyline points="22 4 12 14.01 9 11.01" />
            </svg>
        ),
        color: S.green,
        bg: S.greenBg,
    },
    {
        id: 2,
        type: 'system',
        title: 'Wallet Funded',
        message: 'You successfully added ₦10,000 to your wallet via Card.',
        time: '5 hours ago',
        read: true,
        icon: (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 12V7H5a2 2 0 0 1 0-4h14v4" /><path d="M3 5v14a2 2 0 0 0 2 2h16v-5" /><path d="M18 12a2 2 0 0 0 0 4h4v-4Z" />
            </svg>
        ),
        color: S.navy,
        bg: "#E2E8F0",
    },
    {
        id: 3,
        type: 'alert',
        title: 'Order Canceled',
        message: 'Order #6157980 has been canceled. ₦1,800 refunded.',
        time: '1 day ago',
        read: true,
        icon: (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" /><line x1="12" y1="8" x2="12" y2="12" /><line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
        ),
        color: S.red,
        bg: S.redBg,
    },
];

const PROMOTIONS = [
    {
        id: 1,
        title: 'Weekend Delivery Promo',
        description: 'Get 20% off all Bike deliveries this weekend using code WEEKEND20.',
        color: S.gold,
        bg: `linear-gradient(135deg, ${S.navy} 0%, #1a2035 100%)`,
        textColor: S.white,
        badgeBg: 'rgba(255,255,255,0.2)',
        badgeText: 'Offer',
    },
    {
        id: 2,
        title: 'Refer & Earn',
        description: 'Invite another merchant and earn ₦5,000 when they complete their first 5 deliveries.',
        color: S.green,
        bg: `linear-gradient(135deg, ${S.greenBg} 0%, #ffffff 100%)`,
        textColor: S.navy,
        badgeBg: S.green,
        badgeText: 'Rewards',
        border: `1px solid ${S.green}40`
    },
];

export default function NotificationSidebar({ isOpen, onClose }: NotificationSidebarProps) {
    if (!isOpen) return null;

    return (
        <>
            <div
                onClick={onClose}
                className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-40 transition-opacity"
            />

            <div
                className={`fixed top-0 right-0 h-full w-full max-w-[400px] bg-white z-50 shadow-2xl flex flex-col transform transition-transform duration-300 ${isOpen ? 'translate-x-0' : 'translate-x-full'}`}
            >
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-slate-100">
                    <div>
                        <h2 className="text-xl font-bold font-['Outfit']" style={{ color: S.navy }}>Notifications</h2>
                        <p className="text-sm font-medium" style={{ color: S.grayLight }}>You have 1 unread message</p>
                    </div>
                    <button
                        onClick={onClose}
                        className="w-10 h-10 flex items-center justify-center rounded-full hover:bg-slate-100 transition-colors"
                        style={{ color: S.gray }}
                    >
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                            <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
                        </svg>
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto no-scrollbar pb-6 p-6">

                    {/* Recent Notifications */}
                    <div className="mb-8">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="font-bold text-sm uppercase tracking-wider font-['Outfit']" style={{ color: S.navyLight }}>Recent</h3>
                            <button className="text-xs font-semibold hover:underline" style={{ color: S.gold }}>Mark all as read</button>
                        </div>

                        <div className="space-y-4">
                            {NOTIFICATIONS.map((notif) => (
                                <div
                                    key={notif.id}
                                    className={`p-4 rounded-2xl border transition-all hover:shadow-md cursor-pointer ${notif.read ? 'bg-white border-slate-100' : 'bg-slate-50 border-slate-200'}`}
                                >
                                    <div className="flex gap-4">
                                        <div className="w-12 h-12 shrink-0 rounded-full flex items-center justify-center shadow-sm" style={{ backgroundColor: notif.bg, color: notif.color }}>
                                            {notif.icon}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center justify-between mb-1">
                                                <h4 className="font-bold text-sm truncate pr-2 font-['Outfit']" style={{ color: S.navy }}>{notif.title}</h4>
                                                <span className="text-xs font-medium shrink-0" style={{ color: S.grayLight }}>{notif.time}</span>
                                            </div>
                                            <p className="text-sm leading-relaxed" style={{ color: S.gray }}>{notif.message}</p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Promotions & Offers */}
                    <div>
                        <h3 className="font-bold text-sm uppercase tracking-wider mb-4 font-['Outfit']" style={{ color: S.navyLight }}>Promotions & Offers</h3>

                        <div className="space-y-4">
                            {PROMOTIONS.map((promo) => (
                                <div
                                    key={promo.id}
                                    className="p-5 rounded-2xl relative overflow-hidden group cursor-pointer"
                                    style={{ background: promo.bg, border: promo.border || 'none', boxShadow: '0 4px 15px rgba(0,0,0,0.05)' }}
                                >
                                    {/* Decorative faint circle */}
                                    <div className="absolute -right-8 -top-8 w-24 h-24 rounded-full opacity-10 transition-transform group-hover:scale-110" style={{ backgroundColor: promo.textColor }} />

                                    <div className="relative z-10">
                                        <div className="inline-block px-2.5 py-1 rounded-md text-[10px] uppercase tracking-wider font-bold mb-3" style={{ backgroundColor: promo.badgeBg, color: promo.badgeText === 'Rewards' ? '#fff' : promo.textColor }}>
                                            {promo.badgeText}
                                        </div>
                                        <h4 className="font-bold text-base mb-2 font-['Outfit']" style={{ color: promo.textColor }}>{promo.title}</h4>
                                        <p className="text-sm opacity-90 leading-relaxed mb-4" style={{ color: promo.textColor }}>{promo.description}</p>
                                        <button
                                            className="text-sm font-bold flex items-center gap-1 hover:gap-2 transition-all"
                                            style={{ color: promo.textColor === S.white ? S.gold : S.navy }}
                                        >
                                            View Details
                                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                                                <path d="M5 12h14M12 5l7 7-7 7" />
                                            </svg>
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                </div>

                {/* Footer */}
                <div className="p-4 border-t border-slate-100 bg-slate-50">
                    <button className="w-full py-3 rounded-xl font-bold text-sm transition-all bg-white border border-slate-200 hover:bg-slate-100 hover:shadow-sm" style={{ color: S.navy }}>
                        View Notification Settings
                    </button>
                </div>
            </div>
        </>
    );
}
