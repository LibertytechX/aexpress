'use client';

import React from 'react';
import { S } from '@/lib/theme';
import Icons from '@/components/Icons';
import DeliveryMapView from '@/components/common/DeliveryMapView';
import { STATUS_COLORS, formatDate, getVehicleIcon } from '@/lib/utils';

export default function OrderDetailModal({ order, onClose, onRate }) {
  if (!order) return null;
  const statusColor = STATUS_COLORS[order.status] || STATUS_COLORS.Pending;

  // Mock tracking steps for visualization
  const steps = [
    { label: "Order Placed", time: order.date, done: true },
    { label: "Rider Assigned", time: order.status !== 'Pending' ? "Verified" : null, done: order.status !== 'Pending' },
    { label: "Picked Up", time: order.status === 'PickedUp' || order.status === 'Done' ? "Verified" : null, done: order.status === 'PickedUp' || order.status === 'Done' },
    { label: "Delivered", time: order.status === 'Done' ? "Verified" : null, done: order.status === 'Done' },
  ];

  return (
    <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }} onClick={onClose}>
      <div onClick={e => e.stopPropagation()} style={{
        background: "#fff", borderRadius: 20, width: 900, height: "85vh", display: "flex", overflow: "hidden",
        boxShadow: "0 24px 48px rgba(0,0,0,0.2)"
      }}>
        {/* Left Panel - Details */}
        <div style={{ width: 400, padding: 32, overflowY: "auto", borderRight: "1px solid #e2e8f0", display: "flex", flexDirection: "column" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 24 }}>
            <div style={{
              width: 48, height: 48, borderRadius: 12, background: statusColor.bg,
              display: "flex", alignItems: "center", justifyContent: "center", color: statusColor.text
            }}>{getVehicleIcon(order.vehicle)}</div>
            <div>
              <h2 style={{ fontSize: 20, fontWeight: 800, color: S.navy, margin: 0 }}>#{order.order_number}</h2>
              <div style={{ fontSize: 13, fontWeight: 600, color: statusColor.text, marginTop: 4 }}>{statusColor.label}</div>
            </div>
          </div>

          {/* Tracking Timeline */}
          <div style={{ marginBottom: 32 }}>
            <h3 style={{ fontSize: 14, fontWeight: 700, color: S.navy, marginBottom: 16 }}>Timeline</h3>
            <div style={{ paddingLeft: 8 }}>
              {steps.map((step, i) => (
                <div key={i} style={{ display: "flex", gap: 16, paddingBottom: i < steps.length - 1 ? 24 : 0, position: "relative" }}>
                  {i < steps.length - 1 && (
                    <div style={{
                      position: "absolute", left: 7, top: 20, bottom: -4, width: 2,
                      background: step.done && steps[i + 1].done ? S.green : "#e2e8f0"
                    }} />
                  )}
                  <div style={{
                    width: 16, height: 16, borderRadius: "50%", background: step.done ? S.green : "#e2e8f0",
                    border: "2px solid #fff", boxShadow: "0 0 0 2px " + (step.done ? S.green : "#e2e8f0"), zIndex: 1
                  }} />
                  <div style={{ marginTop: -2 }}>
                    <div style={{ fontSize: 13, fontWeight: 600, color: step.done ? S.navy : S.gray }}>{step.label}</div>
                    {step.time && <div style={{ fontSize: 11, color: S.grayLight, marginTop: 2 }}>{step.time}</div>}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ marginTop: "auto" }}>
            <button style={{
              width: "100%", padding: "12px", borderRadius: 10, border: "1px solid #e2e8f0", background: "#fff",
              color: S.navy, fontWeight: 600, fontSize: 13, marginBottom: 12, cursor: "pointer"
            }}>Download Receipt</button>
            {order.status === 'Done' && (
              <button onClick={onRate} style={{
                width: "100%", padding: "12px", borderRadius: 10, border: "none",
                background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`,
                color: S.navy, fontWeight: 600, fontSize: 13, cursor: "pointer"
              }}>Rate Experience</button>
            )}
            <button onClick={onClose} style={{
              width: "100%", padding: "12px", borderRadius: 10, border: "none", background: "#f1f5f9",
              color: S.navy, fontWeight: 600, fontSize: 13, cursor: "pointer", marginTop: 8
            }}>Close</button>
          </div>
        </div>

        {/* Right Panel - Map/Info */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
          {/* Map */}
          <div style={{ flex: 1, position: "relative" }}>
            {/* Note: In a real app we'd pass actual coordinates if available. 
                MerchantPortal.jsx might have passed them. 
                For now we rely on address strings if coordinates aren't in order object 
                (which they might not be in the transformed object unless we added them).
                DeliveryMapView handles basic markers but geocoding might happen inside it 
                or in NewOrderScreen. For detail view, we ideally want lat/lng.
                If not available, map might be blank or centered on default.
                Let's assume transformed order might have them or we can geocode again.
            */}
            <DeliveryMapView
              pickupAddress={order.pickup}
              dropoffs={[{ address: order.dropoff }]}
              vehicle={order.vehicle}
              totalDeliveries={1}
              totalCost={order.amount}
              onRouteCalculated={() => { }}
            />
            <div style={{
              position: "absolute", bottom: 24, left: 24, right: 24, background: "#fff",
              borderRadius: 16, padding: 20, boxShadow: "0 8px 32px rgba(0,0,0,0.15)"
            }}>
              <div style={{ display: "flex", gap: 16 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: S.grayLight, textTransform: "uppercase" }}>Pickup</div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: S.navy, marginTop: 4, lineHeight: 1.4 }}>
                    {order.pickup}
                  </div>
                </div>
                <div style={{ width: 1, background: "#f1f5f9" }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: S.grayLight, textTransform: "uppercase" }}>Dropoff</div>
                  <div style={{ fontSize: 13, fontWeight: 600, color: S.navy, marginTop: 4, lineHeight: 1.4 }}>
                    {order.dropoff}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
