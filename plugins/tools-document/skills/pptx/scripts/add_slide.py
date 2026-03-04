"""スライドの追加・複製を行う。

既存スライドの複製またはスライドレイアウトからの新規作成を実行し、
Content_Types.xml とリレーションシップを自動更新する。
追加された <p:sldId> 要素を標準出力に出力する。
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import sys
from pathlib import Path

try:
    from defusedxml import minidom as safe_minidom
except ImportError:
    print(
        "Error: defusedxml is not installed. Run: pip install defusedxml",
        file=sys.stderr,
    )
    sys.exit(1)


# --- 名前空間 ---
NS_CONTENT_TYPES = "http://schemas.openxmlformats.org/package/2006/content-types"
NS_PRESENTATION = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS_RELATIONSHIPS = "http://schemas.openxmlformats.org/package/2006/relationships"
REL_TYPE_SLIDE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide"
)
REL_TYPE_SLIDE_LAYOUT = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/slideLayout"
)
REL_TYPE_NOTES_SLIDE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/notesSlide"
)
CONTENT_TYPE_SLIDE = (
    "application/vnd.openxmlformats-officedocument.presentationml.slide+xml"
)


def _parse_xml(path: Path) -> safe_minidom.Document:
    """defusedxml でファイルをパースする。"""
    with open(path, "r", encoding="utf-8") as f:
        return safe_minidom.parseString(f.read())


def _write_xml(doc: safe_minidom.Document, path: Path) -> None:
    """XML を整形して書き出す。"""
    xml_str = doc.toprettyxml(indent="  ", encoding="UTF-8")
    # toprettyxml の余分な空行を除去
    lines = xml_str.decode("utf-8").split("\n")
    cleaned = "\n".join(line for line in lines if line.strip())
    with open(path, "w", encoding="utf-8") as f:
        f.write(cleaned + "\n")


def _find_next_slide_number(slides_dir: Path) -> int:
    """次に使用可能なスライド番号を返す。"""
    existing: list[int] = []
    for f in slides_dir.iterdir():
        m = re.match(r"slide(\d+)\.xml$", f.name)
        if m:
            existing.append(int(m.group(1)))
    return max(existing, default=0) + 1


def _find_next_sld_id(pres_doc: safe_minidom.Document) -> int:
    """presentation.xml 内の次に使用可能な sldId を返す。"""
    sld_ids: list[int] = []
    for elem in pres_doc.getElementsByTagName("p:sldId"):
        id_val = elem.getAttribute("id")
        if id_val:
            sld_ids.append(int(id_val))
    return max(sld_ids, default=255) + 1


def _find_next_rid(rels_doc: safe_minidom.Document) -> str:
    """リレーションシップ内の次に使用可能な rId を返す。"""
    max_id = 0
    for elem in rels_doc.getElementsByTagName("Relationship"):
        rid = elem.getAttribute("Id")
        m = re.match(r"rId(\d+)", rid)
        if m:
            max_id = max(max_id, int(m.group(1)))
    return f"rId{max_id + 1}"


def _is_slide_layout(source_name: str) -> bool:
    """ソースがスライドレイアウトかどうか判定する。"""
    return source_name.startswith("slideLayout")


def add_slide(unpacked_dir: Path, source_name: str) -> str:
    """スライドを追加し、追加された sldId 要素のテキストを返す。"""
    ppt_dir = unpacked_dir / "ppt"
    slides_dir = ppt_dir / "slides"
    rels_dir = ppt_dir / "_rels"

    if not slides_dir.exists():
        print(f"Error: {slides_dir} not found", file=sys.stderr)
        sys.exit(1)

    # ソースファイルの特定
    is_layout = _is_slide_layout(source_name)
    if is_layout:
        source_path = ppt_dir / "slideLayouts" / source_name
    else:
        source_path = slides_dir / source_name

    if not source_path.exists():
        print(f"Error: source file not found: {source_path}", file=sys.stderr)
        sys.exit(1)

    # 新しいスライド番号
    new_num = _find_next_slide_number(slides_dir)
    new_slide_name = f"slide{new_num}.xml"
    new_slide_path = slides_dir / new_slide_name

    # ソースをコピー
    shutil.copy2(source_path, new_slide_path)

    # --- リレーションシップの作成 ---
    slides_rels_dir = slides_dir / "_rels"
    slides_rels_dir.mkdir(exist_ok=True)

    new_slide_rels_path = slides_rels_dir / f"{new_slide_name}.rels"

    if is_layout:
        # レイアウトからの新規作成: レイアウトへの参照のみ
        layout_rel_target = f"../slideLayouts/{source_name}"
        rels_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
            f'<Relationships xmlns="{NS_RELATIONSHIPS}">\n'
            f'  <Relationship Id="rId1" Type="{REL_TYPE_SLIDE_LAYOUT}" '
            f'Target="{layout_rel_target}"/>\n'
            "</Relationships>\n"
        )
        with open(new_slide_rels_path, "w", encoding="utf-8") as f:
            f.write(rels_xml)
    else:
        # 既存スライドの複製: .rels もコピーし、ノート参照は除去
        source_rels_path = slides_rels_dir / f"{source_name}.rels"
        if source_rels_path.exists():
            rels_doc = _parse_xml(source_rels_path)
            # ノート参照を除去（複製先には不要）
            for rel in rels_doc.getElementsByTagName("Relationship"):
                if rel.getAttribute("Type") == REL_TYPE_NOTES_SLIDE:
                    rel.parentNode.removeChild(rel)
            _write_xml(rels_doc, new_slide_rels_path)
        else:
            # .rels が無い場合は空のリレーションシップを作成
            rels_xml = (
                '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                f'<Relationships xmlns="{NS_RELATIONSHIPS}"/>\n'
            )
            with open(new_slide_rels_path, "w", encoding="utf-8") as f:
                f.write(rels_xml)

    # --- Content_Types.xml にエントリ追加 ---
    ct_path = unpacked_dir / "[Content_Types].xml"
    if ct_path.exists():
        ct_doc = _parse_xml(ct_path)
        types_elem = ct_doc.documentElement
        # 既に存在するか確認
        part_name = f"/ppt/slides/{new_slide_name}"
        already_exists = False
        for override in ct_doc.getElementsByTagName("Override"):
            if override.getAttribute("PartName") == part_name:
                already_exists = True
                break
        if not already_exists:
            new_override = ct_doc.createElement("Override")
            new_override.setAttribute("PartName", part_name)
            new_override.setAttribute("ContentType", CONTENT_TYPE_SLIDE)
            types_elem.appendChild(new_override)
            _write_xml(ct_doc, ct_path)

    # --- presentation.xml に sldId 追加 ---
    pres_path = ppt_dir / "presentation.xml"
    pres_doc = _parse_xml(pres_path)

    # presentation.xml の _rels からリレーション追加
    pres_rels_path = rels_dir / "presentation.xml.rels"
    pres_rels_doc = _parse_xml(pres_rels_path)
    new_rid = _find_next_rid(pres_rels_doc)

    new_rel = pres_rels_doc.createElement("Relationship")
    new_rel.setAttribute("Id", new_rid)
    new_rel.setAttribute("Type", REL_TYPE_SLIDE)
    new_rel.setAttribute("Target", f"slides/{new_slide_name}")
    pres_rels_doc.documentElement.appendChild(new_rel)
    _write_xml(pres_rels_doc, pres_rels_path)

    # sldIdLst に追加
    new_sld_id = _find_next_sld_id(pres_doc)
    sld_id_lst = pres_doc.getElementsByTagName("p:sldIdLst")
    if not sld_id_lst:
        print("Error: <p:sldIdLst> not found in presentation.xml", file=sys.stderr)
        sys.exit(1)

    new_sld_id_elem = pres_doc.createElement("p:sldId")
    new_sld_id_elem.setAttribute("id", str(new_sld_id))
    new_sld_id_elem.setAttribute("r:id", new_rid)
    sld_id_lst[0].appendChild(new_sld_id_elem)
    _write_xml(pres_doc, pres_path)

    sld_id_text = f'<p:sldId id="{new_sld_id}" r:id="{new_rid}"/>'
    return sld_id_text


def main() -> None:
    parser = argparse.ArgumentParser(
        description="スライドの追加・複製を行う",
        epilog=(
            "例:\n"
            "  %(prog)s unpacked/ slide2.xml        # slide2 を複製\n"
            "  %(prog)s unpacked/ slideLayout2.xml   # レイアウトから新規作成"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("unpacked_dir", type=Path, help="展開済みディレクトリ")
    parser.add_argument(
        "source",
        help="コピー元 (slide{N}.xml または slideLayout{N}.xml)",
    )
    args = parser.parse_args()

    if not args.unpacked_dir.is_dir():
        print(f"Error: directory not found: {args.unpacked_dir}", file=sys.stderr)
        sys.exit(1)

    sld_id_text = add_slide(args.unpacked_dir, args.source)
    print(f"Added: {sld_id_text}")
    print("presentation.xml の <p:sldIdLst> 内の希望位置に配置してください。")


if __name__ == "__main__":
    main()
