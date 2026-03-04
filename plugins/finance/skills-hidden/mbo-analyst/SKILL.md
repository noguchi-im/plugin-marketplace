---
name: mbo-analyst
description: MBO候補銘柄の発掘・分析・監視を行い、買収コスト・事業品質・支配構造・実行容易性・阻害要因の5軸評価レポートを生成する。MBO分析・スクリーニング条件・オーナー構造確認を行いたい時に使用する。
disable-model-invocation: false
user-invocable: false
allowed-tools: Read, Glob, Write, WebSearch, WebFetch, Bash, Task
---

あなたは mbo-analyst スキルとして動作している。
MBO（マネジメント・バイアウト）候補銘柄の発掘・分析・監視を行う。
対象市場は日本市場（東証上場企業）に限定する。
評価は **Gate + DualScore 構造** に従い、以下の 2 段階で行う:
- **Gate（Stage 1）**: 除外条件を先行適用し、MBO が構造的に成立しない銘柄を除去する
- **DualScore（Stage 2）**: Gate 通過銘柄に 5 軸（A/B/C/D/E）+ MCS/Tier + P_Score + Priority を算出する

## SPEC 整合ルール

- 設計仕様の正本は `/.claude/packagespec/finance/skills/mbo-analyst/SPEC.md` とする。
- 実装（この `SKILL.md`）を変更する前に、必ず SPEC を先に更新する。
- SPEC と実装で不整合を検知した場合は、SPEC を基準に契約（入力/出力/副作用/受け入れ条件）を調整する。

## モデル選択ポリシー

外部データ取得（WebFetch / WebSearch）や簡易処理は OPUS を使用せず、必ず SONNET 以下のモデルに委任する。
自セッションが OPUS で実行されている場合でも、WebFetch を直接呼び出してはならない。

| 処理カテゴリ | モデル | 理由 |
|---|---|---|
| WebFetch によるデータ取得 | **sonnet** | I/O バウンドであり OPUS 不要 |
| WebSearch + 結果解釈 | **sonnet** | 検索と要約は sonnet で十分 |
| report-collector の collect 操作 | **sonnet** | データ収集は sonnet に委任 |
| CSV 解析・スコアリング計算 | 自セッション | 計算処理のみ、外部通信なし |
| Gate 判定（mbo_gate_score.py gate） | 自セッション（Bash） | 確定的ルール適用。LLM 判断不要 |
| P_Score 算出（mbo_gate_score.py p-score） | 自セッション（Bash） | 純粋な算術計算 |
| Priority 判定（mbo_gate_score.py priority） | 自セッション（Bash） | 閾値比較のみ |
| 5 軸評価判断・レポート生成 | 自セッション | 定性判断は現セッションで実行 |
| pipeline Phase 2（scan） | **haiku** | 単純なオーナー構造確認 |
| pipeline Phase 3（analyze） | **sonnet** | 5 軸分析を含むが sonnet で十分 |

### 委任方法

WebFetch / WebSearch を伴うデータ収集タスクは、Task ツールで sonnet subagent に委任する:

```
Task(subagent_type="general-purpose", model="sonnet", prompt=<データ収集指示>)
```

subagent から結果（テキスト / JSON）を受け取り、分析・判断は自セッションで行う。

## 操作の判定

$ARGUMENTS から操作を判定する:

| 操作 | トリガー |
|---|---|
| criteria | スクリーニング条件を教えて、抽出条件、フィルタ条件 |
| scan | CSV が渡された、スクリーニング結果を渡す |
| analyze | 特定銘柄の MBO 分析依頼 |
| review | 分析済み銘柄の変化確認、定期チェック |
| batch-score | CSV の一括スコアリング、A/B 評価、財務スコアリング |
| pipeline | パイプライン実行、ファネル分析、一括分析して |
| watchlist | 候補銘柄の登録・一覧・更新・昇格、噂銘柄を記録したい、ウォッチリスト |

判定できない場合は呼び出し元に確認する。

## DB 共通手順

全操作の冒頭で DB の存在を確認する。

1. `home/finance/mbo-analyst/db/mbo.db` の存在を Bash で確認する
2. 存在しない場合 → Glob でスクリプトパスを解決し、`mbo_db.py init` で初期化する:

```bash
python3 <scripts/mbo_db.py のパス> init \
  --init-sql <scripts/init.sql のパス> \
  --db-path home/finance/mbo-analyst/db/mbo.db
```

DB パス: `home/finance/mbo-analyst/db/mbo.db`（リポジトリルートからの相対パス）

## criteria 操作

### 1. 条件構成

scoring-rubric.md を Read で読み込む:

```
.claude/plugins/finance/**/mbo-analyst/references/scoring-rubric.md
```

rubric のスクリーニング 3 層構造（L1 ゲート、L2 フィルタ、L3 重視指標）を参照し、MBO 候補スクリーニングに適した条件を構成する。

構成する条件カテゴリ:
- **L1 ゲート条件**: 業種別の必須通過条件
- **L2 バリュエーション条件**: 業種別の PBR、EV/EBITDA 閾値
- **キャッシュフロー**: FCF 利回り、営業 CF マージン等
- **財務健全性**: 自己資本比率、ネットキャッシュ等
- **企業規模**: 時価総額レンジ（MBO 実行可能な規模）
- **その他**: オーナー比率（Buffett Code で取得可能であれば）

focus が指定されている場合、その観点の条件を重視・深掘りする。
profile が指定されている場合、そのプロファイルの条件に絞って返す。

### 2. 結果返却

条件一覧を以下の形式で返す:

```
## MBO スクリーニング条件

### L1: 業種別ゲート条件
| プロファイル | ゲート条件 |
|---|---|
| α IT型 | ... |
| β SVC型 | ... |
| γ 加工型 | ... |
| δ 素材型 | ... |
| ε 資産型 | ... |

### L2: 業種別フィルタ
| 指標 | α IT型 | β SVC型 | γ 加工型 | δ 素材型 | ε 資産型 |
|---|---|---|---|---|---|
| PBR | ... | ... | ... | ... | ... |
| EV/EBITDA | ... | ... | ... | ... | ... |

### L3: 業種別重視指標
| プロファイル | 最重視指標 |
|---|---|
| ... | ... |

### 対象外業種
銀行業、保険業は MBO 対象外

### Buffett Code での設定手順
1. ...
```

### 3. イベント記録

events.jsonl に記録する:
```json
{"ts":"<ISO8601>","op":"criteria","focus":"<focus or null>","profile":"<profile or null>"}
```

## batch-score 操作

CSV の財務データ + 業種情報から A/B 評価を一括計算する。
Web 検索は一切行わない。コスト効率重視の操作。
東証業種に基づく閾値プロファイルを適用し、業種特性を考慮したスコアリングを行う。

### 1. CSV 解析

$ARGUMENTS に含まれる CSV データを解析する。

- ヘッダ行から以下の列を認識する:
  - 銘柄コード列（「証券コード」「コード」「銘柄コード」「code」等）
  - 企業名列（「銘柄名」「企業名」「company」等）
  - **業種列**（「業種」「東証業種」「sector」等）← **v3 で追加**
  - 財務指標列:
    - EV/EBITDA（「EV/EBITDA」「EV/EBITDA(会予)」等）
    - PBR（「PBR」等）
    - 時価総額（「時価総額」等。百万円 or 億円単位を認識）
    - 営業利益率（「営業利益率」等）
    - ROE（「ROE」等）
    - 自己資本比率（「自己資本比率」等）
    - FCF（「フリーCF」「FCF」等）
    - 配当利回り（「配当利回り」等）
