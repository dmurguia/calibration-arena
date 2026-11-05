// All demo data is fictional: claims, VINs, TSB numbers, labor ops and people are invented for the walkthrough.

export const COMPANY = {
  name: 'Ford Motor Company',
  domain: 'ford.com',
  workspace: 'Ford · Global Warranty Operations',
  plan: 'Enterprise trial',
}

export const DEMO_USER = {
  name: 'Maya Patel',
  email: 'maya.patel@ford.com',
  title: 'Sr. Engineer, Warranty Analytics',
  initials: 'MP',
}

export const AGENT = {
  name: 'warranty-triage-agent',
  display: 'Warranty Claims Triage',
  harness: 'Claude Agent SDK',
  model: 'claude-sonnet-4.6',
  description:
    'Reviews dealer warranty claims, checks coverage, TSBs and labor-time allowances, then approves, adjusts, requests info or escalates to a human analyst.',
  claimsPerDay: 18400,
}

export interface Template {
  id: string
  title: string
  blurb: string
  who: string
  tools: number
  icon: 'clipboard' | 'wrench' | 'file' | 'factory'
}

export const TEMPLATES: Template[] = [
  { id: 'warranty', title: 'Warranty claim triage', blurb: 'Approve, adjust or escalate dealer claims against coverage, TSBs and labor-time guides.', who: 'Warranty Ops', tools: 7, icon: 'clipboard' },
  { id: 'diag', title: 'Dealer diagnostic copilot', blurb: 'Walk technicians from DTCs and symptoms to a confirmed root cause and repair.', who: 'Service Engineering', tools: 9, icon: 'wrench' },
  { id: 'ppap', title: 'Supplier PPAP review', blurb: 'Check supplier submissions against APQP requirements and flag missing elements.', who: 'Supplier Quality', tools: 5, icon: 'file' },
  { id: 'ecr', title: 'Engineering change request drafting', blurb: 'Draft ECRs from field data with impact analysis across BOM and plants.', who: 'Product Development', tools: 6, icon: 'factory' },
]

export const HARNESSES = [
  { id: 'claude', name: 'Claude Agent SDK', detail: 'Anthropic · Python / TS' },
  { id: 'codex', name: 'OpenAI Agents SDK / Codex', detail: 'OpenAI · Python / TS' },
  { id: 'langgraph', name: 'LangGraph', detail: 'LangChain · Python' },
  { id: 'http', name: 'Any OpenAI-compatible client', detail: 'Change base_url only' },
]

export interface FailureCluster {
  id: string
  label: string
  share: number
  impact: string
  example: string
  severity: 'high' | 'medium' | 'low'
}

export const FAILURE_CLUSTERS: FailureCluster[] = [
  { id: 'labor', label: 'Labor op / time doesn’t match the applicable TSB', share: 0.21, impact: '$412k / yr overpaid labor', example: 'Approved 9.8 h on 12-6500-A when TSB 26-2141 specifies 12-6500-B at 8.4 h', severity: 'high' },
  { id: 'escalate', label: 'Escalates claims a human analyst would approve', share: 0.18, impact: '2,900 analyst hours / yr', example: 'Escalated a routine brake-pad claim at 18k mi because the RO narrative was short', severity: 'medium' },
  { id: 'tsb', label: 'Misses an applicable TSB or Field Service Action', share: 0.14, impact: 'Repeat repairs, CSAT', example: 'Didn’t search TSBs for P0016 on a 3.5L EcoBoost', severity: 'high' },
  { id: 'coverage', label: 'Approves outside coverage (time, mileage, commercial use)', share: 0.07, impact: '$1.1M / yr leakage', example: 'Approved powertrain claim at 63,410 mi on a 5yr/60k warranty', severity: 'high' },
  { id: 'parts', label: 'Invents part numbers in the dealer note', share: 0.04, impact: 'Dealer rework, audit risk', example: 'Cited part “ML3Z-6C524-ZZ” which does not exist in the catalog', severity: 'medium' },
]

