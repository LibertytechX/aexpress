'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Phone, Lock, ArrowRight, Loader2, Eye, EyeOff, Package, Zap, Shield } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import Image from 'next/image';
import Logo from '@/components/ui/logo';

const slides = [
    {
        title: "Deliver Anything,",
        subtitle: "Anywhere in Lagos",
        description: "Experience seamless logistics with our advanced delivery network. Fund your wallet, create orders, and track deliveries in real-time.",
        stats: [
            { label: "Active Riders", value: "500+", color: "#FBB12F" },
            { label: "Avg Delivery", value: "25min", color: "#00B67A" },
            { label: "Starting From", value: "₦1,000", color: "white" }
        ]
    },
    {
        title: "Real-Time Tracking",
        subtitle: "For Peace of Mind",
        description: "Monitor your packages every step of the way. Our advanced tracking system ensures you always know where your delivery is.",
        stats: [
            { label: "Live Updates", value: "100%", color: "#FBB12F" },
            { label: "Satisfaction", value: "4.9/5", color: "#00B67A" },
            { label: "Coverage", value: "Lagos", color: "white" }
        ]
    },
    {
        title: "Empowering Merchants",
        subtitle: "To Grow Faster",
        description: "Tools designed for your business. Manage multiple orders, view analytics, and streamline your logistics operations.",
        stats: [
            { label: "Merchants", value: "2k+", color: "#FBB12F" },
            { label: "Growth", value: "3x", color: "#00B67A" },
            { label: "Support", value: "24/7", color: "white" }
        ]
    }
];

const mobileFeatures = [
    { icon: Zap, label: "25min avg delivery", color: "#FBB12F" },
    { icon: Shield, label: "Fully insured", color: "#00B67A" },
    { icon: Package, label: "500+ riders", color: "#FBB12F" },
];

