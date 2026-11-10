import { apiUrl } from '../lib/api'

const KEY = 'calibrated_pilot_token'
export function token() { return localStorage.getItem(KEY) }
export function setToken(value: string) { localStorage.setItem(KEY, value) }
export function saveToken(value: string) { setToken(value) }
export function clearToken() { localStorage.removeItem(KEY) }
export async function call<T>(path: string, body?: unknown, headers: Record<string, string> = {}, authToken?: string | null): Promise<T> {
  const authorization = authToken === undefined ? token() : authToken
  const response = await fetch(apiUrl(`/api/pilot${path}`), {
    method: body === undefined ? 'GET' : 'POST',
    headers: { 'Content-Type': 'application/json', ...(authorization ? { Authorization: `Bearer ${authorization}` } : {}), ...headers },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  })
  if (response.status === 401 && path === '/me') clearToken()
  if (!response.ok) {
    let message = 'Could not save your work. Please try again.'
    try { const data = await response.json(); message = typeof data.detail === 'string' ? data.detail : data.detail?.[0]?.msg ?? message } catch { /* safe fallback */ }
    throw new Error(message)
  }
  return response.json()
}
export interface Case { task_type: string; id: string; title: string; topic: string; minutes: number; brief: string }
export interface Participant { identity?: string; id: string; name: string; role: string; experience: string; framework: string }
export interface Artifact { id: string; kind: 'journal-entry' | 'schedule' | 'reconciliation' | 'invoice' | 'memo' | 'table' | 'workpaper'; title: string; format: 'markdown'; content: string; source?: string }
export interface Draft { position: string; text: string; truncated?: boolean; narrative?: string; artifacts?: Artifact[]; author?: string; model_id?: string; origin?: string; review_note?: string; checks?: { label: string; passed: boolean }[] }
export interface Judgment { a: string | null; b: string | null; preference: string; reasons: string[]; confidence: string | null; rationale: string; correction: string; decision_ms?: number }
export interface Run { archived?: boolean; failures?: { side: string; error: string }[]; limit_rejection?: string; workflow_id?: string | null; category?: string | null; topic?: string | null; attachments?: { name: string; role: string; size: number; sha256: string }[]; identity_exposed?: boolean; conversation?: { position: string; messages: { role: string; content: string }[] }[]; task_type: string; source_run_id?: string; source_position?: string; retry_of_run_id?: string; source_example_id?: string; root_run_id?: string; history?: { role: string; content: string }[]; turn_number?: number; evaluation_scope?: string; id: string; status: string; created_at: string; kind: string; case_id?: string; title: string; brief: string; conclusion?: string; mode: string; version: string; drafts: Draft[]; expected?: string; takeaway?: string; validation?: string; judgment?: Judgment; feedback?: { usefulness: string; note: string } }
export interface Me { participant: Participant; runs: Run[]; account?: { email: string; provider?: 'clerk' | 'password' } | null; usage?: { used: number; budget: number; remaining: number } }
export interface Config { inference_backend?: string; generation_paused?: boolean; ask_mode: 'live' | 'fixture'; invite_required: boolean; accounts_enabled?: boolean; auth_provider?: 'clerk' | 'password'; leaderboard_public?: boolean; models?: string[]; prompt_starters: { id: string; title: string; brief: string; version: string }[]; task_types: { id: string; label: string; placeholder: string }[] }
export interface CaseAssignment { id: string; pack_id: string; case_id: string; version: string; title: string; brief: string; framework: string; evidence: unknown[]; ordinal: number; run_id: string | null; status: string; exposure: string }

// Live view of a comparison while both models write. Display only: the POST /runs
// response is still what the person votes on, and every failure here falls back
// to waiting for it. Events name a side (a or b) and never a model.
export interface PanelStream { thinking: string; answer: string; state: 'working' | 'complete' | 'stopped'; hidden: boolean }
export interface PairStream { a: PanelStream; b: PanelStream }
const emptyPanel = (): PanelStream => ({ thinking: '', answer: '', state: 'working', hidden: false })

async function followStream(streamId: string, signal: AbortSignal, onStream: (stream: PairStream) => void) {
  const authorization = token()
  const response = await fetch(apiUrl(`/api/pilot/runs/stream/${streamId}`), { headers: authorization ? { Authorization: `Bearer ${authorization}` } : {}, signal })
  if (!response.ok || !response.body) return
  const pair: PairStream = { a: emptyPanel(), b: emptyPanel() }
  let dirty = false
  // Markdown re-renders on every update, so paint at most ten times a second.
  const timer = setInterval(() => { if (dirty) { dirty = false; onStream({ a: { ...pair.a }, b: { ...pair.b } }) } }, 100)
  const reader = response.body.getReader(); const decoder = new TextDecoder(); let buffer = ''
  try {
    for (;;) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      let cut: number
      while ((cut = buffer.indexOf('\n\n')) >= 0) {
        const block = buffer.slice(0, cut); buffer = buffer.slice(cut + 2)
        const data = block.split('\n').filter(line => line.startsWith('data:')).map(line => line.slice(5).trimStart()).join('\n')
        if (!data) continue
        let event: { type?: string; position?: string; text?: string; state?: string }
        try { event = JSON.parse(data) } catch { continue }
        const panel = event.position === 'a' ? pair.a : event.position === 'b' ? pair.b : null
        if (!panel) continue
        if (event.type === 'thinking' || event.type === 'answer') panel[event.type] += event.text ?? ''
        else if (event.type === 'withheld') { panel.hidden = true; panel.thinking = ''; panel.answer = '' }
        else if (event.type === 'state' && (event.state === 'complete' || event.state === 'stopped')) panel.state = event.state
        dirty = true
      }
    }
  } finally { clearInterval(timer) }
}

export async function callStreamed<T>(path: string, body: Record<string, unknown>, onStream: (stream: PairStream | null) => void): Promise<T> {
  const bytes = new Uint8Array(16); crypto.getRandomValues(bytes)
  const streamId = Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('')
  const abort = new AbortController()
  followStream(streamId, abort.signal, onStream).catch(() => { /* the answer still arrives with the response below */ })
  try { return await call<T>(path, { ...body, stream_id: streamId }) } finally { abort.abort(); onStream(null) }
}
