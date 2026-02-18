'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import AppLayout from '@/components/layout/AppLayout';
import NewOrderScreen from '@/components/orders/NewOrderScreen';
import API from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';

export default function NewOrderPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [balance, setBalance] = useState(0);

  useEffect(() => {
    if (user) {
      loadBalance();
    }
  }, [user]);

  const loadBalance = async () => {
    try {
      const res = await API.Wallet.getBalance();
      if (res.success) {
        setBalance(parseFloat(res.data?.balance || '0'));
      }
    } catch (e) {
      console.error(e);
    }
  }

  const handlePlaceOrder = async (orderData: any) => {
    try {
      let response;
      if (orderData.mode === 'quick') {
        response = await API.Orders.createQuickSend(orderData);
      } else if (orderData.mode === 'multi') {
        response = await API.Orders.createMultiDrop(orderData);
      } else if (orderData.mode === 'bulk') {
        response = await API.Orders.createBulkImport(orderData);
      } else {
        throw new Error("Invalid order mode");
      }

      if (response && response.success) {
        alert("Order placed successfully!");
        router.push('/orders');
      } else {
        // Handle error properly
        const errorMsg = response?.message || response?.error || "Failed to place order";
        throw new Error(errorMsg);
      }
    } catch (e: any) {
      console.error(e);
      alert(e.message || "Failed to place order");
    }
  };

  return (
    <AppLayout>
      <NewOrderScreen
        balance={balance}
        currentUser={user}
        onPlaceOrder={handlePlaceOrder}
      />
    </AppLayout>
  )
}
