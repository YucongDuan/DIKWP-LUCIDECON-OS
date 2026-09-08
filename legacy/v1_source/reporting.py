from __future__ import annotations
import json
from pathlib import Path
from typing import Any
from .common import write_json, sha256_file, merkle_root

def write_path_report(outdir: str | Path, portfolio: dict[str, Any], passport: dict[str, Any]) -> dict[str, Any]:
    d=Path(outdir); d.mkdir(parents=True,exist_ok=True)
    write_json(d/"capability_passport.json",passport)
    write_json(d/"path_portfolio.json",portfolio)
    lines=[
        "# DIKWP-LUCIDECON Path Report",
        "",
        f"Profile: `{portfolio['profile_id']}`",
        f"Portfolio status: **{portfolio['portfolio_status']}**",
        "",
        "## Bounded DIKWP capability passport",
    ]
    for role,rec in passport["dikwp_roles"].items():
        lines.append(f"- {role}: {rec['bounded_capability']:.3f} — {rec['status']} ({rec['evidence_count']} evidence item(s))")
    lines += ["","## Opportunity results"]
    for r in portfolio["results"]:
        lines += [
            f"### {r['opportunity_title']}",
            f"- Status: **{r['status']}**",
            f"- Saturation: {r['market']['saturation']:.3f}",
            f"- Commoditization pressure: {r['market']['commoditization_pressure']:.3f}",
            f"- First-mover capture: {r['market']['first_mover_capture']:.3f}",
            f"- Opportunity slack: {r['market']['opportunity_slack']:.3f}",
            f"- Largest DIKWP gaps: {', '.join(k+':'+str(v) for k,v in sorted(r['dikwp_gaps'].items(), key=lambda x:-x[1])[:2])}",
            "",
        ]
    lines += [
        "## Boundary",
        "A result of NO_CURRENT_VERIFIED_PATH applies only to the submitted person-controlled evidence, market model, time horizon and constraints. It is not a verdict on a person's worth or future.",
    ]
    (d/"path_report.md").write_text("\n".join(lines),encoding="utf-8")
    files=sorted([p for p in d.iterdir() if p.is_file()])
    manifest={p.name:sha256_file(p) for p in files}
    write_json(d/"output_manifest.json",manifest)
    return {"files":list(manifest),"merkle_root":merkle_root([f"{k}:{v}" for k,v in sorted(manifest.items())])}
