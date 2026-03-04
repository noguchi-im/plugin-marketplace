# budget-tiers 予算ティア定義

finance-advisor が参照する複雑さレベルごとの予算枠。

## 予算の単位

- search_budget: 外部検索（WebSearch + WebFetch）の合計上限回数
- analyst_slots: 同時に起動するアナリストの上限数

## simple

| 項目 | 値 |
|---|---|
| advisor_search_budget | 5 |
| analyst_slots | 0 |
| confirmation_required | false |

advisor 自身が report-store 検索と report-collector による情報収集で回答する。
アナリストは起動しない。

## expert

| 項目 | 値 |
|---|---|
| advisor_search_budget | 3 |
| analyst_slots | 1 |
| analyst_search_budget | アナリストの depth 設定に従う |
| confirmation_required | depth: 詳細 の場合 true、それ以外 false |

1件のアナリストに委任する。
アナリストの search_budget はアナリスト自身の depth 設定（概要: 5、標準: 15、詳細: 30）に従う。

### 承認閾値

depth: 詳細（search_budget: 30）の場合、命令者に予算内訳を提示し承認を得る。

## research

| 項目 | 値 |
|---|---|
| advisor_search_budget | 5 |
| analyst_slots | 5 |
| analyst_search_budget | 各アナリストの depth 設定に従う |
| confirmation_required | true（常に必要） |

複数アナリストに委任する。常に命令者の承認が必要。

### 合計予算の見積もり

命令者に提示する見積もりは以下を合計する:

- advisor_search_budget
- 各アナリストの search_budget（depth に基づく）の合計