- 銘柄コード列が特定できない場合 → エラーを返す
- 業種列がない場合 → 全銘柄に γ（加工型）を適用し、警告を出力する
- 財務指標列が不足する場合 → 利用可能な指標のみで評価し、不足を明記する

### 2. scoring-rubric 読み込み

scoring-rubric.md を Read で読み込む:

```
.claude/plugins/finance/**/mbo-analyst/references/scoring-rubric.md
```

rubric の「CSV ベーススコアリング」セクションに従い処理する。

### 3. 業種プロファイル割当

rubric のマッピングテーブルに従い、各銘柄に閾値プロファイル（α/β/γ/δ/ε）を割り当てる。

```
1. CSV の業種列 → 東証業種名で検索
2. マッチ → プロファイル割当
3. MBO 対象 × → "excluded" としてマーク
4. マッチなし → γ（加工型）をデフォルト適用、警告出力
```

### 4. L1 ゲート判定

rubric の L1 ゲート条件を各銘柄に適用する。
不合格銘柄は gate_result = "fail" としてマークし、スコアリングは行うがランキングからは除外する。

### 5. 一括スコアリング

rubric の業種別閾値テーブルと業種別ウエイト配分に従い、各銘柄の A スコアと B スコアを算出する。

**A スコア算出:**
1. 各指標（EV/EBITDA, PBR, FCF利回り, プレミアム耐性, 自己資本比率）を当該プロファイルの閾値で 1-5 にスコアリング
2. 当該プロファイルの業種別ウエイトで加重平均
3. 欠損指標がある場合は残りの指標のウエイトで再正規化
4. 小数点 1 位まで保持

**B スコア算出（CSV に営業利益率・ROE・自己資本比率がある場合）:**
1. 営業利益率を当該プロファイルの閾値でスコアリング
2. 調整 ROE を算出してスコアリング
3. 資本効率ボーナスを加算
4. 小数点 1 位まで保持

threshold が指定されている場合、A スコアがその値以上の銘柄のみを結果に含める（デフォルト: フィルタなし）。

### 6. DB 保存

mbo_db.py で一括保存する:

```bash
python3 <scripts/mbo_db.py> batch-score-save \
  --scores '<JSON配列>' \
  --source-info '<CSV概要>' \
  --db-path home/finance/mbo-analyst/db/mbo.db
```

JSON 配列の各要素:
```json
{"stock_code": "1234", "company_name": "企業名", "tse_industry": "化学", "threshold_profile": "delta", "valuation_score": 4.2, "business_score": 3.5, "gate_result": "pass", "metrics": {"ev_ebitda": 6.5, "pbr": 0.7, "premium_tolerance": 42.9, "fcf_stability": "stable"}}
```

### 7. 結果返却

スコア順にソートした結果を返す:

```
## batch-score 結果（N 件中 M 件表示）

| 順位 | コード | 企業名 | 業種 | プロファイル | A スコア | B スコア | EV/EBITDA | PBR | FCF利回り | プレミアム耐性 | ゲート |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ... | ... | 化学 | δ素材 | 4.2 | 3.5 | ... | ... | ... | +42% | pass |

### L1 ゲート除外（N 件）
| コード | 企業名 | 業種 | 除外理由 |
|---|---|---|---|

### 業種プロファイル分布
- α IT型: X 件
- β サービス型: X 件
- γ 加工型: X 件
- δ 素材型: X 件
- ε 資産型: X 件
- 対象外: X 件

### A スコア分布
- 4.0-5.0（魅力的）: X 件
- 3.0-3.9（標準）: X 件
- 2.0-2.9（やや割高）: X 件
- 1.0-1.9（割高）: X 件
```

### 8. イベント記録

```json
{"ts":"<ISO8601>","op":"batch-score","total":<n>,"gated_out":<n>,"profiles":{"alpha":<n>,"beta":<n>,"gamma":<n>,"delta":<n>,"epsilon":<n>},"a_distribution":{"4-5":<n>,"3-3.9":<n>,"2-2.9":<n>,"1-1.9":<n>},"threshold":<n or null>}
```

## scan 操作

### 1. CSV 解析

$ARGUMENTS に含まれる CSV データを解析する。

- ヘッダ行から銘柄コード列を特定する（「証券コード」「コード」「銘柄コード」「code」等）
- 企業名列があれば認識する（「銘柄名」「企業名」「company」等）
- 財務指標列があれば認識する
- 銘柄コード列を特定できない場合 → エラーを返して終了

### 2. scan 記録

mbo_db.py で scan を登録する:

```bash
python3 <scripts/mbo_db.py> scan-create \
  --source-info '<CSV概要: 行数, 認識列名>' \
  --db-path home/finance/mbo-analyst/db/mbo.db
```

返却された scan_id を以降のステップで使用する。

### 3. オーナー構造検証

各銘柄のオーナー構造確認を sonnet subagent に委任する（モデル選択ポリシー準拠）。

**委任指示:**

```
Task(subagent_type="general-purpose", model="sonnet", prompt="
以下の銘柄リストについて、各銘柄のオーナー構造を WebSearch で確認してください。

検索クエリ例:
- 「{企業名} 大株主 経営者」
- 「{企業名} オーナー経営 創業家」

確認ポイント:
- 経営者（代表取締役等）が大株主か
- 創業家・同族が経営に関与しているか
- 持株比率（判明する範囲で）

判定: pass（オーナー経営確認、概ね10%以上）/ fail（サラリーマン経営、分散株主）/ uncertain（情報不足）

対象銘柄:
{銘柄リスト（コード、企業名）}

各銘柄について以下の JSON を1行ずつ出力してください:
{\"stock_code\":\"XXXX\",\"company_name\":\"...\",\"result\":\"pass|fail|uncertain\",\"reason\":\"...\",\"ownership_pct\":N or null}
")
```

銘柄数が多い場合は 10 社ごとにバッチ分割し、複数の sonnet subagent を並列実行する。

strict: true が指定されている場合、uncertain を fail として扱う。

### 4. 結果記録

各銘柄の結果を mbo_db.py で記録する:

```bash
python3 <scripts/mbo_db.py> scan-result-add \
  --scan-id '<scan_id>' \
  --stock-code '<code>' \
  --company-name '<name>' \
  --result '<pass|fail|uncertain>' \
  --reason '<判定理由>' \
  --ownership-pct '<持株比率 or null>' \
  --db-path home/finance/mbo-analyst/db/mbo.db
```

### 5. 結果返却

候補リストを以下の形式で返す:

```
## scan 結果（scan_id: scan-XXXXXXXX-NNN）

### 通過銘柄（N 件）
| コード | 企業名 | オーナー構造 | 持株比率 |
|---|---|---|---|
| ... | ... | ... | ... |

### 除外銘柄（N 件）
| コード | 企業名 | 除外理由 |
|---|---|---|
| ... | ... | ... |

### 不確定銘柄（N 件）
| コード | 企業名 | 確認が必要な点 |
|---|---|---|
| ... | ... | ... |
```

### 6. イベント記録

```json
{"ts":"<ISO8601>","op":"scan","scan_id":"<id>","total":<n>,"pass":<n>,"fail":<n>,"uncertain":<n>}
```

## analyze 操作

### 1. 対象特定

$ARGUMENTS から分析対象を特定する。

- 銘柄コード → そのまま使用
- 企業名 → WebSearch で銘柄コードを解決
- 東証上場企業でない場合 → スコープ外を報告して終了

$ARGUMENTS から depth を抽出する（指定なし → 標準）。
$ARGUMENTS から csv-data を抽出する（CSV の財務指標がキーバリューで渡される場合がある）。

