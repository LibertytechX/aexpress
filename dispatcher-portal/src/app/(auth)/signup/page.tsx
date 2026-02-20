/* eslint-disable @typescript-eslint/no-explicit-any */
'use client';

import React, { useState, useEffect } from 'react';
// import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
    User, Phone, Mail, Lock, Building, MapPin, ArrowRight, Loader2, Eye, EyeOff, Check, Package,

    // Zap,
    //  Shield, 
    ChevronLeft
} from 'lucide-react';
import Image from 'next/image';
import Logo from '@/components/ui/logo';
import { useDispatcher } from '@/contexts/DispatcherContext';
import { AuthService } from '@/services/authService';

const slides = [
    { title: "Command & Control,", subtitle: "For Lagos Logistics", description: "Manage your entire fleet from a single powerful dashboard. Assign orders, track riders, and ensure smooth operations.", stats: [{ label: "Active Riders", value: "500+", color: "#FBB12F" }, { label: "On-Time Rate", value: "98%", color: "#00B67A" }, { label: "Daily Orders", value: "10k+", color: "white" }] },
    { title: "Fleet Management,", subtitle: "In Real-Time", description: "Monitor every vehicle and package. Our advanced overview system ensures you always know where your assets are.", stats: [{ label: "Live Tracking", value: "100%", color: "#FBB12F" }, { label: "Fleet Size", value: "1k+", color: "#00B67A" }, { label: "Coverage", value: "Lagos", color: "white" }] },
    { title: "Empowering Dispatchers,", subtitle: "To Move Faster", description: "Tools designed for administrators. Resolve issues, view system analytics, and streamline your entire logistics network.", stats: [{ label: "Resolution", value: "<5m", color: "#FBB12F" }, { label: "Uptime", value: "99.9%", color: "#00B67A" }, { label: "Support", value: "24/7", color: "white" }] }
];

