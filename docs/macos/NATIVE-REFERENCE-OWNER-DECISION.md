<!--
SPDX-FileCopyrightText: 2026 MontroneDSP
SPDX-License-Identifier: GPL-3.0-or-later
-->

# Native audio-reference policy (1.3.3 macOS)

Owner authorization: replace the unconditional native-reference veto with an
evidence-based gate. Candidates never admit their own hashes.

## Rule

**Passing CTest against an immutable, independently established reference is
valid qualification evidence. Passing against a candidate-generated or
substituted reference is not.**

`require_approved_authority` verifies independent reference provenance
(`CurrentAudioGoldens.h` public 1.3.3 blob, protected Dual SVF selectors) and
rejects unknown architecture/profile, missing evidence, regenerated goldens,
and unapproved substitutions. It no longer raises solely because
`APPROVED_REFERENCES` is empty.

## Family audit

| Family | Classification | Authority |
| --- | --- | --- |
| Classic Q23 (8) | `REFERENCE_VERIFIED` | Public 1.3.3 header blob `6ddd3aa0…`; owner-approved Debug/Release; same header for sanitizer profiles |
| Integrated FX | `REFERENCE_VERIFIED` | Same protected `CurrentAudioGoldens.h` `kIntegrated` table |
| Dual SVF section-2 | `REFERENCE_VERIFIED` | Protected Mac selector blob `59a37d98…` → `DualSvfCurrentLinuxGoldens.h` |
| Dual SVF integration | `REFERENCE_VERIFIED` | Protected Mac audit blob `a9a4cab9…` |
| Host SRC | `REFERENCE_VERIFIED` | `ExactParityGoldens.h` `kSrc` independent table |

Any real hash mismatch fails CTest. That is a product/test failure, not a
policy deadlock.

## Still fail-closed

Wrong SHA, missing/skipped CTest, failed audio hash, missing sanitizer negative
controls, incomplete matrix, missing AU/VST3 candidate, mismatched candidate
hashes, altered reference provenance.
