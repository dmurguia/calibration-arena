// Calibrated Co. — "sketch finds syntax" hero.
// Framework-agnostic ES module. No dependencies.
//
//   import { mountCalibratedHero } from './calibrated-hero.js';
//   const hero = mountCalibratedHero(document.getElementById('hero'), { image: '/assets/open-sketch.webp' });
//   // later: hero.destroy();
//
// How it works: on mount, the sketch image is drawn to an offscreen canvas and its graphite is
// thinned to 1px centerlines, then traced into polylines. The code block is rendered and traced
// the same way. Scroll progress (0 → 1) moves every sketch line along its own delayed arc into a
// code line. The image fades to a faint trace; the real code text fades in over the lines.
// Hover (optional) re-inks the drawing's own strokes near the pointer (SVG) and makes the code
// revise itself.

const INK = '#464643', PAPER = '#F4F1E9', GRAPHITE = '#656460', STROKE = '#535350', LEATHER = '#70543E';
const NPTS = 24, MAXSEG = 900;
const MONO = '"IBM Plex Mono", ui-monospace, monospace';

const DEFAULT_CODE = [
  'observation = observe(world)',
  'hypothesis = sketch(observation)',
  '',
  'while learning:',
  '    proposal = agent.refine(hypothesis)',
  '    feedback = human.review(proposal)',
  '    hypothesis = revise(proposal, feedback)',
  '',
  '# observe / draw / test / refine',
];
// [line index, token, revision] — cycled while hovered in the code state
const DEFAULT_EDITS = [
  [6, 'feedback', 'human_judgment'],
  [4, 'agent.refine', 'agent.propose'],
  [5, 'human.review', 'expert.review'],
  [0, 'observe(world)', 'observe(work)'],
  [8, 'refine', 'repeat'],
];
const PHASES = ['01 — OPEN GESTURE', '02 — GATHERING STROKES', '03 — FINDING SYNTAX', '04 — AGENT / HUMAN / REVISION'];

export const DEFAULTS = {
  image: './assets/open-sketch.webp', // must be same-origin (pixels are read)
  driver: 'scroll',       // 'scroll' | 'scroll+hover' | 'hover'
  panelHeight: 70,        // vh — height of the pinned art panel
  scrollLength: 230,      // vh — total scroll distance the panel stays pinned for
  minHeight: 480,         // px — floor for the panel height
  trace: 4,               // % opacity of the sketch retained behind the code
  showLabel: true,        // phase chip bottom-left
  showHint: true,         // "SCROLL — …" hint beside the chip
  code: DEFAULT_CODE,
  edits: DEFAULT_EDITS,
};

const smooth = (n) => { n = Math.max(0, Math.min(1, n)); return n * n * (3 - 2 * n); };
const lerp = (a, b, t) => a + (b - a) * t;

function makeRand(s) {
  let seed = s;
  return () => { seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0; return seed / 4294967296; };
}

