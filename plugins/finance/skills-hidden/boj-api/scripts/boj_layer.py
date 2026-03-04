#!/usr/bin/env python3
"""BOJ 階層 API クライアント。

階層情報を指定して時系列統計データを取得する。

Usage:
    python3 boj_layer.py <db> <frequency> <layer> [--start DATE] [--end DATE] [--format json|csv] [--start-position N]

Examples:
    python3 boj_layer.py BP01 M 1,1,1 --start 202504 --end 202509
    python3 boj_layer.py FF Q 1,1,* --format csv
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from boj_common import build_url, check_error, fetch, output


def main():
    parser = argparse.ArgumentParser(description="BOJ 階層 API")
    parser.add_argument("db", help="DB 名")
    parser.add_argument("frequency", help="期種（CY,FY,CH,FH,Q,M,W,D）")
    parser.add_argument("layer", help="階層情報（カンマ区切り、* 可）")
    parser.add_argument("--start", help="開始期")
    parser.add_argument("--end", help="終了期")
    parser.add_argument("--format", default="json", choices=["json", "csv"])
    parser.add_argument("--start-position", type=int, help="検索開始位置")
    args = parser.parse_args()

    params = {
        "format": args.format,
        "lang": "jp",
        "db": args.db,
        "frequency": args.frequency,
        "layer": args.layer,
    }
    if args.start:
        params["startDate"] = args.start
    if args.end:
        params["endDate"] = args.end
    if args.start_position:
        params["startPosition"] = args.start_position

    url = build_url("getDataLayer", params)
    result = fetch(url)
    if isinstance(result, dict) and check_error(result):
        sys.exit(1)
    output(result)


if __name__ == "__main__":
    main()
