---
name: docx
description: Word 文書（.docx）の読取・新規作成・既存編集に関する知識と文書操作パイプラインを提供する。テキスト抽出、レポート作成、既存文書の XML 編集、変更履歴・コメント操作、.doc 変換が必要な時に使用する。
disable-model-invocation: false
allowed-tools: Read, Glob, Bash, Write, Edit
---

あなたは docx スキルとして動作している。
Word 文書（.docx）の読取・新規作成・既存編集に関する知識と文書操作パイプラインを提供する。

## クイックリファレンス

| タスク | アプローチ |
|--------|----------|
| テキスト抽出 | `pandoc` で Markdown 変換 or unpack で生 XML |
| 新規作成 | `docx-js`（JavaScript）で生成 → validate |
| 既存編集 | unpack → XML 編集 → validate → pack |
| .doc → .docx | LibreOffice で変換 |
| 変更履歴承認 | `accept_changes.py` |

## 環境セットアップ

**依存関係は使用前に自動チェックし、未インストールなら自動インストールする。**
自動インストール失敗時はインストールコマンドをユーザーに提示する。

### 依存関係チェック・自動インストール

| 依存 | 必要な機能 | チェック | 自動インストール |
|------|-----------|---------|-----------------|
| docx (npm) | 新規作成 | `npm list -g docx >/dev/null 2>&1` | `npm install -g docx` |
| defusedxml, lxml | スクリプト全般 | `python3 -c "import defusedxml; import lxml"` | `pip install defusedxml lxml` |
| pandoc | テキスト抽出 | `which pandoc` | apt: `sudo apt install pandoc` / brew: `brew install pandoc` |
| libreoffice | .doc 変換、変更履歴承認 | `which soffice` | apt: `sudo apt install libreoffice` / brew: `brew install --cask libreoffice` |
| poppler-utils | PDF → 画像変換 | `which pdftoppm` | apt: `sudo apt install poppler-utils` / brew: `brew install poppler` |

システムパッケージは `sudo` が必要なため自動インストールが失敗する場合がある。

### エラーリカバリー

依存不在時の対応: (1) 自動インストールを試みる → (2) 失敗時はコマンドを提示 → (3) フォールバック可能なら代替手段で続行

| 不在の依存 | フォールバック |
|-----------|--------------|
| pandoc | unpack で直接 XML を読めばテキスト抽出可能 |
| libreoffice | 新規作成（docx-js）と XML 編集は可能。.doc 変換・変更履歴承認は不可 |
| poppler-utils | LibreOffice で直接画像出力可能 |
| docx-js | 新規作成不可。既存編集（unpack/pack）とテキスト抽出は可能 |
| defusedxml/lxml | スクリプト実行不可 |

---

## 読取

### テキスト抽出

```bash
# Markdown に変換
pandoc document.docx -o output.md

# 変更履歴を含めて抽出
pandoc --track-changes=all document.docx -o output.md

# プレーンテキスト
pandoc document.docx -t plain -o output.txt
```

### XML アクセス（生データ）

```bash
python scripts/office/unpack.py document.docx unpacked/
```

展開後のディレクトリ構造:
```
unpacked/
├── [Content_Types].xml
├── _rels/.rels
├── word/
│   ├── document.xml          # 本文
│   ├── styles.xml            # スタイル定義
│   ├── numbering.xml         # リスト定義
│   ├── comments.xml          # コメント（存在する場合）
│   ├── header1.xml           # ヘッダー
│   ├── footer1.xml           # フッター
│   ├── media/                # 埋め込み画像
│   └── _rels/document.xml.rels
└── docProps/
    ├── core.xml              # タイトル、著者、日時
    └── app.xml               # アプリケーション情報
```

### メタデータ取得

unpack 後、`docProps/core.xml` を読む:
```xml
<cp:coreProperties>
  <dc:title>文書タイトル</dc:title>
  <dc:creator>著者名</dc:creator>
  <dcterms:created>2026-01-15T10:00:00Z</dcterms:created>
  <dcterms:modified>2026-02-10T14:30:00Z</dcterms:modified>
</cp:coreProperties>
```

### 画像変換

```bash
# .docx → PDF → JPEG
python scripts/office/soffice.py --headless --convert-to pdf document.docx
pdftoppm -jpeg -r 150 document.pdf page
```

---

## 新規作成

docx-js（JavaScript）で .docx を生成し、validate で検証する。

### 基本構造

```javascript
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        ImageRun, Header, Footer, AlignmentType, PageOrientation, LevelFormat,
        ExternalHyperlink, TableOfContents, HeadingLevel, BorderStyle, WidthType,
        ShadingType, VerticalAlign, PageNumber, PageBreak } = require('docx');
const fs = require('fs');

const doc = new Document({
  sections: [{
    children: [
      new Paragraph({
        children: [new TextRun("Hello, World!")]
      })
    ]
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("output.docx", buffer);
});
```

