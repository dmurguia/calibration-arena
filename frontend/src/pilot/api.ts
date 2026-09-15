import { apiUrl } from '../lib/api'

const KEY = 'calibrated_pilot_token'
export function token() { return localStorage.getItem(KEY) }
export function saveToken(value: string) { localStorage.setItem(KEY, value) }
export async function call<T>(path: string, body?: unknown, headers: Record<string, string> = {}): Promise<T> {
  const response = await fetch(apiUrl(`/api/pilot${path}`), {
    method: body === undefined ? 'GET' : 'POST',
    headers: { 'Content-Type': 'application/json', ...(token() ? { Authorization: `Bearer ${token()}` } : {}), ...headers },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  })
  if (!response.ok) {
    let message = 'Could not save your work. Please try again.'
    try { const data = await response.json(); message = typeof data.detail === 'string' ? data.detail : data.detail?.[0]?.msg ?? message } catch { /* safe fallback */ }
    throw new Error(message)
  }
  return response.json()
}
export interface Case { task_type: string; id: string; title: string; topic: string; minutes: number; brief: string }
export interface Participant { identity?: string; id: string; name: string; role: string; experience: string; framework: string; email?: string; followup: boolean }
export interface Draft { position: string; text: string; author?: string; model_id?: string; origin?: string; review_note?: string; checks?: { label: string; passed: boolean }[] }
export interface Judgment { a: string | null; b: string | null; preference: string; reasons: string[]; confidence: string | null; rationale: string; correction: string; decision_ms?: number }
export interface Run { task_type: string; source_run_id?: string; source_position?: string; retry_of_run_id?: string; source_example_id?: string; history?: { role: string; content: string }[]; turn_number?: number; evaluation_scope?: string; id: string; status: string; created_at: string; kind: string; case_id?: string; title: string; brief: string; conclusion?: string; mode: string; version: string; drafts: Draft[]; expected?: string; takeaway?: string; validation?: string; judgment?: Judgment; feedback?: { usefulness: string; note: string } }
export interface Me { participant: Participant; runs: Run[] }
export interface Config { inference_backend?: string; ask_mode: 'live' | 'fixture'; invite_required: boolean; prompt_starters: { id: string; title: string; brief: string; version: string }[]; task_types: { id: string; label: string; placeholder: string }[] }
export interface CaseAssignment { id: string; pack_id: string; case_id: string; version: string; title: string; brief: string; framework: string; evidence: unknown[]; ordinal: number; run_id: string | null; status: string; exposure: string }
