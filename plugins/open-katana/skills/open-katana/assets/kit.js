// Shared motion helpers. Every tween is absolute and seek-safe; nothing reads a clock.
window.K = (() => {
  // index-seeded pseudo random, 0..1
  const rnd = (i, s = 1) => { const x = Math.sin(i * 127.1 + s * 311.7) * 43758.5453; return x - Math.floor(x); };
  const q = (s, root = document) => (typeof s === "string" ? root.querySelector(s) : s);

  // wrap each character in a span, return the spans
  function split(sel) {
    const el = q(sel); const txt = el.textContent; el.textContent = "";
    return [...txt].map((ch) => { const s = document.createElement("span"); s.textContent = ch === " " ? " " : ch; el.appendChild(s); return s; });
  }

  // comet flight from a to b: {x,y} in px. Tail stretches with speed and collapses on landing.
  function fly(tl, sel, a, b, t, d, o = {}) {
    const el = q(sel); const tail = el.querySelector(".tail");
    const rot = (Math.atan2(b.y - a.y, b.x - a.x) * 180) / Math.PI;
    const len = Math.min(1.6, Math.hypot(b.x - a.x, b.y - a.y) / 520);
    tl.set(el, { opacity: 1, rotation: rot }, t);
    tl.fromTo(el, { x: a.x, y: a.y }, { x: b.x, y: b.y, duration: d, ease: o.ease || "power2.inOut", immediateRender: false }, t);
    tl.fromTo(tail, { scaleX: 0.05, opacity: 1 }, { scaleX: len, duration: d * 0.45, ease: "power2.in", immediateRender: false }, t);
    tl.to(tail, { scaleX: 0.05, duration: d * 0.55, ease: "power3.out" }, t + d * 0.45);
    if (o.hide !== false) tl.set(el, { opacity: 0 }, t + d + (o.linger || 0));
  }

  // a blade of light through (x,y) at deg: it travels across, holds, then thins away slowly. o.rev draws it the other way.
  function slash(tl, sel, x, y, deg, t, o = {}) {
    const el = q(sel); const hold = o.hold ?? 0.32, fade = o.fade ?? 0.5;
    const from = o.rev ? "inset(-200px 0% -200px 100%)" : "inset(-200px 100% -200px 0%)";
    tl.set(el, { x, y, rotation: deg, opacity: 1 }, t);
    tl.fromTo(el, { clipPath: from, scaleY: 1.9 }, { clipPath: "inset(-200px 0% -200px 0%)", scaleY: 1, duration: 0.18, ease: "power2.out", immediateRender: false }, t);
    tl.to(el, { scaleY: 0.5, duration: hold, ease: "power1.out" }, t + 0.18);
    tl.to(el, { scaleY: 0, opacity: 0, duration: fade, ease: "power2.inOut" }, t + 0.18 + hold);
  }

  // sparks: petals thrown from the burst element that slow in the air and fall (a pure ballistic function of time)
  function burst(tl, sel, t, o = {}) {
    const el = q(sel); const n = o.n || 16; const V = (o.r || 300) * 3.2; const seed = o.seed || 1; const life = o.life || 0.75; const g = o.g ?? 1500;
    if (!el.children.length) for (let i = 0; i < n; i++) el.appendChild(document.createElement("i"));
    const P = [...el.children].map((node, i) => {
      const a = (((o.from ?? 0) + ((o.arc ?? 360) / n) * (i + rnd(i, seed) * 0.8)) * Math.PI) / 180; const v = V * (0.35 + rnd(i, seed + 3) * 0.75);
      return { node, vx: Math.cos(a) * v, vy: Math.sin(a) * v, k: 3.2 + rnd(i, seed + 5) * 2, life: life * (0.65 + rnd(i, seed + 7) * 0.35), s: 0.7 + rnd(i, seed + 9) * 0.8 };
    });
    track(tl, [[t, 0], [t + life, life]], (T) => P.forEach((p) => {
      if (T <= 0 || T >= p.life) { p.node.style.opacity = 0; return; }
      const e = (1 - Math.exp(-p.k * T)) / p.k, x = p.vx * e, y = p.vy * e + 0.5 * g * T * T;
      const ang = Math.atan2(p.vy * Math.exp(-p.k * T) + g * T, p.vx * Math.exp(-p.k * T)) * 57.2958, u = T / p.life;
      p.node.style.opacity = u < 0.7 ? 1 : (1 - u) / 0.3;
      p.node.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px) rotate(${ang.toFixed(1)}deg) scale(${(p.s * (1.25 - u * 0.6)).toFixed(3)})`;
    }));
  }

  // impact: the whole shot kicks and settles (decaying, deterministic)
  function hit(tl, sel, t, amp = 12) {
    const el = q(sel);
    track(tl, [[t, 0], [t + 0.4, 0.4]], (T) => {
      const k = T <= 0 || T >= 0.4 ? 0 : amp * Math.exp(-T * 11);
      el.style.transform = k ? `translate(${(k * Math.sin(T * 78)).toFixed(2)}px, ${(k * 0.7 * Math.cos(T * 61)).toFixed(2)}px)` : "none";
    });
  }

  // hero word slams in from the lens: big and blurred to sharp and still
  function slam(tl, sel, t, o = {}) {
    tl.fromTo(sel, { scale: o.from || 2.6, opacity: 0, filter: "blur(22px)" },
      { scale: 1, opacity: 1, filter: "blur(0px)", duration: o.d || 0.3, ease: o.ease || "expo.out" }, t);
  }

  // the camera pushes through: everything rushes past and is gone
  function through(tl, sel, t, o = {}) {
    tl.to(sel, { scale: o.to || 5, opacity: 0, filter: "blur(26px)", duration: o.d || 0.22, ease: "power3.in" }, t);
  }

  // whip out sideways with a smear
  function whip(tl, sel, t, dx, o = {}) {
    tl.to(sel, { x: dx, scaleX: 2.2, opacity: 0, filter: "blur(30px)", duration: o.d || 0.2, ease: "power3.in" }, t);
  }

  // slow continuous camera drift for the whole scene
  function drift(tl, sel, d, a, b) {
    tl.fromTo(sel, a, { ...b, duration: d, ease: "none" }, 0);
  }

  // draw a line (scaleX from its origin)
  function draw(tl, sel, t, d = 0.3, ease = "power3.out") {
    tl.fromTo(sel, { scaleX: 0 }, { scaleX: 1, duration: d, ease }, t);
  }

  // type text into el one character at a time between t and t+d (index is a pure function of progress)
  function type(tl, sel, text, t, d) {
    const el = q(sel); const p = { n: 0 };
    tl.fromTo(p, { n: 0 }, { n: text.length, duration: d, ease: "none", immediateRender: false,
      onUpdate: () => { const s = text.slice(0, Math.round(p.n)); if (el.textContent !== s) el.textContent = s; } }, t);
  }

  // scene starts (seconds) come from assets/grid.js; they mirror the hosts' data-start in index.html (change both together)
  const G = window.GRID || {};
  // cue("s02")(2, 3) = when word 3 of sentence 2 is spoken, in that scene's own time
  const cue = (scene) => (s, w) => +(window.VO.W[s - 1][w - 1][1] - G[scene]).toFixed(3);

  // a hidden twin of el, taken before any tween touches it, for cut()
  function dup(sel) {
    const el = q(sel); const c = el.cloneNode(true); c.removeAttribute("id");
    c.querySelectorAll("[id]").forEach((n) => n.removeAttribute("id")); c.style.opacity = 0; el.after(c); return c;
  }
  // slice el along a blade through (x,y) at deg. Nothing snaps: the halves ease apart along the cut, keep drifting,
  // then gravity takes them and they tumble away in depth. o.part opens them like shutters instead of dropping them.
  function cut(tl, sel, twin, t, o) {
    const el = q(sel); const a = (o.deg * Math.PI) / 180; const dx = Math.cos(a), dy = Math.sin(a), nx = -dy, ny = dx, L = 4000;
    const P = (k, m) => `${o.x + dx * k * L + nx * m * L}px ${o.y + dy * k * L + ny * m * L}px`;
    const half = (m) => `polygon(${P(-1, 0)}, ${P(1, 0)}, ${P(1, m)}, ${P(-1, m)})`;
    const d = o.d || 0.95, slip = o.slip ?? 46, gap = o.gap ?? 10, hang = o.hang ?? 0.2, spin = o.spin ?? 12, io = gsap.parseEase("power2.inOut");
    [el, twin].forEach((n) => { n.style.transformOrigin = `${o.x}px ${o.y}px`; });
    tl.set(el, { clipPath: half(-1) }, t); tl.set(twin, { clipPath: half(1), opacity: 1 }, t);
    const pose = (n, sgn, T) => {
      if (T <= 0) { n.style.transform = "none"; n.style.filter = "none"; return; }
      if (o.part) { const w = 1500 * io(Math.min(1, T / d)) + gap * (1 - Math.exp(-T / 0.1)); n.style.transform = `translate(${sgn * nx * w}px, ${sgn * ny * w}px)`; return; }
      const s = slip * (1 - Math.exp(-T / 0.18)), w = gap * (1 - Math.exp(-T / 0.12)) + 30 * T;   // slide along the blade, open away from it
      const f = Math.max(0, T - hang - (sgn < 0 ? 0.07 : 0)), drop = 2300 * f * f * (1 + f);         // then fall, from rest
      const x = sgn * (dx * s + nx * w) + sgn * 180 * f * f, y = sgn * (dy * s + ny * w) + drop;
      n.style.transform = `translate3d(${x.toFixed(1)}px, ${y.toFixed(1)}px, ${(-900 * f * f).toFixed(1)}px) rotateX(${(-sgn * 70 * f * f).toFixed(2)}deg) rotate(${(sgn * spin * (T * 0.2 + f * f * 3)).toFixed(2)}deg)`;
      n.style.filter = f > 0.12 ? `blur(${Math.min(9, f * f * 30).toFixed(1)}px)` : "none";
    };
    track(tl, [[t, 0], [t + d, d]], (T) => { pose(el, -1, T); pose(twin, 1, T); });
    tl.set([el, twin], { opacity: 0 }, t + d);
  }

  // glitch out: el is replaced by horizontal bands of itself that tear sideways on a stepped clock, stretch and vanish.
  // bands(sel) must run before any tween touches el (it copies the settled layout).
  function bands(sel, n = 7) {
    const el = q(sel); const h = el.offsetHeight || 1080;
    return Array.from({ length: n }, (_, i) => { const c = dup(el); c.style.clipPath = `inset(${(i * h) / n}px -600px ${h - ((i + 1) * h) / n}px -600px)`; return c; });
  }
  function glitch(tl, sel, strips, t, d = 0.34) {
    const el = q(sel);
    tl.set(el, { opacity: 0 }, t); tl.set(strips, { opacity: 1 }, t); tl.set(strips, { opacity: 0 }, t + d);
    track(tl, [[t, 0], [t + d, 1]], (u) => {
      const step = Math.floor(u * 9);   // 9 discrete states over the glitch
      strips.forEach((c, i) => {
        const r = rnd(i * 13 + step, 5) - 0.5, amp = 60 + 700 * u * u;
        c.style.transform = u <= 0 ? "none" : `translate(${(r * amp).toFixed(1)}px, 0) scale(${(1 + Math.abs(r) * 2.4 * u).toFixed(3)}, ${(1 - 0.85 * u * u).toFixed(3)})`;
        c.style.filter = u > 0.5 ? `blur(${((u - 0.5) * 10).toFixed(1)}px)` : "none";
      });
    });
  }

  // piecewise-linear driver through keys [[t, v], ...]: fn(v) is a pure function of the playhead
  function track(tl, keys, fn) {
    const t0 = keys[0][0], t1 = keys[keys.length - 1][0], p = { u: 0 };
    const at = (u) => {
      const t = t0 + u * (t1 - t0); let i = 1; while (i < keys.length - 1 && keys[i][0] < t) i++;
      const [ta, va] = keys[i - 1], [tb, vb] = keys[i];
      return va + (vb - va) * Math.min(1, Math.max(0, (t - ta) / (tb - ta || 1)));
    };
    tl.fromTo(p, { u: 0 }, { u: 1, duration: t1 - t0, ease: "none", onUpdate: () => fn(at(p.u)) }, t0);
    fn(keys[0][1]);
  }
  // typewriter over monospace lines: lines = [{el, len}], cw = glyph advance in px; cursor follows the last glyph
  function typer(tl, keys, lines, cursor, cw, lh) {
    track(tl, keys, (v) => {
      let n = Math.round(v), row = 0, col = 0;
      lines.forEach((ln, i) => {
        const k = Math.max(0, Math.min(ln.len, n)); n -= ln.len;
        ln.el.style.clipPath = k ? `inset(-12px ${(ln.len - k) * cw - 8}px -12px -12px)` : "inset(0 100% 0 0)";
        if (k > 0 || i === 0) { row = i; col = k; }
      });
      cursor.style.transform = `translate(${col * cw}px, ${row * lh}px)`;
    });
  }

  return { track, typer, bands, glitch, hit, rnd, split, fly, slash, burst, slam, through, whip, drift, draw, type, cue, dup, cut, G };
})();
