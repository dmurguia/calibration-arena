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
  return `<footer class="footer wrap"><div class="footer-top"><a href="/" class="footer-signature" aria-label="Calibrated Co. home"><img src="/assets/calibrated-wordmark-ink.svg" width="290" height="40" alt="Calibrated Co."></a><p>The art of better.</p><div class="footer-links"><a href="/enterprises/">For enterprises</a><a href="/training/">Our approach</a><a href="/company/">Company</a><a href="/contact/">Contact</a></div></div><div class="footer-bottom"><span>© 2026 Calibrated Co.</span><span>AI training & evaluation.</span><div><a href="/privacy/">Privacy</a><a href="/terms/">Terms</a></div></div></footer>`;
}
export function closing(
  title = "What should your<br>agent learn?",
  text = "Tell us the task. We’ll help identify the data and evaluation it needs.",
) {
  return `<section class="closing wrap"><div><h2>${title}</h2><div><p>${text}</p>${link("/contact/", "Talk to us", "button")}</div></div></section>`;
}
export function partnership() {
  return `<section class="section wrap" id="partnership">
    <div class="section-heading"><h2>How we partner.</h2></div>
    <div class="partnerships">
      <article><h3>Embedded</h3><p>We work alongside your engineers and domain experts to design tasks, review agent outputs and build training material.</p>${link('/contact/?partnership=embedded', 'Work with your team')}</article>
      <article><h3>Managed</h3><p>We build a dataset, evaluation set or environment to an agreed specification. Your team reviews the deliverable at each stage.</p>${link('/contact/?partnership=managed', 'Discuss a project')}</article>
    </div>
  </section>`;
}

export function deliverables() {
  const rows = [
    ['01', 'Training data', 'Expert demonstrations, comparisons and corrections for the tasks your agent needs to learn.'],
    ['02', 'Evaluations', 'Test cases and grading rubrics that identify errors in an agent’s answers and actions.'],
    ['03', 'RL environments', 'Workflows with tools, constraints and feedback for training agents through trial and error.'],
  ];
  return `<section class="section wrap" id="outputs"><div class="section-heading"><h2>What we build.</h2></div>
    <div class="output-list">${rows.map(([n,title,text])=>`<article class="output-row"><span class="index">${n}</span><h3>${title}</h3><div><p>${text}</p></div></article>`).join('')}</div>
  </section>`;
}

export function demo(sample, compact = false) {
  return `<section class="section wrap sample-section" id="example"><div class="section-heading">${label("An example from Calibration Arena")}<h2>Can the agent spot<br>the accounting error?</h2><p>Both entries balance. Only one follows the insurance policy.</p></div><div class="workbench" data-demo><div class="workbench-heading"><span>WORK STUDY / 001</span><span>Authored practice case</span></div><div class="workbench-body"><div class="case-brief"><p class="small-label">The assignment</p><h3>Review the insurance cutoff.</h3><p>A company pays $14,400 on March 15. Coverage starts April 1 and runs for 12 months.</p><p class="case-rule">The stated policy: no expense before coverage begins.</p><div class="case-facts"><div><span>Payment</span><strong>15 March</strong></div><div><span>Coverage begins</span><strong>01 April</strong></div><div><span>Annual premium</span><strong>$14,400</strong></div></div><p class="caption">Authored practice case from Calibration Arena. Fictional company; no live model call.</p></div><div class="case-review"><div class="draft-switch" role="group" aria-label="Choose a draft"><button type="button" data-draft="0" aria-pressed="true">Draft A</button><button type="button" data-draft="1" aria-pressed="false">Draft B</button></div><div class="draft-content" id="draft-content"><p class="small-label">March close / Draft A</p><p class="draft-conclusion">No amortization entry.<br>Coverage has not begun.</p><div class="entry-line"><span>Dr Prepaid insurance</span><span>$14,400</span></div><div class="entry-line"><span>Cr Cash</span><span>$14,400</span></div><p class="caption">Begin $1,200 monthly recognition in April.</p></div><button type="button" class="button check-button" data-check>Run case checks</button><div class="check-result" aria-live="polite" aria-atomic="true"><p>Check the posting against the stated case policy.</p></div><noscript><p>Draft A follows the stated policy. Draft B begins expense one month early. Both balance. Enable JavaScript to compare the checks.</p></noscript></div></div><div class="workbench-footer"><span>Source: Calibration Arena / insurance-cutoff</span><span>Independent accountant validation pending</span></div></div>${compact ? "" : `<div class="sample-note"><p>The checks compare the postings with the policy in the case brief.</p>${link("/training/", "About our evaluations")}</div>`}</section>`;
}
export function pageHero(kicker, title, body, extra = "") {
  return `<section class="page-hero wrap">${label(kicker)}<h1>${title}</h1><p class="lead">${body}</p>${extra}</section>`;
}
