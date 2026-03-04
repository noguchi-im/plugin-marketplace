# 日本語 Word 文書ガイド

## docx-js での日本語フォント指定

### フォント名

| フォント | 用途 | Windows 名 | macOS 名 |
|---------|------|-----------|---------|
| MS 明朝 | 本文（正式文書） | MS Mincho | — |
| MS ゴシック | 見出し・強調 | MS Gothic | — |
| 游明朝 | 本文（モダン） | Yu Mincho | YuMincho |
| 游ゴシック | 見出し（モダン） | Yu Gothic | YuGothic |
| ヒラギノ明朝 | macOS 本文 | — | Hiragino Mincho ProN |
| ヒラギノ角ゴ | macOS 見出し | — | Hiragino Sans |
| Noto Sans JP | クロスプラットフォーム | Noto Sans JP | Noto Sans JP |
| Noto Serif JP | クロスプラットフォーム | Noto Serif JP | Noto Serif JP |

### eastAsia フォント分離指定

docx-js で日本語フォントを指定する場合、`font` に加えて XML レベルで `w:rFonts` の `w:eastAsia` 属性を設定する必要がある場合がある:

```javascript
// docx-js での基本的なフォント指定
const doc = new Document({
  styles: {
    default: {
      document: {
        run: {
          font: "Yu Gothic"   // 全体のデフォルト
        }
      }
    }
  },
  // ...
});
```

XML レベルで分離指定が必要な場合（unpack → edit → pack で対応）:

```xml
<w:rFonts w:ascii="Arial" w:hAnsi="Arial" w:eastAsia="游ゴシック" w:cs="Arial"/>
```

- `w:ascii` / `w:hAnsi`: 半角英数フォント
- `w:eastAsia`: 日本語（CJK）フォント
- `w:cs`: Complex Script フォント（アラビア語等）

### 推奨フォント設定

**ビジネス文書:**
```javascript
run: {
  font: "Yu Gothic",
  size: 21   // 10.5pt（日本語ビジネス文書の標準）
}
```

**学術・正式文書:**
```javascript
run: {
  font: "Yu Mincho",
  size: 24   // 12pt
}
```

---

## 行間設定

### 日本語文書の行間

日本語文書では行間を広めに取るのが一般的:

```javascript
new Paragraph({
  spacing: {
    line: 360,       // 行間（twips: 360 = 18pt ≈ 1.5 行）
    lineRule: "auto"
  },
  children: [new TextRun("テキスト")]
})
```

| 倍率 | line 値（概算） | 用途 |
|------|----------------|------|
| 1.0 行 | 240 | 英語文書 |
| 1.15 行 | 276 | docx-js デフォルト |
| 1.5 行 | 360 | 日本語ビジネス文書 |
| 2.0 行 | 480 | 校正用 |

### 固定行間（XML レベル）

```xml
<w:spacing w:line="400" w:lineRule="exact"/>
```

`exact`: 固定値（twips）。日本語の均等な行間に使う。

---

## 文字間隔

```javascript
// docx-js では spacing を TextRun の characterSpacing で指定
new TextRun({
  text: "テキスト",
  characterSpacing: 20  // twips 単位の字間
})
```

XML レベル:
```xml
<w:rPr>
  <w:spacing w:val="20"/>  <!-- twips 単位の字間 -->
</w:rPr>
```

---

## ルビ（ふりがな）

ルビは OOXML の `<w:ruby>` 要素で記述する。docx-js では直接サポートされていないため、XML 編集（unpack → edit → pack）で対応する。

```xml
<w:r>
  <w:ruby>
    <w:rubyPr>
      <w:rubyAlign w:val="distributeSpace"/>
      <w:hps w:val="12"/>           <!-- ルビのフォントサイズ（half-point） -->
      <w:hpsRaise w:val="22"/>      <!-- ルビの高さ -->
      <w:hpsBaseText w:val="24"/>   <!-- 本文のフォントサイズ -->
      <w:lid w:val="ja-JP"/>
    </w:rubyPr>
    <w:rt>                          <!-- ルビテキスト -->
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="Yu Gothic" w:eastAsia="游ゴシック"/>
          <w:sz w:val="12"/>
        </w:rPr>
        <w:t>かんじ</w:t>
      </w:r>
    </w:rt>
    <w:rubyBase>                    <!-- 本文テキスト -->
      <w:r>
        <w:rPr>
          <w:rFonts w:ascii="Yu Gothic" w:eastAsia="游ゴシック"/>
          <w:sz w:val="24"/>
        </w:rPr>
        <w:t>漢字</w:t>
      </w:r>
    </w:rubyBase>
  </w:ruby>
</w:r>
```

### ルビの配置オプション

| w:rubyAlign 値 | 配置 |
|----------------|------|
| `center` | 中央揃え |
| `distributeSpace` | 均等割り付け（日本語標準） |
| `distributeLetter` | 文字ごとに均等割り付け |
| `left` | 左揃え |
| `right` | 右揃え |

---

## 縦書き

セクション単位で縦書きを指定する。docx-js では直接サポートされていないため、XML 編集で対応する。

```xml
<w:sectPr>
  <w:textDirection w:val="tbRl"/>  <!-- Top to Bottom, Right to Left -->
</w:sectPr>
```

`w:textDirection` の値:
- `lrTb`: 横書き（左→右、上→下）— デフォルト
- `tbRl`: 縦書き（上→下、右→左）— 日本語縦書き

**注意:**
- 縦書き時はページサイズの width/height が自動で入れ替わる場合がある
- テーブルやリストの動作が横書きと異なる場合がある
- 画像の配置には注意が必要
