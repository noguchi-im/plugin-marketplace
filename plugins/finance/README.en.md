# finance

[日本語](README.md)

Financial analysis skills for economics, investment products, stocks, portfolios, and investment decision support.

## Configuration override

To override plugin settings (e.g. `base_dir`), use the project's `.claude/settings.json` or `settings.local.json`. The default for `base_dir` is `home/finance` (base path for outputs and learning data).

## skills-hidden

Some skills live in `skills-hidden/` and are not invokable via the Skill tool. A calling skill must Read `skills-hidden/<name>/SKILL.md` and execute its procedures inline. Public skills such as finance-advisor use hidden skills (e.g. report-store, analyst-catalog) internally in this way.

## Namespace

Invoke skills and commands as `<plugin-name>:<resource-name>`. Examples: `finance:finance-advisor`, `finance:stock`, `/finance:stock NVDA`.

## Workspace (temporary files)

Use the plugin's base_dir for temporary work: place files under `<base_dir>/workspace/`. If you override `base_dir` in settings, the same applies. Prefer the naming convention `YYYYMMDD-<label>-<seq>` for workspace subdirectories.
