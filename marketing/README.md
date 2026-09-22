# Calibrated Co. marketing site

An independent company website inside the Calibration Arena repository. The accounting app and backend remain separate. No runtime API, npm dependency, Gateway credential or database is needed to preview the site.

## Start

Requires Node **22.18 or newer**. From the repository root:

```bash
cd marketing
npm run dev
```

- Site: [http://127.0.0.1:4317/](http://127.0.0.1:4317/)
- Original JEV results: [http://127.0.0.1:4317/review/](http://127.0.0.1:4317/review/)
- Craft: [http://127.0.0.1:4317/directions/craft/](http://127.0.0.1:4317/directions/craft/)
- Outcomes: [http://127.0.0.1:4317/directions/outcomes/](http://127.0.0.1:4317/directions/outcomes/)

The server binds only to `127.0.0.1`. If the port is occupied, run `PORT=4318 npm run dev`. Stop this server with Ctrl-C in its terminal. It does not need either Arena service to run.

`npm run dev` builds once and serves the result. After an edit, run `npm run build` in another terminal and refresh the browser. `npm run preview` serves an existing build. There is intentionally no separate dependency installation or background build watcher.

## Review the work

- [Structure, reference analysis and copy decisions](research/STRUCTURE-AND-COPY.md)
- [JEV result, limitations and recommendation](evaluation/REPORT.md)
- [Local verification](QA.md)
- [Approved identity](../brand/calibrated/DESIGN-BRIEF.md)

The default homepage has been rewritten after founder feedback. It opens with “Hone your agents,” names the three services, presents the company-expertise/open-weight-model thesis and includes the graphite hero artwork. Both variations share the same supporting structure. The original JEV results remain available for audit and do not evaluate the revised site. See [the copy review](research/COPY-REVIEW.md).

## Files

```text
marketing/
  src/                 Shared layout, page copy, config, authored sample
  public/              CSS, browser interactions, licensed brand assets
  scripts/             Static build, local server, tests, JEV runner
  research/            Source analysis and proposed information architecture
  evaluation/          Exact JEV inputs, typed results and interpretation
  dist/                Generated static site (ignored)
```

Edit copy in `src/pages.mjs` and shared sections in `src/components.mjs`. Change `defaultDirection` in `src/config.mjs` to `craft` or `outcomes`. CSS lives in `public/styles.css`. The build renders complete HTML for every route, so search crawlers and visitors do not need JavaScript to read the pages. JavaScript enhances navigation and the brief form.

## What works now

Twelve pages, responsive navigation, desktop and phone layouts, direct routes, keyboard controls, native FAQ disclosure, and an illustrative knowledge-work workflow. The brief form can prepare, copy and download text without saving or sending it. The data entry point is an intentional placeholder for the future offering. The leaderboard states that no validated public rankings are connected.

The knowledge-work example is an illustrative support workflow, not a live model run or measured result. Historical fixture code remains in the repository but is no longer rendered by the marketing site. Team backgrounds (Stanford, MIT and Verkada) and systems expertise were supplied by the founder; they do not represent vendor or institutional endorsements.

Local webfonts, OFL notices, SVG identity assets and existing generated brand studies are bundled. The share image is a 1200 × 630 PNG with an outlined SVG source. `scripts/generate-share.py` regenerates the SVG with `fonttools`; use a standard SVG renderer such as Sharp for the PNG. These tools are not required to build the site.

## Configuration and launch boundary

Copy `.env.example` to `.env.local` if you need configuration. The file is ignored. The website supports only these non-secret build-time settings:

| Setting | Purpose |
| --- | --- |
| `CONTACT_URL` | Confirmed HTTPS booking/contact URL or `mailto:` address. Adds a real direct-contact route while retaining the local brief. |
| `ARENA_URL` | Verified public Arena URL. If blank, the leaderboard links to the local practice example. |
| `SITE_URL` | Canonical domain. Defaults to `https://calibrated.co`. |
| `PUBLIC_LAUNCH` | Defaults to `0`, so every page is noindex and robots disallows indexing. |
| `LEGAL_REVIEWED` | Set to `1` only after the preview privacy/terms copy has been updated for the operator and actual hosting. |

**Before hosting for customers:** confirm the contact destination; finish operator/contact and hosting details in the two legal drafts; approve the exact public commercial copy; connect the Arena only if its public route is verified. A public build requires both `CONTACT_URL` and `LEGAL_REVIEWED=1`. Changing a flag does not itself complete legal review.

Build output is `marketing/dist`. A future host can use repository root directory `marketing`, build command `npm run build`, and output directory `dist`. It needs ordinary directory-index routing and the supplied `404.html`; there is no SPA rewrite to the Arena. Keep `/review/` and `/directions/` private or remove them from the public artifact. No actual hosting project, deployment or DNS change was made.

The local server sends a restrictive content-security policy, no-sniff and referrer-policy headers. Apply equivalent headers on the chosen public host. The site has no analytics, third-party font request, API endpoint or tracking cookie. Adding those requires changing the privacy notice and testing the real integration.

The provided DNS screenshot shows Porkbun parking records. It is context, not a verified current DNS audit or an instruction to edit records. Configure DNS only after choosing and approving the host.

## Verify

```bash
npm test
npm run build
```

Tests cover fixture/check agreement, policy errors that still balance, order independence, contact URL protocols, brief behavior, and every page's internal links, fragments and local assets. Browser verification is documented in `QA.md`.

## Repeat the JEV evaluation

The evaluator is a separate local script. It sends the marketing copy and rubric through the existing Gateway. It never bundles credentials into the website.

Use an existing AI SDK installation with `ai@7.0.107` and its ignored credential file:

```bash
GATEWAY_PROJECT_DIR='/path/to/existing/gateway-project' \
GATEWAY_ENV_FILE='/path/to/existing/gateway-project/.env.local' \
npm run evaluate
```

Alternatively install `ai@7.0.107` in this project without saving credentials and set `AI_GATEWAY_API_KEY` only in the evaluator's environment. The site build never reads that key. No key value is printed or saved. Input hashes let unchanged completed runs be reused; changed copy triggers new live requests. Each of the two sequential requests has a bounded timeout and one retry. Failures are recorded without credential-bearing error text.

Do not interpret the resulting probabilities as purchase likelihoods. Review the full [evaluation report](evaluation/REPORT.md), including the substantial order sensitivity outside the enterprise-buyer persona.
