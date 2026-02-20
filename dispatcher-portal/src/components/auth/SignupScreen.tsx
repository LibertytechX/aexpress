import { useState } from "react";
import { AuthService } from "../../services/authService";
import { S } from "../common/theme";

interface SignupScreenProps {
    onSignupSuccess: () => void;
    onSwitchToLogin: () => void;
}

export function SignupScreen({ onSignupSuccess, onSwitchToLogin }: SignupScreenProps) {
    const [formData, setFormData] = useState({
        phone: "",
        email: "",
        contact_name: "",
        business_name: "",
        password: "",
        confirm_password: ""
    });
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSignup = async (e: React.FormEvent) => {
        e.preventDefault();
        if (formData.password !== formData.confirm_password) {
            setError("Passwords do not match");
            return;
        }

        setLoading(true);
        setError(null);

        try {
            await AuthService.signup(formData); // This sends usertype="Dispatcher"
            onSignupSuccess(); // Usually redirects to login
        } catch (err: any) {
            setError(err.message || "Signup failed. Please try again.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ display: "flex", justifyContent: "center", alignItems: "center", minHeight: "100vh", background: S.navy, padding: 20 }}>
            <div style={{ background: S.card, padding: 40, borderRadius: 16, width: "100%", maxWidth: 450, boxShadow: "0 10px 25px rgba(0,0,0,0.2)" }}>
                <div style={{ textAlign: "center", marginBottom: 30 }}>
                    <h2 style={{ fontSize: 24, fontWeight: 800, color: S.navy, marginBottom: 8 }}>Create Account</h2>
                    <p style={{ color: S.textMuted, fontSize: 14 }}>Join as a Dispatcher</p>
                </div>

                {error && (
                    <div style={{ background: S.redBg, color: S.red, padding: "10px 14px", borderRadius: 8, fontSize: 13, marginBottom: 20, textAlign: "center" }}>
                        {error}
                    </div>
                )}

                <form onSubmit={handleSignup} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                        <div>
                            <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: S.textDim, marginBottom: 6 }}>Contact Name</label>
                            <input name="contact_name" value={formData.contact_name} onChange={handleChange} placeholder="John Doe" required style={inputStyle} />
                        </div>
                        <div>
                            <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: S.textDim, marginBottom: 6 }}>Business Name</label>
                            <input name="business_name" value={formData.business_name} onChange={handleChange} placeholder="Fast Dispatch" required style={inputStyle} />
                        </div>
                    </div>

                    <div>
                        <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: S.textDim, marginBottom: 6 }}>Phone Number</label>
                        <input name="phone" type="tel" value={formData.phone} onChange={handleChange} placeholder="+234..." required style={inputStyle} />
                    </div>

                    <div>
                        <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: S.textDim, marginBottom: 6 }}>Email Address</label>
                        <input name="email" type="email" value={formData.email} onChange={handleChange} placeholder="john@example.com" required style={inputStyle} />
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
                        <div>
                            <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: S.textDim, marginBottom: 6 }}>Password</label>
                            <input name="password" type="password" value={formData.password} onChange={handleChange} placeholder="******" required style={inputStyle} />
                        </div>
                        <div>
                            <label style={{ display: "block", fontSize: 12, fontWeight: 600, color: S.textDim, marginBottom: 6 }}>Confirm PW</label>
                            <input name="confirm_password" type="password" value={formData.confirm_password} onChange={handleChange} placeholder="******" required style={inputStyle} />
                        </div>
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
                        {loading ? "Creating Account..." : "Sign Up"}
                    </button>
                </form>

                <div style={{ marginTop: 24, textAlign: "center", fontSize: 13, color: S.textDim }}>
                    Already have an account? <span onClick={onSwitchToLogin} style={{ color: S.blue, fontWeight: 600, cursor: "pointer" }}>Login</span>
                </div>
            </div>
        </div>
    );
}

const inputStyle = { width: "100%", padding: "12px 14px", borderRadius: 10, border: `1px solid ${S.border}`, fontSize: 14, fontFamily: "inherit", outline: "none", boxSizing: "border-box" as const };
