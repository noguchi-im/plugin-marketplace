---
name: pdf
description: PDF ファイルの読取・作成・操作に関する知識とフォーム記入パイプラインを提供する。PDF のテキスト抽出、テーブル抽出、新規作成、結合・分割・回転・暗号化、フォーム記入、日本語対応が必要な時に使用する。
disable-model-invocation: false
allowed-tools: Read, Glob, Bash, Write
---

あなたは pdf スキルとして動作している。
PDF ファイルの読取・作成・操作に関する知識とフォーム記入パイプラインを提供する。

## 環境セットアップ

### pip パッケージ

```bash
pip install pypdf pdfplumber reportlab pypdfium2 pdf2image pytesseract Pillow
```

### システムパッケージ

| パッケージ | 用途 | インストール |
|-----------|------|-------------|
| poppler-utils | pdftotext, pdfimages, pdftoppm, pdf2image の実行 | apt: `sudo apt install poppler-utils` / brew: `brew install poppler` |
| tesseract-ocr | OCR（スキャン文書の文字認識） | apt: `sudo apt install tesseract-ocr` / brew: `brew install tesseract` |
| qpdf | PDF 修復・最適化・暗号化 | apt: `sudo apt install qpdf` / brew: `brew install qpdf` |

### Node.js パッケージ（pdf-lib を使う場合）

```bash
npm install pdf-lib
```

### フォールバック

- poppler-utils が未インストールでも、pypdfium2 で PDF→画像変換は可能
- pdftotext が未インストールでも、pypdf や pdfplumber でテキスト抽出は可能
- qpdf が未インストールでも、pypdf で基本的な結合・分割・暗号化は可能

---

## 読取

### テキスト抽出

用途に応じて使い分ける:

| ツール | 向いている用途 | 注意点 |
|--------|--------------|--------|
| pypdf | 簡易的な全文取得 | レイアウト情報なし |
| pdfplumber | レイアウト保持、座標が必要な場合 | やや低速 |
| pdftotext | 高速な大量処理 | system パッケージ必要 |

**pypdf:**

```python
from pypdf import PdfReader

reader = PdfReader("document.pdf")
for page in reader.pages:
    text = page.extract_text()
    print(text)
```

**pdfplumber:**

```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        print(text)
```

**pdftotext (CLI):**

```bash
pdftotext document.pdf output.txt
pdftotext -layout document.pdf output.txt  # レイアウト保持
```

### テーブル抽出

```python
import pdfplumber
import pandas as pd

with pdfplumber.open("document.pdf") as pdf:
    page = pdf.pages[0]
    tables = page.extract_tables()
    for table in tables:
        df = pd.DataFrame(table[1:], columns=table[0])
        print(df)
```

複雑なテーブルの場合、カスタム設定を使う:

```python
table_settings = {
    "vertical_strategy": "lines",
    "horizontal_strategy": "lines",
    "snap_tolerance": 3,
    "intersection_tolerance": 15,
}
tables = page.extract_tables(table_settings)
```

### メタデータ取得

```python
from pypdf import PdfReader

reader = PdfReader("document.pdf")
meta = reader.metadata
print(f"Title: {meta.title}")
print(f"Author: {meta.author}")
print(f"Pages: {len(reader.pages)}")
```

### 画像抽出

```bash
# 埋め込み画像を元のフォーマットで抽出
pdfimages -all document.pdf images/img

# 画像情報の一覧表示
pdfimages -list document.pdf
```

### OCR（スキャン文書）

```python
import pytesseract
from pdf2image import convert_from_path

images = convert_from_path("scanned.pdf", dpi=300)
for i, image in enumerate(images):
    text = pytesseract.image_to_string(image, lang="jpn")  # 日本語の場合
    print(f"--- Page {i+1} ---")
    print(text)
```

日本語 OCR には `tesseract-ocr-jpn` パッケージが追加で必要:
```bash
sudo apt install tesseract-ocr-jpn
```

---

## 作成

### reportlab Canvas（基本）

```python
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

c = canvas.Canvas("output.pdf", pagesize=A4)
width, height = A4

c.setFont("Helvetica", 16)
c.drawString(72, height - 72, "Hello, PDF!")

c.setFont("Helvetica", 12)
c.drawString(72, height - 100, "This is a simple PDF document.")

c.showPage()
c.save()
```

