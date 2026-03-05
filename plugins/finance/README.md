# finance

[English](README.en.md)

金融分析（経済・投資商品・株式・ポートフォリオ）と投資判断支援のスキル群です。

## 設定の上書き

設定変数（例: `base_dir`）を変更したい場合は、プロジェクトの `.claude/settings.json` または `settings.local.json` で上書きできます。`base_dir` のデフォルトは `home/finance` です（成果物・学習データの配置ベースパス）。

## skills-hidden について

一部のスキルは `skills-hidden/` にあり、Skill ツールからは呼び出せません。呼び出し元のスキルが Read で `skills-hidden/<name>/SKILL.md` を読み、手順をインラインで実行します。公開スキルである finance-advisor などが、内部で report-store や analyst-catalog などの隠蔽スキルを利用します。

## 名前空間

スキル・コマンドは `<plugin-name>:<resource-name>` で呼び出します。例: `finance:finance-advisor`、`finance:stock`、`/finance:stock NVDA`。

## 一時作業領域（workspace）

一時作業領域は、当該 Plugin の base_dir 配下の `workspace/` に置きます（例: `<base_dir>/workspace/`）。base_dir を設定で変更している場合も同様です。命名は `YYYYMMDD-<label>-<seq>` を推奨します。
