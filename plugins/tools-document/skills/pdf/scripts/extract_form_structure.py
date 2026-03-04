"""non-fillable PDF の視覚的構造（ラベル・線・チェックボックス候補）を抽出する。"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import pdfplumber


def _extract_text_elements(page: Any) -> list[dict[str, Any]]:
    """ページ内のテキスト要素（ラベル候補）を抽出する。"""
    elements: list[dict[str, Any]] = []
    words = page.extract_words(keep_blank_chars=True, extra_attrs=["size"])
    for word in words:
        elements.append({
            "type": "text",
            "text": word["text"],
            "x0": round(word["x0"], 2),
            "y0": round(word["top"], 2),
            "x1": round(word["x1"], 2),
            "y1": round(word["bottom"], 2),
            "font_size": round(word.get("size", 12), 1),
        })
    return elements


def _extract_lines(page: Any) -> list[dict[str, Any]]:
    """ページ内の線要素を抽出する。"""
    elements: list[dict[str, Any]] = []
    for line in page.lines:
        elements.append({
            "type": "line",
            "x0": round(line["x0"], 2),
            "y0": round(line["top"], 2),
            "x1": round(line["x1"], 2),
            "y1": round(line["bottom"], 2),
            "orientation": "horizontal" if abs(line["top"] - line["bottom"]) < 2 else "vertical",
        })
    return elements


def _extract_rects(page: Any) -> list[dict[str, Any]]:
    """ページ内の矩形要素（チェックボックス候補を含む）を抽出する。"""
    elements: list[dict[str, Any]] = []
    for rect in page.rects:
        width = rect["x1"] - rect["x0"]
        height = rect["bottom"] - rect["top"]
        is_checkbox_candidate = 5 <= width <= 25 and 5 <= height <= 25
        elements.append({
            "type": "rect",
            "x0": round(rect["x0"], 2),
            "y0": round(rect["top"], 2),
            "x1": round(rect["x1"], 2),
            "y1": round(rect["bottom"], 2),
            "width": round(width, 2),
            "height": round(height, 2),
            "is_checkbox_candidate": is_checkbox_candidate,
        })
    return elements


def extract_form_structure(pdf_path: str) -> dict[str, Any]:
    """PDF の視覚的構造を抽出して辞書として返す。"""
    result: dict[str, Any] = {"pages": [], "elements": []}

    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            page_number = i + 1
            pdf_width = round(page.width, 2)
            pdf_height = round(page.height, 2)

            result["pages"].append({
                "page_number": page_number,
                "pdf_width": pdf_width,
                "pdf_height": pdf_height,
            })

            # テキスト要素
            for elem in _extract_text_elements(page):
                elem["page_number"] = page_number
                result["elements"].append(elem)

            # 線要素
            for elem in _extract_lines(page):
                elem["page_number"] = page_number
                result["elements"].append(elem)

            # 矩形要素
            for elem in _extract_rects(page):
                elem["page_number"] = page_number
                result["elements"].append(elem)

    return result


def main() -> None:
    parser = argparse.ArgumentParser(
        description="non-fillable PDF の視覚的構造を抽出する",
        epilog="例: python extract_form_structure.py document.pdf structure.json",
    )
    parser.add_argument("pdf", help="入力 PDF ファイルのパス")
    parser.add_argument("output_json", help="出力 JSON ファイルのパス")
    args = parser.parse_args()

    try:
        structure = extract_form_structure(args.pdf)
    except FileNotFoundError:
        print(f"Error: File not found: {args.pdf}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    with open(args.output_json, "w", encoding="utf-8") as f:
        json.dump(structure, f, ensure_ascii=False, indent=2)

    n_pages = len(structure["pages"])
    n_elements = len(structure["elements"])
    print(f"Extracted {n_elements} element(s) from {n_pages} page(s) to {args.output_json}")


if __name__ == "__main__":
    main()
