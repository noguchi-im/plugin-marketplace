"""BOJ 時系列統計データ検索サイト API 共通ユーティリティ。

他の API スクリプト（boj_metadata.py, boj_code.py, boj_layer.py）から import して使用する。
"""

import gzip
import json
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://www.stat-search.boj.or.jp/api/v1"

ERROR_GUIDE = {
    "M181001E": "パラメータ不正。系列コードに DB 名プレフィクス（例: IR01'）が付いていないか確認してください。",
    "M181005E": "DB 名が不正です。正しい DB 名を指定してください。",
    "M181007E": "系列数が 1250 件を超えています。階層を絞り込むか、コード API で 250 件ずつ指定してください。",
    "M181013E": "指定した系列コードが存在しません。explore で正しい系列コードを確認してください。",
    "M181014E": "異なる期種の系列コードが混在しています。同じ期種の系列のみを指定してください。",
    "M181030I": "該当データがありません。期間が収録範囲外の可能性があります。",
    "M181090S": "サーバーエラーです。時間をおいてリトライしてください。",
    "M181091S": "データベースアクセスエラーです。時間をおいてリトライしてください。",
}


def build_url(endpoint: str, params: dict) -> str:
    """API リクエスト URL を構築する。"""
    return f"{BASE_URL}/{endpoint}?{urllib.parse.urlencode(params)}"


def fetch(url: str) -> dict | str:
    """HTTP GET を実行し、JSON またはテキストを返す。gzip 対応。"""
    req = urllib.request.Request(url, headers={"Accept-Encoding": "gzip"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            if resp.headers.get("Content-Encoding") == "gzip":
                data = gzip.decompress(data)
            content_type = resp.headers.get("Content-Type", "")
            if "json" in content_type:
                return json.loads(data.decode("utf-8"))
            else:
                try:
                    return data.decode("utf-8")
                except UnicodeDecodeError:
                    return data.decode("shift_jis")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"STATUS": e.code, "MESSAGE": body}
    except urllib.error.URLError as e:
        return {"STATUS": 0, "MESSAGE": f"接続エラー: {e.reason}"}
    except Exception as e:
        return {"STATUS": 0, "MESSAGE": f"予期しないエラー: {e}"}


def check_error(result: dict) -> bool:
    """エラーがあれば stderr に出力して True を返す。"""
    if not isinstance(result, dict):
        return False
    status = result.get("STATUS")
    if status is None or status == 200:
        return False
    msg_id = result.get("MESSAGEID", "")
    message = result.get("MESSAGE", "不明なエラー")
    guide = ERROR_GUIDE.get(msg_id, "")
    err = {"status": status, "message_id": msg_id, "message": message}
    if guide:
        err["guide"] = guide
    print(json.dumps(err, ensure_ascii=False), file=sys.stderr)
    return True


def output(result) -> None:
    """結果を stdout に出力する。"""
    if isinstance(result, dict):
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(result)


def strip_db_prefix(code: str) -> str:
    """系列コードから DB 名プレフィクス（例: IR01'MADR1Z@D → MADR1Z@D）を除去する。"""
    if "'" in code:
        return code.split("'", 1)[1]
    return code
