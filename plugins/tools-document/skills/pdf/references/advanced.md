# PDF 高度な操作リファレンス

## pypdfium2

PDF→画像変換に最適。Chromium の PDFium のバインディング。バイナリ同梱のため poppler-utils なしで動作する。

### ページを画像に変換

```python
import pypdfium2 as pdfium

pdf = pdfium.PdfDocument("document.pdf")

# 単一ページ
page = pdf[0]
bitmap = page.render(scale=2.0)  # scale=2.0 で 144 DPI 相当
img = bitmap.to_pil()
img.save("page_1.png", "PNG")

# 全ページ
for i, page in enumerate(pdf):
    bitmap = page.render(scale=1.5)
    img = bitmap.to_pil()
    img.save(f"page_{i+1}.png", "PNG")
```

### テキスト抽出

```python
import pypdfium2 as pdfium

pdf = pdfium.PdfDocument("document.pdf")
for i, page in enumerate(pdf):
    text = page.get_text()
    print(f"Page {i+1}: {len(text)} chars")
```

## pdf-lib (JavaScript)

Node.js 環境での PDF 生成・編集。MIT ライセンス。

### 既存 PDF の編集

```javascript
import { PDFDocument } from "pdf-lib";
import fs from "fs";

async function addPage() {
  const existingPdfBytes = fs.readFileSync("input.pdf");
  const pdfDoc = await PDFDocument.load(existingPdfBytes);

  const newPage = pdfDoc.addPage([600, 400]);
  newPage.drawText("Added by pdf-lib", { x: 100, y: 300, size: 16 });

  const pdfBytes = await pdfDoc.save();
  fs.writeFileSync("modified.pdf", pdfBytes);
}
```

### 新規作成

```javascript
import { PDFDocument, rgb, StandardFonts } from "pdf-lib";
import fs from "fs";

async function createPDF() {
  const pdfDoc = await PDFDocument.create();
  const font = await pdfDoc.embedFont(StandardFonts.Helvetica);
  const boldFont = await pdfDoc.embedFont(StandardFonts.HelveticaBold);

  const page = pdfDoc.addPage([595, 842]); // A4
  const { width, height } = page.getSize();

  page.drawText("Invoice #12345", {
    x: 50,
    y: height - 50,
    size: 18,
    font: boldFont,
    color: rgb(0.2, 0.2, 0.8),
  });

  page.drawRectangle({
    x: 40,
    y: height - 100,
    width: width - 80,
    height: 30,
    color: rgb(0.9, 0.9, 0.9),
  });

  const pdfBytes = await pdfDoc.save();
  fs.writeFileSync("created.pdf", pdfBytes);
}
```

### 結合

```javascript
import { PDFDocument } from "pdf-lib";
import fs from "fs";

async function mergePDFs() {
  const mergedPdf = await PDFDocument.create();

  const pdf1 = await PDFDocument.load(fs.readFileSync("doc1.pdf"));
  const pdf2 = await PDFDocument.load(fs.readFileSync("doc2.pdf"));

  const pages1 = await mergedPdf.copyPages(pdf1, pdf1.getPageIndices());
  pages1.forEach((page) => mergedPdf.addPage(page));

  // 特定ページのみ
  const pages2 = await mergedPdf.copyPages(pdf2, [0, 2, 4]);
  pages2.forEach((page) => mergedPdf.addPage(page));

  const pdfBytes = await mergedPdf.save();
  fs.writeFileSync("merged.pdf", pdfBytes);
}
```

## CLI 高度な操作

### poppler-utils

```bash
# バウンディングボックス付きテキスト抽出（XML）
pdftotext -bbox-layout document.pdf output.xml

# 高解像度画像変換
pdftoppm -png -r 300 document.pdf output_prefix
pdftoppm -png -r 600 -f 1 -l 3 document.pdf high_res  # ページ指定

# JPEG 変換（品質指定）
pdftoppm -jpeg -jpegopt quality=85 -r 200 document.pdf output

# 画像抽出（メタデータ付き）
pdfimages -j -p document.pdf images/  # JPEG で抽出、ページ番号付き
pdfimages -list document.pdf  # 画像情報一覧
```

