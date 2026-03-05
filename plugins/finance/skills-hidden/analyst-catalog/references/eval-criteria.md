# analyst-catalog 評価基準

本ファイルは `analyst-catalog` スキルの動作を検証するためのチェックリストです。
SPEC の受け入れ基準を、ユーザが観察可能な入出力の振る舞いとして記述しています。

---

## register 正常系

- [ ] Given finance パッケージ内のアナリストスキル名が渡された時
      When register を実行する
      Then SKILL.md を読み込み capability を抽出し、成果物を検査して competence を評価し、カタログエントリを生成して保存する

- [ ] Given アナリストが references/ 配下にルーブリックを持っている時
      When register を実行する
      Then rubric_exists: true、rubric_updated にファイルの更新日が記録される

- [ ] Given アナリストの分析レポートが保存されている時
      When register を実行する
      Then analysis_count に実績数、last_analysis に最終分析日が記録される

- [ ] Given 保存サービスが利用不可の時
      When register を実行する
      Then analysis_count: 0、last_analysis: null として登録を完了する

- [ ] Given アナリストのジャーナルが存在する時
      When register を実行する
      Then ジャーナル内容から quality_summary, strength_areas, weakness_areas を集約して competence に反映する

## register 異常系

- [ ] Given 存在しないスキル名が渡された時
      When register を実行する
      Then エラーを返す

- [ ] Given finance パッケージ外のスキル名が渡された時
      When register を実行する
      Then スコープ外であることを報告する

- [ ] Given 既に登録済みのスキル名が渡された時
      When register を実行する
      Then エラーを返し、update を使用するよう案内する（register は非冪等）

- [ ] Given frontmatter に `role: infra` が設定されたスキル名が渡された時
      When register を実行する
      Then エラーを返し、analyst ではないことを報告する

## register の capability confidence

- [ ] Given SKILL.md から domain, market, focus_areas が全て抽出できた時
      When register を実行する
      Then confidence: high のエントリを生成する

- [ ] Given SKILL.md から domain, market, focus_areas のいずれかが抽出できなかった時
      When register を実行する
      Then confidence: low のエントリを生成し、警告を出しつつ登録を完了する

## update 正常系

- [ ] Given 登録済みアナリストのスキル名が渡された時
      When update を実行する
      Then SKILL.md を再読み込みし capability を再抽出、成果物を再検査して competence を再評価し、カタログエントリを更新して上書きする

- [ ] Given capability に変更がある時（SPEC 変更後）
      When update を実行する
      Then 変更された capability が反映され、changes に変更点が記録される

- [ ] Given competence のみ変更がある時（分析実績の増加等）
      When update を実行する
      Then competence が最新値に更新され、changes に変更点が記録される

- [ ] Given ジャーナルに新しい記録が追加された後
      When update を実行する
      Then quality_summary, strength_areas, weakness_areas が最新のジャーナル内容で再集約される

## update 異常系

- [ ] Given 未登録のスキル名が渡された時
      When update を実行する
      Then エラーを返し、register を使用するよう案内する

## record 正常系

- [ ] Given 登録済みアナリスト名、task_summary、outcome が渡された時
      When record を実行する
      Then ジャーナルエントリを生成しジャーナルファイルに追記する

- [ ] Given note が指定された時
      When record を実行する
      Then note がジャーナルエントリに含まれる

- [ ] Given note が省略された時
      When record を実行する
      Then note: null としてジャーナルエントリを記録する

- [ ] Given ジャーナルファイルが存在しない時
      When record を実行する
      Then ジャーナルファイルを新規作成しエントリを記録する

## record 異常系

- [ ] Given 未登録のスキル名が渡された時
      When record を実行する
      Then エラーを返し、register を使用するよう案内する

- [ ] Given task_summary が空の時
      When record を実行する
      Then エラーを返す

- [ ] Given outcome が規定値以外の時
      When record を実行する
      Then エラーを返す