### 2. 早期終了チェック

csv-data が存在する場合のみ実行する。csv-data がない場合はこのステップをスキップしてステップ 3 へ進む。

#### A スコア即時算出

scoring-rubric.md が未読の場合は Read で読み込む。

batch-score と同じロジック（rubric の「CSV ベーススコアリング」セクション）で当該銘柄の A スコアを算出する。
csv-data に業種情報が含まれていない場合は γ（加工型）をデフォルト適用し、後続ステップで修正する。

#### MBO シグナル確認

$ARGUMENTS に以下のキーワードが含まれるかを確認する:

| シグナルキーワード | 判定 |
|---|---|
| 「MBO」「TOB」「非公開化」「買収」「ファンド」 | MBO シグナルあり |
| 「要分析」「注目」「候補」 | MBO シグナルあり |
| （上記なし） | MBO シグナルなし |

#### 早期終了判定

以下の**両方**が成立する場合に早期終了を適用する:
- A スコア < 2.5（バリュエーションが MBO に適さない水準）
- MBO シグナルなし（$ARGUMENTS にキーワードなし）

**caller=finance-advisor の場合（構造化データを返して終了）:**

```json
{
  "early_exit_check": true,
  "a_score": <算出値>,
  "threshold_profile": "<プロファイル（暫定）>",
  "mbo_signals": [],
  "recommendation": "skip",
  "reason": "A スコア {X}（バリュエーション水準が MBO 成立には不十分）。フルスコープ分析のコスト対効果が低いと判断。"
}
```

ここで終了する。アドバイザーが継続可否を判断する。

**直接呼び出しの場合（命令者に確認）:**

```
[早期終了チェック]
A スコア（暫定）: {X} / 5.0（{プロファイル}閾値、暫定）
MBO シグナル: なし

バリュエーション水準が MBO 成立には不十分と判定されました。
WebSearch を伴う本格分析（高コスト）を継続しますか？
1. 継続する（フルスコープ analyze を実行）
2. 終了する
```

「終了」が選択された場合 → A スコアと理由を簡潔に返して終了する。
「継続」が選択された場合 → ステップ 3 へ進む。

#### 早期終了条件を満たさない場合

A スコア ≥ 2.5 または MBO シグナルあり → ステップ 3 へ進む。

### 3. 収集依頼

#### csv-data が存在する場合（コスト最適化モード）

csv-data に財務指標（EV/EBITDA, PBR, 営業利益率, ROE, 自己資本比率, FCF 等）が含まれている場合、T1（決算・財務）、T2（株価・バリュエーション）、T5（キャッシュフロー）の Web 検索をスキップする。

csv-data から A 評価に必要な情報は取得済みのため、C/D/E 評価に必要なトピックのみ検索する:

| ID | カテゴリ | 検索トピック例 | csv-data 時 |
|---|---|---|---|
| T1 | 決算・財務 | 「{code} 決算 業績 売上 営業利益」 | **スキップ** |
| T2 | 株価・バリュエーション | 「{code} 株価 EV/EBITDA PBR」 | **スキップ** |
| T3 | 大株主・株主構成 | 「{企業名} 大株主 株主構成 有価証券報告書」 | 実行 |
| T4 | 経営者情報 | 「{企業名} 代表取締役 経歴 持株」 | 実行 |
| T5 | キャッシュフロー | 「{企業名} FCF フリーキャッシュフロー」 | **スキップ** |
| T6 | 業界動向 | 「{企業名} 業界 競合 動向」 | 実行 |
| T7 | MBO 事例 | 「{業界} MBO 事例」「同規模 MBO 実績」 | 実行 |

csv-data 時の search_budget:

| depth | トピック | search_budget |
|---|---|---|
| 概要 | T3 のみ | 2 |
| 標準 | T3, T4, T6, T7 | 8 |
| 詳細 | T3, T4, T6, T7 + 資産評価 + 類似 MBO | 15 |

**データ収集の委任（モデル選択ポリシー準拠）:**

上記トピックの WebSearch / WebFetch は sonnet subagent に委任する:

```
Task(subagent_type="general-purpose", model="sonnet", prompt="
以下の銘柄について情報を収集してください。

銘柄: {code} {company_name}

収集トピック:
{depth に応じた T3/T4/T6/T7 のリスト}

各トピックについて WebSearch で検索し、有用な結果があれば WebFetch で詳細を取得してください。
search_budget: {budget}（WebSearch + WebFetch の合計呼び出し回数上限）

出力形式:
各トピックごとに以下を返してください:
- トピック ID
- 取得した情報の要約
- データソースと日付
- 取得できなかった場合はその旨
")
```

subagent の結果を受け取り、C/D/E 評価の入力として使用する。

#### csv-data が存在しない場合（従来モード）

report-collector の collect 操作を sonnet subagent 経由で呼び出す（モデル選択ポリシー準拠）。

report-collector の SKILL.md を Read で探索する:

```
.claude/plugins/finance/**/report-collector/SKILL.md
```

MBO 分析に必要な検索トピック:

| ID | カテゴリ | 検索トピック例 |
|---|---|---|
| T1 | 決算・財務 | 「{code} 決算 業績 売上 営業利益」 |
| T2 | 株価・バリュエーション | 「{code} 株価 EV/EBITDA PBR」 |
| T3 | 大株主・株主構成 | 「{企業名} 大株主 株主構成 有価証券報告書」 |
| T4 | 経営者情報 | 「{企業名} 代表取締役 経歴 持株」 |
| T5 | キャッシュフロー | 「{企業名} FCF フリーキャッシュフロー」 |
| T6 | 業界動向 | 「{企業名} 業界 競合 動向」 |
| T7 | MBO 事例 | 「{業界} MBO 事例」「同規模 MBO 実績」 |

depth による制御:

| depth | トピック | search_budget |
|---|---|---|
| 概要 | T1, T2, T3 | 5 |
| 標準 | T1-T7 | 15 |
| 詳細 | T1-T7 + 資産評価 + 類似 MBO ディール分析 | 30 |

**データ収集の委任（モデル選択ポリシー準拠）:**

report-collector の collect 操作は sonnet subagent に委任する:

```
Task(subagent_type="general-purpose", model="sonnet", prompt="
report-collector スキルとして動作してください。
SKILL.md: .claude/plugins/finance/**/report-collector/SKILL.md

collect 操作を実行してください:
- 対象: {code} {company_name}
- トピック: {T1-T7 のリスト}
- search_budget: {budget}

各トピックの収集結果を JSON 形式で返してください。
")
```

subagent がエラーを返した場合 → 利用可能な情報のみで続行し、レポートに制約を明記する。

### 3.5. データ品質評価

収集データから data_quality_score を算出する（0.0-1.0）。

| 評価軸 | 計算方法 | ウエイト |
|---|---|---|
| 鮮度 | 収集情報の最新年月が分析日から 12 ヶ月以内なら 1.0、24 ヶ月以内なら 0.6、それ以上 0.2 | 0.4 |
| カバレッジ | 収集できたトピック数 / 要求トピック数 | 0.4 |
| 信頼性 | 公式（IR/開示）=1.0、報道=0.7、推定・SNS=0.3 の加重平均 | 0.2 |

**低品質・保留判定**（両方成立時）:
- data_quality_score < 0.4
- C/D 先行シグナルなし（T3/T4 で持株比率 or PE 関連情報が未検出）

```
→ 保留レポートを生成して終了する:
   - gate_pass: null、reason: "保留（要追加調査）"
   - data_quality_score の値と不足情報を明記
```

