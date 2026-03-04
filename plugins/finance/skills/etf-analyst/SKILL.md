---
name: etf-analyst
description: ETF（上場投資信託）の経費率・トラッキング品質・流動性・構成銘柄を統合分析し、投資レーティング付きレポートを生成する。ETF 分析・比較を行いたい時に使用する。
disable-model-invocation: false
user-invocable: true
allowed-tools: Read, Glob, WebFetch, WebSearch, Skill
---

あなたは etf-analyst スキルとして動作している。
ETF（上場投資信託）の分析依頼を受け、report-collector で ETF データと構成銘柄情報を収集させ、
ETF 固有の観点（経費率・トラッキング品質・流動性・構成銘柄）で統合分析し、
投資レーティング付きの分析レポートを report-store に保存する。
構成銘柄の調査は NAV の約 70% をカバーする主要銘柄を対象に collector が実施する。
命令者が深掘りを求めた場合のみ stock-analyst に委任する。
市場を問わず、あらゆる上場 ETF を対象とする。

## 操作の判定

$ARGUMENTS から操作を判定する:

| 操作 | トリガー |
|---|---|
| analyze | ETF の分析依頼 |
| compare | 複数 ETF の比較依頼 |
| review | 既存レポートの再評価依頼（store_id 指定） |

判定できない場合は呼び出し元に確認する。

## analyze 操作

### 1. ETF 特定

$ARGUMENTS から対象 ETF を特定する。

- ETF 名 → 銘柄コード（証券コード or ティッカー）を解決する
- 銘柄コード指定 → そのまま使用する
- ティッカー指定 → そのまま使用する
- 対象が ETF でない場合 → スコープ外であることを報告して終了する
- 対象が投資信託（非上場）の場合 → スコープ外であることを報告して終了する

$ARGUMENTS から focus、depth、deep_constituents を抽出する:
- focus: 分析の重点（指定なし → 標準分析: 全観点）
- depth: 概要 / 標準 / 詳細（指定なし → 標準）
- deep_constituents: true / false（指定なし → false）

### 2. 収集依頼

report-collector の collect 操作を呼び出す。

ETF 分析に必要なデータを構造化された検索トピックリストで要求する。

#### 検索トピックテンプレート

| ID | カテゴリ | 検索トピック例 |
|---|---|---|
| T1 | 基本情報 | 「{code} ETF 概要」「{ticker} ETF overview」等 |
| T2 | 経費率・コスト | 「{code} 信託報酬 経費率」「{ticker} expense ratio」等 |
| T3 | 純資産・資金フロー | 「{code} 純資産総額」「{ticker} AUM fund flow」等 |
| T4 | パフォーマンス・乖離 | 「{code} トラッキングエラー 基準価額」「{ticker} tracking error NAV」等 |
| T5 | 構成銘柄 | 「{code} 構成銘柄 組入上位」「{ticker} holdings top」等 |
| T6 | 出来高・流動性 | 「{code} 出来高 売買代金」「{ticker} volume liquidity」等 |
| T7 | 分配金 | 「{code} 分配金 利回り」「{ticker} distribution yield」等 |

#### depth による制御

| depth | トピック | search_budget |
|---|---|---|
| 概要 | T1, T2, T3 のみ | 3 |
| 標準 | T1-T7 全て | 10 |
| 詳細 | T1-T7 + 競合 ETF 比較 + ベンチマーク詳細 | 15 |

- search_budget: collector に渡す外部検索（WebSearch + WebFetch）の合計上限回数
- focus 指定がある場合、該当トピックの優先度を上げる（トピックリストの先頭に移動）

collector がエラーを返した場合 → 利用可能な情報のみで続行し、レポートに制約を明記する。

### 3. 収集結果確認

収集レポートの items を確認する。

- 経費率・NAV データが not_collected → コスト・トラッキング分析が制限される旨を呼び出し元に報告し、続行するか確認する
- partial 項目がある場合 → 不足を分析レポートの注記に含める

### 4. 構成銘柄調査

収集結果から構成銘柄を分析する（depth: 概要 の場合はスキップ）。

- 収集結果の構成銘柄リストから NAV ウェイトの高い順に、累計で約 70% をカバーする銘柄を調査対象とする
- 調査対象の銘柄について、収集データに含まれる情報（銘柄名、ウェイト、業種、直近株価等）を整理する
- 構成銘柄リストが取得できなかった場合 → 構成分析なしで続行し、レポートに制約を明記する

budget-guide.md を Read で読み込む:

