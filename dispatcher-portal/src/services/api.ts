// Re-export everything from the central lib/api.ts so imports like
// `import { ActivityFeedAPI } from '@/services/api'` continue to work.
export {
    fetchWithAuth,
    AuthAPI,
    RidersAPI,
    OrdersAPI,
    MerchantsAPI,
    MerchantPricingOverridesAPI,
    VehiclesAPI,
    VehicleAssetsAPI,
    ActivityFeedAPI,
    SettingsAPI,
    ZonesAPI,
    RelayNodesAPI,
    DispatchersAPI,
} from '@/lib/api';
