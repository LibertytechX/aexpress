import type { Rider } from "../types";

const API_BASE_URL = `${import.meta.env.VITE_API_BASE_URL}/dispatch`;

export const RiderService = {
    async getRiders(): Promise<Rider[]> {
        try {
            // Retrieve token from localStorage
            const token = localStorage.getItem("access_token");

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
    },

    async onboardRider(formData: FormData): Promise<any> {
        try {
            const token = localStorage.getItem("access_token");
            const response = await fetch(`${API_BASE_URL}/riders/onboarding/`, {
                method: "POST",
                headers: {
                    "Authorization": `Bearer ${token}`
                },
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw errorData;
            }
            return await response.json();
        } catch (error) {
            console.error("Rider Onboarding Error:", error);
            throw error;
        }
    }
};
