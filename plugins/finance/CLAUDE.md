# finance plugin: execution rules

This document defines the rules the Agent must follow when executing skills in this plugin. Read this file together with `plugin.json` and the relevant SKILL.md files.

## Path variable resolution

When the Agent finds `<variable-name>` (e.g. `<base_dir>`) in a SKILL.md:

1. Read this plugin's `plugin.json`.
2. Get the value of `settings.<variable-name>` (use the overridden value if the user has set one, otherwise use `default`).
3. Replace `<variable-name>` in the path with that value.
4. Perform file operations using the resolved path.

Example: `<base_dir>/report-store/reports/` is resolved using the `base_dir` setting from `plugin.json` (or the user's override).

## skills-hidden

Some skills in this plugin are in `skills-hidden/`. They are not exposed to Claude Code's skill discovery, so they cannot be invoked via the Skill tool.

**To use a hidden skill:** The caller must use the Read tool to load `skills-hidden/<name>/SKILL.md` and execute its procedures inline. Do not expect to invoke hidden skills as normal skills. Public skills (e.g. finance-advisor) may reference hidden skills (e.g. report-store, analyst-catalog) in this way.

## Namespace

Skills and commands in this plugin are invoked with the `<plugin-name>:<resource-name>` namespace.

- Examples: `finance:finance-advisor`, `finance:stock`, `/finance:stock NVDA`

## Data directory and workspace

- **Data location:** Data paths for this plugin follow the variables defined in `plugin.json`'s `settings` (e.g. `base_dir`). Do not create files directly under the data directory until a skill has defined that structure.
- **Work-in-progress files:** Place temporary or working files under **`<base_dir>/workspace/`** (i.e. the plugin's workspace is under its own base_dir). Use the naming convention `YYYYMMDD-<label>-<seq>` for workspace subdirectories (e.g. `20260305-stock-001/`). Move or remove them when done.
