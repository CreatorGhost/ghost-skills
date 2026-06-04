# Contributing a skill

Each skill is one plugin under `plugins/`, registered in
`.claude-plugin/marketplace.json`.

## Add a new skill

1. **Scaffold the folders:**

   ```
   plugins/<skill-name>/
   ├── .claude-plugin/plugin.json
   ├── README.md
   └── skills/<skill-name>/
       ├── SKILL.md
       └── references/        # optional appendices
   ```

2. **`plugin.json`** — minimal manifest:

   ```json
   {
     "name": "<skill-name>",
     "version": "1.0.0",
     "description": "One line on what it does.",
     "author": { "name": "You", "email": "you@example.com" }
   }
   ```

3. **`SKILL.md`** — YAML frontmatter (`name`, `description`, optional
   `when_to_use`) then the instructions. Keep `description` trigger-rich and the
   body scannable (tables, numbered categories). Put long output templates or
   schemas in `references/` so they load only when needed.

4. **Register it** in `.claude-plugin/marketplace.json` under `plugins`:

   ```json
   {
     "name": "<skill-name>",
     "source": "./plugins/<skill-name>",
     "description": "...",
     "category": "design | dev | docs | ...",
     "version": "1.0.0"
   }
   ```

5. **Validate** with `claude plugin validate` (or `/plugin validate`), then add a
   row to the Skills table in the repo `README.md`.

## Conventions
- `description` is truncated at 1,536 chars in the listing — front-load the key
  use case and trigger phrases.
- Keep `SKILL.md` self-contained and concise; move reference material into
  `references/`.
- Skills are read-only by default unless the task explicitly asks for changes.
