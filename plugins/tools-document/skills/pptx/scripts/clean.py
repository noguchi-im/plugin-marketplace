"""不要ファイルの除去（クリーンアップ）を行う。

presentation.xml の sldIdLst に含まれないスライド、
未参照のメディア・埋め込み・ノートを削除し、
Content_Types.xml を更新する。
"""

from __future__ import annotations

import argparse
import os
import re
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


NS_RELATIONSHIPS = "http://schemas.openxmlformats.org/package/2006/relationships"


def _parse_xml(path: Path) -> safe_minidom.Document:
    """defusedxml でファイルをパースする。"""
    with open(path, "r", encoding="utf-8") as f:
        return safe_minidom.parseString(f.read())


def _write_xml(doc: safe_minidom.Document, path: Path) -> None:
    """XML を整形して書き出す。"""
    xml_str = doc.toprettyxml(indent="  ", encoding="UTF-8")
    lines = xml_str.decode("utf-8").split("\n")
    cleaned = "\n".join(line for line in lines if line.strip())
    with open(path, "w", encoding="utf-8") as f:
        f.write(cleaned + "\n")


def _get_referenced_slides(pres_path: Path) -> set[str]:
    """presentation.xml から参照されているスライドファイル名を取得する。"""
    pres_doc = _parse_xml(pres_path)
    pres_rels_path = pres_path.parent / "_rels" / "presentation.xml.rels"
    if not pres_rels_path.exists():
        return set()

    rels_doc = _parse_xml(pres_rels_path)

    # sldIdLst から参照されている rId を取得
    referenced_rids: set[str] = set()
    for sld_id in pres_doc.getElementsByTagName("p:sldId"):
        rid = sld_id.getAttribute("r:id")
        if rid:
            referenced_rids.add(rid)

    # rId からスライドファイル名を取得
    referenced_slides: set[str] = set()
    for rel in rels_doc.getElementsByTagName("Relationship"):
        rid = rel.getAttribute("Id")
        target = rel.getAttribute("Target")
        if rid in referenced_rids and target:
            # "slides/slide1.xml" → "slide1.xml"
            slide_name = os.path.basename(target)
            referenced_slides.add(slide_name)

    return referenced_slides


def _get_referenced_targets_from_rels(rels_path: Path) -> set[str]:
    """リレーションシップファイルから参照先のファイル名を取得する。"""
    if not rels_path.exists():
        return set()
    rels_doc = _parse_xml(rels_path)
    targets: set[str] = set()
    for rel in rels_doc.getElementsByTagName("Relationship"):
        target = rel.getAttribute("Target")
        if target:
            # 相対パスのベースネームを取得
            targets.add(os.path.basename(target))
    return targets


def _remove_orphaned_slides(
    slides_dir: Path, referenced: set[str]
) -> list[str]:
    """参照されていないスライドファイルを削除する。"""
    removed: list[str] = []
    for f in sorted(slides_dir.iterdir()):
        if re.match(r"slide\d+\.xml$", f.name) and f.name not in referenced:
            f.unlink()
            # .rels も削除
            rels_file = slides_dir / "_rels" / f"{f.name}.rels"
            if rels_file.exists():
                rels_file.unlink()
            removed.append(f.name)
    return removed


def _get_all_referenced_media(ppt_dir: Path, referenced_slides: set[str]) -> set[str]:
    """参照されている全スライドからメディアファイル名を収集する。"""
    media_refs: set[str] = set()
    slides_dir = ppt_dir / "slides"
    slides_rels_dir = slides_dir / "_rels"

    for slide_name in referenced_slides:
        rels_path = slides_rels_dir / f"{slide_name}.rels"
        media_refs |= _get_referenced_targets_from_rels(rels_path)

    # スライドマスター・レイアウトからのメディア参照も収集
    for subdir_name in ("slideMasters", "slideLayouts"):
        subdir = ppt_dir / subdir_name
        if not subdir.exists():
            continue
        rels_subdir = subdir / "_rels"
        if not rels_subdir.exists():
            continue
        for rels_file in rels_subdir.iterdir():
            if rels_file.suffix == ".rels":
                media_refs |= _get_referenced_targets_from_rels(rels_file)

    return media_refs


def _remove_orphaned_media(
    media_dir: Path, referenced_media: set[str]
) -> list[str]:
    """参照されていないメディアファイルを削除する。"""
    removed: list[str] = []
    if not media_dir.exists():
        return removed
    for f in sorted(media_dir.iterdir()):
        if f.is_file() and f.name not in referenced_media:
            f.unlink()
            removed.append(f.name)
    return removed


