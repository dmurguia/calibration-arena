import { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { ArrowUp, Building2, Landmark, ListChecks, MessageCircleQuestion, Scale, Sigma, Users } from 'lucide-react'

// Public profile for the community. Update here when the handle changes.
export const X_URL = 'https://x.com/calibratedco'

function Eyebrow({ children }: { children: ReactNode }) { return <p className="p-eyebrow">{children}</p> }

const XMark = () => <svg viewBox="0 0 24 24" width="15" height="15" aria-hidden="true" fill="currentColor"><path d="M18.2 2h3.4l-7.4 8.5L23 22h-6.8l-5.3-7-6.1 7H1.4l7.9-9.1L1 2h7l4.8 6.4L18.2 2Zm-1.2 18h1.9L7.1 3.9H5.1L17 20Z" /></svg>

/* Illustrations echo the arena itself: the composer, the task chips, the model pool, the two-up comparison. */
function PromptFigure() {
  return <div className="p-ab-figure"><div className="p-ab-composer" aria-hidden="true"><p>Our August close booked $86,400 of steel twice. The invoice arrived September 3 for $87,100. What needs correcting, and what evidence should we check before posting?</p><div><span>Same prompt · two models</span><span className="p-ab-send"><ArrowUp size={15} /></span></div></div></div>
}

function CategoryFigure() {
  return <div className="p-ab-figure"><div className="p-ab-chips" aria-hidden="true"><span><Landmark size={13} />Bank reconciliation</span><span className="is-on"><ListChecks size={13} />Close management</span><span><Building2 size={13} />Consolidation</span><span><MessageCircleQuestion size={13} />Open question</span></div></div>
}

function SamplingFigure() {
  return <div className="p-ab-figure"><div className="p-ab-pool" aria-hidden="true">{Array.from({ length: 20 }, (_, i) => <span key={i} className={i === 4 ? 'is-on' : i === 13 ? 'is-on is-b' : ''}>{i === 4 ? 'A' : i === 13 ? 'B' : ''}</span>)}</div></div>
}

function PairwiseFigure() {
  return <div className="p-ab-pair" aria-hidden="true"><div><span>Response A</span><i /><i /><i style={{ width: '55%' }} /></div><div className="is-on"><span>Response B</span><i /><i /><i style={{ width: '70%' }} /><b>Preferred</b></div></div>
}

export function About() {
  return <div className="p-about p-method">
    <header className="p-ab-hero">
      <Eyebrow>Calibrated · Finance</Eyebrow>
      <h1>About</h1>
      <p className="p-lead">A framework and community of knowledge workers honing their craft for AI financial capabilities. Join the growing community.</p>
      <div className="p-ab-social"><a href={X_URL} target="_blank" rel="noreferrer"><XMark />Follow on X</a></div>
    </header>

    <section className="p-ab-section">
      <h2>Tournament format</h2>
      <div className="p-ab-cards">
        <article><PromptFigure /><h3>Prompt selection</h3><p>You bring the question, in your own words, with the files the work needs.</p></article>
        <article><CategoryFigure /><h3>Category selection</h3><p>Pick a finance task or ask an open question. The task sets the required inputs.</p></article>
        <article><SamplingFigure /><h3>Model sampling</h3><p>Two models are drawn at random from the active pool and answer the same prompt, blind.</p></article>
      </div>
    </section>

    <section className="p-ab-section p-ab-split">
      <div><PairwiseFigure /></div>
      <div>
        <h2>Pairwise ranking</h2>
        <p>Every comparison is side by side: two anonymous responses to one prompt, and you choose the one you would use. There are no scores out of ten, no rubrics to fill in, no single-answer grading.</p>
        <p>Finance is partly a matter of judgment. Which treatment is more defensible, which memo a controller would sign, which caveat matters. Pairwise preference captures that honestly. Underneath it sit truths that are not up for debate: debits equal credits, amounts tie to source, dates land in the right period. The arena keeps both. Your preference ranks the models; structured checks hold the ledger to the standard.</p>
      </div>
    </section>

    <section className="p-ab-section p-ab-why">
      <Eyebrow>Why this matters</Eyebrow>
      <h2>Finance had its spreadsheet moment. This is another one.</h2>
      <div className="p-ab-grid">
        <div><h3>Models are at the edge</h3><p>On close work, reconciliations and technical memos, frontier models are becoming proficient. Not reliably, and not everywhere, but close enough that the question has changed from whether to where.</p></div>
        <div><h3>Professionals stay in the driver’s seat</h3><p>Proficiency is not accountability. Someone still signs the workpaper, defends the treatment and answers to the auditor. The models do not replace that judgment; they raise the premium on it.</p></div>
        <div><h3>The act of calibrating</h3><p>Reading two answers to the same question and deciding which you would use is how you learn where a model is strong, where it is confidently wrong, and where your own instincts need a second look. Calibration is the craft.</p></div>
        <div><h3>Another spreadsheet moment</h3><p>Spreadsheets did not end accounting. They removed the arithmetic and expanded what one professional could reason about. This moment does the same for drafting and analysis, and the people who learn the tool first set the standard for everyone else.</p></div>
      </div>
    </section>

    <section className="p-ab-section">
      <h2>The details</h2>
      <div className="p-ab-details">
        <article>
          <span className="p-ab-icon"><Users size={18} /></span>
          <h3>Community-driven evaluation</h3>
          <p>Every ranking comes from working accountants and finance professionals who opted in to compare responses on real work. Each first, blind comparison counts once and counts equally. No curated panel, no cherry-picked prompts.</p>
          <p>Optional issue reports flag possible calculation, timing, treatment, policy or missing-fact problems. They are observations from the community, not verified correctness scores. A preferred response can still be wrong.</p>
        </article>
        <article>
          <span className="p-ab-icon"><Sigma size={18} /></span>
          <h3>Ranking calculation</h3>
          <p>Ratings are a Bradley-Terry model fit over every pairwise vote, mapped to an Elo-style scale anchored at 1200 so a 400-point gap is about a 10-to-1 preference. The 95% range on the leaderboard comes from bootstrap resampling of the votes.</p>
          <p>Only first, blind preferences count. Follow-ups after a reveal are recorded but excluded. Practice examples with authored drafts never enter the rankings. The leaderboard refreshes as votes arrive.</p>
        </article>
        <article>
          <span className="p-ab-icon"><Scale size={18} /></span>
          <h3>Technical standards</h3>
          <p>Practice cases state an explicit policy and carry structured ledger checks: debits equal credits, and accounts, dates and amounts match the stated case. Checks run on the postings themselves, never on a model’s claims about its own answer.</p>
          <p>For finance tasks, both models receive the same extracted file contents. Readable text from PDFs and values or formulas from spreadsheets are included; images are not interpreted and formulas are not recalculated. The checks do not establish overall accounting competence.</p>
        </article>
      </div>
    </section>

    <p className="p-ab-footnote">Your questions and judgments help build the rankings, with your name and account removed. The <Link to="/privacy">Privacy Policy</Link> and <Link to="/terms">Terms of Use</Link> have the details.</p>
  </div>
}
