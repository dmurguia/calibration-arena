export const esc = (value) =>
  String(value).replace(
    /[&<>"']/g,
    (char) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        char
      ],
  );
export const label = (text) => `<p class="eyebrow">${text}</p>`;
export const link = (href, text, style = "text-link") =>
  `<a class="${style}" href="${esc(href)}">${text}${style === "text-link" ? '<span aria-hidden="true">↗</span>' : ""}</a>`;
export const actions = (
  primary = "Discuss a project",
  secondary = "See the approach",
  secondHref = "/training/",
) =>
  `<div class="actions">${link("/contact/", primary, "button")}${link(secondHref, secondary, "button button-quiet")}</div>`;

export function header(active = "") {
  const nav = [
    ["/enterprises/", "For enterprises"],
    ["/training/", "Our approach"],
    ["/leaderboard/", "Leaderboard"],
    ["/company/", "Company"],
  ];
  return `<a class="skip" href="#main">Skip to content</a><header class="header wrap"><a class="identity" href="/" aria-label="Calibrated Co. home"><span class="mark"><img src="/assets/calibrated-mark-paper.svg" width="32" height="32" alt=""></span><img class="wordmark" src="/assets/calibrated-wordmark-ink.svg" alt="Calibrated Co." width="173" height="24"></a><button class="menu-toggle" type="button" aria-expanded="false" aria-controls="navigation">Menu <span aria-hidden="true">+</span></button><nav id="navigation" aria-label="Main navigation">${nav.map(([url, title]) => `<a href="${url}"${url === active ? ' aria-current="page"' : ""}>${title}</a>`).join("")}${link("/get-data/", "Get data", "button nav-cta")}</nav></header>`;
}
export function footer() {
  return `<footer class="footer wrap"><div class="footer-top"><a href="/" class="footer-signature" aria-label="Calibrated Co. home"><img src="/assets/calibrated-wordmark-ink.svg" width="290" height="40" alt="Calibrated Co."></a><p>The art of better.</p><div class="footer-links"><a href="/enterprises/">For enterprises</a><a href="/training/">Our approach</a><a href="/company/">Company</a><a href="/contact/">Contact</a></div></div><div class="footer-bottom"><span>© 2026 Calibrated Co.</span><span>Expert judgment. Practiced intelligence.</span><div><a href="/privacy/">Privacy</a><a href="/terms/">Terms</a></div></div></footer>`;
}
export function closing(
  title = "Bring us the work.<br>Let’s make it better.",
  text = "Start with a workflow, a difficult failure, or a standard your agent needs to meet.",
) {
  return `<section class="closing wrap">${label("A good place to begin")}<div><h2>${title}</h2><div><p>${text}</p>${link("/contact/", "Discuss a project", "button")}</div></div></section>`;
}
export function partnership() {
  return `<section class="section wrap" id="partnership"><div class="section-heading">${label("How we partner")}<h2>Close to the work.<br>Built around your team.</h2></div><div class="partnerships"><article><span class="index">01 / Embedded</span><h3>Work at the same table.</h3><p>We shape the evaluation, tasks and feedback alongside your engineers and domain experts. Your team stays close to the decisions that define quality.</p><p class="detail">For teams building their own training loop.</p>${link("/contact/?partnership=embedded", "Explore an embedded project")}</article><article><span class="index">02 / Managed</span><h3>A defined body of work.</h3><p>Agree on the workflow, acceptance criteria and handoff. We scope the task set, evaluation materials or environment work, with review points along the way.</p><p class="detail">For teams that need a focused deliverable.</p>${link("/contact/?partnership=managed", "Scope a managed project")}</article></div></section>`;
}
export function deliverables() {
  const rows = [
    [
      "01",
      "A standard you can test.",
      "Expert-led evaluations",
      "Tasks and grading criteria that make professional judgment explicit. See where an agent falls short, and what a good result requires.",
    ],
    [
      "02",
      "Examples worth learning from.",
      "Training data & feedback",
      "Demonstrations, comparisons and corrections shaped around the work. A record of the decisions that distinguish a usable answer from a convincing one.",
    ],
    [
      "03",
      "A place to practice.",
      "Environments for reinforcement learning",
      "Scoped workflows with tools, constraints and feedback. Give agents a repeatable setting in which to attempt the work and learn from the result.",
    ],
    [
      "04",
      "A record of what changed.",
      "Evaluation across iterations",
      "Compare a new version against the same tasks and criteria. Keep the evidence that supports a change, including the failures that remain.",
    ],
  ];
  return `<section class="section wrap" id="outputs"><div class="section-heading">${label("What we build")}<h2>The ingredients<br>of better work.</h2><p>Start with the part your agent needs.<br>Scope the output around a real workflow.</p></div><div class="output-list">${rows.map(([n, title, type, text]) => `<article class="output-row"><span class="index">${n}</span><h3>${title}</h3><div><p class="small-label">${type}</p><p>${text}</p></div></article>`).join("")}</div></section>`;
}
export function demo(sample, compact = false) {
  return `<section class="section wrap sample-section" id="example"><div class="section-heading">${label("An example from Calibration Arena")}<h2>The numbers balance.<br>The judgment still matters.</h2><p>One small case shows why a correct-looking answer needs a standard behind it.</p></div><div class="workbench" data-demo><div class="workbench-heading"><span>WORK STUDY / 001</span><span>Authored practice case</span></div><div class="workbench-body"><div class="case-brief"><p class="small-label">The assignment</p><h3>Review the insurance cutoff.</h3><p>A company pays $14,400 on March 15. Coverage starts April 1 and runs for 12 months.</p><p class="case-rule">The stated policy: no expense before coverage begins.</p><div class="case-facts"><div><span>Payment</span><strong>15 March</strong></div><div><span>Coverage begins</span><strong>01 April</strong></div><div><span>Annual premium</span><strong>$14,400</strong></div></div><p class="caption">Fictional company. Fixed authored drafts. This is an interactive excerpt of the Arena’s practice case, not a live model run or a published benchmark.</p></div><div class="case-review"><div class="draft-switch" role="group" aria-label="Choose a draft"><button type="button" data-draft="0" aria-pressed="true">Draft A</button><button type="button" data-draft="1" aria-pressed="false">Draft B</button></div><div class="draft-content" id="draft-content"><p class="small-label">March close / Draft A</p><p class="draft-conclusion">No amortization entry.<br>Coverage has not begun.</p><div class="entry-line"><span>Dr Prepaid insurance</span><span>$14,400</span></div><div class="entry-line"><span>Cr Cash</span><span>$14,400</span></div><p class="caption">Begin $1,200 monthly recognition in April.</p></div><button type="button" class="button check-button" data-check>Run case checks</button><div class="check-result" aria-live="polite" aria-atomic="true"><p>Check the posting against the stated case policy.</p></div><noscript><p>Draft A follows the stated policy. Draft B begins expense one month early. Both balance. Enable JavaScript to compare the checks.</p></noscript></div></div><div class="workbench-footer"><span>Source: Calibration Arena / insurance-cutoff</span><span>Independent accountant validation pending</span></div></div>${compact ? "" : `<div class="sample-note"><p>A useful evaluation separates arithmetic, policy and professional preference. The example checks structured postings; it does not grade an answer by how confidently it is written.</p>${link("/training/", "See how the pieces fit")}</div>`}</section>`;
}
export function pageHero(kicker, title, body, extra = "") {
  return `<section class="page-hero wrap">${label(kicker)}<h1>${title}</h1><p class="lead">${body}</p>${extra}</section>`;
}
