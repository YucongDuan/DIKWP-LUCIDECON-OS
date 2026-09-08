"""Check the delivered manifest. This verifies consistency, not publisher identity."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

def verify(root: Path) -> dict:
    manifest = json.loads((root / 'MANIFEST.json').read_text(encoding='utf-8'))
    errors = []
    seen = set()
    for item in manifest['files']:
        name = item['path']
        rel = Path(name)
        if rel.is_absolute() or '..' in rel.parts or name in seen:
            errors.append('INVALID_PATH:' + name)
            continue
        seen.add(name)
        p = root / rel
        if p.is_symlink() or not p.is_file():
            errors.append('MISSING_OR_SYMLINK:' + name)
            continue
        b = p.read_bytes()
        if len(b) != item['size_bytes'] or hashlib.sha256(b).hexdigest() != item['sha256']:
            errors.append('MISMATCH:' + name)
    return {'valid': not errors, 'files_checked': len(seen), 'errors': errors,
            'scope': 'Listed release files; extra user-generated files are allowed.',
            'publisher_authentication': False,
            'warning': 'Protect the manifest or compare an independently retained archive checksum.'}

if __name__ == '__main__':
    try:
        result = verify(ROOT)
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result['valid'] else 1)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'valid': False, 'error': str(exc)}), file=sys.stderr)
        raise SystemExit(2)
