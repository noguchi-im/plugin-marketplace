"""PDF の fillable フォームフィールド有無を判定する。"""

from __future__ import annotations

import argparse
import sys

from pypdf import PdfReader


def check_fillable(pdf_path: str) -> bool:
    """PDF に fillable フォームフィールドがあるか判定する。"""
    reader = PdfReader(pdf_path)
    fields = reader.get_fields()
    return bool(fields)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PDF に fillable フォームフィールドがあるか判定する",
        epilog="例: python check_fillable_fields.py form.pdf",
    )
    parser.add_argument("pdf", help="入力 PDF ファイルのパス")
    args = parser.parse_args()

    try:
        if check_fillable(args.pdf):
            print("This PDF has fillable form fields.")
        else:
            print(
                "This PDF does not have fillable form fields; "
                "you will need to visually determine where to enter data."
            )
    except FileNotFoundError:
        print(f"Error: File not found: {args.pdf}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