export interface Trace {
  id: string
  claim: string
  vehicle: string
  concern: string
  decision: 'Approved' | 'Adjusted' | 'Escalated' | 'Rejected' | 'Info requested'
  cluster?: string
  latency: number
  cost: number
  ageMin: number
  flagged?: boolean
}

export const TRACES: Trace[] = [
  { id: 'tr_8f21', claim: 'WC-26-0418837', vehicle: '2024 F-150 3.5L EcoBoost', concern: 'Rattle on cold start, P0016', decision: 'Approved', cluster: 'labor', latency: 41, cost: 0.47, ageMin: 2, flagged: true },
  { id: 'tr_8f1c', claim: 'WC-26-0418829', vehicle: '2025 Bronco 2.7L', concern: 'Water leak at hard-top seam', decision: 'Approved', latency: 33, cost: 0.38, ageMin: 3 },
  { id: 'tr_8f0a', claim: 'WC-26-0418811', vehicle: '2023 Explorer 3.0L Hybrid', concern: 'HV battery coolant pump noise', decision: 'Escalated', cluster: 'escalate', latency: 52, cost: 0.61, ageMin: 5, flagged: true },
  { id: 'tr_8ef9', claim: 'WC-26-0418790', vehicle: '2024 Mustang Mach-E', concern: 'Charge port door inoperative', decision: 'Approved', latency: 29, cost: 0.31, ageMin: 6 },
  { id: 'tr_8ee2', claim: 'WC-26-0418774', vehicle: '2021 F-250 6.7L Power Stroke', concern: 'Turbo actuator, P0299 underboost', decision: 'Approved', cluster: 'coverage', latency: 47, cost: 0.55, ageMin: 8, flagged: true },
  { id: 'tr_8ed0', claim: 'WC-26-0418769', vehicle: '2025 Maverick 2.5L Hybrid', concern: 'Infotainment reboots while driving', decision: 'Info requested', latency: 36, cost: 0.4, ageMin: 9 },
  { id: 'tr_8ec4', claim: 'WC-26-0418752', vehicle: '2024 Escape 1.5L', concern: 'Coolant loss, no visible leak', decision: 'Approved', cluster: 'tsb', latency: 39, cost: 0.44, ageMin: 11, flagged: true },
  { id: 'tr_8eb1', claim: 'WC-26-0418740', vehicle: '2025 F-150 Lightning', concern: 'Pro Power Onboard outlet dead', decision: 'Adjusted', latency: 44, cost: 0.5, ageMin: 12 },
  { id: 'tr_8ea7', claim: 'WC-26-0418733', vehicle: '2024 Ranger 2.3L', concern: 'Front brake pads worn at 18k mi', decision: 'Escalated', cluster: 'escalate', latency: 31, cost: 0.35, ageMin: 14, flagged: true },
  { id: 'tr_8e93', claim: 'WC-26-0418719', vehicle: '2023 Edge 2.0L', concern: 'A/C blows warm, low refrigerant', decision: 'Approved', cluster: 'parts', latency: 37, cost: 0.42, ageMin: 15, flagged: true },
  { id: 'tr_8e80', claim: 'WC-26-0418702', vehicle: '2025 Expedition 3.5L', concern: '10R80 harsh 2-3 upshift', decision: 'Approved', latency: 45, cost: 0.52, ageMin: 17 },
  { id: 'tr_8e6b', claim: 'WC-26-0418688', vehicle: '2022 Transit 3.5L', concern: 'Sliding door latch failure', decision: 'Rejected', latency: 28, cost: 0.3, ageMin: 19 },
]

export interface TraceStep {
  kind: 'input' | 'tool' | 'thought' | 'output'
  title: string
  body: string
  verdict?: 'ok' | 'bad' | 'warn'
}

