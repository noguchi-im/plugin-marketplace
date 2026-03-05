# stock-analyst 評価基準

本ファイルは `stock-analyst` スキルの動作を検証するためのチェックリストです。
SPEC の受け入れ基準を、ユーザが観察可能な入出力の振る舞いとして記述しています。

---

## analyze 正常系

- [ ] Given 企業名の分析依頼（「トヨタを分析して」）が渡された時
      When analyze を実行する
      Then 企業を特定し、財務・株価・開示データを収集し、ファンダメンタルズ・バリュエーション・定性分析を含むレポートを生成し、保存 ID（store_id）が発行される

- [ ] Given 銘柄コードの分析依頼（「7203 を分析して」）が渡された時
      When analyze を実行する
      Then 銘柄コードから企業を特定し、分析レポートを生成する

- [ ] Given focus: バリュエーション が指定された時
      When analyze を実行する
      Then バリュエーション分析を重点的に深掘りしたレポートを生成する

- [ ] Given depth: 概要 が指定された時
      When analyze を実行する
      Then 直近決算と現在株価のみを収集し、簡潔なサマリレポートを生成する

- [ ] Given depth: 詳細 が指定された時
      When analyze を実行する
      Then 過去 5 期分の財務 + 競合比較を含む詳細な分析レポートを生成する

## スコープ外

- [ ] Given 個別企業でない分析依頼（「米国経済を分析して」）が渡された時
      When analyze を実行する
      Then スコープ外であることを報告して終了する

## スコアリングとレーティング

- [ ] Given 分析レポートが生成された時
      When スコアリングを実行する
      Then 評価基準に従い financial_health / growth_potential / valuation_attractiveness の 3 軸評価が付与され、各軸に根拠が付記される

- [ ] Given 3 軸スコアが付与された時
      When 投資レーティングを決定する
      Then 3 軸を総合し strong buy / buy / neutral / sell / strong sell のいずれかが付与され、根拠が 1-2 文で記述される

- [ ] Given 分析レポートが保存された時
      When 保存が完了する
      Then 分析品質スコアが付与される

## レポート保存

- [ ] Given 分析レポートが生成された時
      When 保存を実行する
      Then レポートが株式ドメイン（stock-analyst）のメタデータで保存される

- [ ] Given 収集結果の追跡 ID がある時
      When 保存を実行する
      Then 収集結果の ID が「分析に使用した入力」として関連付けて記録される

- [ ] Given 保存サービスが利用不可の時
      When analyze を実行する
      Then 保存をスキップし、分析レポートを直接返却する（store_id: null）

## データ収集フィードバック

- [ ] Given 収集結果の財務データが古かった時
      When フィードバックを評価する
      Then ソース品質（source-quality）タイプのフィードバックが記録される

- [ ] Given 企業分析に必要だが収集されなかったデータカテゴリがある時
      When フィードバックを評価する
      Then パターン不足（pattern-gap）タイプのフィードバックが記録される

- [ ] Given 収集品質に問題がない時
      When フィードバックを評価する
      Then フィードバックは記録されない

## 3シナリオ適正株価レンジ

- [ ] Given depth: 標準 以上でバリュエーション分析を実行する時
      When 適正株価レンジを推定する
      Then 成長率・マルチプル・主要ドライバーの前提を変動させた Bear/Base/Bull の 3 シナリオ適正株価レンジが提示され、各シナリオの前提が明示される

- [ ] Given depth: 概要 でバリュエーション分析を実行する時
      When 適正株価レンジを推定する
      Then 3シナリオ分析はスキップされ、valuation_scenarios は null となる

- [ ] Given 3シナリオの前提データが不足している時
      When 適正株価レンジを推定する
      Then 利用可能なデータのみでシナリオを構成し、固定した前提とその理由をレポートに明記する

## 収集範囲制御

- [ ] Given depth: 標準 で分析依頼された時
      When 収集を実行する
      Then 標準モードの収集範囲（全 7 トピック、最大 15 回検索）でデータが収集される

- [ ] Given depth: 概要 で分析依頼された時
      When 収集を実行する
      Then 概要モードの収集範囲（決算・株価の 2 トピック、最大 5 回検索）でデータが収集される

- [ ] Given depth: 詳細 で分析依頼された時
      When 収集を実行する
      Then 詳細モードの収集範囲（拡張トピック、最大 30 回検索）でデータが収集される

## 収集結果の不足

- [ ] Given 財務諸表が取得できなかった時
      When 収集結果を確認する
      Then ファンダメンタルズ分析が制限される旨を報告し、続行するか確認する

- [ ] Given データ収集でエラーが発生した時
      When 収集依頼が失敗する
      Then 利用可能な情報のみで分析を続行し、レポートに制約を明記する

## review

- [ ] Given 存在する store_id と concern が渡された時
      When review を実行する
      Then 元レポートを取得し、concern に基づいて再分析し、更新レポートを生成し、元レポートとの関連付けで保存する

- [ ] Given review で追加データが必要な時
      When review を実行する
      Then 追加データを収集し、新データを含めて再分析する

- [ ] Given 存在しない store_id が渡された時
      When review を実行する
      Then エラーを返す

- [ ] Given 株式ドメイン以外のレポートの store_id が渡された時
      When review を実行する
      Then スコープ外であることを報告して終了する

## earnings-update 正常系

- [ ] Given 銘柄と決算情報が渡された時（「トヨタの3Q決算が出た」）
      When earnings-update を実行する
      Then 決算データを収集し、beat/miss を定量化し、スコアリングを再評価し、テーゼ影響を評価したレポートを生成して保存する

- [ ] Given existing_store_id が指定された時
      When earnings-update を実行する
      Then 元レポートを取得し、差分更新モードで決算アップデートレポートを生成し、元レポートへの参照付きで保存する

- [ ] Given 既存レポートが見つからない時
      When earnings-update を実行する
      Then 簡易分析モードで決算フォーカスの分析レポートを生成する

## earnings-preview 正常系

- [ ] Given 銘柄と決算時期が渡された時（「NVDAの来週の決算に備えて」）
      When earnings-preview を実行する
      Then コンセンサス予想を整理し、bull/base/bear 3シナリオと注目カタリストを含むプレビューレポートを生成して保存する

- [ ] Given セクター固有 KPI のデータが取得できた時
      When earnings-preview を実行する
      Then セクター固有 KPI の市場予想がコンセンサス予想に含まれる

## earnings 収集範囲制御

- [ ] Given earnings-update が実行される時
      When 収集を実行する
      Then 決算特化モードの収集範囲（決算短信・業績修正・コンセンサス・説明会、最大 8 回検索）でデータが収集される

- [ ] Given earnings-preview が実行される時
      When 収集を実行する
      Then プレビュー特化モードの収集範囲（コンセンサス予想・過去パターン・セクター動向・カタリスト、最大 10 回検索）でデータが収集される
