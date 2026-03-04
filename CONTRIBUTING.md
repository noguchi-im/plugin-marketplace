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

### 2. `.claude-plugin/plugin.json` を作成 / Create `.claude-plugin/plugin.json`

各Pluginには `.claude-plugin/plugin.json` が必須です。

Each plugin must include a `.claude-plugin/plugin.json`.

```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "type": "skill",
  "description": "Plugin description",
  "skills": [
    {
      "name": "skill-name",
      "description": "Skill description",
      "path": "skills/skill-name.md"
    }
  ]
}
```

**フィールド説明 / Field Descriptions:**

| フィールド / Field | 必須 / Required | 説明 / Description |
|---|---|---|
| `name` | Yes | Plugin名（ディレクトリ名と一致） / Plugin name (must match directory name) |
| `version` | Yes | セマンティックバージョニング / Semantic versioning |
| `type` | Yes | `skill` など / e.g., `skill` |
| `description` | Yes | 説明文 / Description |
| `skills` | Yes | スキル定義の配列 / Array of skill definitions |

### 3. README.md を作成 / Create README.md

各Pluginに `README.md`（日本語）と `README.en.md`（英語）を作成してください。

Create `README.md` (Japanese) and `README.en.md` (English) for each plugin.

以下の内容を含めてください / Include the following:
- Pluginの概要 / Plugin overview
- インストール方法 / Installation instructions
- 使い方 / Usage
- 設定オプション（あれば） / Configuration options (if any)

### 4. `.claude-plugin/marketplace.json` を更新 / Update `.claude-plugin/marketplace.json`

ルートの `.claude-plugin/marketplace.json` にPluginの情報を追加してください。

Add your plugin's information to the root `.claude-plugin/marketplace.json`.

## ディレクトリ構造の例 / Example Directory Structure

```
plugins/my-skill/
├── .claude-plugin/
│   └── plugin.json
├── README.md
├── README.en.md
└── skills/
    └── skill-name.md
```
