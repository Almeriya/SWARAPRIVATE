<!--
SPDX-FileCopyrightText: 2026 MontroneDSP
SPDX-License-Identifier: GPL-3.0-or-later
-->

# Native audio-reference owner decision (1.3.3 macOS)

`mode=full` remains blocked until the owner explicitly admits the complete applicable
reference set. Candidates never self-approve. Hashes must not be regenerated from
macOS candidate output.

## Already approved (narrow)

| Family | Scope | Status |
| --- | --- | --- |
| Classic Q23 (8 public 1.3.3 cases) | Intel + ARM64, Debug + Release only | **APPROVED** (`CLASSIC_OWNER_APPROVAL`) |

Not covered by that approval: Classic ASan/UBSan or TSan; Dual SVF; Host SRC;
integrated FX; any other native floating-point family; full-gate
`require_approved_authority(None, None, None)`.

## Still required before green `mode=full`

For each remaining family below, owner must approve or reject with architecture,
profile, source SHA, toolchain, and independent baseline identified.

| Family | Independent baseline candidates | Mac evidence status | Decision |
| --- | --- | --- | --- |
| Classic sanitizer profiles | Public 1.3.3 Classic Q23 | Not separately approved | `REVIEW_REQUIRED` |
| Dual SVF | Public / Linux-Windows tables; historical 1.3.1 Mac selectors | Historical selector/architecture splits; do not rewrite FAIL→PASS | `REVIEW_REQUIRED` |
| Host SRC | Public / Phase3 / historical Mac captures | Historical Intel/ARM observations exist; not current admission | `REVIEW_REQUIRED` |
| Integrated FX | Public / Phase3 tables | Historical ARM observations; Intel often matched tables historically | `REVIEW_REQUIRED` |
| Other native FP references | Existing `Tests/References/` and protected Mac headers | Fail-closed until listed | `REVIEW_REQUIRED` |

## Gate behavior (unchanged until approval)

- `APPROVED_REFERENCES` maps stay empty.
- `TESTS` stays empty.
- `require_approved_authority(arch, profile)` raises `BLOCKED`.
- Full gate `require_approved_authority(None, None, None)` raises `BLOCKED`.

## Owner action

Approve or reject the complete remaining set in one decision. After explicit approval,
encode only that set in a fail-closed admission policy with mutation tests. Unknown
architecture, profile, SHA, or unapproved family must still fail.
