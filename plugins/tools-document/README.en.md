# tools-document

[日本語](README.md)

A collection of document processing skills for Claude Code that handles reading, creating, and manipulating PDF, Word, PowerPoint, and Excel files.

## Included Skills

| Skill | Description |
|-------|-------------|
| `pdf` | PDF reading, creation, manipulation, form filling, OCR, and Japanese support |
| `docx` | Word document reading, creation, editing, track changes, and comments |
| `pptx` | PowerPoint reading, creation, template editing, and design guidelines |
| `xlsx` | Excel spreadsheet reading, creation, editing, and formula recalculation |

## Installation

Add this plugin directory to your Claude Code plugins configuration.

```bash
# Example: copy to your project's .claude/plugins
cp -r plugins/tools-document /path/to/your/project/.claude/plugins/
```

## Structure

```
tools-document/
├── .claude-plugin/
│   └── plugin.json          # Plugin definition
├── manifest.json             # Metadata
└── skills/
    ├── pdf/
    │   ├── SKILL.md          # PDF skill definition
    │   ├── references/       # Reference documents
    │   └── scripts/          # Helper scripts
    ├── docx/
    │   ├── SKILL.md          # Word skill definition
    │   ├── references/
    │   └── scripts/
    ├── pptx/
    │   ├── SKILL.md          # PowerPoint skill definition
    │   ├── references/
    │   └── scripts/
    └── xlsx/
        ├── SKILL.md          # Excel skill definition
        ├── references/
        └── scripts/
```

## Dependencies

Each skill automatically checks for required packages and attempts auto-installation if missing.
See each skill's `SKILL.md` for details.

## License

[MIT License](../../LICENSE)
