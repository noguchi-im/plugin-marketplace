#!/usr/bin/env python3
"""report-store DB operations CLI.

All output is JSON: {"status": "ok", ...} or {"status": "error", "message": "..."}.
Exit code 0 on success, 1 on error.

Subcommands:
    init          Initialize DB with schema and seed data
    generate-id   Generate next report ID for a given date
    save          Save report metadata (reads JSON from stdin)
    search        Search reports by conditions
    retrieve      Retrieve a report's full metadata
    score         Update report scores
"""

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime

DEFAULT_DB_PATH = "home/finance/report-store/index/report-index.db"

# reliability_score: source_tier -> points
TIER_SCORES = {1: 5, 2: 3, 3: 1}


def _connect(db_path):
    """Create a DB connection with foreign keys enabled."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def _ok(data=None):
    """Print success JSON and exit."""
    result = {"status": "ok"}
    if data:
        result.update(data)
    print(json.dumps(result, ensure_ascii=False, default=str))
    sys.exit(0)


def _error(message):
    """Print error JSON to stderr and exit with code 1."""
    print(json.dumps({"status": "error", "message": message},
                     ensure_ascii=False), file=sys.stderr)
    sys.exit(1)


# ============================================================
# init
# ============================================================
def cmd_init(args):
    db_path = args.db_path
    init_sql = args.init_sql

    if not os.path.isfile(init_sql):
        _error(f"init.sql not found: {init_sql}")

    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        with open(init_sql, encoding="utf-8") as f:
            conn.executescript(f.read())
        conn.close()
        _ok({"message": "DB initialized", "db_path": db_path})
    except sqlite3.Error as e:
        conn.close()
        _error(f"DB init failed: {e}")


# ============================================================
# generate-id
# ============================================================
def cmd_generate_id(args):
    db_path = args.db_path
    date = args.date

    if not os.path.isfile(db_path):
        _error(f"DB not found: {db_path}")

    conn = _connect(db_path)
    try:
        cursor = conn.execute(
            "SELECT COUNT(*) FROM reports WHERE date = ?", (date,))
        count = cursor.fetchone()[0]
        report_id = f"rpt-{date.replace('-', '')}-{count + 1:03d}"
        conn.close()
        _ok({"id": report_id, "date": date, "seq": count + 1})
    except sqlite3.Error as e:
        conn.close()
        _error(f"ID generation failed: {e}")


# ============================================================
# save
# ============================================================
def cmd_save(args):
    db_path = args.db_path

    if not os.path.isfile(db_path):
        _error(f"DB not found: {db_path}. Run 'init' first.")

    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        _error(f"Invalid JSON input: {e}")

    # Validate required fields
    required = ["id", "provenance_id", "domain_id", "subject", "date", "file_path"]
    missing = [f for f in required if not data.get(f)]
    if missing:
        _error(f"Missing required fields: {', '.join(missing)}")

    conn = _connect(db_path)
    try:
        # Validate provenance_id
        row = conn.execute(
            "SELECT 1 FROM provenances WHERE id = ?",
            (data["provenance_id"],)).fetchone()
        if not row:
            _error(f"Invalid provenance_id: {data['provenance_id']}")

        # Validate domain_id
        row = conn.execute(
            "SELECT 1 FROM domains WHERE id = ?",
            (data["domain_id"],)).fetchone()
        if not row:
            _error(f"Invalid domain_id: {data['domain_id']}")

        # Validate tags
        tags = data.get("tags", [])
        for tag in tags:
            row = conn.execute(
                "SELECT 1 FROM tags WHERE name = ?", (tag,)).fetchone()
            if not row:
                _error(f"Invalid tag: {tag}")

        # Begin transaction
        conn.execute("BEGIN")

        # Insert report
        conn.execute("""
            INSERT INTO reports
                (id, provenance_id, domain_id, subject, date,
                 incomplete, analyst, updates, file_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data["id"],
            data["provenance_id"],
            data["domain_id"],
            data["subject"],
            data["date"],
            data.get("incomplete", 0),
            data.get("analyst"),
            data.get("updates"),
            data["file_path"],
            datetime.now().isoformat(),
        ))

        # Insert tags
        for tag in tags:
            conn.execute(
                "INSERT INTO report_tags (report_id, tag_name) VALUES (?, ?)",
                (data["id"], tag))

        # Insert sources
        sources = data.get("sources", [])
        for src in sources:
            conn.execute("""
                INSERT INTO report_sources
                    (report_id, source_name, source_url, source_tier,
                     as_of, retrieved_at, score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                data["id"],
                src["source_name"],
                src.get("source_url"),
                src.get("source_tier"),
                src.get("as_of"),
                src.get("retrieved_at"),
                src.get("score"),
            ))

        # Insert relations
        relations = data.get("relations", [])
        for rel in relations:
            conn.execute("""
                INSERT INTO report_relations
                    (report_id, related_id, relation_type)
                VALUES (?, ?, ?)
            """, (data["id"], rel["related_id"], rel["relation_type"]))

        # Calculate reliability_score from source tiers
        if sources:
            valid_tiers = [s["source_tier"] for s in sources
                          if s.get("source_tier") in TIER_SCORES]
            if valid_tiers:
                avg = round(
                    sum(TIER_SCORES[t] for t in valid_tiers) / len(valid_tiers))
                conn.execute(
                    "UPDATE reports SET reliability_score = ? WHERE id = ?",
                    (avg, data["id"]))

        conn.commit()
        conn.close()
        _ok({"id": data["id"], "file_path": data["file_path"]})

    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        _error(f"Save failed: {e}")


# ============================================================
# search
# ============================================================
def cmd_search(args):
    db_path = args.db_path

    if not os.path.isfile(db_path):
        _ok({"count": 0, "results": []})

    conn = _connect(db_path)
    try:
        where_clauses = []
        params = []

        field_map = {
            "provenance_id": "r.provenance_id",
            "domain_id": "r.domain_id",
            "subject": "r.subject",
            "analyst": "r.analyst",
        }
        for attr, col in field_map.items():
            val = getattr(args, attr.replace("-", "_"), None)
            if val:
                where_clauses.append(f"{col} = ?")
                params.append(val)

        if args.incomplete is not None:
            where_clauses.append("r.incomplete = ?")
            params.append(args.incomplete)

        if args.keyword:
            where_clauses.append("r.subject LIKE ?")
            params.append(f"%{args.keyword}%")

        if args.date_from:
            where_clauses.append("r.date >= ?")
            params.append(args.date_from)

        if args.date_to:
            where_clauses.append("r.date <= ?")
            params.append(args.date_to)

        if args.tag_name:
            where_clauses.append(
                "EXISTS (SELECT 1 FROM report_tags rt "
                "WHERE rt.report_id = r.id AND rt.tag_name = ?)")
            params.append(args.tag_name)

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"
        query = f"SELECT r.* FROM reports r WHERE {where_sql} ORDER BY r.date DESC"

        rows = conn.execute(query, params).fetchall()
        results = []
        for row in rows:
            report = dict(row)
            tag_rows = conn.execute(
                "SELECT tag_name FROM report_tags WHERE report_id = ?",
                (report["id"],)).fetchall()
            report["tags"] = [t["tag_name"] for t in tag_rows]
            results.append(report)

        conn.close()
        _ok({"count": len(results), "results": results})

    except sqlite3.Error as e:
        conn.close()
        _error(f"Search failed: {e}")


# ============================================================
# retrieve
# ============================================================
def cmd_retrieve(args):
    db_path = args.db_path
    report_id = args.id

    if not os.path.isfile(db_path):
        _error(f"DB not found: {db_path}")

    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
        if not row:
            conn.close()
            _error(f"Report not found: {report_id}")

        report = dict(row)

        tag_rows = conn.execute(
            "SELECT tag_name FROM report_tags WHERE report_id = ?",
            (report_id,)).fetchall()
        report["tags"] = [t["tag_name"] for t in tag_rows]

        src_rows = conn.execute(
            "SELECT * FROM report_sources WHERE report_id = ?",
            (report_id,)).fetchall()
        report["sources"] = [dict(s) for s in src_rows]

        rel_rows = conn.execute(
            "SELECT * FROM report_relations WHERE report_id = ?",
            (report_id,)).fetchall()
        report["relations"] = [dict(r) for r in rel_rows]

        conn.close()
        _ok({"report": report})

    except sqlite3.Error as e:
        conn.close()
        _error(f"Retrieve failed: {e}")


# ============================================================
# score
# ============================================================
def cmd_score(args):
    db_path = args.db_path
    report_id = args.id

    if not os.path.isfile(db_path):
        _error(f"DB not found: {db_path}")

    conn = _connect(db_path)
    try:
        row = conn.execute(
            "SELECT 1 FROM reports WHERE id = ?", (report_id,)).fetchone()
        if not row:
            conn.close()
            _error(f"Report not found: {report_id}")

        updates = []
        params = []
        score_fields = {
            "quality_score": args.quality_score,
            "usefulness_score": args.usefulness_score,
            "reliability_score": args.reliability_score,
        }

        for field, val in score_fields.items():
            if val is not None:
                if not (1 <= val <= 5):
                    conn.close()
                    _error(f"{field} must be 1-5, got {val}")
                updates.append(f"{field} = ?")
                params.append(val)

        if not updates:
            conn.close()
            _error("No scores specified")

        params.append(report_id)
        conn.execute(
            f"UPDATE reports SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()

        row = conn.execute(
            "SELECT quality_score, usefulness_score, reliability_score "
            "FROM reports WHERE id = ?", (report_id,)).fetchone()
        conn.close()
        _ok({"id": report_id, "scores": dict(row)})

    except sqlite3.Error as e:
        conn.rollback()
        conn.close()
        _error(f"Score update failed: {e}")


# ============================================================
# CLI entry point
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="report-store DB operations")
    parser.add_argument("--db-path", default=DEFAULT_DB_PATH,
                        help=f"Path to SQLite DB (default: {DEFAULT_DB_PATH})")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = subparsers.add_parser("init", help="Initialize DB")
    p_init.add_argument("--init-sql", required=True,
                        help="Path to init.sql")

    # generate-id
    p_genid = subparsers.add_parser("generate-id",
                                     help="Generate next report ID")
    p_genid.add_argument("--date", required=True,
                         help="Report date (YYYY-MM-DD)")

    # save
    subparsers.add_parser("save",
                          help="Save report metadata (reads JSON from stdin)")

    # search
    p_search = subparsers.add_parser("search", help="Search reports")
    p_search.add_argument("--provenance-id")
    p_search.add_argument("--domain-id")
    p_search.add_argument("--subject")
    p_search.add_argument("--analyst")
    p_search.add_argument("--tag-name")
    p_search.add_argument("--date-from")
    p_search.add_argument("--date-to")
    p_search.add_argument("--incomplete", type=int)
    p_search.add_argument("--keyword")

    # retrieve
    p_retrieve = subparsers.add_parser("retrieve",
                                       help="Retrieve report metadata")
    p_retrieve.add_argument("--id", required=True)

    # score
    p_score = subparsers.add_parser("score", help="Update report scores")
    p_score.add_argument("--id", required=True)
    p_score.add_argument("--quality-score", type=int)
    p_score.add_argument("--usefulness-score", type=int)
    p_score.add_argument("--reliability-score", type=int)

    args = parser.parse_args()

    dispatch = {
        "init": cmd_init,
        "generate-id": cmd_generate_id,
        "save": cmd_save,
        "search": cmd_search,
        "retrieve": cmd_retrieve,
        "score": cmd_score,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