/** The hero claim used in trace viewer, environment preview and before/after comparison. */
export const HERO_CLAIM = {
  id: 'WC-26-0418837',
  vin: '1FTFW1E8XRF•••••• (hashed)',
  vehicle: '2024 F-150 XLT 3.5L EcoBoost',
  mileage: '41,212 mi',
  inService: 'Mar 11, 2024',
  dealer: 'Dealer P&A code 07421 · Dearborn, MI',
  concern: 'Customer states engine rattles for 2–3 seconds on cold start.',
  cause: 'Verified concern. DTC P0016 stored. Found LH and RH cam phasers worn.',
  correction: 'Replaced LH/RH cam phasers and timing chain kit. Cleared codes, road tested OK.',
  laborOp: '12-6500-A · 9.8 h',
  parts: 'ML3Z-6C524-B (phaser kit) ×1, ML3Z-6268-A (chain) ×1',
}

export const BASELINE_STEPS: TraceStep[] = [
  { kind: 'input', title: 'Dealer claim received', body: `${HERO_CLAIM.vehicle} · ${HERO_CLAIM.mileage} · ${HERO_CLAIM.laborOp}` },
  { kind: 'tool', title: 'coverage_lookup(vin)', body: 'Powertrain 5yr/60k — in coverage (2.6 yr, 41,212 mi)', verdict: 'ok' },
  { kind: 'tool', title: 'parts_catalog(“ML3Z-6C524-B”)', body: 'Valid · Cam phaser kit, 3.5L GTDI', verdict: 'ok' },
  { kind: 'thought', title: 'Reasoning', body: 'Coverage is valid and parts are valid. Labor looks reasonable for a timing job. Approve as submitted.', verdict: 'bad' },
  { kind: 'output', title: 'Decision: APPROVE as submitted', body: 'Paid 9.8 h on 12-6500-A. No TSB cited. No PCM reflash requested.', verdict: 'bad' },
]

export const TRAINED_STEPS: TraceStep[] = [
  { kind: 'input', title: 'Dealer claim received', body: `${HERO_CLAIM.vehicle} · ${HERO_CLAIM.mileage} · ${HERO_CLAIM.laborOp}` },
  { kind: 'tool', title: 'coverage_lookup(vin)', body: 'Powertrain 5yr/60k — in coverage (2.6 yr, 41,212 mi)', verdict: 'ok' },
  { kind: 'tool', title: 'tsb_search(dtc=“P0016”, engine=“3.5L GTDI”)', body: 'TSB 26-2141 · Cold-start rattle — cam phaser replacement. Labor op 12-6500-B, 8.4 h. Requires PCM reflash.', verdict: 'ok' },
  { kind: 'tool', title: 'labor_time_guide(“12-6500-B”)', body: 'Allowance 8.4 h incl. timing chain. 12-6500-A is the non-TSB op (9.8 h).', verdict: 'ok' },
  { kind: 'tool', title: 'claim_history(vin)', body: 'No prior PCM reflash on record for this VIN.', verdict: 'warn' },
  { kind: 'thought', title: 'Reasoning', body: 'Repair matches TSB 26-2141, so the TSB labor op applies. Adjust labor to 8.4 h and require the reflash before payment.', verdict: 'ok' },
  { kind: 'output', title: 'Decision: APPROVE with adjustment', body: 'Pay 8.4 h on 12-6500-B per TSB 26-2141 (−1.4 h). Dealer note asks for PCM reflash confirmation in the RO.', verdict: 'ok' },
]

export const ENV_TOOLS = [
  { name: 'vin_decode', desc: 'Model, engine, build plant, build date', source: 'Mocked from vehicle-master API (OpenAPI)' },
  { name: 'coverage_lookup', desc: 'Warranty coverages, time & mileage remaining, commercial use', source: 'Mocked from warranty-api.yaml' },
  { name: 'tsb_search', desc: 'TSBs, SSMs and Field Service Actions by DTC / symptom / engine', source: 'Snapshot of 4,812 bulletins (2019–2026)' },
  { name: 'labor_time_guide', desc: 'Labor operation codes and time allowances', source: 'Snapshot of labor-time guide v26.3' },
  { name: 'parts_catalog', desc: 'Validates part numbers and supersessions', source: 'Snapshot of 212k part numbers' },
  { name: 'claim_history', desc: 'Prior repairs and claims on the VIN', source: 'Synthetic, generated per task' },
  { name: 'submit_decision', desc: 'Terminal action: approve / adjust / request info / escalate / reject', source: 'Ends the episode → graded' },
]

