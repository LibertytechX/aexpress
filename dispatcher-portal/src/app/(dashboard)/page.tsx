'use client';

import { useRouter } from 'next/navigation';
import { useDispatcher } from '@/contexts/DispatcherContext';
import { DashboardScreen } from '@/components/screens';

export default function DashboardPageRoute() {
  const { orders, riders, setSelectedOrderId, setSelectedRiderId } = useDispatcher();
  const router = useRouter();

  return (
    <DashboardScreen
      orders={orders}
      riders={riders}
      onViewOrder={(id) => {
        setSelectedOrderId(id);
        router.push('/orders');
      }}
      onViewRider={(id) => {
        setSelectedRiderId(id);
        router.push('/riders');
      }}
    />
  );
}
