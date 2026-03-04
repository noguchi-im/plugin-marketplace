---
name: xlsx
description: Excel スプレッドシート（.xlsx / .xlsm / .csv / .tsv）の読取・新規作成・既存編集に関する知識と数式再計算パイプラインを提供する。データ分析、レポート作成、数式追加、フォーマット設定、CSV変換が必要な時に使用する。
disable-model-invocation: false
allowed-tools: Read, Glob, Bash, Write, Edit
---

あなたは xlsx スキルとして動作している。
Excel スプレッドシートの読取・新規作成・既存編集に関する知識と数式再計算パイプラインを提供する。

## クイックリファレンス

| タスク | アプローチ |
|--------|----------|
| データ分析 | `pandas` で読み込み → 分析 |
| 新規作成 | `openpyxl` で構築 → 保存 |
| 既存編集 | `openpyxl` で load_workbook → 編集 → 保存 |
| 数式付き作成 | openpyxl で数式記述 → `recalc.py` で再計算 |
| CSV/TSV → Excel | `pandas` で読み込み → openpyxl or to_excel で出力 |

## 環境セットアップ

**依存関係は使用前に自動チェックし、未インストールなら自動インストールする。**
自動インストール失敗時はインストールコマンドをユーザーに提示する。

### 依存関係チェック・自動インストール

| 依存 | 必要な機能 | チェック | 自動インストール |
|------|-----------|---------|-----------------|
| openpyxl | Excel 作成・編集 | `python3 -c "import openpyxl"` | `pip install openpyxl` |
| pandas | データ分析・CSV 読取 | `python3 -c "import pandas"` | `pip install pandas` |
| libreoffice | 数式再計算 | `which soffice` | apt: `sudo apt install libreoffice` / brew: `brew install --cask libreoffice` |

### エラーリカバリー

依存不在時の対応: (1) 自動インストールを試みる → (2) 失敗時はコマンドを提示 → (3) フォールバック可能なら代替手段で続行

| 不在の依存 | フォールバック |
|-----------|--------------|
| pandas | openpyxl で直接セル読取可能（分析機能は制限される） |
| libreoffice | 数式再計算不可。数式は文字列のまま保存される |
| openpyxl | Excel 操作不可（pandas の to_excel は XlsxWriter 経由で簡易出力のみ） |

---

## 読取・分析

### pandas による読み込み

```python
import pandas as pd

# 基本読み込み
df = pd.read_excel("data.xlsx")

# シート指定
df = pd.read_excel("data.xlsx", sheet_name="Sheet2")

# 全シート読み込み（辞書で返る）
all_sheets = pd.read_excel("data.xlsx", sheet_name=None)

# ヘッダー行指定（0始まり）
df = pd.read_excel("data.xlsx", header=2)

# 列の型指定
df = pd.read_excel("data.xlsx", dtype={"ID": str, "Amount": float})
```

### CSV/TSV 読み込み

```python
# CSV（日本語ファイルは encoding 指定が重要）
df = pd.read_csv("data.csv", encoding="utf-8")
df = pd.read_csv("data_sjis.csv", encoding="cp932")  # Shift_JIS

# TSV
df = pd.read_csv("data.tsv", sep="\t", encoding="utf-8")

# エンコーディング自動検出が必要な場合
import chardet
with open("data.csv", "rb") as f:
    detected = chardet.detect(f.read())
df = pd.read_csv("data.csv", encoding=detected["encoding"])
```

### openpyxl による読み込み

```python
from openpyxl import load_workbook

# 数式の計算結果を読む
wb = load_workbook("data.xlsx", data_only=True)
ws = wb.active
value = ws["B5"].value

# 数式自体を読む
wb = load_workbook("data.xlsx")
formula = ws["B5"].value  # "=SUM(B2:B4)"
```

---

## 新規作成

### 基本構造

```python
from openpyxl import Workbook

wb = Workbook()
ws = wb.active
ws.title = "データ"

# セル値の書き込み
ws["A1"] = "項目"
ws["B1"] = "金額"
ws["A2"] = "売上"
ws["B2"] = 1000000

# 行単位の追加
ws.append(["経費", 500000])
ws.append(["利益", None])  # 数式は後で設定

# 数式（文字列として記述、Python で計算してはならない）
ws["B4"] = "=B2-B3"

wb.save("output.xlsx")
```

**重要: 数式は必ず文字列として書く。Python で計算した値をハードコードしてはならない。**

### シート操作

```python
# シート追加
ws2 = wb.create_sheet("集計")
ws3 = wb.create_sheet("データ", 0)  # 先頭に挿入

# シート名変更
ws.title = "月次レポート"

# シート削除
del wb["不要シート"]

# シート間参照（数式）
ws2["A1"] = "=データ!B4"
```

### DataFrame からの一括出力

```python
import pandas as pd
from openpyxl import Workbook
from openpyxl.utils.dataframe import dataframe_to_rows

wb = Workbook()
ws = wb.active

df = pd.DataFrame({"名前": ["田中", "佐藤"], "点数": [85, 92]})

for r in dataframe_to_rows(df, index=False, header=True):
    ws.append(r)

wb.save("output.xlsx")
```

### CSV/TSV への出力

```python
# CSV（日本語は UTF-8 BOM 付きが Excel で安全）
df.to_csv("output.csv", index=False, encoding="utf-8-sig")

# Shift_JIS（レガシーシステム向け）
df.to_csv("output_sjis.csv", index=False, encoding="cp932")

# TSV
df.to_csv("output.tsv", index=False, sep="\t", encoding="utf-8-sig")
```

---

## フォーマット

### 基本スタイル

