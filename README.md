[English](README.md) · [中文](README_CN.md) · [Choose a tool](ECOSYSTEM.md) · [Research directory](https://github.com/YucongDuan/YucongDuan/blob/main/REPOSITORY_DIRECTORY.md)

[![Tests](https://github.com/YucongDuan/DIKWP-LUCIDECON-OS/actions/workflows/tests.yml/badge.svg)](https://github.com/YucongDuan/DIKWP-LUCIDECON-OS/actions/workflows/tests.yml) · Python 3.10+ · Apache-2.0

# DIKWP-LUCIDECON-OS 2.0

Created by Yucong Duan (段玉聪).
## Evidence-scoped transparent economy lab

A local planning tool for ordinary people and small teams: test a bounded opportunity, expose uncertainty and entry barriers, compare authorized execution routes, and account for an agreed contribution pool exactly. It is not a job oracle, a human-ranking service, a broker or a payment system.

## Start without installation
Open `lucidecon.html` in a current desktop browser. It runs locally with no external requests or automatic persistence. Built-in examples are synthetic. JSON imports/exports may contain sensitive business details; keep them private. The browser is a preview; Python is the full reference implementation.

## Python (3.10 or later, standard library only)
From the extracted release directory:
```sh
python lucidecon.pyz inspect
python lucidecon.pyz demo --output outputs/my_first_demo
python lucidecon.pyz init --output my_case.json
python lucidecon.pyz assess my_case.json --output outputs/personal_01
python lucidecon.pyz replay outputs/personal_01
python lucidecon.pyz verify outputs/personal_01/ledger.jsonl
python lucidecon.pyz simulate-market examples/market.json --output outputs/new_market.json
python lucidecon.pyz settle examples/settlement.json --output outputs/new_settlement.json
```
Use a fresh output directory; existing runs are not overwritten. On Windows, `py -3` can replace `python`; `run_demo.bat` is included. On Linux/macOS, use `python3` or `./run_demo.sh`.

The template starts as SYNTHETIC. Replace its assumptions and fictional evidence before use. Supply the actual assessment date, explicit horizon, purpose-bound consent and expiry. USER_SUBMITTED means submitted, not independently authenticated. No internet source checking is performed.

## Interpret results
`ROBUST_WITHIN_DECLARED_SCENARIOS`: submitted lower bounds meet the target in every listed scenario, after resource/route gates and required evidence declarations. Not a real-world guarantee.
`BOUNDED_PILOT_ONLY`: a plausible upside remains, but not all scenario lower bounds meet the target.
`INSUFFICIENT_EVIDENCE`: evidence is absent, stale, out of scope, self-reported or not accepted. This is not a no-path proof.
`NO_CURRENT_PATH_IN_SCOPE`: under the reviewed-as-declared inputs, even the upper cash bound of each authorized route misses the stated target.
`RESOURCE_BLOCKED`, `BLOCKED_BY_RIGHTS`, and `NO_FEASIBLE_EXECUTION_ROUTE` identify the respective binding gate.

Each opportunity uses the full budget independently. Do not sum separate outputs into a feasible portfolio. Amounts are integer minor currency units, not floating-point money. Protected living reserves should be excluded from spendable funds. Cash results exclude unlisted tax, financing, living expenses and unpaid time.

## Full receipts and outcomes
Each run includes private input, assessment, minimized public receipt, semantic trace, report, ledger and checkpoint. `public_receipt.json` omits evidence and financial details, but its alias/hash may still be linkable.

To add an outcome, create a JSON object with `id`, `actor`, `assessment_hash`, `opportunity_id`, `result` (IMPROVED / NO_CHANGE / WORSENED / NOT_MEASURED), and `evidence_ref` for measured results. Then:
```sh
python lucidecon.pyz record-outcome outputs/personal_01 outcome.json
```
Outcomes are new records. They do not rewrite an original decision or prove causality. For a new assessment, change the evidence/assumptions explicitly and write to a new directory.

## Source, tests and distribution verification
```sh
PYTHONPATH=src python -m unittest discover -s tests -v
python tools/build_zipapp.py
python tools/verify_release.py
```
Windows PowerShell: `$env:PYTHONPATH='src'` before running the tests. CI configuration targets Python 3.10–3.13 but no remote CI result is claimed in this delivery. Build/install dependencies are not runtime dependencies; using the .pyz requires no package installation.

`legacy/v1_source` contains recovered, unpatched historical v1 source for inspection, not the default runtime. Migration requires new inputs; old subjective capability scores are not silently promoted to reviewed evidence. See MIGRATION.md.

## Boundaries
All sample markets, counterparties, reviews, prices, energy and demand are synthetic declarations. Quality, reviewer identity and permission declarations are not authenticated. Energy is estimated unless a declared measurement reference is present; the tool itself reads no power sensor. No real payments, model/API/GUI calls, automatic employment decisions or external actions occur. Local files are not encrypted. A hash chain establishes internal consistency, not truth or resistance to a malicious file administrator; retain an independent head checkpoint for truncation/rewrite detection.

Code: Apache-2.0. Documentation and original examples: CC BY 4.0. Prepared for the Yucong Duan DIKWP programme; no external institutional endorsement or economic-effectiveness certification is claimed. See reports and SOURCES.json.

## Download, run and verify

- [Versioned release and original full delivery](https://github.com/YucongDuan/DIKWP-LUCIDECON-OS/releases/tag/v2.0.0)
- [Offline browser app](lucidecon.html) — download the source archive, extract it, then open this HTML file locally. GitHub's file viewer displays source.
- [Publication verification](publication/VALIDATION_2026-09-08.md): 88 local tests passed on 8 September 2026.
- [Source](src/) · [Tests](tests/) · [Archive provenance](publication/PROVENANCE.json)

## Contribute a reproducible result

Run an example, report a failing case with its expected result, or add a documented extension. Use synthetic or anonymized inputs. If useful, star the repository, cite its version and share its canonical link. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Current interface presentation

[Open the interface source](lucidecon.html) from the current repository download. See [interface and authorship notes](INTERFACE_NOTES.md) for English coverage, report generation and validation scope.
