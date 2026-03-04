-- mbo-analyst DB 初期化 SQL v4
-- See references/db-design.md for design rationale

PRAGMA foreign_keys = ON;

-- ============================================================
-- scans: scan 実行記録
-- ============================================================
CREATE TABLE IF NOT EXISTS scans (
    scan_id         TEXT PRIMARY KEY,
    executed_at     TEXT NOT NULL,
    source_info     TEXT NOT NULL,
    total_count     INTEGER NOT NULL,
    pass_count      INTEGER NOT NULL DEFAULT 0,
    fail_count      INTEGER NOT NULL DEFAULT 0,
    uncertain_count INTEGER NOT NULL DEFAULT 0
);

-- ============================================================
-- scan_results: scan 各銘柄の結果
-- ============================================================
CREATE TABLE IF NOT EXISTS scan_results (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id           TEXT NOT NULL REFERENCES scans(scan_id),
    stock_code        TEXT NOT NULL,
    company_name      TEXT,
    tse_industry      TEXT,
    threshold_profile TEXT,
    owner_check       TEXT,
    result            TEXT NOT NULL,
    reason            TEXT NOT NULL,
    ownership_pct     REAL
);

-- ============================================================
-- analyses: analyze 結果（v4: Gate + DualScore）
-- ============================================================
CREATE TABLE IF NOT EXISTS analyses (
    analyze_id             TEXT PRIMARY KEY,
    stock_code             TEXT NOT NULL,
    company_name           TEXT NOT NULL,
    tse_industry           TEXT,
    threshold_profile      TEXT,
    analyzed_at            TEXT NOT NULL,
    depth                  TEXT NOT NULL,
    -- Gate（Stage 1）
    gate_pass              INTEGER NOT NULL DEFAULT 1,   -- 1=通過, 0=除外
    gate_fail_reason       TEXT,                         -- 除外理由（gate_pass=0 時のみ）
    t5_bypass              INTEGER NOT NULL DEFAULT 0,   -- 1=PE検出によりGateをスキップ
    -- 5 軸評価（gate_pass=1 または t5_bypass=1 の場合のみ設定）
    valuation_score        REAL,
    business_score         REAL,
    control_score          REAL,
    control_c1             REAL,
    control_c2             REAL,
    deal_score             REAL,
    impediment_score       REAL,
    mcs                    REAL,
    tier                   TEXT,
    mbo_type               TEXT,
    confidence             TEXT,
    -- P_Score（TOB プレミアム潜在力）
    p_score                REAL,
    p_nav_discount         REAL,
    p_net_cash_ratio       REAL,
    p_hidden_asset_coeff   REAL,
    p_fcf_yield            REAL,
    -- Priority（最優先/通常監視/要確認）
    priority               TEXT,
    -- v2/v3 互換カラム（v4 では非推奨）
    feasibility_score      INTEGER,
    risk_score             INTEGER,
    report_path            TEXT NOT NULL,
    store_id               TEXT
);

-- ============================================================
-- batch_scores: batch-score 一括スコアリング結果（v3 新設）
-- ============================================================
CREATE TABLE IF NOT EXISTS batch_scores (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id          TEXT NOT NULL,
    stock_code        TEXT NOT NULL,
    company_name      TEXT,
    tse_industry      TEXT,
    threshold_profile TEXT,
    valuation_score   REAL,
    business_score    REAL,
    gate_result       TEXT,
    metrics_json      TEXT,
    scored_at         TEXT DEFAULT (datetime('now'))
);

-- ============================================================
-- reviews: review 記録（v3: 5 軸影響評価）
-- ============================================================
CREATE TABLE IF NOT EXISTS reviews (
    review_id            TEXT PRIMARY KEY,
    stock_code           TEXT NOT NULL,
    reviewed_at          TEXT NOT NULL,
    previous_analyze_id  TEXT NOT NULL REFERENCES analyses(analyze_id),
    changes_detected     INTEGER NOT NULL DEFAULT 0,
    impact_a             TEXT NOT NULL DEFAULT 'none',
    impact_b             TEXT NOT NULL DEFAULT 'none',
    impact_c             TEXT NOT NULL DEFAULT 'none',
    impact_d             TEXT NOT NULL DEFAULT 'none',
    impact_e             TEXT NOT NULL DEFAULT 'none',
    reanalyze_recommended INTEGER NOT NULL DEFAULT 0,
    report_path          TEXT
);

-- ============================================================
-- screening_criteria: スクリーニング条件マスタ
-- ============================================================
CREATE TABLE IF NOT EXISTS screening_criteria (
    criteria_id TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    indicator   TEXT NOT NULL,
    threshold   TEXT NOT NULL,
    direction   TEXT NOT NULL,
    reason      TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

-- ============================================================
-- インデックス
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_scan_results_scan  ON scan_results(scan_id);
CREATE INDEX IF NOT EXISTS idx_scan_results_code  ON scan_results(stock_code);
CREATE INDEX IF NOT EXISTS idx_analyses_code      ON analyses(stock_code);
CREATE INDEX IF NOT EXISTS idx_analyses_date      ON analyses(analyzed_at);
CREATE INDEX IF NOT EXISTS idx_analyses_tier      ON analyses(tier);
CREATE INDEX IF NOT EXISTS idx_batch_scores_batch ON batch_scores(batch_id);
CREATE INDEX IF NOT EXISTS idx_batch_scores_code  ON batch_scores(stock_code);
CREATE INDEX IF NOT EXISTS idx_reviews_code       ON reviews(stock_code);
