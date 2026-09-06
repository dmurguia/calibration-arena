import { useEffect, useMemo, useRef, useState } from 'react'

/**
 * The engraving ships locally at frontend/public/engraving.jpg — an
 * industrial-era San Francisco countinghouse: bookkeepers and a master
 * craftsman at work, precision instruments on the desk, a factory skyline
 * behind them. The CDN copy is used only if that file is missing.
 */
const LOCAL_ENGRAVING = '/engraving.jpg'
const FALLBACK_ENGRAVING =
  'https://cdn.magicpatterns.com/patterns/generated-images/7ecb6c02-17f3-4947-bf66-517102656cc1.jpg'

interface CalibrationLensProps {
  /** Lens radius in px. */
  radius?: number
  /** How strongly the engraving reads against the paper ground. */
  intensity?: number
}

interface Readout {
  name: string
  score: number
  ci: number
  rank: number
  delta: number
  winRate: number
}

interface JournalLine {
  account: string
  debit?: number
  credit?: number
}

interface JournalEntry {
  memo: string
  lines: JournalLine[]
}

// A handful of textbook entries, each of which foots. The ledger shows the
// posting and then the check — debits equal credits — so the numbers read as
// something that ties out, not decoration.
const ENTRIES: JournalEntry[] = [
  {
    memo: 'Annual SaaS collected upfront',
    lines: [
      { account: 'Cash', debit: 12000 },
      { account: 'Deferred revenue', credit: 12000 },
    ],
  },
  {
    memo: 'November recognition',
    lines: [
      { account: 'Deferred revenue', debit: 1000 },
      { account: 'Subscription revenue', credit: 1000 },
    ],
  },
  {
    memo: 'Machine purchase with freight',
    lines: [
      { account: 'Machinery', debit: 48250 },
      { account: 'Freight-in', debit: 1750 },
      { account: 'Accounts payable', credit: 50000 },
    ],
  },
  {
    memo: 'Write-off, allowance method',
    lines: [
      { account: 'Allowance for doubtful accts', debit: 3400 },
      { account: 'Accounts receivable', credit: 3400 },
    ],
  },
  {
    memo: 'Month-end accrual',
    lines: [
      { account: 'Wages expense', debit: 18620 },
      { account: 'Accrued liabilities', credit: 18620 },
    ],
  },
  {
    memo: 'Depreciation, straight line',
    lines: [
      { account: 'Depreciation expense', debit: 4166.67 },
      { account: 'Accumulated depreciation', credit: 4166.67 },
    ],
  },
]

const money = (n: number) =>
  n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

function ReadoutBlock({ r }: { r: Readout }) {
  return (
    <div className="border-t border-ink/30 pt-2">
      <p className="truncate font-mono text-[11px] font-semibold uppercase tracking-[0.14em] text-ink">
        {r.name}
      </p>
      <p className="mt-1 font-mono text-[20px] font-semibold leading-none tabular-nums text-ink">
        {r.score}
        <span className="ml-1.5 text-[12px] font-normal text-muted">±{r.ci}</span>
      </p>
      <p className="mt-1.5 font-mono text-[11px] tabular-nums text-muted">
        RANK {String(r.rank).padStart(2, '0')}
        <span className={r.delta > 0 ? 'text-spruce' : r.delta < 0 ? 'text-needle' : ''}>
          {r.delta > 0 ? ` ▲${r.delta}` : r.delta < 0 ? ` ▼${Math.abs(r.delta)}` : ' —'}
        </span>
        <span className="ml-3">WIN {(r.winRate * 100).toFixed(1)}%</span>
      </p>
    </div>
  )
}

function JournalBlock({ e, n }: { e: JournalEntry; n: number }) {
  const dr = e.lines.reduce((s, l) => s + (l.debit ?? 0), 0)
  const cr = e.lines.reduce((s, l) => s + (l.credit ?? 0), 0)
  return (
    <div className="border-t border-ink/30 pt-2 font-mono text-[11px] tabular-nums">
      <p className="truncate uppercase tracking-[0.14em] text-muted">
        JE {String(n).padStart(4, '0')} · {e.memo}
      </p>
      {e.lines.map((l, i) => (
        <p key={i} className="mt-1 flex justify-between gap-3 text-ink">
          <span className={`truncate ${l.credit ? 'pl-4' : ''}`}>
            {l.credit ? 'Cr ' : 'Dr '}
            {l.account}
          </span>
          <span className="shrink-0">{money(l.debit ?? l.credit ?? 0)}</span>
        </p>
      ))}
      <p className="mt-1 flex justify-between gap-3 border-t border-ink/20 pt-1 text-spruce">
        <span>{dr === cr ? 'FOOTS ✓' : 'OUT OF BALANCE'}</span>
        <span className="shrink-0">
          {money(dr)} | {money(cr)}
        </span>
      </p>
    </div>
  )
}

/**
 * The signature interaction, and the page's ground. A period engraving sits far
 * back behind everything; the pointer carries a small calibration lens that
 * locally resolves the drawing into the ledger behind it: model ratings and
 * journal entries that foot. The ledger fills the whole viewport in slow-falling
 * columns so the lens finds something wherever it lands.
 */
