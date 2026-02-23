import { STS } from "./theme";

export const Badge = ({ status }: { status: string }) => {
    const s = STS[status] || { bg: "#f1f5f9", text: "#94A3B8" };
    return <span style={{ fontSize: 10, fontWeight: 700, padding: "3px 10px", borderRadius: 6, background: s.bg, color: s.text, textTransform: "uppercase", letterSpacing: "0.5px" }}>{status}</span>;
};
