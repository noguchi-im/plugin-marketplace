"""展開済み Office 文書ディレクトリを .docx に再パッキングする。

機能:
- 全 XML の構文チェック
- 自動修復（durableId, xml:space="preserve"）
- ZIP 再パッキング（オリジナルのメディアファイルを保持）
"""

from __future__ import annotations

import argparse
import os
import random
import re
import sys
import zipfile
from pathlib import Path

try:
    from lxml import etree
except ImportError:
    print(
        "Error: lxml is not installed. Run: pip install lxml",
        file=sys.stderr,
    )
    sys.exit(1)

WML_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
MAX_DURABLE_ID = 0x7FFFFFFF


def _auto_repair_xml(xml_bytes: bytes, filename: str) -> tuple[bytes, list[str]]:
    """XML の自動修復を行う。修復内容のリストを返す。"""
    repairs: list[str] = []
    try:
        root = etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError:
        return xml_bytes, repairs

    # durableId の修復: >= 0x7FFFFFFF の場合は再生成
    for elem in root.iter():
        durable_id = elem.get("durableId")
        if durable_id is not None:
            try:
                val = int(durable_id, 16) if len(durable_id) == 8 else int(durable_id)
                if val >= MAX_DURABLE_ID:
                    new_id = f"{random.randint(0, MAX_DURABLE_ID - 1):08X}"
                    elem.set("durableId", new_id)
                    repairs.append(
                        f"durableId {durable_id} -> {new_id} in {elem.tag}"
                    )
            except ValueError:
                pass

    # xml:space="preserve" の追加: w:t 要素にスペースが含まれる場合
    tag_t = f"{{{WML_NS}}}t"
    for t_elem in root.iter(tag_t):
        if t_elem.text and (" " in t_elem.text or "\t" in t_elem.text):
            if t_elem.get(XML_SPACE) is None:
                t_elem.set(XML_SPACE, "preserve")
                repairs.append(f"added xml:space='preserve' to w:t")

    if repairs:
        return etree.tostring(root, xml_declaration=True, encoding="UTF-8"), repairs
    return xml_bytes, repairs


def _validate_xml(xml_bytes: bytes, filename: str) -> list[str]:
    """XML の構文チェック。エラーメッセージのリストを返す。"""
    errors: list[str] = []
    try:
        etree.fromstring(xml_bytes)
    except etree.XMLSyntaxError as e:
        errors.append(f"{filename}: XML syntax error: {e}")
    return errors


def pack(
    src: Path,
    dest: Path,
    original: Path | None = None,
    auto_repair: bool = True,
) -> None:
    """展開済みディレクトリを Office 文書に再パッキングする。"""
    if not src.is_dir():
        print(f"Error: directory not found: {src}", file=sys.stderr)
        sys.exit(1)

    all_errors: list[str] = []
    all_repairs: list[str] = []

    # [Content_Types].xml は ZIP のルートに必須
    content_types = src / "[Content_Types].xml"
    if not content_types.exists():
        print(
            f"Error: [Content_Types].xml not found in {src}",
            file=sys.stderr,
        )
        sys.exit(1)

    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for root_dir, dirs, files in os.walk(src):
            for filename in files:
                filepath = Path(root_dir) / filename
                arcname = str(filepath.relative_to(src))

                data = filepath.read_bytes()

                if filename.endswith(".xml") or filename.endswith(".rels"):
                    # XML 構文チェック
                    errors = _validate_xml(data, arcname)
                    all_errors.extend(errors)

                    # 自動修復
                    if auto_repair and not errors:
                        data, repairs = _auto_repair_xml(data, arcname)
                        all_repairs.extend(repairs)

                zf.writestr(arcname, data)

    # 結果報告
    if all_repairs:
        print("Auto-repairs applied:")
        for repair in all_repairs:
            print(f"  {repair}")

    if all_errors:
        print("\nXML errors found:", file=sys.stderr)
        for error in all_errors:
            print(f"  {error}", file=sys.stderr)
        print(
            f"\nPacked with errors: {dest} (review XML before using)",
            file=sys.stderr,
        )
        sys.exit(1)
    else:
        print(f"\nPacked: {dest}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="展開済み Office 文書ディレクトリを .docx に再パッキングする。",
        epilog="例: python pack.py unpacked/ output.docx --original document.docx",
    )
    parser.add_argument("input", type=Path, help="展開済みディレクトリ")
    parser.add_argument("output", type=Path, help="出力ファイル（.docx）")
    parser.add_argument(
        "--original",
        type=Path,
        default=None,
        help="元の .docx ファイル（メディア等の参照用）",
    )
    parser.add_argument(
        "--no-repair",
        action="store_true",
        help="自動修復を無効にする",
    )
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    pack(args.input, args.output, args.original, auto_repair=not args.no_repair)