data_quality_score < 0.4 だが C/D 先行シグナルがある場合:
```
→ レポートに「データ品質警告: data_quality_score = {value}、以下の情報が不足」を明記して継続
```

data_quality_score ≥ 0.4 → Step 4（Gate 判定）へ進む。

### 4. Stage 1: Gate 判定

収集データから以下の事実を読み取り、`mbo_gate_score.py gate` に渡す:

| 引数 | 読み取り元 |
|------|-----------|
| `--industry` | 東証業種名（T1/csv-data） |
| `--market-cap-oku` | 時価総額（億円）（T2/csv-data） |
| `--owner-pct` | 経営者・創業家持株比率（T3/T4） |
| `--is-subsidiary` | 上場親会社が 50% 超保有（T3） |
| `--has-founding-family` | 創業家関与の記述あり（T3/T4） |
| `--fraud-detected` | 直近 3 年の重大不正・訴訟（T1） |
| `--pe-detected` | PE ファンド 5% 超 or PE 出身役員（T3/T4） |
| `--soft-c1-pass` | 持株 10% 以上かつオーナー構造明確（T3/T4） |
| `--soft-d-pass` | 時価総額 ≤ 500 億円かつ自己資本比率 > 20%（T1/csv-data） |
| `--soft-t-detected` | MBO/TOB/非公開化/ファンド関連の記述あり（T1-T4） |

```bash
python3 <scripts/mbo_gate_score.py> gate \
  --industry '<東証業種>' \
  --market-cap-oku <時価総額_億円> \
  --owner-pct <持株比率> \
  [--is-subsidiary] [--has-founding-family] [--fraud-detected] \
  [--pe-detected] [--soft-c1-pass] [--soft-d-pass] [--soft-t-detected]
# → {"gate_pass": bool, "gate_fail_reason": str|null, "t5_bypass": bool}
```

`gate_pass: false` → ステップ 14（Gate 除外版レポート）へジャンプ。
`gate_pass: true` → ステップ 5 へ進む（t5_bypass フラグを保持）。

### 5. 業種プロファイル判定

scoring-rubric.md を Read で読み込む（criteria で読み込み済みならスキップ）:

```
.claude/plugins/finance/**/mbo-analyst/references/scoring-rubric.md
```

対象銘柄の東証業種からプロファイル（α/β/γ/δ/ε）を判定する。
csv-data に業種情報があればそれを使用。なければ Web 検索で確認する。

### 6. A 評価（買収コスト）

rubric の A 基準に従い、当該プロファイルの閾値で評価する。

#### csv-data がある場合

csv-data の指標値を使って batch-score と同じロジック（rubric の「CSV ベーススコアリング」セクション参照）で、当該プロファイルの閾値・ウエイトで A スコアを算出する。Web 検索で得た情報があればそれも補足的に考慮する。根拠には csv-data からの算出過程を明記する。

#### csv-data がない場合（従来モード）

**バリュエーション分析（業種別閾値を適用）:**
- EV/EBITDA（当該プロファイルの閾値で判定）
- PBR（当該プロファイルの閾値で判定）
- FCF 利回り
- MBO プレミアム耐性（premium_tolerance）

**財務安全性:**
- 自己資本比率
- FCF 安定性フラグ

当該プロファイルの業種別ウエイトで A スコア（1.0-5.0）を算出し、根拠を記述する。

### 7. B 評価（事業品質）

rubric の B 基準に従い、当該プロファイルの閾値で評価する。

- 営業利益率（当該プロファイルの閾値で判定）
- 調整 ROE（自己資本比率 60% 超の場合は上方補正）
- 資本効率ボーナス

B スコア（1.0-5.0）を算出し、根拠を記述する。

### 8. C 評価（支配構造）

rubric の C 基準に従い、C1（能力）と C2（動機）の 2 軸で評価する。

**C1: MBO 能力（Ability）**
- 経営者/創業家の持株比率（合算ルールに従う）
- 友好株主比率
- 浮動株比率

**C2: MBO 動機（Motivation）— 時間軸別に分離評価**

C2 サブ項目を以下のように時間軸で分類する:

| サブ項目 | 時間軸 | 評価基準 |
|---|---|---|
| 後継課題（後継者不在リスク・世代交代圧力） | 短期（C2_short） | 創業者 60 歳超、後継者発表なし |
| 対市場ストレス（PBR < 1.0 不満・アクティビスト圧力） | 短期（C2_short） | PBR < 1.0 かつアクティビスト 5% 超 |
| 上場維持効用の低さ（情報開示コスト・市場との乖離感） | 中期（C2_mid） | 時価総額 200 億円以下、IR コスト負担感 |
| 非公開化便益（戦略的自由度・IR コスト削減） | 中期（C2_mid） | 業界再編・競合 MBO 事例あり |

**C2_short の算出:**
- 後継課題スコア（0-2.5）+ 対市場ストレススコア（0-2.5）= C2_short（0-5.0、1.0-5.0 に正規化）

**C2_mid の算出:**
- 上場維持効用低下スコア（0-2.5）+ 非公開化便益スコア（0-2.5）= C2_mid（0-5.0、1.0-5.0 に正規化）

**C2 統合:**
C2 = C2_short × 0.5 + C2_mid × 0.5

**動機不足ガードレール:**
C2 < 2.5 の場合 → Tier 上限を B に設定し、レポートに以下を記録する:
```
⚠️ 動機不足ガードレール適用: C2 = {value}（< 2.5）のため Tier 上限を B に制約
```

C1, C2 をそれぞれスコアリングし、C = C1 × 0.6 + C2 × 0.4 で統合する。

**C 属性の判定:**
- confidence: 株主構成の調査確度（high/medium/low）
- mbo_type: 7 類型から該当するものを選択
- trigger: MBO の最も可能性の高い契機を記述（短期催化 / 中期構造を区別して記述）

### 9. D 評価（実行容易性）

rubric の D 基準に従い評価する。

- LBO 余力: (EBITDA × 6) / (時価総額 × 1.4)
- 時価総額ファクター
- 浮動株ファクター

**financing_feasibility 評価（追加）:**

| 指標 | 算出式 | 判定 |
|---|---|---|
| 想定 LTV | EV / (有形固定資産 + 投資有価証券) | < 0.7 = 高い担保余力 |
| DSCR | EBITDA / (EV × 推定借入コスト 0.03) | > 1.5 = 返済余力あり |
| 担保余力 | 有形固定資産 + 投資有価証券 − 既存有利子負債 | 正値 = 担保あり |
| 金利耐性 | EBITDA / (EV × 金利水準) | > 1.0 = 高、0.5-1.0 = 中、< 0.5 = 低 |

**金利局面補正** (mbo_gate_score.py で管理する政策金利パラメータを参照):
- 政策金利 < 1% → D スコアに +0.2
- 政策金利 ≥ 2% → D スコアに -0.2
- その他 → 補正なし

financing_feasibility スコア（1.0-5.0）は LTV・DSCR・担保余力・金利耐性の加重平均で算出する。

D = LBO余力スコア × 0.3 + 時価総額スコア × 0.2 + 浮動株スコア × 0.2 + financing_feasibility スコア × 0.3 + 金利局面補正

D スコア（1.0-5.0）を算出し、根拠を記述する。

### 10. E 評価（阻害要因）

rubric の E 基準に従い評価する。

致命的要因（各 +3.0）、重大要因（各 +2.0）、注意要因（各 +1.0）をチェックし、合計を算出する。

各要因の該当/非該当を明記し、E スコア（0〜）を算出する。

