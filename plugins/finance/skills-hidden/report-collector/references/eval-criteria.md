# report-collector 評価基準

本ファイルは `report-collector` スキルの動作を検証するためのチェックリストです。
SPEC の受け入れ基準を、ユーザが観察可能な入出力の振る舞いとして記述しています。

---

## collect 正常系

- [ ] Given 日本企業の開示情報の要求が渡された時
      When collect を実行する
      Then 開示情報を取得し、アブストラクトを生成し、保存して、追跡 ID（store_id）を含む収集レポートを返す

- [ ] Given 米国経済指標の要求が渡された時
      When collect を実行する
      Then 経済指標を取得し、アブストラクトを生成し、保存する

- [ ] Given 株価情報の要求が渡された時
      When collect を実行する
      Then 株価データを取得し、アブストラクトを生成し、保存する

- [ ] Given 複合要求（「トヨタ分析に必要な情報」）が渡された時
      When collect を実行する
      Then 複数の情報ニーズに分解し、各ソースからデータを取得し、全結果をまとめた収集レポートを返す

- [ ] Given ソースカタログにないトピックが要求された時
      When collect を実行する
      Then Web 検索でソースを探索し、取得し、アブストラクトを生成する

## 既存データの再利用

- [ ] Given 要求に合致する十分に新鮮なデータが既に保存されている時
      When collect を実行する
      Then 外部収集をスキップし、status: existing として既存データの ID とアブストラクトを返す

- [ ] Given 要求に合致するが鮮度が不十分なデータが既に保存されている時
      When collect を実行する
      Then 外部ソースから新規収集を行い、新しいアブストラクトで更新する

- [ ] Given 要求に合致するデータが保存されていない時
      When collect を実行する
      Then 外部ソースから新規収集を行う

## collect フォールバック

- [ ] Given 優先ソース（MCP サーバー等）が応答しない時
      When collect を実行する
      Then フォールバック URL で代替取得を試みる

- [ ] Given 優先ソースとフォールバック URL の両方が失敗した時
      When collect を実行する
      Then status: not-collected として理由を記録し、Web 検索による代替を試みる

## collect 制約

- [ ] Given 有料ソースのみが該当する場合
      When collect を実行する
      Then データ取得を行わず、status: not-collected と有料ソースの存在を提案（suggestions）として返す

- [ ] Given sources オプションで特定ソースが指定された場合
      When collect を実行する
      Then 指定ソースのみを使用して取得する

- [ ] Given date_range オプションが指定された場合
      When collect を実行する
      Then 指定期間内のデータのみを取得対象とする

## 収集予算制御

- [ ] Given search_budget: 15 が指定された時
      When 外部検索が 15 回に達した
      Then 残りのニーズは status: not-collected（reason: budget_exhausted）となる

- [ ] Given search_budget が省略された時
      When collect を実行する
      Then 検索回数の制限なく全ニーズを収集する

- [ ] Given search_budget: 15 で MCP 経由の取得がある時
      When データ取得する
      Then MCP 呼び出しは収集予算のカウント対象外となる

## 保存連携

- [ ] Given 新規収集に成功した項目がある時
      When 保存を実行する
      Then レポートが収集基盤（report-collector）のメタデータで保存される

- [ ] Given 保存サービスが利用不可の時
      When collect を実行する
      Then 保存をスキップし、収集レポートに結果を直接含める（store_id: null）

## 経験参照

- [ ] Given 過去に「日本企業分析」パターンで成功した収集履歴がある時
      When 類似の要求（「ソニーの分析に必要な情報」）を受ける
      Then 過去の分解パターンが類似検索で返り、分解の出発点として使用される

- [ ] Given 複数のソースの過去実績が記録されている時
      When 同等ソースから取得可能な情報を収集する
      Then 成功率の高いソースを優先して使用する

- [ ] Given 過去に有効なクエリが記録されているトピックで Web 検索を実行する時
      When 検索クエリを決定する
      Then 過去の有効クエリが優先的に使用される

## 経験記録

- [ ] Given 収集が完了した時
      When 経験記録を実行する
      Then 分解パターン・ソース実績・検索クエリが経験ジャーナルに記録される

- [ ] Given ジャーナル DB が存在しない時
      When 初回の収集を実行する
      Then ジャーナル DB が初期化され、収集結果が記録される

- [ ] Given ジャーナルに大量のパターンがある時
      When 類似パターンを検索する
      Then 上位 N 件のみ返し、全件をコンテキストに読み込まない

- [ ] Given 経験を記録する時
      When 記録する内容を決定する
      Then 操作的実績（成功/失敗・速度）のみ記録し、内容の品質評価は行わない

## 引用フォーマット

- [ ] Given Web 検索・取得で情報を取得した時
      When 出力を正規化する
      Then 各取得結果に document_type / source_name / url / published_at の 4 必須フィールドが付与される

- [ ] Given データソース経由で情報を取得し URL が得られなかった時
      When 出力を正規化する
      Then url フィールドは空とし、補足（note）に取得経路を記載する

- [ ] Given ソースの公開日が特定できなかった時
      When 出力を正規化する
      Then published_at に取得日時を代用し、補足（note）に「公開日不明、取得日で代用」と明記する

- [ ] Given 収集結果を保存する時
      When 保存を実行する
      Then sources フィールドに引用フォーマットの必須フィールドが含まれ、ドキュメント種別による絞り込みが可能な形で保存される

## feedback

- [ ] Given アナリストが「edinet の情報が古かった」とフィードバックした時
      When feedback(store_id, source-quality, detail) を実行する
      Then 該当ソースの実績に失敗記録が追加される

- [ ] Given アナリストが「競合分析が欠けていた」とフィードバックした時
      When feedback(store_id, pattern-gap, detail) を実行する
      Then 該当パターンの分解に競合分析が追加されて再記録される

- [ ] Given アナリストが「検索式が不適切だった」とフィードバックした時
      When feedback(store_id, query-quality, detail) を実行する
      Then 該当クエリの有効性が「無効」に更新され、理由が記録される

- [ ] Given 存在しない store_id でフィードバックした時
      When feedback を実行する
      Then エラーを返し、ジャーナルは更新しない
