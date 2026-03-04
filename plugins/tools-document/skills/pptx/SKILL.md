---
name: pptx
description: PowerPoint プレゼンテーション（.pptx）の読取・新規作成・テンプレート編集に関する知識とスライド操作・品質検証パイプラインを提供する。プレゼン作成、スライド追加・編集、デザイン調整、QA が必要な時に使用する。
disable-model-invocation: false
allowed-tools: Read, Glob, Bash, Write, Edit
---

あなたは pptx スキルとして動作している。
PowerPoint プレゼンテーションの読取・新規作成・テンプレート編集に関する知識とスライド操作パイプラインを提供する。

## クイックリファレンス

| タスク | アプローチ |
|--------|----------|
| テキスト抽出 | `python -m markitdown presentation.pptx` |
| サムネイル概要 | `python scripts/thumbnail.py presentation.pptx` |
| 新規作成 | pptxgenjs で JavaScript 生成（references/pptxgenjs-reference.md 参照） |
| テンプレート編集 | unpack → 構造操作 → XML 編集 → clean → pack（references/editing-reference.md 参照） |
| 日本語プレゼン | references/japanese.md 参照 |

## 環境セットアップ

**依存関係は使用前に自動チェックし、未インストールなら自動インストールする。**
自動インストール失敗時はインストールコマンドをユーザーに提示する。

### 依存関係チェック・自動インストール

| 依存 | 必要な機能 | チェック | 自動インストール |
|------|-----------|---------|-----------------|
| pptxgenjs (npm) | 新規作成 | `npm list -g pptxgenjs >/dev/null 2>&1` | `npm install -g pptxgenjs` |
| markitdown (pip) | テキスト抽出 | `python3 -c "import markitdown"` | `pip install "markitdown[pptx]"` |
| defusedxml, lxml | スクリプト全般 | `python3 -c "import defusedxml; import lxml"` | `pip install defusedxml lxml` |
| Pillow | サムネイル生成 | `python3 -c "import PIL"` | `pip install Pillow` |
| libreoffice | PDF 変換・QA | `which soffice` | apt: `sudo apt install libreoffice` / brew: `brew install --cask libreoffice` |
| poppler-utils | PDF → 画像 | `which pdftoppm` | apt: `sudo apt install poppler-utils` / brew: `brew install poppler` |

システムパッケージは `sudo` が必要なため自動インストールが失敗する場合がある。

### エラーリカバリー

依存不在時の対応: (1) 自動インストールを試みる → (2) 失敗時はコマンドを提示 → (3) フォールバック可能なら代替手段で続行

| 不在の依存 | フォールバック |
|-----------|--------------|
| pptxgenjs | 新規作成不可。テンプレート編集（unpack/pack）は可能 |
| markitdown | unpack で直接 XML を読めばテキスト抽出可能 |
| Pillow | サムネイル生成不可。soffice + pdftoppm で個別画像は可能 |
| libreoffice | QA の画像変換不可。markitdown によるテキスト QA のみ |
| poppler-utils | LibreOffice で直接画像出力可能 |
| defusedxml/lxml | スクリプト実行不可 |

---

## 読取・分析

### テキスト抽出

```bash
python -m markitdown presentation.pptx
```

### サムネイルグリッド生成

```bash
python scripts/thumbnail.py presentation.pptx
# → thumbnails.jpg（スライド番号ラベル付きグリッド）

# カラム数指定
python scripts/thumbnail.py presentation.pptx --cols 4
```

テンプレート分析（レイアウト選定）に使用する。QA 用の高解像度画像は「画像変換」セクションを使う。

### XML アクセス（生データ）

```bash
python scripts/office/unpack.py presentation.pptx unpacked/
```

展開後のディレクトリ構造:
```
unpacked/
├── [Content_Types].xml
├── _rels/.rels
├── ppt/
│   ├── presentation.xml      # スライド順序（sldIdLst）
│   ├── slides/
│   │   ├── slide1.xml        # スライド本文
│   │   └── slide2.xml
│   ├── slideLayouts/         # レイアウト定義
│   ├── slideMasters/         # マスタースライド
│   ├── theme/                # テーマ（配色・フォント）
│   ├── media/                # 埋め込み画像
│   └── _rels/
└── docProps/
    ├── core.xml              # タイトル、著者
    └── app.xml               # スライド数等
```

