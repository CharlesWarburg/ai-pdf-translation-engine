#!/usr/bin/env python3
"""Download DejaVuSans.ttf into app/fonts/ for Unicode PDF support. Safe to run multiple times."""

import os
import sys
import zipfile
from io import BytesIO
from urllib.request import urlopen

# SourceForge: dejavu 2.37, sans-only zip (single TTF)
DEJAVU_SANS_ZIP = "https://downloads.sourceforge.net/project/dejavu/dejavu/2.37/dejavu-sans-ttf-2.37.zip"
FONT_FILENAME = "DejaVuSans.ttf"


def main() -> None:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fonts_dir = os.path.join(repo_root, "app", "fonts")
    target = os.path.join(fonts_dir, FONT_FILENAME)

    if os.path.isfile(target):
        print(f"Already present: {target}", file=sys.stderr)
        return

    os.makedirs(fonts_dir, exist_ok=True)
    print(f"Downloading DejaVu Sans from SourceForge...", file=sys.stderr)
    with urlopen(DEJAVU_SANS_ZIP, timeout=60) as resp:
        data = resp.read()
    with zipfile.ZipFile(BytesIO(data), "r") as zf:
        # zip may have root folder (e.g. dejavu-sans-ttf-2.37/DejaVuSans.ttf)
        candidates = [n for n in zf.namelist() if n.endswith(FONT_FILENAME)]
        if not candidates:
            raise SystemExit(f"Zip does not contain {FONT_FILENAME}")
        with zf.open(candidates[0]) as src:
            with open(target, "wb") as dst:
                dst.write(src.read())
    print(f"Wrote {target}", file=sys.stderr)


if __name__ == "__main__":
    main()
