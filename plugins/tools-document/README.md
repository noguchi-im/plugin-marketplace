# tools-document

[English](README.en.md)

PDF・Word・PowerPoint・Excel の読取・作成・操作を行うClaude Code用ドキュメント処理スキル群です。

## 含まれるスキル

| スキル | 説明 |
|--------|------|
| `pdf` | PDFファイルの読取・作成・操作、フォーム記入、OCR、日本語対応 |
| `docx` | Word文書の読取・新規作成・既存編集、変更履歴・コメント操作 |
| `pptx` | PowerPointの読取・新規作成・テンプレート編集、デザインガイドライン |
| `xlsx` | Excelスプレッドシートの読取・作成・編集、数式再計算 |

## インストール

```bash
# マーケットプレイスからインストール
/plugin marketplace add noguchi-im/plugin-marketplace
/plugin install tools-document
```

## 構造

```
tools-document/
├── .claude-plugin/
│   └── plugin.json          # プラグイン定義
└── skills/
    ├── pdf/
    │   ├── SKILL.md          # PDFスキル定義
    │   ├── references/       # 参照ドキュメント
    │   └── scripts/          # ヘルパースクリプト
    ├── docx/
    │   ├── SKILL.md          # Wordスキル定義
    │   ├── references/
    │   └── scripts/
    ├── pptx/
    │   ├── SKILL.md          # PowerPointスキル定義
    │   ├── references/
    │   └── scripts/
    └── xlsx/
        ├── SKILL.md          # Excelスキル定義
        ├── references/
        └── scripts/
```

## 依存関係

各スキルは使用時に依存パッケージを自動チェックし、未インストールの場合は自動インストールを試みます。
詳細は各スキルの `SKILL.md` を参照してください。

## ライセンス

[MIT License](../../LICENSE)