export default function LoginPage() {
    const router = useRouter();
    const { login } = useAuth();
    const [phone, setPhone] = useState("");
    const [pass, setPass] = useState("");
    const [showPass, setShowPass] = useState(false);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [currentSlide, setCurrentSlide] = useState(0);

    useEffect(() => {
        const timer = setInterval(() => {
            setCurrentSlide((prev) => (prev + 1) % slides.length);
        }, 5000);
        return () => clearInterval(timer);
    }, []);

    const handleLogin = async () => {
        if (!phone || !pass) {
            setError("Please enter phone and password");
            return;
        }
        try {
            setLoading(true);
            setError("");
            const success = await login(phone, pass);
            if (!success) {
                setError("Login failed. Please check your credentials.");
            }
        } catch (err: any) {
            setError(err.message || "Login failed. Please check your credentials.");
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') handleLogin();
    };

    return (
        <div className="min-h-screen w-full flex bg-white font-sans overflow-hidden">

            {/* ─── LEFT PANEL (desktop only) ─── */}
            <div className="hidden lg:flex w-[55%] relative overflow-hidden bg-[#2F3758] flex-col justify-between p-12 z-0">
                <div className="absolute inset-0 z-0">
                    <div className="absolute inset-0 opacity-[0.05]" style={{ backgroundImage: 'radial-gradient(#ffffff 1.5px, transparent 1.5px)', backgroundSize: '40px 40px' }} />
                    <motion.div initial={{ opacity: 0 }} animate={{ y: [0, -30, 0], rotate: [0, 10, 0], opacity: [0.1, 0.2, 0.1] }} transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }} className="absolute top-[15%] left-[10%] w-24 h-24 rounded-full border-2 border-[#FBB12F]/30 z-0" />
                    <motion.div animate={{ y: [0, 40, 0], rotate: 360, scale: [1, 1.1, 1] }} transition={{ duration: 25, repeat: Infinity, ease: "linear" }} className="absolute top-[10%] right-[15%] w-48 h-48 border border-[#00B67A]/20 rounded-full z-0 opacity-30" />
                    <motion.div animate={{ x: [0, 30, 0], y: [0, 20, 0] }} transition={{ duration: 15, repeat: Infinity, ease: "easeInOut" }} className="absolute bottom-[30%] left-[5%] w-32 h-32 bg-[#FBB12F]/10 rounded-full blur-xl" />
                    <motion.div animate={{ rotate: -360 }} transition={{ duration: 30, repeat: Infinity, ease: "linear" }} className="absolute top-[-5%] right-[-5%] w-[400px] h-[400px] border-[2px] border-dashed border-[#ffffff]/10 rounded-full" />
                    <motion.div animate={{ rotate: 360 }} transition={{ duration: 40, repeat: Infinity, ease: "linear" }} className="absolute bottom-[-10%] left-[-10%] w-[600px] h-[600px] border-[1px] border-[#ffffff]/5 rounded-full" />
                    <div className="absolute top-[-20%] right-[-10%] w-[600px] h-[600px] bg-[#FBB12F]/5 blur-[100px] rounded-full" />
                    <div className="absolute bottom-[-10%] left-[-20%] w-[800px] h-[800px] bg-[#00B67A]/5 blur-[120px] rounded-full" />
                </div>

                <motion.div initial={{ opacity: 0, y: -20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6 }} className="relative z-10 flex items-center gap-3">
                    <Logo />
                </motion.div>

                <div className="relative z-10 flex-1 flex flex-col justify-center max-w-xl pb-20">
                    <AnimatePresence mode="wait">
                        <motion.div key={currentSlide} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.5 }} className="space-y-6">
                            <h1 className="text-white text-4xl lg:text-5xl font-extrabold leading-tight">
                                {slides[currentSlide].title} <br />
                                <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#FBB12F] to-[#ffd074]">{slides[currentSlide].subtitle}</span>
                            </h1>
                            <p className="text-slate-300 text-lg leading-relaxed max-w-md h-[84px]">{slides[currentSlide].description}</p>
                            <div className="flex gap-8 pt-4">
                                {slides[currentSlide].stats.map((stat, i) => (
                                    <div key={i} className="flex flex-col">
                                        <span className="text-2xl font-bold font-mono" style={{ color: stat.color }}>{stat.value}</span>
                                        <span className="text-slate-400 text-xs font-medium uppercase tracking-wider">{stat.label}</span>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    </AnimatePresence>
                    <div className="flex gap-2 mt-12">
                        {slides.map((_, index) => (
                            <button key={index} onClick={() => setCurrentSlide(index)} className={`h-1.5 rounded-full transition-all duration-300 ${currentSlide === index ? "w-8 bg-[#FBB12F]" : "w-2 bg-slate-600 hover:bg-slate-500"}`} />
                        ))}
                    </div>
                </div>

                <div className="absolute bottom-0 right-0 w-full h-[55%] pointer-events-none z-0">
                    <motion.div initial={{ x: 100, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ duration: 1, delay: 0.8, type: "spring", stiffness: 60 }} className="absolute bottom-[8%] right-[-2%] w-[45%] z-20" style={{ filter: 'drop-shadow(0 20px 30px rgba(0,0,0,0.4))' }}>
                        <Image src="/bike_img.png" alt="Delivery Bike" width={600} height={400} className="object-contain" priority />
                    </motion.div>
                </div>
            </div>

            {/* ─── RIGHT PANEL / MOBILE FULL PAGE ─── */}
            <div className="flex-1 flex flex-col bg-white relative overflow-hidden">

                {/* ══════════════════════════════════════════
                    MOBILE HERO HEADER (hidden on lg)
                ══════════════════════════════════════════ */}
                <div className="lg:hidden relative w-full overflow-hidden" style={{ minHeight: '280px' }}>

                    {/* Deep navy base */}
                    <div className="absolute inset-0 bg-[#1e2540]" />

                    {/* Animated mesh gradient */}
                    <div className="absolute inset-0">
                        <motion.div
                            animate={{ x: [0, 40, 0], y: [0, -20, 0] }}
                            transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
                            className="absolute top-[-30%] right-[-20%] w-[320px] h-[320px] rounded-full"
                            style={{ background: 'radial-gradient(circle, rgba(251,177,47,0.25) 0%, transparent 70%)' }}
                        />
                        <motion.div
                            animate={{ x: [0, -30, 0], y: [0, 30, 0] }}
                            transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 2 }}
                            className="absolute bottom-[-20%] left-[-10%] w-[280px] h-[280px] rounded-full"
                            style={{ background: 'radial-gradient(circle, rgba(0,182,122,0.2) 0%, transparent 70%)' }}
                        />
                        <motion.div
                            animate={{ scale: [1, 1.2, 1], opacity: [0.15, 0.3, 0.15] }}
                            transition={{ duration: 7, repeat: Infinity, ease: "easeInOut", delay: 1 }}
                            className="absolute top-[30%] left-[40%] w-[200px] h-[200px] rounded-full"
                            style={{ background: 'radial-gradient(circle, rgba(251,177,47,0.15) 0%, transparent 70%)' }}
                        />
                    </div>

                    {/* Dot grid pattern */}
                    <div
                        className="absolute inset-0 opacity-[0.12]"
                        style={{ backgroundImage: 'radial-gradient(rgba(255,255,255,0.8) 1px, transparent 1px)', backgroundSize: '24px 24px' }}
                    />

                    {/* Diagonal stripe accent */}
                    <div
                        className="absolute inset-0 opacity-[0.04]"
                        style={{ backgroundImage: 'repeating-linear-gradient(45deg, #FBB12F 0px, #FBB12F 1px, transparent 1px, transparent 32px)' }}
                    />

                    {/* Spinning rings */}
                    <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 35, repeat: Infinity, ease: "linear" }}
                        className="absolute top-[-60px] right-[-60px] w-[200px] h-[200px] rounded-full border border-dashed border-[#FBB12F]/25"
                    />
                    <motion.div
                        animate={{ rotate: -360 }}
                        transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
                        className="absolute top-[-30px] right-[-30px] w-[130px] h-[130px] rounded-full border border-[#00B67A]/20"
                    />
                    <motion.div
                        animate={{ rotate: 360 }}
                        transition={{ duration: 50, repeat: Infinity, ease: "linear" }}
                        className="absolute bottom-[-80px] left-[-50px] w-[220px] h-[220px] rounded-full border border-dashed border-white/10"
                    />


                    {/* Main hero text */}
                    <div className="relative z-10 px-6 pt-5 pb-5">
                        {/* Logo */}
                        <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.5 }}
                            className="flex items-center gap-2.5 mb-6"
                        >
                            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#FBB12F] to-[#F5C563] flex items-center justify-center shadow-lg shadow-[#FBB12F]/30">
                                <span className="font-black text-[#2F3758] text-sm font-mono">AX</span>
                            </div>
                            <div>
                                <p className="text-white font-extrabold text-sm tracking-widest">ASSURED XPRESS</p>
                                <p className="text-[#FBB12F] text-[8px] tracking-[3px] font-bold uppercase">Merchant Portal</p>
                            </div>
                        </motion.div>

                        <AnimatePresence mode="wait">
                            <motion.div
                                key={currentSlide}
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                transition={{ duration: 0.4 }}
                            >
                                <h1 className="text-white text-2xl font-extrabold leading-snug mb-1">
                                    {slides[currentSlide].title}
                                </h1>
                                <h2 className="text-transparent bg-clip-text bg-gradient-to-r from-[#FBB12F] to-[#ffd074] text-2xl font-extrabold leading-snug mb-5">
                                    {slides[currentSlide].subtitle}
                                </h2>

                                {/* Stats row */}
                                <div className="flex gap-5">
                                    {slides[currentSlide].stats.map((stat, i) => (
                                        <div key={i} className="flex flex-col">
                                            <span className="text-lg font-black font-mono" style={{ color: stat.color }}>{stat.value}</span>
                                            <span className="text-white/50 text-[9px] font-semibold uppercase tracking-wider">{stat.label}</span>
                                        </div>
                                    ))}
                                </div>
                            </motion.div>
                        </AnimatePresence>

                        {/* Slide dots */}
                        <div className="flex gap-1.5 mt-5">
                            {slides.map((_, i) => (
                                <button key={i} onClick={() => setCurrentSlide(i)} className={`h-1 rounded-full transition-all duration-300 ${currentSlide === i ? "w-6 bg-[#FBB12F]" : "w-1.5 bg-white/30"}`} />
                            ))}
                        </div>
                    </div>



                    {/* Wave / curved bottom edge */}
                    <div className="absolute bottom-0 left-0 right-0 h-8 bg-white" style={{ borderRadius: '40px 40px 0 0' }} />
                </div>

                {/* ══════════════════════════════════════════
                    FORM SECTION
                ══════════════════════════════════════════ */}
                <div className="flex-1 flex flex-col justify-start lg:justify-center items-center px-6 pt-4 pb-8 lg:p-8 bg-white relative">

                    {/* Desktop-only subtle background */}
                    <div className="absolute inset-0 z-0 pointer-events-none hidden lg:block">
                        <div className="absolute top-[-10%] right-[-20%] w-[300px] h-[300px] bg-[#FBB12F]/5 blur-[80px] rounded-full" />
                        <div className="absolute bottom-[-10%] left-[-10%] w-[400px] h-[400px] bg-[#00B67A]/5 blur-[80px] rounded-full" />
                    </div>

                    <div className="w-full max-w-[420px] space-y-7 relative z-10">

                        {/* Heading */}
                        <div className="space-y-1">
                            <h2 className="text-2xl lg:text-3xl font-bold text-[#2F3758]">Welcome back 👋</h2>
                            <p className="text-slate-500 text-sm">Sign in to manage your deliveries.</p>
                        </div>

                        {/* Error */}
                        {error && (
                            <motion.div
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="p-3.5 bg-red-50 border border-red-100 rounded-xl flex items-center gap-3 text-red-600 text-sm"
                            >
                                <div className="w-1.5 h-1.5 rounded-full bg-red-500 flex-shrink-0" />
                                {error}
                            </motion.div>
                        )}

                        {/* Fields */}
                        <div className="space-y-4">
                            {/* Phone */}
                            <div className="space-y-1.5">
                                <label className="text-sm font-semibold text-[#2F3758]">Phone Number</label>
                                <div className="group relative">
                                    <div className="absolute left-3 top-1/2 -translate-y-1/2 w-8 h-8 rounded-lg bg-slate-50 flex items-center justify-center text-slate-400 group-focus-within:text-[#FBB12F] group-focus-within:bg-[#FBB12F]/10 transition-colors z-10">
                                        <Phone size={17} />
                                    </div>
                                    <div className="absolute left-12 top-1/2 -translate-y-1/2 text-slate-500 font-medium text-sm border-r border-slate-200 pr-3 h-5 flex items-center z-10">
                                        +234
                                    </div>
                                    <input
                                        type="tel"
                                        value={phone}
                                        onChange={(e) => setPhone(e.target.value)}
                                        onKeyPress={handleKeyPress}
                                        placeholder="8099999999"
                                        className="w-full pl-24 pr-4 py-3.5 bg-slate-50/80 border border-slate-200 rounded-xl text-[#2F3758] placeholder:text-slate-400 focus:outline-none focus:border-[#FBB12F] focus:ring-4 focus:ring-[#FBB12F]/10 transition-all font-medium"
                                    />
                                </div>
                            </div>

                            {/* Password */}
                            <div className="space-y-1.5">
                                <div className="flex items-center justify-between">
                                    <label className="text-sm font-semibold text-[#2F3758]">Password</label>
                                    <Link href="/forgot-password" className="text-sm font-medium text-[#FBB12F] hover:text-[#e0981e] transition-colors">
                                        Forgot password?
                                    </Link>
                                </div>
                                <div className="group relative">
                                    <div className="absolute left-3 top-1/2 -translate-y-1/2 w-8 h-8 rounded-lg bg-slate-50 flex items-center justify-center text-slate-400 group-focus-within:text-[#FBB12F] group-focus-within:bg-[#FBB12F]/10 transition-colors">
                                        <Lock size={17} />
                                    </div>
                                    <input
                                        type={showPass ? "text" : "password"}
                                        value={pass}
                                        onChange={(e) => setPass(e.target.value)}
                                        onKeyPress={handleKeyPress}
                                        placeholder="Enter your password"
                                        className="w-full pl-13 pr-12 py-3.5 bg-slate-50/80 border border-slate-200 rounded-xl text-[#2F3758] placeholder:text-slate-400 focus:outline-none focus:border-[#FBB12F] focus:ring-4 focus:ring-[#FBB12F]/10 transition-all font-medium"
                                    />
                                    <button type="button" onClick={() => setShowPass(!showPass)} className="absolute right-4 top-1/2 -translate-y-1/2 text-slate-400 hover:text-[#2F3758] transition-colors">
                                        {showPass ? <EyeOff size={17} /> : <Eye size={17} />}
                                    </button>
                                </div>
                            </div>
                        </div>

                        {/* Submit */}
                        <button
                            onClick={handleLogin}
                            disabled={loading}
                            className="w-full relative overflow-hidden group bg-[#2F3758] text-white font-bold py-4 rounded-xl flex items-center justify-center gap-2 hover:bg-[#232a45] transition-all shadow-lg shadow-[#2F3758]/20 disabled:opacity-70 disabled:cursor-not-allowed"
                        >
                            <span className="relative z-10 flex items-center gap-2">
                                {loading ? (
                                    <><Loader2 size={20} className="animate-spin" />Signing in...</>
                                ) : (
                                    <>Sign In to Dashboard<ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" /></>
                                )}
                            </span>
                            <div className="absolute inset-0 bg-gradient-to-r from-[#FBB12F] to-[#F5C563] opacity-0 group-hover:opacity-10 transition-opacity" />
                            <div className="absolute bottom-0 left-0 h-1 w-full bg-[#FBB12F]" />
                        </button>

                        {/* Divider with trust signals - mobile only */}
                        <div className="lg:hidden flex items-center gap-3">
                            <div className="flex-1 h-px bg-slate-100" />
                            <span className="text-[10px] text-slate-400 font-medium tracking-wider uppercase">Secure Login</span>
                            <div className="flex-1 h-px bg-slate-100" />
                        </div>

                        {/* Trust badges - mobile only */}
                        <div className="lg:hidden flex justify-center gap-6">
                            {[
                                { icon: Shield, label: "SSL Secured" },
                                { icon: Zap, label: "Instant Access" },
                                { icon: Package, label: "2k+ Merchants" },
                            ].map(({ icon: Icon, label }, i) => (
                                <div key={i} className="flex flex-col items-center gap-1">
                                    <div className="w-8 h-8 rounded-lg bg-[#2F3758]/5 flex items-center justify-center">
                                        <Icon size={14} className="text-[#2F3758]/60" />
                                    </div>
                                    <span className="text-[9px] text-slate-400 font-medium text-center">{label}</span>
                                </div>
                            ))}
                        </div>

                        {/* Sign up link */}
                        <div className="text-center pt-1">
                            <p className="text-slate-500 text-sm">
                                Don't have an account?{' '}
                                <Link href="/signup" className="font-bold text-[#FBB12F] hover:text-[#e0981e] transition-colors">
                                    Create Merchant Account
                                </Link>
                            </p>
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="text-center py-4 text-slate-400 text-xs">
                    &copy; {new Date().getFullYear()} Assured Xpress. All rights reserved.
                </div>
            </div>
        </div>
    );
}