// Zhang–Suen thinning of dark pixels, then greedy direction-preserving tracing into polylines.
function getPaths(c, threshold, minimum) {
  const scale = Math.min(1, 900 / c.width), tmp = document.createElement('canvas');
  tmp.width = Math.round(c.width * scale); tmp.height = Math.round(c.height * scale);
  const gc = tmp.getContext('2d', { willReadFrequently: true });
  gc.fillStyle = '#fff'; gc.fillRect(0, 0, tmp.width, tmp.height); gc.drawImage(c, 0, 0, tmp.width, tmp.height);
  const W = tmp.width, H = tmp.height, d = gc.getImageData(0, 0, W, H).data, m = new Uint8Array(W * H);
  for (let i = 0; i < m.length; i++) m[i] = (d[i * 4] + d[i * 4 + 1] + d[i * 4 + 2]) / 3 < threshold ? 1 : 0;
  const off = [-W, -W + 1, 1, W + 1, W, W - 1, -1, -W - 1], p = new Uint8Array(8);
  for (let it = 0; it < 18; it++) {
    let changed = 0;
    for (let pass = 0; pass < 2; pass++) {
      const remove = [];
      for (let y = 1; y < H - 1; y++) for (let x = 1; x < W - 1; x++) {
        const i = y * W + x; if (!m[i]) continue;
        let n = 0, a = 0;
        for (let k = 0; k < 8; k++) p[k] = m[i + off[k]];
        for (let k = 0; k < 8; k++) { n += p[k]; if (!p[k] && p[(k + 1) % 8]) a++; }
        if (n < 2 || n > 6 || a !== 1) continue;
        if (pass === 0 ? (p[0] * p[2] * p[4] === 0 && p[2] * p[4] * p[6] === 0) : (p[0] * p[2] * p[6] === 0 && p[0] * p[4] * p[6] === 0)) remove.push(i);
      }
      for (const i of remove) m[i] = 0; changed += remove.length;
    }
    if (!changed) break;
  }
  const seen = new Uint8Array(m.length), paths = [];
  const neighbors = (i) => { const out = []; for (const o of off) { const j = i + o; if (j >= 0 && j < m.length && m[j] && !seen[j] && Math.abs(j % W - i % W) < 2) out.push(j); } return out; };
  const seeds = [];
  for (let i = W + 1; i < m.length - W - 1; i++) if (m[i] && neighbors(i).length === 1) seeds.push(i);
  for (let i = W + 1; i < m.length - W - 1; i++) if (m[i]) seeds.push(i);
  for (const start of seeds) {
    if (seen[start]) continue;
    const path = []; let i = start, dx = 0, dy = 0;
    for (let j = 0; j < 500; j++) {
      seen[i] = 1; path.push({ x: (i % W) / scale, y: Math.floor(i / W) / scale });
      const ns = neighbors(i); if (!ns.length) break;
      const score = (n) => ((n % W - i % W) * dx + (Math.floor(n / W) - Math.floor(i / W)) * dy) / Math.hypot(n % W - i % W, Math.floor(n / W) - Math.floor(i / W));
      ns.sort((a, b) => score(b) - score(a));
      const next = ns[0]; dx = next % W - i % W; dy = Math.floor(next / W) - Math.floor(i / W); i = next;
    }
    if (path.length >= minimum) paths.push(path);
  }
  return paths.sort((a, b) => a[0].y - b[0].y || a[0].x - b[0].x);
}

function resample(path) {
  const L = [0]; for (let i = 1; i < path.length; i++) L.push(L[i - 1] + Math.hypot(path[i].x - path[i - 1].x, path[i].y - path[i - 1].y));
  const total = L[L.length - 1], out = []; let k = 1;
  for (let j = 0; j < NPTS; j++) {
    const t = total * j / (NPTS - 1); while (k < L.length - 1 && L[k] < t) k++;
    const q = (t - L[k - 1]) / (L[k] - L[k - 1] || 1);
    out.push([lerp(path[k - 1].x, path[k].x, q), lerp(path[k - 1].y, path[k].y, q)]);
  }
  return out;
}

