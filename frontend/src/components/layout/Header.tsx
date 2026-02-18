'use client';

import React from 'react';
import Icons from '@/components/Icons';
import { S } from '@/lib/theme';
import { useAuth } from '@/contexts/AuthContext';

export default function Header({ title, onResendVerification }) {
  const { user } = useAuth();
  
  if (!user) return null;

  return (
    <div style={{ marginBottom: 40, display: "flex", justifyContent: "space-between", alignItems: "flex-end" }}>
      <div>
        <h1 style={{ fontSize: 28, fontWeight: 700, color: S.navy, margin: 0 }}>{title}</h1>
        <p style={{ color: S.gray, marginTop: 4 }}>
          Welcome back, {user.contact_name?.split(' ')[0]}
        </p>
        
        {/* Verification Warning */}
        {!user.email_verified && (
          <div style={{ 
            marginTop: 12, display: "flex", alignItems: "center", gap: 8, 
            background: "#fffbeb", border: "1px solid #fcd34d", padding: "8px 12px", borderRadius: 8, fontSize: 13, color: "#92400E" 
          }}>
            <span>⚠️ Your email is not verified.</span>
            <button 
              onClick={onResendVerification}
              style={{ textDecoration: "underline", fontWeight: 600, cursor: "pointer", border: "none", background: "none", color: "inherit", padding: 0, fontFamily: "inherit" }}
            >
              Resend Link
            </button>
          </div>
        )}
      </div>

      <div style={{ display: "flex", gap: 16 }}>
        <button style={{
          width: 44, height: 44, borderRadius: 12, background: "#fff", border: "1px solid #e2e8f0",
          display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", color: S.navy
        }}>
          {Icons.bell}
        </button>
        <div style={{
          height: 44, padding: "0 16px 0 6px", borderRadius: 12, background: "#fff", border: "1px solid #e2e8f0",
          display: "flex", alignItems: "center", gap: 10, cursor: "pointer"
        }}>
          <div style={{ width: 32, height: 32, borderRadius: 8, background: S.goldPale, display: "flex", alignItems: "center", justifyContent: "center", fontWeight: 700, color: S.gold, fontSize: 14 }}>
            {user.contact_name?.charAt(0) || 'U'}
          </div>
          <div style={{ fontSize: 14, fontWeight: 600, color: S.navy }}>{user.business_name || 'My Business'}</div>
          {Icons.arrowDown}
        </div>
      </div>
    </div>
  );
}
