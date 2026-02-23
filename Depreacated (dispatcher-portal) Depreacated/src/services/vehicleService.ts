
export interface Vehicle {
    id: number;
    name: string;
    max_weight_kg: number;
    base_price: string; // Deprecated flat rate
    base_fare: string;
    rate_per_km: string;
    rate_per_minute: string;
    min_distance_km: string;
    min_fee: string;
    description: string;
    is_active: boolean;
}

const API_BASE_URL = `${import.meta.env.VITE_API_BASE_URL}/orders`;

export const VehicleService = {
    getVehicles: async (): Promise<Vehicle[]> => {
        try {
            const token = localStorage.getItem("access_token");
            const response = await fetch(`${API_BASE_URL}/vehicles/`, {
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            });

            if (!response.ok) throw new Error("Failed to fetch vehicles");

            const data = await response.json();
            return data.vehicles || [];
        } catch (error) {
            console.error('Failed to fetch vehicles', error);
            return [];
        }
    },

    updateVehicle: async (id: number, data: Partial<Vehicle>): Promise<Vehicle | null> => {
        try {
            const token = localStorage.getItem("access_token");
            const response = await fetch(`${API_BASE_URL}/vehicles/${id}/`, {
                method: "PATCH",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(data)
            });

            if (!response.ok) throw new Error("Failed to update vehicle");

            const resData = await response.json();
            return resData.vehicle;
        } catch (error) {
            console.error('Failed to update vehicle', error);
            return null;
        }
    }
};
