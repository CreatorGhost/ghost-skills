# Curriculum map + launch plan

A full CBSE Class 9–12 maths curriculum was mapped to lessons, each rated for visual-fit and given a
concept-gem hook. **Don't regenerate it — read these files.** (Regenerate only to add a subject like
physics, or to refresh for a syllabus change.)

## Files (in `~/code/maths/curriculum/`)
- **`curriculum.xlsx`** — 257 lessons. Sheets: `All Lessons` + `Class 9/10/11/12` + `Launch Plan`.
  Columns: Class · Chapter · Topic · Subtopic · **Visual fit** (🟢High / 🟡Medium / ⬜Low, colour-coded) ·
  Gem idea (one-line hook) · Est minutes · Notes.
- **`curriculum.csv`** — same rows, plain text.
- **`launch_plan.csv`** — the recommended first 12 videos (order, class, chapter, title, why).

Coverage: Class 9 = 64 rows, 10 = 48, 11 = 77, 12 = 68. **186 of 257 are High visual-fit** (strong
3b1b-style candidates, each with a ready hook). Pick green rows first.

## The 12-video launch plan (recommended order)
1. **Why sin² + cos² = 1 (It's Just a Hidden Triangle)** — C10 — *the pilot, already built* (source now lives in the flat `src/` layout; deliverables in `Math/<Topic>/`)
2. What Is a Derivative? Slide the Secant Until It Kisses — C11
3. Why Is a Circle's Area πr²? Unroll It and See — C10
4. Multiplying by i Is Just a 90° Turn — C11
5. One Cone, Four Curves: Circle, Ellipse, Parabola, Hyperbola — C11
6. Probability Is Just Counting the Squares That Light Up — C10
7. The Determinant Is How Much Space Got Stretched — C12
8. See (a+b)² — Algebra You Can Actually Touch — C9
9. Pythagoras Proves Itself: The Triangle Inside the Triangle — C10
10. Gauss's Trick: How a Kid Summed 1 to 100 in Seconds — C11
11. Where Sine Waves Come From (Unroll the Circle) — C11
12. The Distance Formula Is Secretly Pythagoras in Disguise — C10

## How it was generated (to redo for physics/chem or a refresh)
A Workflow fan-out: one agent per class (9/10/11/12) researched the NCERT syllabus and returned a
structured row per (chapter, topic, subtopic) with `visual_fit`, `gem_idea`, `est_minutes`, `notes`
(JSON-schema-constrained); a final synthesis agent picked the 12-video launch plan. The combined JSON
was then written to CSV + XLSX with `openpyxl` (one sheet per class, visual-fit colour-coded). To repeat
for a new subject, reuse that workflow shape — swap "Mathematics" for the subject and adjust the
visual-fit guidance (e.g. for physics: fields, waves, motion, optics = High; numerical/measurement = Low).
