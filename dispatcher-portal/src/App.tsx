import { useState } from 'react';
import './index.css';
import { I } from './components/icons';
import { S } from './components/common/theme';
import { DashboardScreen, OrdersScreen, RidersScreen, MerchantsScreen, CustomersScreen, MessagingScreen, SettingsScreen } from './components/screens';
import { CreateOrderModal } from './components/modals/CreateOrderModal';
import { INIT_ORDERS, INIT_RIDERS, MERCHANTS_DATA, CUSTOMERS_DATA } from './data/mockData';
import type { Order, LogEvent } from './types';

function App() {
  const [nav, setNav] = useState("Dashboard");
  const [orders, setOrders] = useState<Order[]>(INIT_ORDERS);
  const [riders] = useState(INIT_RIDERS);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedOrderId, setSelectedOrderId] = useState<string | null>(null);
  const [selectedRiderId, setSelectedRiderId] = useState<string | null>(null);
  const [eventLogs, setEventLogs] = useState<Record<string, LogEvent[]>>({});

  const menus = [
    { id: "Dashboard", icon: I.dashboard },
    { id: "Orders", icon: I.orders },
    { id: "Riders", icon: I.riders },
    { id: "Merchants", icon: I.merchants },
    { id: "Customers", icon: I.customers },
    { id: "Messaging", icon: I.messaging },
    { id: "Settings", icon: I.settings },
  ];

  /* 
    Helper to add logs 
    This is extracted here so it can be passed down.
  */
  const addLog = (oid: string, text: string, type: string = "status") => {
    const log: LogEvent = { time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }), event: text, by: "Dispatcher", type };
    setEventLogs(prev => ({ ...prev, [oid]: [log, ...(prev[oid] || [])] }));
  };

  const handleUpdateOrder = (oid: string, field: string, val: any) => {
    setOrders(prev => prev.map(o => o.id === oid ? { ...o, [field]: val } : o));
  };

  const handleStatusChange = (oid: string, status: any) => {
    handleUpdateOrder(oid, "status", status);
    addLog(oid, `Status changed to ${status}`);
  };

  const handleAssign = (oid: string, rid: string) => {
    if (!rid) {
      // Unassign
      handleUpdateOrder(oid, "riderId", null);
      handleUpdateOrder(oid, "rider", null);
      handleStatusChange(oid, "Pending");
      addLog(oid, "Rider unassigned", "issue");
    } else {
      const r = riders.find(rx => rx.id === rid);
      if (r) {
        handleUpdateOrder(oid, "riderId", rid);
        handleUpdateOrder(oid, "rider", r.name);
        handleStatusChange(oid, "Assigned");
        addLog(oid, `Assigned to ${r.name} (${r.vehicle})`);
      }
    }
  };

  const renderContent = () => {
    switch (nav) {
      case "Dashboard":
        return <DashboardScreen orders={orders} riders={riders} onViewOrder={id => { setNav("Orders"); setSelectedOrderId(id); }} onViewRider={id => { setNav("Riders"); setSelectedRiderId(id); }} />;
      case "Orders":
        return <OrdersScreen orders={orders} riders={riders} selectedId={selectedOrderId} onSelect={setSelectedOrderId} onBack={() => setSelectedOrderId(null)} onViewRider={id => { setNav("Riders"); setSelectedRiderId(id); }} onAssign={handleAssign} onChangeStatus={handleStatusChange} onUpdateOrder={handleUpdateOrder} addLog={addLog} eventLogs={eventLogs} />;
      case "Riders":
        return <RidersScreen riders={riders} orders={orders} selectedId={selectedRiderId} onSelect={setSelectedRiderId} onBack={() => setSelectedRiderId(null)} onViewOrder={id => { setNav("Orders"); setSelectedOrderId(id); }} />;
      case "Merchants":
        return <MerchantsScreen data={MERCHANTS_DATA} />;
      case "Customers":
        return <CustomersScreen data={CUSTOMERS_DATA} />;
      case "Messaging":
        return <MessagingScreen />;
      case "Settings":
        return <SettingsScreen />;
      default:
        return <div>Not Implemented</div>;
    }
  };

  return (
    <div style={{ display: "flex", height: "100vh", background: S.bg, color: S.text }}>
      {/* Sidebar */}
      <div style={{ width: 240, background: S.navy, color: "#fff", display: "flex", flexDirection: "column", padding: 20 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 40, paddingLeft: 10 }}>
          <div style={{ width: 32, height: 32, background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, borderRadius: 8 }} />
          <div>
            <div style={{ fontSize: 16, fontWeight: 800, letterSpacing: "-0.5px" }}>AX DISPATCH</div>
            <div style={{ fontSize: 10, opacity: 0.5, letterSpacing: "2px" }}>PORTAL v2.0</div>
          </div>
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          {menus.map(m => (
            <button key={m.id} onClick={() => { setNav(m.id); setSelectedOrderId(null); setSelectedRiderId(null); }}
              style={{
                display: "flex", alignItems: "center", gap: 12, padding: "12px 16px", borderRadius: 10, border: "none", cursor: "pointer",
                background: nav === m.id ? "rgba(255,255,255,0.1)" : "transparent",
                color: nav === m.id ? S.gold : "#94a3b8",
                fontFamily: "inherit", fontWeight: 600, fontSize: 13, textAlign: "left", transition: "all 0.2s"
              }}>
              <span style={{ opacity: nav === m.id ? 1 : 0.7 }}>{m.icon}</span>
              {m.id}
            </button>
          ))}
        </div>

        <div style={{ marginTop: "auto" }}>
          <div style={{ padding: 16, background: "rgba(255,255,255,0.05)", borderRadius: 12 }}>
            <div style={{ fontSize: 11, color: "#94a3b8", marginBottom: 6 }}>SYSTEM STATUS</div>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}><div style={{ width: 6, height: 6, borderRadius: "50%", background: S.green }} /><span style={{ fontSize: 12, fontWeight: 600 }}>All Systems Operational</span></div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        {/* Top Header */}
        <div style={{ height: 70, borderBottom: `1px solid ${S.border}`, display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 30px", background: "#fff" }}>
          <h1 style={{ fontSize: 20, fontWeight: 800 }}>{nav}</h1>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div style={{ textAlign: "right" }}><div style={{ fontSize: 13, fontWeight: 700 }}>Dispatcher Jane</div><div style={{ fontSize: 11, color: S.textMuted }}>Admin</div></div>
              <div style={{ width: 36, height: 36, borderRadius: "50%", background: "#e2e8f0" }} />
            </div>
            <button onClick={() => setShowCreateModal(true)} style={{ display: "flex", alignItems: "center", gap: 6, padding: "10px 18px", background: S.navy, color: "#fff", border: "none", borderRadius: 10, fontSize: 12, fontWeight: 700, cursor: "pointer" }}>
              {I.plus} New Order
            </button>
          </div>
        </div>

        {/* Scrollable Area */}
        <div style={{ flex: 1, overflowY: "auto", padding: 30 }}>
          {renderContent()}
        </div>
      </div>

      {showCreateModal && <CreateOrderModal riders={riders} onClose={() => setShowCreateModal(false)} />}
    </div>
  );
}

export default App;