### reportlab Platypus（構造化文書）

```python
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

doc = SimpleDocTemplate("report.pdf", pagesize=A4)
styles = getSampleStyleSheet()
elements = []

# 見出し
elements.append(Paragraph("Quarterly Report", styles["Title"]))
elements.append(Spacer(1, 12))

# 段落
elements.append(Paragraph("This is the summary section.", styles["Normal"]))
elements.append(Spacer(1, 12))

# 表
data = [
    ["Item", "Q1", "Q2", "Q3", "Q4"],
    ["Revenue", "100", "120", "135", "150"],
    ["Cost", "80", "85", "90", "95"],
]
table = Table(data)
table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
    ("GRID", (0, 0), (-1, -1), 1, colors.black),
]))
elements.append(table)

doc.build(elements)
```

### 下付き・上付き文字

reportlab で下付き・上付き文字を使う場合、`<sub>` と `<super>` タグを使う。
**Unicode の下付き・上付き文字（₀₁₂₃, ⁰¹²³ 等）は使用禁止。** ビルトインフォントにグリフがなく黒い四角になる。

```python
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet

styles = getSampleStyleSheet()
text = "H<sub>2</sub>O and E=mc<super>2</super>"
p = Paragraph(text, styles["Normal"])
```

---

## 操作

### 結合

```python
from pypdf import PdfWriter

writer = PdfWriter()
for pdf_file in ["doc1.pdf", "doc2.pdf", "doc3.pdf"]:
    writer.append(pdf_file)
writer.write("merged.pdf")
writer.close()
```

CLI: `qpdf --empty --pages doc1.pdf doc2.pdf doc3.pdf -- merged.pdf`

### 分割

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("document.pdf")
for i, page in enumerate(reader.pages):
    writer = PdfWriter()
    writer.add_page(page)
    writer.write(f"page_{i+1}.pdf")
    writer.close()
```

特定ページの抽出:
```bash
qpdf document.pdf --pages document.pdf 1,3-5,8 -- extracted.pdf
```

### ページ回転

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("document.pdf")
writer = PdfWriter()
for page in reader.pages:
    page.rotate(90)  # 90, 180, 270
    writer.add_page(page)
writer.write("rotated.pdf")
writer.close()
```

### ページ切り抜き (crop)

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("document.pdf")
writer = PdfWriter()
page = reader.pages[0]
# mediabox: left, bottom, right, top (in points, 72pt = 1 inch)
page.mediabox.left = 50
page.mediabox.bottom = 50
page.mediabox.right = 550
page.mediabox.top = 750
writer.add_page(page)
writer.write("cropped.pdf")
writer.close()
```

### 透かし追加

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("document.pdf")
watermark = PdfReader("watermark.pdf")
writer = PdfWriter()

for page in reader.pages:
    page.merge_page(watermark.pages[0])
    writer.add_page(page)

writer.write("watermarked.pdf")
writer.close()
```

### パスワード保護

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("document.pdf")
writer = PdfWriter()
for page in reader.pages:
    writer.add_page(page)

writer.encrypt(user_password="user123", owner_password="owner456")
writer.write("encrypted.pdf")
writer.close()
```

CLI: `qpdf --encrypt user_pass owner_pass 256 -- input.pdf encrypted.pdf`

### パスワード解除

```python
from pypdf import PdfReader, PdfWriter

reader = PdfReader("encrypted.pdf")
if reader.is_encrypted:
    reader.decrypt("password")

writer = PdfWriter()
for page in reader.pages:
    writer.add_page(page)
writer.write("decrypted.pdf")
writer.close()
```

CLI: `qpdf --password=secret --decrypt encrypted.pdf decrypted.pdf`

### しおり (bookmarks/outlines) 操作

**読取:**

```python
from pypdf import PdfReader

reader = PdfReader("document.pdf")
if reader.outline:
    for item in reader.outline:
        if isinstance(item, list):
            for sub in item:
                print(f"  Sub: {sub.title}")
        else:
            print(f"Bookmark: {item.title}")
```

**追加:**

```python
from pypdf import PdfWriter

writer = PdfWriter()
writer.append("document.pdf")