### qpdf

```bash
# ページグループ分割
qpdf --split-pages=3 input.pdf output_%02d.pdf

# 複数 PDF から特定ページを結合
qpdf --empty --pages doc1.pdf 1-3 doc2.pdf 5-7 doc3.pdf 2,4 -- combined.pdf

# Web 最適化（線形化）
qpdf --linearize input.pdf optimized.pdf

# PDF 構造チェック
qpdf --check input.pdf

# 修復
qpdf --replace-input corrupted.pdf

# 暗号化（権限指定）
qpdf --encrypt user_pass owner_pass 256 --print=none --modify=none -- input.pdf encrypted.pdf

# 暗号化状態確認
qpdf --show-encryption encrypted.pdf
```

## 座標付きテキスト抽出

```python
import pdfplumber

with pdfplumber.open("document.pdf") as pdf:
    page = pdf.pages[0]

    # 文字ごとの座標
    for char in page.chars[:10]:
        print(f"'{char['text']}' at x:{char['x0']:.1f} y:{char['top']:.1f}")

    # 領域指定でテキスト抽出 (left, top, right, bottom)
    cropped = page.within_bbox((100, 100, 400, 200))
    text = cropped.extract_text()
```

## バッチ処理

```python
import glob
import logging
from pypdf import PdfReader, PdfWriter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def batch_merge(input_dir: str, output_path: str) -> None:
    writer = PdfWriter()
    for pdf_file in sorted(glob.glob(f"{input_dir}/*.pdf")):
        try:
            reader = PdfReader(pdf_file)
            for page in reader.pages:
                writer.add_page(page)
            logger.info(f"Processed: {pdf_file}")
        except Exception as e:
            logger.error(f"Failed: {pdf_file}: {e}")
            continue
    writer.write(output_path)
    writer.close()

def batch_extract_text(input_dir: str, output_dir: str) -> None:
    for pdf_file in sorted(glob.glob(f"{input_dir}/*.pdf")):
        try:
            reader = PdfReader(pdf_file)
            text = "\n".join(page.extract_text() for page in reader.pages)
            output_file = pdf_file.replace(".pdf", ".txt")
            with open(f"{output_dir}/{output_file.split('/')[-1]}", "w") as f:
                f.write(text)
            logger.info(f"Extracted: {pdf_file}")
        except Exception as e:
            logger.error(f"Failed: {pdf_file}: {e}")
            continue
```

## パフォーマンス最適化

| 用途 | 推奨ツール | 理由 |
|------|-----------|------|
| 大量テキスト抽出 | pdftotext | 最も高速。C 実装 |
| テーブル抽出 | pdfplumber | テーブル認識精度が最高 |
| PDF→画像 | pypdfium2 | poppler 不要。高速 |
| 大きいファイルの分割 | qpdf --split-pages | ストリーミング処理 |

### 大規模 PDF のメモリ管理

```python
from pypdf import PdfReader, PdfWriter

def process_in_chunks(pdf_path: str, chunk_size: int = 10) -> None:
    reader = PdfReader(pdf_path)
    total = len(reader.pages)
    for start in range(0, total, chunk_size):
        end = min(start + chunk_size, total)
        writer = PdfWriter()
        for i in range(start, end):
            writer.add_page(reader.pages[i])
        writer.write(f"chunk_{start // chunk_size}.pdf")
        writer.close()
```

## トラブルシューティング

### 暗号化 PDF

```python
from pypdf import PdfReader

reader = PdfReader("encrypted.pdf")
if reader.is_encrypted:
    try:
        reader.decrypt("password")
    except Exception as e:
        print(f"Decryption failed: {e}")
```

### 破損 PDF

```bash
qpdf --check corrupted.pdf
qpdf --replace-input corrupted.pdf  # 修復を試みる
```

### テキスト抽出の失敗

テキストが抽出できない場合の確認手順:

1. 暗号化されていないか確認
2. スキャン画像の PDF か確認（テキストレイヤーがない）→ OCR を使う
3. CID フォントのエンコーディング問題 → references/japanese.md を参照
4. pdfplumber で座標付き抽出を試す
5. pdftotext -layout で試す
