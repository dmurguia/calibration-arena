import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

// Vite only ships VITE_-prefixed variables to the browser. Clerk's dashboard
// hands out the key as NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY, which this app never
// reads, so a build with only that name silently falls back to password
// sign-in while the backend expects Clerk. Production builds on Vercel stop
// here instead of shipping that mismatch.
function checkClerkKey(mode: string) {
  // "." is the project root Vite builds from. Avoid process here: Vercel's fresh
  // install has no Node type definitions, so tsc -b rejects it.
  const env = loadEnv(mode, ".", "");
  const key = env.VITE_CLERK_PUBLISHABLE_KEY?.trim();
  const production = env.VERCEL_ENV === "production";
  const problems: string[] = [];
  if (!key && env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY) {
    problems.push(
      "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY is set, but this Vite app reads VITE_CLERK_PUBLISHABLE_KEY. Rename the variable.",
    );
  }
  if (!problems.length) return;
  const message = `[clerk] ${problems.join(" ")}`;
  if (production) throw new Error(message);
  console.warn(message);
}

export default defineConfig(({ mode }) => {
  checkClerkKey(mode);
  return {
    plugins: [react()],
    server: {
      port: 5173,
      proxy: {
        "/api": { target: "http://localhost:8000", changeOrigin: true },
      },
    },
  };
});
