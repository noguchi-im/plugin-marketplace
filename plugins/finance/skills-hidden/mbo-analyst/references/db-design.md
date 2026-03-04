# mbo-analyst DB 設計ドキュメント v3

## 構成方針

### ハイブリッド構成（SQLite + Markdown）

- **SQLite（mbo.db）**: 構造化データの永続化・検索に使用する
  - scan 実行履歴と各銘柄の判定結果
  - analyze の 5 軸スコア・メタデータ
  - batch-score の一括スコアリング結果
  - review の差分検出結果
  - スクリーニング条件マスタ
- **Markdown（reports/）**: 分析レポート本文の保存に使用する
  - 人間が直接読める形式で保存
  - Git で差分追跡が可能
  - DB には report_path でパスのみ記録

### 採用理由

1. 分析レポートは長文の構造化テキストであり、BLOB として DB に格納するよりファイルとして管理する方が扱いやすい
2. スコアやメタデータは SQL で検索・集計できることに価値がある
3. DB とファイルの整合性は report_path カラムで維持する

## DB パス

`home/finance/mbo-analyst/db/mbo.db`（リポジトリルートからの相対パス）

## テーブル設計

### scans: scan 実行記録

| カラム | 型 | 説明 |
|---|---|---|
| scan_id | TEXT PK | scan-YYYYMMDD-NNN 形式の実行 ID |
| executed_at | TEXT NOT NULL | 実行日時（ISO 8601） |
| source_info | TEXT NOT NULL | CSV の概要（行数、認識列名等）。JSON 文字列 |
| total_count | INTEGER NOT NULL | CSV の総銘柄数 |
| pass_count | INTEGER NOT NULL DEFAULT 0 | オーナー構造確認済み銘柄数 |
| fail_count | INTEGER NOT NULL DEFAULT 0 | 除外銘柄数 |
| uncertain_count | INTEGER NOT NULL DEFAULT 0 | 不確定銘柄数 |

### scan_results: scan 各銘柄の結果

| カラム | 型 | 説明 |
|---|---|---|
| id | INTEGER PK AUTOINCREMENT | 内部連番 |
| scan_id | TEXT NOT NULL FK → scans | 親 scan の ID |
| stock_code | TEXT NOT NULL | 銘柄コード（証券コード） |
| company_name | TEXT | 企業名（CSV に含まれていれば） |
| tse_industry | TEXT | 東証業種名 |
| threshold_profile | TEXT | 閾値プロファイル（alpha/beta/gamma/delta/epsilon） |
| owner_check | TEXT | WebSearch で確認したオーナー構造の概要 |
| result | TEXT NOT NULL | pass / fail / uncertain |
| reason | TEXT NOT NULL | 判定理由 |
| ownership_pct | REAL | 経営者の推定持株比率（%）。不明の場合 NULL |

### analyses: analyze 結果

| カラム | 型 | 説明 |
|---|---|---|
| analyze_id | TEXT PK | analyze-YYYYMMDD-NNN 形式の分析 ID |
| stock_code | TEXT NOT NULL | 銘柄コード |
| company_name | TEXT NOT NULL | 企業名 |
| tse_industry | TEXT | 東証業種名 |
| threshold_profile | TEXT | 閾値プロファイル |
| analyzed_at | TEXT NOT NULL | 分析日時（ISO 8601） |
| depth | TEXT NOT NULL | スクリーニング / 概要 / 標準 / 詳細 |
| valuation_score | REAL NOT NULL | A 評価スコア（1.0-5.0） |
| business_score | REAL | B 評価スコア（1.0-5.0）。batch-score の場合 NULL 可 |
| control_score | REAL | C 評価スコア（1.0-5.0）。batch-score の場合 NULL |
| control_c1 | REAL | C1: MBO 能力（1-5）。NULL 可 |
| control_c2_short | REAL | C2_short: 短期催化動機スコア（1-5）。NULL 可 |
| control_c2_mid | REAL | C2_mid: 中期構造動機スコア（1-5）。NULL 可 |
| deal_score | REAL | D 評価スコア（1.0-5.0）。NULL 可 |
| financing_feasibility_json | TEXT | financing_feasibility の詳細 JSON（ltv, dscr, collateral_margin, interest_tolerance, rate_adjustment）。NULL 可 |
| impediment_score | REAL | E 評価スコア（0〜）。NULL 可 |
| mcs | REAL | MBO 総合スコア。NULL 可 |
| tier | TEXT | ティア（S/A/B/C）。NULL 可 |
| mbo_type | TEXT | MBO 類型。NULL 可 |
| confidence | TEXT | 調査確度（high/medium/low）。NULL 可 |
| priority_short | TEXT | 短期 Priority（最優先/通常監視/要確認/対象外）。NULL 可 |
| priority_mid | TEXT | 中期 Priority（最優先/通常監視/要確認/対象外）。NULL 可 |
| authority_signal_json | TEXT | authority_signal の詳細 JSON。未検出は NULL |
| data_quality_score | REAL | データ品質スコア（0.0-1.0）。NULL 可 |
| report_path | TEXT NOT NULL | Markdown レポートの相対パス |
| store_id | TEXT | report-store に保存した場合の ID。未保存は NULL |

