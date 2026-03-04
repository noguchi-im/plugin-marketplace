# 面接プロトコル

analyst-catalog の面接手順・抽出ルール・評価基準・集約方法を定義する。

## capability 抽出ルール

SKILL.md の各セクションから以下のフィールドを抽出する。

### domain

**参照セクション**: 冒頭の説明（frontmatter の description + 開頭段落）

アナリストの分析ドメインを特定する。

| SPEC の記述パターン | domain 値 |
|---|---|
| 個別株式・企業 | 個別株式分析 |
| ETF（上場投資信託） | ETF分析 |
| 投資商品（投信等、ETF 除く） | 投資商品分析 |
| マクロ経済 | マクロ経済分析 |
| セクター・業種 | セクター分析 |
| ポートフォリオ | ポートフォリオ分析 |
| 投資テーマ / マクロテーマ | テーマ分析 |

上記に該当しない場合は、目的の記述から最も適切なドメイン名を生成する。

### market

**参照セクション**: 冒頭の説明、操作内のパラメータ

対象市場を特定する。

| 手がかり | market 値 |
|---|---|
| 日本株、銘柄コード（4桁）、証券コード | 日本株 |
| 米国株、ティッカー | 米国株 |
| 特定の言及なし | null |

### operations

**参照セクション**: 操作の判定テーブル（`## 操作の判定`）

操作名をリストとして列挙する。

例: 操作の判定テーブルに analyze と review があれば → `[analyze, review]`

操作セクション見出し（`## X 操作`）にサブモードが存在する場合（`## review/update 操作`、`## review/validate 操作` 等）、
操作の判定テーブルの操作名ではなくサブモード名で展開して列挙する。

例: `## review/update 操作` と `## review/validate 操作` があれば → `[review/update, review/validate]`

### focus_areas

**参照セクション**: 各操作の処理ステップ（主操作）

分析の主要観点を抽出する。主操作の処理ステップ内で分析作業として記述されているステップから観点を取得する。

例: 「ファンダメンタルズ分析」「バリュエーション分析」「定性分析」があれば → `[ファンダメンタルズ, バリュエーション, 定性分析]`

### depth_levels

**参照セクション**: 各操作の処理ステップ、パラメータ抽出部

対応する分析深度をリストとして列挙する。

例: depth オプションに「概要 / 標準 / 詳細」があれば → `[概要, 標準, 詳細]`

depth の概念がない場合 → null

### input_type

**参照セクション**: 各操作のパラメータ抽出部（$ARGUMENTS）

入力の種類を 1 文で要約する。

例: 「自然言語の分析依頼（企業名・銘柄コード）+ オプション（focus, depth）」

### output_type

**参照セクション**: 結果返却セクション

出力の種類を 1 文で要約する。

例: 「構造化 Markdown レポート + スコアリング + 投資レーティング」

## competence 評価ルール

### rubric 検査

1. アナリスト実装ディレクトリの references/ を Glob で検索する
2. `*rubric*` または `*scoring*` にマッチするファイルを探す
3. 検索パス:
   - `.claude/plugins/finance/skills/<analyst_name>/references/`
   - `.claude/plugins/finance/skills-hidden/<analyst_name>/references/`

| 結果 | rubric_exists | rubric_updated |
|---|---|---|
| ファイルあり | true | `stat -c %Y` で取得した日時を YYYY-MM-DD に変換 |
| ファイルなし | false | null |

### report-store 検索

report-store の search 操作で `--analyst <analyst_name>` を検索する。

| 結果 | analysis_count | last_analysis |
|---|---|---|
| 結果あり | 件数 | 最新レポートの date |
| 結果なし | 0 | null |
| エラー | 0 | null |

### ジャーナル検査

ジャーナルファイル `<base_dir>/analyst-catalog/journals/<analyst_name>.yaml` を確認する。

| 結果 | 処理 |
|---|---|
| ファイルあり | Read で読み込み、ジャーナル集約ルールで集約する |
| ファイルなし | quality_summary: null, strength_areas: [], weakness_areas: [] |

## ジャーナル集約ルール

ジャーナルエントリのリストから competence フィールドを導出する。

### quality_summary

outcome の分布を集計し、以下のテンプレートで生成する:

```
{useful_count}/{total_count} useful ({useful_pct}%), {partial_count} partial, {not_useful_count} not_useful
```

例: `8/10 useful (80%), 1 partial, 1 not_useful`

エントリが 0 件の場合 → null

### strength_areas

1. outcome が useful のエントリを抽出する
2. task_summary を分類し、頻出パターンを特定する
3. 3 件以上の useful がある task_summary パターンを strength_areas に追加する
4. 最大 5 件まで

例: `["ファンダメンタルズ分析", "バリュエーション評価"]`

useful エントリが 3 件未満の場合 → 空リスト

### weakness_areas

1. outcome が not_useful のエントリを抽出する
2. task_summary を分類し、頻出パターンを特定する
3. 2 件以上の not_useful がある task_summary パターンを weakness_areas に追加する
4. note の内容も参考にする（問題点の具体的記述）
5. 最大 5 件まで

例: `["リスク分析の深度不足"]`

not_useful エントリが 2 件未満の場合 → 空リスト

## カタログエントリ構造

```yaml
name: <スキル名>
registered_at: <初回登録日 YYYY-MM-DD>
updated_at: <最終更新日 YYYY-MM-DD>
capability:
  domain: <分析ドメイン>
  market: <対象市場 or null>
  operations: [<操作名>]
  focus_areas: [<分析観点>]
  depth_levels: [<分析深度> or null]
  input_type: <入力の種類（1文）>
  output_type: <出力の種類（1文）>
competence:
  rubric_exists: <boolean>
  rubric_updated: <YYYY-MM-DD or null>
  analysis_count: <数値>
  last_analysis: <YYYY-MM-DD or null>
  quality_summary: <文字列 or null>
  strength_areas: [<文字列>]
  weakness_areas: [<文字列>]
status: active | inactive
```

### status の判定

- register 時は常に `active`
- update 時:
  - SPEC.md が存在し読み込めれば `active`
  - SPEC.md が存在しない（削除された）場合 → `inactive`

## ジャーナルエントリ構造

```yaml
- recorded_at: <YYYY-MM-DD>
  task_summary: <依頼内容の要約>
  outcome: useful | partial | not_useful
  note: <自由記述 or null>
```
