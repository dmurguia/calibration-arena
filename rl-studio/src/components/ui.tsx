import { type ButtonHTMLAttributes, type ReactNode, useState } from 'react'
import { Check, Copy } from 'lucide-react'

const cx = (...c: (string | false | undefined | null)[]) => c.filter(Boolean).join(' ')
export { cx }

type BtnVariant = 'primary' | 'secondary' | 'ghost' | 'leather'
export function Button({ variant = 'primary', size = 'md', className, children, ...rest }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: BtnVariant; size?: 'sm' | 'md' | 'lg' }) {
  const v = {
    primary: 'bg-ink text-paper hover:bg-ink-deep disabled:bg-steel',
    leather: 'bg-leather text-paper hover:bg-[#5c4432] disabled:bg-steel',
    secondary: 'bg-card text-ink border border-hairline hover:border-ink/40 disabled:text-steel',
    ghost: 'text-graphite hover:text-ink hover:bg-ink/5',
  }[variant]
  const sz = { sm: 'h-8 px-3 text-[13px]', md: 'h-9 px-4 text-sm', lg: 'h-11 px-5 text-[15px]' }[size]
  return (
    <button className={cx('inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors disabled:cursor-not-allowed', v, sz, className)} {...rest}>
      {children}
    </button>
  )
}

export function Card({ className, children, pad = true }: { className?: string; children: ReactNode; pad?: boolean }) {
  return <div className={cx('rounded-lg border border-hairline bg-card', pad && 'p-5', className)}>{children}</div>
}

type Tone = 'neutral' | 'good' | 'bad' | 'warn' | 'leather' | 'ink'
export function Badge({ tone = 'neutral', children, className }: { tone?: Tone; children: ReactNode; className?: string }) {
  const t = {
    neutral: 'bg-ink/5 text-graphite',
    good: 'bg-good-tint text-good',
    bad: 'bg-bad-tint text-bad',
    warn: 'bg-warn-tint text-warn',
    leather: 'bg-leather-tint text-leather',
    ink: 'bg-ink text-paper',
  }[tone]
  return <span className={cx('inline-flex items-center gap-1 whitespace-nowrap rounded px-1.5 py-0.5 text-[11px] font-medium uppercase tracking-wide', t, className)}>{children}</span>
}

export function LiveDot({ tone = 'good' }: { tone?: 'good' | 'leather' | 'warn' }) {
  const c = { good: 'bg-good', leather: 'bg-leather', warn: 'bg-warn' }[tone]
  return <span className={cx('inline-block h-2 w-2 animate-pulsedot rounded-full', c)} />
}

export function Stat({ label, value, sub, delta, deltaTone = 'good' }: { label: string; value: ReactNode; sub?: ReactNode; delta?: string; deltaTone?: 'good' | 'bad' }) {
  return (
    <Card>
      <div className="text-xs uppercase tracking-wider text-graphite">{label}</div>
      <div className="mt-2 flex items-baseline gap-2">
        <div className="text-2xl font-semibold text-ink">{value}</div>
        {delta && <span className={cx('text-xs font-medium', deltaTone === 'good' ? 'text-good' : 'text-bad')}>{delta}</span>}
      </div>
      {sub && <div className="mt-1 text-xs text-graphite">{sub}</div>}
    </Card>
  )
}

export function PageHeader({ eyebrow, title, desc, actions }: { eyebrow?: string; title: string; desc?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
      <div className="max-w-3xl">
        {eyebrow && <div className="mb-1 font-mono text-[11px] uppercase tracking-[0.14em] text-leather">{eyebrow}</div>}
        <h1 className="text-[26px] font-semibold leading-tight text-ink">{title}</h1>
        {desc && <p className="mt-1.5 text-[14.5px] leading-relaxed text-graphite">{desc}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  )
}

export function Progress({ value, tone = 'ink', className }: { value: number; tone?: 'ink' | 'leather' | 'good'; className?: string }) {
  const c = { ink: 'bg-ink', leather: 'bg-leather', good: 'bg-good' }[tone]
  return (
    <div className={cx('h-1.5 w-full overflow-hidden rounded-full bg-ink/10', className)}>
      <div className={cx('h-full rounded-full transition-all duration-500', c)} style={{ width: `${Math.round(value * 100)}%` }} />
    </div>
  )
}

export function Code({ code, title, className }: { code: string; title?: string; className?: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <div className={cx('overflow-hidden rounded-lg border border-ink/80 bg-ink-deep text-[12.5px]', className)}>
      <div className="flex items-center justify-between border-b border-white/10 px-3 py-1.5 font-mono text-[11px] text-steel">
        <span>{title ?? 'code'}</span>
        <button
          className="flex items-center gap-1 hover:text-paper"
          onClick={() => {
            navigator.clipboard?.writeText(code)
            setCopied(true)
            setTimeout(() => setCopied(false), 1200)
          }}
        >
          {copied ? <Check size={12} /> : <Copy size={12} />} {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <pre className="scrollbar-thin overflow-x-auto p-3 font-mono leading-relaxed text-[#E9E5DA]">{code}</pre>
    </div>
  )
}

export function Tabs<T extends string>({ tabs, value, onChange }: { tabs: { id: T; label: ReactNode }[]; value: T; onChange: (t: T) => void }) {
  return (
    <div className="flex gap-1 border-b border-hairline">
      {tabs.map((t) => (
        <button
          key={t.id}
          onClick={() => onChange(t.id)}
          className={cx('-mb-px border-b-2 px-3 py-2 text-[13px] font-medium transition-colors', value === t.id ? 'border-ink text-ink' : 'border-transparent text-graphite hover:text-ink')}
        >
          {t.label}
        </button>
      ))}
    </div>
  )
}

export function SectionTitle({ children, right }: { children: ReactNode; right?: ReactNode }) {
  return (
    <div className="mb-3 flex items-center justify-between">
      <h2 className="text-[13px] font-semibold uppercase tracking-wider text-graphite">{children}</h2>
      {right}
    </div>
  )
}

export function Empty({ icon, title, desc, action }: { icon: ReactNode; title: string; desc: ReactNode; action?: ReactNode }) {
  return (
    <Card className="grid-bg flex flex-col items-center py-14 text-center">
      <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-full border border-hairline bg-card text-leather">{icon}</div>
      <div className="text-[17px] font-semibold">{title}</div>
      <div className="mt-1 max-w-md text-sm text-graphite">{desc}</div>
      {action && <div className="mt-5">{action}</div>}
    </Card>
  )
}

export function Logo({ dark = false, size = 22 }: { dark?: boolean; size?: number }) {
  return (
    <div className="flex items-center gap-2">
      <img src={dark ? '/logos/calibrated-mark-paper.svg' : '/logos/calibrated-mark-ink.svg'} width={size} height={size} alt="" />
      <span className={cx('font-identity text-[15px] tracking-tight', dark ? 'text-paper' : 'text-ink')}>
        Calibrated <span className="font-sans font-medium text-leather">Studio</span>
      </span>
    </div>
  )
}

export const chartColors = { ink: '#464643', leather: '#70543E', steel: '#929698', good: '#4E6B4F', bad: '#9A4A36', warn: '#A27A2C', grid: '#4646431A' }