### batch_scores: batch-score 一括スコアリング結果

| カラム | 型 | 説明 |
|---|---|---|
| id | INTEGER PK AUTOINCREMENT | 内部連番 |
| batch_id | TEXT NOT NULL | バッチ ID（batch-YYYYMMDD-NNN） |
| stock_code | TEXT NOT NULL | 銘柄コード |
| company_name | TEXT | 企業名 |
| tse_industry | TEXT | 東証業種名 |
| threshold_profile | TEXT | 閾値プロファイル |
| valuation_score | REAL | A スコア（1.0-5.0）。ゲート除外は 0 |
| business_score | REAL | B スコア（1.0-5.0）。算出不能は NULL |
| gate_result | TEXT | L1 ゲート判定（pass/fail/excluded） |
| metrics_json | TEXT | 算出元の指標値。JSON 文字列 |
| scored_at | TEXT DEFAULT (datetime('now')) | スコアリング日時 |

### reviews: review 記録

| カラム | 型 | 説明 |
|---|---|---|
| review_id | TEXT PK | review-YYYYMMDD-NNN 形式のレビュー ID |
| stock_code | TEXT NOT NULL | 銘柄コード |
| reviewed_at | TEXT NOT NULL | レビュー日時（ISO 8601） |
| previous_analyze_id | TEXT NOT NULL FK → analyses | 比較対象の分析 ID |
| changes_detected | INTEGER NOT NULL DEFAULT 0 | 変化検出フラグ（0: なし, 1: あり） |
| impact_a | TEXT NOT NULL DEFAULT 'none' | A 軸への影響（none / minor / reanalyze） |
| impact_b | TEXT NOT NULL DEFAULT 'none' | B 軸への影響（none / minor / reanalyze） |
| impact_c | TEXT NOT NULL DEFAULT 'none' | C 軸への影響（none / minor / reanalyze） |
| impact_d | TEXT NOT NULL DEFAULT 'none' | D 軸への影響（none / minor / reanalyze） |
| impact_e | TEXT NOT NULL DEFAULT 'none' | E 軸への影響（none / minor / reanalyze） |
| reanalyze_recommended | INTEGER NOT NULL DEFAULT 0 | 再分析推奨フラグ（0: 不要, 1: 推奨） |
| time_axis_label | TEXT | 時間軸ラベル（短期シグナル失効 / 中期シナリオ継続 / NULL） |
| fund_watchlist_events_json | TEXT | fund-watchlist で検出したイベントの JSON 配列。未検出は NULL |
| authority_events_json | TEXT | authority-signal で検出したイベントの JSON 配列。未検出は NULL |
| report_path | TEXT | review レポートの相対パス。変化なしの場合 NULL |

### screening_criteria: スクリーニング条件マスタ

| カラム | 型 | 説明 |
|---|---|---|
| criteria_id | TEXT PK | 条件 ID（例: val-ev-ebitda） |
| name | TEXT NOT NULL | 条件名（表示用） |
| indicator | TEXT NOT NULL | 指標名（例: EV/EBITDA） |
| threshold | TEXT NOT NULL | 閾値（例: 10倍以下） |
| direction | TEXT NOT NULL | 条件方向（lte / gte / eq / between） |
| reason | TEXT NOT NULL | 条件の根拠 |
| updated_at | TEXT NOT NULL | 最終更新日時（ISO 8601） |

## ID 生成規則

| 対象 | 形式 | 例 |
|---|---|---|
| scan_id | scan-YYYYMMDD-NNN | scan-20260217-001 |
| analyze_id | analyze-YYYYMMDD-NNN | analyze-20260217-001 |
| batch_id | batch-YYYYMMDD-NNN | batch-20260218-001 |
| review_id | review-YYYYMMDD-NNN | review-20260217-001 |
| criteria_id | 自由文字列 | val-ev-ebitda |

