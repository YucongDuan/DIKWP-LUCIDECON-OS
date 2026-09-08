"""Build a deterministic standalone archive; run from any current directory."""
from pathlib import Path
import zipfile
ROOT=Path(__file__).resolve().parents[1]
TARGET=ROOT/'lucidecon.pyz'
with TARGET.open('wb') as f:f.write(b'#!/usr/bin/env python3\n')
with zipfile.ZipFile(TARGET,'a',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    sources=[(p.relative_to(ROOT/'src').as_posix(),p.read_bytes()) for p in sorted((ROOT/'src'/'lucidecon').glob('*.py'))]
    sources.append(('__main__.py',b'from lucidecon.cli import main\nraise SystemExit(main())\n'))
    for name,data in sorted(sources):
        info=zipfile.ZipInfo(name,(2026,9,7,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
        z.writestr(info,data)
print(TARGET)
