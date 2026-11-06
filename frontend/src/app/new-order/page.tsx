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
      if (orderData.mode === 'quick' || orderData.mode === 'grouped') {
        const apiPayload = {
          pickup_address: orderData.pickup,
          sender_name: orderData.senderName || user?.contact_name || '',
          sender_phone: orderData.senderPhone || user?.phone || '',
          dropoff_address: orderData.dropoff,
          receiver_name: orderData.receiverName || '',
          receiver_phone: orderData.receiverPhone || '',
          vehicle: orderData.vehicle,
          payment_method: orderData.payMethod,
          package_type: orderData.packageType || 'Box',
          notes: orderData.notes || '',
          distance_km: orderData.distance_km || 0,
          duration_minutes: orderData.duration_minutes || 0,
          mode: orderData.mode,
          is_pickup_percel: orderData.is_pickup_percel || false,
          isdelivery_percel: orderData.isdelivery_percel || false,
          collect_code: orderData.collect_code,
          box_id: orderData.box_id,
          locker_size_id: orderData.locker_size_id
        };
        response = await API.Orders.createQuickSend(apiPayload);
      } else if (orderData.mode === 'multi') {
        response = await API.Orders.createMultiDrop({
          pickup_address: orderData.pickup,
          sender_name: orderData.senderName || user?.contact_name || '',
          sender_phone: orderData.senderPhone || user?.phone || '',
          vehicle: orderData.vehicle,
          payment_method: orderData.payMethod,
          deliveries: orderData.deliveries || [],
          notes: orderData.notes || '',
          distance_km: orderData.distance_km || 0,
          duration_minutes: orderData.duration_minutes || 0
        });
      } else if (orderData.mode === 'bulk') {
        response = await API.Orders.createBulkImport({
          pickup_address: orderData.pickup,
          sender_name: orderData.senderName || user?.contact_name || '',
          sender_phone: orderData.senderPhone || user?.phone || '',
          vehicle: orderData.vehicle,
          payment_method: orderData.payMethod,
          deliveries: orderData.deliveries || [],
          notes: orderData.notes || '',
          distance_km: orderData.distance_km || 0,
          duration_minutes: orderData.duration_minutes || 0
        });
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
