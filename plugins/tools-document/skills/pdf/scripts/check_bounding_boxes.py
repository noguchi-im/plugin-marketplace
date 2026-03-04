"""フォームフィールドのバウンディングボックスの重複・サイズ不足を検証する。"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass


@dataclass
class RectInfo:
    rect: list[float]
    field_label: str
    rect_type: str  # "label" or "entry"
    page: int


def rects_intersect(a: list[float], b: list[float]) -> bool:
    """2つの矩形 [x0, y0, x1, y1] が交差するか判定する。"""
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def validate_bounding_boxes(fields_path: str) -> list[str]:
    """バウンディングボックスを検証し、エラーメッセージのリストを返す。"""
    with open(fields_path, encoding="utf-8") as f:
        data = json.load(f)

    form_fields = data.get("form_fields", [])
    errors: list[str] = []

    # 全矩形を収集
    rects: list[RectInfo] = []
    for field in form_fields:
        label = field.get("label", "unknown")
        page = field.get("page_number", 0)
        if "label_bounding_box" in field:
            rects.append(RectInfo(field["label_bounding_box"], label, "label", page))
        if "entry_bounding_box" in field:
            rects.append(RectInfo(field["entry_bounding_box"], label, "entry", page))

    # ペアワイズ重複チェック
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            a, b = rects[i], rects[j]
            if a.page != b.page:
                continue
            if rects_intersect(a.rect, b.rect):
                if a.field_label == b.field_label:
                    errors.append(
                        f"FAILURE: Field '{a.field_label}' has overlapping "
                        f"{a.rect_type} and {b.rect_type} bounding boxes"
                    )
                else:
                    errors.append(
                        f"FAILURE: Overlapping bounding boxes between "
                        f"'{a.field_label}' ({a.rect_type}) and "
                        f"'{b.field_label}' ({b.rect_type}) on page {a.page}"
                    )
        if len(errors) >= 20:
            break

    # エントリ矩形のサイズチェック
    for field in form_fields:
        if "entry_bounding_box" not in field:
            continue
        rect = field["entry_bounding_box"]
        font_size = field.get("font_size", 14)
        height = abs(rect[3] - rect[1])
        if height < font_size:
            errors.append(
                f"FAILURE: Field '{field.get('label', 'unknown')}' entry box "
                f"height ({height:.1f}) is smaller than font size ({font_size})"
            )
        if len(errors) >= 20:
            break

    return errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="フォームフィールドのバウンディングボックスを検証する",
        epilog="例: python check_bounding_boxes.py fields.json",
    )
    parser.add_argument("fields_json", help="フォームフィールド定義の JSON ファイルパス")
    args = parser.parse_args()

    try:
        errors = validate_bounding_boxes(args.fields_json)
    except FileNotFoundError:
        print(f"Error: File not found: {args.fields_json}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    if errors:
        for error in errors:
            print(error)
        sys.exit(1)
    else:
        print("SUCCESS: All bounding boxes are valid.")


if __name__ == "__main__":
    main()
