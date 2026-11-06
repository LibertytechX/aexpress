'use client';

import React, { useState } from 'react';
import { S } from '@/lib/theme';
import Icons from '@/components/Icons';
import DeliveryMapView from '@/components/common/DeliveryMapView';
import { STATUS_COLORS, formatDate, getVehicleIcon, UIOrder } from '@/lib/utils';
import { OrdersAPI } from '@/lib/api';

/* ─── Pay Now Modal ────────────────────────────────────────────────
   Shows virtual account details returned by the pay-now endpoint.
───────────────────────────────────────────────────────────────── */
interface PaymentInfo {
  account_number: string;
  account_name: string;
  bank_name: string;
  bank_code: string;
}

function PayNowModal({
  orderNumber,
  totalAmount,
  initial,
  onClose,
}: {
  orderNumber: string;
  totalAmount: number;
  initial: PaymentInfo | null;
  onClose: () => void;
}) {
  const [loading, setLoading] = useState(!initial);
  const [info, setInfo] = useState<PaymentInfo | null>(initial);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // If no pre-fetched info, call the endpoint immediately
  React.useEffect(() => {
    if (initial) return;
    (async () => {
      try {
        const res = await OrdersAPI.payNow(orderNumber);
        setInfo(res.payment_info);
      } catch (e: any) {
        setError(e.message || 'Failed to generate payment info. Please try again.');
      } finally {
        setLoading(false);
      }
    })();
  }, [orderNumber, initial]);

  const copyAccount = () => {
    if (!info) return;
    navigator.clipboard.writeText(info.account_number).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div
      style={{
        position: 'fixed', inset: 0, zIndex: 2000,
        background: 'rgba(15,23,42,0.6)', backdropFilter: 'blur(6px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24,
        animation: 'fadeIn 0.2s ease',
      }}
      onMouseDown={e => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div style={{
        background: '#fff', borderRadius: 24, width: '100%', maxWidth: 420,
        overflow: 'hidden', boxShadow: '0 32px 80px rgba(0,0,0,0.25)',
        animation: 'scaleUp 0.25s cubic-bezier(0.34,1.56,0.64,1)',
      }}>
        {/* Header */}
        <div style={{
          padding: '20px 24px',
          background: 'linear-gradient(135deg, #1B2A4A 0%, #0f1b33 100%)',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{
              width: 40, height: 40, borderRadius: 12,
              background: 'linear-gradient(135deg, #E8A838, #F5C563)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 20,
            }}>🏦</div>
            <div>
              <div style={{ fontSize: 15, fontWeight: 800, color: '#fff' }}>Bank Transfer</div>
              <div style={{ fontSize: 11, color: 'rgba(255,255,255,0.5)', marginTop: 1 }}>
                Order #{orderNumber}
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'rgba(255,255,255,0.1)', border: 'none', borderRadius: 8,
              width: 30, height: 30, cursor: 'pointer', color: 'rgba(255,255,255,0.7)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: '24px 24px 8px' }}>
          {loading && (
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '32px 0', gap: 14 }}>
              <div style={{
                width: 40, height: 40,
                border: '4px solid #E8A838', borderTopColor: 'transparent',
                borderRadius: '50%', animation: 'pnSpin 0.7s linear infinite',
              }} />
              <span style={{ fontSize: 13, color: '#94a3b8', fontWeight: 500 }}>Generating payment details…</span>
            </div>
          )}

          {error && !loading && (
            <div style={{
              background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 12,
              padding: '14px 16px', fontSize: 13, color: '#dc2626', fontWeight: 600,
              display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 16,
            }}>
              <span style={{ fontSize: 18 }}>⚠️</span>
              <span>{error}</span>
            </div>
          )}

          {info && !loading && (
            <>
              {/* Amount banner */}
              <div style={{
                background: 'linear-gradient(135deg, #fef3c7, #fde68a)',
                border: '1px solid #fbbf24',
                borderRadius: 14, padding: '16px 20px', marginBottom: 20,
                display: 'flex', alignItems: 'center', justifyContent: 'space-between',
              }}>
                <div>
                  <div style={{ fontSize: 11, fontWeight: 700, color: '#92400e', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 4 }}>
                    Total Amount Due
                  </div>
                  <div style={{ fontSize: 28, fontWeight: 800, color: '#1B2A4A', fontFamily: "'Space Mono', monospace" }}>
                    ₦{totalAmount.toLocaleString()}
                  </div>
                </div>
                <div style={{ fontSize: 32 }}>💰</div>
              </div>

              {/* Account details */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 20 }}>
                {/* Bank name */}
                <div style={{
                  background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 12,
                  padding: '12px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                }}>
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 2 }}>Bank</div>
                    <div style={{ fontSize: 15, fontWeight: 700, color: S.navy }}>{info.bank_name}</div>
                  </div>
                  <div style={{
                    width: 36, height: 36, borderRadius: 10,
                    background: '#e0e7ff', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 18,
                  }}>🏛️</div>
                </div>

                {/* Account number — copyable */}
                <div style={{
                  background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 12,
                  padding: '12px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between',
                }}>
                  <div>
                    <div style={{ fontSize: 10, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 2 }}>Account Number</div>
                    <div style={{ fontSize: 20, fontWeight: 800, color: S.navy, fontFamily: "'Space Mono', monospace", letterSpacing: 2 }}>
                      {info.account_number}
                    </div>
                  </div>
                  <button
                    onClick={copyAccount}
                    style={{
                      padding: '6px 12px', borderRadius: 8,
                      border: '1.5px solid ' + (copied ? '#10b981' : '#e2e8f0'),
                      background: copied ? '#d1fae5' : '#fff',
                      color: copied ? '#065f46' : S.navy,
                      fontSize: 12, fontWeight: 700, cursor: 'pointer',
                      transition: 'all 0.2s', fontFamily: 'inherit', flexShrink: 0,
                      display: 'flex', alignItems: 'center', gap: 5,
                    }}
                  >
                    {copied ? '✓ Copied' : '📋 Copy'}
                  </button>
                </div>

                {/* Account name */}
                <div style={{
                  background: '#f8fafc', border: '1px solid #e2e8f0', borderRadius: 12,
                  padding: '12px 16px',
                }}>
                  <div style={{ fontSize: 10, fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 2 }}>Account Name</div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: S.navy }}>{info.account_name}</div>
                </div>
              </div>

              {/* Instruction note */}
              <div style={{
                background: '#eff6ff', border: '1px solid #bfdbfe', borderRadius: 12,
                padding: '12px 16px', display: 'flex', gap: 10, marginBottom: 8,
              }}>
                <span style={{ fontSize: 16, flexShrink: 0 }}>ℹ️</span>
                <div style={{ fontSize: 12, color: '#1e40af', lineHeight: 1.55 }}>
                  Transfer exactly <strong>₦{totalAmount.toLocaleString()}</strong> to the account above.
                  Your order will be confirmed automatically once payment is verified.
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div style={{ padding: '12px 24px 24px' }}>
          <button
            onClick={onClose}
            style={{
              width: '100%', padding: '13px', borderRadius: 12, border: 'none',
              background: 'linear-gradient(135deg, #1B2A4A, #243554)',
              color: '#fff', fontSize: 14, fontWeight: 700, cursor: 'pointer',
              fontFamily: 'inherit',
            }}
          >
            Done
          </button>
        </div>
      </div>

      <style>{`
        @keyframes pnSpin { to { transform: rotate(360deg); } }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
        @keyframes scaleUp { from { opacity: 0; transform: scale(0.94) translateY(12px); } to { opacity: 1; transform: scale(1) translateY(0); } }
      `}</style>
    </div>
  );
}

