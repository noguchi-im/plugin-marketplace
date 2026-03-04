# Plugin Marketplace

[日本語](README.md)

A collection of plugins for Claude Code. This repository hosts plugins that extend Claude Code's capabilities, including Skills, MCP Servers, and Hooks.

## Plugin List

| Plugin | Type | Description |
|--------|------|-------------|
| [tools-document](plugins/tools-document/) | Skill | Document processing skills for reading, creating, and manipulating PDF, Word, PowerPoint, and Excel files |

## Usage

### Skills

Copy the skill file (`.md`) to your Claude Code configuration directory.

```bash
# Example: install a skill
cp plugins/<plugin-name>/skill.md ~/.claude/commands/<skill-name>.md
```

### MCP Servers

Follow the installation instructions in each MCP Server's `README.md`.

### Hooks

Follow the setup instructions in each Hook's `README.md`.

## Repository Structure

```
plugin-marketplace/
├── README.md
├── README.en.md
├── CONTRIBUTING.md
├── LICENSE
├── catalog.json
└── plugins/
    └── <plugin-name>/
        ├── manifest.json
        ├── README.md
        └── ...
```

Each plugin is placed as an independent folder under the `plugins/` directory.
See the `README.md` in each folder for details.

## Contributing

Contributions are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

[MIT License](LICENSE)
