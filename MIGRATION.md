# Recovery and migration: v1 to v2

Only the previous executable, dashboard, architecture SVG and minimal SPDX record were available in the working runtime. The claimed v1 full archive and reports were not available there. Source `.py` files were recovered from the executable; their original archive hash is recorded in RECOVERY.json. New reports are a reconstruction, not a byte-preserving edit of inaccessible originals.

## Behavioral changes
- v1 weighted strength/transferability/outcome flags into capability ratings and could issue PATH_VERIFIED_IN_CURRENT_SCOPE from heuristic cutoffs. v2 removes this numerical person-capability pipeline. Evidence is dated, operation-scoped and separately required for demand, delivery, access and task roles. No outcome status asserts field verification.
- v1 accepted more missing/defaulted resource fields. v2 rejects incomplete money/time declarations, NaN, boolean-as-money, negative amounts, conflicting currencies, duplicate IDs and duplicate JSON keys.
- Route selection now evaluates the **joint economic and technical** feasible subsets before minimizing the energy upper bound. Unknown or incomparable energy is not zero. A cost fallback is explicitly labelled.
- v1 independently computed repair, commons and newcomer reserves from gross and rounded individual amounts. These can over-allocate under extreme inputs. v2 reserves repair first, applies negotiated pool rates to the remainder, and allocates integer cents exactly; disputes retain their shares in a hold.
- v1 verification did not check exact event sequence numbers. v2 checks keys, sequences, links, hashes and optional external checkpoints, and refuses to append to an inconsistent chain. This is not protection against a privileged administrator who can rewrite all files.
- v1 CLI syntax in the prior prose did not match all actual parser flags. v2 README commands are smoke-tested against the delivered executable.
- v2 public receipts omit detailed financial and evidence fields. Raw local inputs remain private, unencrypted files under the user's control.

## Migration is intentionally not automatic
Run `python lucidecon.pyz audit-v1 old_profile.json` for a migration reminder. Do not map a 0.8 rating into a reviewed pass. Use `init`, provide explicit assumptions, append real evidence and renew scope-bound consent. Retain old results as historical records; never overwrite them with a new conclusion.

The recovered v1 source is not included on the v2 import path. Its historical claims remain visible for audit, not endorsed as current runtime behavior.
