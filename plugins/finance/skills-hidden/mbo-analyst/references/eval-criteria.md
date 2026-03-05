# mbo-analyst 評価基準

本ファイルは `mbo-analyst` スキルの動作を検証するためのチェックリストです。
SPEC の受け入れ基準を、ユーザが観察可能な入出力の振る舞いとして記述しています。

---

## criteria

- [ ] Given criteria を実行した時
      When 引数なしで実行する
      Then MBO スクリーニングに適した条件一覧（指標名、閾値、理由）が返り、スクリーニングツールでの設定方法が案内される

- [ ] Given focus: FCF 重視 が指定された時
      When criteria を実行する
      Then FCF 関連指標を重視した条件構成が返る

## batch-score

- [ ] Given 財務指標列を含む CSV が渡された時
      When batch-score を実行する
      Then Web 検索を行わず CSV データのみから各銘柄の A/B スコアを算出し、スコア降順リストとスコア分布が返る

- [ ] Given threshold: 4 が指定された時
      When batch-score を実行する
      Then A スコア 4 以上の銘柄のみが結果に含まれる

- [ ] Given 業種列を含む CSV が渡された時
      When batch-score を実行する
      Then 東証業種から業種プロファイル（α/β/γ/δ/ε）が割り当てられ、L1 ゲート判定が結果に含まれる

- [ ] Given 一部の財務指標列が欠損している CSV が渡された時
      When batch-score を実行する
      Then 利用可能な指標のみで A スコアを算出し、欠損指標を明記する

## pipeline

- [ ] Given CSV が渡され dry-run: true が指定された時
      When pipeline を実行する
      Then Phase 1（バッチスコア算出）のみ実行され、Phase 2 以降の推定コストが返る

- [ ] Given CSV が渡され a-threshold: 3 が指定された時
      When pipeline を実行する
      Then Phase 1 で A ≥ 3 の銘柄が抽出され、オーナー構造検証 → 5軸分析と段階的に絞り込まれた最終候補リストが返る

- [ ] Given pipeline が完了した時
      When 結果を確認する
      Then 各フェーズの中間報告と最終統合レポートが返り、全結果が記録されている

## scan 正常系

- [ ] Given ヘッダ付き CSV（銘柄コード列あり）が渡された時
      When scan を実行する
      Then CSV を解析し、各銘柄のオーナー構造を Web 検索で確認し、通過/除外/不確定に分類した候補リストと実行 ID が返る

- [ ] Given CSV に企業名・財務指標列が含まれている時
      When scan を実行する
      Then それらの情報も実行記録に含まれる

- [ ] Given strict: true が指定された時
      When scan を実行する
      Then 不確定（uncertain）判定の銘柄も除外として扱われる

- [ ] Given DB が存在しない状態で scan を実行した時
      When scan を実行する
      Then DB が初期化された後、scan が正常完了する

## scan 異常系

- [ ] Given 銘柄コード列を特定できない CSV が渡された時
      When scan を実行する
      Then エラーメッセージが返り、DB への記録は行われない

## Gate 判定

- [ ] Given 規制業種（銀行・保険・電力等）の銘柄が指定された時
      When analyze を実行する
      Then gate_pass: false、除外理由に「規制業種」が設定され、5 軸スコアは算出されない

- [ ] Given 経営者持株 < 5% かつ創業家関係なし の銘柄が指定された時
      When analyze を実行する
      Then gate_pass: false、除外理由に「自然な買い手が存在しない」が設定される

- [ ] Given 時価総額 > 1,000 億円 の銘柄が指定された時
      When analyze を実行する
      Then gate_pass: false、除外理由に「時価総額超過」が設定される

- [ ] Given Gate ハード除外条件に該当しないがソフト確認 2/3 を満たさない銘柄が指定された時
      When analyze を実行する
      Then gate_pass: false、除外理由に「ソフト確認 2/3 未満」が設定される

- [ ] Given PE 大株主または PE 出身役員が確認された銘柄が指定された時
      When Gate 判定を行う
      Then t5_bypass: true が設定され、Gate の他の条件に関わらず 5 軸評価に進む

- [ ] Given Gate を通過した銘柄が指定された時
      When analyze を実行する
      Then gate_pass: true が設定され、5 軸評価・P_Score・優先度判定が算出される