### 画像変換

```bash
# .pptx → PDF → JPEG
python scripts/office/soffice.py --headless --convert-to pdf presentation.pptx
pdftoppm -jpeg -r 150 presentation.pdf slide
# → slide-01.jpg, slide-02.jpg, ...

# 特定スライドのみ再レンダリング
pdftoppm -jpeg -r 150 -f 3 -l 3 presentation.pdf slide-fixed
```

---

## 新規作成（pptxgenjs）

テンプレートなしで .pptx をゼロから作る場合に使用する。

**詳細な API リファレンスは references/pptxgenjs-reference.md を参照すること。**

### 基本構造

```javascript
const pptxgen = require("pptxgenjs");
const pres = new pptxgen();

pres.layout = "LAYOUT_16x9";  // 10" x 5.625"
pres.author = "Author Name";
pres.title = "Presentation Title";

const slide = pres.addSlide();
slide.addText("Hello World", {
  x: 0.5, y: 0.5, w: 9, h: 1,
  fontSize: 36, fontFace: "Arial", color: "363636"
});

pres.writeFile({ fileName: "output.pptx" });
```

実行:
```bash
NODE_PATH=$(npm root -g) node generate.js
```

### 重要ルール

- 色指定に `#` を付けてはならない: `"FF0000"` が正しい
- 8 桁 hex（透明度付き）は使ってはならない: `opacity` プロパティを使う
- Unicode 弾丸文字は使ってはならない: `bullet: true` を使う
- オプションオブジェクトを再利用してはならない: 毎回新規に作る（内部で変換される）
- `breakLine: true` で改行する（配列内の各テキスト項目に必要）
- `pptxgen()` インスタンスを再利用してはならない

---

## テンプレート編集

既存 .pptx をテンプレートとして編集する場合に使用する。

**詳細なワークフローと XML 構造は references/editing-reference.md を参照すること。**

### 編集パイプライン

```bash
# 1. サムネイルで構造把握
python scripts/thumbnail.py template.pptx

# 2. 展開
python scripts/office/unpack.py template.pptx unpacked/

# 3. スライド操作（追加・複製）
python scripts/add_slide.py unpacked/ slide2.xml

# 4. Edit ツールで XML 編集（slide{N}.xml を直接編集）

# 5. クリーンアップ
python scripts/clean.py unpacked/

# 6. 再パッキング
python scripts/office/pack.py unpacked/ output.pptx --original template.pptx
```

### スライド順序の管理

スライド順序は `ppt/presentation.xml` の `<p:sldIdLst>` で管理される:

```xml
<p:sldIdLst>
  <p:sldId id="256" r:id="rId2"/>  <!-- slide1 -->
  <p:sldId id="257" r:id="rId3"/>  <!-- slide2 -->
  <p:sldId id="258" r:id="rId4"/>  <!-- slide3 -->
</p:sldIdLst>
```

- **並び替え**: `<p:sldId>` 要素の順序を変更する
- **削除**: `<p:sldId>` 要素を削除し、`clean.py` で孤立ファイルを除去する
- **追加**: `add_slide.py` を使う（手動コピーは禁止）

### office/ 共通ツール

pack.py, unpack.py, validate.py, soffice.py は docx スキルの `scripts/office/` に配置されている。pptx から利用する場合はそちらを参照する。

---

## デザインガイドライン

### 配色パレット

トピックに合った配色を選ぶ。デフォルトの青を避ける。迷った場合は Charcoal Minimal を推奨する。