writer.add_outline_item("Chapter 1", page_number=0)
writer.add_outline_item("Chapter 2", page_number=5)
parent = writer.add_outline_item("Chapter 3", page_number=10)
writer.add_outline_item("Section 3.1", page_number=11, parent=parent)

writer.write("with_bookmarks.pdf")
writer.close()
```

### ページ番号追加

```python
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io

reader = PdfReader("document.pdf")
writer = PdfWriter()

for i, page in enumerate(reader.pages):
    # ページ番号用の PDF を生成
    packet = io.BytesIO()
    c = canvas.Canvas(packet, pagesize=A4)
    width, height = A4
    c.setFont("Helvetica", 10)
    c.drawCentredString(width / 2, 30, str(i + 1))
    c.save()
    packet.seek(0)

    # オーバーレイ
    overlay = PdfReader(packet)
    page.merge_page(overlay.pages[0])
    writer.add_page(page)

writer.write("numbered.pdf")
writer.close()
```

---

## フォーム記入

フォーム記入は references/forms.md に詳細なワークフローを定義している。

### 手順概要

1. `scripts/check_fillable_fields.py` で PDF にフォームフィールドがあるか判定する
2. **fillable の場合**: `extract_form_field_info.py` → 値 JSON 作成 → `fill_fillable_fields.py`
3. **non-fillable の場合**: `extract_form_structure.py` → `convert_pdf_to_images.py` → 座標特定 → `check_bounding_boxes.py` → `create_validation_image.py` → `fill_pdf_form_with_annotations.py`

フォーム記入を指示された場合は、references/forms.md を読み込んでから実行すること。

---

## 日本語 PDF

日本語 PDF を扱う場合は references/japanese.md を参照すること。
以下の問題に対処するガイドを提供する:

- テキスト抽出時の CID フォント・エンコーディング問題
- 縦書きテキストの処理
- reportlab での日本語フォント登録・使用

---

## Webページ → PDF 変換

Webページの内容を reportlab で PDF 化する場合、コンテンツ取得段階で品質劣化が起きやすい。
以下の手順に従うこと。

### 1. コンテンツ取得

WebFetch はAIモデルがコンテンツを処理して返すため、原文を要約・省略する傾向がある。

- WebFetch の prompt に「原文を省略せず一字一句そのまま返す」旨を明示的に指示する
- 同時に「HTMLの構造情報（段組・カラム指定・特殊レイアウト等）も併せて返す」旨を指示する
- 1回の取得で内容が不足・省略されている場合は、観点を変えて追加取得する
  - 例: 1回目「全テキストを原文のまま」、2回目「HTMLの構造・CSSレイアウト情報」

### 2. レイアウト構造の確定

PDF 生成コードを書く前に、元ページのレイアウト構造を確認する。

- **段組**: column-count の有無。2段組の場合は BaseDocTemplate + Frame を使用する
- **配置方向**: 横書き / 縦書き
- **セクション構成**: ヘッダー・本文・フッターの区分。ヘッダーが1段組で本文が2段組、等の混合レイアウト
- **特殊要素**: 表、画像、回答欄、罫線など

| レイアウト | reportlab の構造 |
|-----------|-----------------|
| 1段組（通常） | SimpleDocTemplate |
| 2段組以上 | BaseDocTemplate + Frame（左右カラム） |
| 混合（ヘッダー1段+本文2段） | BaseDocTemplate + 複数 PageTemplate |

### 3. PDF 生成

既存の「作成」セクションの知識（reportlab Canvas / Platypus）を使用してコンテンツを PDF 化する。
日本語テキストが含まれる場合は references/japanese.md を参照すること。

### 4. 照合検証

生成した PDF を Read ツールで開き、元ページの内容と照合する。

- テキストの省略・脱落がないか確認する
- レイアウト（段組等）が反映されているか確認する
- 問題があれば修正して再生成する

---

## 高度な操作

高度な操作が必要な場合は references/advanced.md を参照すること。
以下の知識を提供する:

- pypdfium2 による高品質な PDF→画像変換
- pdf-lib (JavaScript) による PDF 操作
- poppler-utils / qpdf の高度な CLI オプション
- バッチ処理のパターン
- パフォーマンス最適化
- トラブルシューティング
