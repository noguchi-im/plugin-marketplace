"""Office 文書（.docx 等）を展開し、XML を整形する。

機能:
- ZIP 展開
- 全 XML ファイルの pretty-print
- 同一書式の隣接 Run 結合（merge_runs）
- 同一著者の隣接変更履歴統合（simplify_redlines）
- スマートクォートの XML エンティティ変換
"""

from __future__ import annotations

import argparse
import os
import re
import sys
import zipfile
from pathlib import Path

try:
    from defusedxml import ElementTree as SafeET
except ImportError:
    print(
        "Error: defusedxml is not installed. Run: pip install defusedxml",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    from lxml import etree
except ImportError:
    print(
        "Error: lxml is not installed. Run: pip install lxml",
        file=sys.stderr,
    )
    sys.exit(1)

# scripts/ をモジュール検索パスに追加（実行時のカレントディレクトリに依存しない）
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent)
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

from office.helpers.merge_runs import merge_runs
from office.helpers.simplify_redlines import simplify_redlines

# スマートクォート置換マップ
SMART_QUOTES = {
    "\u2018": "&#x2018;",  # '
    "\u2019": "&#x2019;",  # '
    "\u201c": "&#x201C;",  # "
    "\u201d": "&#x201D;",  # "
}


def _replace_smart_quotes(text: str) -> str:
    """スマートクォートを XML エンティティに変換する。"""
    for char, entity in SMART_QUOTES.items():
        text = text.replace(char, entity)
    return text


def _pretty_print_xml(xml_bytes: bytes) -> bytes:
    """XML を整形して返す。パース不能な場合はそのまま返す。"""
    try:
        tree = etree.fromstring(xml_bytes)
        etree.indent(tree, space="  ")
        return etree.tostring(tree, xml_declaration=True, encoding="UTF-8")
    except etree.XMLSyntaxError:
        return xml_bytes


def _process_document_xml(xml_bytes: bytes) -> bytes:
    """document.xml に対して Run 結合と変更履歴統合を実行する。"""
    try:
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError:
        return xml_bytes

    merged = merge_runs(root)
    simplified = simplify_redlines(root)

    if merged > 0 or simplified > 0:
        info_parts = []
        if merged > 0:
            info_parts.append(f"merged {merged} runs")
        if simplified > 0:
            info_parts.append(f"simplified {simplified} redlines")
        print(f"  document.xml: {', '.join(info_parts)}")

    etree.indent(root, space="  ")
    return etree.tostring(root, xml_declaration=True, encoding="UTF-8")


def unpack(src: Path, dest: Path) -> None:
    """Office 文書を展開し、XML を整形する。"""
    if not src.exists():
        print(f"Error: file not found: {src}", file=sys.stderr)
        sys.exit(1)

    if not zipfile.is_zipfile(src):
        print(f"Error: not a valid ZIP/Office file: {src}", file=sys.stderr)
        sys.exit(1)

    dest.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(src, "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                (dest / info.filename).mkdir(parents=True, exist_ok=True)
                continue

            data = zf.read(info.filename)
            out_path = dest / info.filename
            out_path.parent.mkdir(parents=True, exist_ok=True)

            if info.filename.endswith(".xml") or info.filename.endswith(".rels"):
                # XML 整形
                if info.filename.endswith("document.xml"):
                    data = _process_document_xml(data)
                else:
                    data = _pretty_print_xml(data)

                # スマートクォート変換
                text = data.decode("utf-8", errors="replace")
                text = _replace_smart_quotes(text)
                data = text.encode("utf-8")

            out_path.write_bytes(data)
            print(f"  {info.filename}")

    print(f"\nUnpacked to: {dest}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Office 文書（.docx 等）を展開し、XML を整形する。",
        epilog="例: python unpack.py document.docx unpacked/",
    )
    parser.add_argument("input", type=Path, help="入力ファイル（.docx 等）")
    parser.add_argument("output", type=Path, help="展開先ディレクトリ")
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    unpack(args.input, args.output)
