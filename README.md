# Plugin Marketplace

[English](README.en.md)

Claude Code用のPluginコレクションです。Skills、MCP Servers、Hooksなど、Claude Codeの機能を拡張するPluginを公開しています。

## Plugin一覧

| Plugin | 種類 | 説明 |
|--------|------|------|
| [tools-document](plugins/tools-document/) | Skill | PDF・Word・PowerPoint・Excel の読取・作成・操作を行うドキュメント処理スキル群 |
| [finance](plugins/finance/) | Skill | 金融分析（経済・投資商品・株式・ポートフォリオ）と投資判断支援のスキル群 |

## 利用方法

### Skills

Skillファイル（`.md`）をClaude Codeの設定ディレクトリにコピーしてください。

```bash
# 例: skillをインストール
cp plugins/<plugin-name>/skill.md ~/.claude/commands/<skill-name>.md
```

### MCP Servers

各MCP Serverの `README.md` に記載のインストール手順に従ってください。

### Hooks

各Hookの `README.md` に記載の設定手順に従ってください。

## リポジトリ構造

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

各Pluginは `plugins/` ディレクトリ配下に独立したフォルダとして配置されます。
Pluginの詳細は各フォルダ内の `README.md` を参照してください。

## コントリビュート

Pluginの追加・改善は歓迎です。[CONTRIBUTING.md](CONTRIBUTING.md) を参照してください。

## ライセンス

[MIT License](LICENSE)
