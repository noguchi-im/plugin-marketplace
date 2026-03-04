# OOXML 構造リファレンス

## 目次

- [基本要素階層](#基本要素階層) — w:body, w:p, w:r, w:t の構造と pPr 要素順序
- [変更履歴](#変更履歴) — w:ins, w:del, w:delText による挿入・削除・置換
- [コメント](#コメント) — 4 XML ファイル構造、マーカー配置、返信、ID 制約
- [画像参照](#画像参照) — w:drawing, リレーションシップ、単位変換
- [スマートクォート](#スマートクォート) — XML エンティティ一覧

## 基本要素階層

```xml
<w:body>
  <w:p>                           <!-- 段落 -->
    <w:pPr>                       <!-- 段落プロパティ -->
      <w:pStyle w:val="Heading1"/>
      <w:numPr>...</w:numPr>
      <w:spacing w:before="240" w:after="240"/>
      <w:ind w:left="720"/>
      <w:jc w:val="center"/>
      <w:rPr>...</w:rPr>         <!-- 段落の既定 Run プロパティ（最後に置く） -->
    </w:pPr>
    <w:r>                         <!-- Run（テキスト単位） -->
      <w:rPr>                     <!-- Run プロパティ -->
        <w:rFonts w:ascii="Arial" w:eastAsia="MS Gothic"/>
        <w:b/>                    <!-- 太字 -->
        <w:i/>                    <!-- 斜体 -->
        <w:sz w:val="24"/>        <!-- フォントサイズ (half-point: 24 = 12pt) -->
        <w:color w:val="FF0000"/>
      </w:rPr>
      <w:t xml:space="preserve">テキスト内容</w:t>
    </w:r>
  </w:p>
</w:body>
```

### w:pPr 内の要素順序（スキーマ準拠）

以下の順序を守る。順序違反はバリデーションエラーになる。

1. `w:pStyle`
2. `w:keepNext`
3. `w:keepLines`
4. `w:pageBreakBefore`
5. `w:numPr`
6. `w:spacing`
7. `w:ind`
8. `w:jc`
9. `w:rPr`（最後）

### xml:space="preserve"

先頭・末尾に空白を含む `<w:t>` には `xml:space="preserve"` が必須:

```xml
<!-- 必要 -->
<w:t xml:space="preserve"> leading space</w:t>
<w:t xml:space="preserve">trailing space </w:t>

<!-- 不要 -->
<w:t>no surrounding spaces</w:t>
```

### RSID

RSID（Revision Save ID）は 8 桁の 16 進数:

```xml
<w:r w:rsidR="00A12B3C">
```

---

## 変更履歴

### 挿入（w:ins）

```xml
<w:ins w:id="1" w:author="Claude" w:date="2026-02-10T12:00:00Z">
  <w:r>
    <w:rPr>
      <w:rFonts w:ascii="Arial"/>
    </w:rPr>
    <w:t>挿入されたテキスト</w:t>
  </w:r>
</w:ins>
```

### 削除（w:del）

```xml
<w:del w:id="2" w:author="Claude" w:date="2026-02-10T12:00:00Z">
  <w:r>
    <w:rPr>
      <w:rFonts w:ascii="Arial"/>
    </w:rPr>
    <w:delText xml:space="preserve">削除されたテキスト</w:delText>
  </w:r>
</w:del>
```

**重要:**
- `<w:del>` 内のテキストは `<w:t>` ではなく `<w:delText>` を使う
- `<w:ins>` 内のテキストは通常の `<w:t>` を使う
- `<w:ins>` 内に `<w:delText>` を入れてはならない（`<w:del>` の中でない限り）

### テキスト置換（削除＋挿入）

```xml
<w:p>
  <w:del w:id="3" w:author="Claude" w:date="2026-02-10T12:00:00Z">
    <w:r>
      <w:rPr><w:rFonts w:ascii="Arial"/></w:rPr>
      <w:delText>旧テキスト</w:delText>
    </w:r>
  </w:del>
  <w:ins w:id="4" w:author="Claude" w:date="2026-02-10T12:00:00Z">
    <w:r>
      <w:rPr><w:rFonts w:ascii="Arial"/></w:rPr>
      <w:t>新テキスト</w:t>
    </w:r>
  </w:ins>
</w:p>
```

### 変更履歴の実装ルール

- `<w:r>` 要素全体を置換する（Run の中身だけ変えない）
- 元の `<w:rPr>`（書式）を変更履歴の Run にも保持する
- w:id は文書内でユニーク（最大値を確認して +1 する）
- w:date は ISO 8601 形式

---

## コメント

### コメント XML ファイル構造

コメントは 4 つの XML ファイルで管理される:

**word/comments.xml:**
```xml
<w:comments>
  <w:comment w:id="0" w:author="Claude" w:date="2026-02-10T12:00:00Z" w:initials="C">
    <w:p w14:paraId="1A2B3C4D">
      <w:r>
        <w:t>コメントテキスト</w:t>
      </w:r>
    </w:p>
  </w:comment>
</w:comments>
```

**word/commentsExtended.xml:**
```xml
<w15:commentsEx>
  <w15:commentEx w15:paraId="1A2B3C4D" w15:done="0"/>
</w15:commentsEx>
```

**word/commentsIds.xml:**
```xml
<w16cid:commentsIds>
  <w16cid:commentId w16cid:paraId="1A2B3C4D" w16cid:durableId="12345678"/>
</w16cid:commentsIds>
```

**word/commentsExtensible.xml:**
```xml
<w16cex:commentsExtensible>
  <w16cex:comment w16cex:durableId="12345678" w16cex:dateUtc="2026-02-10T12:00:00Z"/>
</w16cex:commentsExtensible>
```

### document.xml 内のコメントマーカー

```xml
<w:p>
  <w:commentRangeStart w:id="0"/>
  <w:r>
    <w:t>コメント対象のテキスト</w:t>
  </w:r>
  <w:commentRangeEnd w:id="0"/>
  <w:r>
    <w:rPr>
      <w:rStyle w:val="CommentReference"/>
    </w:rPr>
    <w:commentReference w:id="0"/>
  </w:r>
</w:p>
```

**マーカー配置ルール:**
- `w:commentRangeStart` と `w:commentRangeEnd` は同じ w:id でペア
- `w:commentReference` を `w:commentRangeEnd` の直後に配置
- w:id は comments.xml の w:comment@w:id と一致させる

### コメント返信

返信は `w15:commentEx` で親子関係を指定する:

```xml
<w15:commentEx w15:paraId="REPLY_PARA_ID" w15:paraIdParent="PARENT_PARA_ID" w15:done="0"/>
```

### ID の制約

- `w14:paraId`: 8 桁の 16 進数。0x80000000 未満
- `w16cid:durableId`: 0x7FFFFFFF 未満
- 文書内でユニーク

---

## 画像参照

### 画像の XML 構造

```xml
<w:r>
  <w:drawing>
    <wp:inline distT="0" distB="0" distL="0" distR="0">
      <wp:extent cx="1905000" cy="1428750"/>  <!-- EMU 単位: 1 inch = 914400 EMU -->
      <wp:docPr id="1" name="Picture 1" descr="説明"/>
      <a:graphic>
        <a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">
          <pic:pic>
            <pic:blipFill>
              <a:blip r:embed="rId5"/>       <!-- word/_rels/document.xml.rels の ID -->
            </pic:blipFill>
            <pic:spPr>
              <a:xfrm>
                <a:ext cx="1905000" cy="1428750"/>
              </a:xfrm>
            </pic:spPr>
          </pic:pic>
        </a:graphicData>
      </a:graphic>
    </wp:inline>
  </w:drawing>
</w:r>
```

### リレーションシップ

`word/_rels/document.xml.rels` に画像ファイルへの参照を追加:

```xml
<Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image"
              Target="media/image1.png"/>
```

### 単位変換

| 単位 | 用途 | 変換 |
|------|------|------|
| DXA (twentieths of a point) | ページサイズ、マージン | 1440 DXA = 1 inch |
| EMU (English Metric Unit) | 画像サイズ | 914400 EMU = 1 inch |
| Half-point | フォントサイズ | 24 half-point = 12 pt |

---

## スマートクォート

新規テキストでは常に XML エンティティを使う:

| エンティティ | 文字 | 用途 |
|-------------|------|------|
| `&#x2018;` | ' | 左シングルクォート |
| `&#x2019;` | ' | 右シングルクォート / アポストロフィ |
| `&#x201C;` | " | 左ダブルクォート |
| `&#x201D;` | " | 右ダブルクォート |
| `&#x2014;` | — | em ダッシュ |
| `&#x2013;` | – | en ダッシュ |
| `&amp;` | & | アンパサンド |
| `&lt;` | < | 小なり |
| `&gt;` | > | 大なり |
