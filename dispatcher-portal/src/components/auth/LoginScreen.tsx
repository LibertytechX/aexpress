import { useState } from "react";
import { AuthService } from "../../services/authService";
import { S } from "../common/theme";

interface LoginScreenProps {
    onLoginSuccess: (user: any) => void;
    onSwitchToSignup: () => void;
}

export function LoginScreen({ onLoginSuccess, onSwitchToSignup }: LoginScreenProps) {
    const [phone, setPhone] = useState("");
    const [password, setPassword] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError(null);

        try {
            const user = await AuthService.login(phone, password);
            if (user) {
                onLoginSuccess(user);
            } else {
                setError("Login failed. Please check your credentials.");
            }
        } catch (err: any) {
            setError(err.message || "An error occurred during login.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", height: "100vh", background: S.navy }}>
            <div style={{ background: S.card, padding: 40, borderRadius: 16, width: "100%", maxWidth: 400, boxShadow: "0 10px 25px rgba(0,0,0,0.2)" }}>
                <div style={{ textAlign: "center", marginBottom: 30 }}>
                    <h2 style={{ fontSize: 24, fontWeight: 800, color: S.navy, marginBottom: 8 }}>Welcome Back</h2>
                    <p style={{ color: S.textMuted, fontSize: 14 }}>Login to your Dispatcher Portal</p>
                </div>

                {error && (
                    <div style={{ background: S.redBg, color: S.red, padding: "10px 14px", borderRadius: 8, fontSize: 13, marginBottom: 20, textAlign: "center" }}>
                        {error}
                    </div>
                )}

                <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                    <div>
                        <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: S.textDim, marginBottom: 6 }}>Phone Number</label>
                        <input
                            type="tel"
                            value={phone}
                            onChange={(e) => setPhone(e.target.value)}
                            placeholder="+234..."
                            required
                            style={{ width: "100%", padding: "12px 14px", borderRadius: 10, border: `1px solid ${S.border}`, fontSize: 14, fontFamily: "inherit", outline: "none" }}
                        />
                    </div>
                    <div>
                        <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: S.textDim, marginBottom: 6 }}>Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Enter your password"
                            required
                            style={{ width: "100%", padding: "12px 14px", borderRadius: 10, border: `1px solid ${S.border}`, fontSize: 14, fontFamily: "inherit", outline: "none" }}
                        />
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        style={{
                            marginTop: 10,
                            padding: "14px",
                            background: loading ? S.textDim : S.gold,
                            color: "#fff",
                            border: "none",
                            borderRadius: 10,
                            fontSize: 14,
                            fontWeight: 700,
                            cursor: loading ? "not-allowed" : "pointer",
                            transition: "background 0.2s"
                        }}
                    >
                        {loading ? "Logging in..." : "Login"}
                    </button>
                </form>

                <div style={{ marginTop: 24, textAlign: "center", fontSize: 13, color: S.textDim }}>
                    Don't have an account? <span onClick={onSwitchToSignup} style={{ color: S.blue, fontWeight: 600, cursor: "pointer" }}>Sign up</span>
                </div>
            </div>
        </div>
    );
}
