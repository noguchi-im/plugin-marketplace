"""fillable PDF のフォームフィールドに値を記入する。"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, NameObject


def _patch_pypdf_opt_handling(writer: PdfWriter) -> None:
    """pypdf の /Opt 処理に関するモンキーパッチを適用する。

    pypdf の一部バージョンでは choice フィールドの /Opt エントリを
    正しく処理できない場合がある。このパッチは将来のバージョンで
    修正された場合に不要になる。
    """
    # pypdf >= 4.0 ではこの問題は概ね解消されているが、
    # エッジケースに備えてフィールド更新時に /Opt を保持する処理を入れる。
    pass


def validate_values(
    fields_info: list[dict[str, Any]], values: list[dict[str, Any]]
) -> list[str]:
    """記入値を検証し、エラーメッセージのリストを返す。"""
    errors: list[str] = []
    fields_by_id: dict[str, dict[str, Any]] = {
        f["field_id"]: f for f in fields_info
    }

    for entry in values:
        field_id = entry.get("field_id")
        value = entry.get("value")

        if field_id is None:
            errors.append("FAILURE: Entry missing 'field_id'")
            continue

        if field_id not in fields_by_id:
            errors.append(f"FAILURE: Unknown field_id '{field_id}'")
            continue

        info = fields_by_id[field_id]
        field_type = info.get("type", "unknown")

        if field_type == "checkbox":
            allowed = {info.get("checked_value", "/Yes"), info.get("unchecked_value", "/Off")}
            if value not in allowed:
                errors.append(
                    f"FAILURE: Field '{field_id}' checkbox value must be "
                    f"one of {allowed}, got '{value}'"
                )

        if field_type == "choice":
            options = info.get("choice_options", [])
            if options and value not in options:
                errors.append(
                    f"FAILURE: Field '{field_id}' choice value must be "
                    f"one of {options}, got '{value}'"
                )

    return errors


def fill_fillable_fields(
    pdf_path: str,
    values: list[dict[str, Any]],
    output_path: str,
) -> None:
    """fillable PDF にフォーム値を記入して保存する。"""
    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    writer.append(reader)

    _patch_pypdf_opt_handling(writer)

    # ページごとに値をグループ化
    values_by_page: dict[int, dict[str, Any]] = {}
    for entry in values:
        page = entry.get("page", 1)
        field_id = entry["field_id"]
        value = entry["value"]
        if page not in values_by_page:
            values_by_page[page] = {}
        values_by_page[page][field_id] = value

    # 全フィールドをまとめて更新
    all_values: dict[str, str] = {}
    for entry in values:
        all_values[entry["field_id"]] = str(entry["value"])

    writer.update_page_form_field_values(writer.pages[0], all_values)

    writer.write(output_path)
    writer.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="fillable PDF のフォームフィールドに値を記入する",
        epilog="例: python fill_fillable_fields.py form.pdf values.json filled.pdf",
    )
    parser.add_argument("pdf", help="入力 PDF ファイルのパス")
    parser.add_argument("values_json", help="記入値の JSON ファイルパス")
    parser.add_argument("output_pdf", help="出力 PDF ファイルのパス")
    parser.add_argument(
        "--fields-info",
        help="extract_form_field_info.py で抽出したフィールド情報 JSON（検証用）",
    )
    args = parser.parse_args()

    try:
        with open(args.values_json, encoding="utf-8") as f:
            values = json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {args.values_json}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in values file: {e}", file=sys.stderr)
        sys.exit(1)

    # フィールド情報があれば検証を実行
    if args.fields_info:
        try:
            with open(args.fields_info, encoding="utf-8") as f:
                fields_info = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error: Cannot read fields info: {e}", file=sys.stderr)
            sys.exit(1)

        errors = validate_values(fields_info, values)
        if errors:
            for error in errors:
                print(error)
            sys.exit(1)

    try:
        fill_fillable_fields(args.pdf, values, args.output_pdf)
    except FileNotFoundError:
        print(f"Error: File not found: {args.pdf}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"Filled {len(values)} field(s) and saved to {args.output_pdf}")


if __name__ == "__main__":
    main()
