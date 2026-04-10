'use client';

import React, { useState, useEffect } from 'react';
import Icons from '@/components/Icons';
import { S } from '@/lib/theme';
import API from '@/lib/api';

// Loading Spinner Component moved outside to avoid "Cannot create components during render"
const LoadingSpinner = ({ state }: { state: string }) => (
  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", padding: "60px 40px" }}>
    <div style={{
      width: 60,
      height: 60,
      border: `4px solid ${S.goldPale}`,
      borderTop: `4px solid ${S.gold}`,
      borderRadius: "50%",
      animation: "spin 1s linear infinite"
    }} />
    <style jsx>{`
      @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    `}</style>
    <p style={{ marginTop: 24, fontSize: 15, fontWeight: 600, color: S.navy }}>
      {state === 'loading' ? 'Generating account details...' : 'Processing confirmation...'}
    </p>
    <p style={{ marginTop: 8, fontSize: 13, color: S.grayLight }}>Please wait</p>
  </div>
);

export default function BankTransferModal({ amount, onClose, onSuccess }: { amount: number, onClose: () => void, onSuccess: () => void }) {
  const [state, setState] = useState('loading'); // 'loading', 'show-details', 'confirming', 'success', 'error'
  const [copied, setCopied] = useState(false);
  const [bankDetails, setBankDetails] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Initial loading - fetch virtual account
  useEffect(() => {
    const fetchVirtualAccount = async () => {
      try {
        setState('loading');
        const response = await API.Wallet.getVirtualAccount();
        if (response.success) {
          setBankDetails({
            bankName: response.data.bank_name,
            accountNumber: response.data.account_number,
            accountName: response.data.account_name
          });
          setState('show-details');
        } else {
          setError(response.message || "Failed to load bank details");
          setState('error');
        }
      } catch (err: any) {
        console.error("Error fetching virtual account:", err);
        setError("Network error. Please try again.");
        setState('error');
      }
    };

    fetchVirtualAccount();
  }, []);

  const copyAccountNumber = () => {
    if (!bankDetails) return;
    navigator.clipboard.writeText(bankDetails.accountNumber);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleConfirmPayment = () => {
    setState('confirming');
    setTimeout(() => {
      setState('success');
    }, 2500);
  };

  const handleClose = () => {
    if (state === 'success' && onSuccess) {
      onSuccess();
    }
    onClose();
  };

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 100, display: "flex", alignItems: "center", justifyContent: "center", fontFamily: "'DM Sans', sans-serif" }}>
      <div onClick={handleClose} style={{ position: "absolute", inset: 0, background: "rgba(0,0,0,0.5)" }} />
      <div style={{ position: "relative", background: "#fff", borderRadius: 18, width: 440, maxHeight: "90vh", overflow: "auto", boxShadow: "0 20px 60px rgba(0,0,0,0.2)", animation: "fadeIn 0.3s ease" }}>

        {/* Header */}
        <div style={{ padding: "20px 24px", borderBottom: "1px solid #f1f5f9", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <h3 style={{ fontSize: 18, fontWeight: 700, color: S.navy, margin: 0 }}>
            {state === 'success' ? 'Payment Confirmed' : 'Bank Transfer'}
          </h3>
          <button onClick={handleClose} style={{ background: "none", border: "none", cursor: "pointer", color: S.gray, padding: 4 }}>
            {Icons.close || '×'}
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: 24 }}>
          {/* Loading State */}
          {(state === 'loading' || state === 'confirming') && <LoadingSpinner state={state} />}

          {/* Show Bank Details */}
          {state === 'show-details' && (
            <div>
              {/* Amount to Transfer */}
              <div style={{ background: S.goldPale, borderRadius: 12, padding: 20, marginBottom: 20, textAlign: "center" }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: S.grayLight, marginBottom: 6 }}>Amount to Transfer</div>
                <div style={{ fontSize: 32, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono', monospace" }}>
                  ₦{(amount || 0).toLocaleString()}
                </div>
              </div>

              {/* Bank Details */}
              <div style={{ background: "#f8fafc", borderRadius: 12, padding: 20, marginBottom: 20 }}>
                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: S.grayLight, marginBottom: 4 }}>Bank Name</div>
                  <div style={{ fontSize: 16, fontWeight: 700, color: S.navy }}>{bankDetails.bankName}</div>
                </div>

                <div style={{ marginBottom: 16 }}>
                  <div style={{ fontSize: 12, fontWeight: 600, color: S.grayLight, marginBottom: 4 }}>Account Number</div>
                  <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                    <div style={{ fontSize: 20, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono', monospace", flex: 1 }}>
                      {bankDetails.accountNumber}
                    </div>
                    <button onClick={copyAccountNumber} style={{
                      padding: "6px 12px",
                      borderRadius: 8,
                      border: "none",
                      background: copied ? S.greenBg : S.goldPale,
                      color: copied ? S.green : S.gold,
                      fontSize: 12,
                      fontWeight: 700,
                      cursor: "pointer",
                      fontFamily: "inherit",
                      transition: "all 0.2s"
                    }}>
                      {copied ? '✓ Copied' : 'Copy'}
                    </button>
                  </div>
                </div>

                <div>
                  <div style={{ fontSize: 12, fontWeight: 600, color: S.grayLight, marginBottom: 4 }}>Account Name</div>
                  <div style={{ fontSize: 16, fontWeight: 700, color: S.navy }}>{bankDetails.accountName}</div>
                </div>
              </div>

              {/* Instructions */}
              <div style={{ background: "#fffbeb", border: "1px solid #fef3c7", borderRadius: 10, padding: 16, marginBottom: 20 }}>
                <div style={{ fontSize: 13, fontWeight: 600, color: "#92400e", marginBottom: 8 }}>⚠️ Important Instructions</div>
                <ul style={{ margin: 0, paddingLeft: 20, fontSize: 12, color: "#78350f", lineHeight: 1.6 }}>
                  <li>Transfer exactly <strong>₦{(amount || 0).toLocaleString()}</strong> to the account above</li>
                  <li>Your wallet will be credited within 5-10 minutes after payment</li>
                  <li>Click "I have paid" only after completing the transfer</li>
                </ul>
              </div>

              {/* Confirm Button */}
              <button onClick={handleConfirmPayment} style={{
                width: "100%",
                height: 48,
                border: "none",
                borderRadius: 10,
                fontSize: 15,
                fontWeight: 700,
                cursor: "pointer",
                background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`,
                color: S.navy,
                fontFamily: "inherit",
                boxShadow: "0 4px 12px rgba(232,168,56,0.3)"
              }}>
                I have paid
              </button>
            </div>
          )}

          {/* Error State */}
          {state === 'error' && (
            <div style={{ textAlign: "center", padding: "40px 20px" }}>
              <p style={{ color: S.red, fontWeight: 600, marginBottom: 16 }}>{error}</p>
              <button onClick={onClose} style={{
                padding: "10px 24px",
                borderRadius: 10,
                border: "none",
                background: S.navy,
                color: "#fff",
                fontWeight: 700,
                cursor: "pointer"
              }}>
                Close
              </button>
            </div>
          )}

          {/* Success State */}
          {state === 'success' && (
            <div style={{ textAlign: "center", padding: "40px 20px" }}>
              {/* Success Icon */}
              <div style={{
                width: 80,
                height: 80,
                borderRadius: "50%",
                background: S.greenBg,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                margin: "0 auto 24px",
                animation: "scaleIn 0.5s ease"
              }}>
                <div style={{ fontSize: 40, color: S.green }}>✓</div>
              </div>

              {/* Success Message */}
              <h3 style={{ fontSize: 20, fontWeight: 800, color: S.navy, margin: "0 0 12px" }}>
                Payment Confirmation Received!
              </h3>
              <p style={{ fontSize: 14, color: S.gray, lineHeight: 1.6, margin: "0 0 24px" }}>
                Your wallet will be credited once payment is verified. This usually takes 5-10 minutes.
              </p>

              {/* Transaction Details */}
              <div style={{ background: "#f8fafc", borderRadius: 10, padding: 16, marginBottom: 24, textAlign: "left" }}>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                  <span style={{ fontSize: 13, color: S.grayLight }}>Amount</span>
                  <span style={{ fontSize: 13, fontWeight: 700, color: S.navy }}>₦{(amount || 0).toLocaleString()}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 8 }}>
                  <span style={{ fontSize: 13, color: S.grayLight }}>Bank</span>
                  <span style={{ fontSize: 13, fontWeight: 700, color: S.navy }}>{bankDetails.bankName}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span style={{ fontSize: 13, color: S.grayLight }}>Status</span>
                  <span style={{ fontSize: 12, fontWeight: 700, padding: "2px 8px", borderRadius: 6, background: "#fef3c7", color: "#92400e" }}>
                    Pending Verification
                  </span>
                </div>
              </div>

              {/* Done Button */}
              <button onClick={handleClose} style={{
                width: "100%",
                height: 48,
                border: "none",
                borderRadius: 10,
                fontSize: 15,
                fontWeight: 700,
                cursor: "pointer",
                background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`,
                color: S.navy,
                fontFamily: "inherit",
                boxShadow: "0 4px 12px rgba(232,168,56,0.3)"
              }}>
                Done
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
