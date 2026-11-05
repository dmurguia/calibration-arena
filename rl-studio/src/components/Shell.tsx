import { NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Activity, Boxes, ChevronDown, FlaskConical, Gauge, LayoutDashboard, Rocket, Search, ScrollText, Users } from 'lucide-react'
import { useEffect } from 'react'
import { AGENT, COMPANY, DEMO_USER } from '../lib/data'
import { runProgress, useDemo } from '../lib/store'
import { Badge, cx, LiveDot, Logo } from './ui'

const NAV = [
  { group: 'Workspace', items: [{ to: '/app', label: 'Overview', icon: LayoutDashboard, end: true }] },
  {
    group: 'Learn',
    items: [
      { to: '/app/traces', label: 'Production traces', icon: ScrollText },
      { to: '/app/environment', label: 'Environment', icon: Boxes },
      { to: '/app/experts', label: 'Experts & data', icon: Users },
    ],
  },
  {
    group: 'Improve',
    items: [
      { to: '/app/evals', label: 'Evaluations', icon: FlaskConical },
      { to: '/app/training', label: 'Training runs', icon: Gauge },
    ],
  },
  {
    group: 'Ship',
    items: [
      { to: '/app/deploy', label: 'Deployments', icon: Rocket },
      { to: '/app/monitor', label: 'Online evals', icon: Activity },
    ],
  },
]

export default function Shell() {
  const { s, now } = useDemo()
  const nav = useNavigate()
  const loc = useLocation()
  useEffect(() => {
    if (!s.user) nav('/signup', { replace: true })
  }, [s.user, nav])
  useEffect(() => {
    document.querySelector('main')?.scrollTo(0, 0)
  }, [loc.pathname])
  const running = s.runs.filter((r) => runProgress(r, now) < 1).length

  return (
    <div className="flex h-full">
      <aside className="flex w-[232px] shrink-0 flex-col border-r border-hairline bg-[#EFEBE1]">
        <div className="px-4 pb-3 pt-4">
          <Logo />
        </div>
        <button className="mx-3 mb-3 flex items-center justify-between rounded-md border border-hairline bg-card px-2.5 py-2 text-left">
          <div className="flex items-center gap-2">
            <div className="flex h-6 w-6 items-center justify-center rounded bg-[#1B3A6B] font-mono text-[10px] font-semibold text-white">F</div>
            <div className="leading-tight">
              <div className="text-[12.5px] font-medium">{AGENT.display}</div>
              <div className="text-[11px] text-graphite">{COMPANY.name}</div>
            </div>
          </div>
          <ChevronDown size={14} className="text-graphite" />
        </button>
        <div className="mx-3 mb-2 flex items-center gap-2 rounded-md border border-hairline px-2.5 py-1.5 text-[12.5px] text-steel">
          <Search size={13} /> Search <span className="ml-auto font-mono text-[10px]">⌘K</span>
        </div>
        <nav className="scrollbar-thin flex-1 overflow-y-auto px-2 pb-4">
          {NAV.map((g) => (
            <div key={g.group} className="mt-3">
              <div className="px-2 pb-1 font-mono text-[10px] uppercase tracking-[0.14em] text-steel">{g.group}</div>
              {g.items.map((it) => (
                <NavLink
                  key={it.to}
                  to={it.to}
                  end={'end' in it ? it.end : false}
                  className={({ isActive }) =>
                    cx('flex items-center gap-2.5 rounded-md px-2 py-1.5 text-[13.5px] transition-colors', isActive ? 'bg-card font-medium text-ink shadow-[0_0_0_1px_#4646432B]' : 'text-graphite hover:bg-card/60 hover:text-ink')
                  }
                >
                  <it.icon size={15} strokeWidth={1.8} />
                  {it.label}
                  {it.to === '/app/training' && running > 0 && (
                    <span className="ml-auto flex items-center gap-1 text-[11px] text-leather">
                      <LiveDot tone="leather" /> {running}
                    </span>
                  )}
                  {it.to === '/app/monitor' && (s.deployment?.stage === 'canary' || s.deployment?.stage === 'full') && (
                    <span className="ml-auto">
                      <LiveDot />
                    </span>
                  )}
                </NavLink>
              ))}
            </div>
          ))}
        </nav>
        {s.deployment && (
          <div className="mx-3 mb-3 rounded-md border border-hairline bg-card px-3 py-2 text-[12px]">
            <div className="flex items-center gap-1.5 font-medium">
              <LiveDot /> {s.deployment.runId} {s.deployment.stage === 'full' ? 'serving 100%' : s.deployment.stage === 'canary' ? 'canary 10%' : s.deployment.stage}
            </div>
            <div className="text-graphite">incumbent: {AGENT.model}</div>
          </div>
        )}
        <div className="flex items-center gap-2 border-t border-hairline px-4 py-3">
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-leather text-[11px] font-semibold text-paper">{DEMO_USER.initials}</div>
          <div className="min-w-0 leading-tight">
            <div className="truncate text-[12.5px] font-medium">{s.user?.name ?? DEMO_USER.name}</div>
            <div className="truncate text-[11px] text-graphite">{s.user?.email ?? DEMO_USER.email}</div>
          </div>
        </div>
      </aside>
      <main className="scrollbar-thin flex-1 overflow-y-auto">
        <div className="sticky top-0 z-10 flex h-11 items-center justify-between border-b border-hairline bg-paper/90 px-8 text-[12.5px] backdrop-blur">
          <div className="flex items-center gap-2 text-graphite">
            <span>{COMPANY.workspace}</span>
            <span className="text-steel">/</span>
            <span className="font-mono text-ink">{AGENT.name}</span>
          </div>
          <div className="flex items-center gap-3">
            <Badge tone="leather">{COMPANY.plan}</Badge>
            <span className="text-graphite">Credits <span className="font-mono text-ink">$18,400</span></span>
          </div>
        </div>
        <div className="mx-auto max-w-[1180px] px-8 py-7 pb-40">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
