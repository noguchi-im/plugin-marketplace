#!/usr/bin/env python3
"""mbo-analyst gate/score utility v1.

Encapsulates deterministic calculation logic that would otherwise bloat SKILL.md.
The calling LLM extracts structured facts from collected text data, then delegates
the rule application to this script via Bash.

Subcommands:
  gate      – Stage 1 Gate judgment (hard exclusion → T5 bypass → soft confirmation)
  p-score   – TOB premium potential score (P_Score, 1.0-5.0)
  priority  – Portfolio priority classification (最優先 / 通常監視 / 要確認 / 対象外)
"""

import argparse
import json
import sys

# 規制業種: MBO 対象外
REGULATED_INDUSTRIES = {
    "銀行業", "保険業", "電気・ガス業",
    "電気業", "ガス業", "放送業",
}


def _ok(data: dict):
    print(json.dumps(data, ensure_ascii=False))
    sys.exit(0)


def _error(msg: str):
    print(json.dumps({"error": msg}, ensure_ascii=False), file=sys.stderr)
    sys.exit(1)


# ── gate ─────────────────────────────────────────────────────────────────────

def cmd_gate(args):
    """Stage 1 Gate: hard exclusion → T5 bypass → soft confirmation.

    The LLM reads collected text (T1-T4) and extracts structured facts,
    then passes them as arguments. This function applies the deterministic rules.
    """
    fail_reason = None

    # ── Hard exclusions (first match wins) ───────────────────────────────────
    industry = (args.industry or "").strip()
    if industry in REGULATED_INDUSTRIES:
        fail_reason = f"規制業種: {industry}"

    if fail_reason is None and args.is_subsidiary:
        fail_reason = "上場親会社の連結子会社（持株 50% 超）"

    if (fail_reason is None
            and args.owner_pct is not None
            and args.owner_pct < 5.0
            and not args.has_founding_family):
        fail_reason = f"経営者持株 {args.owner_pct:.1f}% < 5% かつ創業家関係なし"

    if (fail_reason is None
            and args.market_cap_oku is not None
            and args.market_cap_oku > 1000):
        fail_reason = f"時価総額 {args.market_cap_oku:.0f} 億円 > 1,000 億円"

    if fail_reason is None and args.fraud_detected:
        fail_reason = "直近 3 年以内に重大不正・訴訟"

    if fail_reason is not None:
        _ok({"gate_pass": False, "gate_fail_reason": fail_reason, "t5_bypass": False})

    # ── T5 bypass (PE detected → skip soft confirmation) ─────────────────────
    if args.pe_detected:
        _ok({"gate_pass": True, "gate_fail_reason": None, "t5_bypass": True})

    # ── Soft confirmation (need 2 of 3) ──────────────────────────────────────
    passed = sum([
        bool(args.soft_c1_pass),
        bool(args.soft_d_pass),
        bool(args.soft_t_detected),
    ])
    if passed < 2:
        missing = []
        if not args.soft_c1_pass:    missing.append("C1<3")
        if not args.soft_d_pass:     missing.append("D<3")
        if not args.soft_t_detected: missing.append("T未検出")
        fail_reason = f"ソフト確認 {passed}/3（不足: {', '.join(missing)}）"
        _ok({"gate_pass": False, "gate_fail_reason": fail_reason, "t5_bypass": False})

    _ok({"gate_pass": True, "gate_fail_reason": None, "t5_bypass": False})


# ── p-score ──────────────────────────────────────────────────────────────────

def _nav_score(pbr: float) -> int:
    nd = max(0.0, 1.0 / pbr - 1.0) if pbr > 0 else 0.0
    if nd >= 1.0:  return 5
    if nd >= 0.5:  return 4
    if nd >= 0.25: return 3
    if nd >= 0.05: return 2
    return 1


def _net_cash_score(ratio: float) -> int:
    if ratio >= 0.30: return 5
    if ratio >= 0.10: return 4
    if ratio >= 0.05: return 3
    if ratio >= 0.0:  return 2
    return 1


def _hidden_asset_score(coeff: float) -> int:
    if coeff >= 0.50: return 5
    if coeff >= 0.30: return 4
    if coeff >= 0.10: return 3
    if coeff >= 0.05: return 2
    return 1


def _fcf_yield_score(pct: float) -> int:
    if pct > 10: return 5
    if pct > 6:  return 4
    if pct > 4:  return 3
    if pct > 2:  return 2
    return 1


