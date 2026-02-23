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
                const errorData = await response.json();
                // Handle various error formats: {error: "..."}, {errors: {...}}, or {field: [...]}
                if (errorData.error) {
                    throw new Error(errorData.error);
                }
                const errors = errorData.errors || errorData;
                const errorMessages: string[] = [];
                for (const [field, messages] of Object.entries(errors)) {
                    if (Array.isArray(messages)) {
                        errorMessages.push(...messages.map((msg: string) => `${field}: ${msg}`));
                    } else if (typeof messages === 'string') {
                        errorMessages.push(`${field}: ${messages}`);
                    }
                }
                throw new Error(errorMessages.length > 0 ? errorMessages.join('. ') : "Login failed");
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
                const errorData = await response.json();
                // Handle nested errors object: {errors: {phone: [...], email: [...]}} or {phone: [...], email: [...]}
                const errors = errorData.errors || errorData;

                // Build a readable error message from all field errors
                const errorMessages: string[] = [];
                for (const [field, messages] of Object.entries(errors)) {
                    if (Array.isArray(messages)) {
                        errorMessages.push(...messages.map((msg: string) => `${field}: ${msg}`));
                    } else if (typeof messages === 'string') {
                        errorMessages.push(`${field}: ${messages}`);
                    }
                }

                const msg = errorMessages.length > 0 ? errorMessages.join('. ') : "Signup failed";
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
