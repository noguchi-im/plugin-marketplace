# 日本語プレゼンテーション リファレンス

日本語 PowerPoint プレゼンテーション固有の設定と注意点。

## 目次

- [フォント指定（pptxgenjs）](#フォント指定pptxgenjs)
- [フォント指定（XML）](#フォント指定xml)
- [テキスト配置とアラインメント](#テキスト配置とアラインメント)
- [行間と文字間隔](#行間と文字間隔)
- [縦書き](#縦書き)
- [推奨設定まとめ](#推奨設定まとめ)

---

## フォント指定（pptxgenjs）

### 推奨フォント

| フォント | 用途 | 環境 |
|----------|------|------|
| 游ゴシック (Yu Gothic) | ゴシック体・本文/見出し | Windows / Mac 共通 |
| メイリオ (Meiryo) | 画面表示重視・プレゼン向き | Windows |
| ヒラギノ角ゴ (Hiragino Sans) | Mac 標準ゴシック | Mac |
| 游明朝 (Yu Mincho) | 明朝体・フォーマル | Windows / Mac 共通 |
| MS ゴシック (MS Gothic) | レガシー互換 | Windows |
| MS 明朝 (MS Mincho) | レガシー明朝 | Windows |

### コード例

```javascript
// 見出し: メイリオ、本文: 游ゴシック
slide.addText("プロジェクト概要", {
  x: 0.5, y: 0.3, w: 9, h: 0.8,
  fontSize: 36, fontFace: "Meiryo", bold: true, color: "1E2761"
});

slide.addText("本プロジェクトは...", {
  x: 0.5, y: 1.5, w: 9, h: 3,
  fontSize: 16, fontFace: "Yu Gothic", color: "333333"
});
```

### ポータビリティ

Windows/Mac 間でフォントが異なる場合、PowerPoint がフォント置換を行う。互換性を最大化するには:

- **游ゴシック / 游明朝**: Windows 10+ と macOS 10.9+ に搭載。最も安全
- **メイリオ**: Windows 専用だが、プレゼンでは読みやすさに優れる
- **ヒラギノ**: Mac 専用。Windows では游ゴシック等に置換される

フォールバック指定は pptxgenjs では不可。XML 編集時は `<a:ea>` でフォールバックチェーンを設定できる。

---

## フォント指定（XML）

テンプレート編集時は `<a:rPr>` 内の `<a:ea>` 要素で東アジアフォントを指定する:

```xml
<a:rPr lang="ja-JP" sz="2400" dirty="0">
  <a:latin typeface="Arial"/>
  <a:ea typeface="游ゴシック"/>
</a:rPr>
```

### フォント要素の役割

| 要素 | 対象文字 |
|------|---------|
| `<a:latin>` | ラテン文字（英数字） |
| `<a:ea>` | 東アジア文字（日本語、中国語、韓国語） |
| `<a:cs>` | 複雑スクリプト文字（アラビア語等） |

### lang 属性

日本語テキストには `lang="ja-JP"` を設定する。これにより:
- 正しいフォントフォールバックが適用される
- 禁則処理（行頭禁則・行末禁則）が有効になる
- ハイフネーションルールが日本語用になる

```xml
<!-- 日本語テキスト -->
<a:rPr lang="ja-JP" altLang="en-US" sz="2400">
  <a:ea typeface="游ゴシック"/>
</a:rPr>
<a:t>プロジェクト概要</a:t>

<!-- 混在テキスト中の英数字部分 -->
<a:rPr lang="en-US" altLang="ja-JP" sz="2400">
  <a:latin typeface="Arial"/>
</a:rPr>
<a:t>2026 Q1</a:t>
```

---

## テキスト配置とアラインメント

### 日本語プレゼンの配置ルール

- **タイトル**: 中央揃え（`algn="ctr"`）が標準
- **本文**: 左揃え（`algn="l"`）が読みやすい
- **箇条書き**: 左揃え
- **統計値・キーメッセージ**: 中央揃え

### 長い日本語テキストの折り返し

日本語は単語間にスペースがないため、英語と異なる折り返しルールが適用される。
テキストボックスの幅に注意:

```javascript
// 十分な幅を確保する
slide.addText("長い日本語のテキストがここに入ります。十分な幅がないと不自然な位置で折り返されます。", {
  x: 0.5, y: 1, w: 9, h: 2,  // 幅を広めに取る
  fontSize: 16, fontFace: "Yu Gothic",
  wrap: true  // デフォルトで true
});
```

### 禁則処理

PowerPoint は `lang="ja-JP"` が設定されたテキストに対して自動的に禁則処理を適用する:
- **行頭禁則**: 句読点（、。）、閉じ括弧（）」）は行頭に来ない
- **行末禁則**: 開き括弧（「（）は行末に来ない

XML で明示的に制御する場合:
```xml
<a:pPr>
  <a:defRPr kumimoji="1"/>  <!-- 組文字（禁則処理）有効 -->
</a:pPr>
```

---

## 行間と文字間隔

### 行間

日本語テキストは英語より行間を広く取ると読みやすい。

| 用途 | 推奨行間 | XML 値 |
|------|---------|--------|
| タイトル | 1.2 倍 | — |
| 本文 | 1.5-1.8 倍 | — |
| 箇条書き | 1.4 倍 | — |

pptxgenjs:
```javascript
slide.addText("テキスト", {
  x: 0.5, y: 1, w: 9, h: 3,
  fontSize: 16, fontFace: "Yu Gothic",
  lineSpacingMultiple: 1.5  // 1.5 倍
});
```

XML:
```xml
<!-- 固定値（ポイントの 100 倍） -->
<a:lnSpc><a:spcPts val="2800"/></a:lnSpc>

<!-- 倍率（パーセントの 1000 倍） -->
<a:lnSpc><a:spcPct val="150000"/></a:lnSpc>
```

### 文字間隔

日本語フォントは元々文字間隔が広いため、追加の文字間隔は通常不要。
タイトルで文字を詰めたい場合:

```javascript
slide.addText("タイトル", {
  x: 0.5, y: 0.5, w: 9, h: 1,
  fontSize: 36, fontFace: "Yu Gothic",
  charSpacing: -1  // わずかに詰める
});
```

---

## 縦書き

### pptxgenjs での縦書き

pptxgenjs は縦書きをネイティブサポートしていない。縦書きが必要な場合はテンプレート編集で XML を直接操作する。

### XML での縦書き設定

```xml
<p:txBody>
  <a:bodyPr vert="eaVert"/>  <!-- 東アジア縦書き -->
  <a:p>
    <a:r>
      <a:rPr lang="ja-JP" sz="2400">
        <a:ea typeface="游明朝"/>
      </a:rPr>
      <a:t>縦書きテキスト</a:t>
    </a:r>
  </a:p>
</p:txBody>
```

| vert 値 | 方向 |
|---------|------|
| `horz` | 横書き（デフォルト） |
| `eaVert` | 東アジア縦書き（句読点が回転する） |
| `vert` | 欧文縦書き（文字が回転する） |
| `vert270` | 270 度回転 |

---

## 推奨設定まとめ

### pptxgenjs での新規作成

```javascript
const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";

// 日本語プレゼンの基本設定
const TITLE_FONT = "Meiryo";      // 見出し
const BODY_FONT = "Yu Gothic";    // 本文
const TITLE_SIZE = 36;
const BODY_SIZE = 16;

const slide = pres.addSlide();

// タイトル
slide.addText("プロジェクト報告", {
  x: 0.5, y: 0.3, w: 9, h: 0.8,
  fontSize: TITLE_SIZE, fontFace: TITLE_FONT,
  bold: true, color: "1E2761"
});

// 本文（箇条書き）
slide.addText([
  { text: "進捗状況", options: { bullet: true, breakLine: true, bold: true } },
  { text: "本四半期の主要な成果を報告する", options: { bullet: true, breakLine: true } },
  { text: "次四半期の計画", options: { bullet: true, breakLine: true, bold: true } },
  { text: "新規プロジェクトの立ち上げ", options: { bullet: true } }
], {
  x: 0.5, y: 1.5, w: 9, h: 3.5,
  fontSize: BODY_SIZE, fontFace: BODY_FONT,
  color: "333333",
  lineSpacingMultiple: 1.5
});
```

### XML テンプレート編集

```xml
<!-- 日本語テキストランの標準設定 -->
<a:r>
  <a:rPr lang="ja-JP" altLang="en-US" sz="1600" dirty="0">
    <a:latin typeface="Arial"/>
    <a:ea typeface="游ゴシック"/>
  </a:rPr>
  <a:t>テキスト内容</a:t>
</a:r>
```
