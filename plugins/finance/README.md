# finance

[English](README.en.md)

金融分析（経済・投資商品・株式・ポートフォリオ）と投資判断支援を行うClaude Code用スキル群です。

## 含まれるスキル

### 公開スキル（skills/）

| スキル | 説明 |
|--------|------|
| `finance-advisor` | 投資アドバイザー。ポートフォリオ分析・投資判断支援の統括スキル |
| `stock-analyst` | 個別株式の分析・スコアリング |
| `etf-analyst` | ETFの分析・スコアリング |
| `reit-analyst` | REIT（不動産投資信託）の分析・スコアリング |

### 非公開スキル（skills-hidden/）

Advisor経由でアクセスされる基盤・特化スキル群です。

| スキル | 説明 |
|--------|------|
| `analyst-catalog` | アナリストスキルのカタログ・ルーティング基盤 |
| `boj-api` | 日本銀行統計データAPI連携 |
| `macro-theme-analyst` | マクロ経済テーマ分析 |
| `mbo-analyst` | MBO（経営者による買収）分析 |
| `report-collector` | レポート収集基盤 |
| `report-store` | レポート保存・管理基盤 |
| `sector-analyst` | セクター分析 |

## インストール

このPluginディレクトリをClaude Codeのplugins設定に追加してください。

```bash
# 例: プロジェクトの.claude/pluginsにコピー
cp -r plugins/finance /path/to/your/project/.claude/plugins/
```

## 構造

```
finance/
├── .claude-plugin/
│   └── plugin.json           # プラグイン定義
├── manifest.json              # メタデータ
├── skills-hidden.yaml         # 非公開スキルの設定
├── skills/                    # 公開スキル
│   ├── finance-advisor/
│   ├── stock-analyst/
│   ├── etf-analyst/
│   └── reit-analyst/
└── skills-hidden/             # 非公開スキル（基盤サービス）
    ├── analyst-catalog/
    ├── boj-api/
    ├── macro-theme-analyst/
    ├── mbo-analyst/
    ├── report-collector/
    ├── report-store/
    └── sector-analyst/
```

## ライセンス

[MIT License](../../LICENSE)
