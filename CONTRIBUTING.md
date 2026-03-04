# コントリビューションガイド / Contributing Guide

## Pluginの追加方法 / How to Add a Plugin

### 1. ディレクトリを作成 / Create a Directory

`plugins/` 配下にPlugin名のディレクトリを作成してください。

Create a directory with your plugin name under `plugins/`.

```
plugins/<your-plugin-name>/
```

**命名規則 / Naming Convention:**
- 小文字のケバブケース（例: `my-awesome-skill`）
- Lowercase kebab-case (e.g., `my-awesome-skill`)

### 2. manifest.json を作成 / Create manifest.json

各Pluginには `manifest.json` が必須です。

Each plugin must include a `manifest.json`.

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "type": "skill | mcp-server | hook",
  "description": {
    "ja": "日本語の説明",
    "en": "English description"
  },
  "author": "your-name",
  "license": "MIT",
  "tags": ["tag1", "tag2"],
  "claude_code_version": ">=1.0.0",
  "entry": "skill.md | index.ts | hook.sh"
}
```

**フィールド説明 / Field Descriptions:**

| フィールド / Field | 必須 / Required | 説明 / Description |
|---|---|---|
| `name` | Yes | Plugin名（ディレクトリ名と一致） / Plugin name (must match directory name) |
| `version` | Yes | セマンティックバージョニング / Semantic versioning |
| `type` | Yes | `skill`, `mcp-server`, `hook` のいずれか / One of `skill`, `mcp-server`, `hook` |
| `description` | Yes | 日英の説明文 / Description in Japanese and English |
| `author` | Yes | 作者名 / Author name |
| `license` | Yes | ライセンス / License |
| `tags` | No | 検索用タグ / Tags for search |
| `claude_code_version` | No | 対応するClaude Codeのバージョン / Compatible Claude Code version |
| `entry` | Yes | エントリーポイントファイル / Entry point file |

### 3. README.md を作成 / Create README.md

各Pluginに `README.md`（日本語）と `README.en.md`（英語）を作成してください。

Create `README.md` (Japanese) and `README.en.md` (English) for each plugin.

以下の内容を含めてください / Include the following:
- Pluginの概要 / Plugin overview
- インストール方法 / Installation instructions
- 使い方 / Usage
- 設定オプション（あれば） / Configuration options (if any)

### 4. catalog.json を更新 / Update catalog.json

ルートの `catalog.json` にPluginの情報を追加してください。

Add your plugin's information to the root `catalog.json`.

## ディレクトリ構造の例 / Example Directory Structure

```
plugins/my-skill/
├── manifest.json
├── README.md
├── README.en.md
└── skill.md
```
