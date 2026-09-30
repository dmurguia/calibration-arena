import { AppShell } from '../components/app/AppShell'
import { CalibrationLens } from '../components/brand/CalibrationLens'
import { Resolve } from '../components/brand/Resolve'
import { MethodSteps } from '../components/about/MethodSteps'
import { StatBand } from '../components/about/StatBand'
import { WhyAccounting } from '../components/about/WhyAccounting'
import { TwoAudiences } from '../components/about/TwoAudiences'
import { ReportTeaser } from '../components/about/ReportTeaser'
import { SocialRow } from '../components/about/SocialRow'
import { seasonMeta } from '../data/competitors'

export function About() {
  return (
    <AppShell>
      <div id="about-top" className="relative w-full">
        <CalibrationLens radius={84} intensity={0.14} />

        <div className="relative z-10">
          <header className="border-b border-hairline pb-24 pt-20">
            <div className="mx-auto max-w-[1180px] px-6 text-center lg:px-10">
              <p className="inline-block bg-paper/85 px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.22em] text-muted">
                The rating agency for AI professional work
              </p>
              <Resolve
                as="h1"
                className="mx-auto mt-6 max-w-3xl font-display text-[40px] leading-[1.1] text-ink md:text-[54px]"
              >
                We measure the judges, then let them measure the machines.
              </Resolve>
              <p className="mx-auto mt-6 max-w-xl bg-paper/85 px-3 py-1 text-[15px] leading-relaxed text-muted">
                Calibration Arena is run by Calibrated Co. Working CPAs judge AI-drafted accounting work blind;
                their measured-accuracy votes move public boards where foundation models and vendor products
                compete on the same evidence.
              </p>
              <div className="mt-8">
                <SocialRow />
              </div>

              <p className="mx-auto mt-16 max-w-lg border-t border-hairline bg-paper/85 px-3 pt-4 text-[12.5px] leading-relaxed text-muted">
                A watchmaker never trusted a movement because it looked right. He put it on a timing rig, measured
                the error, and adjusted until the instrument agreed with a known reference. That is the whole idea
                here — move your cursor across the page to see it.
              </p>
            </div>
          </header>

          <MethodSteps />
          <StatBand />
          <WhyAccounting />
          <TwoAudiences />
          <ReportTeaser />

          <footer className="border-t border-hairline bg-panel">
            <div className="mx-auto flex max-w-[1180px] flex-wrap items-center justify-between gap-3 px-6 py-6 lg:px-10">
              <p className="font-mono text-[9.5px] uppercase tracking-[0.16em] text-muted">
                Calibration Arena · by Calibrated Co. · {seasonMeta.season}
              </p>
              <p className="text-[11.5px] text-muted/80">by Calibrated Co.</p>
            </div>
          </footer>
        </div>
      </div>
    </AppShell>
  )
}
