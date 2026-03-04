# テンプレート編集リファレンス

既存 .pptx をテンプレートとして編集するワークフローと XML 構造のリファレンス。

## 目次

- [編集ワークフロー](#編集ワークフロー)
- [スクリプト一覧](#スクリプト一覧)
- [スライド操作](#スライド操作)
- [XML 構造](#xml-構造)
- [コンテンツ編集](#コンテンツ編集)
- [よくある問題](#よくある問題)

---

## 編集ワークフロー

### 1. テンプレート分析

```bash
# サムネイルグリッドでレイアウトを把握
python scripts/thumbnail.py template.pptx

# テキスト内容を確認
python -m markitdown template.pptx
```

サムネイルを見てスライドごとのレイアウトタイプを特定する:
- タイトル / セクション区切り
- テキスト + 画像（2 カラム）
- アイコン + テキスト行
- 統計カード / グリッド
- 引用 / コールアウト

### 2. スライドマッピング

各コンテンツセクションに対して、テンプレートのどのスライドレイアウトを使うか決める。

**レイアウトを変化させる** — 同じテキスト重視レイアウトの繰り返しは避ける。

### 3. 展開

```bash
python scripts/office/unpack.py template.pptx unpacked/
```

### 4. 構造操作（XML 編集前に完了させる）

この順序で実行する:

1. 不要なスライドを削除（presentation.xml の `<p:sldIdLst>` から除去）
2. 再利用するスライドを複製（`add_slide.py`）
3. スライドの順序を整える（`<p:sldIdLst>` の並び替え）

**構造操作をすべて完了してからコンテンツ編集に進む。**

### 5. コンテンツ編集

`unpacked/ppt/slides/slide{N}.xml` を Edit ツールで直接編集する。
スライドは独立したファイルなので並列編集が可能。

### 6. クリーンアップ

```bash
python scripts/clean.py unpacked/
```

削除したスライドに関連するファイル（メディア、リレーション等）を除去する。

### 7. 再パッキング

```bash
python scripts/office/pack.py unpacked/ output.pptx --original template.pptx
```

---

## スクリプト一覧

| スクリプト | 役割 |
|-----------|------|
| `office/unpack.py` | .pptx を展開し XML を整形する |
| `add_slide.py` | スライドの複製またはレイアウトからの追加 |
| `clean.py` | 孤立ファイル（未参照のスライド、メディア、リレーション）を除去 |
| `office/pack.py` | XML 検証・修復し .pptx に再パッキング |
| `thumbnail.py` | サムネイルグリッドを生成（テンプレート分析用） |

### add_slide.py

```bash
# 既存スライドの複製
python scripts/add_slide.py unpacked/ slide2.xml

# レイアウトからの新規作成
python scripts/add_slide.py unpacked/ slideLayout2.xml
```

出力: 追加された `<p:sldId>` 要素。presentation.xml の `<p:sldIdLst>` 内の希望位置に挿入する。

### clean.py

```bash
python scripts/clean.py unpacked/
```

以下を除去する:
- `<p:sldIdLst>` に含まれないスライドファイル
- どのスライドからも参照されていないメディアファイル
- 孤立したリレーションシップファイル

---

## スライド操作

### スライド順序の管理

`ppt/presentation.xml` の `<p:sldIdLst>` がスライド順序を定義する:

```xml
<p:sldIdLst>
  <p:sldId id="256" r:id="rId2"/>
  <p:sldId id="257" r:id="rId3"/>
  <p:sldId id="258" r:id="rId4"/>
</p:sldIdLst>
```

### 並び替え

`<p:sldId>` 要素の順序を変更する。`id` と `r:id` の値は変更しない。

### 削除

1. `<p:sldIdLst>` から該当の `<p:sldId>` を削除する
2. `clean.py` を実行して孤立ファイルを除去する

### 追加

`add_slide.py` を使う。手動でスライドファイルをコピーしてはならない。
スクリプトが以下を自動処理する:
- ノート参照の作成
- Content_Types.xml の更新
- リレーションシップ ID の付与

---

## XML 構造

### スライド XML の基本構造

`ppt/slides/slide{N}.xml`:

```xml
<p:sld xmlns:p="..." xmlns:a="..." xmlns:r="...">
  <p:cSld>
    <p:spTree>
      <!-- 図形ツリー（全要素がここに含まれる） -->
      <p:sp>
        <!-- テキストボックスまたは図形 -->
        <p:txBody>
          <a:p>
            <a:pPr algn="l">
              <a:lnSpc><a:spcPts val="2800"/></a:lnSpc>
            </a:pPr>
            <a:r>
              <a:rPr lang="ja-JP" sz="2400" b="1"/>
              <a:t>テキスト内容</a:t>
            </a:r>
          </a:p>
        </p:txBody>
      </p:sp>
    </p:spTree>
  </p:cSld>
</p:sld>
```

### 主要要素

| 要素 | 役割 |
|------|------|
| `<p:sp>` | 図形（テキストボックス、四角形、楕円等） |
| `<p:pic>` | 画像 |
| `<p:graphicFrame>` | チャート、表 |
| `<p:grpSp>` | グループ化された要素 |
| `<p:txBody>` | テキスト本体 |
| `<a:p>` | 段落 |
| `<a:r>` | テキストラン（同一書式のテキスト単位） |
| `<a:rPr>` | ランプロパティ（フォント、サイズ、太字等） |
| `<a:t>` | テキスト内容 |

### テキストプロパティ

```xml
<!-- フォント・サイズ・太字 -->
<a:rPr lang="ja-JP" sz="2400" b="1" dirty="0">
  <a:latin typeface="Arial"/>
  <a:ea typeface="游ゴシック"/>
</a:rPr>

<!-- sz はポイントの 100 倍（2400 = 24pt） -->
```

### 段落プロパティ

```xml
<!-- 左揃え、行間 28pt -->
<a:pPr algn="l">
  <a:lnSpc><a:spcPts val="2800"/></a:lnSpc>
</a:pPr>

<!-- algn: l=左, ctr=中央, r=右, just=両端揃え -->
```

---

## コンテンツ編集

### 基本ルール

- **Edit ツールを使う** — sed やスクリプトではなく、Edit ツールの文字列置換で編集する
- **見出しは太字にする** — `b="1"` を `<a:rPr>` に設定
- **Unicode 弾丸文字は使わない** — `<a:buChar>` または `<a:buAutoNum>` を使う
- **箇条書きはレイアウトから継承させる** — `<a:buChar>` または `<a:buNone>` のみ指定

### 複数項目のコンテンツ

各項目を個別の `<a:p>` 要素にする。1 つの文字列に連結してはならない。

正しい例:
```xml
<a:p>
  <a:pPr algn="l">
    <a:lnSpc><a:spcPts val="2800"/></a:lnSpc>
  </a:pPr>
  <a:r>
    <a:rPr lang="ja-JP" sz="2400" b="1"/>
    <a:t>ステップ 1</a:t>
  </a:r>
</a:p>
<a:p>
  <a:pPr algn="l">
    <a:lnSpc><a:spcPts val="2800"/></a:lnSpc>
  </a:pPr>
  <a:r>
    <a:rPr lang="ja-JP" sz="2400"/>
    <a:t>最初の作業を実行する。</a:t>
  </a:r>
</a:p>
```

元の段落から `<a:pPr>` をコピーして行間を保持する。

### スマートクォート

unpack/pack が自動処理する。ただし Edit ツールはスマートクォートを ASCII に変換する。

新しいテキストにクォートを含める場合は XML エンティティを使う:

```xml
<a:t>the &#x201C;Agreement&#x201D;</a:t>
```

| エンティティ | 文字 |
|-------------|------|
| `&#x201C;` | 左ダブルクォート " |
| `&#x201D;` | 右ダブルクォート " |
| `&#x2018;` | 左シングルクォート ' |
| `&#x2019;` | 右シングルクォート ' |

### ホワイトスペース

先頭・末尾にスペースがあるテキストには `xml:space="preserve"` を設定する:

```xml
<a:t xml:space="preserve"> テキスト </a:t>
```

---

## よくある問題

### テンプレート適応

テンプレートの項目数とコンテンツの項目数が合わない場合:

- **コンテンツが少ない場合**: 余分な要素（画像、図形、テキストボックス）を丸ごと削除する。テキストだけ空にしてはならない
- **コンテンツが多い場合**: オーバーフローに注意。ビジュアル QA で確認する
- **テンプレートスロット ≠ コンテンツ数**: 例えばテンプレートにチーム 4 人分あるがコンテンツは 3 人の場合、4 人目の画像 + テキストボックスのグループ全体を削除する

### XML パーサーの選択

XML のパースには `defusedxml.minidom` を使う。`xml.etree.ElementTree` は名前空間を破壊するため使用しない。

### clean.py の実行タイミング

構造操作（スライド削除・並び替え）の後、pack の前に必ず実行する。clean せずに pack すると不要ファイルが .pptx に残る。
