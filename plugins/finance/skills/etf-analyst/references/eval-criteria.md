# etf-analyst 評価基準

本ファイルは `etf-analyst` スキルの動作を検証するためのチェックリストです。
SPEC の受け入れ基準を、ユーザが観察可能な入出力の振る舞いとして記述しています。

---

## analyze 正常系

- [ ] Given ETF 名の分析依頼（「TOPIX 連動 ETF を分析して」）が渡された時
      When analyze を実行する
      Then ETF を特定し、ETF データを収集し、ETF 固有分析を含むレポートを生成し、保存 ID（store_id）が発行される

- [ ] Given 銘柄コードの分析依頼（「1306 を分析して」）が渡された時
      When analyze を実行する
      Then 銘柄コードから ETF を特定し、分析レポートを生成する

- [ ] Given ティッカーの分析依頼（「SPY を分析して」）が渡された時
      When analyze を実行する
      Then ティッカーから ETF を特定し、分析レポートを生成する

- [ ] Given depth: 標準 で分析依頼された時
      When analyze を実行する
      Then 標準モードのデータ収集（最大 10 回検索）と NAV 70% カバーの構成銘柄調査が実行される

- [ ] Given depth: 概要 が指定された時
      When analyze を実行する
      Then ETF レベルの基本データのみ収集（最大 3 回検索）し、構成銘柄調査は行わない

- [ ] Given depth: 詳細 が指定された時
      When analyze を実行する
      Then 拡張データ収集（最大 15 回検索）と NAV 70% カバーの構成銘柄調査が実行される

- [ ] Given focus: コスト が指定された時
      When analyze を実行する
      Then コスト分析を重点的に深掘りしたレポートを生成する

## 構成銘柄カバレッジ

- [ ] Given 構成銘柄リストが取得できた時
      When 調査対象を決定する
      Then NAV ウェイト上位から累計約 70% をカバーする銘柄が調査対象になる

- [ ] Given 構成銘柄リストが取得できなかった時
      When 調査対象を決定する
      Then 構成分析なしで ETF レベル分析のみ続行し、レポートに制約を明記する

## deep_constituents（構成銘柄の深掘り分析）

- [ ] Given deep_constituents: true が指定された時
      When 個別銘柄の深掘り分析を開始する前に
      Then 予算計画（対象銘柄数、推定コスト）が提示され、承認を得る

- [ ] Given deep_constituents 中に個別銘柄の深掘り分析が失敗した時
      When 個別銘柄の分析が失敗する
      Then 当該銘柄をスキップし、残りの銘柄の分析を続行する

- [ ] Given deep_constituents で全ての個別銘柄分析が失敗した時
      When 深掘り分析が全て失敗する
      Then 収集データのみで構成分析を行い、レポートに制約を明記する

## スコープ外

- [ ] Given ETF でない分析依頼（「トヨタを分析して」）が渡された時
      When analyze を実行する
      Then スコープ外であることを報告して終了する

- [ ] Given 投資信託（非上場）の分析依頼が渡された時
      When analyze を実行する
      Then スコープ外であることを報告して終了する

## 収集結果の不足

- [ ] Given 経費率・NAV データが取得できなかった時
      When 収集結果を確認する
      Then コスト・トラッキング分析が制限される旨を報告し、続行するか確認する

- [ ] Given データ収集でエラーが発生した時
      When 収集依頼が失敗する
      Then 利用可能な情報のみで分析を続行し、レポートに制約を明記する

## スコアリングとレーティング

- [ ] Given 分析レポートが生成された時
      When スコアリングを実行する
      Then 評価基準に従い cost_efficiency / tracking_quality / liquidity_accessibility / constituent_quality の 4 軸評価が付与され、各軸に根拠が付記される

- [ ] Given 4 軸スコアが付与された時
      When 投資レーティングを決定する
      Then 4 軸を総合し strong buy / buy / neutral / sell / strong sell のいずれかが付与され、根拠が 1-2 文で記述される

- [ ] Given 分析レポートが保存された時
      When 保存が完了する
      Then 分析品質スコアが付与される

## compare

- [ ] Given 2 つの ETF の比較依頼が渡された時
      When compare を実行する
      Then 各 ETF を概要モードで分析し、比較マトリクスと推奨を含む比較レポートを生成する

- [ ] Given 5 銘柄を超える比較依頼が渡された時
      When compare を実行する
      Then 5 銘柄以下への絞り込みを求める

- [ ] Given compare 操作を実行する時
      When 個別分析を行う
      Then 構成銘柄の深掘り分析は行わない（コスト抑制）

- [ ] Given 2 つ以上の同カテゴリ ETF の比較依頼が渡された時
      When compare の比較分析を実行する
      Then 経費率・トラッキングエラーの同カテゴリ四分位統計（max / 75th / median / 25th / min）が算出され、各 ETF のパーセンタイル位置が比較マトリクスに含まれる

- [ ] Given 純資産フローデータが収集できた時
      When compare の比較分析を実行する
      Then 各 ETF のフロートレンド（前期比変化率・加速度）が算出され、同カテゴリ内でのフロー動向が比較される

- [ ] Given 同カテゴリの統計データが不足している時
      When 四分位統計を算出する
      Then 比較対象 ETF 群内の統計のみで代替し、カテゴリ統計が限定的であることをレポートに明記する

## レポート保存

- [ ] Given 分析レポートが生成された時
      When 保存を実行する
      Then レポートが ETF ドメイン（etf-analyst）のメタデータで保存される

- [ ] Given deep_constituents で個別銘柄分析の保存 ID がある時
      When 保存を実行する
      Then 個別銘柄分析の ID も「使用した入力」として関連付けて記録される

- [ ] Given 保存サービスが利用不可の時
      When analyze を実行する
      Then 保存をスキップし、分析レポートを直接返却する（store_id: null）

## データ収集フィードバック

- [ ] Given ETF データの鮮度に問題がある時
      When フィードバックを評価する
      Then ソース品質（source-quality）タイプのフィードバックが記録される

- [ ] Given ETF 分析に必要だが収集されなかったデータカテゴリがある時
      When フィードバックを評価する
      Then パターン不足（pattern-gap）タイプのフィードバックが記録される

## review

- [ ] Given 存在する store_id と concern が渡された時
      When review を実行する
      Then 元レポートを取得し、concern に基づいて再分析し、更新レポートを保存する

- [ ] Given review で構成銘柄の深掘りが必要な時
      When review を実行する
      Then 予算を提示して承認を得てから個別銘柄分析を実行する

- [ ] Given ETF ドメイン以外のレポートの store_id が渡された時
      When review を実行する
      Then スコープ外であることを報告して終了する

## 収集範囲制御

- [ ] Given depth: 標準 で分析依頼された時
      When 収集を実行する
      Then 標準モードの収集範囲（全 7 トピック、最大 10 回検索）でデータが収集される

- [ ] Given depth: 概要 で分析依頼された時
      When 収集を実行する
      Then 概要モードの収集範囲（基本情報・コスト・純資産の 3 トピック、最大 3 回検索）でデータが収集される

- [ ] Given depth: 詳細 で分析依頼された時
      When 収集を実行する
      Then 詳細モードの収集範囲（拡張トピック、最大 15 回検索）でデータが収集される
