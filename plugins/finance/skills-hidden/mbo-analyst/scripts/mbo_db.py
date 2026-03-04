#!/usr/bin/env python3
"""mbo-analyst DB operations CLI v4."""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone

DEFAULT_DB_PATH = "<base_dir>/mbo-analyst/db/mbo.db"


# ── helpers ──────────────────────────────────────────────────

def _connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def _ok(data=None):
    result = {"status": "ok"}
    if data:
        result.update(data)
    print(json.dumps(result, ensure_ascii=False, default=str))
    sys.exit(0)


def _error(message):
    print(json.dumps({"status": "error", "message": message},
                     ensure_ascii=False), file=sys.stderr)
    sys.exit(1)


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today():
    return datetime.now(timezone.utc).strftime("%Y%m%d")


def _generate_id(conn, prefix, date_str=None):
    """Generate ID like prefix-YYYYMMDD-NNN."""
    if date_str is None:
        date_str = _today()
    pattern = f"{prefix}-{date_str}-%"
    row = conn.execute(
        f"SELECT COUNT(*) as cnt FROM ("
        f"  SELECT scan_id AS id FROM scans WHERE scan_id LIKE ?"
        f"  UNION ALL"
        f"  SELECT analyze_id AS id FROM analyses WHERE analyze_id LIKE ?"
        f"  UNION ALL"
        f"  SELECT review_id AS id FROM reviews WHERE review_id LIKE ?"
        f"  UNION ALL"
        f"  SELECT batch_id AS id FROM batch_scores WHERE batch_id LIKE ?"
        f")",
        (pattern, pattern, pattern, pattern)
    ).fetchone()
    seq = (row["cnt"] if row else 0) + 1
    return f"{prefix}-{date_str}-{seq:03d}"


def _opt_float(val):
    """Convert optional string to float or None."""
    if val is None or val == "" or val == "null":
        return None
    return float(val)


# ── commands ─────────────────────────────────────────────────

def cmd_init(args):
    db_path = args.db_path
    init_sql = args.init_sql
    if not os.path.isfile(init_sql):
        _error(f"init.sql not found: {init_sql}")
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        with open(init_sql, encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.close()
        _ok({"message": "DB initialized", "db_path": db_path})
    except sqlite3.Error as e:
        conn.close()
        _error(f"DB init failed: {e}")


def cmd_scan_create(args):
    db_path = args.db_path
    if not os.path.isfile(db_path):
        _error(f"DB not found: {db_path}. Run init first.")
    conn = _connect(db_path)
    try:
        scan_id = _generate_id(conn, "scan")
        now = _now()
        conn.execute(
            "INSERT INTO scans (scan_id, executed_at, source_info, total_count) "
            "VALUES (?, ?, ?, 0)",
            (scan_id, now, args.source_info)
        )
        conn.commit()
        conn.close()
        _ok({"scan_id": scan_id, "executed_at": now})
    except sqlite3.Error as e:
        conn.close()
        _error(f"scan-create failed: {e}")


def cmd_scan_result_add(args):
    db_path = args.db_path
    if not os.path.isfile(db_path):
        _error(f"DB not found: {db_path}. Run init first.")
    conn = _connect(db_path)
    try:
        ownership = float(args.ownership_pct) if args.ownership_pct else None
        conn.execute(
            "INSERT INTO scan_results "
            "(scan_id, stock_code, company_name, tse_industry, threshold_profile, "
            "owner_check, result, reason, ownership_pct) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (args.scan_id, args.stock_code, args.company_name,
             args.tse_industry, args.threshold_profile,
             args.owner_check, args.result, args.reason, ownership)
        )
        # Update counts in scans table
        counts = {}
        for r in ["pass", "fail", "uncertain"]:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM scan_results "
                "WHERE scan_id = ? AND result = ?",
                (args.scan_id, r)
            ).fetchone()
            counts[r] = row["cnt"]
        total = counts["pass"] + counts["fail"] + counts["uncertain"]
        conn.execute(
            "UPDATE scans SET total_count = ?, pass_count = ?, "
            "fail_count = ?, uncertain_count = ? WHERE scan_id = ?",
            (total, counts["pass"], counts["fail"],
             counts["uncertain"], args.scan_id)
        )
        conn.commit()
        conn.close()
        _ok({"scan_id": args.scan_id, "stock_code": args.stock_code,
             "result": args.result})
    except sqlite3.Error as e:
        conn.close()
        _error(f"scan-result-add failed: {e}")


