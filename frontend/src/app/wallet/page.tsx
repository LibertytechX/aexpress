'use client';

import React, { useState, useEffect } from 'react';
import AppLayout from '@/components/layout/AppLayout';
import WalletScreen from '@/components/wallet/WalletScreen';
import API from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { transformTransactions, UITransaction } from '@/lib/utils';
// import { toast } from 'react-hot-toast'; 

export default function WalletPage() {
    const { user } = useAuth();
    const [balance, setBalance] = useState(0);
    const [transactions, setTransactions] = useState<UITransaction[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (user) {
            loadData();
        }
    }, [user]);

    const loadData = async () => {
        try {
            setLoading(true);
            const balRes = await API.Wallet.getBalance();
            if (balRes.success) {
                setBalance(parseFloat(balRes.data?.balance || '0'));
            }

            const txnRes = await API.Wallet.getTransactions();
            if (txnRes.success || txnRes.results) {
                const data = txnRes.results?.data || txnRes.data || [];
                setTransactions(transformTransactions(data));
            }
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    }

    const handleFund = async (amount: number) => {
        try {
            const keyRes = await API.Wallet.getPaystackKey();
            if (!keyRes.success) throw new Error("Could not get payment key");

            const initRes = await API.Wallet.initializePayment(amount);
            if (!initRes.success) throw new Error("Could not initialize payment");

            const reference = initRes.data.reference;

            // Load Paystack script dynamically if not present
            if (!(window as any).PaystackPop) {
                const script = document.createElement('script');
                script.src = 'https://js.paystack.co/v1/inline.js';
                script.async = true;
                document.body.appendChild(script);
                await new Promise(resolve => script.onload = resolve);
            }

            const handler = (window as any).PaystackPop.setup({
                key: keyRes.data.public_key,
                email: user?.email,
                amount: amount * 100,
                currency: 'NGN',
                ref: reference,
                onClose: () => alert('Payment cancelled'),
                callback: async function (response: any) {
                    const verifyRes = await API.Wallet.verifyPayment(reference);
                    if (verifyRes.success) {
                        alert(`₦${amount.toLocaleString()} added successfully!`);
                        loadData();
                    } else {
                        alert('Payment verification failed');
                    }
                }
            });
            handler.openIframe();

        } catch (e: any) {
            console.error(e);
            alert(e.message || "Payment failed");
        }
    };

    const handleBankTransfer = (amount: number) => {
        // Logic for manual bank transfer notification if needed
        // Current modal handles 'success' state locally for user feedback
        // We might want to refresh data just in case
        // or simply wait for manual verification backend side
        loadData();
    };


    return (
        <AppLayout>
            <WalletScreen
                balance={balance}
                transactions={transactions}
                onFund={handleFund}
                onBankTransfer={handleBankTransfer}
            />
        </AppLayout>
    )
}
