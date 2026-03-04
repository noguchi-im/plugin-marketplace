"""バウンディングボックスをページ画像にオーバーレイした検証画像を生成する。"""

from __future__ import annotations

import argparse
import json
import sys

from PIL import Image, ImageDraw


def create_validation_image(
    page_number: int,
    fields_path: str,
    input_image_path: str,
    output_image_path: str,
) -> None:
    """指定ページのバウンディングボックスを画像にオーバーレイして保存する。"""
    with open(fields_path, encoding="utf-8") as f:
        data = json.load(f)

    # ページ情報を取得
    pages = data.get("pages", [])
    page_info = None
    for p in pages:
        if p["page_number"] == page_number:
            page_info = p
            break

    if page_info is None:
        raise ValueError(f"Page {page_number} not found in fields JSON")

    pdf_width = page_info["pdf_width"]
    pdf_height = page_info["pdf_height"]

    # 画像を開く
    image = Image.open(input_image_path).copy()
    img_width, img_height = image.size
    draw = ImageDraw.Draw(image)

    # PDF 座標 → 画像座標の変換係数
    scale_x = img_width / pdf_width
    scale_y = img_height / pdf_height

    def pdf_to_img(rect: list[float]) -> tuple[float, float, float, float]:
        """PDF 座標系 [x0, y0, x1, y1] を画像座標系に変換する。"""
        x0 = rect[0] * scale_x
        y0 = (pdf_height - rect[3]) * scale_y
        x1 = rect[2] * scale_x
        y1 = (pdf_height - rect[1]) * scale_y
        return (x0, y0, x1, y1)

    # フィールドを描画
    form_fields = data.get("form_fields", [])
    drawn = 0
    for field in form_fields:
        if field.get("page_number") != page_number:
            continue

        # エントリ領域: 赤
        if "entry_bounding_box" in field:
            img_rect = pdf_to_img(field["entry_bounding_box"])
            draw.rectangle(img_rect, outline="red", width=2)
            drawn += 1

        # ラベル領域: 青
        if "label_bounding_box" in field:
            img_rect = pdf_to_img(field["label_bounding_box"])
            draw.rectangle(img_rect, outline="blue", width=2)
            drawn += 1

    image.save(output_image_path)
    print(f"Drew {drawn} rectangle(s) on page {page_number}, saved to {output_image_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="バウンディングボックスを画像にオーバーレイした検証画像を生成する",
        epilog="例: python create_validation_image.py 1 fields.json page_1.png validation.png",
    )
    parser.add_argument("page_number", type=int, help="対象ページ番号（1-based）")
    parser.add_argument("fields_json", help="フィールド定義 JSON ファイルのパス")
    parser.add_argument("input_image", help="入力画像ファイルのパス（ページ画像）")
    parser.add_argument("output_image", help="出力画像ファイルのパス")
    args = parser.parse_args()

    try:
        create_validation_image(
            args.page_number,
            args.fields_json,
            args.input_image,
            args.output_image,
        )
    except FileNotFoundError as e:
        print(f"Error: File not found: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