def _remove_orphaned_notes(
    notes_dir: Path, referenced_slides: set[str]
) -> list[str]:
    """孤立したノートスライドを削除する。"""
    removed: list[str] = []
    if not notes_dir.exists():
        return removed

    # スライドの .rels からノート参照を収集
    slides_dir = notes_dir.parent / "slides"
    slides_rels_dir = slides_dir / "_rels"
    referenced_notes: set[str] = set()

    for slide_name in referenced_slides:
        rels_path = slides_rels_dir / f"{slide_name}.rels"
        if rels_path.exists():
            rels_doc = _parse_xml(rels_path)
            for rel in rels_doc.getElementsByTagName("Relationship"):
                target = rel.getAttribute("Target")
                if target and "notesSlides" in target:
                    referenced_notes.add(os.path.basename(target))

    for f in sorted(notes_dir.iterdir()):
        if re.match(r"notesSlide\d+\.xml$", f.name) and f.name not in referenced_notes:
            f.unlink()
            rels_file = notes_dir / "_rels" / f"{f.name}.rels"
            if rels_file.exists():
                rels_file.unlink()
            removed.append(f.name)
    return removed


def _update_content_types(
    ct_path: Path,
    removed_slides: list[str],
    removed_notes: list[str],
) -> None:
    """Content_Types.xml から削除されたファイルのエントリを除去する。"""
    if not ct_path.exists():
        return

    removed_parts: set[str] = set()
    for s in removed_slides:
        removed_parts.add(f"/ppt/slides/{s}")
    for n in removed_notes:
        removed_parts.add(f"/ppt/notesSlides/{n}")

    if not removed_parts:
        return

    ct_doc = _parse_xml(ct_path)
    to_remove: list = []
    for override in ct_doc.getElementsByTagName("Override"):
        part_name = override.getAttribute("PartName")
        if part_name in removed_parts:
            to_remove.append(override)

    for elem in to_remove:
        elem.parentNode.removeChild(elem)

    if to_remove:
        _write_xml(ct_doc, ct_path)


def _remove_orphaned_rels_from_presentation(
    pres_rels_path: Path, referenced_slides: set[str]
) -> int:
    """presentation.xml.rels から孤立したスライドリレーションシップを除去する。"""
    if not pres_rels_path.exists():
        return 0

    rels_doc = _parse_xml(pres_rels_path)
    to_remove: list = []

    for rel in rels_doc.getElementsByTagName("Relationship"):
        target = rel.getAttribute("Target")
        if target and target.startswith("slides/"):
            slide_name = os.path.basename(target)
            if slide_name not in referenced_slides:
                to_remove.append(rel)

    for elem in to_remove:
        elem.parentNode.removeChild(elem)

    if to_remove:
        _write_xml(rels_doc, pres_rels_path)

    return len(to_remove)


def clean(unpacked_dir: Path) -> dict[str, list[str]]:
    """クリーンアップを実行し、削除されたファイルのレポートを返す。"""
    ppt_dir = unpacked_dir / "ppt"
    pres_path = ppt_dir / "presentation.xml"

    if not pres_path.exists():
        print(f"Error: {pres_path} not found", file=sys.stderr)
        sys.exit(1)

    # 参照されているスライドを特定
    referenced_slides = _get_referenced_slides(pres_path)

    # 孤立スライドの削除
    slides_dir = ppt_dir / "slides"
    removed_slides = _remove_orphaned_slides(slides_dir, referenced_slides)

    # 孤立ノートの削除
    notes_dir = ppt_dir / "notesSlides"
    removed_notes = _remove_orphaned_notes(notes_dir, referenced_slides)

    # 参照されているメディアを収集し、孤立メディアを削除
    referenced_media = _get_all_referenced_media(ppt_dir, referenced_slides)
    media_dir = ppt_dir / "media"
    removed_media = _remove_orphaned_media(media_dir, referenced_media)

    # Content_Types.xml を更新
    ct_path = unpacked_dir / "[Content_Types].xml"
    _update_content_types(ct_path, removed_slides, removed_notes)

    # presentation.xml.rels から孤立リレーションを除去
    pres_rels_path = ppt_dir / "_rels" / "presentation.xml.rels"
    removed_rels_count = _remove_orphaned_rels_from_presentation(
        pres_rels_path, referenced_slides
    )

    return {
        "slides": removed_slides,
        "notes": removed_notes,
        "media": removed_media,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="不要ファイルの除去（クリーンアップ）を行う",
        epilog=(
            "例:\n"
            "  %(prog)s unpacked/\n"
            "\n"
            "presentation.xml の sldIdLst に含まれないスライド、\n"
            "未参照のメディア・ノートを削除します。"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("unpacked_dir", type=Path, help="展開済みディレクトリ")
    args = parser.parse_args()

    if not args.unpacked_dir.is_dir():
        print(f"Error: directory not found: {args.unpacked_dir}", file=sys.stderr)
        sys.exit(1)

    result = clean(args.unpacked_dir)

    total = sum(len(v) for v in result.values())
    if total == 0:
        print("クリーンアップ完了: 孤立ファイルなし")
    else:
        print(f"クリーンアップ完了: {total} ファイル削除")
        for category, files in result.items():
            if files:
                print(f"  {category}: {', '.join(files)}")


if __name__ == "__main__":
    main()
