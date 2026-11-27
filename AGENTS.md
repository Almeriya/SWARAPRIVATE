<!--
SPDX-FileCopyrightText: 2026 MontroneDSP
SPDX-License-Identifier: GPL-3.0-or-later
-->

# SWARA XT — Agent Instructions

Repository: Almeriya/SWARAPRIVATE. Active macOS work targets SWARA XT **1.3.3** on branch `port/swaraxt-133-macos-surgical` via existing **PR #1** (do not merge unless explicitly authorized).

## Product and source

- Preserve official SWARA XT **1.3.3** production `Source/` parity except the documented Apple-specific exceptions in the 1.3.3 source profile.
- Do not invent extra Apple exceptions; record any justified new exception in the source profile and engineering report.
- Keep **JUCE 9.0.1** and the pinned Apple toolchain (Xcode 16.4 / deployment target as configured in CI).
- Do not upgrade JUCE, weaken tests, or alter production DSP/parameter contracts to manufacture green CI.

## Compilation and machines

- **GitHub Actions is the only product compilation environment.**
- This Intel Mac is for **REAPER and runtime validation only**.
- **No local compilation:** no Ninja, CMake product builds, Xcode product builds, JUCE rebuilds, CTest compilation, or sanitizer builds on this Mac.
- All native test compilation and CTest execution run on hosted runners.

## Testing and evidence

- Prefer focused hosted probes over full eight-profile matrices when diagnosing a known failure.
- Keep assertions strong; do not delete or soften checks to pass.
- **Do not regenerate, overwrite, or self-approve audio goldens.** Unresolved Mac audio authority stays `REVIEW_REQUIRED`.
- Do not modify `native_reference.py` to bypass approval.
- Attribute binaries and results to the exact source SHA that produced them.

## Apple security

- **Never** access, read, export, commit, push, or expose Apple credentials (Apple ID, App Store Connect `.p8`, Developer ID keys, `.p12`/`.pfx`, Keychain secrets, notarization tokens, provisioning material).
- CI remains secret-free. Use unsigned or ad-hoc-signed engineering builds only.
- Do not run notarization or Developer ID signing operations.

## Branch and PR discipline

- Continue on `port/swaraxt-133-macos-surgical`; update PR #1.
- Do not modify `main`, force-push, rewrite history, publish releases/tags, or change customer downloads / Gumroad / website without explicit authorization.
- Do not merge PR #1 unless the owner explicitly requests it.

## GITHUB ACTIONS NO-WAIT POLICY

Coding agents must never remain active solely to await GitHub Actions completion. Agents may inspect completed workflow evidence once at the beginning of a task when required. After implementing, committing and pushing changes, dispatch the relevant CI workflow once, report the dispatch information and end the session. Do not poll, watch, sleep, repeatedly query GitHub, or start a new workflow based on results that have not yet arrived. CI results are reviewed in a separate user-initiated session.

**AGENTS MUST NOT POLL OR WAIT FOR GITHUB ACTIONS.**

Permitted workflow: `INSPECT COMPLETED EVIDENCE → IMPLEMENT → COMMIT → PUSH → DISPATCH → REPORT → EXIT`

**Agents must work, commit, push, dispatch CI and exit.**

## Policy files (tracked)

These files are intentional repository assets and must remain committed:

- `AGENTS.md`
- `.cursor/rules/macos-engineering.mdc`
- `.cursor/rules/ci-no-polling.mdc`
