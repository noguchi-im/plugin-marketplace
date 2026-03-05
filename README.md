# Plugin Marketplace

[English](README.en.md)

Claude Code用のPluginコレクションです。Skills、MCP Servers、Hooksなど、Claude Codeの機能を拡張するPluginを公開しています。

## Plugin一覧

| Plugin | 種類 | 説明 |
|--------|------|------|
| [tools-document](plugins/tools-document/) | Skill | PDF・Word・PowerPoint・Excel の読取・作成・操作を行うドキュメント処理スキル群 |
| [finance](plugins/finance/) | Skill | 金融分析（経済・投資商品・株式・ポートフォリオ）と投資判断支援のスキル群 |

## インストール

Claude Code の Plugin Marketplace コマンドでインストールできます。

```bash
# マーケットプレイスを追加
/plugin marketplace add noguchi-im/plugin-marketplace

# 個別のPluginをインストール
/plugin install tools-document
/plugin install finance
```

## リポジトリ構造

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

各Pluginは `plugins/` ディレクトリ配下に独立したフォルダとして配置されます。
Pluginの詳細は各フォルダ内の `README.md` を参照してください。

## 各 Plugin の共通のきまり

- **設定の上書き**: 各 Plugin の設定変数（例: finance の `base_dir`）は、プロジェクトの `.claude/settings.json` または `settings.local.json` で上書きできます。
- **skills-hidden**: 一部の Plugin では、Skill ツールから呼び出せない隠蔽スキルがあります。呼び出し元が Read で該当する SKILL.md を読み、手順をインラインで実行します。詳細は各 Plugin の README を参照してください。
- **名前空間**: スキル・コマンドは `plugin-name:resource-name` の形式で呼び出します（例: `finance:stock`、`tools-document:pdf`）。
- **workspace**: Plugin が base_dir を定義している場合、一時作業領域はその base_dir 配下の `workspace/` に置きます。定義していない Plugin ではプロジェクトのルールに従います。

詳細は各 Plugin の README および CLAUDE.md を参照してください。

## コントリビュート

Pluginの追加・改善は歓迎です。[CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

## ライセンス

[MIT License](LICENSE)
