# SPDX-License-Identifier: AGPL-3.0-or-later
# Copyright 2026 Oruk, Inc.
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo
base = Path(__file__).resolve().parent
with ZipFile(base / "Fourier-English-Notes.ankiaddon", "w") as out:
    for name in ("manifest.json", "__init__.py", "core.py", "recognize.py", "LICENSE"):
        info = ZipInfo(name, (2026, 11, 22, 0, 0, 0))
        info.compress_type = ZIP_DEFLATED
        info.external_attr = 0o100644 << 16
        out.writestr(info, (base / "addon" / name).read_bytes())
