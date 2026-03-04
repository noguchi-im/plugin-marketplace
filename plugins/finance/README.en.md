# finance

[日本語](README.md)

A collection of Claude Code skills for financial analysis (economics, investment products, stocks, portfolios) and investment decision support.

## Included Skills

### Public Skills (skills/)

| Skill | Description |
|-------|-------------|
| `finance-advisor` | Investment advisor. Orchestrates portfolio analysis and investment decision support |
| `stock-analyst` | Individual stock analysis and scoring |
| `etf-analyst` | ETF analysis and scoring |
| `reit-analyst` | REIT (Real Estate Investment Trust) analysis and scoring |

### Hidden Skills (skills-hidden/)

Infrastructure and specialized skills accessed through the Advisor.

| Skill | Description |
|-------|-------------|
| `analyst-catalog` | Analyst skill catalog and routing infrastructure |
| `boj-api` | Bank of Japan statistical data API integration |
| `macro-theme-analyst` | Macroeconomic theme analysis |
| `mbo-analyst` | MBO (Management Buyout) analysis |
| `report-collector` | Report collection infrastructure |
| `report-store` | Report storage and management infrastructure |
| `sector-analyst` | Sector analysis |

## Installation

Add this plugin directory to your Claude Code plugins configuration.

```bash
# Example: copy to your project's .claude/plugins
cp -r plugins/finance /path/to/your/project/.claude/plugins/
```

## Structure

```
finance/
├── .claude-plugin/
│   └── plugin.json           # Plugin definition
├── manifest.json              # Metadata
├── skills-hidden.yaml         # Hidden skills configuration
├── skills/                    # Public skills
│   ├── finance-advisor/
│   ├── stock-analyst/
│   ├── etf-analyst/
│   └── reit-analyst/
└── skills-hidden/             # Hidden skills (infrastructure)
    ├── analyst-catalog/
    ├── boj-api/
    ├── macro-theme-analyst/
    ├── mbo-analyst/
    ├── report-collector/
    ├── report-store/
    └── sector-analyst/
```

## License

[MIT License](../../LICENSE)
