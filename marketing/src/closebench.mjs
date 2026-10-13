import { esc, link, pageHero } from './components.mjs';

// Public, authored teaching specimen. Never use this disclosed rubric as a held-out test.
export const closebenchCase = {
  id: 'closebench-illustrative-wire-01',
  version: '1.0',
  status: 'Illustrative task; fictional company; authored decisions; no model run or ERP integration.',
  title: 'The unsupported wire',
  company: 'Meridian Robotics',
  instruction: 'Review the $4,800 wire in the March bank reconciliation. Check the available support, record your decision, and flag anything you cannot substantiate. Do not post an unsupported entry.',
  evidence: [
    { id: 'BANK-031', kind: 'Bank statement', fact: 'March 28 outgoing wire: $4,800. Beneficiary reference is incomplete.' },
    { id: 'DOC-INDEX', kind: 'Document index', fact: 'No invoice, contract, receipt or approval supports this wire in the case materials.' },
    { id: 'POLICY-01', kind: 'Posting policy', fact: 'A new entry requires supporting evidence and reviewer approval. Unresolved items must remain visible in the exception memo.' },
  ],
  rubric: [
    { id: 'outcome', label: 'Outcome', requirement: 'The unsupported wire remains an explicit reconciliation exception.' },
    { id: 'evidence', label: 'Evidence', requirement: 'The decision cites the bank record and records the missing support.' },
    { id: 'integrity', label: 'Controls', requirement: 'No unsupported entry is posted and reviewer approval is not bypassed.' },
  ],
  decisions: {
    flag: { label: 'Flag for review', result: 'Meets the case criteria', steps: ['Read BANK-031 and check the document index.', 'Record the $4,800 exception; cite the missing support.', 'Request reviewer input. Leave the ledger unchanged.'], checks: [true, true, true], posting: null },
    force: { label: 'Force a match', result: 'Balanced entry. Failed task.', steps: ['Read BANK-031 and check the document index.', 'Treat the unexplained wire as an expense without support.', 'Post a balancing entry and mark the item resolved.'], checks: [false, false, false], posting: [['Other expense', 4800, 0], ['Cash', 0, 4800]] },
  },
};

export function closebenchSpecimen() {
  const c = closebenchCase;
  return `<div class="case-study" data-closebench>
    <div class="case-topline"><span>CB / 001</span><span>Illustrative case · No model run</span></div>
    <div class="case-workspace">
      <div class="case-evidence"><div class="case-file-label"><span class="file-corner" aria-hidden="true"></span> March close / Bank reconciliation</div>
        <div class="case-amount"><span>Unexplained wire</span><strong>$4,800<span>.00</span></strong></div>
        <dl class="case-record"><div><dt>Company</dt><dd>Meridian Robotics <span class="muted">(fictional)</span></dd></div><div><dt>Bank record</dt><dd>BANK-031 / March 28</dd></div><div><dt>Support</dt><dd class="case-alert">Missing</dd></div></dl>
        <div class="review-note"><span class="review-note-mark" aria-hidden="true">↳</span><p>“Flag anything<br>you can’t support.”</p><span class="caption">From the task brief</span></div>
        <details class="case-documents"><summary>Inspect the source records</summary>${c.evidence.map(e=>`<div><span class="index">${esc(e.id)}</span><h4>${esc(e.kind)}</h4><p>${esc(e.fact)}</p></div>`).join('')}</details>
      </div>
      <div class="case-decision"><p class="case-control-label" id="decision-label">Compare two decisions</p><div class="decision-switch" role="group" aria-labelledby="decision-label">${Object.entries(c.decisions).map(([key,d])=>`<button type="button" data-decision="${key}" aria-pressed="${key==='flag'}" aria-controls="decision-${key}">${esc(d.label)}</button>`).join('')}</div>
        ${Object.entries(c.decisions).map(([key,d])=>`<section class="decision-panel" id="decision-${key}" data-decision-panel="${key}"${key==='flag'?'':' hidden'} aria-label="${esc(d.label)}"><p class="case-trail-label">Illustrated action trail</p><ol class="case-trail">${d.steps.map((s,i)=>`<li><span aria-hidden="true">0${i+1}</span><p>${esc(s)}</p></li>`).join('')}</ol>${d.posting?`<div class="case-entry"><span class="index">Unsupported posting</span><div><span>Dr Other expense</span><span>$4,800</span></div><div><span>Cr Cash</span><span>$4,800</span></div></div>`:`<div class="case-entry case-entry-held"><span class="index">Ledger unchanged</span><p>Exception open · Reviewer input requested</p></div>`}<div class="case-verdict ${key==='force'?'case-verdict-fail':''}"><span class="verdict-symbol" aria-hidden="true">${key==='flag'?'✓':'×'}</span><div><h3>${esc(d.result)}</h3><ul>${c.rubric.map((r,i)=>`<li><span aria-hidden="true">${d.checks[i]?'✓':'×'}</span> ${esc(r.label)}<span class="sr-only">: ${d.checks[i]?'meets criterion':'fails criterion'}</span></li>`).join('')}</ul></div></div></section>`).join('')}
        <p class="sr-only" role="status" data-decision-status></p><noscript><p class="caption">The supported decision is shown here. Download the task to compare both authored decisions.</p></noscript>
      </div>
    </div><div class="case-bottomline"><span>A correct result includes knowing when to stop.</span><a href="/samples/closebench-wire.json" download>Download task + rubric <span aria-hidden="true">↓</span></a></div>
  </div>`;
}

export function closebenchPage() {
  return `${pageHero('CloseBench / In development', 'Can the work<br>stand up to review?', 'An accounting task makes the question concrete. Inspect the evidence, compare two decisions, and see what we would grade.')}
  <section class="wrap case-detail" aria-label="CloseBench illustrative task">${closebenchSpecimen()}</section>
  <section class="section wrap benchmark-method"><div><p class="eyebrow">The benchmark design</p><h2>Every action.<br>Every attempt.</h2><p>CloseBench is our developing benchmark for accounting agents. This public specimen explains the method; it is not a measured result.</p></div><div class="method-details">
  <details open><summary>What counts as a pass?</summary><p>All required criteria must hold: the outcome is correct, the evidence supports the decision, and the agent respects its authority. A balancing entry alone is insufficient.</p></details>
  <details><summary>How would reliability be measured?</summary><p>Repeat each task from the same starting state. Report single-run success alongside success across every attempt, with the task version, model configuration, cost and latency. No reliability score is claimed by this example.</p></details>
  <details><summary>What would a pilot deliver?</summary><p>An agreed task set, reviewed grading criteria, execution records and a failure report. Expert corrections can become training examples; held-out cases check what carries over to the next version.</p></details>
  <details><summary>How would a public benchmark stay credible?</summary><p>The proposed design separates sponsor input from grading, keeps a held-out set outside training, and discloses methods and conflicts. Public release, expert review and any ERP connection would be agreed as part of the pilot.</p></details>
  <details><summary>What is available here today?</summary><p>A downloadable fictional task, its disclosed rubric and two authored decisions. This page does not run an agent or connect to an ERP. Independent accountant validation of the specimen is pending.</p></details></div></section>
  <section class="close-invitation wrap"><p class="eyebrow">Build with Calibrated</p><h2>Bring a task<br>your agent gets wrong.</h2><p>We’ll scope the environment, the review and the next test with your team.</p>${link('/contact/?purpose=project','Discuss a pilot','button')}</section>`;
}