### 生成後の検証

```bash
python scripts/office/validate.py output.docx
```

検証エラーが出た場合: unpack → XML 修正 → repack で対処する。

### ページ設定

```javascript
// 重要: docx-js のデフォルトは A4。US Letter を使う場合は明示指定が必要
sections: [{
  properties: {
    page: {
      size: {
        width: 12240,   // 8.5 inches (DXA 単位: 1440 DXA = 1 inch)
        height: 15840   // 11 inches
      },
      margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 }
    }
  },
  children: [/* content */]
}]
```

**用紙サイズ（DXA 単位）:**

| 用紙 | width | height | コンテンツ幅（1" マージン時） |
|------|-------|--------|---------------------------|
| US Letter | 12,240 | 15,840 | 9,360 |
| A4（デフォルト） | 11,906 | 16,838 | 9,026 |
| B5 | 10,318 | 14,570 | 7,438 |

**横向き:** portrait の寸法を渡し、docx-js に swap させる:

```javascript
size: {
  width: 12240,   // 短辺を width に
  height: 15840,  // 長辺を height に
  orientation: PageOrientation.LANDSCAPE  // docx-js が XML で swap する
}
// コンテンツ幅 = 15840 - left margin - right margin
```

### スタイル定義

Arial をデフォルトフォントにする。タイトルは黒で可読性を保つ。

```javascript
const doc = new Document({
  styles: {
    default: {
      document: { run: { font: "Arial", size: 24 } }  // 12pt
    },
    paragraphStyles: [
      // 重要: ビルトインスタイルのオーバーライドには正確な ID を使う
      {
        id: "Heading1", name: "Heading 1",
        basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 240, after: 240 }, outlineLevel: 0 }
      },
      {
        id: "Heading2", name: "Heading 2",
        basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 28, bold: true, font: "Arial" },
        paragraph: { spacing: { before: 180, after: 180 }, outlineLevel: 1 }
      },
    ]
  },
  sections: [{
    children: [
      new Paragraph({
        heading: HeadingLevel.HEADING_1,
        children: [new TextRun("Title")]
      }),
    ]
  }]
});
```

### リスト（Unicode 弾丸文字は使用禁止）

```javascript
// NG: 手動で弾丸文字を入れてはならない
new Paragraph({ children: [new TextRun("• Item")] })        // NG
new Paragraph({ children: [new TextRun("\u2022 Item")] })   // NG

// OK: numbering config で LevelFormat.BULLET を使う
const doc = new Document({
  numbering: {
    config: [
      {
        reference: "bullets",
        levels: [{
          level: 0, format: LevelFormat.BULLET, text: "*",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } }
        }]
      },
      {
        reference: "numbers",
        levels: [{
          level: 0, format: LevelFormat.DECIMAL, text: "%1.",
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } }
        }]
      },
    ]
  },
  sections: [{
    children: [
      new Paragraph({
        numbering: { reference: "bullets", level: 0 },
        children: [new TextRun("Bullet item")]
      }),
      new Paragraph({
        numbering: { reference: "numbers", level: 0 },
        children: [new TextRun("Numbered item")]
      }),
    ]
  }]
});
```

同じ reference → 連番が継続。別の reference → 番号がリスタート。

### テーブル

**重要: テーブルには dual width が必要** — `columnWidths` と各セルの `width` の両方を設定する。

```javascript
const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };

new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [4680, 4680],
  rows: [
    new TableRow({
      children: [
        new TableCell({
          borders,
          width: { size: 4680, type: WidthType.DXA },
          shading: { fill: "D5E8F0", type: ShadingType.CLEAR },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: [new TextRun("Cell")] })]
        }),
        new TableCell({
          borders,
          width: { size: 4680, type: WidthType.DXA },
          margins: { top: 80, bottom: 80, left: 120, right: 120 },
          children: [new Paragraph({ children: [new TextRun("Cell")] })]
        }),
      ]
    })
  ]
})
```

幅のルール:
- 常に `WidthType.DXA` を使う（`WidthType.PERCENTAGE` は Google Docs で崩れる）
- テーブル width = columnWidths の合計
- 各セル width = 対応する columnWidth と一致
- フル幅テーブル: コンテンツ幅（ページ幅 − 左右マージン）を使う

### 画像挿入

```javascript
new Paragraph({
  children: [new ImageRun({
    type: "png",  // 必須: png, jpg, jpeg, gif, bmp, svg
    data: fs.readFileSync("image.png"),
    transformation: { width: 200, height: 150 },
    altText: { title: "Title", description: "Desc", name: "Name" }
  })]
})
```

