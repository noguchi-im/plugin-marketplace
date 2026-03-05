# macro-theme-analyst 評価基準

本ファイルは `macro-theme-analyst` スキルの動作を検証するためのチェックリストです。
SPEC の受け入れ基準を、ユーザが観察可能な入出力の振る舞いとして記述しています。

---

## evaluate 正常系

- [ ] Given テーマの分析依頼（「AI半導体サプライチェーンを評価して」）が渡された時
      When evaluate を実行する
      Then テーゼを言語化し、前提に確率レンジを付与し、支持・反証の両方を収集し、条件付き未来の確率分布を構築し、自己批判（self_critique）を含むレポートを生成し、保存 ID（report_id）が発行される

- [ ] Given depth: overview が指定された時
      When evaluate を実行する
      Then 概要モードの収集範囲（最大 8 回検索）で主要前提のみを検証し、簡潔な確率分布を構築する

- [ ] Given depth: detailed が指定された時
      When evaluate を実行する
      Then 詳細モードの収集範囲（最大 40 回検索）で広範にデータを収集し、サブテーマ個別分析を含む詳細な確率分布を構築する

- [ ] Given sub_themes が指定された時
      When evaluate を実行する
      Then 各サブテーマのライフサイクルステージを判定し、個別にテーゼ要約と確率レンジを付与する

## evaluate の分析品質

- [ ] Given テーゼが構築された時
      When データ収集・懐疑的検証を実行する
      Then 各前提に supporting_evidence と contradicting_evidence の両方が収集される

- [ ] Given データが不足する前提がある時
      When 不確実性を構造化する
      Then 既知の未知（unknowns）に記載し、ベースレート・類推・制約から蓋然性を推定し、テーゼへの影響度を明示する

- [ ] Given 確率分布を構築した時
      When 自己懐疑を実行する
      Then self_critique に「最も間違っている可能性が高い部分」「反対ポジションの合理的根拠」「見落とし（blind_spots）」が記載される

- [ ] Given 分析中に新しいシグナルチェーンを構築した時
      When 分析が完了する
      Then シグナルチェーン一覧に「仮説（hypothesis）」ステータスで追記される

## スコープ外

- [ ] Given 投資テーマでない分析依頼（「トヨタを分析して」）が渡された時
      When evaluate を実行する
      Then スコープ外であることを報告して終了する

## review/update

- [ ] Given 存在する report_id とトリガー情報が渡された時
      When review/update を実行する
      Then トリガーがどの前提を変動させるかを特定し、確率レンジを更新し、条件付き未来（futures）に伝播し、差分を明示した更新レポートを生成して保存する

- [ ] Given 確率分布が有意に変わった時
      When review/update を実行する
      Then 自己懐疑フェーズを再実行する

- [ ] Given 存在しない report_id が渡された時
      When review/update を実行する
      Then エラーを返す

- [ ] Given テーマドメイン以外のレポートの report_id が渡された時
      When review/update を実行する
      Then スコープ外であることを報告して終了する

## review/validate

- [ ] Given 過去の評価レポートの report_id が渡された時
      When review/validate を実行する
      Then 各前提の判断精度（accurate / partial / inaccurate）を評価し、先行指標のラグを検証し、系統的偏りを検出し、検証済み知見を蓄積する

- [ ] Given シグナルチェーンが仮説（hypothesis）状態の時
      When validate で有効性が確認された時
      Then シグナルチェーン一覧の当該チェーンを「検証済み（verified）」ステータスに変更する

## レポート保存

- [ ] Given 分析レポートが生成された時
      When 保存を実行する
      Then レポートがテーマドメイン（macro-theme-analyst）のメタデータで保存される

- [ ] Given 保存サービスが利用不可の時
      When evaluate を実行する
      Then 保存をスキップし、分析レポートを直接返却する（report_id: null）

## データ収集フィードバック

- [ ] Given 収集結果にテーマ分析に必要だが収集されなかったデータカテゴリがある時
      When フィードバックを評価する
      Then パターン不足（pattern-gap）タイプのフィードバックが記録される

- [ ] Given 収集品質に問題がない時
      When フィードバックを評価する
      Then フィードバックは記録されない

## 学習記録

- [ ] Given evaluate が完了した時
      When 結果を返却する
      Then 実行ログ（テーマ名、分析深度、前提数、確率レンジ、self_critique フラグ、データギャップ数）が記録される

- [ ] Given review/update が完了した時
      When 結果を返却する
      Then 実行ログ（トリガー、変更前提数、確率シフト有無）が記録される

- [ ] Given review/validate が完了した時
      When 結果を返却する
      Then 実行ログ（前提精度、シグナル精度、検出された偏り）が記録される

## 較正情報の活用

- [ ] Given 過去の validate で系統的偏りが検出されている時
      When evaluate を実行する
      Then 偏り傾向を認識し、分析に反映する

- [ ] Given 実行ログが存在しない時（初回実行）
      When evaluate を実行する
      Then 較正情報の参照をスキップし、通常通りテーゼ構築から開始する