def cmd_batch_score_save(args):
    """Save batch-score results to batch_scores table (v3)."""
    db_path = args.db_path
    if not os.path.isfile(db_path):
        _error(f"DB not found: {db_path}. Run init first.")
    try:
        scores = json.loads(args.scores)
    except json.JSONDecodeError as e:
        _error(f"Invalid JSON for --scores: {e}")
    if not isinstance(scores, list):
        _error("--scores must be a JSON array")
    conn = _connect(db_path)
    try:
        batch_id = _generate_id(conn, "batch")
        saved = []
        for item in scores:
            code = item.get("stock_code")
            name = item.get("company_name", "")
            tse_industry = item.get("tse_industry")
            profile = item.get("threshold_profile")
            vscore = item.get("valuation_score")
            bscore = item.get("business_score")
            gate = item.get("gate_result", "pass")
            if not code:
                continue
            metrics_json = json.dumps(item.get("metrics", {}), ensure_ascii=False)
            conn.execute(
                "INSERT INTO batch_scores "
                "(batch_id, stock_code, company_name, tse_industry, threshold_profile, "
                "valuation_score, business_score, gate_result, metrics_json) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (batch_id, code, name, tse_industry, profile,
                 vscore, bscore, gate, metrics_json)
            )
            saved.append({"stock_code": code, "valuation_score": vscore,
                          "business_score": bscore, "gate_result": gate})
        conn.commit()
        conn.close()
        _ok({"batch_id": batch_id, "saved_count": len(saved), "results": saved})
    except sqlite3.Error as e:
        conn.close()
        _error(f"batch-score-save failed: {e}")


def _opt_bool(val, default=False):
    """Convert optional string to int (SQLite bool) or default."""
    if val is None or val == "" or val == "null":
        return 1 if default else 0
    return 1 if val.lower() in ("true", "1", "yes") else 0


def cmd_analyze_save(args):
    """Save analysis result (v4: Gate + DualScore)."""
    db_path = args.db_path
    if not os.path.isfile(db_path):
        _error(f"DB not found: {db_path}. Run init first.")
    conn = _connect(db_path)
    try:
        analyze_id = _generate_id(conn, "analyze")
        now = _now()
        gate_pass = _opt_bool(args.gate_pass, default=True)
        t5_bypass = _opt_bool(args.t5_bypass, default=False)
        conn.execute(
            "INSERT INTO analyses "
            "(analyze_id, stock_code, company_name, tse_industry, threshold_profile, "
            "analyzed_at, depth, "
            "gate_pass, gate_fail_reason, t5_bypass, "
            "valuation_score, business_score, "
            "control_score, control_c1, control_c2, deal_score, impediment_score, "
            "mcs, tier, mbo_type, confidence, "
            "p_score, p_nav_discount, p_net_cash_ratio, p_hidden_asset_coeff, p_fcf_yield, "
            "priority, "
            "feasibility_score, risk_score, report_path, store_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (analyze_id, args.stock_code, args.company_name,
             args.tse_industry, args.threshold_profile,
             now, args.depth,
             gate_pass, args.gate_fail_reason, t5_bypass,
             _opt_float(args.valuation_score), _opt_float(args.business_score),
             _opt_float(args.control_score), _opt_float(args.control_c1),
             _opt_float(args.control_c2), _opt_float(args.deal_score),
             _opt_float(args.impediment_score),
             _opt_float(args.mcs), args.tier, args.mbo_type, args.confidence,
             _opt_float(args.p_score), _opt_float(args.p_nav_discount),
             _opt_float(args.p_net_cash_ratio), _opt_float(args.p_hidden_asset_coeff),
             _opt_float(args.p_fcf_yield),
             args.priority,
             _opt_float(args.feasibility_score), _opt_float(args.risk_score),
             args.report_path, args.store_id)
        )
        conn.commit()
        conn.close()
        _ok({"analyze_id": analyze_id, "stock_code": args.stock_code,
             "analyzed_at": now, "gate_pass": bool(gate_pass),
             "priority": args.priority})
    except sqlite3.Error as e:
        conn.close()
        _error(f"analyze-save failed: {e}")


