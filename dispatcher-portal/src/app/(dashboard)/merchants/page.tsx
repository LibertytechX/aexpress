'use client';

import { useDispatcher } from '@/contexts/DispatcherContext';
import { MerchantsScreen } from '@/components/screens';

export default function MerchantsPageRoute() {
    const {
        merchants,
        orders,
        selectedMerchantId,
        setSelectedMerchantId
    } = useDispatcher();

    return (
        <MerchantsScreen
            data={merchants}
            orders={orders}
            selectedId={selectedMerchantId}
            onSelect={setSelectedMerchantId}
            onBack={() => setSelectedMerchantId(null)}
        />
    );
}
