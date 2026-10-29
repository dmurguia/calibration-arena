import posthog from "posthog-js";

const posthogKey = import.meta.env.VITE_POSTHOG_KEY?.trim();
const posthogHost = import.meta.env.VITE_POSTHOG_HOST?.trim();

let posthogClient: typeof posthog | null = null;

if (!posthogKey || !posthogHost) {
  if (import.meta.env.DEV) {
    console.warn("PostHog disabled: set VITE_POSTHOG_KEY and VITE_POSTHOG_HOST to send analytics.");
  }
} else {
  posthogClient = posthog.init(posthogKey, {
    api_host: posthogHost,
    defaults: "2026-08-30",
    logs: {
      serviceName: "calibration-arena-frontend",
      environment: import.meta.env.MODE,
    },
    // Prompts, uploads and model answers can hold confidential client data, so replays never record text.
    session_recording: {
      maskAllInputs: true,
      maskTextSelector: "*",
    },
    capture_exceptions: {
      capture_unhandled_errors: true,
      capture_unhandled_rejections: true,
      capture_console_errors: false,
    },
  });
}

export default posthogClient;
