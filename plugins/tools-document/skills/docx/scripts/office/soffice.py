"""LibreOffice (soffice) ヘルパー。

機能:
- soffice コマンドの存在チェック
- サンドボックス環境での AF_UNIX ソケット回避（LD_PRELOAD shim）
- 引数のパススルー実行
"""

from __future__ import annotations

import argparse
import os
import shutil
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

# AF_UNIX ソケット回避用 C コード
_SHIM_SOURCE = """\
#define _GNU_SOURCE
#include <sys/types.h>
#include <sys/socket.h>
#include <dlfcn.h>
#include <errno.h>
#include <string.h>
#include <sys/un.h>
#include <netinet/in.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>

/* Intercept connect() for AF_UNIX sockets and silently succeed */
int connect(int sockfd, const struct sockaddr *addr, socklen_t addrlen) {
    int (*real_connect)(int, const struct sockaddr *, socklen_t);
    real_connect = dlsym(RTLD_NEXT, "connect");
    if (addr->sa_family == AF_UNIX) {
        return 0;
    }
    return real_connect(sockfd, addr, addrlen);
}
"""


def _needs_shim() -> bool:
    """サンドボックス環境で AF_UNIX ソケットがブロックされているか確認する。"""
    try:
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.close()
        return False
    except OSError:
        return True


def _compile_shim() -> str | None:
    """LD_PRELOAD 用の共有ライブラリをコンパイルする。"""
    if not shutil.which("gcc"):
        return None

    shim_dir = Path(tempfile.gettempdir()) / "soffice_shim"
    shim_dir.mkdir(exist_ok=True)
    shim_so = shim_dir / "socket_shim.so"

    if shim_so.exists():
        return str(shim_so)

    shim_c = shim_dir / "socket_shim.c"
    shim_c.write_text(_SHIM_SOURCE)

    try:
        subprocess.run(
            ["gcc", "-shared", "-fPIC", "-o", str(shim_so), str(shim_c), "-ldl"],
            check=True,
            capture_output=True,
        )
        return str(shim_so)
    except subprocess.CalledProcessError:
        return None


def find_soffice() -> str | None:
    """soffice コマンドのパスを検索する。"""
    path = shutil.which("soffice")
    if path:
        return path

    # macOS の一般的なパス
    mac_path = "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    if os.path.isfile(mac_path):
        return mac_path

    return None


def run_soffice(args: list[str]) -> int:
    """soffice を実行する。サンドボックス環境では自動的に shim を適用する。"""
    soffice_path = find_soffice()
    if soffice_path is None:
        print(
            "Error: LibreOffice (soffice) not found.\n"
            "Install: apt: sudo apt install libreoffice / "
            "brew: brew install --cask libreoffice",
            file=sys.stderr,
        )
        return 1

    env = os.environ.copy()

    if _needs_shim():
        shim_path = _compile_shim()
        if shim_path:
            existing = env.get("LD_PRELOAD", "")
            env["LD_PRELOAD"] = (
                f"{shim_path}:{existing}" if existing else shim_path
            )
            print("Note: applying socket shim for sandboxed environment")
        else:
            print(
                "Warning: sandboxed environment detected but gcc not available for shim",
                file=sys.stderr,
            )

    cmd = [soffice_path] + args
    result = subprocess.run(cmd, env=env)
    return result.returncode


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="LibreOffice (soffice) ヘルパー。サンドボックス環境に自動対応する。",
        epilog=(
            "例:\n"
            "  python soffice.py --headless --convert-to pdf document.docx\n"
            "  python soffice.py --headless --convert-to docx document.doc"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "soffice_args",
        nargs=argparse.REMAINDER,
        help="soffice に渡す引数",
    )
    return parser


if __name__ == "__main__":
    args = build_parser().parse_args()
    sys.exit(run_soffice(args.soffice_args))
