# Calibrated Studio — RL environment demo

A standalone, click-through demo of "vibe-building" an RL environment end to end, told from the point of view of a Fortune-500 team (Ford Global Warranty Operations) that has a primitive Claude-based agent and wants a specialist model it owns.

Everything is simulated in the browser: no backend, no API keys, no real training. Company, people, claims, VINs, TSBs and metrics are fictional. State lives in `localStorage` (`calibrated-studio-demo-v1`), and long jobs run on an accelerated demo clock (experts 3 days → 45 s, training ≈5 h → 70 s).

```bash
cd rl-studio
npm install
npm run dev      # http://localhost:5199
npm run build    # typecheck + production build
```

To host it on Vercel, create a project with **Root Directory = `rl-studio`** (framework: Vite). `vercel.json` adds the SPA rewrite.

## Walkthrough

The dark **Demo guide** panel (bottom right) follows you through 12 steps. **Reset** clears all state; **Skip to end state** loads a fully populated workspace (3 finished runs, run-02 on a 10% canary).

| # | Page | What to show |
|---|------|--------------|
| 1 | `/` Landing | Pitch: coding agents made software accessible; Studio does the same for post-training. |
| 2 | `/signup` | Work email or Okta/Entra SSO → demo code → Ford workspace discovered by domain, with data-isolation, PII/VIN scrubbing and BYO-VPC controls. |
| 3 | `/onboarding` | Pick the harness (Claude Agent SDK, OpenAI Agents/Codex, LangGraph, any OpenAI-compatible client), 2-line proxy change, import 1,842 traces, pick the *Warranty claim triage* template. |
| 4 | `/app` Overview | The 7-step learning loop checklist and the business case. |
| 5 | `/app/traces` | Failure clusters from analyst overrides (wrong labor op, unneeded escalations, missed TSBs, out-of-coverage approvals, invented parts). Open WC-26-0418837 to see the bad trajectory and the analyst override. |
| 6 | `/app/environment` | Chat with the environment copilot: it drafts tools, 1,240 tasks (replayed + synthetic), a reward (checks + calibrated rubric + penalties) and asks one question that sets reward weights by business cost. **Validate** runs sandbox, determinism, grader agreement, reward-hacking and headroom checks. |
| 7 | `/app/experts` | Pick experts (master tech, warranty admin, leakage auditor, EV, diesel, internal analysts), set quantities, see the estimate, start the job. Watch counts fill and grader↔expert agreement climb to κ≈0.85. |
| 8 | `/app/evals` | Baseline 6 models on the held-out split. Claude 61%, open-weight models ~30–39% but 10–20× cheaper. |
| 9 | `/app/training/new` | Pick base model + recipe (SFT warm start, GRPO, single-rollout from production), budget cap, guardrails. **Start + compare with Nemotron** launches two runs. |
| 10 | `/app/training/:id` | Live reward + held-out curves vs. the production line, KL, guardrails, and the same claim replayed at any checkpoint. |
| 11 | `/app/deploy` | Gate (held-out ≥ prod, wrong approvals ≤ prod, latency, regression suite, rubric-owner approval) then test → shadow → 10% canary → 100% with rollback. |
| 12 | `/app/monitor` | Online grader scores live traffic for incumbent vs candidate, live graded-claims feed, a drift alert on a new TSB → send traces to experts → schedule nightly retrain (the flywheel). |

## Structure

- `src/lib/data.ts` — all fictional demo data
- `src/lib/store.tsx` — demo state, timers, simulated runs, end-state fixture
- `src/lib/sim.ts`, `src/lib/runs.ts` — seeded curves and run metrics
- `src/components/` — shell, demo guide, UI kit (Calibrated brand)
- `src/pages/` — one file per step
