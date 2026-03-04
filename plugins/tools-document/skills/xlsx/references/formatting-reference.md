# Excel フォーマットリファレンス

## 目次

- [数値フォーマット文字列](#数値フォーマット文字列) — 通貨・パーセント・日付・カスタム形式
- [日本語数値フォーマット](#日本語数値フォーマット) — 日本円・和暦・漢字単位
- [財務モデル色コード規約](#財務モデル色コード規約) — 入力/数式/参照の色分け
- [セルスタイルパターン](#セルスタイルパターン) — ヘッダー・合計行・交互色
- [条件付き書式パターン](#条件付き書式パターン) — 閾値・データバー・アイコンセット

## 数値フォーマット文字列

### 基本構文

`正の数;負の数;ゼロ;テキスト` の最大4セクション。

### 通貨

| フォーマット | 表示例 | 用途 |
|-------------|--------|------|
| `$#,##0` | $1,234 | US ドル（整数） |
| `$#,##0.00` | $1,234.56 | US ドル（小数） |
| `$#,##0;($#,##0);"-"` | $1,234 / ($1,234) / - | 財務（負数括弧、ゼロハイフン） |
| `¥#,##0` | ¥1,234 | 日本円 |
| `#,##0"円"` | 1,234円 | 日本円（漢字） |
| `#,##0"万円"` | 1,234万円 | 万円単位 |
| `#,##0"億円"` | 12億円 | 億円単位 |

### パーセント・倍率

| フォーマット | 表示例 | 用途 |
|-------------|--------|------|
| `0%` | 12% | 整数パーセント |
| `0.0%` | 12.3% | 小数1桁パーセント |
| `0.00%` | 12.34% | 小数2桁パーセント |
| `0.0"x"` | 1.5x | 倍率 |

### 数値

| フォーマット | 表示例 | 用途 |
|-------------|--------|------|
| `#,##0` | 1,234 | カンマ区切り |
| `#,##0.0` | 1,234.5 | 小数1桁 |
| `0` | 1234 | カンマなし |
| `#,##0;(#,##0);"-"` | 1,234 / (1,234) / - | 財務数値 |

### 日付・時刻

| フォーマット | 表示例 | 用途 |
|-------------|--------|------|
| `YYYY/MM/DD` | 2026/02/10 | 日本標準 |
| `YYYY-MM-DD` | 2026-02-10 | ISO 8601 |
| `MM/DD/YYYY` | 02/10/2026 | US 形式 |
| `YYYY年MM月DD日` | 2026年02月10日 | 日本語 |
| `YYYY/MM/DD HH:MM` | 2026/02/10 14:30 | 日時 |
| `HH:MM:SS` | 14:30:00 | 時刻 |

## 日本語数値フォーマット

### 和暦

| フォーマット | 表示例 |
|-------------|--------|
| `[$-411]ggge"年"m"月"d"日"` | 令和8年2月10日 |
| `[$-411]gggee"年"mm"月"dd"日"` | 令和08年02月10日 |

### 曜日

| フォーマット | 表示例 |
|-------------|--------|
| `YYYY/MM/DD(aaa)` | 2026/02/10(火) |
| `aaa` | 火 |
| `aaaa` | 火曜日 |

### 年度表示の注意

年度を数値で入力すると `2,026` のようにカンマ区切りされる。年度は文字列として入力する:

```python
ws["A1"] = "2026"   # 文字列（推奨）
# または
ws["A1"] = 2026
ws["A1"].number_format = "0"  # カンマなし数値
```

## 財務モデル色コード規約

### テキスト色

| 色 | RGB | 意味 | 使用場面 |
|----|-----|------|---------|
| 青 | (0, 0, 255) | ハードコード入力値 | 仮定値、シナリオ変数、手入力データ |
| 黒 | (0, 0, 0) | 数式・計算値 | SUM, IF, VLOOKUP 等の結果 |
| 緑 | (0, 128, 0) | シート間参照 | 同一ワークブック内の他シートからのリンク |
| 赤 | (255, 0, 0) | 外部参照 | 他ファイルからのリンク |

```python
from openpyxl.styles import Font

FONT_INPUT = Font(name="Yu Gothic", color="0000FF")      # 青: 入力値
FONT_FORMULA = Font(name="Yu Gothic", color="000000")     # 黒: 数式
FONT_SHEET_REF = Font(name="Yu Gothic", color="008000")   # 緑: シート参照
FONT_EXTERNAL = Font(name="Yu Gothic", color="FF0000")    # 赤: 外部参照
```

### 背景色

| 色 | RGB | 意味 |
|----|-----|------|
| 黄色 | (255, 255, 0) | 要注意の仮定値 |
| 薄灰色 | (242, 242, 242) | 計算領域 |
| 白 | (255, 255, 255) | 通常 |

```python
from openpyxl.styles import PatternFill

FILL_ATTENTION = PatternFill(start_color="FFFF00", end_color="FFFF00", fill_type="solid")
FILL_CALC = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")
```

### 財務数値形式ルール

| 項目 | ルール |
|------|--------|
| 通貨 | 単位はヘッダーに記載（例: "売上高（百万円）"）。セルには数値のみ |
| 負数 | 括弧表示 `(123)` を使用。マイナス記号 `-123` は使わない |
| ゼロ | ハイフン `-` で表示 |
| パーセント | `0.0%` 形式 |
| 倍率 | `0.0x` 形式 |
| 年度 | 文字列。数値にしない（カンマ区切りを防ぐ） |
| フォーマット文字列 | `#,##0;(#,##0);"-"` （正;負;ゼロ） |

## セルスタイルパターン

### ヘッダー行

```python
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

header_font = Font(name="Yu Gothic", size=11, bold=True, color="FFFFFF")
header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
thin = Side(style="thin", color="000000")
header_border = Border(top=thin, left=thin, right=thin, bottom=thin)

for cell in ws[1]:
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = header_align
    cell.border = header_border
```

### 合計行

```python
total_font = Font(name="Yu Gothic", size=11, bold=True)
total_border = Border(top=Side(style="double", color="000000"),
                      bottom=Side(style="double", color="000000"))
```

### 交互色（ストライプ）

```python
light_fill = PatternFill(start_color="F2F7FB", end_color="F2F7FB", fill_type="solid")
for row_idx in range(2, ws.max_row + 1):
    if row_idx % 2 == 0:
        for cell in ws[row_idx]:
            cell.fill = light_fill
```

## 条件付き書式パターン

### 閾値ベース

```python
from openpyxl.formatting.rule import CellIsRule

# 負の値を赤色
red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
red_font = Font(color="9C0006")
ws.conditional_formatting.add(
    "B2:B100",
    CellIsRule(operator="lessThan", formula=["0"], fill=red_fill, font=red_font),
)

# 目標超過を緑色
green_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
green_font = Font(color="006100")
ws.conditional_formatting.add(
    "C2:C100",
    CellIsRule(operator="greaterThan", formula=["100"], fill=green_fill, font=green_font),
)
```

### データバー

```python
from openpyxl.formatting.rule import DataBarRule

ws.conditional_formatting.add(
    "D2:D100",
    DataBarRule(start_type="min", end_type="max", color="4472C4"),
)
```

### カラースケール

```python
from openpyxl.formatting.rule import ColorScaleRule

ws.conditional_formatting.add(
    "E2:E100",
    ColorScaleRule(
        start_type="min", start_color="F8696B",
        mid_type="percentile", mid_value=50, mid_color="FFEB84",
        end_type="max", end_color="63BE7B",
    ),
)
```