### ページブレイク

```javascript
new Paragraph({ children: [new PageBreak()] })
// または pageBreakBefore
new Paragraph({ pageBreakBefore: true, children: [new TextRun("New page")] })
```

### 目次

```javascript
new TableOfContents("Table of Contents", {
  hyperlink: true,
  headingStyleRange: "1-3"
})
```

目次が動作するには HeadingLevel と outlineLevel の設定が必要。

### ヘッダー・フッター

```javascript
sections: [{
  properties: {
    page: { margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 } }
  },
  headers: {
    default: new Header({
      children: [new Paragraph({ children: [new TextRun("Header Text")] })]
    })
  },
  footers: {
    default: new Footer({
      children: [new Paragraph({
        children: [
          new TextRun("Page "),
          new TextRun({ children: [PageNumber.CURRENT] })
        ]
      })]
    })
  },
  children: [/* content */]
}]
```

### docx-js 重要ルールまとめ

- 用紙サイズは明示指定する（デフォルト A4）
- 横向き: portrait 寸法を渡して docx-js に swap させる
- `\n` は使わない — 別の Paragraph にする
- Unicode 弾丸文字は使わない — `LevelFormat.BULLET` を使う
- PageBreak は Paragraph 内に入れる
- ImageRun には `type` が必須
- テーブル幅は常に DXA — `WidthType.PERCENTAGE` は使わない
- テーブルには dual width が必要 — `columnWidths` + セル `width`
- テーブル width = columnWidths の合計
- セルには margins を設定する
- `ShadingType.CLEAR` を使う（SOLID ではない）
- TOC には HeadingLevel が必要
- スタイルオーバーライドは正確な ID を使う: "Heading1", "Heading2"
- `outlineLevel` を含める（TOC に必要）

---

## 既存文書編集

**3 ステップを順番に実行する。**

### ステップ 1: 展開

```bash
python scripts/office/unpack.py document.docx unpacked/
```

unpack は以下を自動実行する:
- ZIP 展開
- 全 XML の整形（pretty-print）
- 同一著者の隣接変更履歴の統合
- 同一書式の隣接 Run の結合
- スマートクォートの XML エンティティ変換

### ステップ 2: XML 編集

`unpacked/word/` 配下のファイルを Edit ツールで直接編集する。
Python スクリプトは書かない — Edit ツールの文字列置換を使う。

変更履歴の author にはユーザーが指定しない限り "Claude" を使用する。

**スマートクォート（新規テキストに必須）:**

| エンティティ | 文字 |
|-------------|------|
| `&#x2018;` | 左シングルクォート ' |
| `&#x2019;` | 右シングルクォート / アポストロフィ ' |
| `&#x201C;` | 左ダブルクォート " |
| `&#x201D;` | 右ダブルクォート " |

XML 編集の詳細は references/xml-reference.md を参照すること。

### ステップ 3: 検証と再パッキング

```bash
# 検証（auto-repair 付き）
python scripts/office/validate.py unpacked/ --auto-repair

# 再パッキング
python scripts/office/pack.py unpacked/ output.docx --original document.docx
```

pack の自動修復:
- durableId >= 0x7FFFFFFF → 再生成
- xml:space="preserve" 欠落 → 追加

pack で修復できないもの:
- 不正な XML 構造
- 無効な要素のネスト
- リレーションシップの欠落
- スキーマ違反

### .doc → .docx 変換

```bash
python scripts/office/soffice.py --headless --convert-to docx document.doc
```

---

## 変更履歴・コメント

### 変更履歴の承認（全件）

```bash
python scripts/accept_changes.py input.docx output.docx
```

LibreOffice が必要。LibreOffice Basic マクロで全変更を承認する。

### コメント追加

```bash
# コメント追加（ID=0）
python scripts/comment.py unpacked/ 0 "Comment text with &amp; and &#x2019;"

# 返信（親コメント ID=0 への返信、ID=1）
python scripts/comment.py unpacked/ 1 "Reply text" --parent 0

# 著者指定
python scripts/comment.py unpacked/ 0 "Text" --author "Custom Author"
```

コメント追加後、document.xml にマーカーを配置する必要がある（スクリプトの出力に従う）。

変更履歴とコメントの XML 記述の詳細は references/xml-reference.md を参照すること。

---

## 日本語 Word 文書

日本語 Word 文書を扱う場合は references/japanese.md を参照すること。
以下の知識を提供する:

- docx-js での日本語フォント指定（MS 明朝、MS ゴシック、游明朝等）
- eastAsia フォント分離指定
- 日本語文書の行間設定
- ルビ（ふりがな）
