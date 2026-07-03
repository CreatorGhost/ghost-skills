# Lucid Science — Thumbnail Style Guide (LOCKED — use for EVERY video)

The look the owner approved (Video #1). Keep these constants identical across all videos so the channel
reads as one consistent brand; only the **diagram** and the **hook text** change per topic.

## The locked constants (never change)
- **Canvas:** 1280×720 (16:9).
- **Background:** solid dark charcoal `#0e0e12` (near-black), subtle vignette. No busy backgrounds.
- **Layout:** the topic's key **visual on the LEFT half**, big **hook text on the RIGHT half**.
- **Palette (3Blue1Brown-style neon):**
  - Blue `#58C4DD` = the main curve/object (glowing)
  - Yellow `#F5C542` = the key accent line / the "answer" / the label underline
  - White = the big hook text
  - Green `#83C167` = the mascot + the √ in the wordmark
- **Hook text (right):** 2–4 HUGE glyphs — a formula (`dy/dx = ?`) or a very short question. Bold, white,
  glowing. Below it a small **yellow underlined label** (e.g. `SEE IT`, `WHY?`, `समझो`).
- **Mascot:** the green **Root (√ with big white eyes)** peeking from the **bottom-right corner**, friendly.
- **NO channel name on the thumbnail** — keep it clean. The name lives on the **logo/avatar**
  (`logo_lucid_science.png`), which YouTube shows next to every video anyway. Don't clutter the thumbnail.
- **Feel:** minimal, high-contrast, readable at tiny size, cinematic soft glow. Never cluttered.

## Reusable workflow (this is how #1 was made — repeat it)
1. **Generate the base** with gpt-image-2 (`size 1536x1024`), prompt template below. Let the model draw the
   diagram + hook + mascot. (Text like `dy/dx`, `y=x^2`, `SEE IT` renders reliably; keep in-image text
   ENGLISH/symbols — the model garbles Devanagari.)
2. **Crop to 16:9** keeping the mascot: `ffmpeg -i base.png -vf "crop=1536:864,scale=1280:720" out.png`
   (center crop; if the mascot sits very low, bias the crop upward). That's it — no wordmark overlay.

## gpt-image-2 PROMPT TEMPLATE (fill the two [BRACKETS] per video)
> YouTube thumbnail, 16:9, dark charcoal `#0e0e12` background, high-contrast, bold and clean, 3Blue1Brown
> neon style. LEFT half: **[THE VIDEO'S KEY VISUAL — e.g. a glowing blue curve / shape / diagram, with a
> bright yellow accent line or highlight and a small glowing dot at the key point]**. RIGHT half: very large
> bold white text **"[HOOK — a formula or 2–4 word question]"**, and a smaller yellow underlined label
> **"[LABEL — SEE IT / WHY? / etc.]"** beneath it. A friendly green square-root mascot with two big white
> eyes peeking from the bottom-right corner. Minimal, punchy, readable when small, cinematic soft glow.
> (No channel name — keep the thumbnail clean; the name is on the logo/avatar.)

Example (Video #1): visual = "glowing blue parabola y=x² with a yellow tangent line touching at a point";
hook = "dy/dx = ?"; label = "SEE IT".
