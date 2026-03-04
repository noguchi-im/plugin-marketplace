# PDF フォーム記入ガイド

**重要: 以下の手順を順番に実行すること。先にコードを書かない。**

## 判定: fillable か non-fillable か

まず PDF にフォームフィールドがあるか確認する:

```bash
python scripts/check_fillable_fields.py INPUT_PDF
```

結果に応じて分岐する:
- fillable → 「fillable パイプライン」へ
- non-fillable → 「non-fillable パイプライン」へ

---

## fillable パイプライン

### ステップ 1: フォーム情報の抽出

```bash
python scripts/extract_form_field_info.py INPUT_PDF field_info.json
```

出力 JSON の構造:

```json
[
  {
    "field_id": "form.name",
    "type": "text",
    "page": 1,
    "rect": [100, 200, 300, 220]
  },
  {
    "field_id": "form.agree",
    "type": "checkbox",
    "page": 1,
    "rect": [100, 250, 115, 265],
    "checked_value": "/Yes",
    "unchecked_value": "/Off"
  },
  {
    "field_id": "form.category",
    "type": "choice",
    "page": 1,
    "rect": [100, 300, 300, 320],
    "choice_options": ["Option A", "Option B", "Option C"]
  }
]
```

### ステップ 2: 値 JSON の作成

フィールド情報を読み取り、ユーザーの指示に基づいて値 JSON を作成する:

```json
[
  {"field_id": "form.name", "page": 1, "value": "山田太郎"},
  {"field_id": "form.agree", "page": 1, "value": "/Yes"},
  {"field_id": "form.category", "page": 1, "value": "Option A"}
]
```

注意:
- `field_id` は抽出した JSON と完全一致させる
- `page` は抽出した JSON と一致させる
- checkbox の `value` は `checked_value` または `unchecked_value` のいずれかのみ
- choice の `value` は `choice_options` に含まれる値のみ
- text の `value` は任意の文字列

### ステップ 3: フォーム記入

```bash
python scripts/fill_fillable_fields.py INPUT_PDF values.json OUTPUT_PDF
```

検証エラーが出た場合: エラーメッセージに従って値 JSON を修正し、再実行する。

---

## non-fillable パイプライン

fillable フィールドを持たない PDF（スキャン画像、フラットな PDF 等）に対して、FreeText アノテーションで値を配置する。

### ステップ 1: 構造の抽出

```bash
python scripts/extract_form_structure.py INPUT_PDF structure.json
```

出力 JSON にはテキストラベル、水平線、チェックボックス候補の位置が含まれる。

### ステップ 2: ページ画像の生成

```bash
python scripts/convert_pdf_to_images.py INPUT_PDF output_images/
```

各ページが `page_1.png`, `page_2.png`, ... として出力される。

### ステップ 3: 座標の特定

3つの方法がある:

**方法 A: 構造ベース（推奨）**

`extract_form_structure.py` がテキストラベルを検出できた場合、そのラベルの座標を基準にエントリ領域を推定する。
座標は PDF 座標系（y=0 がページ下端）。

**方法 B: 画像目視**

スキャン画像の場合やラベル検出が不十分な場合、ページ画像からエントリ領域を目視で推定する。
座標は画像ピクセル座標系。

**方法 C: ハイブリッド**

構造抽出で検出できたラベルは方法 A、検出できなかった部分は方法 B で座標を特定する。
座標系の変換が必要:

```
pdf_x = image_x * (pdf_width / image_width)
pdf_y = pdf_height - (image_y * (pdf_height / image_height))
```

### ステップ 4: fields JSON の作成

```json
{
  "pages": [
    {"page_number": 1, "pdf_width": 595, "pdf_height": 842}
  ],
  "form_fields": [
    {
      "label": "氏名",
      "page_number": 1,
      "label_bounding_box": [50, 700, 100, 720],
      "entry_bounding_box": [110, 700, 300, 720],
      "entry_text": true,
      "text": "山田太郎",
      "font_size": 12
    },
    {
      "label": "住所",
      "page_number": 1,
      "label_bounding_box": [50, 670, 100, 690],
      "entry_bounding_box": [110, 670, 500, 690],
      "entry_text": true,
      "text": "東京都渋谷区...",
      "font_size": 10
    }
  ]
}
```

バウンディングボックスの座標: `[x0, y0, x1, y1]` (PDF 座標系: 左下が原点)

### ステップ 5: 座標の検証

```bash
python scripts/check_bounding_boxes.py fields.json
```

エラーが出た場合: 重複する矩形や小さすぎるエントリ領域を修正して再実行。

### ステップ 6: 検証画像の生成

```bash
python scripts/create_validation_image.py 1 fields.json output_images/page_1.png validation.png
```

生成された画像を確認する:
- 赤い矩形 = エントリ領域
- 青い矩形 = ラベル領域

位置がずれていれば fields.json の座標を修正して再生成する。

### ステップ 7: アノテーション記入

```bash
python scripts/fill_pdf_form_with_annotations.py INPUT_PDF fields.json OUTPUT_PDF
```

---

## 座標系まとめ

| 座標系 | 原点 | Y 軸 | 使用箇所 |
|--------|------|------|---------|
| PDF 座標 | 左下 | 上向き | fillable フィールド、構造抽出結果 |
| 画像座標 | 左上 | 下向き | ページ画像のピクセル位置 |

PDF 座標 → 画像座標:
```
img_x = pdf_x * (img_width / pdf_width)
img_y = (pdf_height - pdf_y) * (img_height / pdf_height)
```

画像座標 → PDF 座標:
```
pdf_x = img_x * (pdf_width / img_width)
pdf_y = pdf_height - (img_y * (pdf_height / img_height))
```
