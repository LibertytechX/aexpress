'use client';

import { useRouter } from 'next/navigation';
import { useDispatcher } from '@/contexts/DispatcherContext';
import { RidersScreen } from '@/components/screens';

export default function RidersPageRoute() {
    const {
        riders,
        orders,
        selectedRiderId,
        setSelectedRiderId,
        setSelectedOrderId
    } = useDispatcher();
    const router = useRouter();

    return (
        <RidersScreen
            riders={riders}
            orders={orders}
            selectedId={selectedRiderId}
            onSelect={setSelectedRiderId}
            onBack={() => setSelectedRiderId(null)}
            onViewOrder={(id) => {
                setSelectedOrderId(id);
                router.push('/orders');
            }}
        />
    );
}
