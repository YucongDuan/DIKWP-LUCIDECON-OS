from __future__ import annotations
import hashlib, json, math, re
from datetime import date
from pathlib import Path
from typing import Any

class ValidationError(ValueError):
    """Malformed or incomplete declarations; never silently treated as zero."""

MAX_INT = 10**12

def integer(v: Any, name: str, minimum: int = 0, maximum: int = MAX_INT) -> int:
    if type(v) is not int or not minimum <= v <= maximum:
        raise ValidationError(f'{name}: integer in [{minimum}, {maximum}] required')
    return v

def flag(v: Any, name: str) -> bool:
    if type(v) is not bool:
        raise ValidationError(f'{name}: explicit boolean required')
    return v

def text(v: Any, name: str, maximum: int = 4000) -> str:
    if not isinstance(v,str) or not v.strip() or len(v) > maximum:
        raise ValidationError(f'{name}: nonempty text of at most {maximum} characters required')
    return v

def identifier(v: Any, name: str) -> str:
    if not isinstance(v,str) or not re.fullmatch(r'[A-Za-z0-9_.-]{1,80}',v):
        raise ValidationError(f'{name}: short ASCII identifier required')
    return v

def day(v: Any, name: str) -> date:
    try:
        if not isinstance(v,str) or len(v)!=10: raise ValueError()
        return date.fromisoformat(v)
    except ValueError as exc:
        raise ValidationError(f'{name}: ISO YYYY-MM-DD required') from exc

def array(v: Any, name: str, maximum: int = 100) -> list:
    if not isinstance(v,list) or len(v)>maximum:
        raise ValidationError(f'{name}: list of at most {maximum} items required')
    return v

def interval(v: Any, name: str, minimum: int = 0, maximum: int = MAX_INT) -> tuple[int,int]:
    if not isinstance(v,list) or len(v)!=2: raise ValidationError(f'{name}: [lower, upper] required')
    lo,hi=(integer(x,name,minimum,maximum) for x in v)
    if lo>hi: raise ValidationError(f'{name}: lower exceeds upper')
    return lo,hi

def unique(items: list[dict], key: str, name: str) -> None:
    ids=[identifier(x.get(key),name) for x in items]
    if len(ids)!=len(set(ids)): raise ValidationError(f'{name}: duplicate identifiers')

def canonical(x: Any) -> str:
    return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)

def digest(x: Any) -> str:
    return hashlib.sha256(canonical(x).encode('utf-8')).hexdigest()

def _pairs(pairs):
    d={}
    for k,v in pairs:
        if k in d: raise ValidationError(f'duplicate JSON key: {k}')
        d[k]=v
    return d

def parse(s: str) -> Any:
    if len(s.encode('utf-8')) > 2_000_000: raise ValidationError('JSON input exceeds 2 MB')
    try:
        return json.loads(s,object_pairs_hook=_pairs,parse_constant=lambda x: (_ for _ in ()).throw(ValidationError(f'non-finite number: {x}')))
    except (json.JSONDecodeError,RecursionError) as exc:
        raise ValidationError(f'invalid JSON: {exc}') from exc

def load(p: str|Path) -> Any:
    p=Path(p)
    if p.stat().st_size>2_000_000: raise ValidationError('JSON input exceeds 2 MB')
    return parse(p.read_text(encoding='utf-8-sig'))

def write(p: str|Path, obj: Any) -> None:
    p=Path(p); p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(obj,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+'\n',encoding='utf-8')

def signed(obj: dict, key: str='content_hash') -> dict:
    return {**obj,key:digest(obj)}