def cmd_review_save(args):
    db_path = args.db_path
    if not os.path.isfile(db_path):
        _error(f"DB not found: {db_path}. Run init first.")
    # Validate impact values
    valid_impacts = ("none", "minor", "reanalyze")
    for name, val in [("impact_a", args.impact_a),
                      ("impact_b", args.impact_b),
                      ("impact_c", args.impact_c),
                      ("impact_d", args.impact_d),
                      ("impact_e", args.impact_e)]:
        if val not in valid_impacts:
            _error(f"{name} must be one of {valid_impacts}, got '{val}'")
    conn = _connect(db_path)
    try:
        review_id = _generate_id(conn, "review")
        now = _now()
        changes = 1 if args.changes_detected == "true" else 0
        reanalyze = 1 if args.reanalyze_recommended == "true" else 0
        conn.execute(
            "INSERT INTO reviews "
            "(review_id, stock_code, reviewed_at, previous_analyze_id, "
            "changes_detected, impact_a, impact_b, impact_c, impact_d, impact_e, "
            "reanalyze_recommended, report_path) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (review_id, args.stock_code, now, args.previous_analyze_id,
             changes, args.impact_a, args.impact_b, args.impact_c,
             args.impact_d, args.impact_e,
             reanalyze, args.report_path)
        )
        conn.commit()
        conn.close()
        _ok({"review_id": review_id, "stock_code": args.stock_code,
             "reviewed_at": now})
    except sqlite3.Error as e:
        conn.close()
        _error(f"review-save failed: {e}")


def cmd_criteria_list(args):
    db_path = args.db_path
    if not os.path.isfile(db_path):
        _error(f"DB not found: {db_path}. Run init first.")
    conn = _connect(db_path)
    try:
        rows = conn.execute(
            "SELECT * FROM screening_criteria ORDER BY criteria_id"
        ).fetchall()
        conn.close()
        _ok({"criteria": [dict(r) for r in rows]})
    except sqlite3.Error as e:
        conn.close()
        _error(f"criteria-list failed: {e}")


def cmd_criteria_upsert(args):
    db_path = args.db_path
    if not os.path.isfile(db_path):
        _error(f"DB not found: {db_path}. Run init first.")
    conn = _connect(db_path)
    try:
        now = _now()
        conn.execute(
            "INSERT INTO screening_criteria "
            "(criteria_id, name, indicator, threshold, direction, reason, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(criteria_id) DO UPDATE SET "
            "name=excluded.name, indicator=excluded.indicator, "
            "threshold=excluded.threshold, direction=excluded.direction, "
            "reason=excluded.reason, updated_at=excluded.updated_at",
            (args.criteria_id, args.name, args.indicator,
             args.threshold, args.direction, args.reason, now)
        )
        conn.commit()
        conn.close()
        _ok({"criteria_id": args.criteria_id, "updated_at": now})
    except sqlite3.Error as e:
        conn.close()
        _error(f"criteria-upsert failed: {e}")


def cmd_search_analyses(args):
    db_path = args.db_path
    if not os.path.isfile(db_path):
        _error(f"DB not found: {db_path}. Run init first.")
    conn = _connect(db_path)
    try:
        where_clauses = []
        params = []
        if args.stock_code:
            where_clauses.append("stock_code = ?")
            params.append(args.stock_code)
        if args.depth:
            where_clauses.append("depth = ?")
            params.append(args.depth)
        if args.tier:
            where_clauses.append("tier = ?")
            params.append(args.tier)
        if args.profile:
            where_clauses.append("threshold_profile = ?")
            params.append(args.profile)
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        rows = conn.execute(
            f"SELECT * FROM analyses WHERE {where_sql} ORDER BY analyzed_at DESC",
            params
        ).fetchall()
        conn.close()
        _ok({"analyses": [dict(r) for r in rows]})
    except sqlite3.Error as e:
        conn.close()
        _error(f"search-analyses failed: {e}")


