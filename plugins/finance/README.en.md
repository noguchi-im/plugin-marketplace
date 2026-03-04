# finance

[日本語](README.md)

A collection of financial analysis skills for Claude Code covering economics, investment products, stocks, portfolios, and investment decision support.

## Included Skills

| Skill | Description |
|-------|-------------|
| `finance-advisor` | Financial query router. Dispatches to appropriate analysts based on query complexity |
| `stock-analyst` | Individual stock analysis, earnings updates, earnings previews, and reviews |
| `etf-analyst` | ETF analysis, comparison, and reviews |
| `reit-analyst` | REIT analysis, comparison, and reviews |

### Internal Skills (accessed via finance-advisor)

| Skill | Description |
|-------|-------------|
| `macro-theme-analyst` | Macro-economic theme analysis |
| `sector-analyst` | Sector analysis |
| `mbo-analyst` | MBO (management buyout) analysis |
| `report-store` | Analysis report storage and retrieval (SQLite) |
| `report-collector` | External financial data collection |
| `analyst-catalog` | Analyst registration and evaluation management |
| `boj-api` | Bank of Japan statistics API integration |

## Installation

```bash
# Install from marketplace
/plugin marketplace add noguchi-im/plugin-marketplace
/plugin install finance
```

## Structure

```
finance/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── finance-advisor/
│   │   ├── SKILL.md
│   │   └── references/
│   ├── stock-analyst/
│   │   ├── SKILL.md
│   │   └── references/
│   ├── etf-analyst/
│   │   ├── SKILL.md
│   │   └── references/
│   └── reit-analyst/
│       ├── SKILL.md
│       └── references/
└── skills-hidden/
    ├── macro-theme-analyst/
    ├── sector-analyst/
    ├── mbo-analyst/
    ├── report-store/
    ├── report-collector/
    ├── analyst-catalog/
    └── boj-api/
```

## License

[MIT License](../../LICENSE)
