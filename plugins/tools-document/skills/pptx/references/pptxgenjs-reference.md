# pptxgenjs リファレンス

pptxgenjs を使った .pptx 新規作成の API リファレンス。

## 目次

- [セットアップと基本構造](#セットアップと基本構造)
- [レイアウト寸法](#レイアウト寸法)
- [テキストとフォーマット](#テキストとフォーマット)
- [リストと箇条書き](#リストと箇条書き)
- [図形](#図形)
- [画像](#画像)
- [テーブル](#テーブル)
- [チャート](#チャート)
- [スライドマスター](#スライドマスター)
- [スライド背景](#スライド背景)
- [重要ルールとよくある問題](#重要ルールとよくある問題)

---

## セットアップと基本構造

```javascript
const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
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

---

## レイアウト寸法

座標はインチ単位。

| レイアウト | 幅 | 高さ |
|-----------|-----|------|
| `LAYOUT_16x9` | 10" | 5.625" |
| `LAYOUT_16x10` | 10" | 6.25" |
| `LAYOUT_4x3` | 10" | 7.5" |
| `LAYOUT_WIDE` | 13.3" | 7.5" |

---

## テキストとフォーマット

### 基本テキスト

```javascript
slide.addText("Simple Text", {
  x: 1, y: 1, w: 8, h: 2,
  fontSize: 24, fontFace: "Arial",
  color: "363636", bold: true,
  align: "center", valign: "middle"
});
```

### 文字間隔

```javascript
// charSpacing を使う（letterSpacing は無視される）
slide.addText("SPACED TEXT", {
  x: 1, y: 1, w: 8, h: 1, charSpacing: 6
});
```

### リッチテキスト（配列）

```javascript
slide.addText([
  { text: "太字 ", options: { bold: true } },
  { text: "斜体 ", options: { italic: true } },
  { text: "通常テキスト" }
], { x: 1, y: 3, w: 8, h: 1 });
```

### 改行（breakLine）

配列内のテキスト要素間で改行するには `breakLine: true` が必要:

```javascript
slide.addText([
  { text: "1 行目", options: { breakLine: true } },
  { text: "2 行目", options: { breakLine: true } },
  { text: "3 行目" }  // 最後は breakLine 不要
], { x: 0.5, y: 0.5, w: 8, h: 2 });
```

### テキストボックスのマージン

```javascript
// 図形やアイコンとテキストを揃える場合は margin: 0
slide.addText("Title", {
  x: 0.5, y: 0.3, w: 9, h: 0.6,
  margin: 0
});
```

---

## リストと箇条書き

### 箇条書き（bullet: true）

```javascript
slide.addText([
  { text: "項目 1", options: { bullet: true, breakLine: true } },
  { text: "項目 2", options: { bullet: true, breakLine: true } },
  { text: "項目 3", options: { bullet: true } }
], { x: 0.5, y: 0.5, w: 8, h: 3 });
```

**Unicode 弾丸文字は絶対に使わない。** `"* 項目"` や `"\u2022 項目"` は二重弾丸になる。

### サブ項目と番号付きリスト

```javascript
// サブ項目（インデント）
{ text: "サブ項目", options: { bullet: true, indentLevel: 1 } }

// 番号付きリスト
{ text: "手順 1", options: { bullet: { type: "number" }, breakLine: true } }
```

### スペーシング

箇条書きで `lineSpacing` を使うと過剰なギャップが生じる。代わりに `paraSpaceAfter` を使う。

---

## 図形

### 基本図形

```javascript
// 四角形
slide.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 0.8, w: 1.5, h: 3.0,
  fill: { color: "FF0000" },
  line: { color: "000000", width: 2 }
});

// 楕円
slide.addShape(pres.shapes.OVAL, {
  x: 4, y: 1, w: 2, h: 2,
  fill: { color: "0000FF" }
});

// 線
slide.addShape(pres.shapes.LINE, {
  x: 1, y: 3, w: 5, h: 0,
  line: { color: "FF0000", width: 3, dashType: "dash" }
});
```

### 透過

```javascript
slide.addShape(pres.shapes.RECTANGLE, {
  x: 1, y: 1, w: 3, h: 2,
  fill: { color: "0088CC", transparency: 50 }
});
```

### 角丸

```javascript
// ROUNDED_RECTANGLE を使う（RECTANGLE の rectRadius は無効）
slide.addShape(pres.shapes.ROUNDED_RECTANGLE, {
  x: 1, y: 1, w: 3, h: 2,
  fill: { color: "FFFFFF" }, rectRadius: 0.1
});
```

角丸にアクセント矩形を重ねると角が見えてしまう。その場合は RECTANGLE を使う。

### 影

```javascript
const makeShadow = () => ({
  type: "outer", color: "000000",
  blur: 6, offset: 2, angle: 135, opacity: 0.15
});

slide.addShape(pres.shapes.RECTANGLE, {
  x: 1, y: 1, w: 3, h: 2,
  fill: { color: "FFFFFF" },
  shadow: makeShadow()  // 毎回新規オブジェクト
});
```

| プロパティ | 型 | 範囲 | 備考 |
|-----------|-----|------|------|
| type | string | "outer", "inner" | |
| color | string | 6 桁 hex | `#` 不要、8 桁禁止 |
| blur | number | 0-100 pt | |
| offset | number | 0-200 pt | 負値禁止（ファイル破損） |
| angle | number | 0-359 | 135=右下、270=上方向 |
| opacity | number | 0.0-1.0 | 透過はここで指定 |

上方向の影は `angle: 270` + 正の offset を使う（負の offset は使わない）。

### 利用可能な図形

RECTANGLE, OVAL, LINE, ROUNDED_RECTANGLE

---

## 画像

### 画像ソース

```javascript
// ファイルパス
slide.addImage({ path: "images/chart.png", x: 1, y: 1, w: 5, h: 3 });

// base64（ファイル I/O 不要で高速）
slide.addImage({ data: "image/png;base64,iVBORw0KGgo...", x: 1, y: 1, w: 5, h: 3 });
```

### 画像オプション

```javascript
slide.addImage({
  path: "image.png",
  x: 1, y: 1, w: 5, h: 3,
  rounding: true,          // 円形クロップ
  transparency: 50,        // 0-100
  altText: "説明文",
  hyperlink: { url: "https://example.com" }
});
```

### サイズモード

```javascript
// contain — 枠内に収める（アスペクト比維持）
{ sizing: { type: "contain", w: 4, h: 3 } }

// cover — 枠を埋める（アスペクト比維持、はみ出し切り取り）
{ sizing: { type: "cover", w: 4, h: 3 } }

// crop — 特定部分を切り取り
{ sizing: { type: "crop", x: 0.5, y: 0.5, w: 2, h: 2 } }
```

### アスペクト比を維持した寸法計算

```javascript
const origWidth = 1978, origHeight = 923, maxHeight = 3.0;
const calcWidth = maxHeight * (origWidth / origHeight);
const centerX = (10 - calcWidth) / 2;  // 16:9 の場合

slide.addImage({
  path: "image.png", x: centerX, y: 1.2,
  w: calcWidth, h: maxHeight
});
```

対応フォーマット: PNG, JPG, GIF, SVG

---

## テーブル

### 基本テーブル

```javascript
slide.addTable([
  ["見出し 1", "見出し 2"],
  ["セル 1", "セル 2"]
], {
  x: 1, y: 1, w: 8, h: 2,
  border: { pt: 1, color: "999999" },
  fill: { color: "F1F1F1" }
});
```

### スタイル付きテーブル

```javascript
const headerRow = [
  {
    text: "項目",
    options: {
      fill: { color: "6699CC" },
      color: "FFFFFF", bold: true
    }
  },
  {
    text: "金額",
    options: {
      fill: { color: "6699CC" },
      color: "FFFFFF", bold: true
    }
  }
];

slide.addTable([headerRow, ["商品 A", "¥10,000"]], {
  x: 1, y: 3.5, w: 8, colW: [4, 4]
});
```

### セル結合

```javascript
[{ text: "結合セル", options: { colspan: 2 } }]
```

---

## チャート

### 棒グラフ

```javascript
slide.addChart(pres.charts.BAR, [{
  name: "売上",
  labels: ["Q1", "Q2", "Q3", "Q4"],
  values: [4500, 5500, 6200, 7100]
}], {
  x: 0.5, y: 0.6, w: 6, h: 3,
  barDir: "col",
  showTitle: true, title: "四半期売上"
});
```

### 折れ線グラフ

```javascript
slide.addChart(pres.charts.LINE, [{
  name: "推移",
  labels: ["1月", "2月", "3月"],
  values: [32, 35, 42]
}], {
  x: 0.5, y: 4, w: 6, h: 3,
  lineSize: 3, lineSmooth: true
});
```

### 円グラフ

```javascript
slide.addChart(pres.charts.PIE, [{
  name: "シェア",
  labels: ["製品A", "製品B", "その他"],
  values: [35, 45, 20]
}], { x: 7, y: 1, w: 5, h: 4, showPercent: true });
```

### モダンなチャートスタイル

```javascript
slide.addChart(pres.charts.BAR, chartData, {
  x: 0.5, y: 1, w: 9, h: 4, barDir: "col",
  chartColors: ["0D9488", "14B8A6", "5EEAD4"],
  chartArea: { fill: { color: "FFFFFF" }, roundedCorners: true },
  catAxisLabelColor: "64748B",
  valAxisLabelColor: "64748B",
  valGridLine: { color: "E2E8F0", size: 0.5 },
  catGridLine: { style: "none" },
  showValue: true,
  dataLabelPosition: "outEnd",
  dataLabelColor: "1E293B",
  showLegend: false
});
```

### 利用可能なチャート種類

BAR, LINE, PIE, DOUGHNUT, SCATTER, BUBBLE, RADAR

---

## スライドマスター

```javascript
pres.defineSlideMaster({
  title: "TITLE_SLIDE",
  background: { color: "283A5E" },
  objects: [{
    placeholder: {
      options: {
        name: "title", type: "title",
        x: 1, y: 2, w: 8, h: 2
      }
    }
  }]
});

const titleSlide = pres.addSlide({ masterName: "TITLE_SLIDE" });
titleSlide.addText("My Title", { placeholder: "title" });
```

---

## スライド背景

```javascript
// 単色
slide.background = { color: "F1F1F1" };

// 透過付き単色
slide.background = { color: "FF3399", transparency: 50 };

// 画像
slide.background = { path: "background.jpg" };

// base64 画像
slide.background = { data: "image/png;base64,iVBORw0KGgo..." };
```

グラデーション塗りはネイティブ未対応。グラデーション画像を背景として使用する。

---

## 重要ルールとよくある問題

### 禁止事項（ファイル破損の原因）

1. **`#` 付き hex カラー禁止** — `"FF0000"` を使う（`"#FF0000"` は破損する）
2. **8 桁 hex カラー禁止** — `"00000020"` はファイルを破損する。`opacity` プロパティを使う
3. **Unicode 弾丸文字禁止** — `"* 項目"` は二重弾丸になる。`bullet: true` を使う
4. **影の offset に負値禁止** — ファイルが破損する。上方向の影は `angle: 270` で実現する
5. **オブジェクト再利用禁止** — pptxgenjs はオプションオブジェクトを内部で変換する。毎回新規に作る

### 注意事項

6. **breakLine: true** — 配列内の各テキスト項目に必要（最後の項目は不要）
7. **lineSpacing と bullet の併用禁止** — 過剰なギャップになる。`paraSpaceAfter` を使う
8. **pptxgen() の再利用禁止** — プレゼンテーションごとに新しいインスタンスを作る
9. **ROUNDED_RECTANGLE + アクセント矩形** — 角丸が見えてしまう。RECTANGLE を使う
10. **テキストボックスの margin** — 図形と位置を揃える時は `margin: 0` を設定する