def cmd_get_latest_analysis(args):
    db_path = args.db_path
    if not os.path.isfile(db_path):
        _error(f"DB not found: {db_path}. Run init first.")
    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM analyses WHERE stock_code = ? "
            "ORDER BY analyzed_at DESC LIMIT 1",
            (args.stock_code,)
        ).fetchone()
        conn.close()
        if row is None:
            _error(f"No analysis found for stock_code: {args.stock_code}")
        _ok({"analysis": dict(row)})
    except sqlite3.Error as e:
        conn.close()
        _error(f"get-latest-analysis failed: {e}")


def cmd_search_batch_scores(args):
    """Search batch_scores table."""
    db_path = args.db_path
    if not os.path.isfile(db_path):
        _error(f"DB not found: {db_path}. Run init first.")
    conn = _connect(db_path)
    try:
        where_clauses = []
        params = []
        if args.batch_id:
            where_clauses.append("batch_id = ?")
            params.append(args.batch_id)
        if args.stock_code:
            where_clauses.append("stock_code = ?")
            params.append(args.stock_code)
        if args.profile:
            where_clauses.append("threshold_profile = ?")
            params.append(args.profile)
        if args.min_score:
            where_clauses.append("valuation_score >= ?")
            params.append(float(args.min_score))
        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        rows = conn.execute(
            f"SELECT * FROM batch_scores WHERE {where_sql} "
            f"ORDER BY valuation_score DESC",
            params
        ).fetchall()
        conn.close()
        _ok({"batch_scores": [dict(r) for r in rows]})
    except sqlite3.Error as e:
        conn.close()
        _error(f"search-batch-scores failed: {e}")


