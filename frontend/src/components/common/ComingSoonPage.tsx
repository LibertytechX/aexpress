'use client';

import React from 'react';
import AppLayout from '@/components/layout/AppLayout';
import { S } from '@/lib/theme';

export default function ComingSoonPage({ title, description }) {
  return (
    <AppLayout>
       <div style={{ 
           display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", 
           height: "calc(100vh - 140px)", textAlign: "center", color: S.navy 
       }}>
           <div style={{ fontSize: 64, marginBottom: 20 }}>🚧</div>
           <h1 style={{ fontSize: 24, fontWeight: 800, marginBottom: 12 }}>{title || "Coming Soon"}</h1>
           <p style={{ fontSize: 14, color: S.gray, maxWidth: 400, lineHeight: 1.6 }}>
               {description || "We are working hard to bring this feature to you. Stay tuned!"}
           </p>
       </div>
    </AppLayout>
  )
}