### 11. 総合スコア（MCS）とティア判定

rubric の MCS 算出式とティア判定基準に従い算出する。

```
MCS = (A + B + D) × C_factor - E_penalty
```

ティアを S/A/B/C で判定し、confidence による補正を適用する。

### 12. P_Score 算出

A 評価で得た数値を `mbo_gate_score.py p-score` に渡す（追加 Web 検索不要）:

```bash
python3 <scripts/mbo_gate_score.py> p-score \
  --pbr <PBR> \
  --net-cash-ratio <ネット現金/時価総額> \
  --fcf-yield-pct <FCF利回り_%> \
  [--hidden-asset-coeff <含み益/時価総額>]   # 不明時は省略
# → {"p_score": X.X, "nav_score": N, "net_cash_score": N, "hidden_score": N|null, "fcf_score": N}
```

ネット現金 = 現金及び現金同等物 + 短期有価証券 − 有利子負債合計。負値（ネット負債）もそのまま渡す。

### 12.5. authority_signal 検出

references/authority-signal.md を Read で読み込む:

```
.claude/plugins/finance/**/mbo-analyst/references/authority-signal.md
```

authority-signal.md で定義された対象投資家ユニバースと当該銘柄を照合する。

**委任（sonnet subagent）:**

```
Task(subagent_type="general-purpose", model="sonnet", prompt="
以下の銘柄について、authority-signal の対象投資家が保有・関与しているか確認してください。

銘柄: {code} {company_name}
対象投資家リスト: {authority-signal.md から抽出したリスト}

検索クエリ例:
- 「{企業名} {投資家名} 大量保有報告」
- 「{企業名} {投資家名} 役員 取締役」

各投資家について以下の JSON を出力してください:
{\"investor\": \"...\", \"detected\": true|false, \"signal_type\": \"新規大量保有|取締役関与|共同保有化|提案履歴|null\", \"evidence\": \"...\"}
")
```

**加点ルール（検出された場合のみ）:**

| シグナル種別 | C2 加点 | D 加点 |
|---|---|---|
| 新規大量保有 | +0.3 | - |
| 取締役関与 | +0.5 | +0.3（PE出身の場合） |
| 共同保有化 | +0.2 | - |
| 提案履歴 | +0.2 | - |

加点がある場合:
- C2_short / C2_mid を按分して加点（短期催化性が高い種別は C2_short 寄り、構造的なものは C2_mid 寄り）
- C2 を再計算 → MCS を更新
- authority_signal_boost フラグを設定し、Priority 計算で 1 段階引き上げを適用

検出されなかった場合: authority_signal = null を設定し、Step 13 へ進む。

### 13. Priority 判定

**Priority_short（短期イベントドリブン重視）:**

```bash
python3 <scripts/mbo_gate_score.py> priority-short \
  --c2-short <C2_short> --mcs <MCS> [--authority-boost]
# → {"priority_short": "最優先|通常監視|要確認|対象外"}
```

判定マトリクス（authority_boost なし）:
- C2_short ≥ 3 かつ MBO_Score ≥ 閾値 → 最優先
- C2_short ≥ 3 かつ MBO_Score < 閾値 → 通常監視
- C2_short < 3 → 要確認 / 対象外

**Priority_mid（中期構造重視）:**

```bash
python3 <scripts/mbo_gate_score.py> priority-mid \
  --c2-mid <C2_mid> --p-score <P_Score> [--authority-boost]
# → {"priority_mid": "最優先|通常監視|要確認|対象外"}
```

判定マトリクス（authority_boost なし）:
- C2_mid ≥ 3 かつ P_Score ≥ 閾値 → 最優先
- C2_mid ≥ 3 かつ P_Score < 閾値 → 通常監視
- C2_mid < 3 → 要確認 / 対象外

authority_boost = true の場合: 両 Priority を 1 段階引き上げる（要確認 → 通常監視、通常監視 → 最優先）

### 14. レポート生成

Gate 通過銘柄は通常レポートを、Gate 除外銘柄は除外版レポートを生成する。

#### Gate 除外版レポート

```
# {企業名}（{銘柄コード}） MBO 分析レポート

## Gate 除外

- **Gate**: 除外（{gate_fail_reason}）
- **除外日**: {YYYY-MM-DD}
- **除外理由の詳細**: ...

5 軸評価は実施しない。
```

#### 通常レポート（Gate 通過銘柄）

以下の構造で Markdown レポートを作成する:

```
# {企業名}（{銘柄コード}） MBO 分析レポート

## サマリ
- **業種**: {東証業種} → {プロファイル}
- **Gate**: {通過 / T5バイパス}
- **Priority_short**: {最優先 / 通常監視 / 要確認}（短期・イベントドリブン）
- **Priority_mid**: {最優先 / 通常監視 / 要確認}（中期・構造重視）
- **Tier**: {S/A/B/C}（confidence: {high/medium/low}）（C2 < 2.5 の場合は上限 B）
- **MCS**: {総合スコア}
- **P_Score**: {1-5}（nav_discount: X.X, net_cash_ratio: X.X, hidden_asset: X.X, fcf_yield: X.X）
- A（買収コスト）: X.X — 一文要約
- B（事業品質）: X.X — 一文要約
- C（支配構造）: X.X（C1: X, C2_short: X, C2_mid: X） — 一文要約
- D（実行容易性）: X.X — 一文要約
- E（阻害要因）: X — 一文要約
- **mbo_type**: {類型}
- **trigger**: {想定される契機}

## A 評価: 買収コスト（{プロファイル}閾値を適用）
### バリュエーション分析
...（各指標のスコアと業種別閾値の対比を明記）
### MBO プレミアム耐性
premium_tolerance: +XX%
### スコアリング
A = X.X（業種別ウエイト: EV/EBITDA XX% + PBR XX% + ...）
根拠: ...

## B 評価: 事業品質（{プロファイル}閾値を適用）
### 営業利益率
...
### 調整 ROE
...
### 資本効率ボーナス
...
### スコアリング
B = X.X
根拠: ...

## C 評価: 支配構造
### C1: MBO 能力（Ability）
#### 経営者/創業家の持株構造
...
#### 友好株主・浮動株
...
C1 = X

### C2_short: MBO 動機（短期催化）
| チェック項目 | 該当 | 配点 |
|---|---|---|
| 後継課題（後継者不在・世代交代圧力） | ○/× | +0.0〜+2.5 |
| 対市場ストレス（PBR < 1.0・アクティビスト圧力） | ○/× | +0.0〜+2.5 |
C2_short = X

### C2_mid: MBO 動機（中期構造）
| チェック項目 | 該当 | 配点 |
|---|---|---|
| 上場維持効用の低さ（情報開示コスト・市場乖離） | ○/× | +0.0〜+2.5 |
| 非公開化便益（戦略的自由度・IR コスト削減） | ○/× | +0.0〜+2.5 |
C2_mid = X

### 統合
C2 = C2_short × 0.5 + C2_mid × 0.5 = X.X
C = C1 × 0.6 + C2 × 0.4 = X.X
動機不足ガードレール: {適用あり（Tier上限B）/ 適用なし}
confidence: {high/medium/low}
mbo_type: {類型}
trigger: {契機（短期催化 / 中期構造）}

## D 評価: 実行容易性
### LBO 余力
lbo_capacity = X.X
### 時価総額ファクター
...
### 浮動株ファクター
...
### 資金調達実行性（financing_feasibility）
- 想定LTV: X.X
- DSCR: X.X
- 担保余力: X.X（億円）
- 金利耐性: {高/中/低}
- 金利局面補正: {+0.2 / -0.2 / なし}
### スコアリング
D = X.X（金利局面補正後）
根拠: ...

## E 評価: 阻害要因
### 致命的要因
| 要因 | 該当 | 配点 |
|---|---|---|
| ... | ○/× | +3.0/0 |

### 重大要因
| 要因 | 該当 | 配点 |
|---|---|---|
| ... | ○/× | +2.0/0 |

### 注意要因
| 要因 | 該当 | 配点 |
|---|---|---|
| ... | ○/× | +1.0/0 |

E = X.X

## MCS・ティア判定
MCS = (A + B + D) × C_factor - E_penalty = X.X
ティア: {S/A/B/C}

## データ出典
...
```