NNN は同日の連番（001, 002, ...）。mbo_db.py が自動採番する。

## インデックス

| インデックス名 | 対象テーブル | カラム | 目的 |
|---|---|---|---|
| idx_scan_results_scan | scan_results | scan_id | scan_id による結果検索 |
| idx_scan_results_code | scan_results | stock_code | 銘柄コードによる結果検索 |
| idx_analyses_code | analyses | stock_code | 銘柄コードによる分析検索 |
| idx_analyses_date | analyses | analyzed_at | 日付順ソート |
| idx_analyses_tier | analyses | tier | ティア別検索 |
| idx_batch_scores_batch | batch_scores | batch_id | バッチ ID による検索 |
| idx_batch_scores_code | batch_scores | stock_code | 銘柄コードによる検索 |
| idx_reviews_code | reviews | stock_code | 銘柄コードによるレビュー検索 |

## スキーマ変更方針

1. テーブルの追加は `init.sql` に `CREATE TABLE IF NOT EXISTS` で追加する
2. カラムの追加は `ALTER TABLE ADD COLUMN` で対応する（既存データとの互換性維持）
3. カラムの削除・型変更は原則行わない（必要な場合はマイグレーションスクリプトを作成）
4. 変更時は本ドキュメントも同時に更新する

## v3 マイグレーション

既存 DB がある場合の v2 → v3 マイグレーション:

```sql
-- scan_results に業種カラム追加
ALTER TABLE scan_results ADD COLUMN tse_industry TEXT;
ALTER TABLE scan_results ADD COLUMN threshold_profile TEXT;

-- analyses に v3 カラム追加
ALTER TABLE analyses ADD COLUMN tse_industry TEXT;
ALTER TABLE analyses ADD COLUMN threshold_profile TEXT;
ALTER TABLE analyses ADD COLUMN business_score REAL;
ALTER TABLE analyses ADD COLUMN control_score REAL;
ALTER TABLE analyses ADD COLUMN control_c1 REAL;
ALTER TABLE analyses ADD COLUMN control_c2_short REAL;
ALTER TABLE analyses ADD COLUMN control_c2_mid REAL;
ALTER TABLE analyses ADD COLUMN deal_score REAL;
ALTER TABLE analyses ADD COLUMN financing_feasibility_json TEXT;
ALTER TABLE analyses ADD COLUMN impediment_score REAL;
ALTER TABLE analyses ADD COLUMN priority_short TEXT;
ALTER TABLE analyses ADD COLUMN priority_mid TEXT;
ALTER TABLE analyses ADD COLUMN authority_signal_json TEXT;
ALTER TABLE analyses ADD COLUMN data_quality_score REAL;
ALTER TABLE reviews ADD COLUMN time_axis_label TEXT;
ALTER TABLE reviews ADD COLUMN fund_watchlist_events_json TEXT;
ALTER TABLE reviews ADD COLUMN authority_events_json TEXT;
ALTER TABLE analyses ADD COLUMN mcs REAL;
ALTER TABLE analyses ADD COLUMN tier TEXT;
ALTER TABLE analyses ADD COLUMN mbo_type TEXT;
ALTER TABLE analyses ADD COLUMN confidence TEXT;

-- analyses の既存カラム名マッピング
-- valuation_score: そのまま（A スコア）
-- feasibility_score: v2 互換。v3 では control_score を使用
-- risk_score: v2 互換。v3 では impediment_score を使用

-- reviews に D/E 軸の影響カラム追加
ALTER TABLE reviews ADD COLUMN impact_d TEXT NOT NULL DEFAULT 'none';
ALTER TABLE reviews ADD COLUMN impact_e TEXT NOT NULL DEFAULT 'none';

-- batch_scores テーブル新設
-- init.sql の CREATE TABLE で対応
```

## depth='スクリーニング' の特殊ルール

batch-score 操作で使用する depth 値。

- valuation_score: 1.0-5.0（業種別閾値で算出）
- business_score: 1.0-5.0 または NULL（CSV に必要データがない場合）
- control_score: NULL（未評価）
- deal_score: NULL（未評価）
- impediment_score: NULL（未評価）
- mcs: NULL（未算出）
- tier: NULL（未判定）
- report_path: `batch-score:{metrics_json}` 形式（レポートファイルなし。代わりに算出元の指標値を JSON で保持）

この行は後続の analyze で上書き（同一 stock_code で新規 INSERT）されることを想定している。
検索時に depth='スクリーニング' を除外する場合は `WHERE depth != 'スクリーニング'` を使用する。
