#!/usr/bin/env python3
"""BOJ コード API クライアント。

系列コードを指定して時系列統計データを取得する。

Usage:
    python3 boj_code.py <db> <codes> [--start DATE] [--end DATE] [--format json|csv] [--start-position N]

Examples:
    python3 boj_code.py CO TK99F1000601GCQ01000,TK99F2000601GCQ01000 --start 202401 --end 202504
    python3 boj_code.py IR01 MADR1Z@D --format csv
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from boj_common import build_url, check_error, fetch, output, strip_db_prefix


def main():
    parser = argparse.ArgumentParser(description="BOJ コード API")
    parser.add_argument("db", help="DB 名")
    parser.add_argument("codes", help="系列コード（カンマ区切り）")
    parser.add_argument("--start", help="開始期（YYYY or YYYYMM or YYYYQQ）")
    parser.add_argument("--end", help="終了期")
    parser.add_argument("--format", default="json", choices=["json", "csv"])
    parser.add_argument("--start-position", type=int, help="検索開始位置")
    args = parser.parse_args()

    codes = ",".join(strip_db_prefix(c.strip()) for c in args.codes.split(","))
    params = {"format": args.format, "lang": "jp", "db": args.db, "code": codes}
    if args.start:
        params["startDate"] = args.start
    if args.end:
        params["endDate"] = args.end
    if args.start_position:
        params["startPosition"] = args.start_position

    url = build_url("getDataCode", params)
    result = fetch(url)
    if isinstance(result, dict) and check_error(result):
        sys.exit(1)
    output(result)


if __name__ == "__main__":
    main()
