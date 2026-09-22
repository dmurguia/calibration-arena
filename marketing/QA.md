# Local verification

Verified 22 September 2026 on the separate `codex/calibrated-company-site` worktree. This records local website and integration checks, not a public deployment, recruited-persona study or model-performance benchmark.

## Copy cleanup verification

The founder-requested second pass shortened the Outcomes homepage from 574 to 181 main-content words (68%). The hero now names AI training and shows the approved graphite artwork. Supporting service pages were also shortened. The interactive case now lives on `/training/#example`.

All 12 routes were rechecked at 320, 390, 768 and 1280 pixels after the rewrite: 48 checks with no document overflow or broken images. Desktop and phone hero layouts were visually reviewed. The five automated test groups pass. Original JEV probabilities and raw response downloads are displayed on `/review/`; those results apply to the old drafts. No new model evaluation was run for this rewrite.

The moved demo was checked in the browser: Draft A passes both checks; Draft B balances but fails the policy check with the early-expense explanation. The run-1 disclosure opens and displays the complete saved response. The temporary browser viewport was reset.

## Original build and functional checks

- Static build renders **12 pages**, plus a dedicated 404, robots file and sitemap. The marketing site needs no application backend or runtime API key.
- **5 automated test groups pass**: fixture and computed-check agreement, check order independence, contact-protocol validation, project-brief behavior, and full-page/link/fragment/asset validation.
- Draft A passes both checks. Draft B balances but fails the date/account/amount match against the stated case policy. An intentionally unbalanced test posting fails the balancing check.
- All pages have one H1, a main landmark, a skip link, a local font/asset path, and preview noindex metadata. The share PNG is exactly **1200 × 630**.
- Direct local HTTP checks return 200 for the home, enterprise, approach and share-image routes. An unknown page returns an actual 404.
- No application, participant database, real provider run, published ranking or customer record is modified by the marketing preview.

## Browser checks

The rendered site was checked in the Codex browser at **320, 390, 768 and 1280 CSS-pixel viewport widths**: 12 routes × 4 sizes. The browser's scrollbar reduces usable document width by 15 pixels.

An initial 320px header overflow was identified and fixed by tightening the small-screen identity and menu spacing. All 12 routes were rerun at 320px after the fix and had equal document and client widths. The other three widths had no horizontal overflow. Fonts loaded, images resolved, and the heading check passed across all routes. Wide artifact tables scroll inside their own region.

Visual review covered both desktop homepages, both phone homepages, the working case, the mobile contact result and the private comparison page. The final mobile Outcomes headline uses three intentional lines. The brand uses the supplied wordmark, paper-on-charcoal mark, regular IBM Plex type and approved artwork.

Interactions checked:

- Mobile menu opens; Escape closes it and returns focus to the menu button.
- Draft selection switches the visible posting. Running Draft A reports two passes. Running Draft B reports balanced entries and a policy mismatch with the early-expense explanation.
- A managed-project link preselects Managed; data/embedded parameters select the intended inquiry and partnership.
- Preparing a synthetic brief displays the entered workflow and standard as text, with an explicit not-sent notice.
- The browser downloaded the synthetic brief. The saved file was checked for the exact QA sentence and not-sent notice. The browser automation download-event wait timed out, but the actual file on disk verified the download; no product error appeared in the console.
- Reloading the contact page cleared the tested form and hid its generated brief. Browser-managed history/autofill can differ, so the privacy draft does not promise universal clearing behavior.
- The enterprise FAQ opens and exposes its answer.
- A temporary script-free contact rendering kept navigation visible, all content readable and the submit button disabled. It cannot accidentally submit form fields as a GET request. The temporary QA route was removed by the next normal build.
- No browser JavaScript errors or warnings were observed during the checked flows. The copy control has unit-covered brief content and a clipboard-denial fallback; an end-to-end clipboard overwrite was intentionally not performed.
- Temporary viewport settings were reset after responsive testing.

## JEV verification

Two live Gateway requests completed with ten judgments each. Both candidate orders were assessed against six persona briefs. The raw results and input hashes are saved in `evaluation/`. The original input-match check passed before the founder's copy cleanup. Those saved inputs no longer match the revised pages, and the original results are labeled historical. See [the report](evaluation/REPORT.md) for the result and its limitations.

## Release status

Ready for local review and demo. The source and run instructions are in `marketing/`, separate from the Arena's frontend and backend. A real contact destination, final operator/privacy/terms details and an approved public host/domain configuration remain necessary before public launch. The public-facing copy includes no fake customers, invented statistics, unverified certifications or synthetic rankings.

No push, deployment, domain attachment or DNS edit is included in this verification. Canonical metadata targets the founder-confirmed `calibrated.co`. The site remains noindex by default.
