import { S } from "./theme";

interface StatCardProps {
    label: string;
    value: string | number;
    sub?: string;
    color?: string;
}

export const StatCard = ({ label, value, sub, color }: StatCardProps) => (
    <div style={{ background: S.card, borderRadius: 14, border: `1px solid ${S.border}`, padding: "16px 18px", flex: 1 }}>
        <div style={{ fontSize: 11, color: S.textMuted, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 6 }}>{label}</div>
        <div style={{ fontSize: 24, fontWeight: 800, color: color || S.text, fontFamily: "'Space Mono', monospace", lineHeight: 1 }}>{value}</div>
        {sub && <div style={{ fontSize: 11, color: S.textMuted, marginTop: 4 }}>{sub}</div>}
    </div>
);