function buildScene(img, W, H, CODE) {
  const sc = document.createElement('canvas'); sc.width = W; sc.height = H;
  const s = sc.getContext('2d'); s.fillStyle = PAPER; s.fillRect(0, 0, W, H);
  const scale = Math.max(W / img.naturalWidth, H / img.naturalHeight) * 1.02, iw = img.naturalWidth * scale, ih = img.naturalHeight * scale;
  s.drawImage(img, (W - iw) * 0.5, (H - ih) / 2, iw, ih);
  const fs = W < 700 ? 13 : Math.min(18, W / 70), line = Math.round(fs * 1.75), ch = fs * 0.6;
  const longest = CODE.reduce((m, l) => Math.max(m, l.length), 0) + 4;
  const left = Math.round((W - longest * ch) / 2), top = Math.round(H * 0.5 - CODE.length * line / 2);
  const cc = document.createElement('canvas'); cc.width = W; cc.height = H;
  const g = cc.getContext('2d'); g.fillStyle = '#fff'; g.fillRect(0, 0, W, H);
  g.font = `${fs}px ${MONO}`; g.fillStyle = INK;
  CODE.forEach((str, i) => g.fillText(str, left, top + i * line + fs));
  const start = getPaths(sc, 157, 12), end = getPaths(cc, 195, 3);
  let rand = makeRand(593);
  const vec = start.map((pth) => {
    let d = ''; const step = Math.max(1, Math.floor(pth.length / 40));
    for (let j = 0; j < pth.length; j += step) d += (j ? 'L' : 'M') + pth[j].x.toFixed(1) + ' ' + pth[j].y.toFixed(1);
    const l = pth[pth.length - 1]; d += 'L' + l.x.toFixed(1) + ' ' + l.y.toFixed(1);
    return { d, x: pth[0].x, y: pth[0].y, w: 0.6 + rand() * 0.9, n: pth.length, near: false };
  });
  rand = makeRand(593);
  const n = Math.min(MAXSEG, start.length), segs = [];
  for (let i = 0; i < n && end.length; i++) {
    const a = resample(start[Math.floor(i * start.length / n)]), z = resample(end[Math.floor(i * end.length / n)]);
    const cx = a[0][0] / W, cy = a[0][1] / H;
    segs.push({
      a, z, weight: 0.5 + rand() * 0.7,
      // spatially coherent delays + arcs: neighbouring lines leave together, like a flock turning
      delay: 0.22 * (0.5 + 0.5 * Math.sin(cx * 4.1 + cy * 2.3)) + 0.16 * rand(),
      arc: H * (0.11 * Math.sin(cx * 5.2 + 1.1) * Math.cos(cy * 3.7) + (rand() - 0.5) * 0.04),
      ph: rand(),
    });
  }
  return { sketch: sc, segs, vec, code: { fs, line, ch, left, top }, W, H };
}

function el(tag, style, parent) {
  const e = document.createElement(tag);
  if (style) Object.assign(e.style, style);
  if (parent) parent.appendChild(e);
  return e;
}