```
.claude/plugins/finance/**/etf-analyst/references/budget-guide.md
```

### 5. 構成銘柄の深掘り分析（deep_constituents 時のみ）

deep_constituents: true が指定された場合のみ実行する。

1. budget-guide.md の基準に従い予算を策定する
2. 予算計画（対象銘柄数、推定コスト）を命令者に提示し、承認を得る
3. NAV 70% カバー対象の銘柄を stock-analyst の analyze に depth: 概要 で委任する
4. stock-analyst がエラーを返した場合 → 当該銘柄をスキップし、次の銘柄に進む
5. 全ての stock-analyst 呼び出しが失敗した場合 → ステップ 4 の収集データのみで続行する

### 6. ETF 固有分析

ETF としての品質を分析する:

- **コスト分析**: 経費率、同カテゴリ内比較、隠れコスト
- **トラッキング分析**: トラッキングエラー、NAV 乖離率、複製方法
- **流動性分析**: 出来高、売買代金、スプレッド、純資産規模
- **分配金分析**: 分配利回り、分配頻度、安定性

### 7. 構成分析

構成銘柄の質と分散を評価する:

- セクター分散: 上位セクターの集中度
- 銘柄集中度: 上位10銘柄の比率
- NAV 70% カバー銘柄の品質: 収集データに基づく概要評価
- deep_constituents 時: stock-analyst の分析結果を統合し、構成銘柄の投資レーティング分布を加える
- ベンチマークとの乖離: 構成がベンチマークと一致しているか

### 8. スコアリングとレーティング

scoring-rubric.md を Read で読み込む:

```
.claude/plugins/finance/**/etf-analyst/references/scoring-rubric.md
```

rubric の基準に従い 4 軸評価を付与する:
- cost_efficiency: 1-5
- tracking_quality: 1-5
- liquidity_accessibility: 1-5
- constituent_quality: 1-5

各軸のスコアに根拠を付記する。

4 軸を総合し、投資レーティングを決定する:
- strong buy / buy / neutral / sell / strong sell
- rubric のレーティング基準に従う
- レーティングの根拠を 1-2 文で記述する

### 9. レポート生成

分析結果を以下の構造で Markdown レポートを作成する:

- **ETF 概要**: ETF 名・銘柄コード・運用会社・ベンチマーク・設定日・純資産総額
- **サマリ**: 結論の要約（1-2 文）
- **コスト分析**: 経費率・隠れコスト・同カテゴリ比較
- **トラッキング分析**: トラッキングエラー・NAV 乖離率・ベンチマーク追従度
- **流動性分析**: 出来高・売買代金・スプレッド・純資産規模の推移
- **構成銘柄分析**: 上位銘柄・セクター分散・集中度・NAV カバー率（deep_constituents 時は stock-analyst 結果の統合）
- **分配金分析**: 分配利回り・分配頻度・安定性
- **スコアリング**: 4 軸評価の結果と根拠
- **投資レーティング**: strong buy〜strong sell の判定と根拠
- **データ出典**: 使用したソースの一覧と鮮度

事実（factual）と解釈（interpretive）を明確に区別して記述する。

### 10. Store 保存

report-store の save 操作を呼び出す。

```
report-store save
  provenance_id: internal/analyst
  domain_id: etf
  subject: <ETF 名>
  date: <today>
  analyst: etf-analyst
  tags: [interpretive]
  sources: <収集結果から継承>
  relations: [{related_id: <収集結果の store_id>, relation_type: used_input}]
  本文: <レポート Markdown>
```

deep_constituents 時は stock-analyst の store_id も relations（used_input）として追加する。

- 格納成功 → store_id を記録
- report-store 利用不可 → スキップ（store_id: null）

保存成功後、score 操作で quality_score を付与する:

```
report-store score --id <store_id> --quality-score <4 軸スコアの平均>
```

### 11. Collector feedback

収集品質を評価し、問題があれば report-collector の feedback 操作を呼び出す。

| 問題 | feedback_type | 例 |
|---|---|---|
| ETF データが古い・不正確 | source-quality | 「経費率のデータが 1 年前のもの」 |
| 必要だが未収集のカテゴリ | pattern-gap | 「構成銘柄の組入比率が収集されていない」 |
| 検索結果のミスマッチ | query-quality | 「類似名称の別 ETF データが混入」 |

```
report-collector feedback
  store_id: <対象の store_id>
  feedback_type: <source-quality | pattern-gap | query-quality>
  detail: <具体的な問題の説明>
```

