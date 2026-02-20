'use client';

import { useRouter } from 'next/navigation';
import { useDispatcher } from '@/contexts/DispatcherContext';
import { OrdersScreen } from '@/components/screens';

export default function OrdersPageRoute() {
    const {
        orders,
        riders,
        selectedOrderId,
        setSelectedOrderId,
        setSelectedRiderId,
        handleAssign,
        handleStatusChange,
        handleUpdateOrder,
        addLog,
        eventLogs
    } = useDispatcher();
    const router = useRouter();

    return (
        <OrdersScreen
            orders={orders}
            riders={riders}
            selectedId={selectedOrderId}
            onSelect={setSelectedOrderId}
            onBack={() => setSelectedOrderId(null)}
            onViewRider={(id) => {
                setSelectedRiderId(id);
                router.push('/riders');
            }}
            onAssign={handleAssign}
            onChangeStatus={handleStatusChange}
            onUpdateOrder={handleUpdateOrder}
            addLog={addLog}
            eventLogs={eventLogs}
        />
    );
}
