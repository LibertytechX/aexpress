export const S = {
  navy: "#1B2A4A", navyLight: "#243656", bg: "#f5f7fa", card: "#FFFFFF", border: "#e2e8f0", borderLight: "#f1f5f9",
  text: "#1B2A4A", textDim: "#64748b", textMuted: "#94a3b8",
  gold: "#E8A838", goldLight: "#F5C563", goldPale: "#FFF8EC",
  green: "#16a34a", greenBg: "#dcfce7",
  red: "#dc2626", redBg: "#fee2e2",
  blue: "#2563eb", blueBg: "#dbeafe",
  purple: "#8B5CF6", purpleBg: "rgba(139,92,246,0.08)",
  yellow: "#F59E0B", yellowBg: "rgba(245,158,11,0.08)",
  grayBg: "#f8fafc",
};

export const STS: Record<string, { bg: string; text: string }> = {
  Pending: { bg: S.yellowBg, text: S.yellow },
  Assigned: { bg: S.blueBg, text: S.blue },
  "Picked Up": { bg: S.purpleBg, text: S.purple },
  "In Transit": { bg: "rgba(232,168,56,0.1)", text: S.gold },
  Delivered: { bg: S.greenBg, text: S.green },
  Cancelled: { bg: S.redBg, text: S.red },
  Failed: { bg: S.redBg, text: "#F87171" }
};