export interface RewardTerm {
  id: string
  label: string
  kind: 'check' | 'rubric' | 'penalty'
  weight: number
  how: string
}

export const REWARD_TERMS: RewardTerm[] = [
  { id: 'decision', label: 'Correct decision (approve / adjust / escalate / reject)', kind: 'check', weight: 0.35, how: 'Exact match vs expert answer key' },
  { id: 'labor', label: 'Labor op and hours within allowance', kind: 'check', weight: 0.2, how: 'Compared to labor_time_guide + TSB' },
  { id: 'tsb', label: 'Cites the applicable TSB / FSA', kind: 'check', weight: 0.15, how: 'Set match vs expert-listed bulletins' },
  { id: 'note', label: 'Dealer note is clear, actionable, policy-grounded', kind: 'rubric', weight: 0.2, how: 'Expert-calibrated judge, per-task rubric' },
  { id: 'efficiency', label: 'Efficient tool use (≤ 8 calls, no loops)', kind: 'check', weight: 0.1, how: 'Trajectory length' },
  { id: 'leak', label: 'Approves an out-of-coverage claim', kind: 'penalty', weight: -1.0, how: 'Hard penalty — episode reward floored' },
  { id: 'halluc', label: 'Mentions a part number not in the catalog', kind: 'penalty', weight: -0.5, how: 'Regex + parts_catalog lookup' },
]

export interface Expert {
  id: string
  name: string
  role: string
  years: number
  creds: string
  rate: number
  rating: number
  tasksDone: number
  available: string
  focus: string[]
  internal?: boolean
}

export const EXPERTS: Expert[] = [
  { id: 'e1', name: 'Ray Delgado', role: 'Master Technician (ASE L1, Ford Senior Master)', years: 22, creds: 'ASE A1–A8, L1 · Ford Senior Master', rate: 105, rating: 4.9, tasksDone: 1840, available: 'Today', focus: ['EcoBoost', 'Diagnostics', 'Labor ops'] },
  { id: 'e2', name: 'Denise Okafor', role: 'Dealer Warranty Administrator', years: 14, creds: 'Warranty admin, 3 Ford dealers', rate: 85, rating: 4.8, tasksDone: 2310, available: 'Today', focus: ['Claim policy', 'Coverage', 'Dealer notes'] },
  { id: 'e3', name: 'Tom Kowalski', role: 'Former OEM Warranty Analyst', years: 11, creds: 'Ex-Tier-1 OEM field quality', rate: 110, rating: 4.9, tasksDone: 960, available: 'Tomorrow', focus: ['Leakage', 'Audit', 'FSAs'] },
  { id: 'e4', name: 'Priya Raman', role: 'EV High-Voltage Technician', years: 8, creds: 'EV HV certified, Mach-E / Lightning', rate: 100, rating: 4.7, tasksDone: 640, available: 'Today', focus: ['HV battery', 'Charging', 'EV TSBs'] },
  { id: 'e5', name: 'Luis Herrera', role: 'Diesel Specialist (6.7L Power Stroke)', years: 17, creds: 'Diesel master, Super Duty', rate: 95, rating: 4.8, tasksDone: 1120, available: 'In 2 days', focus: ['Diesel', 'Turbo', 'Emissions'] },
  { id: 'e6', name: 'Your warranty analysts', role: 'Invite internal SMEs (no charge)', years: 0, creds: 'Ford Global Warranty Ops', rate: 0, rating: 0, tasksDone: 0, available: 'Invite', focus: ['Policy', 'Final say on rubric'], internal: true },
]

