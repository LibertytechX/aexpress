'use client';

import { CustomersScreen } from '@/components/screens';
import { CUSTOMERS_DATA } from '@/data/mockData';

export default function CustomersPageRoute() {
    return (
        <CustomersScreen data={CUSTOMERS_DATA} />
    );
}
