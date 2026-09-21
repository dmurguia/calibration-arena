# Calibrated Co. — Brand kit 3.0

**The art of better.** Paper, soft charcoal, graphite, steel and leather brown. A strong signature surrounded by an ordinary, usable page of thought.

Open the **[visual guide](index.html)**, **[designer brief PDF](Calibrated-Co-Design-Brief.pdf)** or **[editable brief](DESIGN-BRIEF.md)**.

## The revision

Silver is replaced by restrained leather brown, and charcoal is softened to gray. Regular Plex Sans now handles headings and notes as well as reading. The C and wordmark retain their bold weight. The graphite artwork, layout and motion concept remain intact. The prior kit is preserved separately in brand/archive/calibrated-brand-kit-v3.zip.

## Typography

| Role | Typeface | Weight | Use |
| --- | --- | --- | --- |
| Identity | Archivo Black | 400, visually black | Company wordmark and rare deliberate emphasis |
| Headings and notes | IBM Plex Sans | Regular 400 | Conservative headings, tagline and annotations |
| Reading | IBM Plex Sans | Regular 400 | Paragraphs, navigation and UI |
| Code | IBM Plex Mono | Regular 400 | Code, numbers and technical labels |

Bold is selective, not the default. The logo already supplies weight.

Use the same quiet regular face throughout the page. Start around 32–50px for section headings and 16–18px for notes. Let size, spacing and composition create hierarchy. The existing graphite images carry the human handwriting; the interface typography stays restrained.

Use Plex Sans at 16–18px with 1.5–1.6 line-height. Use Plex Mono at 14–16px for meaningful code and 12–14px for short metadata. Long paragraphs, instructions and code should remain easy to read. Weight 500 is available for occasional functional emphasis; the bundled 600 has no default brand role.

Archivo Black's file weight is 400: it is already visually heavy. Use the outlined wordmark and do not synthesize bold.

All three families include desktop files, local WOFF2 files and OFL notices. The Plex Sans desktop font is variable; choose weight 400 and normal width where relevant. Webfonts are Latin subsets. No italics are included.

## Neutral palette

| Token | Name | Hex | Role |
| --- | --- | --- | --- |
| ink | Charcoal | #464643 | Identity and primary text |
| paper | Notebook paper | #F4F1E9 | Main lightly warm canvas |
| graphite | Graphite | #656460 | Secondary text and drawn marks |
| steel | Brushed steel | #929698 | Restrained material details |
| leather | Leather brown | #70543E | Restrained warmth; watch-strap reference |
| white | Chalk white | #FAF9F6 | Light reading surface |

Paper dominates. Charcoal and graphite carry the marks. Steel provides finish and precise edges. Leather brown adds one small note of warmth. Brushed metal, polished metal, matte graphite and paper can contrast through light and texture.

Use charcoal or graphite on paper, paper on charcoal, and paper on leather brown. Steel is not a small-text color on paper. Approved combinations in colors/contrast.json meet 4.5:1 normal-text contrast. Check actual image crops separately. Focus indicators must contrast with their local background.

Values are sRGB. Grey tokens are not metallic-ink specifications. Foil, metal and physical print require production samples. Avoid chrome lettering and decorative metallic gradients.

## Identity

The C preserves the heavy left/lower stroke, uneven bowl, cut terminals and separate dash. Its imperfection should follow the motion of a hand.

The SVG set contains mark, wordmark, horizontal, stacked, signature and tagline variants in charcoal, paper and graphite, plus app icons and favicon. All lettering is outlined. PNGs are transparent except app-icon tiles.

- Charcoal horizontal lockup: light website headers.
- Primary C: paper on a charcoal backdrop. Leather brown is an accent only; never use it for the logo or its background.
- Mark: at least 24px. Inspect the supplied 16px icon at actual size.
- Horizontal lockup: at least 200px; below that use the mark or wordmark alone.
- Clear space: at least one quarter of the mark's height.
- Signature with regular tagline: at least 320px; omit the tagline below that.
- Keep the identity flat: no bevels, shadows, texture or artificial distress.

## Image library

Five active generated studies are included:

1. **Open sketch** — the original flowing graphite gesture.
2. **Graphite pressure** — heavier physical marks for occasional emphasis.
3. **Instrument steel** — neutral brushed surfaces and a precise slotted screw.
4. **Working notation** — fine shorthand, pencil loops and emerging syntax.
5. **Paper and cloth** — off-white paper, black book cloth and a steel edge.

PNG masters are unchanged originals. Full-size and 768px WebP derivatives are ready for web use. Prompts, provenance, dimensions, suggested uses and alt text are in images/manifest.json and images/prompts.json.

These are generated illustrations and material studies, not documentary photographs. Written fragments are texture, not verified code or research. Keep real information live and readable. Do not stretch or tile the images.

## Motion

Open motion/sketch-to-structure.html. Begin with recognizable loose drawing. Let continuous strokes find alignment, spacing and syntax, preserving a trace of the hand. Keep code regular and the signature bold.

The prototype starts paused, has play/pause and a scrubber, and handles reduced-motion preferences. It needs production integration review and a static fallback.

## Handoff

The folder includes logos, three font families, color tokens and contrast checks, five image masters and ten WebP exports, the portable motion study, revised previews, a designer brief and source tools. Tools are not needed to use the assets.

Link fonts/fonts.css and colors/tokens.css into the website, keeping fonts.css beside its web/ folder. Use --cal-font-display for regular headings, --cal-font-body for reading, --cal-font-mono for code and --cal-font-identity for deliberate emphasis.

See **[RIGHTS.md](RIGHTS.md)** and **[REFERENCES.md](REFERENCES.md)** for permissions and inspiration.

