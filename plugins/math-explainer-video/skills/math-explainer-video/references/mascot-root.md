# "Root" — the Lucid Science channel mascot (3b1b-style Pi-creature equivalent)

The channel (**Lucid Science**) has a recurring animated mascot, **Root**: the radical sign **√** with
two big eyes sitting on top of the vinculum. It's the Pi-creature of this channel. Reusable code:
`assets/root_buddy.py` (copy it next to `scene.py`; `from root_buddy import build_root, blink, look`).

## Design (locked)
- Green `#83C167` radical on the `#0e0e12` background, stroke ~17, round caps/joints.
- Shape: a small **tail** rising into a peak → deep **V** → up to the roof corner → horizontal vinculum.
  (NO extra notch, NO up-left hook — just tail, peak, deep-V, roof.)
- Two **big bold white eyes** (radius ~0.29, black pupils looking slightly up) resting ON TOP of the bar,
  toward the left. `build_root(scale)` returns the mobject with `.eyes` set.

## The usage RULE (owner's directive — follow it)
**Root appears ONLY for questions and headlines — never over the math.**
- ✅ Show him during: the **intro**, **chapter-title cards / headlines**, and **rhetorical questions**
  (e.g. "How fast are you going right NOW?").
- ❌ The instant an **equation or graph starts drawing**, he **slides off and is removed**
  (`self.play(buddy.animate.shift(RIGHT*4)); self.remove(buddy)`). He must never sit over formulas/curves.

## How to animate him (and NOT break audio sync)
- **Reveal** (channel open): big & centered — `Create(radical)` → `GrowFromCenter(eyes)` → `blink` → shrink
  and `to_corner(DR)`. Then he lives in that corner.
- **Idle life — keep him moving the WHOLE time he's on screen.** Call `look(scene, buddy)` (a little HOP +
  glance + blink) repeatedly in each block. Sprinkle 1–3 per block.
- **Persist across sections:** store `self.buddy = buddy`; carry him through `wipe()` with `self.wipe(buddy)`.
  A guarded idle inside `chapter_title` (`if buddy in self.mobjects: look(...)`) keeps him alive on title cards.
- **Re-summon later (proven in video #2):** after he's been removed, bring him back for a mid-video
  rhetorical question (e.g. the pizza-test "which one do you take?") and for the outro subscribe beat with
  `b = self.buddy.copy().scale(0.9).to_corner(DR, buff=0.4)`, `FadeIn(b, shift=LEFT*0.5)` + `look(...)`,
  then the usual slide-off before any numbers/equations draw. Same rule applies: questions/headlines only.
- **Never add duration.** Every `look()`/reveal play must fit inside the current voiceover block's audio
  slack (block waits for max(audio, plays)). Verify the rendered total is unchanged so music + chapter
  timestamps stay valid — this is how you "inject the mascot without touching the audio."

## Verifying
Extract frames across the mascot's whole span (reveal, corner-idle, question, the slide-off) and Read them
— confirm he's in the corner, never overlapping the math, and gone once equations/graphs begin. Static PNG
frames are the reliable check (QuickTime caches video and will show stale frames).
