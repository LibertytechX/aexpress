import type { Rider } from "../types";

const API_BASE_URL = "http://localhost:8000/api/dispatch"; // Adjust port if needed, assuming Django runs on 8000 or use env var

export const RiderService = {
    async getRiders(): Promise<Rider[]> {
        try {
            // Retrieve token from localStorage (assuming auth is implemented this way in other apps)
            const token = localStorage.getItem("accessToken") || localStorage.getItem("token");

            const headers: HeadersInit = {
                "Content-Type": "application/json",
            };

            if (token) {
                headers["Authorization"] = `Bearer ${token}`;
            }

            const response = await fetch(`${API_BASE_URL}/riders/`, {
                method: "GET",
                headers: headers,
            });

            if (!response.ok) {
                throw new Error(`Error fetching riders: ${response.statusText}`);
            }

            const data = await response.json();

            // Transform backend data to frontend Rider interface if needed
            // The serializer was aligned, but let's ensure type safety
            return data.map((r: any) => ({
                id: r.rider_id || r.id, // Use rider_id as display ID if available
                name: r.name,
                phone: r.phone,
                vehicle: r.vehicle, // "Bike", "Car", etc.
                status: r.status,
                currentOrder: r.current_order, // Backend uses snake_case
                todayOrders: r.todayOrders,
                todayEarnings: r.todayEarnings,
                rating: parseFloat(r.rating),
                totalDeliveries: r.totalDeliveries,
                completionRate: r.completionRate,
                avgTime: r.avgTime,
                joined: r.joined
            }));
        } catch (error) {
            console.error("Failed to fetch riders:", error);
            return [];
        }
    }
};
