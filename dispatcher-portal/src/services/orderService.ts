import type { Order } from "../types";

const API_BASE_URL = "http://localhost:8000/api/dispatch";

export const OrderService = {
    async getOrders(): Promise<Order[]> {
        try {
            const token = localStorage.getItem("access_token");

            const headers: HeadersInit = {
                "Content-Type": "application/json",
            };

            if (token) {
                headers["Authorization"] = `Bearer ${token}`;
            }

            const response = await fetch(`${API_BASE_URL}/orders/`, {
                method: "GET",
                headers: headers,
            });

            if (!response.ok) {
                // If 401, maybe logout? For now just throw
                throw new Error(`Error fetching orders: ${response.statusText}`);
            }

            const data = await response.json();

            // The serializer matches the Order interface, so we might just return data
            // But let's map to be safe if specific transforms needed (e.g. dates)
            return data.map((o: any) => ({
                ...o,
                // Ensure fields match if backend returns nulls where frontend expects strings (though serializer handles most)
                rider: o.rider || null,
                riderId: o.riderId || null,
                status: o.status, // Ensure status string matches enum if possible
            }));
        } catch (error) {
            console.error("Failed to fetch orders:", error);
            return [];
        }
    },

    async createOrder(orderData: any): Promise<boolean> {
        try {
            const token = localStorage.getItem("access_token");
            const response = await fetch(`${API_BASE_URL}/orders/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify(orderData)
            });

            if (!response.ok) {
                const err = await response.json();
                console.error("Create Order Failed:", err);
                throw new Error("Failed to create order");
            }
            return true;
        } catch (error) {
            console.error("Create Order Error:", error);
            return false;
        }
    },

    async calculateFare(vehicle: string, distanceKm: number, durationMinutes: number): Promise<number | null> {
        try {
            const token = localStorage.getItem("access_token");
            const response = await fetch("http://localhost:8000/api/orders/calculate-fare/", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}`
                },
                body: JSON.stringify({
                    vehicle,
                    distance_km: distanceKm,
                    duration_minutes: durationMinutes
                })
            });

            if (!response.ok) throw new Error("Failed to calculate fare");

            const data = await response.json();
            return data.price;
        } catch (error) {
            console.error("Calculate Fare Error:", error);
            return null;
        }
    },

    async getVehicles(): Promise<any[]> {
        try {
            const token = localStorage.getItem("access_token");
            const response = await fetch("http://localhost:8000/api/orders/vehicles/", {
                headers: {
                    "Authorization": `Bearer ${token}`
                }
            });
            if (!response.ok) throw new Error("Failed to fetch vehicles");
            const data = await response.json();
            return data.vehicles || [];
        } catch (error) {
            console.error("Vehicle fetch error:", error);
            return [];
        }
    },

    calculatePrice(vehicle: any, distanceKm: number, durationMinutes: number): number {
        const base = parseFloat(vehicle.base_fare);
        const rateKm = parseFloat(vehicle.rate_per_km);
        const rateMin = parseFloat(vehicle.rate_per_minute);

        const total = base + (distanceKm * rateKm) + (durationMinutes * rateMin);
        return Math.round(total * 100) / 100;
    }
};
