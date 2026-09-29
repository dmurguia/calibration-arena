import { ArrowRightIcon } from 'lucide-react'
import { CalibratedMark } from '../brand/CalibratedMark'

export function ReportTeaser() {
  return (
    <section aria-labelledby="report" className="bg-paper py-20">
      <div className="mx-auto grid max-w-[1180px] items-center gap-12 px-6 lg:grid-cols-[minmax(0,1fr)_400px] lg:px-10">
        <div>
          <p className="flex items-center gap-3 font-mono text-[10px] uppercase tracking-[0.2em] text-muted">
            <span className="text-ink">06</span>
            <span aria-hidden="true" className="h-px w-8 bg-hairline" />
            <span>State of Finance AI</span>
          </p>
          <h2 id="report" className="mt-4 max-w-xl font-display text-[34px] leading-[1.15] text-ink md:text-[42px]">
            Issue #2 adds vendor products. Five founding seats.
          </h2>
          <p className="mt-5 max-w-lg text-[14.5px] leading-relaxed text-muted">
            A twice-yearly report on what AI can and cannot do in accounting, built entirely from blind CPA
            judgment. Issue #1 covered eleven foundation models across four task families.
          </p>
          <div className="mt-7 flex flex-wrap items-center gap-5">
            <a
              href="#report"
              className="flex items-center gap-2 rounded-[8px] bg-spruce px-4 py-2.5 text-[13px] font-bold text-paper transition-colors duration-150 ease-out hover:bg-spruce-hover"
            >
              Read Issue #1
              <ArrowRightIcon className="h-3.5 w-3.5" aria-hidden="true" />
            </a>
            <a
              href="#report"
              className="border-b border-ink/30 pb-1 text-[13px] font-bold text-ink transition-colors duration-150 ease-out hover:border-needle hover:text-needle"
            >
              Enquire about a founding seat
            </a>
          </div>
        </div>

        <div className="mx-auto w-full max-w-[360px] rounded-[4px] border border-hairline bg-card px-8 py-9 shadow-lift">
          <div className="flex items-center justify-between border-b-2 border-ink pb-2">
            <span className="flex items-center gap-2 text-ink">
              <CalibratedMark size={16} />
              <span className="text-[11px] font-extrabold tracking-tight">Calibrated Co.</span>
            </span>
            <span className="font-mono text-[9px] uppercase tracking-[0.16em] text-muted">Issue #1</span>
          </div>
          <div className="mt-1 h-px w-full bg-ink" />

          <p className="mt-8 font-mono text-[9px] uppercase tracking-[0.2em] text-muted">Spring 2026</p>
          <h3 className="mt-3 font-display text-[30px] leading-[1.1] text-ink">
            The State of
            <br />
            Finance AI
          </h3>
          <p className="mt-4 border-t border-hairline pt-3 text-[12px] leading-relaxed text-muted">
            Eleven foundation models, judged blind by 2,104 verified CPAs across 56,410 comparisons.
          </p>

          <div className="mt-10 space-y-2">
            {[
              ['Journal Entries', '68%'],
              ['Reconciliation', '54%'],
              ['Revenue Recognition', '41%'],
            ].map(([label, value]) => (
              <div key={label} className="flex items-baseline justify-between border-b border-hairline pb-1.5">
                <span className="text-[11.5px] text-muted">{label}</span>
                <span className="font-display text-[15px] tabular-nums text-ink">{value}</span>
              </div>
            ))}
          </div>

          <p className="mt-8 border-t-2 border-ink pt-2 font-mono text-[9px] uppercase tracking-[0.16em] text-muted">
            Calibration Arena · by Calibrated Co.
          </p>
        </div>
      </div>
    </section>
  )
}
