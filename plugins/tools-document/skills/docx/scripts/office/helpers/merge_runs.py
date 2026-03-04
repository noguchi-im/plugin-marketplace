"""隣接する同一書式の w:r 要素を結合する。

unpack 時に呼ばれ、XML 編集の可読性を向上させる。
"""

from __future__ import annotations

import copy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lxml import etree

WML_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _tag(local: str) -> str:
    return f"{{{WML_NS}}}{local}"


def _rpr_signature(run: "etree._Element") -> str | None:
    """w:r の w:rPr を正規化した文字列として返す。rPr がなければ空文字列。"""
    rpr = run.find(_tag("rPr"))
    if rpr is None:
        return ""
    from lxml import etree as _et

    # 子要素をタグ名順にソートして比較可能にする
    children = sorted(rpr, key=lambda e: e.tag)
    parts: list[str] = []
    for child in children:
        parts.append(_et.tostring(child, encoding="unicode"))
    return "".join(parts)


def _get_text(run: "etree._Element") -> str:
    """w:r 内の w:t テキストを取得する。"""
    t_elem = run.find(_tag("t"))
    if t_elem is not None and t_elem.text:
        return t_elem.text
    return ""


def _is_simple_text_run(run: "etree._Element") -> bool:
    """w:r が単純なテキスト run かどうか（w:t のみを含む）。"""
    children = [c for c in run if c.tag != _tag("rPr")]
    if len(children) != 1:
        return False
    return children[0].tag == _tag("t")


def merge_runs(root: "etree._Element") -> int:
    """root 配下の全 w:p 内で隣接する同一書式の w:r を結合する。

    Returns:
        結合により削除された w:r の数。
    """
    merged_count = 0
    for para in root.iter(_tag("p")):
        children = list(para)
        i = 0
        while i < len(children) - 1:
            current = children[i]
            next_elem = children[i + 1]

            # 両方が w:r で、単純テキスト run で、同一書式の場合のみ結合
            if (
                current.tag == _tag("r")
                and next_elem.tag == _tag("r")
                and _is_simple_text_run(current)
                and _is_simple_text_run(next_elem)
            ):
                sig_current = _rpr_signature(current)
                sig_next = _rpr_signature(next_elem)
                if sig_current == sig_next:
                    # テキストを結合
                    t_current = current.find(_tag("t"))
                    t_next = next_elem.find(_tag("t"))
                    combined = _get_text(current) + _get_text(next_elem)
                    if t_current is not None:
                        t_current.text = combined
                        t_current.set(
                            "{http://www.w3.org/XML/1998/namespace}space",
                            "preserve",
                        )
                    # next を削除
                    para.remove(next_elem)
                    children = list(para)
                    merged_count += 1
                    continue
            i += 1
    return merged_count
