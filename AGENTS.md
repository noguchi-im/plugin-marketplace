# my-operations: Codex instructions

このリポジトリで作業する際は、最初に `CLAUDE.md` を読み、定義された最優先原則・確認レベル・禁止事項に従うこと。

Plugin 仕様とスキル運用は `.claude/plugins/CLAUDE.md` を参照すること。

hidden スキルは `.claude/plugins/*/skills-hidden.yaml` を根拠に除外し、`skills-hidden/` 配下を通常の実行対象として扱わないこと。

スキル運用の入口は `core:skill-operator` を優先すること。
