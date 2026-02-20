const API_BASE_URL = `${(process.env.NEXT_PUBLIC_API_BASE_URL || '')}/dispatch`;

export interface SystemSettings {
    id: number;
    bridge_surcharge: number; // Decimal string or number from backend? usually string for Decimal
    outer_zone_surcharge: number;
    island_premium: number;
    weight_threshold_kg: number;
    weight_surcharge_per_unit: number;
    weight_unit_kg: number;
    surge_enabled: boolean;
    surge_multiplier: number;
    surge_morning_start: string;
    surge_morning_end: string;
    surge_evening_start: string;
    surge_evening_end: string;
    rain_surge_enabled: boolean;
    rain_surge_multiplier: number;
    tier_enabled: boolean;
    tier1_km: number;
    tier1_discount_pct: number;
    tier2_km: number;
    tier2_discount_pct: number;
    auto_assign_enabled: boolean;
    auto_assign_radius_km: number;
    accept_timeout_sec: number;
    max_concurrent_bike: number;
    max_concurrent_car: number;
    max_concurrent_van: number;
    cod_flat_fee: number;
    cod_pct_fee: number;
    notif_new_order: boolean;
    notif_unassigned: boolean;
    notif_completed: boolean;
    notif_cod_settled: boolean;
}

export const SettingsService = {
    async getSettings(): Promise<SystemSettings | null> {
        try {
            const token = localStorage.getItem("access_token");
            const headers: HeadersInit = { "Content-Type": "application/json" };
            if (token) headers["Authorization"] = `Bearer ${token}`;

            const response = await fetch(`${API_BASE_URL}/settings/`, {
                method: "GET",
                headers,
            });

            if (!response.ok) throw new Error("Failed to fetch settings");
            return await response.json();
        } catch (error) {
            console.error("SettingsService Error:", error);
            return null;
        }
    },

    async updateSettings(data: Partial<SystemSettings>): Promise<SystemSettings | null> {
        try {
            const token = localStorage.getItem("access_token");
            const headers: HeadersInit = { "Content-Type": "application/json" };
            if (token) headers["Authorization"] = `Bearer ${token}`;

            const response = await fetch(`${API_BASE_URL}/settings/`, {
                method: "POST", // Using POST as defined in view (or should be PUT/PATCH?) View uses POST.
                headers,
                body: JSON.stringify(data),
            });

            if (!response.ok) throw new Error("Failed to update settings");
            return await response.json();
        } catch (error) {
            console.error("SettingsService Update Error:", error);
            return null;
        }
    }
};