事実と解釈を明確に区別して記述する。
データには必ずソースと日付を明記する。
取得できなかった情報はその旨を明示する。

### 15. DB 保存

mbo_db.py で分析結果を保存する。Gate 除外銘柄は gate_pass=false を設定し、5 軸スコアを省略する:

```bash
# Gate 通過銘柄
python3 <scripts/mbo_db.py> analyze-save \
  --stock-code '<code>' \
  --company-name '<name>' \
  --tse-industry '<東証業種>' \
  --threshold-profile '<alpha|beta|gamma|delta|epsilon>' \
  --depth '<概要|標準|詳細>' \
  --gate-pass 'true' \
  --t5-bypass '<true|false>' \
  --valuation-score <A> \
  --business-score <B> \
  --control-score <C> \
  --control-c1 <C1> \
  --control-c2 <C2> \
  --control-c2-short <C2_short> \
  --control-c2-mid <C2_mid> \
  --deal-score <D> \
  --impediment-score <E> \
  --mcs <MCS> \
  --tier '<S|A|B|C>' \
  --mbo-type '<類型>' \
  --confidence '<high|medium|low>' \
  --p-score <P_Score> \
  --p-nav-discount <nav_discount_score> \
  --p-net-cash-ratio <net_cash_ratio_score> \
  --p-hidden-asset-coeff '<hidden_score or null>' \
  --p-fcf-yield <fcf_score> \
  --priority-short '<最優先|通常監視|要確認|対象外>' \
  --priority-mid '<最優先|通常監視|要確認|対象外>' \
  --financing-feasibility '<JSON: {ltv, dscr, collateral_margin, interest_tolerance, rate_adjustment}>' \
  --authority-signal '<JSON or null>' \
  --report-path '<相対パス>' \
  --db-path home/finance/mbo-analyst/db/mbo.db

# Gate 除外銘柄
python3 <scripts/mbo_db.py> analyze-save \
  --stock-code '<code>' \
  --company-name '<name>' \
  --depth '<概要|標準|詳細>' \
  --gate-pass 'false' \
  --gate-fail-reason '<除外理由>' \
  --valuation-score 0 \
  --report-path '<相対パス>' \
  --db-path home/finance/mbo-analyst/db/mbo.db
```

### 16. レポート保存

Write で Markdown ファイルを保存する:

パス: `home/finance/mbo-analyst/reports/{code}/analyze-{YYYY-MM-DD}.md`

同日に既存ファイルがある場合: `analyze-{YYYY-MM-DD}-{seq}.md`（seq: 2, 3, ...）

保存前にディレクトリの存在を Bash で確認・作成する:

```bash
mkdir -p home/finance/mbo-analyst/reports/{code}
```

### 17. report-store 保存（任意）

report-store の SKILL.md を Read で探索する:

```
.claude/plugins/finance/**/report-store/SKILL.md
```

読み込めた場合、save 操作を呼び出す:

```
report-store save
  provenance_id: internal/analyst
  domain_id: equity
  subject: <企業名>
  date: <today>
  analyst: mbo-analyst
  tags: [interpretive]
  sources: <収集結果から継承>
  relations: [{related_id: <収集結果の store_id>, relation_type: used_input}]
  本文: <レポート Markdown>
```

report-store 利用不可 → スキップ。

### 18. Collector feedback

収集品質を評価し、問題があれば report-collector の feedback 操作を呼び出す。

| 問題 | feedback_type | 例 |
|---|---|---|
| 財務データが古い・不正確 | source-quality | 「株主構成が 1 年以上前のデータ」 |
| 必要だが未収集のカテゴリ | pattern-gap | 「経営者の持株比率が取得できていない」 |
| 検索結果のミスマッチ | query-quality | 「関連会社のデータが混入」 |

問題がなければスキップする。

### 19. 結果返却

以下を呼び出し元に返す:
- 分析レポート（Markdown）
- gate 情報（gate_pass, gate_fail_reason, t5_bypass）
- 5 軸スコア（A/B/C/D/E）、MCS、ティア（gate_pass=true の場合のみ）
- P_Score、Priority_short、Priority_mid（gate_pass=true の場合のみ）
- C 属性（confidence, mbo_type, trigger, c2_short, c2_mid）
- financing_feasibility（D評価の詳細）
- authority_signal（検出された場合。なければ null）
- store_id（report-store 保存した場合。なければ null）
- collector_feedback サマリ（なければ null）

### 20. イベント記録

```json
// Gate 通過の場合
{"ts":"<ISO8601>","op":"analyze","code":"<code>","depth":"<depth>","tse_industry":"<業種>","profile":"<プロファイル>","gate":{"pass":true,"t5_bypass":false},"scores":{"a":<n>,"b":<n>,"c":<n>,"c1":<n>,"c2_short":<n>,"c2_mid":<n>,"d":<n>,"e":<n>},"mcs":<n>,"tier":"<S|A|B|C>","p_score":<n>,"priority_short":"<最優先|通常監視|要確認>","priority_mid":"<最優先|通常監視|要確認>","financing_feasibility":{"ltv":<n>,"dscr":<n>,"interest_tolerance":"<高|中|低>"},"authority_signal":"<種別 or null>","mbo_type":"<類型>","confidence":"<high|medium|low>","data_coverage":"<full|partial>","data_quality_score":<n>,"feedback_sent":<bool>}

// Gate 除外の場合
{"ts":"<ISO8601>","op":"analyze","code":"<code>","depth":"<depth>","tse_industry":"<業種>","gate":{"pass":false,"fail_reason":"<理由>","t5_bypass":false},"scores":null,"p_score":null,"priority":null}
```

## watchlist 操作

watchlist ファイルパス: `home/finance/mbo-analyst/watchlist/candidates.jsonl`
index ファイルパス: `home/finance/mbo-analyst/watchlist/index.md`

### サブコマンド判定

$ARGUMENTS の動詞から判定する:

| サブコマンド | トリガー |
|---|---|
| add | 追加、登録、追いかけたい |
| list | 一覧、リスト、見せて |
| update | 更新、ステータス変更、メモ |
| promote | 昇格、分析に進む |

### watchlist add

#### 1. 入力解析

$ARGUMENTS から以下を取得する:
- stock_code（必須）
- company_name（必須）
- source（必須）: 情報の出所（例: いちよし経済研究所レポート2025-04）
- reason（必須）: 候補に挙げた理由
- tse_industry（任意）
- rumor_level（任意、デフォルト: medium）: high / medium / low
- note（任意）

tse_industry が提供されている場合、scoring-rubric.md のプロファイルマッピングで profile を補完する。

#### 2. 重複チェック

`candidates.jsonl` を Read で読み込む（ファイルが存在しない場合はスキップ）。
同一 stock_code が存在する場合、命令者に上書き確認を求める。

#### 3. JSONL 追記

以下の形式で1行を追記する（Edit ではなく既存行を保持して追記）:

```json
{"stock_code":"XXXX","company_name":"企業名","tse_industry":"東証業種 or null","profile":"α|β|γ|δ|ε|null","added_date":"YYYY-MM-DD","source":"情報源","rumor_level":"high|medium|low","reason":"候補理由","status":"watching","note":""}
```

ファイルが存在しない場合は新規作成する。

#### 4. index.md 再生成

`candidates.jsonl` を Read し、全エントリを status 別に整理した Markdown を生成し Write で上書き保存する:

```markdown
# MBO候補 watchlist

最終更新: YYYY-MM-DD

## watching（監視中）

| コード | 企業名 | 業種 | プロファイル | 噂確度 | 追加日 | 情報源 | 候補理由 |
|---|---|---|---|---|---|---|---|
| XXXX | 企業名 | 業種 | α | high | YYYY-MM-DD | ... | ... |

## analyzing（分析中）

| コード | 企業名 | 噂確度 | 追加日 |
|---|---|---|---|

## excluded（除外）

| コード | 企業名 | 除外理由 | 除外日 |
|---|---|---|---|

## confirmed（確定）

→ `confirmed.md` を参照
```

#### 5. イベント記録

```json
{"ts":"<ISO8601>","op":"watchlist","sub":"add","stock_code":"<code>","company_name":"<name>","rumor_level":"<level>"}
```

#### 6. 結果返却

登録内容サマリを返す。

---

### watchlist list

#### 1. JSONL 読み取り

`candidates.jsonl` を Read する。ファイルが存在しない場合は「登録されている候補銘柄はありません」を返す。

#### 2. フィルタ適用

$ARGUMENTS に status / rumor_level の指定があれば該当エントリのみ抽出する。

#### 3. テーブル返却

status 別にグルーピングし、一覧テーブルを返す。

---

### watchlist update

#### 1. JSONL 読み取り + 対象特定

`candidates.jsonl` を Read し、stock_code でエントリを特定する。見つからない場合はエラーを返す。

#### 2. フィールド更新

$ARGUMENTS で指定されたフィールドを更新する: status / note / rumor_level / reason

status が 'excluded' に変更された場合は、reason に除外理由を記録するよう促す。

#### 3. JSONL 上書き + index.md 再生成

全エントリを Write で上書き保存し、index.md を再生成する。

#### 4. イベント記録

```json
{"ts":"<ISO8601>","op":"watchlist","sub":"update","stock_code":"<code>","fields":["<更新フィールド>"]}
```

---

### watchlist promote

#### 1. 対象特定

`candidates.jsonl` を Read し、stock_code でエントリを特定する。

#### 2. status 更新 → analyzing

status を 'analyzing' に更新し、JSONL 上書き + index.md 再生成する。

#### 3. analyze パラメータ提示

以下を命令者に提示する:

```
## watchlist promote: {企業名}（{code}）

status を 'watching' → 'analyzing' に更新しました。

analyze を開始するには以下を実行してください:
> mbo-analyst analyze {code}

（tse_industry: {業種}、profile: {プロファイル}、source: {情報源}）
```

#### 4. イベント記録

```json
{"ts":"<ISO8601>","op":"watchlist","sub":"promote","stock_code":"<code>","company_name":"<name>"}
```

---

## review 操作

### 1. 対象特定

$ARGUMENTS からレビュー対象を決定する。

- 銘柄コード指定 → mbo_db.py で直近の分析を取得:
  ```bash
  python3 <scripts/mbo_db.py> get-latest-analysis \
    --stock-code '<code>' \
    --db-path home/finance/mbo-analyst/db/mbo.db
  ```
- all → mbo_db.py で分析済み全銘柄を取得:
  ```bash
  python3 <scripts/mbo_db.py> search-analyses \
    --db-path home/finance/mbo-analyst/db/mbo.db
  ```
- 分析履歴がない場合 → エラーを返す

### 2. 前回分析読み込み

対象銘柄の直近の分析レポート（Markdown）を Read で読み込む。
report_path は DB から取得済み。

### 3. 変化検出

前回分析以降の変化検出を sonnet subagent に委任する（モデル選択ポリシー準拠）。

**委任指示:**

```
Task(subagent_type="general-purpose", model="sonnet", prompt="
以下の銘柄について、{前回分析日} 以降の変化を WebSearch で確認してください。

銘柄: {code} {company_name}
前回分析日: {analyzed_at}

検索クエリ:
- 「{企業名} IR 適時開示」
- 「{code} 株価」
- 「{企業名} 大株主 変更 大量保有報告」
- 「{企業名} MBO TOB 非公開化」
- 「{企業名} ニュース」

fund-watchlist 追跡（必須）: references/fund-watchlist.md を Read で読み込み、登録ファンド群について:
- 「{企業名} {ファンド名} 大量保有報告」
- 「{企業名} PE ファンド 株主 変動」
- 大量保有報告提出・役員派遣・共同保有化を必須検出対象とする

authority-signal 追跡（必須）: references/authority-signal.md を Read で読み込み、対象投資家について:
- 「{企業名} {投資家名} 株主 変更」
- 「{企業名} {投資家名} 役員」

各検索結果について:
- 前回分析日以降の情報かどうか判定
- 変化の内容を要約
- A（買収コスト）/ B（事業品質）/ C（支配構造）/ D（実行容易性）/ E（阻害要因）のどの軸に影響するか

出力形式:
{\"changes_detected\": true|false, \"changes\": [{\"category\": \"...\", \"summary\": \"...\", \"impact_axes\": [\"A\",\"C\"], \"date\": \"...\", \"source\": \"...\"}]}
")
```

複数銘柄の場合は並列で sonnet subagent を起動する。
subagent の結果を受け取り、影響評価（ステップ 4）は自セッションで行う。

### 4. 影響評価

検出した変化の A/B/C/D/E 各軸への影響を評価する:

各軸について:
- **影響なし**: 変化がその軸の評価に影響しない
- **軽微**: スコアが変わるほどではないが注意すべき変化
- **要再分析**: スコアが変わる可能性がある重大な変化

変化がない場合 → 「変化なし」と簡潔に報告する。

**時間軸ラベルの付与:**
- 短期催化イベント（trigger）が消滅・無効化された場合 → 「短期シグナル失効」ラベルを付与し Priority_short を下方修正する
- 中期構造シナリオが継続している場合 → 「中期シナリオ継続」ラベルを付与し Priority_mid を維持する

**fund_watchlist_events の評価:**
- fund-watchlist で検出したイベント（大量保有報告・役員派遣・共同保有化）の C/D への影響を評価する
- 検出した場合 → 要再分析を強く推奨

**authority_events の評価:**
- authority-signal で検出したイベントの C2/D/Priority 再計算を推奨する
- 検出した場合 → 要再分析を推奨（authority シグナルは優先度が高い）

### 5. DB 記録

mbo_db.py でレビュー結果を保存する:

```bash
python3 <scripts/mbo_db.py> review-save \
  --stock-code '<code>' \
  --previous-analyze-id '<analyze_id>' \
  --changes-detected '<true|false>' \
  --impact-a '<none|minor|reanalyze>' \
  --impact-b '<none|minor|reanalyze>' \
  --impact-c '<none|minor|reanalyze>' \
  --impact-d '<none|minor|reanalyze>' \
  --impact-e '<none|minor|reanalyze>' \
  --reanalyze-recommended '<true|false>' \
  --time-axis-label '<短期シグナル失効|中期シナリオ継続|null>' \
  --fund-watchlist-events '<JSON配列 or null>' \
  --authority-events '<JSON配列 or null>' \
  --report-path '<相対パス or null>' \
  --db-path home/finance/mbo-analyst/db/mbo.db
```

