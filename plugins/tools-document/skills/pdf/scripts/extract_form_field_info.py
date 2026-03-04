"""fillable PDF からフォームフィールド情報を抽出し JSON に書き出す。"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from pypdf import PdfReader
from pypdf.generic import ArrayObject, IndirectObject, NameObject


def _resolve(obj: Any) -> Any:
    """IndirectObject を解決して実体を返す。"""
    while isinstance(obj, IndirectObject):
        obj = obj.get_object()
    return obj


def _get_page_number(reader: PdfReader, field: dict[str, Any]) -> int:
    """フィールドが属するページ番号（1-based）を返す。"""
    widget = _resolve(field.get("/P"))
    if widget is not None:
        for i, page in enumerate(reader.pages):
            if page.get_object() == widget:
                return i + 1
    # /P がない場合は /Kids からページを探す
    for i, page in enumerate(reader.pages):
        annots = page.get("/Annots")
        if annots is None:
            continue
        annots = _resolve(annots)
        if not isinstance(annots, ArrayObject):
            continue
        for annot in annots:
            annot_obj = _resolve(annot)
            if annot_obj == field:
                return i + 1
    return 1


def _get_rect(field: dict[str, Any]) -> list[float] | None:
    """フィールドの /Rect を [x0, y0, x1, y1] として返す。"""
    rect = field.get("/Rect")
    if rect is None:
        return None
    rect = _resolve(rect)
    if isinstance(rect, ArrayObject) and len(rect) == 4:
        return [float(v) for v in rect]
    return None


def _get_choice_options(field: dict[str, Any]) -> list[str]:
    """ドロップダウン / リストボックスの選択肢を返す。"""
    opt = field.get("/Opt")
    if opt is None:
        return []
    opt = _resolve(opt)
    if not isinstance(opt, ArrayObject):
        return []
    options: list[str] = []
    for item in opt:
        item = _resolve(item)
        if isinstance(item, ArrayObject) and len(item) >= 2:
            options.append(str(_resolve(item[1])))
        else:
            options.append(str(item))
    return options


def _determine_field_type(field: dict[str, Any]) -> str:
    """フィールドの型文字列を返す: text, checkbox, radio, choice, signature, unknown。"""
    ft = field.get("/FT")
    if ft is None:
        return "unknown"
    ft = str(ft)
    if ft == "/Tx":
        return "text"
    if ft == "/Btn":
        flags = int(field.get("/Ff", 0))
        # bit 16 (0-indexed 15) = pushbutton, bit 17 (0-indexed 16) = radio
        if flags & (1 << 16):
            return "radio"
        return "checkbox"
    if ft == "/Ch":
        return "choice"
    if ft == "/Sig":
        return "signature"
    return "unknown"


def _get_checkbox_values(field: dict[str, Any]) -> tuple[str, str]:
    """checkbox の checked / unchecked 値を返す。"""
    ap = field.get("/AP")
    if ap is None:
        return "/Yes", "/Off"
    ap = _resolve(ap)
    normal = ap.get("/N") if isinstance(ap, dict) else None
    if normal is None:
        return "/Yes", "/Off"
    normal = _resolve(normal)
    if isinstance(normal, dict):
        keys = [str(k) for k in normal.keys()]
        checked = next((k for k in keys if k != "/Off"), "/Yes")
        return checked, "/Off"
    return "/Yes", "/Off"


def extract_form_field_info(pdf_path: str) -> list[dict[str, Any]]:
    """fillable PDF からフィールド情報を抽出する。"""
    reader = PdfReader(pdf_path)

    if not reader.get_fields():
        return []

    results: list[dict[str, Any]] = []

    # フィールドツリーを走査する
    def _collect_fields(fields_dict: dict[str, Any]) -> None:
        for field_name, field_obj in fields_dict.items():
            if hasattr(field_obj, "get_object"):
                field_data = field_obj.get_object()
            elif isinstance(field_obj, dict) and "/FT" in field_obj:
                field_data = field_obj
            else:
                # indirect_reference 等から辿れるものは辿る
                if hasattr(field_obj, "indirect_reference"):
                    field_data = _resolve(field_obj.indirect_reference)
                else:
                    continue

            if not isinstance(field_data, dict):
                continue

            field_type = _determine_field_type(field_data)
            page = _get_page_number(reader, field_data)
            rect = _get_rect(field_data)

            entry: dict[str, Any] = {
                "field_id": field_name,
                "type": field_type,
                "page": page,
            }

            if rect is not None:
                entry["rect"] = rect

            if field_type == "checkbox":
                checked, unchecked = _get_checkbox_values(field_data)
                entry["checked_value"] = checked
                entry["unchecked_value"] = unchecked

            if field_type == "choice":
                entry["choice_options"] = _get_choice_options(field_data)

            results.append(entry)

    fields = reader.get_fields()
    if fields:
        _collect_fields(fields)

    # ページ番号順にソート
    results.sort(key=lambda x: (x["page"], (x.get("rect") or [0, 0])[1]))

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="fillable PDF からフォームフィールド情報を抽出する",
        epilog="例: python extract_form_field_info.py form.pdf field_info.json",
    )
    parser.add_argument("pdf", help="入力 PDF ファイルのパス")
    parser.add_argument("output_json", help="出力 JSON ファイルのパス")
    args = parser.parse_args()

    try:
        fields = extract_form_field_info(args.pdf)
    except FileNotFoundError:
        print(f"Error: File not found: {args.pdf}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(fields, f, ensure_ascii=False, indent=2)

    print(f"Extracted {len(fields)} field(s) to {args.output_json}")


if __name__ == "__main__":
    main()
