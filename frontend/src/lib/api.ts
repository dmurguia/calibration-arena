// In dev the Vite proxy forwards /api to the local backend, so paths stay
// relative. In hosted builds (Vercel), set VITE_API_URL to the backend origin
// (e.g. https://api.calibrationarena.ai or the Railway URL) and every request
// — fetches and document iframes alike — gets prefixed through apiUrl().
const RAW_API_BASE = ((import.meta.env.VITE_API_URL as string | undefined) ?? "").trim().replace(/\/+$/, "");
// A schemeless value ("foo.up.railway.app") would resolve as a relative path
// against the frontend origin — normalize it so the env var forgives that.
export const API_BASE =
  RAW_API_BASE && !/^https?:\/\//i.test(RAW_API_BASE) ? `https://${RAW_API_BASE}` : RAW_API_BASE;

export function apiUrl(path: string): string {
  return `${API_BASE}${path}`;
}