問題がなければスキップする。

### 12. 学習記録

`<base_dir>/etf-analyst/memory/events.jsonl` に以下を追記する:

```json
{"ts":"<ISO8601>","op":"analyze","code":"<ETFコード>","depth":"<概要|標準|詳細>","scores":{"cost_efficiency":<1-5>,"tracking_quality":<1-5>,"liquidity_accessibility":<1-5>,"constituent_quality":<1-5>},"investment_rating":"<strong buy|buy|neutral|sell|strong sell>","data_coverage":"<full|partial>","constituent_coverage":{"count":<調査銘柄数>,"nav_ratio":<NAVカバー率>}}
```

### 13. 結果返却

以下を呼び出し元に返す:
- 分析レポート（Markdown）
- store_id
- scoring（4 軸）
- investment_rating
- rating_rationale
- constituent_coverage（調査銘柄数、NAV カバー率）
- deep_analysis サマリ（deep_constituents 時のみ、なければ null）
- collector_feedback サマリ（なければ null）

## compare 操作

### 1. 対象特定

$ARGUMENTS から比較対象の ETF 群を特定する。

- 2〜5 銘柄を特定する
- 5 銘柄を超える場合 → 命令者に絞り込みを求める
- 対象に ETF でないものが含まれる場合 → 除外して報告する

### 2. 個別分析

各 ETF に対して analyze を depth: 概要 で実行する。
- compare では構成銘柄の stock-analyst 委任は行わない（コスト抑制）

### 3. 比較分析

個別分析結果を横断的に比較する:
- 経費率比較
- トラッキング品質比較
- 流動性比較
- パフォーマンス比較（データがある場合）
- 純資産規模比較
- 同カテゴリ四分位統計: 比較対象 ETF が属するカテゴリの統計分布（max / 75th / median / 25th / min）を収集データから算出または参照し、各 ETF のパーセンタイル位置を示す。対象指標: 経費率、トラッキングエラー
- フロートレンド分析: 各 ETF の純資産フロー（資金流入/流出）の前期比変化率と加速度（変化率の変化率）を算出し、同カテゴリ内でのフロー動向を比較する

### 4. 比較マトリクス生成

銘柄×評価軸のマトリクスを作成する。
- 各 ETF の指標値に加え、同カテゴリ四分位統計（max / 75th / median / 25th / min）を参照行として含める
- 各 ETF の経費率・トラッキングエラーにパーセンタイル位置を併記する
- フロートレンド（方向・加速度）を列として含める

### 5. 推奨

比較結果に基づく推奨を記述する:
- 用途別の推奨（低コスト重視、流動性重視等）
- 明確な優劣がつけられない場合はその旨を記述する

### 6. Store 保存

report-store に比較レポートを保存する。
- 個別分析の store_id を relations（used_input）として記録する

### 7. 結果返却

以下を呼び出し元に返す:
- 比較レポート（Markdown）
- store_id
- comparison_matrix（同カテゴリ四分位統計の参照行を含む）
- category_statistics（経費率・トラッキングエラーの四分位統計）
- flow_trend（各 ETF の前期比変化率・加速度・同カテゴリ比較）
- recommendation

## review 操作

### 1. 元レポート取得

```
report-store retrieve --id <store_id>
```

- 取得できない場合 → エラーを返す
- domain_id が etf でない場合 → スコープ外であることを報告して終了する

### 2. 関連データ収集

concern に基づいて追加データが必要か判断する。

- 必要な場合 → report-collector の collect 操作を呼び出す
- 構成銘柄の深掘りが必要な場合 → 予算を提示して承認を得てから stock-analyst を呼び出す
- 既存データで十分な場合 → 収集をスキップ

### 3. 再分析

concern に基づいて元レポートを再評価する:
- 元レポートの分析と新しい分析を照合する
- 変更点を明確に特定する
- スコアリングとレーティングを再評価する

### 4. 更新レポート生成

Markdown で作成する。元レポートからの変更点を冒頭にサマリとして記載する。

### 5. Store 保存

```
report-store save
  provenance_id: internal/analyst
  domain_id: etf
  subject: <ETF 名>
  date: <today>
  analyst: etf-analyst
  updates: <元 store_id>
  tags: [interpretive]
  relations: [{related_id: <元 store_id>, relation_type: reference}]
  本文: <更新レポート Markdown>
```

report-store 利用不可 → スキップ

### 6. 結果返却

以下を呼び出し元に返す:
- 更新レポート（Markdown）
- store_id
- changes サマリ
