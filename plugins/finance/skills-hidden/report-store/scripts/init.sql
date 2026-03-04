-- report-store DB schema
-- See references/db-design.md for design rationale

PRAGMA foreign_keys = ON;

-- ============================================================
-- provenances: 出自マスタ
-- ============================================================
CREATE TABLE IF NOT EXISTS provenances (
    id          TEXT PRIMARY KEY,
    description TEXT NOT NULL
);

-- ============================================================
-- domains: 分析ドメインマスタ
-- ============================================================
CREATE TABLE IF NOT EXISTS domains (
    id          TEXT PRIMARY KEY,
    description TEXT NOT NULL
);

-- ============================================================
-- reports: レポートメタデータ
-- ============================================================
CREATE TABLE IF NOT EXISTS reports (
    id                TEXT PRIMARY KEY,        -- rpt-YYYYMMDD-NNN
    provenance_id     TEXT NOT NULL REFERENCES provenances(id),
    domain_id         TEXT NOT NULL REFERENCES domains(id),
    subject           TEXT NOT NULL,           -- 分析対象
    date              TEXT NOT NULL,           -- YYYY-MM-DD
    incomplete        INTEGER NOT NULL DEFAULT 0,
    analyst           TEXT,                    -- 生成元スキル名 or "user"
    updates           TEXT REFERENCES reports(id),
    file_path         TEXT NOT NULL,           -- Markdown の相対パス
    quality_score     INTEGER,                -- 1-5
    usefulness_score  INTEGER,                -- 1-5
    reliability_score INTEGER,                -- 1-5
    created_at        TEXT NOT NULL            -- ISO 8601
);

-- ============================================================
-- tag_categories: タグカテゴリ（分類の軸）
-- ============================================================
CREATE TABLE IF NOT EXISTS tag_categories (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    description  TEXT,
    multi_select INTEGER NOT NULL DEFAULT 1,   -- 0: 単一選択  1: 複数選択
    required     INTEGER NOT NULL DEFAULT 0    -- 1: レポートに必須
);

-- ============================================================
-- tags: タグ語彙
-- ============================================================
CREATE TABLE IF NOT EXISTS tags (
    name        TEXT PRIMARY KEY,
    category_id TEXT NOT NULL REFERENCES tag_categories(id),
    description TEXT,
    created_at  TEXT NOT NULL
);

-- ============================================================
-- report_tags: レポート ↔ タグ
-- ============================================================
CREATE TABLE IF NOT EXISTS report_tags (
    report_id TEXT NOT NULL REFERENCES reports(id),
    tag_name  TEXT NOT NULL REFERENCES tags(name),
    PRIMARY KEY (report_id, tag_name)
);

-- ============================================================
-- report_sources: レポートが依拠した情報ソース
-- ============================================================
CREATE TABLE IF NOT EXISTS report_sources (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id    TEXT NOT NULL REFERENCES reports(id),
    source_name  TEXT NOT NULL,
    source_url   TEXT,
    source_tier  INTEGER,                     -- 1: 公的/一次  2: 公式集計  3: 二次メディア
    as_of        TEXT,                        -- データ時点
    retrieved_at TEXT,                        -- 取得日時
    score        INTEGER                      -- 1-5
);

-- ============================================================
-- report_relations: レポート間の関連
-- ============================================================
CREATE TABLE IF NOT EXISTS report_relations (
    report_id     TEXT NOT NULL REFERENCES reports(id),
    related_id    TEXT NOT NULL REFERENCES reports(id),
    relation_type TEXT NOT NULL,              -- reference | used_input
    PRIMARY KEY (report_id, related_id, relation_type)
);

-- ============================================================
-- インデックス
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_reports_domain     ON reports(domain_id);
CREATE INDEX IF NOT EXISTS idx_reports_subject    ON reports(subject);
CREATE INDEX IF NOT EXISTS idx_reports_date       ON reports(date);
CREATE INDEX IF NOT EXISTS idx_reports_provenance ON reports(provenance_id);
CREATE INDEX IF NOT EXISTS idx_reports_analyst    ON reports(analyst);
CREATE INDEX IF NOT EXISTS idx_report_tags_tag    ON report_tags(tag_name);
CREATE INDEX IF NOT EXISTS idx_report_sources_rpt ON report_sources(report_id);
CREATE INDEX IF NOT EXISTS idx_report_relations   ON report_relations(report_id);

-- ============================================================
-- 初期データ: マスタ
-- ============================================================
INSERT OR IGNORE INTO provenances VALUES
    ('internal/analyst',       'Analyst スキルによる分析結果'),
    ('internal/collector',     'Collector スキルによる収集データ'),
    ('internal/judgment',      'investment-thesis による判断材料'),
    ('external/human-curated', '命令者が提出した外部資料'),
    ('internal/decision',      '命令者の判断記録');

INSERT OR IGNORE INTO domains VALUES
    ('equity',    '個別株式・企業'),
    ('macro',     'マクロ経済'),
    ('sector',    'セクター・業種'),
    ('product',   '投資商品'),
    ('portfolio', 'ポートフォリオ');

INSERT OR IGNORE INTO tag_categories VALUES
    ('content_type', 'コンテンツ性質', 'レポート内容の性質を示すキーワード', 1, 0),
    ('aspect',       '分析観点',       'レポートが扱う分析の切り口',         1, 0);

INSERT OR IGNORE INTO tags (name, category_id, description, created_at) VALUES
    ('factual',       'content_type', '事実・データ中心の内容',    datetime('now')),
    ('interpretive',  'content_type', '解釈・仮説を含む内容',     datetime('now')),
    ('speculative',   'content_type', '推測的な内容',             datetime('now')),
    ('opinion-based', 'content_type', '意見・判断を含む内容',     datetime('now'));
