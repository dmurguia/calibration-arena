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
  return `<a class="skip" href="#main">Skip to content</a><header class="header wrap"><a class="identity" href="/" aria-label="Calibrated Co. home"><span class="mark"><img src="/assets/calibrated-mark-ink.svg" width="32" height="32" alt=""></span><img class="wordmark" src="/assets/calibrated-wordmark-ink.svg" alt="Calibrated Co." width="173" height="24"></a><button class="menu-toggle" type="button" aria-expanded="false" aria-controls="navigation">Menu <span aria-hidden="true">+</span></button><nav id="navigation" aria-label="Main navigation">${nav.map(([url, title]) => `<a href="${url}"${url === active ? ' aria-current="page"' : ""}>${title}</a>`).join("")}${link("/get-data/", "Get data", "button nav-cta")}</nav></header>`;
}
export function footer() {
  return `<footer class="footer wrap"><div class="footer-top"><a href="/" class="footer-signature" aria-label="Calibrated Co. home"><img src="/assets/calibrated-wordmark-ink.svg" width="290" height="40" alt="Calibrated Co."></a><div class="footer-links"><a href="/enterprises/">For enterprises</a><a href="/training/">Our approach</a><a href="/company/">Company</a><a href="/contact/">Contact</a></div></div><div class="footer-bottom"><span>© 2026 Calibrated Co.</span><div><a href="/privacy/">Privacy</a><a href="/terms/">Terms</a></div></div></footer>`;
}
export function closing(
  title = "Build your<br>best agent.",
  text = "Bring your expertise. Let’s put it to work in your models.",
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

export function systems() {
  const names = ['SAP', 'Snowflake', 'Databricks', 'Google Cloud', 'GitHub', 'Notion'];
  return `<section class="systems-band"><div class="wrap"><h2>We improve agents working in the systems you use.</h2><ul class="systems-list" aria-label="Systems expertise">${names.map(name => `<li>${name}</li>`).join('')}</ul></div></section>`;
}

// Mount point for public/calibrated-hero.mjs, enhanced by site.mjs. The static sketch is the
// no-JS view and covers the panel until the canvas is ready. styles.css reserves the scroll
// track height (.cal-hero-mount) so mounting causes no layout shift; keep it in sync with
// panelHeight, scrollLength and the module's 480px minHeight.
export const heroOptions = {
  image: "/assets/open-sketch.webp",
  driver: "scroll",
  panelHeight: 70,
  scrollLength: 230,
  trace: 4,
};
export function calibratedHero(options = heroOptions) {
  return `<div class="cal-hero-mount" data-calibrated-hero="${esc(JSON.stringify(options))}"><div class="cal-hero-fallback"><div class="cal-hero-panel"><img src="${esc(options.image)}" width="1536" height="1024" fetchpriority="high" alt="An open graphite sketch of flowing lines on paper, from the Calibrated brand study."></div></div></div>`;
}

export function pageHero(kicker, title, body, extra = "") {
  return `<section class="page-hero wrap">${label(kicker)}<h1>${title}</h1><p class="lead">${body}</p>${extra}</section>`;
}
