// Calibrated kit 3.0 — Clerk appearance for Calibration Arena (calibrationarena.ai)
// Surfaces: no hard boxes. Rounded corners, hairline edges, lifted fills.
// No shadows, gradients or glow. Usage: <ClerkProvider appearance={calibratedAppearance}>
import type { ComponentProps } from "react";
import type { ClerkProvider } from "@clerk/react";

// @clerk/react v6 (Core 3) types; @clerk/types is not a dependency here.
type Appearance = NonNullable<ComponentProps<typeof ClerkProvider>["appearance"]>;

const t = {
  paper: "#F4F1E9", surface: "#FAF9F6", ink: "#464643",
  graphite: "#656460", steel: "#929698", leather: "#70543E",
  hairline: "#E2DFD8", // light steel/paper mix
};
const hair = `1px solid ${t.hairline}`;

export const calibratedAppearance: Appearance = {
  options: { // Core 3 name for the old `layout` key
    socialButtonsVariant: "blockButton", // full-width buttons WITH provider logos + label
    socialButtonsPlacement: "top",
  },
  variables: {
    colorPrimary: t.ink,
    colorBackground: t.surface,
    colorForeground: t.ink,
    colorMutedForeground: t.graphite,
    colorPrimaryForeground: t.paper,
    colorInput: t.paper,
    colorInputForeground: t.ink,
    colorNeutral: t.ink,
    colorDanger: t.leather,
    fontFamily: '"IBM Plex Sans", system-ui, sans-serif',
    fontFamilyButtons: '"IBM Plex Sans", system-ui, sans-serif',
    fontFamilyMono: '"IBM Plex Mono", monospace',
    colorBorder: t.hairline,
    colorShadow: "transparent",
    borderRadius: "12px",
  },
  elements: {
    cardBox: { borderRadius: "16px", border: hair, boxShadow: "none" },
    card: { borderRadius: "16px", backgroundColor: t.surface, boxShadow: "none", border: "none" },
    header: { textAlign: "center", alignItems: "center" },
    headerTitle: { fontFamily: '"Archivo Black", sans-serif', fontWeight: 400, color: t.ink, textAlign: "center" },
    headerSubtitle: { color: t.graphite, textAlign: "center" },
    socialButtonsBlockButton: {
      borderRadius: "12px", border: hair, boxShadow: "none",
      backgroundColor: t.surface, color: t.ink,
      "&:hover": { backgroundColor: t.paper },
    },
    // Provider logos are rendered by Clerk; keep them visible at full color.
    socialButtonsProviderIcon: { width: "18px", height: "18px", opacity: 1, filter: "none" },
    socialButtonsBlockButtonText: { fontWeight: 500 },
    dividerRow: { margin: "4px 0" },
    dividerLine: { backgroundColor: t.hairline },
    dividerText: { color: t.graphite, textTransform: "lowercase" }, // Clerk's default text is "or"
    formFieldLabel: { color: t.graphite, fontWeight: 500 },
    formFieldInput: {
      backgroundColor: t.paper, border: "1px solid transparent", borderRadius: "10px", boxShadow: "none",
      "&:focus": { borderColor: t.steel, boxShadow: "none" },
    },
    formButtonPrimary: {
      backgroundColor: t.ink, color: t.paper, borderRadius: "12px",
      boxShadow: "none", backgroundImage: "none", textTransform: "none",
      "&:hover": { backgroundColor: t.graphite },
    },
    footer: { background: t.surface, backgroundImage: "none", borderTop: hair, borderRadius: "0 0 16px 16px" },
    footerActionLink: { color: t.leather },
  },
};
export default calibratedAppearance;
