#!/usr/bin/env python3
"""BOJ メタデータ API クライアント。

DB 内の系列一覧（系列コード、名称、単位、期種、階層等）を取得する。

Usage:
    python3 boj_metadata.py <db> [--lang jp|en]

Examples:
    python3 boj_metadata.py FM08
    python3 boj_metadata.py CO --lang en
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from boj_common import build_url, check_error, fetch, output


def main():
    parser = argparse.ArgumentParser(description="BOJ メタデータ API")
    parser.add_argument("db", help="DB 名（例: FM08, CO, IR01）")
    parser.add_argument("--lang", default="jp", choices=["jp", "en"])
    args = parser.parse_args()

    url = build_url("getMetadata", {"format": "json", "lang": args.lang, "db": args.db})
    result = fetch(url)
    if check_error(result):
        sys.exit(1)
    output(result)


if __name__ == "__main__":
    main()
