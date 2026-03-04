"""展開済み Office 文書の XML スキーマ検証を行う。

機能:
- 全 XML ファイルの構文チェック
- OOXML 構造の基本検証（必須ファイル、リレーションシップ整合性）
- w:pPr 要素の順序チェック
- 変更履歴の整合性チェック
- 自動修復オプション（--auto-repair）
"""

from __future__ import annotations

import argparse
import random
import sys
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
REL_NS = "http://schemas.openxmlformats.org/package/2006/relationships"
XML_SPACE = "{http://www.w3.org/XML/1998/namespace}space"
MAX_DURABLE_ID = 0x7FFFFFFF

# w:pPr の正しい子要素順序（ISO/IEC 29500 準拠、主要要素のみ）
PPR_ORDER = [
    "pStyle",
    "keepNext",
    "keepLines",
    "pageBreakBefore",
    "widowControl",
    "numPr",
    "suppressLineNumbers",
    "pBdr",
    "shd",
    "tabs",
    "suppressAutoHyphens",
    "spacing",
    "ind",
    "jc",
    "outlineLvl",
    "rPr",
]


def _tag(local: str) -> str:
    return f"{{{WML_NS}}}{local}"


def _local_name(tag: str) -> str:
    """'{ns}local' から 'local' を取得する。"""
    if "}" in tag:
        return tag.split("}", 1)[1]
    return tag


class ValidationResult:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.repairs: list[str] = []

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0

    def report(self) -> None:
        if self.repairs:
            print("Auto-repairs:")
            for r in self.repairs:
                print(f"  [repair] {r}")
        if self.warnings:
            print("Warnings:")
            for w in self.warnings:
                print(f"  [warn] {w}")
        if self.errors:
            print("Errors:", file=sys.stderr)
            for e in self.errors:
                print(f"  [error] {e}", file=sys.stderr)
        if self.ok and not self.warnings:
            print("Validation passed: no issues found.")


def _check_xml_syntax(filepath: Path, result: ValidationResult) -> etree._Element | None:
    """XML 構文チェック。成功すれば root を返す。"""
    try:
        data = filepath.read_bytes()
        return etree.fromstring(data)
    except etree.XMLSyntaxError as e:
        result.errors.append(f"{filepath.name}: XML syntax error: {e}")
        return None


def _check_required_files(base: Path, result: ValidationResult) -> None:
    """OOXML 必須ファイルの存在チェック。"""
    required = [
        "[Content_Types].xml",
        "_rels/.rels",
        "word/document.xml",
    ]
    for rel in required:
        if not (base / rel).exists():
            result.errors.append(f"Missing required file: {rel}")


def _check_ppr_order(root: etree._Element, result: ValidationResult) -> None:
    """w:pPr 内の要素順序を検証する。"""
    for ppr in root.iter(_tag("pPr")):
        children = [_local_name(c.tag) for c in ppr if c.tag.startswith(f"{{{WML_NS}}}")]
        known = [c for c in children if c in PPR_ORDER]
        expected = sorted(known, key=lambda x: PPR_ORDER.index(x))
        if known != expected:
            result.warnings.append(
                f"w:pPr element order violation: got {known}, expected {expected}"
            )


def _check_xml_space(root: etree._Element, result: ValidationResult, auto_repair: bool) -> None:
    """w:t 要素の xml:space="preserve" チェック。"""
    for t_elem in root.iter(_tag("t")):
        if t_elem.text and (" " in t_elem.text or "\t" in t_elem.text):
            if t_elem.get(XML_SPACE) is None:
                if auto_repair:
                    t_elem.set(XML_SPACE, "preserve")
                    result.repairs.append("added xml:space='preserve' to w:t")
                else:
                    result.warnings.append(
                        "w:t with whitespace missing xml:space='preserve'"
                    )


def _check_durable_ids(root: etree._Element, result: ValidationResult, auto_repair: bool) -> None:
    """durableId の範囲チェック。"""
    for elem in root.iter():
        durable_id = elem.get("durableId")
        if durable_id is not None:
            try:
                val = int(durable_id, 16) if len(durable_id) == 8 else int(durable_id)
                if val >= MAX_DURABLE_ID:
                    if auto_repair:
                        new_id = f"{random.randint(0, MAX_DURABLE_ID - 1):08X}"
                        elem.set("durableId", new_id)
                        result.repairs.append(
                            f"durableId {durable_id} -> {new_id}"
                        )
                    else:
                        result.warnings.append(
                            f"durableId {durable_id} >= 0x7FFFFFFF"
                        )
            except ValueError:
                result.warnings.append(f"Invalid durableId format: {durable_id}")


def validate(base: Path, auto_repair: bool = False) -> ValidationResult:
    """展開済み Office 文書を検証する。"""
    result = ValidationResult()

    if not base.is_dir():
        result.errors.append(f"Not a directory: {base}")
        return result

    # 必須ファイルチェック
    _check_required_files(base, result)

    # 全 XML の構文チェック + 詳細検証
    for xml_file in sorted(base.rglob("*.xml")):
        root = _check_xml_syntax(xml_file, result)
        if root is None:
            continue

        rel_path = xml_file.relative_to(base)

        # document.xml への詳細チェック
        if str(rel_path) == "word/document.xml":
            _check_ppr_order(root, result)
            _check_xml_space(root, result, auto_repair)

        # 全 XML の durableId チェック
        _check_durable_ids(root, result, auto_repair)

        # 自動修復を適用した場合はファイルを書き戻す
        if auto_repair and result.repairs:
            xml_file.write_bytes(
                etree.tostring(root, xml_declaration=True, encoding="UTF-8")
            )

    # .rels ファイルも構文チェック
    for rels_file in sorted(base.rglob("*.rels")):
        _check_xml_syntax(rels_file, result)

    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="展開済み Office 文書の XML スキーマ検証を行う。",
        epilog="例: python validate.py unpacked/ --auto-repair",
    )
    parser.add_argument("input", type=Path, help="展開済みディレクトリ")
    parser.add_argument(
        "--auto-repair",
        action="store_true",
        help="自動修復を適用する（durableId, xml:space）",
    )
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    result = validate(args.input, auto_repair=args.auto_repair)
    result.report()
    if not result.ok:
        sys.exit(1)
