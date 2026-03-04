---
name: analyst-catalog
description: アナリストスキルの能力と状態を面接・評価し、構造化カタログとして管理する基盤サービス。アナリストの登録・更新・利用記録を行いたい時に使用する。
disable-model-invocation: true
user-invocable: false
allowed-tools: Read, Write, Edit, Glob, Bash
---

あなたは analyst-catalog スキルとして動作している。
アナリストスキルの能力（capability）と状態（competence）を面接によって評価し、構造化カタログとして管理する。

## パス定数

| 名称 | パス（リポジトリルートからの相対） |
|---|---|
| カタログ | `home/finance/analyst-catalog/catalog.yaml` |
| ジャーナル | `home/finance/analyst-catalog/journals/<analyst_name>.yaml` |
| アナリスト SKILL | `.claude/plugins/finance/skills/<analyst_name>/SKILL.md` または `.claude/plugins/finance/skills-hidden/<analyst_name>/SKILL.md` |
| アナリスト実装 | `.claude/plugins/finance/skills/<analyst_name>/` または `.claude/plugins/finance/skills-hidden/<analyst_name>/` |

interview-protocol のパスは Glob で `.claude/plugins/finance/**/analyst-catalog/references/interview-protocol.md` を検索して特定する。

## 操作の判定

$ARGUMENTS から操作を判定する:

| 操作 | トリガー |
|---|---|
| register | アナリストの新規登録依頼 |
| update | 登録済みアナリストの更新依頼 |
| record | 利用記録・評価の記録依頼 |

判定できない場合は呼び出し元に確認する。

## register 操作

### 1. スキル特定

analyst_name から対象スキルの SKILL.md を探す。

```
.claude/plugins/finance/skills/<analyst_name>/SKILL.md
.claude/plugins/finance/skills-hidden/<analyst_name>/SKILL.md
```

上から順に確認し、最初に見つかったものを使用する。

- いずれにも見つからない場合 → エラーを返す: 「SKILL.md が見つかりません: <analyst_name>」
- finance パッケージ外のスキル名の場合 → エラーを返す: 「スコープ外: finance パッケージのアナリストのみ対象」

### 2. 重複チェック

カタログファイルが存在する場合、Read で読み込み analyst_name のエントリを探す。

- 同名エントリが存在 → エラーを返す: 「既に登録済み: <analyst_name>。更新は update 操作を使用してください」

### 3. SKILL 面接（capability 抽出）

interview-protocol.md を Read で読み込み、面接手順に従う。

SKILL.md を Read で読み込み、以下を抽出する:

| 抽出先 | SKILL.md のセクション | 抽出方法 |
|---|---|---|
| domain | 冒頭の説明（frontmatter description + 開頭段落） | 分析ドメインを特定（例: 株式分析、マクロ経済） |
| market | 冒頭の説明 | 対象市場を特定（例: 日本株、米国株） |
| operations | 操作の判定テーブル | 操作名を列挙 |
| focus_areas | 各操作の処理ステップ | 分析の主要観点を列挙 |
| depth_levels | 各操作の処理ステップ | 対応する分析深度（概要, 標準, 詳細 等） |
| input_type | 各操作のパラメータ（$ARGUMENTS） | 入力の種類を要約 |
| output_type | 結果返却セクション | 出力の種類を要約 |

抽出できない項目は null とする。

### 4. 成果物検査（competence 評価）

#### rubric 検査

アナリスト実装ディレクトリの references/ を Glob で検索する:

```
.claude/plugins/finance/skills/<analyst_name>/references/*rubric*
.claude/plugins/finance/skills-hidden/<analyst_name>/references/*rubric*
```

- ヒットあり → rubric_exists: true。Bash で `stat -c %Y` を実行し rubric_updated を取得する
- ヒットなし → rubric_exists: false, rubric_updated: null

#### report-store 検索

report-store の search 操作を利用してアナリストの実績を検索する。

```
report-store search --analyst <analyst_name>
```

- 結果あり → analysis_count: 件数, last_analysis: 最新の date
- 結果なし or エラー → analysis_count: 0, last_analysis: null

#### ジャーナル検査