- [ ] Given データ品質スコアが低く（< 0.4）かつ先行シグナルもない銘柄が分析された時
      When Gate 判定前のデータ品質評価を行う
      Then Gate 判定は行われず「保留（要追加調査）」として出力されレポートが生成される

- [ ] Given データ品質スコアが低い（< 0.4）が先行シグナル（持株・PE 関連情報）がある時
      When Gate 判定前のデータ品質評価を行う
      Then 品質低下をレポートに明記して Gate 判定へ継続する

- [ ] Given データ品質スコアが十分（≥ 0.4）の時
      When Gate 判定前のデータ品質評価を行う
      Then 品質警告なしで通常の Gate 判定へ継続する

## P_Score・Priority 判定

- [ ] Given PBR が 0.5 未満かつネット現金が時価総額の 30% 超の銘柄が通過した時
      When P_Score を算出する
      Then p_score が 4 以上となる

- [ ] Given C2_short ≥ 3 かつ MBO_Score が一定以上の銘柄の時
      When Priority_short を判定する
      Then priority_short が「最優先」となる

- [ ] Given C2_short ≥ 3 かつ MBO_Score が閾値未満の銘柄の時
      When Priority_short を判定する
      Then priority_short が「通常監視」となる

- [ ] Given C2_mid ≥ 3 かつ P_Score が一定以上の銘柄の時
      When Priority_mid を判定する
      Then priority_mid が「最優先」となる

- [ ] Given C2_mid ≥ 3 かつ P_Score が閾値未満の銘柄の時
      When Priority_mid を判定する
      Then priority_mid が「通常監視」となる

- [ ] Given 注目投資家（authority-signal の対象）が当該銘柄を保有していることが検出された時
      When analyze で authority_signal 検出を行う
      Then 支配構造・実行容易性スコアが加点再計算され、Priority_short/Priority_mid が 1 段階引き上げられ、シグナル種別と加点量がレポートに明記される

- [ ] Given 注目投資家が検出されなかった時
      When analyze を実行する
      Then authority_signal = null として記録され、スコアの再計算は行われない

## analyze 正常系

- [ ] Given 銘柄コードの分析依頼（「9984 を MBO 分析して」）が渡された時
      When analyze を実行する
      Then データを収集し、A/B/C/D/E 5 軸 + MCS/Tier を含むレポートを生成し、DB とレポートファイルに保存する

- [ ] Given depth: 概要 が指定された時
      When analyze を実行する
      Then 概要モードの収集範囲（T1, T2, T3、最大 5 回検索）でデータを収集し、簡潔なレポートを生成する

- [ ] Given depth: 詳細 が指定された時
      When analyze を実行する
      Then 詳細モードの収集範囲（拡張トピック、最大 30 回検索）でデータを収集し、類似 MBO 事例比較を含む詳細レポートを生成する

- [ ] Given 保存サービスが利用可能な時
      When analyze が完了する
      Then 株式ドメイン（mbo-analyst）のメタデータで保存される

- [ ] Given 保存サービスが利用不可の時
      When analyze が完了する
      Then 保存サービスへの書き込みをスキップし、DB とレポートファイルのみに保存する

## analyze スコアリング

- [ ] Given 分析レポートが生成された時
      When スコアリングを実行する
      Then 評価基準に従い valuation_score / business_score / control_score / deal_score / impediment_score が付与され、MCS/Tier が算出される

- [ ] Given A/B/C/D/E スコアが付与された時
      When 結果を確認する
      Then C は C1/C2_short/C2_mid を併記し、5 軸の根拠・MCS・Tier が一貫して提示される

- [ ] Given analyze で C 評価を行った時
      When C2 を算出する
      Then C2_short（0-6ヶ月催化：後継課題・対市場ストレス）と C2_mid（6-24ヶ月構造：上場維持効用低下・非公開化便益）が分離してスコアリングされる

- [ ] Given C2 < 2.5 の銘柄が analyze された時
      When Tier を判定する
      Then Tier 上限が B に制約され、レポートに「動機不足ガードレール適用」が注記される

