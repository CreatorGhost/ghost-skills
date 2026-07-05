# Animation craft — 3b1b's actual idioms (mined from his 2025–26 scene code) + the pre-ship audit

Source: `github.com/3b1b/videos` `_2025/laplace`, `_2025/zeta`, `_2025/cosmic_distance`,
`_2026/cross_entropy`, `_2026/monthly_mindbenders` (ManimGL — mine techniques, NEVER copy code).
Applied to video #2's craft pass. Correctness gets a video rendered; THIS is what makes it feel 3b1b.

## The five core idioms (with CE translations)

1. **Physical moves arc, and pieces travel as pieces.** Never slide a group as a block. Per-piece
   `Transform(a, b, path_arc=…)` with a **fan of arcs** (`np.linspace(-70, 70, n) * DEGREES`) inside
   `LaggedStart(..., lag_ratio=0.1)` — pieces funnel like confetti. The arc is derived from the move's
   geometry, and both the object and any pointer/annotation share the SAME arc.
2. **Teach the action once, then batch.** For a rearrangement: first piece moves alone and slowly
   (~0.16×block), the second demonstrates the special part (the FLIP — pick the piece whose rotation
   delta ≈ π so it visibly turns in flight, on a high arc `path_arc=100*DEGREES`), remaining pieces
   batch with the lag fan. Grant does exactly this in loops: `if n == 0:` slow demo (+zoom), `elif n < 4:`
   normal, then compressed.
3. **The camera is a passenger, not a performer.** In formula/proof scenes the frame mostly stays
   still. When it moves: small (~1.1–1.5×), anchored so the subject doesn't jump, and riding INSIDE a
   content play (`self.play(self.camera.frame.animate.scale(1/1.25).move_to(p), <content anim>)`) —
   never its own silent beat. Always `Restore(self.camera.frame)` inside the next block's first play.
4. **Formulas are MADE OF the picture.** Every equation term that already exists on screen arrives as
   `TransformFromCopy(label, term, path_arc=±45*DEGREES)` (source stays put); only genuinely new glue
   (`=`, `×`) gets `Write`. Split the MathTex into parts (`MathTex(r"A =", r"\pi r", r"\times", ...)`)
   and color the flown-in parts to match their labels — color = identity, declared once, kept forever
   (semantic map: YELLOW=rim/circumference, GREEN=radius, BLUE=area/pieces).
5. **Timing table:** real moves 2s (his mode), big moves 3s, accents 0.5–0.75s, narration-length plays
   8–30s. `lag_ratio`: 0.1 default, 0.25–0.5 for a few discrete items, 0.01–0.05 for glyph cascades.
   `rate_func`: default smooth for real changes; `there_and_back` ONLY for reversible asides ("what if
   it were smaller…"); `wiggle` to draw the eye; `linear` for ValueTracker ambience.

## Supporting habits worth stealing
- **One persistent highlight rectangle** that *slides* between targets
  (`Transform(rect, SurroundingRectangle(next))`, same path_arc as the term it escorts) instead of many
  one-shot Circumscribes.
- **Ghost copies for permanence**: before something transforms away, leave `thing.copy().set_opacity(0.4)`
  so the proof's history stays visible (use only where it won't overlap later layout).
- **Transient pointers clean themselves**: `Succession(FadeIn(arrow), FadeOut(arrow))`; entrances are
  micro-drift fades (`FadeIn(m, shift=0.5*DOWN)`); group exits are `LaggedStart(*[FadeOut(x, shift=DOWN)...],
  lag_ratio=0.2)`, never a hard cut.
- **True unrolls over crossfades**: anything called "unroll/open/flatten" must preserve arc length —
  tracker + `always_redraw(Arc(radius=L/θ, start_angle=-PI/2-θ/2, angle=θ, arc_center=pin+UP*L/θ))`,
  θ: TAU→~0.03, pinned at the object's own tangent point. For N nested rings: unroll each around its own
  bottom pin, `LaggedStart` outermost-first — the staircase forms mid-air, then settles with a rigid
  lagged shift. (Video #2: keeping H=Rmax makes every strip's drop the same constant shift.)

## The pre-ship CRAFT AUDIT (run after the layout critique passes, BEFORE the 4K render)
Read the smoke render's frames/clips beat by beat and grade each visual beat against:
1. **Verb match** — does the motion literally perform the narrated verb? ("flip" must rotate ~π in
   flight; "unroll" must preserve length; "stack" must settle downward). A crossfade where a verb is
   spoken = FAIL.
2. **Block-slide smell** — any group moving as one rigid unit that should read as pieces? Add the lag fan.
3. **Formula provenance** — does any equation term that exists in the diagram get `Write`-from-nothing?
   Fly it in as a copy instead; check its color matches its diagram identity.
4. **Camera** — static through a spatial-attention shift (zoom in on the detail being discussed)? Moving
   during a formula beat (don't)? Every zoom restored before the next chapter?
5. **Dead air** — any block where all plays finish in <60% of the narration and nothing breathes?
   Stretch the travelling move to the block (tracker fraction), or add ONE ambient/idle motion.
6. **Duration invariance** — plays inside each voiceover block must total ≤ ~0.9× the audio (blocks are
   audio-bound); if a craft addition exceeds the slack, the total duration shifts and music/chapters
   must be redone. Verify total duration unchanged after the pass.
7. **Frame-bounds at END of block** — sample the LAST frame of each narration block (from the .srt cue
   ends), not arbitrary mid-block timestamps: mid-block frames miss elements written late in the block.
   Nothing may cross the frame edge. The tell-tale of a mispositioned stack is *empty space at the top +
   content clipped at the bottom* (video #3 shipped this: a 4-line antiderivative stack anchored at
   UP*1.6 pushed its last line off-screen). Budget stacked fraction-lines BEFORE writing: each MathTex
   fraction ≈ 1.1–1.3 units tall; frame is 8 — 4 such lines need to start ≈ UP*2.6 with ≤0.5 buffs.
Fix everything graded FAIL, re-render smoke, re-read the changed beats, THEN go 4K.
