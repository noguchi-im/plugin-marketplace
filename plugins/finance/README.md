# finance

[English](README.en.md)

金融分析（経済・投資商品・株式・ポートフォリオ）と投資判断支援のClaude Code用スキル群です。

## 含まれるスキル

| スキル | 説明 |
|--------|------|
| `finance-advisor` | 金融クエリのルーター。質問の複雑さに応じて適切なアナリストに振り分け |
| `stock-analyst` | 個別株の分析・決算アップデート・決算プレビュー・レビュー |
| `etf-analyst` | ETFの分析・比較・レビュー |
| `reit-analyst` | REITの分析・比較・レビュー |

### 内部スキル（finance-advisor 経由で利用）

| スキル | 説明 |
|--------|------|
| `macro-theme-analyst` | マクロ経済テーマ分析 |
| `sector-analyst` | セクター分析 |
| `mbo-analyst` | MBO（経営陣買収）分析 |
| `report-store` | 分析レポートの保存・検索（SQLite） |
| `report-collector` | 外部金融データの収集 |
| `analyst-catalog` | アナリストの登録・評価管理 |
| `boj-api` | 日本銀行統計API連携 |

## インストール

```bash
# マーケットプレイスからインストール
/plugin marketplace add nogutetu/plugin-marketplace
/plugin install finance
```

## 構造

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

## ライセンス

[MIT License](../../LICENSE)
