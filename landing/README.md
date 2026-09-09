# Calibrated Co. landing page

Single-file static page for the company brand (`index.html`). Calibration Arena stays
the product front door; this page points at the whole thesis (measured expert panel →
evals, rubrics, grading for labs and vertical AI vendors).

- No build step. Fonts load from Google Fonts; everything else is inline.
- Light and dark themes via tokens; the toggle in the nav stores a per-browser choice.
- Deploy: new Vercel project → import this repo → **Root Directory** = `landing`,
  framework preset "Other". Point `calibrated.co` (or whatever domain you land on) at it.
- Contact address: one constant, `CONTACT`, at the bottom of `index.html`.
- Claims on the page and where they come from: `docs/STRATEGY-calibrated-co.md` §7.
