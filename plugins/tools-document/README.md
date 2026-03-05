# tools-document

[English](README.en.md)

PDF・Word・PowerPoint・Excel の読取・作成・操作を行う Claude Code 用ドキュメント処理スキル群です。

## 含まれるスキル

| スキル | 説明 |
|--------|------|
| pdf | PDF の読取・作成・操作、フォーム記入、OCR |
| docx | Word 文書の読取・作成・編集 |
| pptx | PowerPoint の読取・作成・テンプレート編集 |
| xlsx | Excel の読取・作成・編集 |

## 設定の上書き

本 Plugin では現在、設定変数（base_dir 等）を定義していません。将来、設定を追加した場合は、プロジェクトの `.claude/settings.json` または `settings.local.json` で上書きできます。

## 名前空間

スキル・コマンドは `<plugin-name>:<resource-name>` で呼び出します。例: `tools-document:pdf`、`tools-document:docx`、`/tools-document:pdf <path>`。

## 一時作業領域（workspace）

本 Plugin では base_dir を定義していません。作業用ファイルの配置は、プロジェクトのルール（AGENTS.md やルートの CLAUDE.md 等）に従ってください。