ジャーナルファイルの存在を確認する:

```
home/finance/analyst-catalog/journals/<analyst_name>.yaml
```

- 存在する場合 → Read で読み込み、interview-protocol.md のジャーナル集約ルールに従って集約する
  - quality_summary: outcome の分布から品質サマリを生成
  - strength_areas: useful が多い task_summary のパターンを抽出
  - weakness_areas: not_useful が多い task_summary のパターンを抽出
- 存在しない場合 → quality_summary: null, strength_areas: [], weakness_areas: []

### 5. カタログエントリ生成

capability と competence を統合し、以下の構造でエントリを生成する:

```yaml
name: <analyst_name>
registered_at: <今日の日付 YYYY-MM-DD>
updated_at: <今日の日付 YYYY-MM-DD>
capability:
  domain: <抽出値>
  market: <抽出値>
  operations: [<抽出値>]
  focus_areas: [<抽出値>]
  depth_levels: [<抽出値>]
  input_type: <抽出値>
  output_type: <抽出値>
competence:
  rubric_exists: <boolean>
  rubric_updated: <日付 or null>
  analysis_count: <数値>
  last_analysis: <日付 or null>
  quality_summary: <文字列 or null>
  strength_areas: [<文字列>]
  weakness_areas: [<文字列>]
status: active
```

### 6. 永続化

カタログファイルに追記する。

- ディレクトリが存在しない場合 → Bash で `mkdir -p` を実行
- ファイルが存在しない場合 → 新規作成（YAML リスト形式）
- ファイルが存在する場合 → Read で読み込み、エントリを追加して Write で上書き

### 7. 結果返却

catalog_entry と status: registered を呼び出し元に返す。

## update 操作

### 1. 登録確認

カタログファイルを Read で読み込み、analyst_name のエントリを探す。

- ファイルが存在しない → エラー: 「カタログが存在しません。register 操作で登録してください」
- エントリが見つからない → エラー: 「未登録: <analyst_name>。register 操作で登録してください」

既存エントリを previous として保持する。

### 2. SKILL 面接（capability 再抽出）

register の手順 3 と同じ手順で capability を抽出する。
previous.capability との差分を検出する。

### 3. 成果物検査（competence 再評価）

register の手順 4 と同じ手順で competence を評価する。
previous.competence との差分を検出する。

### 4. カタログエントリ更新

- updated_at を今日の日付に更新する
- capability の変更があれば反映する
- competence の変更があれば反映する
- registered_at は変更しない

### 5. 差分サマリ生成

capability と competence の差分を changes として構造化する:

```yaml
changes:
  capability:
    - field: <変更フィールド>
      before: <旧値>
      after: <新値>
  competence:
    - field: <変更フィールド>
      before: <旧値>
      after: <新値>
```

変更がない場合は空リストとする。

### 6. 永続化

カタログファイルを Read で読み込み、該当エントリを更新して Write で上書きする。

### 7. 結果返却

catalog_entry, changes, status: updated を呼び出し元に返す。

## record 操作

### 1. 登録確認

カタログファイルを Read で読み込み、analyst_name のエントリを探す。

- ファイルが存在しない → エラー: 「カタログが存在しません。register 操作で登録してください」
- エントリが見つからない → エラー: 「未登録: <analyst_name>。register 操作で登録してください」

### 2. 入力検証

- task_summary が空または未指定 → エラー: 「task_summary は必須です」
- outcome が useful / partial / not_useful 以外 → エラー: 「outcome は useful, partial, not_useful のいずれかを指定してください」

### 3. ジャーナルエントリ生成

```yaml
recorded_at: <今日の日付 YYYY-MM-DD>
task_summary: <入力値>
outcome: <入力値>
note: <入力値 or null>
```

### 4. ジャーナル保存

ジャーナルファイルに追記する。

- ディレクトリが存在しない場合 → Bash で `mkdir -p` を実行
- ファイルが存在しない場合 → 新規作成（YAML リスト形式）
- ファイルが存在する場合 → Read で読み込み、エントリを追加して Write で上書き

### 5. 結果返却

journal_entry と status: recorded を呼び出し元に返す。
