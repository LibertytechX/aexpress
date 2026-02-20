import type { User } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export const AuthService = {
    async login(phone: string, password: string): Promise<User | null> {
        try {
            const response = await fetch(`${API_BASE_URL}/auth/login/`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ phone, password }),
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.error || "Login failed");
            }

            const data = await response.json();

            // Store tokens
            if (data.tokens) {
                localStorage.setItem("access_token", data.tokens.access);
                localStorage.setItem("refresh_token", data.tokens.refresh);

                return {
                    id: data.user.id,
                    name: data.user.contact_name || data.user.business_name || "Dispatcher",
                    phone: data.user.phone,
                    email: data.user.email,
                    token: data.tokens.access
                };
            }

            throw new Error("Invalid response format");
        } catch (error) {
            console.error("Login error:", error);
            throw error;
        }
    },

    async signup(data: { phone: string; email: string; password: string; contact_name: string; business_name: string }): Promise<User | null> {
        try {
            const response = await fetch(`${API_BASE_URL}/auth/signup/`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ ...data, usertype: "Dispatcher" }),
            });

            if (!response.ok) {
                const error = await response.json();
                // Extract first error message if it's a dict
                const msg = Object.values(error).flat()[0] as string || "Signup failed";
                throw new Error(msg);
            }

            // After signup, we might want to auto-login or ask user to login.
            // For now, let's assume we need to login separately, or if the API returns tokens (which DispatcherSignupView did NOT, but generic SignupView likely does not return tokens by default unless customized).
            // Wait, common pattern is to return user data.
            // Existing `SignupView` (from authentication/views.py) usually returns User data but maybe not tokens.

            // Let's check `authentication/views.py` content via memory or assumptions?
            // Safer to just return true/false or user data and then redirect to login.
            return null;
        } catch (error) {
            console.error("Signup error:", error);
            throw error;
        }
    },

    logout() {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        window.location.reload();
    },

    isAuthenticated(): boolean {
        return !!localStorage.getItem("access_token");
    }
};