export default function SignupPage() {
    const router = useRouter();
    const { setAuthState } = useDispatcher();
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");
    const [currentSlide, setCurrentSlide] = useState(0);

    const [contactName, setContactName] = useState("");
    const [phone, setPhone] = useState("");
    const [email, setEmail] = useState("");
    const [pass, setPass] = useState("");
    const [confirmPass, setConfirmPass] = useState("");
    const [showPass, setShowPass] = useState(false);
    const [showConfirmPass, setShowConfirmPass] = useState(false);

    const [businessName, setBusinessName] = useState("");
    const [address, setAddress] = useState("");

    // const passwordsMatch = Boolean(pass && confirmPass && pass === confirmPass);
    const passwordsDontMatch = Boolean(confirmPass && pass !== confirmPass);

    useEffect(() => {
        const timer = setInterval(() => { setCurrentSlide((prev) => (prev + 1) % slides.length); }, 5000);
        return () => clearInterval(timer);
    }, []);

    const handleSignup = async () => {
        try {
            setLoading(true);
            setError("");

            await AuthService.signup({
                business_name: businessName,
                contact_name: contactName,
                phone: phone,
                email: email,
                password: pass,
                address: address
            } as any);

            setStep(3);
            setTimeout(() => {
                setAuthState("login");
                router.push('/login');
            }, 2000);

        } catch (err: any) {
            setError(err.message || "Signup failed. Please try again.");
            setStep(2);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen w-full flex bg-white font-sans overflow-hidden">
            {/* ─── LEFT PANEL (desktop only) ─── */}
            <div className="hidden lg:flex w-[50%] 2xl:w-[55%] relative overflow-hidden bg-[#2F3758] flex-col justify-between py-12 px-16 z-0" style={{ borderRight: '1px solid rgba(255,255,255,0.05)' }}>
                {/* Modern Geometric Background */}
                <div className="absolute inset-0 z-0 overflow-hidden">
                    {/* Deep base with subtle grid */}
                    <div className="absolute inset-0 bg-[#2F3758]" />

                    {/* Architectural Grid */}
                    <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: 'linear-gradient(#ffffff 1px, transparent 1px), linear-gradient(90deg, #ffffff 1px, transparent 1px)', backgroundSize: '40px 40px' }} />

                    {/* Lighting & Gradients */}
                    <div className="absolute top-[-20%] left-[-10%] w-[70%] h-[70%] rounded-full opacity-[0.15] blur-[120px] mix-blend-screen pointer-events-none" style={{ background: 'radial-gradient(circle, #FBB12F 0%, transparent 70%)' }} />
                    <div className="absolute bottom-[-20%] right-[-20%] w-[80%] h-[80%] rounded-full opacity-[0.05] blur-[100px] mix-blend-screen pointer-events-none" style={{ background: 'radial-gradient(circle, #ffffff 0%, transparent 70%)' }} />

                    {/* Geometric Accents */}
                    <div className="absolute top-[15%] right-[10%] w-[400px] h-[400px] border border-white/5 rounded-full" />
                    <div className="absolute top-[20%] right-[15%] w-[300px] h-[300px] border border-[#FBB12F]/10 rounded-full" />

                    <motion.div animate={{ rotate: 180 }} transition={{ duration: 120, repeat: Infinity, ease: "linear" }} className="absolute bottom-[10%] right-[30%] opacity-20">
                        <svg width="200" height="200" viewBox="0 0 100 100"><polygon points="50,15 85,85 15,85" fill="none" stroke="#FBB12F" strokeWidth="0.5" strokeDasharray="2 4" /></svg>
                    </motion.div>
                </div>

                {/* Header / Logo */}
                <div className="relative z-10 flex items-center justify-between">
                    <motion.div initial={{ opacity: 0, x: -20 }} animate={{ opacity: 1, x: 0 }} transition={{ duration: 0.6 }}>
                        <Logo />
                    </motion.div>
                    <div className="flex items-center gap-3 bg-white/5 px-4 py-2 rounded-full border border-white/10 backdrop-blur-md">
                        <span className="relative flex h-2.5 w-2.5">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#FBB12F] opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-[#FBB12F]"></span>
                        </span>
                        <span className="text-white/90 text-xs font-semibold tracking-wider uppercase">Portal Active</span>
                    </div>
                </div>

                {/* Main Content Area */}
                <div className="relative z-10 flex-1 flex flex-col justify-center mt-8">
                    <AnimatePresence mode="wait">
                        <motion.div
                            key={currentSlide}
                            initial={{ opacity: 0, y: 30 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: -30 }}
                            transition={{ duration: 0.5, ease: "easeOut" }}
                            className="max-w-xl"
                        >
                            <div className="mb-6 inline-flex items-center gap-2 px-3 py-1 rounded-md border-l-2 border-[#FBB12F] bg-gradient-to-r from-[#FBB12F]/10 to-transparent">
                                <span className="text-[#FBB12F] tracking-widest text-[10px] font-black uppercase">AX Engine v2.0</span>
                            </div>

                            <h1 className="text-white text-5xl lg:text-[56px] font-bold leading-[1.1] tracking-tight mb-6 flex flex-col gap-2">
                                <span>{slides[currentSlide].title}</span>
                                <span className="text-transparent bg-clip-text" style={{ backgroundImage: 'linear-gradient(90deg, #FBB12F 0%, #FFE0B2 100%)' }}>
                                    {slides[currentSlide].subtitle}
                                </span>
                            </h1>

                            <p className="text-slate-300 text-lg leading-relaxed max-w-md h-[84px] font-medium opacity-90">
                                {slides[currentSlide].description}
                            </p>

                            <div className="grid grid-cols-3 gap-8 pt-8 mt-8 border-t border-white/10">
                                {slides[currentSlide].stats.map((stat, i) => (
                                    <div key={i} className="flex flex-col gap-1.5">
                                        <span className="text-3xl font-black font-mono tracking-tighter" style={{ color: stat.color }}>{stat.value}</span>
                                        <span className="text-slate-400 text-[10px] font-bold uppercase tracking-widest">{stat.label}</span>
                                    </div>
                                ))}
                            </div>
                        </motion.div>
                    </AnimatePresence>

                    {/* Navigation Dots */}
                    <div className="flex gap-4 mt-20 items-center">
                        <div className="text-white/40 font-mono text-sm font-medium mr-4">0{currentSlide + 1} / 0{slides.length}</div>
                        {slides.map((_, index) => (
                            <button
                                key={index}
                                onClick={() => setCurrentSlide(index)}
                                className={`transition-all duration-500 ease-out h-1 ${currentSlide === index ? "w-16 bg-[#FBB12F]" : "w-6 bg-white/20 hover:bg-white/40"}`}
                            />
                        ))}
                    </div>
                </div>

                {/* Sophisticated Image Integration */}
                <div className="absolute bottom-0 right-0 w-[65%] max-w-[600px] pointer-events-none z-0">
                    <motion.div
                        key={`img-${currentSlide}`}
                        initial={{ opacity: 0, x: 50 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 1, delay: 0.2, ease: "easeOut" }}
                        className="relative w-full h-full"
                    >
                        {/* Overlay gradient to blend image smoothly into the background */}
                        <div className="absolute inset-0 bg-gradient-to-t from-[#2F3758] via-transparent to-transparent z-10" />
                        <div className="absolute inset-0 bg-gradient-to-l from-transparent via-[#2F3758]/20 to-[#2F3758] z-10" />

                        <Image
                            src={currentSlide % 2 === 0 ? "/bike_img.png" : "/bus_img.png"}
                            alt="Logistics Vehicle"
                            width={800}
                            height={600}
                            className="object-contain w-full h-auto opacity-70 drop-shadow-[0_20px_50px_rgba(0,0,0,0.5)] translate-x-[15%] translate-y-[5%]"
                            priority
                            onError={(e) => {
                                (e.target as HTMLImageElement).src = '/bike_img.png';
                            }}
                        />
                    </motion.div>
                </div>
            </div>

            {/* ─── RIGHT PANEL / MOBILE FULL PAGE ─── */}
            <div className="flex-1 flex flex-col bg-white relative overflow-hidden">
                <div className="lg:hidden relative w-full overflow-hidden" style={{ minHeight: '280px' }}>
                    <div className="absolute inset-0 bg-[#1e2540]" />
                    <div className="absolute inset-0">
                        <motion.div animate={{ x: [0, 40, 0], y: [0, -20, 0] }} transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }} className="absolute top-[-30%] right-[-20%] w-[320px] h-[320px] rounded-full" style={{ background: 'radial-gradient(circle, rgba(251,177,47,0.25) 0%, transparent 70%)' }} />
                        <motion.div animate={{ x: [0, -30, 0], y: [0, 30, 0] }} transition={{ duration: 10, repeat: Infinity, ease: "easeInOut", delay: 2 }} className="absolute bottom-[-20%] left-[-10%] w-[280px] h-[280px] rounded-full" style={{ background: 'radial-gradient(circle, rgba(0,182,122,0.2) 0%, transparent 70%)' }} />
                    </div>
                    <div className="absolute inset-0 opacity-[0.12]" style={{ backgroundImage: 'radial-gradient(rgba(255,255,255,0.8) 1px, transparent 1px)', backgroundSize: '24px 24px' }} />
                    <motion.div animate={{ rotate: 360 }} transition={{ duration: 35, repeat: Infinity, ease: "linear" }} className="absolute top-[-60px] right-[-60px] w-[200px] h-[200px] rounded-full border border-dashed border-[#FBB12F]/25" />

                    <div className="relative z-10 px-6 pt-5 pb-5">
                        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="flex items-center gap-2.5 mb-6">
                            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#FBB12F] to-[#F5C563] flex items-center justify-center shadow-lg shadow-[#FBB12F]/30">
                                <span className="font-black text-[#2F3758] text-sm font-mono">AX</span>
                            </div>
                            <div>
                                <p className="text-white font-extrabold text-sm tracking-widest">ASSURED XPRESS</p>
                                <p className="text-[#FBB12F] text-[8px] tracking-[3px] font-bold uppercase">Dispatcher Portal</p>
                            </div>
                        </motion.div>

                        <AnimatePresence mode="wait">
                            <motion.div key={currentSlide} initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} transition={{ duration: 0.4 }}>
                                <h1 className="text-white text-2xl font-extrabold leading-snug mb-1">{slides[currentSlide].title}</h1>
                                <h2 className="text-transparent bg-clip-text bg-gradient-to-r from-[#FBB12F] to-[#ffd074] text-2xl font-extrabold leading-snug mb-5">{slides[currentSlide].subtitle}</h2>
                            </motion.div>
                        </AnimatePresence>
                        <div className="flex gap-1.5 mt-5">
                            {slides.map((_, i) => (<button key={i} onClick={() => setCurrentSlide(i)} className={`h-1 rounded-full transition-all duration-300 ${currentSlide === i ? "w-6 bg-[#FBB12F]" : "w-1.5 bg-white/30"}`} />))}
                        </div>
                    </div>
                    <div className="absolute bottom-0 left-0 right-0 h-8 bg-white" style={{ borderRadius: '40px 40px 0 0' }} />
                </div>

                <div className="flex-1 flex flex-col justify-start lg:justify-center items-center px-6 pt-4 pb-8 lg:p-8 bg-white relative">
                    <div className="absolute inset-0 z-0 pointer-events-none hidden lg:block">
                        <div className="absolute top-[-10%] right-[-20%] w-[300px] h-[300px] bg-[#FBB12F]/5 blur-[80px] rounded-full" />
                        <div className="absolute bottom-[-10%] left-[-10%] w-[400px] h-[400px] bg-[#00B67A]/5 blur-[80px] rounded-full" />
                    </div>

                    <div className="w-full max-w-[480px] space-y-7 relative z-10">
                        {step < 3 && (
                            <div className="flex flex-col gap-6">
                                <div><h2 className="text-2xl lg:text-3xl font-bold text-[#2F3758]">Create Account</h2><p className="text-slate-500 text-sm mt-1">Join thousands of dispatchers growing with us.</p></div>
                                <div className="flex items-center gap-2">
                                    {[1, 2, 3].map((s) => {
                                        const isActive = step >= s;
                                        const isCompleted = step > s;
                                        return (
                                            <React.Fragment key={s}>
                                                <div className={`flex items-center gap-2 ${isActive ? 'text-[#2F3758]' : 'text-slate-300'}`}>
                                                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all duration-300 ${isActive ? 'bg-[#FBB12F] text-[#2F3758] shadow-lg shadow-[#FBB12F]/20' : 'bg-slate-100'}`}>
                                                        {isCompleted ? <Check size={14} strokeWidth={3} /> : s}
                                                    </div>
                                                    <span className={`text-xs font-bold uppercase tracking-wider hidden sm:block ${isActive ? 'text-[#2F3758]' : 'text-slate-300'}`}>{s === 1 ? "Account" : s === 2 ? "Business" : "Verify"}</span>
                                                </div>
                                                {s < 3 && <div className={`flex-1 h-0.5 rounded-full transition-all duration-300 ${isCompleted ? 'bg-[#FBB12F]' : 'bg-slate-100'}`} />}
                                            </React.Fragment>
                                        );
                                    })}
                                </div>
                            </div>
                        )}

                        {error && (
                            <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} className="p-3.5 bg-red-50 border border-red-100 rounded-xl flex items-center gap-3 text-red-600 text-sm">
                                <div className="w-1.5 h-1.5 rounded-full bg-red-500 flex-shrink-0" />
                                {error}
                            </motion.div>
                        )}

                        <AnimatePresence mode="wait">
                            {step === 1 && (
                                <motion.div key="step1" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-4">
                                    <div className="space-y-1.5">
                                        <label className="text-sm font-semibold text-[#2F3758]">Full Name</label>
                                        <div className="relative group">
                                            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-[#FBB12F] transition-colors"><User size={18} /></div>
                                            <input value={contactName} onChange={e => setContactName(e.target.value)} placeholder="e.g. John Doe" className="w-full pl-10 pr-4 py-3.5 bg-slate-50 border border-slate-200 rounded-xl text-[#2F3758] placeholder:text-slate-400 focus:outline-none focus:border-[#FBB12F] focus:ring-4 focus:ring-[#FBB12F]/10 transition-all font-medium" />
                                        </div>
                                    </div>

                                    <div className="space-y-1.5">
                                        <label className="text-sm font-semibold text-[#2F3758]">Phone Number</label>
                                        <div className="relative group">
                                            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-[#FBB12F] transition-colors z-10"><Phone size={18} /></div>
                                            <div className="absolute left-10 top-1/2 -translate-y-1/2 text-slate-500 font-medium text-sm border-r border-slate-200 pr-3 h-5 flex items-center z-10">+234</div>
                                            <input type="tel" value={phone} onChange={e => setPhone(e.target.value)} placeholder="8099999999" className="w-full pl-24 pr-4 py-3.5 bg-slate-50 border border-slate-200 rounded-xl text-[#2F3758] placeholder:text-slate-400 focus:outline-none focus:border-[#FBB12F] focus:ring-4 focus:ring-[#FBB12F]/10 transition-all font-medium" />
                                        </div>
                                    </div>

                                    <div className="space-y-1.5">
                                        <label className="text-sm font-semibold text-[#2F3758]">Email Address</label>
                                        <div className="relative group">
                                            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-[#FBB12F] transition-colors"><Mail size={18} /></div>
                                            <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@dispatch.com" className="w-full pl-10 pr-4 py-3.5 bg-slate-50 border border-slate-200 rounded-xl text-[#2F3758] placeholder:text-slate-400 focus:outline-none focus:border-[#FBB12F] focus:ring-4 focus:ring-[#FBB12F]/10 transition-all font-medium" />
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                        <div className="space-y-1.5">
                                            <label className="text-sm font-semibold text-[#2F3758]">Password</label>
                                            <div className="relative group">
                                                <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-[#FBB12F] transition-colors"><Lock size={18} /></div>
                                                <input type={showPass ? "text" : "password"} value={pass} onChange={e => setPass(e.target.value)} placeholder="Min. 8 chars" className="w-full pl-10 pr-10 py-3.5 bg-slate-50 border border-slate-200 rounded-xl text-[#2F3758] placeholder:text-slate-400 focus:outline-none focus:border-[#FBB12F] focus:ring-4 focus:ring-[#FBB12F]/10 transition-all font-medium" />
                                                <button type="button" onClick={() => setShowPass(!showPass)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-[#2F3758]"><div className="p-1">{showPass ? <EyeOff size={16} /> : <Eye size={16} />}</div></button>
                                            </div>
                                        </div>
                                        <div className="space-y-1.5">
                                            <label className="text-sm font-semibold text-[#2F3758]">Confirm</label>
                                            <div className="relative group">
                                                <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-[#FBB12F] transition-colors"><Lock size={18} /></div>
                                                <input type={showConfirmPass ? "text" : "password"} value={confirmPass} onChange={e => setConfirmPass(e.target.value)} placeholder="Repeat password" className={`w-full pl-10 pr-10 py-3.5 bg-slate-50 border rounded-xl text-[#2F3758] placeholder:text-slate-400 focus:outline-none focus:ring-4 transition-all font-medium ${passwordsDontMatch ? 'border-red-300 focus:border-red-500 focus:ring-red-100' : 'border-slate-200 focus:border-[#FBB12F] focus:ring-[#FBB12F]/10'}`} />
                                                <button type="button" onClick={() => setShowConfirmPass(!showConfirmPass)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-[#2F3758]"><div className="p-1">{showConfirmPass ? <EyeOff size={16} /> : <Eye size={16} />}</div></button>
                                            </div>
                                        </div>
                                    </div>

                                    <button onClick={() => setStep(2)} disabled={!contactName || !phone || !email || !pass || !confirmPass || passwordsDontMatch} className="w-full mt-4 relative overflow-hidden group bg-[#2F3758] text-white font-bold py-4 rounded-xl flex items-center justify-center gap-2 hover:bg-[#232a45] transition-all shadow-lg shadow-[#2F3758]/20 disabled:opacity-70 disabled:cursor-not-allowed">
                                        <span className="relative z-10 flex items-center gap-2">Continue <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" /></span>
                                        <div className="absolute inset-0 bg-gradient-to-r from-[#FBB12F] to-[#F5C563] opacity-0 group-hover:opacity-10 transition-opacity" />
                                    </button>
                                </motion.div>
                            )}

                            {step === 2 && (
                                <motion.div key="step2" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="space-y-4">
                                    <div className="space-y-1.5">
                                        <label className="text-sm font-semibold text-[#2F3758]">Business Name</label>
                                        <div className="relative group">
                                            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-[#FBB12F] transition-colors"><Building size={18} /></div>
                                            <input value={businessName} onChange={e => setBusinessName(e.target.value)} placeholder="e.g. Vivid Prints" className="w-full pl-10 pr-4 py-3.5 bg-slate-50 border border-slate-200 rounded-xl text-[#2F3758] placeholder:text-slate-400 focus:outline-none focus:border-[#FBB12F] focus:ring-4 focus:ring-[#FBB12F]/10 transition-all font-medium" />
                                        </div>
                                    </div>

                                    <div className="space-y-1.5">
                                        <label className="text-sm font-semibold text-[#2F3758]">Business Address</label>
                                        <div className="relative group">
                                            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-[#FBB12F] transition-colors"><MapPin size={18} /></div>
                                            <input value={address} onChange={e => setAddress(e.target.value)} placeholder="e.g. 19 Allen Ave, Ikeja" className="w-full pl-10 pr-4 py-3.5 bg-slate-50 border border-slate-200 rounded-xl text-[#2F3758] placeholder:text-slate-400 focus:outline-none focus:border-[#FBB12F] focus:ring-4 focus:ring-[#FBB12F]/10 transition-all font-medium" />
                                        </div>
                                    </div>

                                    <div className="flex gap-3 mt-6">
                                        <button onClick={() => setStep(1)} className="px-6 py-4 rounded-xl border border-slate-200 font-bold text-slate-600 hover:bg-slate-50 transition-colors flex items-center justify-center gap-2"><ChevronLeft size={18} /> Back</button>
                                        <button onClick={handleSignup} disabled={loading || !businessName || !address} className="flex-1 relative overflow-hidden group bg-[#2F3758] text-white font-bold py-4 rounded-xl flex items-center justify-center gap-2 hover:bg-[#232a45] transition-all shadow-lg shadow-[#2F3758]/20 disabled:opacity-70 disabled:cursor-not-allowed">
                                            <span className="relative z-10 flex items-center gap-2">
                                                {loading ? <><Loader2 size={18} className="animate-spin" /> Creating...</> : <>Create Account <Package size={18} /></>}
                                            </span>
                                            <div className="absolute inset-0 bg-gradient-to-r from-[#FBB12F] to-[#F5C563] opacity-0 group-hover:opacity-10 transition-opacity" />
                                        </button>
                                    </div>
                                </motion.div>
                            )}

                            {step === 3 && (
                                <motion.div key="step3" initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="text-center py-8">
                                    <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6 text-green-600"><Check size={40} strokeWidth={3} /></div>
                                    <h2 className="text-2xl font-bold text-[#2F3758] mb-2">You&apos;re all set! 🎉</h2>
                                    <p className="text-slate-500 mb-8 max-w-xs mx-auto">Your dispatcher account has been created successfully. Redirecting you to login...</p>
                                    <button onClick={() => { setAuthState('login'); router.push('/login'); }} className="w-full bg-[#E8A838] text-[#2F3758] font-bold py-4 rounded-xl hover:bg-[#e0981e] transition-colors relative overflow-hidden">
                                        <span className="relative z-10">Proceed to Login</span>
                                    </button>
                                </motion.div>
                            )}
                        </AnimatePresence>

                        {step < 3 && (
                            <div className="text-center pt-2">
                                <p className="text-slate-500 text-sm">
                                    Already have an account?{' '}
                                    <span onClick={() => { setAuthState("login"); router.push('/login'); }} className="font-bold text-[#FBB12F] hover:text-[#e0981e] transition-colors cursor-pointer">
                                        Sign In
                                    </span>
                                </p>
                            </div>
                        )}
                    </div>

                    <div className="mt-8 text-center text-slate-400 text-xs">
                        &copy; {new Date().getFullYear()} Assured Xpress. All rights reserved.
                    </div>
                </div>
            </div>
        </div>
    );
}
