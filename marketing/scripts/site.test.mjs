import test from "node:test";
import assert from "node:assert/strict";
import { readFile, stat, access } from "node:fs/promises";
import path from "node:path";
import { build, root } from "./build.mjs";
import { evaluateDraft, projectBrief } from "../public/demo-core.mjs";
import { validatedDestination } from "../src/config.mjs";
const sample = JSON.parse(
  await readFile(path.join(root, "src/sample.json"), "utf8"),
);

test("sample checks match repository fixture results, including the balanced cutoff error", () => {
  for (const draft of sample.drafts) {
    const result = evaluateDraft(draft);
    assert.equal(result.balanced, draft.checks[0].passed);
    assert.equal(result.policyMatch, draft.checks[1].passed);
  }
  assert.deepEqual(evaluateDraft(sample.drafts[1]), {
    balanced: true,
    policyMatch: false,
  });
  const unbalanced = structuredClone(sample.drafts[0]);
  unbalanced.postings[0][2] += 1;
  assert.equal(evaluateDraft(unbalanced).balanced, false);
});
test("checks are order-independent and do not mutate the authored fixtures", () => {
  const copy = structuredClone(sample.drafts[0]);
  copy.postings.reverse();
  assert.deepEqual(evaluateDraft(copy), { balanced: true, policyMatch: true });
  const before = JSON.stringify(copy);
  evaluateDraft(copy);
  assert.equal(JSON.stringify(copy), before);
});
test("contact configuration only allows intended public protocols", () => {
  assert.throws(() =>
    validatedDestination("javascript:alert(1)", "CONTACT_URL", true),
  );
  assert.throws(() =>
    validatedDestination("http://example.com", "CONTACT_URL", true),
  );
  assert.equal(
    validatedDestination("https://example.com/contact", "CONTACT_URL", true),
    "https://example.com/contact",
  );
  assert.equal(
    validatedDestination("mailto:hello@example.com", "CONTACT_URL", true),
    "mailto:hello@example.com",
  );
});
test("brief has useful content and never implies submission", () => {
  const brief = projectBrief({
    workflow: "Review month-end close",
    standard: "Check source dates",
  });
  assert.match(brief, /Review month-end close/);
  assert.match(brief, /has not been sent/);
});
test("all pages render without JS; internal links, fragments, assets and safety boundaries are valid", async () => {
  const routes = await build();
  for (const [route] of routes) {
    const html = await readFile(
      path.join(root, "dist", route, "index.html"),
      "utf8",
    );
    assert.equal(
      (html.match(/<h1[ >]/g) || []).length,
      1,
      route + " should have one H1",
    );
    assert.match(html, /<main id="main">/);
    assert.match(html, /class="no-js"/);
    assert.match(html, /noindex/);
    assert.doesNotMatch(
      html,
      /https?:\/\/[^"\s]+\.(?:woff2|js|css)/,
      "no external font or script dependency",
    );
    assert.doesNotMatch(html, /[—]|lucide|Inter,|Geist/);
    for (const match of html.matchAll(/(?:href|src)="([^"\s]+)"/g)) {
      const value = match[1];
      if (!value.startsWith("/") && !value.startsWith("#")) continue;
      const url = new URL(value, "https://local" + route);
      const pathname = url.pathname;
      const target = path.join(
        root,
        "dist",
        pathname,
        pathname.endsWith("/") ? "index.html" : "",
      );
      assert.ok((await stat(target)).isFile(), route + " -> " + value);
      if (url.hash) {
        const dest = await readFile(target, "utf8");
        assert.ok(
          dest.includes(`id="${url.hash.slice(1)}"`),
          route + " missing " + value,
        );
      }
    }
    if (route.startsWith("/directions/"))
      assert.match(html, /noindex, nofollow/);
    if (html.includes("data-demo"))
      assert.match(html, /authored practice case/i);
    if (route === '/contact/') assert.match(html, /type="submit" disabled data-enhance/);
  }
  const sharingImage = await readFile(path.join(root, 'dist/assets/share-card.png'));
  assert.equal(sharingImage.readUInt32BE(16), 1200);
  assert.equal(sharingImage.readUInt32BE(20), 630);
});


test("deployment contains the current branded site and excludes internal review artifacts", async () => {
  const previousContact = process.env.CONTACT_URL;
  process.env.CONTACT_URL = "mailto:david@corsac.ai";
  try {
    const routes = await build({ includeReview: false });
    assert.equal(routes.length, 9);
    const home = await readFile(path.join(root, "dist/index.html"), "utf8");
    assert.match(home, /Hone your agents/);
    assert.match(home, /assets\/calibrated-wordmark-ink.svg/);
    assert.match(home, /assets\/open-sketch.webp/);
    assert.match(await readFile(path.join(root, "dist/contact/index.html"), "utf8"), /mailto:david@corsac.ai/);
    for (const entry of ["review", "directions", "reports", "research", ".env.local"]) {
      await assert.rejects(access(path.join(root, "dist", entry)), { code: "ENOENT" });
    }
    const sitemap = await readFile(path.join(root, "dist/sitemap.xml"), "utf8");
    assert.doesNotMatch(sitemap, /\/(review|directions|reports)\//);
  } finally {
    if (previousContact === undefined) delete process.env.CONTACT_URL;
    else process.env.CONTACT_URL = previousContact;
  }
});
