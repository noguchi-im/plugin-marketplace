"""サムネイルグリッドを生成する。

.pptx を LibreOffice で PDF に変換し、pdftoppm でスライドごとの JPEG を生成、
Pillow でスライド番号とファイル名のラベルを付与したグリッド画像を出力する。
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print(
        "Error: Pillow is not installed. Run: pip install Pillow",
        file=sys.stderr,
    )
    sys.exit(1)


# --- 定数 ---
DEFAULT_COLS = 3
MAX_SLIDES_PER_GRID = 12
THUMB_WIDTH = 640
LABEL_HEIGHT = 40
GRID_PADDING = 10
GRID_BG_COLOR = (255, 255, 255)
LABEL_BG_COLOR = (40, 40, 40)
LABEL_TEXT_COLOR = (255, 255, 255)


def _check_external_deps() -> None:
    """外部コマンドの存在を確認する。"""
    missing: list[str] = []
    if not shutil.which("soffice"):
        missing.append("soffice (LibreOffice)")
    if not shutil.which("pdftoppm"):
        missing.append("pdftoppm (poppler-utils)")
    if missing:
        print(
            f"Error: required commands not found: {', '.join(missing)}",
            file=sys.stderr,
        )
        print("Install:", file=sys.stderr)
        print("  apt: sudo apt install libreoffice poppler-utils", file=sys.stderr)
        print(
            "  brew: brew install --cask libreoffice && brew install poppler",
            file=sys.stderr,
        )
        sys.exit(1)


def _find_soffice_helper() -> Path | None:
    """docx スキルの soffice.py ヘルパーを探す。"""
    # 自身のスクリプトディレクトリから docx の office/ を探す
    scripts_dir = Path(__file__).resolve().parent
    # pptx/scripts/ → pptx/ → skills/ → docx/scripts/office/soffice.py
    docx_soffice = (
        scripts_dir.parent.parent / "docx" / "scripts" / "office" / "soffice.py"
    )
    if docx_soffice.exists():
        return docx_soffice
    return None


def _convert_to_pdf(pptx_path: Path, output_dir: Path) -> Path:
    """LibreOffice で .pptx を PDF に変換する。"""
    soffice_helper = _find_soffice_helper()

    if soffice_helper:
        # docx スキルの soffice.py ヘルパーを使用（サンドボックス対応）
        cmd = [
            sys.executable,
            str(soffice_helper),
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_dir),
            str(pptx_path),
        ]
    else:
        # 直接 soffice を呼び出す
        cmd = [
            "soffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(output_dir),
            str(pptx_path),
        ]

    result = subprocess.run(
        cmd, capture_output=True, text=True, timeout=120
    )
    if result.returncode != 0:
        print(f"Error: PDF conversion failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    pdf_name = pptx_path.stem + ".pdf"
    pdf_path = output_dir / pdf_name
    if not pdf_path.exists():
        print(f"Error: PDF not found at {pdf_path}", file=sys.stderr)
        sys.exit(1)

    return pdf_path


def _convert_to_jpegs(pdf_path: Path, output_dir: Path) -> list[Path]:
    """pdftoppm で PDF をスライドごとの JPEG に変換する。"""
    prefix = str(output_dir / "slide")
    cmd = ["pdftoppm", "-jpeg", "-r", "150", str(pdf_path), prefix]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"Error: JPEG conversion failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    # slide-01.jpg, slide-02.jpg, ... を収集
    pattern = str(output_dir / "slide-*.jpg")
    jpegs = sorted(glob.glob(pattern))
    return [Path(j) for j in jpegs]


def _create_grid(
    jpegs: list[Path],
    output_path: Path,
    cols: int,
) -> None:
    """JPEG をグリッド画像にまとめる。"""
    if not jpegs:
        print("Warning: no slide images found", file=sys.stderr)
        return

    # サムネイルを読み込みリサイズ
    thumbnails: list[Image.Image] = []
    for jpeg_path in jpegs[:MAX_SLIDES_PER_GRID]:
        img = Image.open(jpeg_path)
        # アスペクト比を維持してリサイズ
        ratio = THUMB_WIDTH / img.width
        new_height = int(img.height * ratio)
        img = img.resize((THUMB_WIDTH, new_height), Image.LANCZOS)
        thumbnails.append(img)

    if not thumbnails:
        return

    thumb_height = thumbnails[0].height
    cell_height = thumb_height + LABEL_HEIGHT
    cell_width = THUMB_WIDTH

    rows = (len(thumbnails) + cols - 1) // cols
    grid_width = cols * cell_width + (cols + 1) * GRID_PADDING
    grid_height = rows * cell_height + (rows + 1) * GRID_PADDING

    grid_img = Image.new("RGB", (grid_width, grid_height), GRID_BG_COLOR)
    draw = ImageDraw.Draw(grid_img)

    # フォント（システムフォントのフォールバック）
    font = _get_font(16)
    small_font = _get_font(12)

    for idx, thumb in enumerate(thumbnails):
        row = idx // cols
        col = idx % cols
        x = col * cell_width + (col + 1) * GRID_PADDING
        y = row * cell_height + (row + 1) * GRID_PADDING

        # サムネイル画像を配置
        grid_img.paste(thumb, (x, y))

        # ラベル背景
        label_y = y + thumb.height
        draw.rectangle(
            [x, label_y, x + cell_width, label_y + LABEL_HEIGHT],
            fill=LABEL_BG_COLOR,
        )

        # ラベルテキスト
        slide_num = idx + 1
        slide_filename = f"slide{slide_num}.xml"
        label_text = f"#{slide_num}  {slide_filename}"
        draw.text(
            (x + 8, label_y + 10),
            label_text,
            fill=LABEL_TEXT_COLOR,
            font=font,
        )

    grid_img.save(str(output_path), "JPEG", quality=90)
    return


def _get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """利用可能なフォントを返す。"""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSMono.ttf",
    ]
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except (OSError, IOError):
                continue
    return ImageFont.load_default()


def generate_thumbnails(
    pptx_path: Path,
    output_prefix: str | None = None,
    cols: int = DEFAULT_COLS,
) -> Path:
    """サムネイルグリッドを生成する。"""
    _check_external_deps()

    if output_prefix is None:
        output_prefix = str(pptx_path.parent / "thumbnails")

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # .pptx → PDF
        pdf_path = _convert_to_pdf(pptx_path, tmpdir_path)

        # PDF → JPEG（スライドごと）
        jpegs = _convert_to_jpegs(pdf_path, tmpdir_path)

        if not jpegs:
            print("Error: no slide images generated", file=sys.stderr)
            sys.exit(1)

        # グリッド画像を生成
        output_path = Path(f"{output_prefix}.jpg")
        _create_grid(jpegs, output_path, cols)

    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="サムネイルグリッドを生成する",
        epilog=(
            "例:\n"
            "  %(prog)s presentation.pptx\n"
            "  %(prog)s presentation.pptx output_prefix\n"
            "  %(prog)s presentation.pptx --cols 4"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("pptx_path", type=Path, help=".pptx ファイルのパス")
    parser.add_argument(
        "output_prefix",
        nargs="?",
        default=None,
        help="出力ファイルのプレフィックス（デフォルト: thumbnails）",
    )
    parser.add_argument(
        "--cols",
        type=int,
        default=DEFAULT_COLS,
        help=f"グリッドのカラム数（デフォルト: {DEFAULT_COLS}）",
    )
    args = parser.parse_args()

    if not args.pptx_path.exists():
        print(f"Error: file not found: {args.pptx_path}", file=sys.stderr)
        sys.exit(1)

    output_path = generate_thumbnails(args.pptx_path, args.output_prefix, args.cols)
    print(f"サムネイルグリッド生成: {output_path}")


if __name__ == "__main__":
    main()
