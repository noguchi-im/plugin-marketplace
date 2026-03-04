# plugin-marketplace vs Anthropic skill-creator: 厳密比較と改善提案

## 1. 比較対象の概要

| 項目 | plugin-marketplace (本リポジトリ) | Anthropic skill-creator |
|---|---|---|
| **目的** | ドメイン特化スキル群の運用基盤（金融分析・文書処理） | スキルそのものの作成・テスト・改善を行うメタスキル |
| **性格** | プロダクション運用システム | 開発・品質管理ツールキット |
| **スキル数** | 15スキル（4公開+7隠蔽+4文書系） | 1スキル（skill-creator自体） |

---

## 2. 本リポジトリが優れている点

### 2-1. 多層エージェントアーキテクチャ

skill-creatorは単一スキルの作成ループを対象としているが、本リポジトリは3層のエージェント階層を実現している:

- **Layer 1** (User-facing): `finance-advisor` がルーター兼オーケストレーター
- **Layer 2** (Hidden specialists): `sector-analyst`, `macro-theme-analyst`, `mbo-analyst`
- **Layer 3** (Infrastructure): `report-store`, `report-collector`, `analyst-catalog`

skill-creatorにはこの種のマルチエージェント協調設計のパターンは存在しない。

### 2-2. 永続的学習メモリシステム

本リポジトリの各スキルは自律的に学習データを蓄積する:

- **report-collector**: SQLiteジャーナルに検索パターンの成否を記録し、将来の`collect`で`find-patterns`を先行呼出し
- **analyst-catalog**: 各アナリストの使用履歴（useful/partial/not_useful）を蓄積し、`strength_areas`/`weakness_areas`を形成
- **events.jsonl**: 各アナリストが全操作を構造化ログとして記録（バイアス検出にも使用）
- **macro-theme-analyst**: 過去の確率推定の偏りを`validate`で検出し、次回の`evaluate`で自己補正

skill-creatorのフィードバックループは`feedback.json`による人間レビューの一方通行であり、スキル自身が過去の実行から自動的に学習する仕組みは持たない。

### 2-3. 予算制御システム

APIコスト管理の仕組みが明示的に設計されている:

- `search_budget`による WebSearch/WebFetch 呼出し数上限
- 深度別バジェットティア（overview: 3-8, standard: 10-20, detailed: 15-40）
- research フローでは常にユーザー確認を要求
- MCP呼出しはバジェット対象外（コスト差を反映）

skill-creatorにはトークン消費の計測はあるが、実行中のコスト制御メカニズムはない。

### 2-4. モデル選択ポリシー

MBO analyst等では処理カテゴリ別にモデルを明示指定:

| 処理 | モデル | 理由 |
|---|---|---|
| WebFetch データ取得 | sonnet | I/Oバウンド |
| バッチスコアリング | haiku | 定型処理 |
| 5軸詳細分析 | sonnet | 判断が必要 |

skill-creatorでは `--model` フラグでセッション全体のモデルを指定するのみ。タスク粒度でのモデル最適化の概念がない。

### 2-5. ドメイン固有の精緻な評価体系

スキルごとに定量的スコアリング基準が参照ファイルとして定義されている:

- **stock-analyst**: 3軸（financial_health, growth_potential, valuation_attractiveness）
- **reit-analyst**: 5軸＋物件タイプ別ウェイト調整
- **mbo-analyst**: Gate + DualScore構造、5軸(A/B/C/D/E) + MCS + Tier + P_Score + Priority、業種プロファイル(α/β/γ/δ/ε)

skill-creatorの評価は汎用的な assertion ベースであり、このレベルのドメイン特化スコアリングは想定外。

### 2-6. プログレッシブ・ディスクロージャの実践

`skills-hidden.yaml` による隠蔽スキル管理、`references/` による段階的ロード、`scripts/` による決定論的処理の分離が一貫して実装されている。skill-creatorが推奨する3層ローディングシステム（Metadata → SKILL.md body → Bundled resources）を、本リポジトリは実際のプロダクションで具現化している。

---

## 3. 本リポジトリが劣っている点

### 3-1. テスト・評価フレームワークの完全な欠如 (致命的)

skill-creatorの最大の強みであり、本リポジトリに最も欠けている要素。

skill-creatorが提供するもの:
- `evals/evals.json` によるテストプロンプト定義
- with-skill vs without-skill/old-skill の並行ベースライン実行
- `eval_metadata.json` + `assertions` による定量評価
- `grading.json`（text/passed/evidence）による機械的採点
- `benchmark.json` による pass_rate/duration/tokens の定量比較
- `eval-viewer/generate_review.py` によるHTML可視化レビュー
- `feedback.json` による構造化フィードバック収集
- iteration-1, iteration-2... によるバージョン間比較
- blind comparison（比較者エージェント）による公平な品質判定
- `scripts.aggregate_benchmark` によるmean±stddev集計

