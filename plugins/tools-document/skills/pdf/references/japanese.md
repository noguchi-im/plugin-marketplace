# 日本語 PDF リファレンス

## テキスト抽出の注意点

### CID フォント

日本語 PDF は CID フォント（Adobe-Japan1）を使用していることが多い。
pypdf でテキスト抽出すると文字化けや空文字列になる場合がある。

**対策の優先順位:**

1. **pdfplumber を使う** — CID フォントのデコードに比較的強い
2. **pdftotext -layout を使う** — poppler のデコーダが対応している場合がある
3. **OCR にフォールバック** — 上記でも文字化けする場合

```python
import pdfplumber

with pdfplumber.open("japanese.pdf") as pdf:
    for page in pdf.pages:
        text = page.extract_text()
        if text and len(text.strip()) > 0:
            print(text)
        else:
            print("テキスト抽出失敗 — OCR を検討")
```

### 縦書き

縦書きテキストは pdfplumber で座標ベースで抽出できるが、文字の読み順が保証されない場合がある。

```python
import pdfplumber

with pdfplumber.open("tategaki.pdf") as pdf:
    page = pdf.pages[0]
    # 文字ごとの座標を取得して、x座標でグループ化→y座標でソート
    chars = page.chars
    # x0 が近い文字を同一列とみなす
    columns = {}
    for char in chars:
        col_key = round(char["x0"] / 20) * 20  # 20pt 単位でグループ化
        columns.setdefault(col_key, []).append(char)

    # 右から左（x降順）、各列は上から下（top昇順）
    for col_key in sorted(columns.keys(), reverse=True):
        col_chars = sorted(columns[col_key], key=lambda c: c["top"])
        line = "".join(c["text"] for c in col_chars)
        print(line)
```

### エンコーディング問題

一部の PDF は ToUnicode CMap を持たず、文字コードから Unicode への変換ができない。

確認方法:
```python
from pypdf import PdfReader

reader = PdfReader("document.pdf")
page = reader.pages[0]
text = page.extract_text()
# 空文字列、文字化け、制御文字が多い場合はエンコーディング問題
if not text or len(text.strip()) < 10:
    print("エンコーディング問題の可能性あり")
```

## 日本語 PDF 作成

### CIDFont（ビルトイン日本語フォント）

Adobe の CID フォントを使う方法。フォントファイルの埋め込み不要だが、ビューアー側にフォントが必要。

```python
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# 日本語 CID フォント登録
pdfmetrics.registerFont(UnicodeCIDFont("HeiseiMin-W3"))      # 明朝
pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))   # ゴシック

c = canvas.Canvas("japanese.pdf", pagesize=A4)
width, height = A4

c.setFont("HeiseiMin-W3", 14)
c.drawString(72, height - 72, "日本語テスト — 明朝体")

c.setFont("HeiseiKakuGo-W5", 14)
c.drawString(72, height - 100, "日本語テスト — ゴシック体")

c.showPage()
c.save()
```

### TTFont（TrueType フォント埋め込み）

システムにインストールされた TrueType フォントを埋め込む。確実に表示される。

```python
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# TrueType フォント登録（パスはシステムに合わせて変更）
# macOS
# pdfmetrics.registerFont(TTFont("IPAGothic", "/Library/Fonts/ipag.ttf"))
# Linux
pdfmetrics.registerFont(TTFont("IPAGothic", "/usr/share/fonts/truetype/ipafont-gothic/ipag.ttf"))

c = canvas.Canvas("japanese_ttf.pdf", pagesize=A4)
width, height = A4

c.setFont("IPAGothic", 14)
c.drawString(72, height - 72, "TrueType フォント埋め込みテスト")

c.showPage()
c.save()
```

よく使われる日本語フォント:

| フォント | パス (Linux) | 備考 |
|---------|-------------|------|
| IPA ゴシック | `/usr/share/fonts/truetype/ipafont-gothic/ipag.ttf` | `apt install fonts-ipafont-gothic` |
| IPA 明朝 | `/usr/share/fonts/truetype/ipafont-mincho/ipam.ttf` | `apt install fonts-ipafont-mincho` |
| Noto Sans JP | `/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc` | `apt install fonts-noto-cjk` |

### Platypus での日本語

```python
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.pagesizes import A4

pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))

doc = SimpleDocTemplate("japanese_report.pdf", pagesize=A4)

# 日本語用スタイル
styles = getSampleStyleSheet()
ja_style = ParagraphStyle(
    "Japanese",
    parent=styles["Normal"],
    fontName="HeiseiKakuGo-W5",
    fontSize=12,
    leading=18,  # 行間（フォントサイズの 1.5 倍程度）
)
ja_title = ParagraphStyle(
    "JapaneseTitle",
    parent=styles["Title"],
    fontName="HeiseiKakuGo-W5",
    fontSize=18,
    leading=24,
)

elements = [
    Paragraph("レポートタイトル", ja_title),
    Paragraph("これは日本語の段落です。Platypus を使って構造化文書を作成しています。", ja_style),
]

doc.build(elements)
```