def cmd_p_score(args):
    nav   = _nav_score(args.pbr)
    net   = _net_cash_score(args.net_cash_ratio)
    fcf   = _fcf_yield_score(args.fcf_yield_pct)
    hid   = None

    if args.hidden_asset_coeff is not None:
        hid = _hidden_asset_score(args.hidden_asset_coeff)
        raw = nav * 0.40 + net * 0.30 + hid * 0.15 + fcf * 0.15
    else:
        # hidden_asset 不明: 残り 3 指標で再正規化 (40/85≈0.47, 30/85≈0.35, 15/85≈0.18)
        raw = nav * 0.47 + net * 0.35 + fcf * 0.18

    p_score = round(max(1.0, min(5.0, raw)), 1)
    _ok({
        "p_score":        p_score,
        "nav_score":      nav,
        "net_cash_score": net,
        "hidden_score":   hid,
        "fcf_score":      fcf,
    })


# ── priority ─────────────────────────────────────────────────────────────────

def cmd_priority(args):
    mbo_score = round(max(1.0, min(5.0, args.mcs / 3.0)), 1)
    p         = args.p_score

    if mbo_score >= 3.5 and p >= 3.5:
        priority = "最優先"
    elif mbo_score >= 3.5:
        priority = "通常監視"
    elif args.t5_bypass or p >= 3.5:
        priority = "要確認"
    else:
        priority = "対象外"

    _ok({"mbo_score": mbo_score, "priority": priority})


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="mbo-analyst gate/score utility v1",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # ── gate ─────────────────────────────────────────────────────────────────
    g = sub.add_parser("gate", help="Stage 1 Gate judgment")
    g.add_argument("--industry",            default=None,
                   help="東証業種名")
    g.add_argument("--market-cap-oku",      type=float, default=None,
                   help="時価総額（億円）")
    g.add_argument("--owner-pct",           type=float, default=None,
                   help="経営者・創業家の持株比率（%%）")
    g.add_argument("--is-subsidiary",       action="store_true",
                   help="上場親会社の連結子会社")
    g.add_argument("--has-founding-family", action="store_true",
                   help="創業家の関与あり（owner-pct が 5%% 未満でも除外しない）")
    g.add_argument("--fraud-detected",      action="store_true",
                   help="直近 3 年以内に重大不正・訴訟あり")
    g.add_argument("--pe-detected",         action="store_true",
                   help="PE ファンドが大株主 5%% 超または PE 出身役員あり（T5 バイパス）")
    g.add_argument("--soft-c1-pass",        action="store_true",
                   help="ソフト確認: 経営者持株 10%% 以上かつオーナー構造明確（C1≥3 暫定）")
    g.add_argument("--soft-d-pass",         action="store_true",
                   help="ソフト確認: 時価総額 500 億円以下かつ自己資本比率 > 20%%（D≥3 暫定）")
    g.add_argument("--soft-t-detected",     action="store_true",
                   help="ソフト確認: 収集データに MBO/TOB/非公開化/ファンド関連の記述あり")

    # ── p-score ──────────────────────────────────────────────────────────────
    ps = sub.add_parser("p-score", help="P_Score (TOB premium potential) calculation")
    ps.add_argument("--pbr",                type=float, required=True,
                    help="PBR（株価純資産倍率）")
    ps.add_argument("--net-cash-ratio",     type=float, required=True,
                    help="ネット現金 / 時価総額（ネット有利子負債の場合は負値）")
    ps.add_argument("--fcf-yield-pct",      type=float, required=True,
                    help="FCF 利回り（%%）")
    ps.add_argument("--hidden-asset-coeff", type=float, default=None,
                    help="土地等含み益 / 時価総額（判明分; 不明時は省略）")

    # ── priority ─────────────────────────────────────────────────────────────
    pr = sub.add_parser("priority", help="Priority classification")
    pr.add_argument("--mcs",       type=float, required=True,
                    help="MBO 総合スコア（MCS）")
    pr.add_argument("--p-score",   type=float, required=True,
                    help="P_Score（1.0-5.0）")
    pr.add_argument("--t5-bypass", action="store_true",
                    help="T5 バイパスあり（PE 検出によるソフト確認スキップ）")

    args = parser.parse_args()
    {
        "gate":     cmd_gate,
        "p-score":  cmd_p_score,
        "priority": cmd_priority,
    }[args.command](args)


if __name__ == "__main__":
    main()
