# report-store DB 設計書

## 目次

1. [構成方針](#構成方針)
2. [テーブル設計](#テーブル設計)
3. [スコア運用ルール](#スコア運用ルール)
4. [マスタデータ管理](#マスタデータ管理)
5. [スキーマ変更方針](#スキーマ変更方針)

---

## 構成方針

### ハイブリッド構成（Markdown + SQLite）

| データ | 格納先 | 理由 |
|---|---|---|
| レポート本文 | Markdown ファイル | 人が読める、Git diff で変更追跡可能 |
| メタデータ・インデックス | SQLite | 検索が効率的、スキーマが明確 |

レポート本文は `home/finance/report-store/reports/YYYY/rpt-YYYYMMDD-NNN.md` に保存する。
SQLite DB は `home/finance/report-store/index/report-index.db` に配置する。

### ID 体系

- 形式: `rpt-YYYYMMDD-NNN`（NNN は同日内の連番、ゼロ埋め 3 桁）
- 一意性: date + 連番で保証
- 生成: `report_db.py generate-id` が DB を参照して次の番号を返す

---

## テーブル設計

### provenances（出自マスタ）

| カラム | 型 | 説明 |
|---|---|---|
| id | TEXT PK | 出自識別子（例: internal/analyst） |
| description | TEXT NOT NULL | 説明 |

### domains（分析ドメインマスタ）

| カラム | 型 | 説明 |
|---|---|---|
| id | TEXT PK | ドメイン識別子（例: equity） |
| description | TEXT NOT NULL | 説明 |

### reports（レポートメタデータ）

| カラム | 型 | 説明 |
|---|---|---|
| id | TEXT PK | rpt-YYYYMMDD-NNN |
| provenance_id | TEXT NOT NULL FK | 出自 → provenances.id |
| domain_id | TEXT NOT NULL FK | ドメイン → domains.id |
| subject | TEXT NOT NULL | 分析対象（例: "トヨタ自動車"） |
| date | TEXT NOT NULL | レポート日付 YYYY-MM-DD |
| incomplete | INTEGER NOT NULL DEFAULT 0 | 1 = 暫定レポート |
| analyst | TEXT | 生成元スキル名 or "user" |
| updates | TEXT FK | 更新元レポート ID → reports.id |
| file_path | TEXT NOT NULL | Markdown の相対パス |
| quality_score | INTEGER | 1-5: 分析の深さ・根拠の充実度 |
| usefulness_score | INTEGER | 1-5: 命令者にとっての価値 |
| reliability_score | INTEGER | 1-5: ソースの質・鮮度 |
| created_at | TEXT NOT NULL | ISO 8601 作成日時 |

### tag_categories（タグカテゴリ）

| カラム | 型 | 説明 |
|---|---|---|
| id | TEXT PK | カテゴリ識別子 |
| name | TEXT NOT NULL | 表示名 |
| description | TEXT | 説明 |
| multi_select | INTEGER NOT NULL DEFAULT 1 | 0: 単一選択 1: 複数選択 |
| required | INTEGER NOT NULL DEFAULT 0 | 1: レポートに必須 |

### tags（タグ語彙）

| カラム | 型 | 説明 |
|---|---|---|
| name | TEXT PK | タグ名 |
| category_id | TEXT NOT NULL FK | カテゴリ → tag_categories.id |
| description | TEXT | 説明 |
| created_at | TEXT NOT NULL | 登録日時 |

### report_tags（レポート ↔ タグ）

| カラム | 型 | 説明 |
|---|---|---|
| report_id | TEXT NOT NULL FK | → reports.id |
| tag_name | TEXT NOT NULL FK | → tags.name |

複合 PK: (report_id, tag_name)

### report_sources（情報ソース）

| カラム | 型 | 説明 |
|---|---|---|
| id | INTEGER PK AUTO | 連番 |
| report_id | TEXT NOT NULL FK | → reports.id |
| source_name | TEXT NOT NULL | ソース名 |
| source_url | TEXT | URL |
| source_tier | INTEGER | 1: 公的/一次 2: 公式集計 3: 二次メディア |
| as_of | TEXT | データ時点 |
| retrieved_at | TEXT | 取得日時 |
| score | INTEGER | 1-5: 個別ソースの信頼度・有用度 |

### report_relations（レポート間関連）

| カラム | 型 | 説明 |
|---|---|---|
| report_id | TEXT NOT NULL FK | → reports.id |
| related_id | TEXT NOT NULL FK | → reports.id |
| relation_type | TEXT NOT NULL | reference / used_input |

複合 PK: (report_id, related_id, relation_type)

- **reference**: 作成時に参照した他レポート
- **used_input**: 統合時に素材として使用した他レポート

---

## スコア運用ルール

| スコア | 付与者 | タイミング | 更新 |
|---|---|---|---|
| quality_score | report-store（タグ付け時） or 命令者 | save 時 or 後から | 命令者が `score` 操作で更新可能 |
| usefulness_score | 命令者 | レポート利用後 | 命令者が `score` 操作で更新 |
| reliability_score | report_db.py（自動算出） | save 時 | ソース情報の変更時に再計算。命令者が手動で上書きも可能 |

### reliability_score 算出ルール

source_tier から機械的に導出する:

| source_tier | スコア |
|---|---|
| 1（公的/一次） | 5 |
| 2（公式集計） | 3 |
| 3（二次メディア） | 1 |

全ソースの平均を四捨五入。ソースがない場合は NULL。

---

## マスタデータ管理

### 追加手順

1. init.sql にレコードを追加する
2. 既存 DB に対しては `INSERT OR IGNORE` で手動適用する
3. db-design.md のテーブル説明を更新する

### 廃止手順

1. 該当レコードを使用しているレポートがないことを確認する
2. init.sql から削除する（既存 DB からは物理削除しない、新規 DB のみ反映）
3. db-design.md を更新する

### 初期マスタデータ

**provenances**: internal/analyst, internal/collector, internal/judgment, external/human-curated, internal/decision

**domains**: equity, macro, sector, product, portfolio

**tag_categories**: content_type, aspect

**tags（content_type）**: factual, interpretive, speculative, opinion-based

---

## スキーマ変更方針

### ALTER TABLE で対応する範囲

- カラムの追加（NULL 許容 or DEFAULT 付き）
- インデックスの追加・削除
- 新テーブルの追加

### ALTER TABLE で対応できない場合

- カラムの型変更、リネーム、削除
- これらが必要になった場合はマイグレーションスクリプトを作成する
- マイグレーション前に必ずバックアップを取る

### 手順

1. init.sql を更新する（新規 DB 用）
2. 既存 DB 用の ALTER 文を作成・実行する
3. db-design.md を更新する
4. 変更内容を changelog に記録する