- [ ] Given analyze で D 評価を行った時
      When 資金調達実行性（financing_feasibility）を算出する
      Then 想定LTV・DSCR・担保余力・金利耐性が算出され、金利局面補正（低金利 +0.2 / 高金利 -0.2）が D スコアに加算される

## analyze 早期終了チェック

- [ ] Given csv-data あり、A スコア < 2.5、MBO シグナルなし、かつ advisor 経由の呼び出しの時
      When analyze を実行する
      Then データ収集・Gate 判定を行わず、スキップ推奨の構造化データを返して終了する

- [ ] Given csv-data あり、A スコア < 2.5、MBO シグナルなし、かつ直接呼び出しの時
      When analyze を実行する
      Then 命令者に継続可否を確認し、「終了」選択時は簡易テキストを返して打ち切る

- [ ] Given csv-data あり、A スコア ≥ 2.5 の時
      When analyze を実行する
      Then 早期終了チェックを通過し、通常の analyze フローを継続する

- [ ] Given csv-data あり、A スコア < 2.5 だが「MBO」等のシグナルキーワードが入力に含まれる時
      When analyze を実行する
      Then 早期終了を適用せず、通常の analyze フローを継続する

- [ ] Given csv-data なし の時
      When analyze を実行する
      Then 早期終了チェックをスキップして通常の analyze フローを実行する

## analyze csv-data モード

- [ ] Given csv-data 付きで analyze を実行した時
      When A 評価を行う
      Then csv-data の財務指標から A スコアを算出し、財務・バリュエーション・キャッシュフローの Web 検索をスキップする

- [ ] Given csv-data 付き depth: 概要 で analyze を実行した時
      When データ収集を行う
      Then 最大 2 回検索で大株主情報のみ取得し、簡潔なレポートを生成する

## analyze スコープ外

- [ ] Given 東証上場企業でない銘柄が指定された時
      When analyze を実行する
      Then スコープ外であることを報告して終了する

## analyze 収集不足

- [ ] Given データ収集でエラーが発生した時
      When analyze を実行する
      Then 利用可能な情報のみで分析を続行し、レポートに制約を明記する

## review

- [ ] Given 分析済み銘柄コードが指定された時
      When review を実行する
      Then 前回分析以降の変化を Web 検索で確認し、A/B/C/D/E への影響と再分析推奨の有無を含む差分レポートが返る

- [ ] Given review を実行した時
      When 変化を検出する
      Then 監視対象ファンド（fund-watchlist）の新規保有・変動・役員派遣・共同保有化が必須検索対象に含まれる

- [ ] Given 監視対象ファンドが当該銘柄を新規保有・持分増加させた時
      When review を実行する
      Then ファンド関連イベントとして記録され、支配構造・実行容易性への影響が評価されレポートに反映される

- [ ] Given 注目投資家の動き（新規保有・役員就任等）が検出された時
      When review を実行する
      Then 投資家シグナルとして記録され、スコア再計算が推奨されレポートに明記される

- [ ] Given 短期催化イベント（trigger）が消滅・無効化された変化が検出された時
      When 影響評価を行う
      Then 「短期シグナル失効」ラベルが付与され Priority_short が下方修正される

- [ ] Given 中期構造シナリオが引き続き継続していることが確認された時
      When 影響評価を行う
      Then 「中期シナリオ継続」ラベルが付与され Priority_mid が維持される

- [ ] Given all が指定された時
      When review を実行する
      Then 分析済み全銘柄について変化を確認し、銘柄ごとの差分レポートが返る

- [ ] Given 変化が検出されなかった時
      When review を実行する
      Then 「変化なし」と報告し、レビュー記録に記録する

- [ ] Given 分析履歴がない銘柄コードが指定された時
      When review を実行する
      Then エラーメッセージが返る

## DB 操作

- [ ] Given analyze が完了した時
      When 結果を DB に保存する
      Then Gate 情報・P_Score・優先度・資金調達実行性・authority_signal を含む記録が DB に保存される

- [ ] Given review が完了した時
      When 結果を DB に保存する
      Then 影響度・再分析推奨フラグ・ファンドイベント・投資家シグナル・時間軸ラベルを含む記録が DB に保存される

- [ ] Given scan で複数銘柄を処理した時
      When 結果を DB に保存する
      Then 全銘柄の結果が 1 トランザクションで保存される