本リポジトリには上記のいずれも存在しない。スキルの品質は `quality_score`（アナリスト自身による自己採点）と `usefulness_score`（ユーザーの事後評価）のみで、スキル定義（SKILL.md）自体の品質をテストする仕組みがない。

### 3-2. スキル記述の最適化プロセスの欠如

skill-creatorは description フィールドのトリガリング精度を最適化する専用ワークフローを持つ:
- 20個のshould-trigger/should-not-triggerクエリ生成
- HTML UIによるユーザーレビュー
- `scripts.run_loop` による自動最適化（最大5イテレーション）
- false positive/false negative の定量計測

本リポジトリの description は静的に手書きされており、トリガリング精度の検証手段がない。

### 3-3. スキル作成プロセスの体系化の欠如

skill-creatorには明確な段階的ワークフローがある:

```
Capture Intent → Interview/Research → Write SKILL.md → Test Cases →
Run + Baseline → Draft Assertions → Grade → Benchmark →
User Review → Improve → Iterate → Description Optimization
```

本リポジトリにはスキルの作成手順を体系化したものがない。`CONTRIBUTING.md` はディレクトリ構造と `plugin.json` の記法のみ。

### 3-4. ベースライン比較の概念の欠如

skill-creatorは常に「スキルあり vs スキルなし」または「新版 vs 旧版」の比較を行う。本リポジトリにはこの比較思考が完全に欠落している。

### 3-5. ユーザーコミュニケーション品質への配慮

skill-creatorは技術リテラシーの幅広いユーザーを想定し、用語説明のガイドラインを設けている。本リポジトリのスキルは全て日本語の専門用語で書かれ、非専門家への配慮が限定的。

### 3-6. 「WHY」の説明不足

skill-creatorの設計原則: 「ALWAYS/NEVERの大文字命令ではなく、理由を説明せよ」。本リポジトリのスキルは指示型寄りで、ルールの根拠説明が薄い箇所がある。

### 3-7. CI/CDとの統合

`.github/workflows/sync-plugins.yml` はプラグインの同期のみで、スキル品質のCI検証は行っていない。

---

## 4. 改善提案

### 提案1: eval フレームワークの導入 (優先度: 最高)

各スキルに最低3つのテストプロンプトを定義し、以下を自動化する:
- 回帰テスト: モデル更新時にスコアリング結果が変化しないか検証
- ベースライン比較: スキルありvsスキルなしで品質差を定量化
- assertion自動採点: スコアリング結果の数値範囲、必須セクションの存在、参照ソース数等

### 提案2: skill-operator (core:skill-operator) の実装

AGENTS.mdで参照されている未実装の `core:skill-operator` を、Anthropic skill-creatorのフレームワークを参考に実装する。

### 提案3: スコアリング閾値の根拠文書化

各 `scoring-rubric.md` に閾値の根拠セクションを追加する。

### 提案4: description トリガリング検証の導入

各スキルの `description` フィールドに対し、should-trigger/should-not-trigger のテストセットを作成する。

### 提案5: イテレーション管理の仕組み

skill-creatorの `iteration-N/` パターンを導入し、スキル改善の追跡を可能にする。

### 提案6: 品質メトリクスの自動集計とCIゲート

PRマージ前にスキル品質の回帰がないことを自動検証する仕組みを追加する。

### 提案7: 学習ループとスキル改善ループの接続

report-collector/analyst-catalog のジャーナルデータをスキル定義自体の改善にも接続する。

### 提案8: blind comparison の導入

重要なスキル改善の際に、独立したgraderエージェントによる公平な品質判定を行う。

---

## 5. 総合評価

| 観点 | plugin-marketplace | skill-creator | 判定 |
|---|---|---|---|
| アーキテクチャの洗練度 | 多層エージェント協調 | 単一スキルのループ | 本リポジトリ優位 |
| 永続学習メカニズム | SQLite+JSONL自動蓄積 | なし | 本リポジトリ優位 |
| コスト制御 | バジェットティア制度 | トークン計測のみ | 本リポジトリ優位 |
| ドメイン知識の深度 | 極めて精緻 | 汎用（深度なし） | 本リポジトリ優位 |
| テスト・品質保証 | なし | 包括的フレームワーク | skill-creator優位 |
| ベースライン比較 | なし | with/without比較必須 | skill-creator優位 |
| スキル作成ガイド | 形式のみ | 包括的ワークフロー | skill-creator優位 |
| description最適化 | なし | 自動化ループ | skill-creator優位 |
| イテレーション管理 | なし | iteration-N構造 | skill-creator優位 |
| CI/CD統合 | sync のみ | ベンチマーク+ダッシュボード | skill-creator優位 |
| WHYの説明 | 部分的 | 設計原則として徹底 | skill-creator優位 |

**結論**: 本リポジトリはプロダクション運用の実装力で優位だが、スキルの品質を検証・改善する「メタプロセス」が完全に欠如している。skill-creatorの test-measure-refine ループを内部化することが、最も投資対効果の高い改善となる。
