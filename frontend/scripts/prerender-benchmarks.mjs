// Writes static, indexable HTML for every /benchmarks page plus sitemap.xml.
// The SPA still renders the live page; this gives crawlers real titles,
// descriptions and content without running JavaScript.
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..')
const DIST = join(ROOT, 'dist')
const ORIGIN = 'https://calibrationarena.ai'
const FEED = `${ORIGIN}/benchmark-feed/benchmarks.json`
const SITE = 'Calibration Arena'

// Keep in sync with benchmarkTitle/benchmarkDescription and SECTION_* in src/pilot/Benchmarks.tsx.
const AREA_WORD = { accounting: 'accounting', audit: 'audit', tax: 'tax', financial_analysis: 'finance', modeling_spreadsheets: 'financial modeling', investment_banking: 'investment banking', financial_nlp: 'financial NLP', reporting_xbrl: 'financial reporting', exams_knowledge: 'accounting exam', general_work: 'professional work' }
const DOMAINS = { accounting: 'Accounting & close', audit: 'Audit', tax: 'Tax', financial_analysis: 'Financial analysis', modeling_spreadsheets: 'Modeling & spreadsheets', investment_banking: 'Investment banking', financial_nlp: 'Financial NLP', reporting_xbrl: 'Reporting & XBRL', exams_knowledge: 'Exams & knowledge', general_work: 'General work' }
const SECTIONS = {
  '': [`Finance & Accounting AI Benchmark Leaderboards | ${SITE}`, "Which AI models lead each public accounting and finance benchmark: Vals AI, APEX-Accounting, DualEntry, TaxBench and more, in each publisher's own metric, checked daily."],
  all: [`All Finance & Accounting AI Benchmarks | ${SITE}`, 'Directory of public accounting, tax, audit and finance AI benchmarks, with data access, grading method, license and the latest published results.'],
  awaiting: [`Finance AI Benchmarks Awaiting Public Results | ${SITE}`, 'Accounting and finance AI benchmarks and products that have no public model results yet.'],
  method: [`How the Benchmark Directory Works | ${SITE}`, 'How Calibration Arena tracks publisher-owned accounting and finance AI benchmarks: checked daily, never re-run, rescaled or combined.'],
}
const title = b => `${b.name} Leaderboard · ${b.publisher} ${AREA_WORD[b.domains[0]] ?? 'finance'} benchmark | ${SITE}`
const description = b => {
  const r = b.results
  const lead = r?.leader && r.leader_score ? ` Top model: ${r.leader} (${r.leader_score}${r.metric ? ` ${r.metric.toLowerCase()}` : ''}${r.as_of ? `, ${r.as_of}` : ''}).` : ''
  return `${b.summary}${lead} Results from ${b.publisher}, linked to the source.`.slice(0, 300)
}

const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c])
const TRY = '<p><a class="p-button bm-try" href="/ask">Try it on your own task</a></p>'

// The bundled catalog decides which pages exist; the daily feed supplies newer results.
async function loadCatalog() {
  const bundled = JSON.parse(readFileSync(join(ROOT, 'public/benchmarks.json'), 'utf8'))
  let feed = null
  try {
    const res = await fetch(FEED, { signal: AbortSignal.timeout(8000) })
    if (res.ok) feed = await res.json()
  } catch { /* bundled snapshot only */ }
  if (!Array.isArray(feed?.benchmarks)) return bundled
  const fresh = new Map(feed.benchmarks.map(b => [b.id, b]))
  const feedBoards = new Map((feed.boards ?? []).map(b => [b.benchmark_id, b]))
  return {
    ...bundled,
    benchmarks: bundled.benchmarks.map(b => fresh.has(b.id) && b.results_status !== 'archived' ? { ...b, results: fresh.get(b.id).results ?? b.results } : b),
    boards: (bundled.boards ?? []).map(b => feedBoards.get(b.benchmark_id) && !b.archived ? feedBoards.get(b.benchmark_id) : b),
    models: [...new Map([...(bundled.models ?? []), ...(feed.models ?? [])].map(m => [m.id, m])).values()],
  }
}