export const DATA_JOBS = [
  { id: 'tasks', label: 'Author hard tasks', desc: 'Experts write new claims from real failure modes, with the answer key', unit: 'task', perHour: 3, default: 300 },
  { id: 'demos', label: 'Expert demonstrations', desc: 'Experts solve tasks step by step with the same tools (used for warm-start)', unit: 'demo', perHour: 4, default: 200 },
  { id: 'labels', label: 'Grade agent attempts', desc: 'Pairwise + rubric grades that calibrate the automatic grader', unit: 'label', perHour: 20, default: 1200 },
  { id: 'redteam', label: 'Red-team the grader', desc: 'Try to get a high score with a wrong answer; patches reward hacks', unit: 'probe', perHour: 6, default: 60 },
]

export interface ModelInfo {
  id: string
  name: string
  vendor: string
  kind: 'frontier' | 'open'
  trainable: boolean
  score: number
  leak: number
  costPerClaim: number
  p50: number
  current?: boolean
}

export const MODELS: ModelInfo[] = [
  { id: 'claude', name: 'Claude Sonnet 4.6', vendor: 'Anthropic', kind: 'frontier', trainable: false, score: 0.612, leak: 0.068, costPerClaim: 0.42, p50: 38, current: true },
  { id: 'gpt', name: 'GPT-5.5', vendor: 'OpenAI', kind: 'frontier', trainable: false, score: 0.641, leak: 0.052, costPerClaim: 0.71, p50: 44 },
  { id: 'gemini', name: 'Gemini 3 Pro', vendor: 'Google', kind: 'frontier', trainable: false, score: 0.585, leak: 0.074, costPerClaim: 0.29, p50: 31 },
  { id: 'qwen35', name: 'Qwen 3.6 35B-A3B', vendor: 'Alibaba · open weights', kind: 'open', trainable: true, score: 0.341, leak: 0.142, costPerClaim: 0.031, p50: 9 },
  { id: 'nemo', name: 'Nemotron 3.5 Lightning 30B', vendor: 'NVIDIA · open weights', kind: 'open', trainable: true, score: 0.297, leak: 0.161, costPerClaim: 0.019, p50: 7 },
  { id: 'glm', name: 'GLM 5.3 Flash', vendor: 'Z.ai · open weights', kind: 'open', trainable: true, score: 0.392, leak: 0.118, costPerClaim: 0.048, p50: 11 },
]

export const RECIPES = [
  { id: 'sft', name: 'Warm start (SFT)', tag: 'Fastest', desc: 'Imitate expert demonstrations. Good first step; plateaus below RL.', uplift: 0.2, minutes: 40, costPerStep: 6 },
  { id: 'grpo', name: 'Reinforcement learning (GRPO)', tag: 'Recommended', desc: 'Model attempts each task 8×, graded by your reward; learns from what beat its average.', uplift: 0.38, minutes: 290, costPerStep: 15 },
  { id: 'gs1', name: 'Learn from production (single rollout)', tag: 'Research preview', desc: 'Trains on live traces scored by the online grader — no replays needed.', uplift: 0.31, minutes: 180, costPerStep: 9 },
] as const

export type RecipeId = (typeof RECIPES)[number]['id']

export const EVAL_CATEGORIES = [
  { id: 'decision', label: 'Decision' },
  { id: 'labor', label: 'Labor op' },
  { id: 'tsb', label: 'TSB cited' },
  { id: 'note', label: 'Dealer note' },
  { id: 'coverage', label: 'Coverage' },
]

export const DRIFT_ALERT = {
  title: '2027 Bronco Sport 1.5L — score dropped after a new bulletin',
  detail: 'TSB 26-2311 (published Tuesday) introduced labor op 12-4410-C. Online grader score on these claims fell from 0.79 to 0.58; 38 traces are flagged as low-confidence.',
  traces: 38,
}