```python
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

# フォント
ws["A1"].font = Font(name="Yu Gothic", size=11, bold=True, color="000000")

# 背景色
ws["A1"].fill = PatternFill(start_color="D5E8F0", end_color="D5E8F0", fill_type="solid")

# 配置
ws["A1"].alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

# 罫線
thin = Side(style="thin", color="000000")
ws["A1"].border = Border(top=thin, left=thin, right=thin, bottom=thin)
```

### 列幅・行高

```python
# 列幅（文字数単位）
ws.column_dimensions["A"].width = 20
ws.column_dimensions["B"].width = 15

# 行高（ポイント単位）
ws.row_dimensions[1].height = 30

# 全列の自動幅調整（概算）
for col in ws.columns:
    max_length = max(len(str(cell.value or "")) for cell in col)
    col_letter = col[0].column_letter
    ws.column_dimensions[col_letter].width = min(max_length + 2, 50)
```

### 日本語フォント

日本語 Excel では以下のフォントを推奨する:

| フォント | 用途 |
|----------|------|
| Yu Gothic (游ゴシック) | 本文・データ（Windows/Mac 共通） |
| Yu Mincho (游明朝) | フォーマルな文書 |
| MS Gothic (ＭＳ ゴシック) | レガシー互換 |
| Meiryo (メイリオ) | 画面表示重視 |

```python
# 日本語フォント設定例
header_font = Font(name="Yu Gothic", size=11, bold=True)
body_font = Font(name="Yu Gothic", size=10)
```

### 数値フォーマット

```python
# 通貨（日本円）
ws["B2"].number_format = '¥#,##0'
ws["B3"].number_format = '#,##0"円"'

# 通貨（US ドル）
ws["C2"].number_format = '$#,##0'

# パーセント
ws["D2"].number_format = '0.0%'

# 日付
ws["E2"].number_format = 'YYYY/MM/DD'
ws["E3"].number_format = 'YYYY年MM月DD日'

# カスタム（負数を括弧、ゼロをハイフン）
ws["F2"].number_format = '#,##0;(#,##0);"-"'
```

詳細な数値フォーマットと財務モデル規約は references/formatting-reference.md を参照すること。

### セル結合

```python
ws.merge_cells("A1:D1")
ws["A1"] = "月次売上レポート"
ws["A1"].alignment = Alignment(horizontal="center")
```

### 条件付き書式

```python
from openpyxl.formatting.rule import CellIsRule

# 値が負の場合に赤色
red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
red_font = Font(color="9C0006")
ws.conditional_formatting.add(
    "B2:B100",
    CellIsRule(operator="lessThan", formula=["0"], fill=red_fill, font=red_font),
)
```

---

## 数式再計算

### 数式の記述ルール

- 数式は文字列として記述する: `ws["B10"] = "=SUM(B2:B9)"`
- **Python で計算した値をハードコードしてはならない**
- クロスシート参照: `"=Sheet1!A1"` （日本語シート名はシングルクォート: `"='売上データ'!A1"`）
- 範囲: `"=SUM(B2:B9)"`, `"=VLOOKUP(A2,Sheet2!A:B,2,FALSE)"`

### recalc.py による再計算（必須）

数式を含む .xlsx を保存した後、必ず recalc.py を実行する。

```bash
python scripts/recalc.py output.xlsx
```

出力（JSON）:
```json
{
  "status": "success",
  "total_formulas": 42,
  "total_errors": 0,
  "error_summary": {}
}
```

エラーがある場合:
```json
{
  "status": "errors_found",
  "total_formulas": 42,
  "total_errors": 2,
  "error_summary": {
    "#REF!": {
      "count": 2,
      "locations": ["Sheet1!B5", "Sheet1!C10"]
    }
  }
}
```

### エラー検出と修正ループ

1. recalc.py を実行する
2. `status` が `errors_found` の場合:
   - `error_summary` からエラー種類とセル位置を確認する
   - openpyxl で該当セルの数式を修正する
   - 再度 recalc.py を実行する
3. `status` が `success` になるまで繰り返す

### Excel エラー種類

| エラー | 原因 | よくある修正 |
|--------|------|-------------|
| #VALUE! | データ型不一致 | セル参照先の型を確認 |
| #DIV/0! | ゼロ除算 | IF で分母ゼロを事前チェック |
| #REF! | 無効なセル参照 | 削除された行/列の参照を修正 |
| #NAME? | 未認識の数式名 | 数式名のスペルを確認 |
| #NULL! | 不正な範囲演算子 | コロンとカンマの使い分けを確認 |
| #NUM! | 無効な数値 | 引数の範囲を確認 |
| #N/A | 値なし | VLOOKUP の検索値を確認 |

---

## 日本語 Excel の注意点

### エンコーディング

| 形式 | 推奨エンコーディング | 理由 |
|------|-------------------|------|
| .xlsx | UTF-8（自動） | openpyxl が自動処理 |
| CSV 出力 | UTF-8 BOM (`utf-8-sig`) | Excel が BOM なし UTF-8 を Shift_JIS と誤認する |
| CSV 入力（レガシー） | `cp932` (Shift_JIS) | 古い日本語システムからの出力 |
| TSV | UTF-8 BOM (`utf-8-sig`) | CSV と同様 |

### 日本語数値フォーマット

```python
# 日本円（漢字単位）
ws["B2"].number_format = '#,##0"万円"'
ws["B3"].number_format = '#,##0"億円"'

# 和暦（Excel 組み込み）
ws["C2"].number_format = '[$-411]ggge"年"m"月"d"日"'

# 曜日
ws["D2"].number_format = 'YYYY/MM/DD(aaa)'  # 月, 火, 水...
```

### シート名の日本語

```python
ws.title = "売上データ"

# 数式でのシート参照（シングルクォート必須）
ws2["A1"] = "='売上データ'!B10"
```