| テーマ | Primary | Secondary | Accent |
|--------|---------|-----------|--------|
| Midnight Executive | `1E2761` | `CADCFC` | `FFFFFF` |
| Forest & Moss | `2C5F2D` | `97BC62` | `F5F5F5` |
| Coral Energy | `F96167` | `F9E795` | `2F3C7E` |
| Warm Terracotta | `B85042` | `E7E8D1` | `A7BEAE` |
| Ocean Gradient | `065A82` | `1C7293` | `21295C` |
| Charcoal Minimal | `36454F` | `F2F2F2` | `212121` |
| Teal Trust | `028090` | `00A896` | `02C39A` |
| Berry & Cream | `6D2E46` | `A26769` | `ECE2D0` |
| Sage Calm | `84B59F` | `69A297` | `50808E` |
| Cherry Bold | `990011` | `FCF6F5` | `2F3C7E` |

### フォントペアリング

| 見出しフォント | 本文フォント | 特徴 |
|--------------|------------|------|
| Georgia | Calibri | クラシック |
| Arial Black | Arial | インパクト |
| Calibri | Calibri Light | モダン |
| Trebuchet MS | Calibri | カジュアル |
| Palatino | Garamond | エレガント |

迷った場合は Calibri / Calibri Light（モダン）を推奨する。

日本語プレゼンのフォント指定は references/japanese.md を参照すること。

### サイズ階層

| 要素 | サイズ |
|------|-------|
| スライドタイトル | 36-44pt bold |
| セクション見出し | 20-24pt bold |
| 本文 | 14-16pt |
| キャプション | 10-12pt muted |

### レイアウトパターン

- **2 カラム**: テキスト左 + 画像右（または逆）
- **アイコン + テキスト行**: カラー円内アイコン + 太字見出し + 説明
- **2x2 / 2x3 グリッド**: 画像片側 + コンテンツブロック群
- **ハーフブリード画像**: 左右どちらかを画像で埋め、テキストオーバーレイ
- **大数字コールアウト**: 60-72pt の統計値 + 小さなラベル
- **比較カラム**: Before/After、Pros/Cons
- **タイムライン / プロセスフロー**: 番号付きステップ、矢印

### スペーシング

- マージン: スライド端から 0.5" 以上
- コンテンツブロック間: 0.3-0.5"
- 余白を恐れない — 詰め込まない

### よくあるミス

- 同じレイアウトを繰り返す — レイアウトを変化させる
- 本文テキストを中央揃え — 本文は左揃え、タイトルのみ中央
- テキストのみのスライド — 画像・アイコン・チャート・図形を必ず入れる
- タイトルサイズ不足 — 36pt 以上で本文との差を出す
- テキストボックスのパディング未考慮 — 図形と揃える時は `margin: 0`

---

## QA（必須）

**最初のレンダリングはほぼ確実に問題がある。確認作業ではなくバグ探しとして臨む。**

### コンテンツ QA

```bash
python -m markitdown output.pptx
```

内容の欠落、タイポ、順序の誤りを確認する。

テンプレート使用時はプレースホルダーテキストの残存を確認:
```bash
python -m markitdown output.pptx | grep -iE "xxxx|lorem|ipsum|placeholder"
```

### ビジュアル QA

画像に変換してスライドごとに検査する:

```bash
python scripts/office/soffice.py --headless --convert-to pdf output.pptx
pdftoppm -jpeg -r 150 output.pdf slide
```

検査項目:
- 要素の重なり（テキストが図形を貫通、要素が積み重なり）
- テキストのはみ出し・切れ
- 要素間のスペース不足（0.3" 未満）
- 不均一なギャップ
- スライド端からのマージン不足（0.5" 未満）
- 低コントラスト（薄い文字 on 薄い背景）
- プレースホルダーコンテンツの残存

### 修正→再検証ループ

1. 生成 → 画像変換 → 検査
2. 問題をリストアップ（問題ゼロなら再度厳しく検査）
3. 修正する
4. 修正したスライドを再検証（修正が別の問題を生むことがある）
5. 問題が出なくなるまで繰り返す

**最低 1 回の修正→再検証サイクルを完了するまで完了宣言しない。**

---

## 日本語プレゼンテーション

日本語プレゼンテーションを扱う場合は references/japanese.md を参照すること。
以下の知識を提供する:

- pptxgenjs での日本語フォント指定（游ゴシック、メイリオ、ヒラギノ等）
- XML での eastAsia フォント指定
- 日本語テキストの配置とアラインメント
- 行間・文字間隔の調整
- 縦書き設定
