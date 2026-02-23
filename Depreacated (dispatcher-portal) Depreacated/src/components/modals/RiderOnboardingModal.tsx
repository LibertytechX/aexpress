import { useState } from "react";
import { RiderService } from "../../services/riderService";
import { S } from "../common/theme";
import { I } from "../icons";

interface RiderOnboardingModalProps {
    onClose: () => void;
    onSuccess: () => void;
}

export function RiderOnboardingModal({ onClose, onSuccess }: RiderOnboardingModalProps) {
    const [step, setStep] = useState(1);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Form States
    const [formData, setFormData] = useState({
        email: "",
        phone: "",
        first_name: "",
        last_name: "",
        bank_name: "",
        bank_account_number: "",
        bank_routing_code: "",
        vehicle_model: "",
        vehicle_plate_number: "",
        vehicle_color: "",
        working_type: "freelancer",
        city: "",
        address: "",
        driving_license_number: "",
        national_id: "",
    });

    const [files, setFiles] = useState<{ [key: string]: File | null }>({
        avatar: null,
        vehicle_photo: null,
        driving_license_photo: null,
        identity_card_photo: null,
    });

    const [filePreviews, setFilePreviews] = useState<{ [key: string]: string }>({
        avatar: "",
        vehicle_photo: "",
        driving_license_photo: "",
        identity_card_photo: "",
    });

    const iSt = { width: "100%", border: `1.5px solid ${S.border}`, borderRadius: 10, padding: "0 14px", height: 42, fontSize: 13, fontFamily: "inherit", color: S.navy, background: "#fff", outline: "none" };
    const lSt = { display: "block", fontSize: 11, fontWeight: 600, color: S.textMuted, marginBottom: 5, textTransform: "uppercase", letterSpacing: "0.5px" };

    const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value } = e.target;
        setFormData(prev => ({ ...prev, [name]: value }));
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>, field: string) => {
        if (e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            setFiles(prev => ({ ...prev, [field]: file }));
            setFilePreviews(prev => ({ ...prev, [field]: URL.createObjectURL(file) }));
        }
    };

    const handleSubmit = async () => {
        setLoading(true);
        setError(null);
        try {
            const formDataToSend = new FormData();

            // 1. Append all text fields
            Object.entries(formData).forEach(([key, value]) => {
                formDataToSend.append(key, value);
            });

            // 2. Append all files
            Object.entries(files).forEach(([key, file]) => {
                if (file) {
                    formDataToSend.append(key, file);
                }
            });

            const result = await RiderService.onboardRider(formDataToSend);
            // Backend returns {message: "...", rider_id: "..."} on success (201)
            // If we get here without throwing, it means success
            if (result.rider_id || result.message?.includes("successfully")) {
                setLoading(false);
                onSuccess();
            } else if (result.success === false) {
                setError(result.message || "Onboarding failed");
                setLoading(false);
            } else {
                // Fallback: treat as success if we got a response
                setLoading(false);
                onSuccess();
            }
        } catch (err: any) {
            console.error(err);
            // Handle DRF dictionary errors
            if (typeof err === "object" && !err.message) {
                const errorMessages = Object.entries(err)
                    .map(([field, msgs]) => `${field}: ${Array.isArray(msgs) ? msgs.join(", ") : msgs}`)
                    .join(" | ");
                setError(errorMessages || "Something went wrong during onboarding.");
            } else {
                setError(err.message || "Something went wrong during onboarding.");
            }
            setLoading(false);
        }
    };

    const renderStep = () => {
        switch (step) {
            case 1:
                return (
                    <div>
                        <div style={{ marginBottom: 16 }}>
                            <label style={lSt}>Full Name</label>
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                                <input name="first_name" placeholder="First Name" style={iSt} value={formData.first_name} onChange={handleInputChange} />
                                <input name="last_name" placeholder="Last Name" style={iSt} value={formData.last_name} onChange={handleInputChange} />
                            </div>
                        </div>
                        <div style={{ marginBottom: 16 }}>
                            <label style={lSt}>Contact Info</label>
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                                <input name="email" type="email" placeholder="Email Address" style={iSt} value={formData.email} onChange={handleInputChange} />
                                <input name="phone" placeholder="Phone Number" style={iSt} value={formData.phone} onChange={handleInputChange} />
                            </div>
                        </div>
                        <div style={{ marginBottom: 16 }}>
                            <label style={lSt}>Banking Details</label>
                            <input name="bank_name" placeholder="Bank Name" style={{ ...iSt, marginBottom: 10 }} value={formData.bank_name} onChange={handleInputChange} />
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                                <input name="bank_account_number" placeholder="Account Number" style={iSt} value={formData.bank_account_number} onChange={handleInputChange} />
                                <input name="bank_routing_code" placeholder="Routing Code" style={iSt} value={formData.bank_routing_code} onChange={handleInputChange} />
                            </div>
                        </div>
                        <div style={{ marginBottom: 16 }}>
                            <label style={lSt}>Profile Photo</label>
                            <div style={{ display: "flex", alignItems: "center", gap: 15 }}>
                                <div style={{ width: 60, height: 60, borderRadius: 12, background: S.borderLight, display: "flex", alignItems: "center", justifyContent: "center", overflow: "hidden", border: `1px solid ${S.border}` }}>
                                    {filePreviews.avatar ? <img src={filePreviews.avatar} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : <span style={{ fontSize: 20 }}>👤</span>}
                                </div>
                                <input type="file" onChange={(e) => handleFileChange(e, "avatar")} style={{ fontSize: 12 }} />
                            </div>
                        </div>
                    </div>
                );
            case 2:
                return (
                    <div>
                        <div style={{ marginBottom: 16 }}>
                            <label style={lSt}>Vehicle Details</label>
                            <input name="vehicle_model" placeholder="Vehicle Model (e.g. Honda CG125)" style={{ ...iSt, marginBottom: 10 }} value={formData.vehicle_model} onChange={handleInputChange} />
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                                <input name="vehicle_plate_number" placeholder="Plate Number" style={iSt} value={formData.vehicle_plate_number} onChange={handleInputChange} />
                                <input name="vehicle_color" placeholder="Color" style={iSt} value={formData.vehicle_color} onChange={handleInputChange} />
                            </div>
                        </div>
                        <div style={{ marginBottom: 16 }}>
                            <label style={lSt}>Location & Type</label>
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 10 }}>
                                <input name="city" placeholder="City" style={iSt} value={formData.city} onChange={handleInputChange} />
                                <select name="working_type" style={iSt} value={formData.working_type} onChange={handleInputChange}>
                                    <option value="freelancer">Freelancer</option>
                                    <option value="full_time">Full Time</option>
                                </select>
                            </div>
                            <input name="address" placeholder="Full Address" style={iSt} value={formData.address} onChange={handleInputChange} />
                        </div>
                        <div style={{ marginBottom: 16 }}>
                            <label style={lSt}>Vehicle Photo</label>
                            <div style={{ display: "flex", alignItems: "center", gap: 15 }}>
                                <div style={{ width: 60, height: 60, borderRadius: 12, background: S.borderLight, display: "flex", alignItems: "center", justifyContent: "center", overflow: "hidden", border: `1px solid ${S.border}` }}>
                                    {filePreviews.vehicle_photo ? <img src={filePreviews.vehicle_photo} style={{ width: "100%", height: "100%", objectFit: "cover" }} /> : <span style={{ fontSize: 20 }}>🏍️</span>}
                                </div>
                                <input type="file" onChange={(e) => handleFileChange(e, "vehicle_photo")} style={{ fontSize: 12 }} />
                            </div>
                        </div>
                    </div>
                );
            case 3:
                return (
                    <div>
                        <div style={{ marginBottom: 16 }}>
                            <label style={lSt}>Identity Documents</label>
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10, marginBottom: 10 }}>
                                <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                                    <input name="driving_license_number" placeholder="License Number" style={iSt} value={formData.driving_license_number} onChange={handleInputChange} />
                                    <div style={{ fontSize: 9, color: S.textMuted }}>DRIVER'S LICENSE PHOTO</div>
                                    <input type="file" onChange={(e) => handleFileChange(e, "driving_license_photo")} style={{ fontSize: 11 }} />
                                    {filePreviews.driving_license_photo && <img src={filePreviews.driving_license_photo} style={{ width: 100, height: 60, borderRadius: 6, objectFit: "cover", marginTop: 5 }} />}
                                </div>
                                <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                                    <input name="national_id" placeholder="National ID (NIN/Voter)" style={iSt} value={formData.national_id} onChange={handleInputChange} />
                                    <div style={{ fontSize: 9, color: S.textMuted }}>IDENTITY CARD PHOTO</div>
                                    <input type="file" onChange={(e) => handleFileChange(e, "identity_card_photo")} style={{ fontSize: 11 }} />
                                    {filePreviews.identity_card_photo && <img src={filePreviews.identity_card_photo} style={{ width: 100, height: 60, borderRadius: 6, objectFit: "cover", marginTop: 5 }} />}
                                </div>
                            </div>
                        </div>
                        {error && <div style={{ padding: 10, background: S.redBg, color: S.red, borderRadius: 8, fontSize: 12, marginBottom: 16, border: `1px solid ${S.red}` }}>{error}</div>}
                    </div>
                );
            default:
                return null;
        }
    };

    return (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1001 }} onClick={onClose}>
            <div onClick={e => e.stopPropagation()} style={{ background: S.card, borderRadius: 20, border: `1px solid ${S.border}`, width: 500, boxShadow: "0 24px 64px rgba(0,0,0,0.25)", overflow: "hidden" }}>
                <div style={{ padding: "20px 24px", background: S.navy, color: "#fff", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                        <h2 style={{ fontSize: 18, fontWeight: 800, margin: 0 }}>Driver Onboarding</h2>
                        <div style={{ display: "flex", gap: 8, marginTop: 8 }}>
                            {[1, 2, 3].map(s => (
                                <div key={s} style={{ width: 30, height: 4, borderRadius: 2, background: step >= s ? S.gold : "rgba(255,255,255,0.2)" }} />
                            ))}
                        </div>
                    </div>
                    <button onClick={onClose} style={{ background: "rgba(255,255,255,0.1)", border: "none", cursor: "pointer", color: "#fff", width: 32, height: 32, borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center" }}>{I.x}</button>
                </div>

                <div style={{ padding: 24, maxHeight: "70vh", overflowY: "auto" }}>
                    {renderStep()}
                </div>

                <div style={{ padding: "16px 24px", borderTop: `1px solid ${S.border}`, background: S.borderLight, display: "flex", gap: 12 }}>
                    {step > 1 && (
                        <button onClick={() => setStep(step - 1)} disabled={loading} style={{ flex: 1, padding: "12px 0", borderRadius: 12, border: `1.5px solid ${S.border}`, background: "#fff", color: S.navy, fontWeight: 700, fontSize: 13, cursor: "pointer" }}>Back</button>
                    )}
                    {step < 3 ? (
                        <button onClick={() => setStep(step + 1)} style={{ flex: 2, padding: "12px 0", borderRadius: 12, border: "none", background: S.navy, color: "#fff", fontWeight: 700, fontSize: 13, cursor: "pointer" }}>Continue</button>
                    ) : (
                        <button onClick={handleSubmit} disabled={loading} style={{ flex: 2, padding: "12px 0", borderRadius: 12, border: "none", background: `linear-gradient(135deg, ${S.gold}, ${S.goldLight})`, color: S.navy, fontWeight: 800, fontSize: 14, cursor: "pointer", opacity: loading ? 0.7 : 1 }}>
                            {loading ? "Processing..." : "Finish Onboarding"}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}
