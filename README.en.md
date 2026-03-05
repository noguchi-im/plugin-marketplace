# Plugin Marketplace

[日本語](README.md)

A collection of plugins for Claude Code. This repository hosts plugins that extend Claude Code's capabilities, including Skills, MCP Servers, and Hooks.

## Plugin List

| Plugin | Type | Description |
|--------|------|-------------|
| [tools-document](plugins/tools-document/) | Skill | Document processing skills for reading, creating, and manipulating PDF, Word, PowerPoint, and Excel files |
| [finance](plugins/finance/) | Skill | Financial analysis skills for economics, investment products, stocks, portfolios, and investment decision support |

## Installation

Install via Claude Code's Plugin Marketplace commands.

```bash
# Add the marketplace
/plugin marketplace add noguchi-im/plugin-marketplace

# Install individual plugins
/plugin install tools-document
/plugin install finance
```

## Repository Structure

```
plugin-marketplace/
├── .claude-plugin/
│   └── marketplace.json
├── README.md
├── README.en.md
├── CONTRIBUTING.md
├── LICENSE
└── plugins/
    └── <plugin-name>/
        ├── .claude-plugin/
        │   └── plugin.json
        ├── README.md
        └── ...
```

Each plugin is placed as an independent folder under the `plugins/` directory.
See the `README.md` in each folder for details.

## Common conventions for all plugins

- **Configuration override**: Plugin settings (e.g. finance's `base_dir`) can be overridden in the project's `.claude/settings.json` or `settings.local.json`.
- **skills-hidden**: Some plugins have hidden skills that are not invokable via the Skill tool. Callers Read the relevant SKILL.md and execute procedures inline. See each plugin's README for details.
- **Namespace**: Invoke skills and commands as `plugin-name:resource-name` (e.g. `finance:stock`, `tools-document:pdf`).
- **Workspace**: If a plugin defines a base_dir, use `<base_dir>/workspace/` for temporary files. If it does not, follow the project's rules.

For details, see each plugin's README and CLAUDE.md.

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[MIT License](LICENSE)
