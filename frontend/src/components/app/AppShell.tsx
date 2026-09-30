import React, { useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import {
  PlusIcon,
  SearchIcon,
  FolderIcon,
  BarChart3Icon,
  BoxesIcon,
  InfoIcon,
  LogOutIcon,
  UserRoundIcon,
} from 'lucide-react'
import { CalibratedMark } from '../brand/CalibratedMark'
import { SearchModal } from './SearchModal'
import { AuthModal } from './AuthModal'
import { useAuth } from '../../lib/auth'
import { seasonMeta } from '../../data/competitors'
import type { UserOut } from '../../lib/api'

interface AppShellProps {
  children: React.ReactNode
}

function initialsOf(user: UserOut): string {
  const source = user.display_name?.trim() || user.email
  const parts = source.split(/[\s.@_-]+/).filter(Boolean)
  return ((parts[0]?.[0] ?? '') + (parts[1]?.[0] ?? '')).toUpperCase() || 'R'
}

const TIER_LABELS: Record<number, string> = {
  0: 'Guest-weight reviewer',
  1: 'Verified · work domain',
  2: 'Licensed · verified',
  3: 'Named reviewer',
}

export function AppShell({ children }: AppShellProps) {
  const location = useLocation()
  const { user, requestAuth, signOut } = useAuth()
  const [searchOpen, setSearchOpen] = useState(false)

  const openSearch = () => {
    if (user) setSearchOpen(true)
    else requestAuth('search')
  }

  const primary = [
    { to: '/leaderboards', label: 'Leaderboards', icon: BarChart3Icon },
    { to: '/models', label: 'Models', icon: BoxesIcon },
    { to: '/about', label: 'About', icon: InfoIcon },
  ]

  const navItemClass = (active: boolean) =>
    `flex w-full items-center gap-2.5 rounded-[8px] px-3 py-2 text-left text-[13px] font-semibold transition-colors duration-150 ease-out ${
      active ? 'bg-card text-ink shadow-whisper' : 'text-muted hover:bg-card/60 hover:text-ink'
    }`

  return (
    <div className="flex min-h-screen w-full bg-paper">
      <aside className="sticky top-0 z-20 hidden h-screen w-[236px] shrink-0 flex-col border-r border-hairline bg-panel md:flex">
        <div className="border-b border-hairline px-5 py-5">
          <Link to="/" className="flex items-center gap-2.5 text-ink">
            <CalibratedMark size={26} title="Calibrated Co." />
            <span className="leading-tight">
              <span className="block text-[14px] font-extrabold tracking-tight">Calibration Arena</span>
              <span className="block text-[10px] font-medium text-muted">by Calibrated Co.</span>
            </span>
          </Link>
        </div>

        <nav className="flex-1 overflow-y-auto px-3 py-4 scroll-quiet" aria-label="Main">
          <ul className="space-y-0.5">
            <li>
              <NavLink to="/" className={navItemClass(location.pathname === '/')}>
                <PlusIcon className="h-4 w-4" strokeWidth={1.9} aria-hidden="true" />
                New Project
              </NavLink>
            </li>
            <li>
              <button type="button" onClick={openSearch} className={navItemClass(false)}>
                <SearchIcon className="h-4 w-4" strokeWidth={1.75} aria-hidden="true" />
                Search Projects
              </button>
            </li>
            <li>
              {user ? (
                <NavLink to="/projects" className={navItemClass(location.pathname === '/projects')}>
                  <FolderIcon className="h-4 w-4" strokeWidth={1.75} aria-hidden="true" />
                  My Projects
                </NavLink>
              ) : (
                <button type="button" onClick={() => requestAuth('projects')} className={navItemClass(false)}>
                  <FolderIcon className="h-4 w-4" strokeWidth={1.75} aria-hidden="true" />
                  My Projects
                </button>
              )}
            </li>
          </ul>

          <ul className="mt-4 space-y-0.5 border-t border-hairline pt-4">
            {primary.map((item) => {
              const Icon = item.icon
              return (
                <li key={item.to}>
                  <NavLink to={item.to} className={navItemClass(location.pathname === item.to)}>
                    <Icon className="h-4 w-4" strokeWidth={1.75} aria-hidden="true" />
                    {item.label}
                  </NavLink>
                </li>
              )
            })}
          </ul>

          <div className="mt-6 border-t border-hairline pt-4">
            <p className="px-3 font-mono text-[9px] uppercase tracking-[0.16em] text-muted">Season</p>
            <p className="mt-1.5 px-3 text-[12px] font-semibold text-ink">
              {seasonMeta.season} · Week {seasonMeta.week}
            </p>
            <p className="px-3 text-[11px] text-muted">
              {seasonMeta.checks.toLocaleString()} calibration checks run
            </p>
          </div>
        </nav>

        <div className="border-t border-hairline p-3">
          {user ? (
            <div className="rounded-[10px] border border-hairline bg-card p-3">
              <div className="flex items-center gap-2.5">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-spruce text-[11px] font-bold text-paper">
                  {initialsOf(user)}
                </span>
                <span className="min-w-0">
                  <span className="block truncate text-[12px] font-bold text-ink">
                    {user.display_name || user.email}
                  </span>
                  <span className="block truncate text-[10px] text-muted">
                    {TIER_LABELS[user.tier] ?? `Tier ${user.tier} reviewer`}
                  </span>
                </span>
              </div>
              <div className="mt-2.5 space-y-1">
                <Link
                  to="/record"
                  className="flex items-center gap-2 rounded-[7px] px-2 py-1.5 text-[11px] font-semibold text-muted transition-colors duration-150 ease-out hover:bg-panel hover:text-ink"
                >
                  <UserRoundIcon className="h-3.5 w-3.5" aria-hidden="true" />
                  My Record
                </Link>
                <button
                  type="button"
                  onClick={signOut}
                  className="flex w-full items-center gap-2 rounded-[7px] px-2 py-1.5 text-[11px] font-semibold text-muted transition-colors duration-150 ease-out hover:bg-panel hover:text-ink"
                >
                  <LogOutIcon className="h-3.5 w-3.5" aria-hidden="true" />
                  Sign out
                </button>
              </div>
            </div>
          ) : (
            <div className="rounded-[10px] border border-hairline bg-card p-3">
              <p className="text-[11px] leading-relaxed text-muted">
                Sign in to keep your projects and build a calibration record.
              </p>
              <button
                type="button"
                onClick={() => requestAuth('projects')}
                className="mt-2.5 w-full rounded-[7px] bg-spruce px-2 py-1.5 text-[11px] font-bold text-paper transition-colors duration-150 ease-out hover:bg-spruce-hover"
              >
                Sign in
              </button>
              <button
                type="button"
                onClick={() => requestAuth('projects')}
                className="mt-1.5 w-full rounded-[7px] border border-hairline px-2 py-1.5 text-[11px] font-semibold text-muted transition-colors duration-150 ease-out hover:border-ink/30 hover:text-ink"
              >
                Create account
              </button>
            </div>
          )}
          <p className="mt-2 px-1 font-mono text-[8.5px] uppercase tracking-[0.14em] text-muted/80">
            by Calibrated Co.
          </p>
        </div>
      </aside>

      {/* Compact rail for small screens */}
      <div className="fixed inset-x-0 top-0 z-30 border-b border-hairline bg-panel md:hidden">
        <div className="flex items-center justify-between px-4 py-2.5">
          <Link to="/" className="flex items-center gap-2 text-ink">
            <CalibratedMark size={20} title="Calibrated Co." />
            <span className="text-[12px] font-extrabold tracking-tight">Calibration Arena</span>
          </Link>
          <button
            type="button"
            onClick={openSearch}
            aria-label="Search projects"
            className="text-muted transition-colors duration-150 ease-out hover:text-ink"
          >
            <SearchIcon className="h-4 w-4" />
          </button>
        </div>
        <nav aria-label="Main" className="flex gap-1 overflow-x-auto px-3 pb-2 scroll-quiet">
          {[{ to: '/', label: 'New' }, ...primary].map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={`whitespace-nowrap rounded-[7px] px-2.5 py-1 text-[12px] font-semibold ${
                location.pathname === item.to ? 'bg-card text-ink' : 'text-muted'
              }`}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>

      <main className="min-w-0 flex-1 pt-[86px] md:pt-0">{children}</main>

      <SearchModal open={searchOpen} onClose={() => setSearchOpen(false)} />
      <AuthModal />
    </div>
  )
}
