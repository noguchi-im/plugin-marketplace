"""隣接する同一著者の変更履歴（w:ins / w:del）を統合する。

unpack 時に呼ばれ、変更履歴の可読性を向上させる。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lxml import etree

WML_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


def _tag(local: str) -> str:
    return f"{{{WML_NS}}}{local}"


def _get_author(elem: "etree._Element") -> str:
    """w:ins / w:del の w:author 属性を返す。"""
    return elem.get(f"{{{WML_NS}}}author", elem.get("w:author", ""))


def _is_tracked_change(elem: "etree._Element") -> bool:
    """要素が w:ins または w:del かどうか。"""
    return elem.tag in (_tag("ins"), _tag("del"))


def simplify_redlines(root: "etree._Element") -> int:
    """root 配下の全 w:p 内で隣接する同一著者・同一種類の変更履歴を統合する。

    Returns:
        統合により削除された要素の数。
    """
    merged_count = 0
    for para in root.iter(_tag("p")):
        children = list(para)
        i = 0
        while i < len(children) - 1:
            current = children[i]
            next_elem = children[i + 1]

            if (
                _is_tracked_change(current)
                and _is_tracked_change(next_elem)
                and current.tag == next_elem.tag
                and _get_author(current) == _get_author(next_elem)
            ):
                # next_elem の子要素を current に移動
                for child in list(next_elem):
                    current.append(child)
                para.remove(next_elem)
                children = list(para)
                merged_count += 1
                continue
            i += 1
    return merged_count
