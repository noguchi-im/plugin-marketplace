# tools-document

[日本語](README.md)

Document processing skills for reading, creating, and manipulating PDF, Word, PowerPoint, and Excel files.

## Included skills

| Skill | Description |
|-------|-------------|
| pdf | PDF read, create, manipulate, form fill, OCR |
| docx | Word document read, create, edit |
| pptx | PowerPoint read, create, template edit |
| xlsx | Excel read, create, edit |

## Configuration override

This plugin does not define settings variables (e.g. base_dir) at this time. If settings are added in the future, you can override them in the project's `.claude/settings.json` or `settings.local.json`.

## Namespace

Invoke skills and commands as `<plugin-name>:<resource-name>`. Examples: `tools-document:pdf`, `tools-document:docx`, `/tools-document:pdf <path>`.

## Workspace (temporary files)

This plugin does not define a base_dir. For working files, follow your project's rules (e.g. AGENTS.md or the root CLAUDE.md).
