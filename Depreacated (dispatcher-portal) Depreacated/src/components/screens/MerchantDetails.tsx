
import type { Order, Merchant } from "../../types";
import { S } from "../common/theme";
import { I } from "../icons";
import { StatCard } from "../common/StatCard";

interface MerchantDetailsProps {
    merchant: Merchant;
    orders: Order[];
    onBack: () => void;
}

export function MerchantDetails({ merchant, orders, onBack }: MerchantDetailsProps) {
    const merchantOrders = orders.filter(o => o.merchant === merchant.id);
    const activeOrders = merchantOrders.filter(o => ["Pending", "Assigned", "Picked Up", "In Transit"].includes(o.status)).length;
    const completedOrders = merchantOrders.filter(o => o.status === "Delivered").length;

    // Calculate total earnings/spent if needed, or rely on merchant.walletBalance
    // For now, let's use the merchant object and order stats

    const getInitials = (name: string) => name.split(" ").map(n => n[0]).join("").substring(0, 2).toUpperCase();

    return (
        <div style={{ animation: "fadeIn 0.3s ease" }}>
            <div style={{ marginBottom: 24 }}>
                <button onClick={onBack} style={{ display: "flex", alignItems: "center", gap: 6, background: "none", border: "none", color: S.textMuted, cursor: "pointer", fontSize: 13, fontWeight: 600, padding: 0 }}>
                    {I.chevronLeft} Back to Merchants
                </button>
            </div>

            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 30 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
                    <div style={{ width: 64, height: 64, borderRadius: 16, background: `linear-gradient(135deg, ${S.navy}, ${S.navyLight})`, color: S.gold, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 24, fontWeight: 800 }}>
                        {getInitials(merchant.name)}
                    </div>
                    <div>
                        <h1 style={{ fontSize: 24, fontWeight: 800, margin: 0, color: S.navy }}>{merchant.name}</h1>
                        <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 4, color: S.textMuted, fontSize: 13 }}>
                            <span>🆔 {merchant.id}</span>
                            <span>•</span>
                            <span>📱 {merchant.phone}</span>
                            <span>•</span>
                            <span style={{ padding: "2px 8px", borderRadius: 4, background: S.bg, border: `1px solid ${S.border}`, fontSize: 11, fontWeight: 600 }}>{merchant.category}</span>
                        </div>
                    </div>
                </div>
                <div style={{ textAlign: "right" }}>
                    <div style={{ fontSize: 12, fontWeight: 600, color: S.textMuted, marginBottom: 4 }}>WALLET BALANCE</div>
                    <div style={{ fontSize: 24, fontWeight: 800, color: S.green, fontFamily: "'Space Mono', monospace" }}>₦{merchant.walletBalance?.toLocaleString()}</div>
                </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 16, marginBottom: 30 }}>
                <StatCard label="Total Orders" value={merchant.totalOrders} icon={I.orders} color={S.navy} />
                <StatCard label="Active Orders" value={activeOrders} icon={I.clock} color={S.gold} />
                <StatCard label="Completed" value={completedOrders} icon={I.check} color={S.green} />
                <StatCard label="Join Date" value={new Date(merchant.joined).toLocaleDateString()} icon={I.calendar} color={S.purple} />
            </div>

            <h3 style={{ fontSize: 16, fontWeight: 700, color: S.navy, marginBottom: 16 }}>Recent Orders</h3>
            <div style={{ background: "#fff", borderRadius: 12, border: `1px solid ${S.border}`, overflow: "hidden" }}>
                <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                    <thead style={{ background: S.bg, color: S.textMuted, fontSize: 11, textTransform: "uppercase", letterSpacing: "0.5px" }}>
                        <tr>
                            <th style={{ padding: "12px 20px", textAlign: "left" }}>ID</th>
                            <th style={{ padding: "12px 20px", textAlign: "left" }}>Date</th>
                            <th style={{ padding: "12px 20px", textAlign: "left" }}>Pickup</th>
                            <th style={{ padding: "12px 20px", textAlign: "left" }}>Dropoff</th>
                            <th style={{ padding: "12px 20px", textAlign: "left" }}>Amount</th>
                            <th style={{ padding: "12px 20px", textAlign: "left" }}>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {merchantOrders.length === 0 ? (
                            <tr><td colSpan={6} style={{ padding: 40, textAlign: "center", color: S.textMuted }}>No orders found</td></tr>
                        ) : (
                            merchantOrders.slice(0, 10).map(o => (
                                <tr key={o.id} style={{ borderTop: `1px solid ${S.border}` }}>
                                    <td style={{ padding: "14px 20px", fontWeight: 600, fontFamily: "'Space Mono', monospace" }}>{o.id}</td>
                                    <td style={{ padding: "14px 20px", color: S.textDim }}>{new Date(o.created).toLocaleDateString()}</td>
                                    <td style={{ padding: "14px 20px" }}>{o.pickup?.split(",")[0]}</td>
                                    <td style={{ padding: "14px 20px" }}>{o.dropoff?.split(",")[0]}</td>
                                    <td style={{ padding: "14px 20px", fontFamily: "'Space Mono', monospace" }}>₦{o.amount.toLocaleString()}</td>
                                    <td style={{ padding: "14px 20px" }}>
                                        <span style={{
                                            padding: "4px 8px", borderRadius: 6, fontSize: 11, fontWeight: 700,
                                            background: o.status === "Delivered" ? S.greenBg : o.status === "Pending" ? S.yellowBg : S.blueBg,
                                            color: o.status === "Delivered" ? S.green : o.status === "Pending" ? S.yellow : S.blue
                                        }}>
                                            {o.status.toUpperCase()}
                                        </span>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