### 6. レポート保存

変化が検出された銘柄について、Write で review レポートを保存する:

パス: `home/finance/mbo-analyst/reports/{code}/review-{YYYY-MM-DD}.md`

変化なしの場合はレポート保存をスキップする。

### 7. 結果返却

銘柄ごとの差分レポートを返す:

```
## review 結果

### {企業名}（{code}）
- 前回分析: YYYY-MM-DD
- 検出された変化: ...
- A（買収コスト）への影響: 影響なし / 軽微 / 要再分析
- B（事業品質）への影響: 影響なし / 軽微 / 要再分析
- C（支配構造）への影響: 影響なし / 軽微 / 要再分析
- D（実行容易性）への影響: 影響なし / 軽微 / 要再分析
- E（阻害要因）への影響: 影響なし / 軽微 / 要再分析
- 時間軸ラベル: 短期シグナル失効 / 中期シナリオ継続 / なし
- fund_watchlist_events: {検出イベント一覧 / なし}
- authority_events: {検出イベント一覧 / なし}
- 再 analyze 推奨: はい / いいえ
```

### 8. イベント記録

```json
{"ts":"<ISO8601>","op":"review","code":"<code>","changes_detected":<bool>,"reanalyze":<bool>,"trigger":"<変化の概要 or null>","time_axis_label":"<短期シグナル失効|中期シナリオ継続|null>","fund_watchlist_events":<bool>,"authority_events":<bool>}
```

## pipeline 操作

CSV 一括分析をファネル方式で実行する。
コスト最適化のため、各フェーズで母数を絞りながら段階的に深掘りする。

### コスト構造

| Phase | 処理 | Web 検索 | モデル | 1社あたりコスト |
|---|---|---|---|---|
| 1 | batch-score（業種別 A/B） | 0 | 自セッション | ≈$0 |
| 2 | scan（オーナー構造） | 2 | haiku | ≈$0.05 |
| 3 | analyze（5 軸） | 2-8 | sonnet | ≈$1.3 |

### 1. 入力解析

$ARGUMENTS から以下を抽出する:

- CSV データ（必須）
- a-threshold: A スコアの閾値（デフォルト: 3）— Phase 1 の足切り
- scan-strict: scan の strict モード（デフォルト: false）
- analyze-depth: analyze の depth（デフォルト: 概要）
- dry-run: true の場合、Phase 1 のみ実行して残りはコスト見積もりを返す

### 2. Phase 1: batch-score（自セッション内）

batch-score 操作と同じロジックで業種別 A/B スコアを一括計算する。Web 検索なし。

- scoring-rubric.md を読み込む
- CSV の業種列からプロファイルを割当
- L1 ゲート条件を適用
- 全銘柄の A/B スコアを業種別閾値で算出
- a-threshold 以上の銘柄を Phase 2 候補として抽出

結果を命令者に中間報告する:

```
## Phase 1 完了: batch-score

- 入力: N 社
- L1 ゲート除外: G 社
- A ≥ {threshold}: M 社（Phase 2 に進む）
- プロファイル分布: α X社 / β X社 / γ X社 / δ X社 / ε X社
- 推定残コスト: scan ≈ $X + analyze ≈ $Y = $Z
```

dry-run の場合はここで終了する。

### 3. Phase 2: scan（Haiku subagent に委任）

Phase 1 通過銘柄を 10 社ごとにバッチ分割し、Task ツールで Haiku subagent に委任する。

各 subagent への指示:

```
以下の銘柄リストについて、各銘柄のオーナー構造を WebSearch で確認してください。

確認ポイント:
- 経営者（代表取締役等）が大株主か
- 創業家・同族が経営に関与しているか
- 持株比率（判明する範囲で）

判定: pass（オーナー経営確認、概ね10%以上）/ fail（サラリーマン経営、分散株主）/ uncertain（情報不足）

対象銘柄:
{銘柄リスト（コード、企業名）}

各銘柄について以下の JSON を1行ずつ出力してください:
{"stock_code":"XXXX","company_name":"...","result":"pass|fail|uncertain","reason":"...","ownership_pct":N or null}
```

Task ツール呼び出し:
```
Task(subagent_type="general-purpose", model="haiku", prompt=<上記>)
```

複数バッチは並列実行する。

結果を集約し、scan 操作と同じ形式で mbo_db.py に記録する。

scan-strict が true の場合、uncertain を fail として扱う。

結果を命令者に中間報告する:

```
## Phase 2 完了: scan

- 入力: M 社
- pass: P 社（Phase 3 に進む）
- fail: F 社
- uncertain: U 社
```

### 4. Phase 3: analyze（Sonnet subagent に委任）

Phase 2 pass 銘柄を 1 社ずつ Sonnet subagent に委任する。

各 subagent への指示:

```
以下の銘柄の MBO 分析を行ってください。

銘柄: {code} {company_name}
業種: {tse_industry} → プロファイル: {profile}
depth: {analyze-depth}
csv-data: {CSV から抽出した当該銘柄の財務指標}

scoring-rubric.md の 5 軸評価基準に従ってください。
A/B 評価は csv-data から業種別閾値で算出してください（Web 検索不要）。
C/D/E 評価のために以下を WebSearch で確認してください:
- T3: 大株主・株主構成
- T4: 経営者情報
- T6: 業界動向（標準以上の場合）
- T7: MBO 事例（標準以上の場合）

出力はレポート全文（Markdown）としてください。
最後に以下の JSON を出力してください:
{"stock_code":"XXXX","tse_industry":"...","profile":"...","a":N,"b":N,"c":N,"c1":N,"c2_short":N,"c2_mid":N,"d":N,"e":N,"mcs":N,"tier":"S|A|B|C","priority_short":"最優先|通常監視|要確認","priority_mid":"最優先|通常監視|要確認","mbo_type":"...","confidence":"high|medium|low"}
```

Task ツール呼び出し:
```
Task(subagent_type="general-purpose", model="sonnet", prompt=<上記>)
```

最大 5 社を並列実行する。

各 subagent の結果からレポートとスコアを抽出し:
- レポートを reports/{code}/ に Write で保存
- mbo_db.py analyze-save で DB 記録（5 軸スコア、MCS、ティア、mbo_type を含む）

### 5. 最終報告

全フェーズの結果を統合して命令者に返す:

```
## pipeline 結果

### サマリ
- Phase 1（batch-score）: N 社 → M 社通過（A ≥ {threshold}、L1 ゲート除外 G 社）
- Phase 2（scan）: M 社 → P 社通過
- Phase 3（analyze）: P 社完了

### 最終候補（ティア順 → MCS 順）
| 順位 | コード | 企業名 | 業種 | ティア | MCS | A | B | C | D | E | Priority_short | Priority_mid | mbo_type |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ... | ... | ... | S | 15.2 | 4.2 | 3.8 | 4.0 | 3.5 | 1 | 最優先 | 最優先 | founder_mbo |
| 2 | ... | ... | ... | A | 12.8 | 3.9 | 4.0 | 3.6 | 3.2 | 2 | 通常監視 | 最優先 | family_holding |

### 各銘柄の分析レポートパス
- {code}: home/finance/mbo-analyst/reports/{code}/analyze-YYYY-MM-DD.md
```

### 6. イベント記録

```json
{"ts":"<ISO8601>","op":"pipeline","input":<n>,"phase1_pass":<n>,"phase2_pass":<n>,"phase3_done":<n>,"a_threshold":<n>,"analyze_depth":"<depth>"}
```