/* ─── OrderDetailModal ────────────────────────────────────────────── */
export default function OrderDetailModal({
  order,
  onClose,
  onRate,
}: {
  order: UIOrder;
  onClose: () => void;
  onRate: () => void;
}) {
  const [payNowOpen, setPayNowOpen] = useState(false);

  if (!order) return null;
  const statusColor = STATUS_COLORS[order.status] || STATUS_COLORS.Pending;

  // Show Pay Now button when payment_info is null and order isn't done/canceled
  const showPayNow = order.payment_info === null &&
    !['Done', 'CustomerCanceled', 'DriverCanceled', 'SupportCanceled'].includes(order.status);

  const steps = [
    { label: 'Order Placed', time: order.date, done: true },
    { label: 'Rider Assigned', time: order.status !== 'Pending' ? 'Verified' : null, done: order.status !== 'Pending' },
    { label: 'Picked Up', time: (order.status === 'PickedUp' || order.status === 'Done') ? 'Verified' : null, done: order.status === 'PickedUp' || order.status === 'Done' },
    { label: 'Delivered', time: order.status === 'Done' ? 'Verified' : null, done: order.status === 'Done' },
  ];

  return (
    <>
      <div
        style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000 }}
        onClick={onClose}
      >
        <div
          onClick={e => e.stopPropagation()}
          style={{ background: '#fff', borderRadius: 20, width: 900, height: '85vh', display: 'flex', overflow: 'hidden', boxShadow: '0 24px 48px rgba(0,0,0,0.2)' }}
        >
          {/* ── Left Panel ── */}
          <div style={{ width: 400, padding: 32, overflowY: 'auto', borderRight: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column' }}>
            {/* Order header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 24 }}>
              <div style={{ width: 48, height: 48, borderRadius: 12, background: statusColor.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', color: statusColor.text }}>
                {getVehicleIcon(order.vehicle)}
              </div>
              <div>
                <h2 style={{ fontSize: 20, fontWeight: 800, color: S.navy, margin: 0 }}>#{order.order_number}</h2>
                <div style={{ fontSize: 13, fontWeight: 600, color: statusColor.text, marginTop: 4 }}>{statusColor.label}</div>
              </div>
            </div>

            {/* Payment status pill */}
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 6, marginBottom: 20,
              padding: '6px 12px', borderRadius: 8,
              background: order.payment_info ? '#d1fae5' : '#fef3c7',
              border: `1px solid ${order.payment_info ? '#6ee7b7' : '#fbbf24'}`,
              fontSize: 12, fontWeight: 700,
              color: order.payment_info ? '#065f46' : '#92400e',
              alignSelf: 'flex-start',
            }}>
              {order.payment_info ? '✓ Payment Initiated' : '⏳ Awaiting Payment'}
            </div>

            {/* Timeline */}
            <div style={{ marginBottom: 32 }}>
              <h3 style={{ fontSize: 14, fontWeight: 700, color: S.navy, marginBottom: 16 }}>Timeline</h3>
              <div style={{ paddingLeft: 8 }}>
                {steps.map((step, i) => (
                  <div key={i} style={{ display: 'flex', gap: 16, paddingBottom: i < steps.length - 1 ? 24 : 0, position: 'relative' }}>
                    {i < steps.length - 1 && (
                      <div style={{ position: 'absolute', left: 7, top: 20, bottom: -4, width: 2, background: step.done && steps[i + 1].done ? S.green : '#e2e8f0' }} />
                    )}
                    <div style={{ width: 16, height: 16, borderRadius: '50%', background: step.done ? S.green : '#e2e8f0', border: '2px solid #fff', boxShadow: '0 0 0 2px ' + (step.done ? S.green : '#e2e8f0'), zIndex: 1 }} />
                    <div style={{ marginTop: -2 }}>
                      <div style={{ fontSize: 13, fontWeight: 600, color: step.done ? S.navy : S.gray }}>{step.label}</div>
                      {step.time && <div style={{ fontSize: 11, color: S.grayLight, marginTop: 2 }}>{step.time}</div>}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Action buttons */}
            <div style={{ marginTop: 'auto', display: 'flex', flexDirection: 'column', gap: 10 }}>
              {/* ── PAY NOW ── */}
              {showPayNow && (
                <button
                  onClick={() => setPayNowOpen(true)}
                  style={{
                    width: '100%', padding: '13px', borderRadius: 12, border: 'none',
                    background: 'linear-gradient(135deg, #E8A838, #F5C563)',
                    color: '#1B2A4A', fontWeight: 800, fontSize: 14, cursor: 'pointer',
                    fontFamily: 'inherit', display: 'flex', alignItems: 'center', justifyContent: 'center',
                    gap: 8, boxShadow: '0 4px 16px rgba(232,168,56,0.35)',
                    transition: 'all 0.15s',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.boxShadow = '0 6px 20px rgba(232,168,56,0.5)')}
                  onMouseLeave={e => (e.currentTarget.style.boxShadow = '0 4px 16px rgba(232,168,56,0.35)')}
                >
                  💳 Pay Now — ₦{order.amount.toLocaleString()}
                </button>
              )}

              <button style={{ width: '100%', padding: '12px', borderRadius: 10, border: '1px solid #e2e8f0', background: '#fff', color: S.navy, fontWeight: 600, fontSize: 13, cursor: 'pointer' }}>
                Download Receipt
              </button>

              {order.status === 'Done' && (
                <button
                  onClick={onRate}
                  style={{ width: '100%', padding: '12px', borderRadius: 10, border: 'none', background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy, fontWeight: 600, fontSize: 13, cursor: 'pointer' }}
                >
                  Rate Experience
                </button>
              )}

              <button
                onClick={onClose}
                style={{ width: '100%', padding: '12px', borderRadius: 10, border: 'none', background: '#f1f5f9', color: S.navy, fontWeight: 600, fontSize: 13, cursor: 'pointer' }}
              >
                Close
              </button>
            </div>
          </div>

          {/* ── Right Panel — Map ── */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <div style={{ flex: 1, position: 'relative' }}>
              <DeliveryMapView
                pickupAddress={order.pickup}
                dropoffs={[{ address: order.dropoff }]}
                vehicle={order.vehicle}
                totalDeliveries={1}
                totalCost={order.amount}
                onRouteCalculated={() => { }}
              />
              <div style={{ position: 'absolute', bottom: 24, left: 24, right: 24, background: '#fff', borderRadius: 16, padding: 20, boxShadow: '0 8px 32px rgba(0,0,0,0.15)' }}>
                <div style={{ display: 'flex', gap: 16 }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: S.grayLight, textTransform: 'uppercase' }}>Pickup</div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: S.navy, marginTop: 4, lineHeight: 1.4 }}>{order.pickup}</div>
                  </div>
                  <div style={{ width: 1, background: '#f1f5f9' }} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 11, fontWeight: 700, color: S.grayLight, textTransform: 'uppercase' }}>Dropoff</div>
                    <div style={{ fontSize: 13, fontWeight: 600, color: S.navy, marginTop: 4, lineHeight: 1.4 }}>{order.dropoff}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Pay Now Modal — rendered as portal above the detail modal */}
      {payNowOpen && (
        <PayNowModal
          orderNumber={order.order_number}
          totalAmount={order.amount}
          initial={order.payment_info}
          onClose={() => setPayNowOpen(false)}
        />
      )}
    </>
  );
}
