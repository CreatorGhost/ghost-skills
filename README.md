<h1 align="center">👻 ghost-skills</h1>

<p align="center">
  <strong>Installable Claude skills that punch above their weight.</strong><br>
  Senior-grade, reference-backed skills you can drop into any project — install the whole marketplace or copy one skill.
</p>

<p align="center">
  <a href="#-install">Install</a> •
  <a href="#-skills">Skills</a> •
  <a href="#-whats-inside">What's inside</a> •
  <a href="CONTRIBUTING.md">Contributing</a> •
  <a href="LICENSE">License</a>
</p>

<p align="center">
  <img alt="skills" src="https://img.shields.io/badge/skills-6-8b5cf6">
  <img alt="Claude Code" src="https://img.shields.io/badge/Claude%20Code-plugin-d97757">
  <img alt="platforms" src="https://img.shields.io/badge/platforms-web%20%C2%B7%20iOS%20%C2%B7%20Android%20%C2%B7%20desktop-2563eb">
  <img alt="license" src="https://img.shields.io/badge/license-MIT-3fb950">
</p>

---

## What is this?

`ghost-skills` is a marketplace of installable [Claude](https://claude.com/claude-code) skills. Each skill is **self-contained**, **reference-backed**, and follows the [Agent Skills](https://agentskills.io) open standard — so it works in Claude Code (CLI, desktop, IDE) and any compatible tool.

Add the marketplace once and install any skill with a single command, or copy a skill folder straight into your project.

## 🧩 Skills

| Skill | What it does |
|-------|--------------|
| [**senior-ux-audit**](plugins/senior-ux-audit) | A principal-level UI/UX audit (web · iOS · Android · desktop) from your codebase — heuristics, accessibility, performance vitals, and a severity-rated, prioritized report with a 30/60/90 roadmap. |
| [**agentic-ai-backend-audit**](plugins/agentic-ai-backend-audit) | A senior adversarial audit of an AI-agent-built / agentic backend — 18 lenses across access control, prompt & agent safety, PII & data leakage, reliability, observability/evals/governance, and AI code smells. Severity-rated, `file:line`-cited, ends in a Ship/Fix/Block verdict. |
| [**test-case-author**](plugins/test-case-author) | Writes tests that catch real bugs. It tests the shipped artifact, asserts behavior instead of liveness, proves red before green, covers boundaries and silent failures, and verifies the fix in the built product. |
| [**math-explainer-video**](plugins/math-explainer-video) | Builds intuition-first math explainer videos with Manim, including scripts, synced English or Hinglish narration, pre-render QA, frame critique, 4K output, music, chapters, and thumbnails. |
| [**ai-video-dubbing**](plugins/ai-video-dubbing) | Builds and debugs translated video dubbing and recap pipelines, with subtitle-timed translation, timestamp-anchored TTS, sync diagnostics, and checks against the final rendered video. |
| [**unslop**](plugins/unslop) | Edits prose to remove AI writing habits while preserving meaning, tone, rhythm, and a distinct human voice. |
| [**open-katana**](plugins/open-katana) | Builds Katana-style kinetic motion graphics from a script with HyperFrames: word-synced narration, hero type, blade slices, a 3D camera tunnel, sound, and a slow-motion review of the render. |

See [CONTRIBUTING.md](CONTRIBUTING.md) to add another skill.

## 📦 Install

Choose the method that fits your setup. The Claude Code marketplace is the simplest way to install and update these skills as plugins.

### 1. Claude Code marketplace

Add the marketplace once:

```text
/plugin marketplace add CreatorGhost/ghost-skills
```

Then install any skill:

| Skill | Install command |
|-------|-----------------|
| `senior-ux-audit` | `/plugin install senior-ux-audit@ghost-skills` |
| `agentic-ai-backend-audit` | `/plugin install agentic-ai-backend-audit@ghost-skills` |
| `test-case-author` | `/plugin install test-case-author@ghost-skills` |
| `math-explainer-video` | `/plugin install math-explainer-video@ghost-skills` |
| `ai-video-dubbing` | `/plugin install ai-video-dubbing@ghost-skills` |
| `unslop` | `/plugin install unslop@ghost-skills` |
| `open-katana` | `/plugin install open-katana@ghost-skills` |

To install all seven, run every install command in the table after adding the marketplace. From a local clone, use `/plugin marketplace add /path/to/ghost-skills` instead.

### 2. npx for multiple AI agents

[SkillFish](https://github.com/knoxgraeme/skillfish) and [Vercel `skills`](https://github.com/vercel-labs/skills) can discover the skill folders in this repository and install them for supported agents.

```bash
npx skillfish add CreatorGhost/ghost-skills
# or
npx skills add CreatorGhost/ghost-skills
```

List the available skills before choosing one:

```bash
npx skills add CreatorGhost/ghost-skills --list
```

Install one skill directly by setting `skill_name` to a name from the table:

```bash
skill_name=unslop
npx skills add "https://github.com/CreatorGhost/ghost-skills/tree/main/plugins/$skill_name/skills/$skill_name"
```

### 3. Manual copy

Clone the repository, then copy a skill into your global or project-level skills directory:

```bash
git clone https://github.com/CreatorGhost/ghost-skills.git
cd ghost-skills
skill_name=unslop
cp -r "plugins/$skill_name/skills/$skill_name" ~/.claude/skills/
# or, for the current project only
cp -r "plugins/$skill_name/skills/$skill_name" .claude/skills/
```

Change `skill_name` to install a different skill.

## 🚀 Invoke & use

Invoke a skill directly, or describe the job in plain language. Claude can load the matching skill from its description.

```text
/senior-ux-audit
/agentic-ai-backend-audit
/test-case-author
/math-explainer-video
/ai-video-dubbing
/unslop
/open-katana

Audit the UI/UX of this app
Review this agentic backend before I ship it
Write regression tests that prove this bug is fixed
Make a Manim explainer about the Fourier transform
Fix the voiceover drift in this translated video
Make this draft sound like a person wrote it
Make a Katana-style motion graphic from this script
```

Each plugin README documents its workflow, requirements, and output.

### ✅ Best practices

- **Run code-focused skills from the project root** so they inspect the real implementation and build output.
- **Provide the real artifact** when using a media skill. For dubbing, include the source video. For a math explainer, specify the topic, audience, language, and target length.
- **Name the scope**. Point audits at the changed files or important flows, and tell the test author which behavior failed.
- **Check each plugin's requirements** before starting. The video skills need local media tools and may need API keys for speech or image services.
- **Treat audit results as read-only**. Ask for implementation in a separate step when you want the reported issues fixed.

## 📂 What's inside

```text
ghost-skills/
├── .claude-plugin/
│   └── marketplace.json              # marketplace registry
├── plugins/
│   ├── senior-ux-audit/
│   ├── agentic-ai-backend-audit/
│   ├── test-case-author/
│   ├── math-explainer-video/
│   ├── ai-video-dubbing/
│   ├── open-katana/
│   └── unslop/
│       ├── .claude-plugin/plugin.json
│       ├── README.md
│       └── skills/<skill-name>/
│           ├── SKILL.md               # skill instructions
│           ├── references/            # supporting playbooks
│           ├── scripts/               # optional helpers
│           └── assets/                # optional templates
├── CONTRIBUTING.md
└── LICENSE
```

## 🤝 Contributing

Each skill is one folder under `plugins/` plus one entry in `marketplace.json`. The full recipe is in **[CONTRIBUTING.md](CONTRIBUTING.md)**.

## Author

**Aditya Pratap Singh** — [@CreatorGhost](https://github.com/CreatorGhost)

## License

[MIT](LICENSE)
