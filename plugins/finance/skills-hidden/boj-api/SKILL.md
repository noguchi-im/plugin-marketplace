---
name: boj-api
description: 日本銀行 時系列統計データ検索サイトの API を利用して約20万系列の統計データの探索・取得を行う。catalog（機能一覧）、explore（DB内メタデータ探索）、fetch（データ取得）の3操作を提供する。日銀統計データが必要な時に使用する。
disable-model-invocation: false
allowed-tools: Read, Glob, Bash
---

あなたは boj-api スキルとして動作している。
日本銀行 時系列統計データ検索サイトの API を利用して統計データの探索・取得を行う。

## リソースのパス

Glob で検索して特定する:
- scripts/: `.claude/plugins/finance/**/boj-api/scripts/boj_metadata.py`（同ディレクトリに boj_code.py, boj_layer.py, boj_common.py）
- db-catalog.yaml: `.claude/plugins/finance/**/boj-api/references/db-catalog.yaml`

## 初期化

各操作の冒頭で db-catalog.yaml を Read で読み込み、以下を取得する:
- `api.limits`: 制限値
- `databases`: DB 一覧

### 注意事項

- 高頻度アクセスは接続遮断の可能性がある。連続リクエストには間隔をあける
- ページネーションによる自動連続取得は行わない

## 操作の判定

$ARGUMENTS から操作を判定する:

| 操作 | トリガー |
|---|---|
| catalog | 機能一覧、DB 一覧、「何ができるか」 |
| explore | DB 内の系列を調べる、メタデータ取得 |
| fetch | データ取得、系列コード指定、期間指定 |

判定できない場合は呼び出し元に確認する。

## catalog 操作

### 1. DB カタログ読み込み

db-catalog.yaml を Read で読み込む。

### 2. カタログ生成

以下の構造で応答する:

**API の種類**（3種）:
- コード API: 系列コードを指定してデータ取得
- 階層 API: DB の階層構造を辿ってデータ取得
- メタデータ API: DB 内の系列一覧・属性情報を取得

**DB 一覧**: db-catalog.yaml のカテゴリ別に全 DB を表形式で提示する。

**利用例**: 典型的な explore → fetch の流れ:
1. `explore db=CO keyword=業況` で短観の業況判断 DI の系列コードを特定
2. `fetch db=CO code=<特定した系列コード> startDate=202401` でデータ取得

**制限値**: db-catalog.yaml の api.limits の内容。

## explore 操作

### 1. 入力解析

$ARGUMENTS から以下を抽出する:
- db（必須）
- keyword（任意）
- layer, frequency（任意。layer 指定時は frequency も必要）

db が db-catalog.yaml に存在しない場合、エラーを報告して終了する。

### 2. メタデータ取得

boj_metadata.py でメタデータ API を呼び出す:

```bash
python3 <scripts_dir>/boj_metadata.py <DB>
```

JSON 出力から各系列の以下を抽出する:
- SERIES_CODE（系列コード）
- NAME_OF_TIME_SERIES_J（系列名称）
- UNIT_J（単位）
- FREQUENCY（期種）
- CATEGORY_J（カテゴリ）
- LAYER1〜LAYER5（階層情報）
- START_OF_THE_TIME_SERIES（収録開始期）
- END_OF_THE_TIME_SERIES（収録終了期）

### 3. フィルタリング

- keyword 指定時: NAME_OF_TIME_SERIES_J に keyword を含む系列に絞り込む
- layer 指定時: boj_layer.py で階層 API を呼び出して絞り込む:
  ```bash
  python3 <scripts_dir>/boj_layer.py <DB> <FREQ> <LAYER> --format json
  ```
  ※ データは不要でメタ情報のみ必要な場合も階層 API を使う（メタデータ API には階層フィルタがないため）

### 4. 整形・返却

系列リストを表形式で整形して返す。

件数が多い場合（50件超）:
- 先頭20件を表示する
- 「他 N 件。keyword や layer で絞り込み可能」とガイドする

## fetch 操作

### 1. 入力解析

$ARGUMENTS から以下を抽出する:
- db（必須）
- code または layer+frequency（いずれか必須）
- startDate, endDate（任意）
- format（任意。デフォルト: json）

### 2. API 呼び出し

**code 指定時** — boj_code.py:

```bash
python3 <scripts_dir>/boj_code.py <DB> <CODES> [--start <START>] [--end <END>] [--format <FORMAT>]
```

**layer 指定時** — boj_layer.py:

```bash
python3 <scripts_dir>/boj_layer.py <DB> <FREQ> <LAYER> [--start <START>] [--end <END>] [--format <FORMAT>]
```

ページネーション継続時は `--start-position <N>` を追加する。

### 3. レスポンス解析

**正常時**（exit code 0）: stdout の JSON を解析する。

JSON レスポンスの構造:
- `NEXTPOSITION`: null でなければページネーション継続あり
- `DATA_OBJ`: 系列データの配列

各系列から以下を抽出する:
- SERIES_CODE, NAME_OF_TIME_SERIES_J, UNIT_J, FREQUENCY
- SURVEY_DATES と VALUES のペアをデータポイントとして整形

**エラー時**（exit code 1）: stderr のエラー情報を読み取る。
スクリプトが MESSAGEID に基づくガイダンスを含めて出力するため、そのまま呼び出し元に報告する。

### 4. 整形・返却

取得データを以下の形式で返す:

各系列:
- 系列コード、系列名称、単位、期種
- 時期と値の一覧（表形式）

ページネーション情報:
- NEXTPOSITION が null でない場合: 「続きがあります。startPosition=<値> を指定して継続取得できます」と案内
- null の場合: 全データ取得済みと報告

欠損値（null）がある場合はその旨を注記する。
