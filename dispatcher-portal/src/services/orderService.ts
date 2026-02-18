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
    }
};
