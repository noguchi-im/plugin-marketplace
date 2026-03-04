"""non-fillable PDF に FreeText アノテーションでテキストを配置する。"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from pypdf import PdfReader, PdfWriter
from pypdf.annotations import FreeText
from pypdf.generic import ArrayObject, FloatObject, NameObject, NumberObject


def fill_pdf_form_with_annotations(
    pdf_path: str,
    fields_path: str,
    output_path: str,
) -> int:
    """non-fillable PDF に FreeText アノテーションを追加して保存する。

    Returns:
        配置したアノテーションの数。
    """
    with open(fields_path, encoding="utf-8") as f:
        data = json.load(f)

    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    writer.append(reader)

    form_fields = data.get("form_fields", [])
    count = 0

    for field in form_fields:
        if not field.get("entry_text", False):
            continue

        text = field.get("text", "")
        if not text:
            continue

        page_number = field.get("page_number", 1)
        page_index = page_number - 1

        if page_index < 0 or page_index >= len(writer.pages):
            print(
                f"Warning: Page {page_number} out of range, skipping field '{field.get('label', 'unknown')}'",
                file=sys.stderr,
            )
            continue

        rect = field.get("entry_bounding_box")
        if rect is None or len(rect) != 4:
            continue

        font_size = field.get("font_size", 12)

        annotation = FreeText(
            text=text,
            rect=tuple(rect),
            font_size=str(font_size) + "pt",
            font_color="000000",
            border_color=None,
        )

        writer.add_annotation(page_number=page_index, annotation=annotation)
        count += 1

    writer.write(output_path)
    writer.close()

    return count


def main() -> None:
    parser = argparse.ArgumentParser(
        description="non-fillable PDF に FreeText アノテーションでテキストを配置する",
        epilog="例: python fill_pdf_form_with_annotations.py input.pdf fields.json output.pdf",
    )
    parser.add_argument("pdf", help="入力 PDF ファイルのパス")
    parser.add_argument("fields_json", help="フィールド定義 JSON ファイルのパス")
    parser.add_argument("output_pdf", help="出力 PDF ファイルのパス")
    args = parser.parse_args()

    try:
        count = fill_pdf_form_with_annotations(args.pdf, args.fields_json, args.output_pdf)
    except FileNotFoundError as e:
        print(f"Error: File not found: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Placed {count} annotation(s), saved to {args.output_pdf}")


if __name__ == "__main__":
    main()
