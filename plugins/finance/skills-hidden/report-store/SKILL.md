---
name: report-store
description: レポート成果物のメタデータ付き保存・タグ付け・検索・取得を行う基盤サービス。レポートの保存・検索・取得・スコア更新を行いたい時に使用する。
disable-model-invocation: true
user-invocable: false
allowed-tools: Read, Write, Glob, Bash
---

あなたは report-store スキルとして動作している。
レポート成果物をメタデータ付きで保存・タグ付け・検索・取得する。

## パス定数

| 名称 | パス（リポジトリルートからの相対） |
|---|---|
| DB | `home/finance/report-store/index/report-index.db` |
| レポート保存先 | `home/finance/report-store/reports/YYYY/` |

スクリプトのパスは Glob で `.claude/plugins/finance/**/report-store/scripts/report_db.py` を検索して特定する。

## 操作の判定

$ARGUMENTS から操作を判定する:

| 操作 | トリガー |
|---|---|
| save | レポートの保存依頼 |
| search | レポートの検索依頼 |
| retrieve | 特定レポートの取得依頼（ID 指定） |
| score | スコアの更新依頼 |

判定できない場合は呼び出し元に確認する。

## DB 初期化

各操作の冒頭で DB ファイルの存在を確認する（Bash: `test -f`）。

- **save / score**: DB が存在しなければ `report_db.py init` を実行する
- **search / retrieve**: DB が存在しなければ空の結果を返して終了する

```bash
python3 <script_path>/report_db.py init \
    --init-sql <script_path>/init.sql
```

## save 操作

### 1. 入力の整理

$ARGUMENTS から以下を抽出する:

- レポート本文（Markdown テキスト）
- 必須: provenance_id, domain_id, subject, date
- 任意: analyst, incomplete, updates, tags, sources, relations

### 2. ID 生成

```bash
python3 <script_path>/report_db.py generate-id --date <date>
```

返却された ID（例: `rpt-20260210-001`）を以降で使用する。

### 3. Markdown ファイル保存

保存先: `home/finance/report-store/reports/YYYY/rpt-YYYYMMDD-NNN.md`

- Bash で `mkdir -p` してディレクトリを確保する
- Write ツールでレポート本文を保存する

### 4. DB 保存

ID、メタデータ、file_path を JSON にまとめて stdin から渡す:

```bash
echo '<json>' | python3 <script_path>/report_db.py save
```

JSON 構造:

```json
{
    "id": "rpt-YYYYMMDD-NNN",
    "provenance_id": "...",
    "domain_id": "...",
    "subject": "...",
    "date": "YYYY-MM-DD",
    "file_path": "home/finance/report-store/reports/YYYY/rpt-YYYYMMDD-NNN.md",
    "analyst": "...",
    "incomplete": 0,
    "updates": null,
    "tags": ["factual"],
    "sources": [{"source_name": "...", "source_url": "...", "source_tier": 1, "as_of": "...", "retrieved_at": "...", "score": null}],
    "relations": [{"related_id": "...", "relation_type": "reference"}]
}
```

バリデーション・トランザクション・reliability_score 算出はスクリプトが処理する。
エラー時はスクリプトが JSON エラーを返す。その内容を呼び出し元に伝えて中断する。

### 5. タグ付け判定

呼び出し元が tags を指定していない場合のみ:

1. `references/tag-rubric.md` を Read で読み込む
2. レポート本文に基づいて content_type タグを判定する
3. 判定したタグを追加で save する（再度 `report_db.py save` は使わず、直接 Python で INSERT する）

呼び出し元がタグを指定済みの場合はスキップする。

### 6. 結果を返す

save の出力（ID + file_path）を呼び出し元に返す。

## search 操作

```bash
python3 <script_path>/report_db.py search \
    --domain-id <domain> \
    --subject <subject> \
    --tag-name <tag> \
    --date-from <from> \
    --date-to <to> \
    --keyword <keyword> \
    --analyst <analyst> \
    --provenance-id <provenance> \
    --incomplete <0|1>
```

条件は $ARGUMENTS で指定されたもののみ渡す。
結果の JSON を整形して呼び出し元に返す。0 件の場合は「該当するレポートはありません」と返す。

## retrieve 操作

### 1. メタデータ取得

```bash
python3 <script_path>/report_db.py retrieve --id <report_id>
```

エラー時はエラーメッセージを返す。

### 2. Markdown 読み込み

返却された `file_path` を Read ツールで読み込む。
ファイルが存在しない場合は「DB とファイルの不整合: {file_path} が見つかりません」と報告する。

### 3. 結果を返す

メタデータ全項目と Markdown 本文を呼び出し元に返す。

## score 操作

```bash
python3 <script_path>/report_db.py score \
    --id <report_id> \
    --quality-score <1-5> \
    --usefulness-score <1-5> \
    --reliability-score <1-5>
```

指定されたスコアのみ渡す。結果を呼び出し元に返す。
