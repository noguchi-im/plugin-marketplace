"""LibreOffice マクロで .docx の全変更履歴を承認する。

機能:
- LibreOffice Basic マクロの自動セットアップ
- マクロ実行による全変更履歴の承認
- タイムアウト保護（デフォルト 60 秒）
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# LibreOffice Basic マクロ
_MACRO_CONTENT = """\
Sub AcceptAllChanges(sURL As String, sOut As String)
    Dim oDoc As Object
    Dim oProps(0) As New com.sun.star.beans.PropertyValue
    oProps(0).Name = "Hidden"
    oProps(0).Value = True

    oDoc = StarDesktop.loadComponentFromURL( _
        ConvertToURL(sURL), "_blank", 0, oProps())

    If IsNull(oDoc) Or IsEmpty(oDoc) Then
        MsgBox "Failed to open: " & sURL
        Exit Sub
    End If

    oDoc.setPropertyValue("RedlineProtectionKey", Array())
    oDoc.setPropertyValue("RecordChanges", False)

    Dim oRedline As Object
    oRedline = oDoc.getRedlines()
    If Not IsNull(oRedline) Then
        oDoc.getRedlines().acceptAllChanges()
    End If

    Dim oOutProps(0) As New com.sun.star.beans.PropertyValue
    oOutProps(0).Name = "FilterName"
    oOutProps(0).Value = "MS Word 2007 XML"

    oDoc.storeToURL(ConvertToURL(sOut), oOutProps())
    oDoc.close(True)
End Sub
"""

_MACRO_NAME = "AcceptChanges"
_MACRO_FILENAME = "AcceptChanges.xba"


def _find_soffice() -> str | None:
    """soffice のパスを検索する。"""
    path = shutil.which("soffice")
    if path:
        return path
    mac_path = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    if os.path.isfile(mac_path):
        return mac_path
    return None


def _get_macro_dir() -> Path:
    """LibreOffice ユーザーマクロディレクトリを返す。"""
    home = Path.home()

    # Linux
    linux_dir = home / ".config/libreoffice/4/user/basic/Standard"
    if linux_dir.parent.parent.exists():
        return linux_dir

    # macOS
    mac_dir = home / "Library/Application Support/LibreOffice/4/user/basic/Standard"
    if mac_dir.parent.parent.exists():
        return mac_dir

    # デフォルト（Linux）
    return linux_dir


def _ensure_macro(soffice_path: str) -> Path:
    """マクロが存在しなければセットアップする。"""
    macro_dir = _get_macro_dir()

    macro_file = macro_dir / _MACRO_FILENAME
    if macro_file.exists() and macro_file.read_text().strip() == _MACRO_CONTENT.strip():
        return macro_file

    # マクロディレクトリが存在しない場合、LibreOffice を一度起動してプロファイルを初期化
    if not macro_dir.exists():
        print("Initializing LibreOffice profile...")
        subprocess.run(
            [soffice_path, "--headless", "--terminate_after_init"],
            capture_output=True,
            timeout=30,
        )
        time.sleep(2)
        macro_dir.mkdir(parents=True, exist_ok=True)

    # マクロファイルを書き込み
    macro_file.write_text(_MACRO_CONTENT)
    print(f"Macro installed: {macro_file}")

    # dialog.xlc / script.xlc が必要な場合は作成
    script_xlc = macro_dir / "script.xlb"
    if not script_xlc.exists():
        script_xlc.write_text(
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE library:library PUBLIC "-//OpenOffice.org//DTD '
            'OfficeDocument 1.0//EN" "library.dtd">\n'
            '<library:library xmlns:library='
            '"http://openoffice.org/2000/library" '
            'library:name="Standard" library:readonly="false" '
            'library:passwordprotected="false">\n'
            f'  <library:element library:name="{_MACRO_NAME}"/>\n'
            "</library:library>\n"
        )

    return macro_file


def accept_changes(
    input_path: Path,
    output_path: Path,
    timeout: int = 60,
) -> None:
    """全変更履歴を承認する。"""
    if not input_path.exists():
        print(f"Error: file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    if not input_path.suffix.lower() == ".docx":
        print(f"Error: expected .docx file: {input_path}", file=sys.stderr)
        sys.exit(1)

    soffice_path = _find_soffice()
    if soffice_path is None:
        print(
            "Error: LibreOffice (soffice) not found.\n"
            "Install: apt: sudo apt install libreoffice / "
            "brew: brew install --cask libreoffice",
            file=sys.stderr,
        )
        sys.exit(1)

    _ensure_macro(soffice_path)

    abs_input = str(input_path.resolve())
    abs_output = str(output_path.resolve())

    macro_url = f"macro:///Standard.{_MACRO_NAME}.AcceptAllChanges({abs_input},{abs_output})"

    cmd = [
        soffice_path,
        "--headless",
        "--norestore",
        macro_url,
    ]

    print(f"Running LibreOffice macro to accept all changes...")
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=timeout, text=True)
        if result.returncode != 0:
            print(f"Warning: soffice exited with code {result.returncode}", file=sys.stderr)
            if result.stderr:
                print(f"stderr: {result.stderr}", file=sys.stderr)
    except subprocess.TimeoutExpired:
        print(
            f"Error: LibreOffice timed out after {timeout}s. "
            "Try closing other LibreOffice instances.",
            file=sys.stderr,
        )
        sys.exit(1)

    if output_path.exists():
        print(f"Output: {output_path}")
    else:
        print(
            f"Error: output file was not created. "
            "LibreOffice may have encountered an issue.",
            file=sys.stderr,
        )
        sys.exit(1)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="LibreOffice マクロで .docx の全変更履歴を承認する。",
        epilog="例: python accept_changes.py input.docx output.docx",
    )
    parser.add_argument("input", type=Path, help="入力 .docx ファイル")
    parser.add_argument("output", type=Path, help="出力 .docx ファイル")
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="タイムアウト秒数（デフォルト: 60）",
    )
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    accept_changes(args.input, args.output, args.timeout)
