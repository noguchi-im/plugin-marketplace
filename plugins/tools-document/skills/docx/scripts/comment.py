"""展開済み .docx にコメントを追加する。

機能:
- comments.xml, commentsExtended.xml, commentsExtensible.xml, commentsIds.xml への
  コメント要素追加
- 返信コメント（--parent）のサポート
- 著者指定（--author）のサポート
- document.xml へのマーカー配置指示の出力

使用後、document.xml にコメントマーカー（w:commentRangeStart, w:commentRangeEnd,
w:r/w:commentReference）を手動で配置する必要がある。
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import uuid
from datetime import datetime, timezone
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
W15_NS = "http://schemas.microsoft.com/office/word/2012/wordml"
W16CID_NS = "http://schemas.microsoft.com/office/word/2016/wordml/cid"
W16CEX_NS = "http://schemas.microsoft.com/office/word/2018/wordml/cex"

NSMAP = {
    "w": WML_NS,
    "w15": W15_NS,
    "w16cid": W16CID_NS,
    "w16cex": W16CEX_NS,
}

SCRIPTS_DIR = Path(__file__).parent
TEMPLATES_DIR = SCRIPTS_DIR / "templates"


def _ensure_file(word_dir: Path, filename: str, template_name: str) -> Path:
    """word/ ディレクトリにファイルが存在しなければテンプレートからコピーする。"""
    filepath = word_dir / filename
    if not filepath.exists():
        template = TEMPLATES_DIR / template_name
        if template.exists():
            shutil.copy2(template, filepath)
            print(f"  Created: word/{filename} (from template)")
        else:
            print(
                f"Error: template not found: {template}",
                file=sys.stderr,
            )
            sys.exit(1)
    return filepath


def _parse_xml(filepath: Path) -> etree._Element:
    """XML ファイルをパースする。"""
    return etree.fromstring(filepath.read_bytes())


def _write_xml(filepath: Path, root: etree._Element) -> None:
    """XML をファイルに書き出す。"""
    etree.indent(root, space="  ")
    filepath.write_bytes(etree.tostring(root, xml_declaration=True, encoding="UTF-8"))


def _now_iso() -> str:
    """現在時刻を ISO 8601 形式で返す。"""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _generate_durable_id() -> str:
    """8 桁の 16 進 durableId を生成する（< 0x7FFFFFFF）。"""
    import random

    return f"{random.randint(0, 0x7FFFFFFE):08X}"


def _generate_guid() -> str:
    """GUID を生成する（{...} 形式）。"""
    return "{" + str(uuid.uuid4()).upper() + "}"


def add_comment(
    unpacked_dir: Path,
    comment_id: int,
    text: str,
    parent_id: int | None = None,
    author: str = "Claude",
) -> None:
    """展開済み .docx にコメントを追加する。"""
    word_dir = unpacked_dir / "word"
    if not word_dir.is_dir():
        print(f"Error: word/ directory not found in {unpacked_dir}", file=sys.stderr)
        sys.exit(1)

    now = _now_iso()

    # --- comments.xml ---
    comments_path = _ensure_file(word_dir, "comments.xml", "comments.xml")
    comments_root = _parse_xml(comments_path)

    comment_elem = etree.SubElement(
        comments_root,
        f"{{{WML_NS}}}comment",
    )
    comment_elem.set(f"{{{WML_NS}}}id", str(comment_id))
    comment_elem.set(f"{{{WML_NS}}}author", author)
    comment_elem.set(f"{{{WML_NS}}}date", now)
    comment_elem.set(f"{{{WML_NS}}}initials", author[0] if author else "C")

    # コメント本文
    p_elem = etree.SubElement(comment_elem, f"{{{WML_NS}}}p")
    r_elem = etree.SubElement(p_elem, f"{{{WML_NS}}}r")
    t_elem = etree.SubElement(r_elem, f"{{{WML_NS}}}t")
    t_elem.text = text
    t_elem.set("{http://www.w3.org/XML/1998/namespace}space", "preserve")

    _write_xml(comments_path, comments_root)
    print(f"  Updated: word/comments.xml (comment id={comment_id})")

    # --- commentsExtended.xml ---
    ext_path = _ensure_file(word_dir, "commentsExtended.xml", "commentsExtended.xml")
    ext_root = _parse_xml(ext_path)

    comment_ex = etree.SubElement(ext_root, f"{{{W15_NS}}}commentEx")
    comment_ex.set(f"{{{W15_NS}}}paraId", _generate_durable_id())
    if parent_id is not None:
        comment_ex.set(f"{{{W15_NS}}}paraIdParent", str(parent_id))
    comment_ex.set(f"{{{W15_NS}}}done", "0")

    _write_xml(ext_path, ext_root)
    print(f"  Updated: word/commentsExtended.xml")

    # --- commentsExtensible.xml ---
    cex_path = _ensure_file(
        word_dir, "commentsExtensible.xml", "commentsExtensible.xml"
    )
    cex_root = _parse_xml(cex_path)

    comment_cex = etree.SubElement(
        cex_root, f"{{{W16CEX_NS}}}comment"
    )
    comment_cex.set(f"{{{W16CEX_NS}}}durableId", _generate_durable_id())
    comment_cex.set(f"{{{W16CEX_NS}}}dateUtc", now)

    _write_xml(cex_path, cex_root)
    print(f"  Updated: word/commentsExtensible.xml")

    # --- commentsIds.xml ---
    cid_path = _ensure_file(word_dir, "commentsIds.xml", "commentsIds.xml")
    cid_root = _parse_xml(cid_path)

    comment_cid = etree.SubElement(cid_root, f"{{{W16CID_NS}}}commentId")
    comment_cid.set(f"{{{W16CID_NS}}}paraId", _generate_durable_id())
    comment_cid.set(f"{{{W16CID_NS}}}durableId", _generate_durable_id())

    _write_xml(cid_path, cid_root)
    print(f"  Updated: word/commentsIds.xml")

    # --- マーカー配置指示 ---
    print(f"\n--- document.xml にマーカーを配置してください ---")
    print(f"コメント対象テキストの前に:")
    print(f'  <w:commentRangeStart w:id="{comment_id}"/>')
    print(f"コメント対象テキストの後に:")
    print(f'  <w:commentRangeEnd w:id="{comment_id}"/>')
    print(f"  <w:r>")
    print(f"    <w:rPr><w:rStyle w:val=\"CommentReference\"/></w:rPr>")
    print(f'    <w:commentReference w:id="{comment_id}"/>')
    print(f"  </w:r>")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="展開済み .docx にコメントを追加する。",
        epilog=(
            "例:\n"
            '  python comment.py unpacked/ 0 "コメント本文"\n'
            '  python comment.py unpacked/ 1 "返信" --parent 0\n'
            '  python comment.py unpacked/ 0 "Text" --author "Author Name"'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input", type=Path, help="展開済みディレクトリ")
    parser.add_argument("id", type=int, help="コメント ID（0 始まり）")
    parser.add_argument("text", help="コメント本文")
    parser.add_argument(
        "--parent",
        type=int,
        default=None,
        help="親コメント ID（返信の場合）",
    )
    parser.add_argument(
        "--author",
        default="Claude",
        help="コメント著者（デフォルト: Claude）",
    )
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    add_comment(args.input, args.id, args.text, args.parent, args.author)
