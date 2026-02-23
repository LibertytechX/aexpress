import type { Merchant } from "../types";

const API_BASE_URL = `${import.meta.env.VITE_API_BASE_URL}/dispatch`;

export const MerchantService = {
    async getMerchants(): Promise<Merchant[]> {
        try {
            const token = localStorage.getItem("access_token");

            const headers: HeadersInit = {
                "Content-Type": "application/json",
            };

            if (token) {
                headers["Authorization"] = `Bearer ${token}`;
            }

            const response = await fetch(`${API_BASE_URL}/merchants/`, {
                method: "GET",
                headers: headers,
            });

            if (!response.ok) {
                console.error("Merchant API Error:", response.status, response.statusText);
                throw new Error(`Error fetching merchants: ${response.statusText}`);
            }

            const data = await response.json();
            console.log("Merchant API Response:", data);

            if (Array.isArray(data)) {
                return data;
            } else if (data && Array.isArray(data.results)) {
                return data.results;
            }

            return [];
        } catch (error) {
            console.error("Failed to fetch merchants:", error);
            return [];
        }
    }
};
