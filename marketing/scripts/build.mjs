import { readFile, writeFile, mkdir, cp, rm } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { site, validatedDestination } from "../src/config.mjs";
import { header, footer, esc } from "../src/components.mjs";
import * as pages from "../src/pages.mjs";

export const root = fileURLToPath(new URL("..", import.meta.url));
export async function build() {
  const config = {
    siteUrl: validatedDestination(
      process.env.SITE_URL || "https://calibrated.co",
      "SITE_URL",
    ),
    contactUrl: validatedDestination(
      process.env.CONTACT_URL,
      "CONTACT_URL",
      true,
    ),
    arenaUrl: validatedDestination(process.env.ARENA_URL, "ARENA_URL"),
    publicLaunch: process.env.PUBLIC_LAUNCH === "1",
  };
  if (
    config.publicLaunch &&
    (!config.contactUrl || process.env.LEGAL_REVIEWED !== "1")
  )
    throw new Error(
      "Public launch requires CONTACT_URL and LEGAL_REVIEWED=1 after updating the draft notices. See README.md.",
    );
  const sample = JSON.parse(
    await readFile(path.join(root, "src/sample.json"), "utf8"),
  );
  const originalJevResults = await Promise.all([1, 2].map(async number =>
    JSON.parse(await readFile(path.join(root, `evaluation/run-${number}-result.json`), 'utf8'))
  ));
  const routes = [
    [
      "/",
      site.defaultDirection === "craft"
        ? "Your expertise. Better agents"
        : "Hone your agents",
      site.defaultDirection === "craft"
        ? pages.homeCraft(sample)
        : pages.homeOutcomes(sample),
      "home",
    ],
    [
      "/directions/craft/",
      "Your expertise. Better agents",
      pages.homeCraft(sample),
      "craft",
    ],
    [
      "/directions/outcomes/",
      "Hone your agents",
      pages.homeOutcomes(sample),
      "outcomes",
    ],
    ["/enterprises/", "For enterprises", pages.enterprisePage(), "enterprises"],
    ["/training/", "Our approach", pages.trainingPage(sample), "training"],
    ["/company/", "The company", pages.companyPage(), "company"],
    [
      "/leaderboard/",
      "Leaderboard",
      pages.leaderboardPage(config),
      "leaderboard",
    ],
    ["/get-data/", "Get data", pages.dataPage(), "data"],
    ["/contact/", "Discuss a project", pages.contactPage(config), "contact"],
    [
      "/privacy/",
      "Privacy notice",
      pages.legalPage("privacy", config),
      "privacy",
    ],
    ["/terms/", "Website terms", pages.legalPage("terms", config), "terms"],
    ["/review/", "Original JEV results", pages.reviewPage(originalJevResults), "review"],
  ];
  const out = path.join(root, "dist");
  await rm(out, { recursive: true, force: true });
  await mkdir(out, { recursive: true });
  await cp(path.join(root, "public"), out, { recursive: true });
  await mkdir(path.join(out, 'reports'), { recursive: true });
  await Promise.all(originalJevResults.map((result,index) => writeFile(
    path.join(out, 'reports', `jev-run-${index+1}.json`), JSON.stringify(result,null,2)+'\n'
  )));
  const descriptions = {
    enterprises:
      "Training data, evaluations and reinforcement learning environments for your enterprise agents.",
    training:
      "See how company expertise becomes training tasks, feedback and evaluations for knowledge-work agents.",
    company:
      "Our belief: companies will own their knowledge work through open-weight models shaped by their expertise.",
    leaderboard:
      "Knowledge-work model comparisons: publication status and evaluation criteria.",
    data: "Discuss training data and evaluation tasks shaped around professional workflows.",
    contact:
      "Prepare a project brief for Calibrated: the workflow, your quality standard and the way your team wants to work.",
    privacy:
      "How the Calibrated marketing preview handles information, project briefs and local interactions.",
    terms:
      "Preview terms for the Calibrated Co. marketing website and authored practice case.",
  };
  for (const [route, title, content, id] of routes) {
    const isPrivate = route.startsWith("/directions/") || route === "/review/";
    const noindex = isPrivate || !config.publicLaunch;
    const canonical = new URL(isPrivate ? "/" : route, config.siteUrl).href;
    const description = descriptions[id] || site.description;
    const html = `<!doctype html>
<html lang="en" class="no-js"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(title)} | Calibrated Co.</title><meta name="description" content="${esc(description)}"><meta name="robots" content="${noindex ? "noindex, nofollow" : "index, follow"}"><meta name="theme-color" content="#F4F1E9"><link rel="canonical" href="${esc(canonical)}"><meta property="og:type" content="website"><meta property="og:site_name" content="Calibrated Co."><meta property="og:title" content="${esc(title)} | Calibrated Co."><meta property="og:description" content="${esc(description)}"><meta property="og:url" content="${esc(canonical)}"><meta property="og:image" content="${esc(new URL("/assets/share-card.png", config.siteUrl).href)}"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630"><meta name="twitter:card" content="summary_large_image"><link rel="icon" type="image/svg+xml" href="/assets/calibrated-favicon.svg"><link rel="preload" href="/assets/IBMPlexSans-400.woff2" as="font" type="font/woff2" crossorigin><link rel="stylesheet" href="/styles.css"><script type="module" src="/site.mjs"></script></head><body data-page="${id}">${header(route)}<main id="main">${content}</main>${footer()}${content.includes("data-demo") ? `<script type="application/json" id="sample-data">${JSON.stringify(sample).replace(/</g, "\\u003c")}</script>` : ""}</body></html>`;
    const directory = path.join(out, route);
    await mkdir(directory, { recursive: true });
    await writeFile(path.join(directory, "index.html"), html);
  }
  const notFound = `<!doctype html><html lang="en" class="no-js"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex"><title>Page not found | Calibrated Co.</title><link rel="stylesheet" href="/styles.css"></head><body>${header()}<main id="main"><section class="page-hero wrap"><p class="eyebrow">404</p><h1>This page is<br>still a blank sheet.</h1><p class="lead">The address does not point to a page on this site.</p><div class="actions"><a class="button" href="/">Return to Calibrated</a></div></section></main>${footer()}<script type="module" src="/site.mjs"></script></body></html>`;
  await writeFile(path.join(out, "404.html"), notFound);
  await writeFile(
    path.join(out, "robots.txt"),
    config.publicLaunch
      ? `User-agent: *\nDisallow: /review/\nDisallow: /directions/\nSitemap: ${new URL("/sitemap.xml", config.siteUrl).href}\n`
      : "User-agent: *\nDisallow: /\n",
  );
  const publicRoutes = routes.filter(
    ([route]) => !route.startsWith("/directions/") && route !== "/review/",
  );
  await writeFile(
    path.join(out, "sitemap.xml"),
    `<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${publicRoutes.map(([route]) => `<url><loc>${esc(new URL(route, config.siteUrl).href)}</loc></url>`).join("")}</urlset>`,
  );
  await writeFile(
    path.join(root, "evaluation/route-manifest.json"),
    JSON.stringify(
      routes.map(([route, title, , id]) => ({ route, title, id })),
      null,
      2,
    ) + "\n",
  );
  console.log(
    `Built ${routes.length} pages in marketing/dist (${config.publicLaunch ? "public" : "preview, noindex"}).`,
  );
  return routes;
}
if (
  process.argv[1] &&
  path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)
)
  await build();