# ── main ─────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="mbo-analyst DB operations v4")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH,
                        help=f"Path to SQLite DB (default: {DEFAULT_DB_PATH})")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = subparsers.add_parser("init", help="Initialize DB")
    p_init.add_argument("--init-sql", required=True, help="Path to init.sql")

    # scan-create
    p_sc = subparsers.add_parser("scan-create", help="Create scan record")
    p_sc.add_argument("--source-info", required=True, help="CSV source info (JSON)")

    # scan-result-add
    p_sra = subparsers.add_parser("scan-result-add", help="Add scan result")
    p_sra.add_argument("--scan-id", required=True)
    p_sra.add_argument("--stock-code", required=True)
    p_sra.add_argument("--company-name", default=None)
    p_sra.add_argument("--tse-industry", default=None)
    p_sra.add_argument("--threshold-profile", default=None)
    p_sra.add_argument("--owner-check", default=None)
    p_sra.add_argument("--result", required=True, choices=["pass", "fail", "uncertain"])
    p_sra.add_argument("--reason", required=True)
    p_sra.add_argument("--ownership-pct", default=None)

    # analyze-save (v4: Gate + DualScore)
    p_as = subparsers.add_parser("analyze-save", help="Save analysis result (v4: Gate + DualScore)")
    p_as.add_argument("--stock-code", required=True)
    p_as.add_argument("--company-name", required=True)
    p_as.add_argument("--tse-industry", default=None)
    p_as.add_argument("--threshold-profile", default=None)
    p_as.add_argument("--depth", required=True, choices=["概要", "標準", "詳細", "スクリーニング"])
    # Gate (v4)
    p_as.add_argument("--gate-pass", default="true",
                      help="Gate pass result (true/false, default: true)")
    p_as.add_argument("--gate-fail-reason", default=None,
                      help="Reason for gate exclusion (when gate-pass=false)")
    p_as.add_argument("--t5-bypass", default="false",
                      help="PE detection bypass (true/false, default: false)")
    # 5-axis scores (optional when gate_pass=false)
    p_as.add_argument("--valuation-score", default=None)
    p_as.add_argument("--business-score", default=None)
    p_as.add_argument("--control-score", default=None)
    p_as.add_argument("--control-c1", default=None)
    p_as.add_argument("--control-c2", default=None)
    p_as.add_argument("--deal-score", default=None)
    p_as.add_argument("--impediment-score", default=None)
    p_as.add_argument("--mcs", default=None)
    p_as.add_argument("--tier", default=None, choices=["S", "A", "B", "C"])
    p_as.add_argument("--mbo-type", default=None)
    p_as.add_argument("--confidence", default=None, choices=["high", "medium", "low"])
    # P_Score (v4)
    p_as.add_argument("--p-score", default=None, help="TOB premium potential (1.0-5.0)")
    p_as.add_argument("--p-nav-discount", default=None)
    p_as.add_argument("--p-net-cash-ratio", default=None)
    p_as.add_argument("--p-hidden-asset-coeff", default=None)
    p_as.add_argument("--p-fcf-yield", default=None)
    # Priority (v4)
    p_as.add_argument("--priority", default=None,
                      choices=["最優先", "通常監視", "要確認", "対象外"])
    # v2/v3 compat
    p_as.add_argument("--feasibility-score", default=None)
    p_as.add_argument("--risk-score", default=None)
    p_as.add_argument("--report-path", required=True)
    p_as.add_argument("--store-id", default=None)

    # review-save (v3: 5-axis impact)
    p_rs = subparsers.add_parser("review-save", help="Save review result")
    p_rs.add_argument("--stock-code", required=True)
    p_rs.add_argument("--previous-analyze-id", required=True)
    p_rs.add_argument("--changes-detected", required=True, choices=["true", "false"])
    p_rs.add_argument("--impact-a", required=True, choices=["none", "minor", "reanalyze"])
    p_rs.add_argument("--impact-b", required=True, choices=["none", "minor", "reanalyze"])
    p_rs.add_argument("--impact-c", required=True, choices=["none", "minor", "reanalyze"])
    p_rs.add_argument("--impact-d", required=True, choices=["none", "minor", "reanalyze"])
    p_rs.add_argument("--impact-e", required=True, choices=["none", "minor", "reanalyze"])
    p_rs.add_argument("--reanalyze-recommended", required=True, choices=["true", "false"])
    p_rs.add_argument("--report-path", default=None)

    # batch-score-save (v3: saves to batch_scores table)
    p_bs = subparsers.add_parser("batch-score-save", help="Save batch A/B-score results")
    p_bs.add_argument("--scores", required=True,
                      help='JSON array: [{"stock_code":"1234","company_name":"...","tse_industry":"...","threshold_profile":"...","valuation_score":4.2,"business_score":3.5,"gate_result":"pass","metrics":{}}]')
    p_bs.add_argument("--source-info", default=None, help="Source info (optional)")

    # criteria-list
    subparsers.add_parser("criteria-list", help="List screening criteria")

    # criteria-upsert
    p_cu = subparsers.add_parser("criteria-upsert", help="Upsert screening criteria")
    p_cu.add_argument("--criteria-id", required=True)
    p_cu.add_argument("--name", required=True)
    p_cu.add_argument("--indicator", required=True)
    p_cu.add_argument("--threshold", required=True)
    p_cu.add_argument("--direction", required=True, choices=["lte", "gte", "eq", "between"])
    p_cu.add_argument("--reason", required=True)

    # search-analyses (v3: tier/profile filters)
    p_sa = subparsers.add_parser("search-analyses", help="Search analyses")
    p_sa.add_argument("--stock-code", default=None)
    p_sa.add_argument("--depth", default=None)
    p_sa.add_argument("--tier", default=None)
    p_sa.add_argument("--profile", default=None)

    # get-latest-analysis
    p_gla = subparsers.add_parser("get-latest-analysis", help="Get latest analysis")
    p_gla.add_argument("--stock-code", required=True)

    # search-batch-scores (v3 new)
    p_sbs = subparsers.add_parser("search-batch-scores", help="Search batch scores")
    p_sbs.add_argument("--batch-id", default=None)
    p_sbs.add_argument("--stock-code", default=None)
    p_sbs.add_argument("--profile", default=None)
    p_sbs.add_argument("--min-score", default=None)

    args = parser.parse_args()

    dispatch = {
        "init": cmd_init,
        "scan-create": cmd_scan_create,
        "scan-result-add": cmd_scan_result_add,
        "batch-score-save": cmd_batch_score_save,
        "analyze-save": cmd_analyze_save,
        "review-save": cmd_review_save,
        "criteria-list": cmd_criteria_list,
        "criteria-upsert": cmd_criteria_upsert,
        "search-analyses": cmd_search_analyses,
        "get-latest-analysis": cmd_get_latest_analysis,
        "search-batch-scores": cmd_search_batch_scores,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
