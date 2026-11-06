'use client';

import React, { useState } from 'react';
import Icons from '@/components/Icons';
import { S } from '@/lib/theme';
import { STATUS_COLORS, getVehicleIcon, UIOrder } from '@/lib/utils';
import OrderDetailModal from './OrderDetailModal';
import RateRiderModal from './RateRiderModal';

interface OrdersScreenProps {
  orders: UIOrder[];
  onRateOrder: (data: { orderId: string, rating: number, comment: string }) => Promise<void>;
}

export default function OrdersScreen({ orders, onRateOrder }: OrdersScreenProps) {
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [selectedOrder, setSelectedOrder] = useState<UIOrder | null>(null);
  const [showRateModal, setShowRateModal] = useState(false);

  // Filter logic
  const filteredOrders = orders.filter(o => {
    if (filter !== "all" && o.status !== filter) return false;
    if (search && !o.id.toLowerCase().includes(search.toLowerCase()) && !o.pickup.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 140px)" }}>
      {/* Controls */}
      <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 20 }}>
        <div style={{ display: "flex", gap: 10 }}>
          {["all", "Pending", "Started", "Done", "Canceled"].map(f => (
            <button key={f} onClick={() => setFilter(f)} style={{
              padding: "8px 16px", borderRadius: 10, border: filter === f ? `2px solid ${S.navy}` : "1px solid #e2e8f0",
              background: filter === f ? S.navy : "#fff", color: filter === f ? "#fff" : S.gray,
              fontSize: 13, fontWeight: 600, cursor: "pointer", fontFamily: "inherit"
            }}>
              {f === "all" ? "All Orders" : f}
            </button>
          ))}
        </div>
        <input
          placeholder="Search by ID or Address"
          value={search}
          onChange={e => setSearch(e.target.value)}
          style={{
            padding: "0 16px", borderRadius: 10, border: "1.5px solid #e2e8f0", width: 300,
            fontSize: 13, fontFamily: "inherit"
          }}
        />
      </div>

      {/* List */}
      <div style={{ flex: 1, overflowY: "auto", background: "#fff", borderRadius: 16, border: "1px solid #e2e8f0" }}>
        {filteredOrders.length === 0 ? (
          <div style={{ padding: 40, textAlign: "center", color: S.gray }}>No orders found</div>
        ) : (
          filteredOrders.map((order, i) => (
            <div key={order.id} onClick={() => setSelectedOrder(order)} style={{
              padding: "20px 24px", display: "flex", alignItems: "center", gap: 20, cursor: "pointer",
              borderBottom: "1px solid #f1f5f9", transition: "background 0.1s"
            }} onMouseEnter={e => e.currentTarget.style.background = "#f8fafc"} onMouseLeave={e => e.currentTarget.style.background = "#fff"}>
              <div style={{ width: 50, height: 50, borderRadius: 12, background: S.goldPale, display: "flex", alignItems: "center", justifyContent: "center", color: S.gold }}>
                {getVehicleIcon(order.vehicle)}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 4 }}>
                  <span style={{ fontSize: 16, fontWeight: 700, color: S.navy }}>#{order.order_number}</span>
                  <span style={{ fontSize: 12, fontWeight: 600, padding: "2px 8px", borderRadius: 6, background: STATUS_COLORS[order.status]?.bg || "#eee", color: STATUS_COLORS[order.status]?.text || "#333" }}>
                    {STATUS_COLORS[order.status]?.label || order.status}
                  </span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: 12, fontSize: 13, color: S.gray }}>
                  <span>{order.date}</span>
                  <span>•</span>
                  <span>{order.pickup} → {order.dropoff}</span>
                </div>
              </div>
              <div style={{ textAlign: "right", fontSize: 16, fontWeight: 700, color: S.navy, fontFamily: "'Space Mono', monospace" }}>
                ₦{order.amount.toLocaleString()}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Modals */}
      {selectedOrder && (
        <OrderDetailModal
          order={selectedOrder}
          onClose={() => setSelectedOrder(null)}
          onRate={() => { setShowRateModal(true); /* Don't close details yet? or overlay? usually close details first or stack */ }}
        />
      )}

      {showRateModal && selectedOrder && (
        <RateRiderModal
          order={selectedOrder}
          onClose={() => setShowRateModal(false)}
          onSubmit={async (review) => {
            await onRateOrder({
              orderId: selectedOrder.id,
              rating: review.rating,
              comment: review.comment
            });
            setShowRateModal(false);
            setSelectedOrder(null);
          }}
        />
      )}
    </div>
  );
}
