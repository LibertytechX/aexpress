'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Icons from '@/components/Icons';
import { S } from '@/lib/theme';
import API, { TokenManager } from '@/lib/api';

function VerifyEmailContent() {
    const router = useRouter();
    const searchParams = useSearchParams();
    const token = searchParams.get('token');

    const [status, setStatus] = useState("verifying"); // verifying, success, error
    const [message, setMessage] = useState("");

    useEffect(() => {
        if (token) {
            verifyEmail(token);
        } else {
            setStatus("error");
            setMessage("No verification token found.");
        }
    }, [token]);

    const verifyEmail = async (tokenStr: string) => {
        try {
            // Direct fetch usage here as in original code, or could use API helper if endpoint exists
            const response = await fetch(`https://www.orders.axpress.net/api/auth/verify-email/?token=${tokenStr}`);
            const data = await response.json();

            if (data.success) {
                setStatus("success");
                setMessage(data.message || "Email verified successfully!");

                // Update user in localStorage via API helper if needed
                if (data.user) {
                    TokenManager.setUser(data.user);
                }

                // Redirect to dashboard after 3 seconds
                setTimeout(() => {
                    router.push('/dashboard');
                }, 3000);
            } else {
                setStatus("error");
                setMessage(data.error || "Verification failed. Please try again.");
            }
        } catch (error) {
            setStatus("error");
            setMessage("Network error. Please check your connection and try again.");
        }
    };

    return (
        <div style={{
            minHeight: "100vh",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            background: S.grayBg,
            padding: 24,
        }}>
            <div style={{
                background: "#fff",
                borderRadius: 18,
                padding: "48px 40px",
                maxWidth: 480,
                width: "100%",
                textAlign: "center",
                boxShadow: "0 4px 24px rgba(0,0,0,0.08)"
            }}>
                {status === "verifying" && (
                    <>
                        <div style={{
                            width: 48,
                            height: 48,
                            border: `4px solid ${S.goldPale}`,
                            borderTop: `4px solid ${S.gold}`,
                            borderRadius: "50%",
                            margin: "0 auto 24px",
                            animation: "spin 1s linear infinite"
                        }} />
                        <h2 style={{ fontSize: 22, fontWeight: 700, color: S.navy, margin: "0 0 12px" }}>
                            Verifying Your Email
                        </h2>
                        <p style={{ fontSize: 14, color: S.gray, margin: 0 }}>
                            Please wait while we verify your email address...
                        </p>
                    </>
                )}

                {status === "success" && (
                    <>
                        <div style={{ color: S.green, margin: "0 auto 24px" }}>
                            {Icons.checkCircle}
                        </div>
                        <h2 style={{ fontSize: 22, fontWeight: 700, color: S.navy, margin: "0 0 12px" }}>
                            Email Verified Successfully!
                        </h2>
                        <p style={{ fontSize: 14, color: S.gray, margin: "0 0 24px" }}>
                            {message}
                        </p>
                        <p style={{ fontSize: 13, color: S.grayLight, margin: 0 }}>
                            Redirecting to dashboard...
                        </p>
                    </>
                )}

                {status === "error" && (
                    <>
                        <div style={{ color: S.red, margin: "0 auto 24px" }}>
                            {Icons.xCircle}
                        </div>
                        <h2 style={{ fontSize: 22, fontWeight: 700, color: S.navy, margin: "0 0 12px" }}>
                            Verification Failed
                        </h2>
                        <p style={{ fontSize: 14, color: S.gray, margin: "0 0 32px" }}>
                            {message}
                        </p>
                        <button
                            onClick={() => router.push('/dashboard')}
                            style={{
                                padding: "12px 32px",
                                borderRadius: 10,
                                border: "none",
                                background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`,
                                color: S.navy,
                                fontWeight: 700,
                                fontSize: 14,
                                cursor: "pointer",
                                fontFamily: "inherit",
                                boxShadow: "0 4px 12px rgba(232,168,56,0.3)"
                            }}
                        >
                            Go to Dashboard
                        </button>
                    </>
                )}
            </div>
            <style>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
        </div>
    );
}

export default function VerifyEmailPage() {
    return (
        <Suspense fallback={<div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>Verifying...</div>}>
            <VerifyEmailContent />
        </Suspense>
    );
}
