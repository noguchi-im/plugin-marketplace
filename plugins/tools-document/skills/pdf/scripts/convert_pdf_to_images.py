"""PDF の各ページを PNG 画像に変換する。"""

from __future__ import annotations

import argparse
import os
import shutil
import sys

from pdf2image import convert_from_path


def convert_pdf_to_images(
    pdf_path: str,
    output_dir: str,
    max_dim: int = 2000,
) -> list[str]:
    """PDF を PNG 画像群に変換し、出力ファイルパスのリストを返す。"""
    os.makedirs(output_dir, exist_ok=True)

    # poppler の pdftoppm が必要
    if shutil.which("pdftoppm") is None:
        print(
            "Warning: pdftoppm not found. Install poppler-utils for best results.",
            file=sys.stderr,
        )

    images = convert_from_path(pdf_path, size=(max_dim, None))

    output_paths: list[str] = []
    for i, image in enumerate(images):
        filename = f"page_{i + 1}.png"
        filepath = os.path.join(output_dir, filename)
        image.save(filepath, "PNG")
        output_paths.append(filepath)

    return output_paths


def main() -> None:
    parser = argparse.ArgumentParser(
        description="PDF の各ページを PNG 画像に変換する",
        epilog="例: python convert_pdf_to_images.py document.pdf output_images/",
    )
    parser.add_argument("pdf", help="入力 PDF ファイルのパス")
    parser.add_argument("output_dir", help="出力ディレクトリのパス")
    parser.add_argument(
        "--max-dim",
        type=int,
        default=2000,
        help="画像の最大幅ピクセル数（デフォルト: 2000）",
    )
    args = parser.parse_args()

    try:
        paths = convert_pdf_to_images(args.pdf, args.output_dir, args.max_dim)
    except FileNotFoundError:
        print(f"Error: File not found: {args.pdf}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    for path in paths:
        print(path)
    print(f"Converted {len(paths)} page(s) to {args.output_dir}")


if __name__ == "__main__":
    main()
