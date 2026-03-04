#!/usr/bin/env python3
"""経験ジャーナル操作スクリプト — ChromaDB ベース

report-collector の操作経験（収集パターン・ソース実績・検索戦略）を
ChromaDB に蓄積し、意味的類似検索で引き出す。

Usage:
    python journal.py init
    python journal.py find-patterns <text> [n]
    python journal.py record-pattern <signature> <decomposition_json> [sources_json]
    python journal.py get-source-stats [source_id]
    python journal.py record-attempt <source_id> <success> [fetch_time_ms] [failure_reason]
    python journal.py find-queries <text> [n]
    python journal.py record-query <topic> <query> <is_effective> [note]
    python journal.py stats
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import chromadb

# --- 定数 ---

DB_DIR = Path(__file__).resolve().parents[2] / "home" / "finance" / "report-collector" / "journal"
COLLECTION_NAME = "experience"
MAX_PATTERNS = 200
MAX_QUERIES = 500


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _client() -> chromadb.ClientAPI:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(DB_DIR))


def _collection(client: chromadb.ClientAPI) -> chromadb.Collection:
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


# --- コマンド ---


def cmd_init() -> dict:
    """DB を初期化する。"""
    client = _client()
    col = _collection(client)
    return {"status": "ok", "path": str(DB_DIR), "count": col.count()}


def cmd_find_patterns(text: str, n: int = 3) -> dict:
    """要求テキストに意味的に類似するパターンを返す。"""
    client = _client()
    col = _collection(client)

    count = col.count()
    if count == 0:
        return {"patterns": [], "note": "no patterns recorded yet"}

    # type=pattern のみで検索
    results = col.query(
        query_texts=[text],
        where={"type": "pattern"},
        n_results=min(n, count),
        include=["documents", "metadatas", "distances"],
    )

    patterns = []
    if results["ids"] and results["ids"][0]:
        for i, id_ in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i]
            patterns.append({
                "id": id_,
                "signature": meta.get("signature", ""),
                "decomposition": json.loads(meta.get("decomposition", "[]")),
                "effective_sources": json.loads(meta.get("effective_sources", "[]")),
                "times_used": meta.get("times_used", 0),
                "last_used": meta.get("last_used", ""),
                "distance": round(results["distances"][0][i], 4),
            })

    return {"patterns": patterns}


def cmd_record_pattern(signature: str, decomposition_json: str, sources_json: str = "[]") -> dict:
    """パターンを記録する。既存なら更新。"""
    client = _client()
    col = _collection(client)
    now = _now()

    # 同じ signature の既存パターンを探す
    existing = col.get(
        where={"$and": [{"type": "pattern"}, {"signature": signature}]},
        include=["metadatas"],
    )

    if existing["ids"]:
        # 既存 → times_used 加算、last_used 更新
        doc_id = existing["ids"][0]
        old_meta = existing["metadatas"][0]
        times_used = old_meta.get("times_used", 0) + 1

        decomposition = json.loads(decomposition_json)
        sources = json.loads(sources_json)

        description = f"{signature}: {', '.join(decomposition)}"
        col.upsert(
            ids=[doc_id],
            documents=[description],
            metadatas=[{
                "type": "pattern",
                "signature": signature,
                "decomposition": json.dumps(decomposition, ensure_ascii=False),
                "effective_sources": json.dumps(sources, ensure_ascii=False),
                "times_used": times_used,
                "last_used": now,
                "created_at": old_meta.get("created_at", now),
            }],
        )
        return {"status": "updated", "id": doc_id, "times_used": times_used}
    else:
        # 新規作成
        decomposition = json.loads(decomposition_json)
        sources = json.loads(sources_json)

        # ID を決定
        all_patterns = col.get(where={"type": "pattern"}, include=[])
        next_num = len(all_patterns["ids"]) + 1
        doc_id = f"pattern-{next_num:03d}"

        description = f"{signature}: {', '.join(decomposition)}"
        col.add(
            ids=[doc_id],
            documents=[description],
            metadatas=[{
                "type": "pattern",
                "signature": signature,
                "decomposition": json.dumps(decomposition, ensure_ascii=False),
                "effective_sources": json.dumps(sources, ensure_ascii=False),
                "times_used": 1,
                "last_used": now,
                "created_at": now,
            }],
        )

        # 淘汰チェック
        _evict_patterns(col)

        return {"status": "created", "id": doc_id}


def cmd_get_source_stats(source_id: str | None = None) -> dict:
    """ソース実績を取得する。"""
    client = _client()
    col = _collection(client)

    if source_id:
        results = col.get(
            ids=[f"source-{source_id}"],
            include=["metadatas"],
        )
        if not results["ids"]:
            return {"stats": [], "note": f"no stats for {source_id}"}

        meta = results["metadatas"][0]
        success_rate = (meta["successes"] / meta["total_attempts"]
                        if meta["total_attempts"] > 0 else 0)
        return {"stats": [{
            "source_id": meta.get("source_id", source_id),
            "total_attempts": meta.get("total_attempts", 0),
            "successes": meta.get("successes", 0),
            "failures": meta.get("failures", 0),
            "success_rate": round(success_rate, 3),
            "avg_fetch_time_ms": meta.get("avg_fetch_time_ms", 0),
            "last_failure_at": meta.get("last_failure_at", ""),
            "last_failure_reason": meta.get("last_failure_reason", ""),
        }]}
    else:
        results = col.get(
            where={"type": "source_stats"},
            include=["metadatas"],
        )
        stats = []
        for meta in results["metadatas"]:
            success_rate = (meta["successes"] / meta["total_attempts"]
                            if meta["total_attempts"] > 0 else 0)
            stats.append({
                "source_id": meta.get("source_id", ""),
                "total_attempts": meta.get("total_attempts", 0),
                "successes": meta.get("successes", 0),
                "failures": meta.get("failures", 0),
                "success_rate": round(success_rate, 3),
                "avg_fetch_time_ms": meta.get("avg_fetch_time_ms", 0),
                "last_failure_at": meta.get("last_failure_at", ""),
                "last_failure_reason": meta.get("last_failure_reason", ""),
            })
        return {"stats": stats}


def cmd_record_attempt(
    source_id: str,
    success: bool,
    fetch_time_ms: int | None = None,
    failure_reason: str | None = None,
) -> dict:
    """ソース試行結果を記録する。"""
    client = _client()
    col = _collection(client)
    now = _now()
    doc_id = f"source-{source_id}"

    existing = col.get(ids=[doc_id], include=["metadatas", "documents"])

    if existing["ids"]:
        meta = existing["metadatas"][0]
        total = meta.get("total_attempts", 0) + 1
        successes = meta.get("successes", 0) + (1 if success else 0)
        failures = meta.get("failures", 0) + (0 if success else 1)

        # 移動平均で avg_fetch_time を更新
        old_avg = meta.get("avg_fetch_time_ms", 0) or 0
        if fetch_time_ms is not None and success:
            old_successes = meta.get("successes", 0)
            if old_successes > 0:
                avg = int((old_avg * old_successes + fetch_time_ms) / successes)
            else:
                avg = fetch_time_ms
        else:
            avg = old_avg

        new_meta = {
            "type": "source_stats",
            "source_id": source_id,
            "total_attempts": total,
            "successes": successes,
            "failures": failures,
            "avg_fetch_time_ms": avg,
            "last_failure_at": now if not success else meta.get("last_failure_at", ""),
            "last_failure_reason": (failure_reason or "") if not success else meta.get("last_failure_reason", ""),
            "updated_at": now,
        }

        doc = existing["documents"][0] if existing["documents"] else f"{source_id}"
        # 失敗理由があればドキュメントに反映
        if not success and failure_reason:
            doc = f"{source_id}: {failure_reason}"

        col.upsert(ids=[doc_id], documents=[doc], metadatas=[new_meta])
    else:
        new_meta = {
            "type": "source_stats",
            "source_id": source_id,
            "total_attempts": 1,
            "successes": 1 if success else 0,
            "failures": 0 if success else 1,
            "avg_fetch_time_ms": fetch_time_ms or 0,
            "last_failure_at": now if not success else "",
            "last_failure_reason": (failure_reason or "") if not success else "",
            "updated_at": now,
        }
        doc = f"{source_id}: {failure_reason}" if failure_reason else source_id
        col.add(ids=[doc_id], documents=[doc], metadatas=[new_meta])

    success_rate = new_meta["successes"] / new_meta["total_attempts"] if new_meta["total_attempts"] > 0 else 0
    return {
        "status": "recorded",
        "source_id": source_id,
        "total_attempts": new_meta["total_attempts"],
        "success_rate": round(success_rate, 3),
    }


def cmd_find_queries(text: str, n: int = 5) -> dict:
    """トピックに意味的に類似する検索戦略を返す。"""
    client = _client()
    col = _collection(client)

    count = col.count()
    if count == 0:
        return {"queries": [], "note": "no queries recorded yet"}

    results = col.query(
        query_texts=[text],
        where={"type": "search_query"},
        n_results=min(n, count),
        include=["documents", "metadatas", "distances"],
    )

    queries = []
    if results["ids"] and results["ids"][0]:
        for i, id_ in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i]
            queries.append({
                "id": id_,
                "topic": meta.get("topic", ""),
                "query_template": meta.get("query_template", ""),
                "is_effective": bool(meta.get("is_effective", 0)),
                "success_rate": meta.get("success_rate", 0),
                "total_uses": meta.get("total_uses", 0),
                "note": meta.get("note", ""),
                "distance": round(results["distances"][0][i], 4),
            })

    return {"queries": queries}


def cmd_record_query(topic: str, query: str, is_effective: bool, note: str = "") -> dict:
    """検索クエリを記録する。"""
    client = _client()
    col = _collection(client)
    now = _now()

    # 同じ topic+query の既存エントリを探す
    existing = col.get(
        where={"$and": [{"type": "search_query"}, {"topic": topic}, {"query_template": query}]},
        include=["metadatas"],
    )

    if existing["ids"]:
        doc_id = existing["ids"][0]
        old_meta = existing["metadatas"][0]
        total_uses = old_meta.get("total_uses", 0) + 1

        # success_rate を更新（有効クエリのみ）
        if is_effective:
            old_rate = old_meta.get("success_rate", 0) or 0
            old_uses = old_meta.get("total_uses", 0)
            new_rate = (old_rate * old_uses + 1.0) / total_uses
        else:
            old_rate = old_meta.get("success_rate", 0) or 0
            old_uses = old_meta.get("total_uses", 0)
            new_rate = (old_rate * old_uses + 0.0) / total_uses

        document = f"{topic}: {query}"
        col.upsert(
            ids=[doc_id],
            documents=[document],
            metadatas=[{
                "type": "search_query",
                "topic": topic,
                "query_template": query,
                "is_effective": 1 if is_effective else 0,
                "success_rate": round(new_rate, 3),
                "total_uses": total_uses,
                "note": note or old_meta.get("note", ""),
                "last_used": now,
                "created_at": old_meta.get("created_at", now),
            }],
        )
        return {"status": "updated", "id": doc_id, "total_uses": total_uses}
    else:
        all_queries = col.get(where={"type": "search_query"}, include=[])
        next_num = len(all_queries["ids"]) + 1
        doc_id = f"query-{next_num:03d}"

        document = f"{topic}: {query}"
        col.add(
            ids=[doc_id],
            documents=[document],
            metadatas=[{
                "type": "search_query",
                "topic": topic,
                "query_template": query,
                "is_effective": 1 if is_effective else 0,
                "success_rate": 1.0 if is_effective else 0.0,
                "total_uses": 1,
                "note": note,
                "last_used": now,
                "created_at": now,
            }],
        )

        _evict_queries(col)

        return {"status": "created", "id": doc_id}


def cmd_stats() -> dict:
    """経験データの統計を返す。"""
    client = _client()
    col = _collection(client)

    total = col.count()

    patterns = col.get(where={"type": "pattern"}, include=[])
    source_stats = col.get(where={"type": "source_stats"}, include=[])
    queries = col.get(where={"type": "search_query"}, include=[])

    return {
        "total": total,
        "patterns": len(patterns["ids"]),
        "source_stats": len(source_stats["ids"]),
        "search_queries": len(queries["ids"]),
        "limits": {
            "patterns": MAX_PATTERNS,
            "search_queries": MAX_QUERIES,
        },
    }


# --- 淘汰 ---


def _evict_patterns(col: chromadb.Collection) -> None:
    """patterns が上限を超えたら、使用頻度が低く古いものを削除する。"""
    all_p = col.get(where={"type": "pattern"}, include=["metadatas"])
    if len(all_p["ids"]) <= MAX_PATTERNS:
        return

    # (id, times_used, last_used) でソートし、下位を削除
    entries = []
    for i, id_ in enumerate(all_p["ids"]):
        meta = all_p["metadatas"][i]
        entries.append((id_, meta.get("times_used", 0), meta.get("last_used", "")))

    entries.sort(key=lambda x: (x[1], x[2]))
    to_delete = len(entries) - MAX_PATTERNS
    delete_ids = [e[0] for e in entries[:to_delete]]
    col.delete(ids=delete_ids)


def _evict_queries(col: chromadb.Collection) -> None:
    """search_queries が上限を超えたら、使用頻度が低く古いものを削除する。"""
    all_q = col.get(where={"type": "search_query"}, include=["metadatas"])
    if len(all_q["ids"]) <= MAX_QUERIES:
        return

    entries = []
    for i, id_ in enumerate(all_q["ids"]):
        meta = all_q["metadatas"][i]
        entries.append((id_, meta.get("total_uses", 0), meta.get("last_used", "")))

    entries.sort(key=lambda x: (x[1], x[2]))
    to_delete = len(entries) - MAX_QUERIES
    delete_ids = [e[0] for e in entries[:to_delete]]
    col.delete(ids=delete_ids)


# --- CLI ---


def main() -> None:
    if len(sys.argv) < 2:
        print(json.dumps({"error": "command required"}, ensure_ascii=False))
        sys.exit(1)

    cmd = sys.argv[1]

    try:
        if cmd == "init":
            result = cmd_init()

        elif cmd == "find-patterns":
            if len(sys.argv) < 3:
                result = {"error": "usage: find-patterns <text> [n]"}
            else:
                text = sys.argv[2]
                n = int(sys.argv[3]) if len(sys.argv) > 3 else 3
                result = cmd_find_patterns(text, n)

        elif cmd == "record-pattern":
            if len(sys.argv) < 4:
                result = {"error": "usage: record-pattern <signature> <decomposition_json> [sources_json]"}
            else:
                sig = sys.argv[2]
                dec = sys.argv[3]
                src = sys.argv[4] if len(sys.argv) > 4 else "[]"
                result = cmd_record_pattern(sig, dec, src)

        elif cmd == "get-source-stats":
            sid = sys.argv[2] if len(sys.argv) > 2 else None
            result = cmd_get_source_stats(sid)

        elif cmd == "record-attempt":
            if len(sys.argv) < 4:
                result = {"error": "usage: record-attempt <source_id> <success> [fetch_time_ms] [failure_reason]"}
            else:
                sid = sys.argv[2]
                success = sys.argv[3].lower() in ("1", "true", "yes")
                ft = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4] else None
                fr = sys.argv[5] if len(sys.argv) > 5 else None
                result = cmd_record_attempt(sid, success, ft, fr)

        elif cmd == "find-queries":
            if len(sys.argv) < 3:
                result = {"error": "usage: find-queries <text> [n]"}
            else:
                text = sys.argv[2]
                n = int(sys.argv[3]) if len(sys.argv) > 3 else 5
                result = cmd_find_queries(text, n)

        elif cmd == "record-query":
            if len(sys.argv) < 5:
                result = {"error": "usage: record-query <topic> <query> <is_effective> [note]"}
            else:
                topic = sys.argv[2]
                query = sys.argv[3]
                eff = sys.argv[4].lower() in ("1", "true", "yes")
                note = sys.argv[5] if len(sys.argv) > 5 else ""
                result = cmd_record_query(topic, query, eff, note)

        elif cmd == "stats":
            result = cmd_stats()

        else:
            result = {"error": f"unknown command: {cmd}"}

    except Exception as e:
        result = {"error": str(e)}
        sys.exit(1)

    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
