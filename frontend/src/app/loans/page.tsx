'use client';

import React from 'react';
import AppLayout from '@/components/layout/AppLayout';
import BusinessLoansScreen from '@/components/loans/BusinessLoansScreen';

export default function LoansPage() {
  return (
    <AppLayout>
       <BusinessLoansScreen />
    </AppLayout>
  )
}