export function mountCalibratedHero(root, options = {}) {
  const o = { ...DEFAULTS, ...options };
  const CODE = o.code, EDITS = o.edits;
  const scrollDriven = o.driver !== 'hover';
  const hoverEnabled = o.driver !== 'scroll';
  const reducedMQ = matchMedia('(prefers-reduced-motion: reduce)');
  const trace = o.trace / 100;

  // DOM
  const track = el('div', { position: 'relative', height: scrollDriven ? `max(${o.scrollLength}vh, ${Math.round(o.minHeight * o.scrollLength / 100)}px)` : `${o.panelHeight}vh`, minHeight: o.minHeight + 'px' }, root);
  track.className = 'cal-hero';
  const sticky = el('div', { position: 'sticky', top: '0', height: `${o.panelHeight}vh`, minHeight: o.minHeight + 'px', overflow: 'hidden', background: PAPER, borderTop: `1px solid ${INK}33`, borderBottom: `1px solid ${INK}33` }, track);
  const canvas = el('canvas', { position: 'absolute', inset: '0', display: 'block' }, sticky);
  canvas.setAttribute('role', 'img');
  canvas.setAttribute('aria-label', 'An open graphite sketch whose lines gather, as you scroll, into a short block of agent and human review code.');
  const SVGNS = 'http://www.w3.org/2000/svg';
  const svg = document.createElementNS(SVGNS, 'svg');
  Object.assign(svg.style, { position: 'absolute', inset: '0', width: '100%', height: '100%', pointerEvents: 'none', opacity: '0' });
  svg.setAttribute('fill', 'none'); svg.setAttribute('stroke', INK); svg.setAttribute('stroke-linecap', 'round'); svg.setAttribute('stroke-linejoin', 'round'); svg.setAttribute('preserveAspectRatio', 'none'); svg.setAttribute('aria-hidden', 'true');
  sticky.appendChild(svg);
  const bar = el('div', { position: 'absolute', left: '4.2%', right: '4.2%', bottom: '28px', display: 'flex', alignItems: 'center', gap: '16px', pointerEvents: 'none' }, sticky);
  const label = el('span', { background: PAPER, color: INK, padding: '6px 10px', fontFamily: MONO, fontSize: '11px', letterSpacing: '.08em', border: `1px solid ${INK}33`, display: o.showLabel ? '' : 'none' }, bar);
  label.textContent = PHASES[0];
  const live = el('span', { position: 'absolute', width: '1px', height: '1px', overflow: 'hidden', clip: 'rect(0 0 0 0)' }, bar);
  live.setAttribute('aria-live', 'polite');
  if (o.showHint && scrollDriven) {
    const hint = el('span', { fontFamily: MONO, fontSize: '11px', letterSpacing: '.08em', color: GRAPHITE }, bar);
    hint.textContent = hoverEnabled ? 'SCROLL — THE SKETCH FINDS SYNTAX ↓ / HOVER — IT MOVES' : 'SCROLL — THE SKETCH FINDS SYNTAX ↓';
  }

  // State
  const st = { scene: null, p: 0, target: 0, hover: 0, hoverIn: false, hx: -1e4, hy: -1e4, tx: -1e4, ty: -1e4, edit: 0, visible: true, phaseIdx: 0 };
  const ctx = canvas.getContext('2d');
  const img = new Image(); img.decoding = 'async'; img.src = o.image;
  let dead = false, rebuildTimer = 0, raf = 0, last = 0;

  function rebuild() {
    if (dead || !img.naturalWidth) return;
    const W = Math.round(sticky.clientWidth), H = Math.round(sticky.clientHeight); if (!W || !H) return;
    if (st.scene && st.scene.W === W && st.scene.H === H) return;
    try { st.scene = buildScene(img, W, H, CODE); } catch (e) { console.error('[calibrated-hero] scene build failed (is the image same-origin?)', e); return; }
    const dpr = Math.min(devicePixelRatio || 1, 2);
    canvas.width = W * dpr; canvas.height = H * dpr; canvas.style.width = W + 'px'; canvas.style.height = H + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    svg.setAttribute('viewBox', `0 0 ${W} ${H}`);
    svg.replaceChildren();
    if (hoverEnabled) for (const v of st.scene.vec) {
      const p = document.createElementNS(SVGNS, 'path');
      p.setAttribute('d', v.d); p.setAttribute('stroke-width', (v.w * 1.5).toFixed(2)); p.setAttribute('pathLength', '1'); p.setAttribute('stroke-dasharray', '1');
      p.style.strokeDashoffset = '1'; p.style.opacity = '0';
      p.style.transition = `stroke-dashoffset ${(0.5 + v.n / 400).toFixed(2)}s cubic-bezier(.4,0,.2,1), opacity .6s`;
      svg.appendChild(p);
    }
    if (!raf) raf = requestAnimationFrame(frame);
  }

  function frame(now) {
    raf = 0;
    if (dead) return;
    if (st.visible) raf = requestAnimationFrame(frame);
    const dt = Math.min(0.05, (now - (last || now)) / 1000); last = now;
    const scene = st.scene; if (!scene) return;
    const { W, H } = scene, reduced = reducedMQ.matches;

    if (scrollDriven) {
      const r = track.getBoundingClientRect();
      st.target = Math.max(0, Math.min(1, -r.top / Math.max(1, r.height - sticky.clientHeight)));
    } else st.target = st.hoverIn ? 1 : 0;
    st.p += (st.target - st.p) * (reduced ? 1 : 1 - Math.exp(-dt * (scrollDriven ? 5 : 1.2)));
    const wantHover = hoverEnabled && st.hoverIn && !reduced ? 1 : 0;
    st.hover += (wantHover - st.hover) * (1 - Math.exp(-dt * 4));
    if (st.hx < -1e3) { st.hx = st.tx; st.hy = st.ty; }
    st.hx += (st.tx - st.hx) * (1 - Math.exp(-dt * 6)); st.hy += (st.ty - st.hy) * (1 - Math.exp(-dt * 6));
    const p = st.p, T = now / 1000, hoverA = st.hover, R = Math.min(W, H) * 0.24;

    ctx.globalAlpha = 1; ctx.fillStyle = PAPER; ctx.fillRect(0, 0, W, H);
    const imgA = Math.max(1 - smooth((p - 0.15) / 0.4), trace * smooth((p - 0.86) / 0.14));
    if (imgA > 0.002) { ctx.globalAlpha = imgA * 0.92; ctx.drawImage(scene.sketch, 0, 0, W, H); }

    // hover in the sketch state: the drawing's own strokes near the pointer re-ink (SVG draw-on)
    const inking = hoverA * (1 - smooth((p - 0.02) / 0.1)) * imgA;
    if (hoverEnabled) {
      svg.style.opacity = inking.toFixed(3);
      const els = svg.children, vecs = scene.vec;
      for (let i = 0; i < els.length && i < vecs.length; i++) {
        const v = vecs[i], near = inking > 0.02 && Math.hypot(v.x - st.hx, v.y - st.hy) < R;
        if (near !== v.near) { v.near = near; els[i].style.strokeDashoffset = near ? '0' : '1'; els[i].style.opacity = near ? '0.9' : '0'; }
      }
    }

    // the flight: each sketch line travels its own delayed arc into a code line
    const visibility = (1 - smooth((p - 0.91) / 0.09)) * smooth((p - 0.06) / 0.14);
    const mid = Math.sin(Math.min(1, Math.max(0, p)) * Math.PI);
    if (visibility > 0.001) {
      ctx.strokeStyle = STROKE; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
      const segs = scene.segs;
      for (let i = 0; i < segs.length; i++) {
        const s = segs[i];
        let q = smooth((p - s.delay) / 0.62);
        q = Math.min(1, Math.max(0, q + hoverA * mid * 0.16 * Math.sin((T / 1.7 + s.ph * 2) * Math.PI * 2)));
        const flight = Math.sin(q * Math.PI);
        const wave = reduced ? 0 : flight * (5 + 9 * hoverA) * Math.sin((T / (3.1 - hoverA) + s.ph + i * 0.013) * Math.PI * 2);
        ctx.globalAlpha = visibility * (0.42 + s.weight * 0.24);
        ctx.lineWidth = lerp(s.weight, 0.75, q);
        ctx.beginPath();
        for (let j = 0; j < NPTS; j++) {
          const x = lerp(s.a[j][0], s.z[j][0], q) + wave * 0.4, y = lerp(s.a[j][1], s.z[j][1], q) + flight * s.arc + wave;
          if (j) ctx.lineTo(x, y); else ctx.moveTo(x, y);
        }
        ctx.stroke();
      }
    }

    // code: fades in over the settled lines; while hovered, it revises itself
    const codeA = smooth((p - 0.76) / 0.21) * 0.92;
    if (codeA > 0.002) {
      const { fs, line, ch, left, top } = scene.code;
      ctx.globalAlpha = codeA; ctx.fillStyle = INK; ctx.font = `${fs}px ${MONO}`; ctx.textBaseline = 'alphabetic';
      st.edit += dt * hoverA;
      let li = -1, liveLine = '', pre = '', cur = '', settled = true, ul = 0, to = '';
      if (EDITS.length) {
        const per = 5.2, k = Math.floor(st.edit / per) % EDITS.length, u = (st.edit % per) / per;
        const e = EDITS[k]; li = e[0]; const from = e[1]; to = e[2];
        const at = CODE[li].indexOf(from);
        pre = CODE[li].slice(0, at); const post = CODE[li].slice(at + from.length);
        const er = smooth((u - 0.08) / 0.18), ty = smooth((u - 0.34) / 0.3), back = smooth((u - 0.82) / 0.1);
        cur = back > 0 ? from.slice(0, Math.round(back * from.length)) : ty > 0 ? to.slice(0, Math.round(ty * to.length)) : from.slice(0, Math.round((1 - er) * from.length));
        settled = er <= 0 || (ty >= 1 && back <= 0) || back >= 1;
        liveLine = pre + cur + (settled ? post : '');
        ul = ty >= 1 && back <= 0 ? 1 : 0;
      }
      CODE.forEach((str, i) => ctx.fillText(i === li ? liveLine : str, left, top + i * line + fs));
      if (li >= 0 && hoverA > 0.05 && !settled && Math.floor(T * 2.4) % 2 === 0) ctx.fillRect(left + (pre + cur).length * ch + 2, top + li * line + 3, ch, fs);
      if (li >= 0 && ul) { ctx.fillStyle = LEATHER; ctx.fillRect(left + pre.length * ch, top + li * line + fs + 5, to.length * ch, 1); }
    }
    ctx.globalAlpha = 1;

    const idx = p < 0.2 ? 0 : p < 0.52 ? 1 : p < 0.85 ? 2 : 3;
    if (idx !== st.phaseIdx) { st.phaseIdx = idx; label.textContent = PHASES[idx]; live.textContent = PHASES[idx]; }
  }

  // Events
  const onMove = (e) => { const r = sticky.getBoundingClientRect(); st.tx = e.clientX - r.left; st.ty = e.clientY - r.top; st.hoverIn = true; };
  const onLeave = () => { st.hoverIn = false; };
  if (hoverEnabled || !scrollDriven) { sticky.addEventListener('pointermove', onMove); sticky.addEventListener('pointerleave', onLeave); }
  const ro = new ResizeObserver(() => { clearTimeout(rebuildTimer); rebuildTimer = setTimeout(rebuild, 120); });
  ro.observe(sticky);
  // pause the frame loop while the hero is off screen
  const io = new IntersectionObserver(([entry]) => {
    st.visible = entry.isIntersecting;
    if (st.visible && !raf && st.scene) { last = 0; raf = requestAnimationFrame(frame); }
  });
  io.observe(track);

  const fontReady = document.fonts ? document.fonts.load(`16px ${MONO}`).catch(() => {}) : Promise.resolve();
  const imgReady = new Promise((res, rej) => {
    if (img.complete && img.naturalWidth) return res();
    img.addEventListener('load', () => res(), { once: true });
    img.addEventListener('error', rej, { once: true });
  });
  Promise.all([imgReady, fontReady]).then(rebuild, (e) => console.error('[calibrated-hero] image failed to load', e));

  return {
    /** Current phase, 0 (sketch) → 1 (code). */
    get progress() { return st.p; },
    /** The traced drawing as a standalone SVG string (sized to the current panel). */
    exportSVG() {
      const s = st.scene; if (!s) return '';
      return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${s.W} ${s.H}" fill="none" stroke="${INK}" stroke-linecap="round" stroke-linejoin="round">` +
        s.vec.map((v) => `<path d="${v.d}" stroke-width="${v.w.toFixed(2)}"/>`).join('') + '</svg>';
    },
    destroy() {
      dead = true; cancelAnimationFrame(raf); clearTimeout(rebuildTimer); ro.disconnect(); io.disconnect();
      sticky.removeEventListener('pointermove', onMove); sticky.removeEventListener('pointerleave', onLeave);
      track.remove();
    },
  };
}
