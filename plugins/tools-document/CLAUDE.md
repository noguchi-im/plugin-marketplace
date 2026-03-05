# tools-document plugin: execution rules

This document defines the rules the Agent must follow when executing skills in this plugin. Read this file together with `plugin.json` and the relevant SKILL.md files.

## Path variable resolution

This plugin does not define settings variables (e.g. no `base_dir` in `plugin.json`). Paths in SKILL.md are used as written; no variable substitution is required.

## Namespace

Skills and commands in this plugin are invoked with the `<plugin-name>:<resource-name>` namespace.

- Examples: `tools-document:pdf`, `tools-document:docx`, `tools-document:pptx`, `tools-document:xlsx`, `/tools-document:pdf <path>`

## Data directory and workspace

This plugin does not define a `base_dir`. For working files and temporary outputs, follow the project's own rules (e.g. project root workspace or paths specified in the project's CLAUDE.md / AGENTS.md).