export function CalibrationLens({ radius = 78, intensity = 0.13 }: CalibrationLensProps) {
  const root = useRef<HTMLDivElement | null>(null)
  const [point, setPoint] = useState<{ x: number; y: number } | null>(null)
  const [pinned, setPinned] = useState(false)
  const [src, setSrc] = useState(LOCAL_ENGRAVING)

  // Practice-only lens: never use fictional model scores as background texture.
  const readouts: Readout[] = useMemo(() => [], [])

  // Interleave ratings with journal entries, then give each column a different
  // starting offset so neighbouring columns don't line up.
  const columns = useMemo(() => {
    const blocks: Array<{ kind: 'readout'; r: Readout } | { kind: 'journal'; e: JournalEntry; n: number }> = []
    const len = Math.max(readouts.length, ENTRIES.length)
    for (let i = 0; i < len * 2; i++) {
      const r = readouts[i % readouts.length]
      if (r) blocks.push({ kind: 'readout', r })
      const e = ENTRIES[i % ENTRIES.length]
      if (e) blocks.push({ kind: 'journal', e, n: 1180 + i })
    }
    const COLS = 7
    return Array.from({ length: COLS }, (_, c) => {
      const offset = (c * 5) % Math.max(blocks.length, 1)
      return blocks.slice(offset).concat(blocks.slice(0, offset))
    })
  }, [readouts])

  // Devices without hover, and readers who ask for less motion, get one fixed
  // already-resolved pool instead of a pointer-tracked one.
  useEffect(() => {
    const noHover = window.matchMedia('(hover: none)')
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)')

    const settle = () => {
      if (noHover.matches || reduced.matches) {
        setPinned(true)
        setPoint({ x: window.innerWidth * 0.82, y: window.innerHeight * 0.28 })
      } else {
        setPinned(false)
        setPoint(null)
      }
    }

    settle()
    noHover.addEventListener('change', settle)
    reduced.addEventListener('change', settle)
    return () => {
      noHover.removeEventListener('change', settle)
      reduced.removeEventListener('change', settle)
    }
  }, [])

  useEffect(() => {
    if (pinned) return
    const onMove = (e: PointerEvent) => {
      const box = root.current?.getBoundingClientRect()
      setPoint({ x: e.clientX - (box?.left ?? 0), y: e.clientY - (box?.top ?? 0) })
    }
    const onLeave = () => setPoint(null)
    window.addEventListener('pointermove', onMove)
    document.documentElement.addEventListener('pointerleave', onLeave)
    return () => {
      window.removeEventListener('pointermove', onMove)
      document.documentElement.removeEventListener('pointerleave', onLeave)
    }
  }, [pinned])

  // Solid through most of the lens, with a short feather at the rim so the
  // ledger dissolves back into paper instead of cutting off.
  const mask = point
    ? `radial-gradient(circle at ${point.x}px ${point.y}px, #000 0 ${radius - 14}px, transparent ${radius}px)`
    : 'radial-gradient(circle at -600px -600px, #000 0 1px, transparent 2px)'

  return (
    <div ref={root} aria-hidden="true" className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
      {/* 1 — the drawing */}
      <img
        src={src}
        onError={() => {
          if (src !== FALLBACK_ENGRAVING) setSrc(FALLBACK_ENGRAVING)
        }}
        alt=""
        className="absolute inset-0 h-full w-full object-cover"
        style={{ opacity: intensity, filter: 'grayscale(1) contrast(1.12)' }}
      />

      {/* 3 — the ledger, clipped to the lens (2) */}
      <div
        className="absolute inset-0 bg-paper"
        style={{ WebkitMaskImage: mask, maskImage: mask }}
      >
        <div className="flex h-full w-full gap-6 px-6">
          {columns.map((col, c) => (
            <div
              key={c}
              className={`ledger-column min-w-0 flex-1 ${c >= 4 ? 'hidden lg:block' : c >= 3 ? 'hidden md:block' : ''}`}
            >
              {/* content is doubled so the fall loops seamlessly */}
              <div
                className="ledger-fall flex flex-col gap-5"
                style={{ animationDuration: `${140 + c * 23}s`, animationDelay: `-${c * 17}s` }}
              >
                {[0, 1].map((rep) => (
                  <div key={rep} className="flex flex-col gap-5">
                    {col.map((b, i) =>
                      b.kind === 'readout' ? (
                        <ReadoutBlock key={`r-${rep}-${i}`} r={b.r} />
                      ) : (
                        <JournalBlock key={`j-${rep}-${i}`} e={b.e} n={b.n} />
                      ),
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* the lens edge — one hairline ring, flat */}
      {point ? (
        <span
          className="absolute rounded-full border border-needle/50"
          style={{
            left: point.x - radius,
            top: point.y - radius,
            width: radius * 2,
            height: radius * 2,
          }}
        />
      ) : null}
    </div>
  )
}
