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
/plugin marketplace add nogutetu/plugin-marketplace

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

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[MIT License](LICENSE)