function page(template, path, pageTitle, pageDescription, body, jsonLd) {
  const url = `${ORIGIN}${path}`
  const head = [
    `<title>${esc(pageTitle)}</title>`,
    `<meta name="description" content="${esc(pageDescription)}" />`,
    `<link rel="canonical" href="${url}" />`,
    `<meta property="og:type" content="website" />`,
    `<meta property="og:site_name" content="${SITE}" />`,
    `<meta property="og:title" content="${esc(pageTitle)}" />`,
    `<meta property="og:description" content="${esc(pageDescription)}" />`,
    `<meta property="og:url" content="${url}" />`,
    `<meta name="twitter:card" content="summary" />`,
    jsonLd ? `<script type="application/ld+json">${JSON.stringify(jsonLd).replace(/</g, '\\u003c')}</script>` : '',
  ].join('\n    ')
  let html = template
    .replace(/<title>[\s\S]*?<\/title>/, '')
    .replace(/<meta name="description"[^>]*>/, '')
    .replace('</head>', `  ${head}\n  </head>`)
    .replace('<div id="root"></div>', `<div id="root"><main class="p-workspace bm-page">${body}</main></div>`)
  const file = join(DIST, path.replace(/^\//, ''), 'index.html')
  mkdirSync(dirname(file), { recursive: true })
  writeFileSync(file, html)
}

const template = readFileSync(join(DIST, 'index.html'), 'utf8')
const catalog = await loadCatalog()
const boards = new Map((catalog.boards ?? []).map(b => [b.benchmark_id, b]))
const models = new Map((catalog.models ?? []).map(m => [m.id, m]))
const link = b => `<a href="/benchmarks/${esc(b.id)}">${esc(b.name)}</a> · ${esc(b.publisher)}`
const urls = []

const header = (h1, tagline) => `<header class="bm-intro"><h1 class="bm-title">${esc(h1)}</h1><p class="bm-tagline">${esc(tagline)}</p>${TRY}</header>`
const nav = '<nav class="bm-tabs" aria-label="Benchmark sections"><a href="/benchmarks">Leaderboards</a> <a href="/benchmarks/all">All benchmarks</a> <a href="/benchmarks/awaiting">Awaiting results</a> <a href="/benchmarks/method">Overview</a></nav>'
const intro = header('Industry Benchmarks', "Calibration Arena's pulse on accounting and financial AI benchmarks.") + nav

const withBoards = catalog.benchmarks.filter(b => boards.has(b.id))
const leaders = withBoards.map(b => `<li>${link(b)}${b.results?.leader ? `: ${esc(b.results.leader)} ${esc(b.results.leader_score ?? '')} ${esc(b.results.metric ?? '')}` : ''}</li>`).join('')
const pages = {
  '': `${intro}<section><h2>Leader on each benchmark</h2><ul>${leaders}</ul></section>`,
  all: `${intro}<section><h2>All ${catalog.benchmarks.length} benchmarks</h2><ul>${catalog.benchmarks.map(b => `<li>${link(b)}: ${esc(b.summary)}</li>`).join('')}</ul></section>`,
  awaiting: `${intro}<section><h2>Built, or claimed, but not yet published</h2><ul>${catalog.benchmarks.filter(b => ['unpublished', 'unknown'].includes(b.results_status)).map(b => `<li>${link(b)}</li>`).join('')}</ul></section>`,
  method: `${intro}<section><h2>Overview</h2><p>Each score is the publisher's own, linked to its source. Model boards are checked daily; a failed check keeps the last verified board. Scores are never re-run, rescaled or combined.</p></section>`,
}
for (const [slug, [pageTitle, pageDescription]] of Object.entries(SECTIONS)) {
  const path = slug ? `/benchmarks/${slug}` : '/benchmarks'
  page(template, path, pageTitle, pageDescription, pages[slug], slug ? null : {
    '@context': 'https://schema.org', '@type': 'CollectionPage', name: pageTitle, description: pageDescription, url: `${ORIGIN}${path}`,
    hasPart: catalog.benchmarks.map(b => ({ '@type': 'Dataset', name: b.name, url: `${ORIGIN}/benchmarks/${b.id}` })),
  })
  urls.push([path, catalog.catalog_updated])
}

for (const b of catalog.benchmarks) {
  const board = boards.get(b.id)
  const r = b.results
  const top = board ? board.entries.slice(0, 10).map((e, i) => `<li>${i + 1}. ${esc(models.get(e.model)?.name ?? e.label)}${e.config ? ` (${esc(e.config)})` : ''}: ${esc(e.scores[board.metrics[0].key])}%</li>`).join('') : ''
  const links = Object.entries(b.links).map(([k, href]) => `<a href="${esc(href)}" rel="noreferrer">${esc(k[0].toUpperCase() + k.slice(1))}</a>`).join(' ')
  const body = `<header class="bm-intro"><p class="bm-crumb"><a href="/benchmarks">Industry Benchmarks</a> / <a href="/benchmarks/all">All benchmarks</a></p>`
    + `<h1 class="bm-title">${esc(b.name)}</h1><p class="bm-tagline">${esc(b.publisher)} · ${b.domains.map(d => esc(DOMAINS[d] ?? d)).join(' · ')}</p>${TRY}</header>`
    + `<p>${esc(b.summary)}</p>`
    + (r?.leader ? `<p>Top model: ${esc(r.leader)} · ${esc(r.leader_score)} ${esc(r.metric ?? '')}${r.as_of ? ` (as of ${esc(r.as_of)})` : ''}.</p>` : '')
    + (top ? `<h2>${esc(board.metrics[0].label)} leaderboard</h2><ol>${top}</ol>` : '')
    + `<p>${esc(b.relevance_note)}</p><p>${links}</p>`
    + `<aside><h2>How do models handle your own work?</h2><p>Bring a task from your own close, reconciliation or reporting work and compare two models' answers side by side.</p>${TRY}</aside>`
  page(template, `/benchmarks/${b.id}`, title(b), description(b), body, {
    '@context': 'https://schema.org', '@type': 'Dataset', name: b.name, description: description(b), url: `${ORIGIN}/benchmarks/${b.id}`,
    creator: { '@type': 'Organization', name: b.publisher }, ...(r?.source_url ? { isBasedOn: r.source_url } : {}),
    ...(b.license ? { license: b.license } : {}), keywords: [b.publisher, `${AREA_WORD[b.domains[0]] ?? 'finance'} benchmark`, 'AI leaderboard'],
  })
  urls.push([`/benchmarks/${b.id}`, r?.as_of ?? b.last_verified])
}

urls.unshift(['/', catalog.catalog_updated])
const sitemap = `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n${urls.map(([path, lastmod]) => `  <url><loc>${ORIGIN}${path}</loc>${lastmod ? `<lastmod>${lastmod}</lastmod>` : ''}</url>`).join('\n')}\n</urlset>\n`
writeFileSync(join(DIST, 'sitemap.xml'), sitemap)
console.log(`Prerendered ${urls.length - 1} benchmark pages and sitemap.xml`)
