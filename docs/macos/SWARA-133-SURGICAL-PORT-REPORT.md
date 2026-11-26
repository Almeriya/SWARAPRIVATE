# SWARA XT 1.3.3 macOS surgical port — engineering report

Status: **PARTIAL**. Engineering development only. Not a public macOS release.

This report records actual work on `port/swaraxt-133-macos-surgical`. Historical 1.3.1 Intel 134/136 and ARM 131/136 results remain original evidence. They are not 1.3.3 qualifications.

## Baselines

| Tree | Repository | Revision |
| --- | --- | --- |
| Destination Mac 1.3.1 | `Almeriya/SWARAPRIVATE` `main` | `64fa3f6640706db5ae7181bd9e694828b0284e3b` |
| Official product 1.3.3 | `montronedsp/SWARAXT` `v1.3.3` | `6ea598e47fb0347d23ffa538a64b02318187a7ed` |
| Integration HEAD | `Almeriya/SWARAPRIVATE` `port/swaraxt-133-macos-surgical` | `5722f902ab8d09c3cb9a43a32014dd2420bd36c0` |

Frozen inputs were verified before edits. Later public `main` packaging/README/Linux-installer commits were not tracked.

File-by-file classification: `docs/macos/SWARA-133-SOURCE-INVENTORY.md`.

## Source integration

Surgical file copies and semantic overlays. No `git merge`, no `git checkout public -- Source/`, no history rewrite.

| Stage | Commit | Ported | Mac exceptions retained |
| --- | --- | --- | --- |
| A identity | `17e1978` | Product version 1.3.3, 1.3.3 source profile, packaging strings | OBJC/OBJCXX, AU, macOS 11.0, JUCE 9.0.1 pin, no Standalone packaging |
| B tuning | `22eec48` | `splitSignedPeriod`, finite pitch, factory/negative-degree math | Apple `RealFromChars.h` + pinned `fast_float`; no public `std::from_chars` |
| C Classic cutoff | `7f2ab1a` | Unrounded firmware cutoff, `knobCutoffTrimBytes_`, Classic-only trim | MSVC `exp2` guard; Dual SVF firmware-byte path; Apple FP `contract(off)` |
| D MIDI/looper | `4a41e64` | CC120 emergency silence, delay wrap, looper hold, SRC lookahead drain | Apple FP guards on host SRC and DC path |
| E sequencer | `6c653cf` | `GrooveClock.h`, host tick inverse, timing-key remap, `SequenceState` writer/revise | Existing sequencer MIDI ownership kept with public stop/realign rules |
| F processor/editor | `4562068` | Bounded preset reads, restore results/notifications, bus layout, LookAndFeel `shared_ptr` | `SWARAXT_JUCE_RESTORE_COMPLETION` **not** enabled on Apple |
| H CI identity | `5722f90` | Workflow/policy/gate point at `Almeriya/SWARAPRIVATE`, private=true | `native_reference.py` still fail-closed; historical 1.3.1 profile intact |

## Mac-specific adaptations

Retained:

- `enable_language(OBJC OBJCXX)`, `CMAKE_OSX_DEPLOYMENT_TARGET=11.0`, `x86_64;arm64`
- Bundle `com.MontroneDSP.SwaraXT`, manufacturer `MnTr`, plugin `SwXT`
- JUCE 9.0.1 `e18f7f506c0b96f2c738a0bcd7fe6467a5005ad8`
- Apple `RealFromChars` / `fast_float`
- `#pragma clang fp contract(off)` in `HostResampler.cpp` and `PolyphaseFirResampler.h`
- Dual SVF Apple reference selectors (historical failures not rewritten as PASS)
- 1.3.1 source profile, goldens, and original Dual SVF / ARM failures

Deliberately not enabled on Apple:

- `cmake/Juce901RestoreCompletion.cmake` — CRLF Windows JUCE 9.0.1 overlay; input hashes not verified against an Apple LF checkout. Public 1.3.3 also enables it only on WIN32. Processor/editor keep `#if defined(SWARAXT_JUCE_RESTORE_COMPLETION)` paths, which compile as the `uncertain` fallthrough on Mac.
- `Juce901PngError.cmake` — MSVC libpng `longjmp` stack issue; not applied on Apple.

## Plugin identity

Intended Mac package remains **AU + VST3**, universal when both slices are present. Standalone and Skin Editor stay out of the production package.

Local Intel configure used `-DCMAKE_OSX_ARCHITECTURES=x86_64` only. That candidate must not be described as universal.

## Tuning

Local Intel Release executables:

- `SwaraXTTuningTableTests`: **PASS**
- Factory SCL/KBM/SWT/negative-degree coverage is in that suite and Stage B unit work
- Parameter IDs were not rewritten; `SwaraXtParameterLayout.cpp` remains an Apple parser exception

JUCE-backed Scala import / saved-session tuning roundtrips: **NOT_RUN** (plugin binaries not yet produced at the time this section was first written).

## Classic cutoff

- `SwaraXTCutoffAuthorityTests`: **0 failures**
- `SwaraXTIR3109BoardTests`: **0 failures**
- First-divergent-sample audio investigation vs Windows/Linux goldens: **NOT_RUN**
- Dual SVF Mac fingerprints: not rebaselined

## MIDI / looper

- `SwaraBoardDelayWrapTests`: **PASS**
- `SwaraBoardLooperProductionTests`: **failures=0**, diagnostic `decision=REVISE` (model comparison, not a silent PASS rewrite)
- CC120 / NRPN plugin-console tests: **NOT_RUN** (require the plugin target)

## Sequencer

- `SwaraXTGrooveClockTests`: **PASS** (`groove clock checks passed`)
- HostGroove, SequencerSafety, ArpAutomationRace, SequencerMidi: **NOT_RUN** (plugin/JUCE console tests)

## Restoration

Code ported. Restore-completion overlay **not** active on Apple. RestoreCompletion listener-failure modes that need the overlay are **NOT_RUN / REVIEW_REQUIRED**. Preset/host-state plugin tests: **NOT_RUN**.

## Intel local

Host: Intel Mac, macOS 13.7.8, Xcode 15.2 / Apple Clang 15.0.0 / SDK 14.2. Hosted CI remains Xcode 16.4. Local toolchain difference is recorded; CI identity checks were not relaxed.

Configure: isolated `build-intel-133`, Ninja, Release, `x86_64`, Standalone OFF, Skin Editor OFF, tests ON. JUCE from existing pin `SWARA_XT_1.2.3_MAC_RELEASE/SWARAXT/.cache/JUCE` at `e18f7f506c0b96f2c738a0bcd7fe6467a5005ad8`. Nested `shruthi-1/avrlib` populated locally at `af7266e5b48ae20c0f83d4352c75c1068545cffc` after a shallow submodule init left it empty (`git://` nested URL).

| Item | Result |
| --- | --- |
| CMake configure | PASS |
| GrooveClock / TuningTable / CutoffAuthority / IR3109 / DelayWrap / Looper | PASS as above |
| AU / VST3 x86_64 Release | PASS compile; x86_64-only; ad-hoc sealed |
| Full CTest | NOT_RUN |
| auval | COLLISION: loaded system 1.3.1, not this candidate |
| pluginval / Steinberg validator | NOT_RUN |
| REAPER AU/VST3 | NOT_RUN (manual owner step required) |

REAPER 7.86 is installed. No existing Swara XT AU/VST3 was found in `~/Library/Audio/Plug-Ins/{Components,VST3}` at the start of this work. A candidate must still use a reversible install path; this report does not claim an auditory check.

## ARM CI / full CI

Not dispatched. Full matrix is reserved for after a coherent local Intel plugin build.

Stage H updated `.github/workflows/macos-qualification.yml`, `policy.py`, `ci.py`, and `gate.py` so jobs no longer skip on `RIG-AUDIO/SW2` / public-repo guards. Destination identity is `Almeriya/SWARAPRIVATE` with `SWARAXT_REPOSITORY_PRIVATE=true`. Secret-free. No Apple credentials, Developer ID, or notarization.

`native_reference.py` still returns **REVIEW_REQUIRED** / fail-closed. No Mac audio golden was admitted.

## Audio authority

**REVIEW_REQUIRED**. Historical Dual SVF / ARM fingerprint failures are preserved. New Mac hashes must not self-approve.

## Package

Unsigned **x86_64-only** development candidate (not universal):

| Bundle | Arch | Mach-O SHA-256 |
| --- | --- | --- |
| `Swara XT.component` | x86_64 | `a7c9b6391bb034244d4f3a5c55f94d764c3b794936716e9ba8fc60d7e9fc8997` |
| `Swara XT.vst3` | x86_64 | `948b5b26c0e21d683c52f4e118e8da2ef8ace204bc703f9116d5b58139a5227e` |

Plist identity: `com.MontroneDSP.SwaraXT`, `CFBundleShortVersionString` 1.3.3, AudioComponent version `0x10303`, type `aumu`, subtype `SwXT`, manufacturer `MnTr`. Ad-hoc sealed (`flags=0x2`), not Developer ID.

Reversible user-folder copies (do not replace `/Library/Audio/Plug-Ins/Components/Swara XT.component`):

- `~/Library/Audio/Plug-Ins/Components/Swara XT 1.3.3-dev-intel.component`
- `~/Library/Audio/Plug-Ins/VST3/Swara XT 1.3.3-dev-intel.vst3`

Rollback: delete those two versioned folders. The system 1.3.1 AU was left in place.

## Security inspection

Staged commits were scanned for credential filenames (`.p8`, `.p12`, `.pfx`, AuthKey, notary store). **PASS** on committed tree. Nested avrlib copy is local working tree only and is not committed. CI remains secret-free.

## PR

Branch: `port/swaraxt-133-macos-surgical`  
HEAD: `5722f902ab8d09c3cb9a43a32014dd2420bd36c0`  
PR URL: opened against `Almeriya/SWARAPRIVATE` after this report commit; keep unmerged while gates remain blocked.

## Untested / remaining blockers

- Local AU/VST3 link and bundle identity (see amendment)
- plugin-console MIDI, host-groove, restore, and sequencer suites
- auval, pluginval, Steinberg validator
- REAPER load, MIDI, transport, Classic/Dual SVF listening, 1.3.1 session restore
- Hosted Intel and ARM64 preflight/smoke/native/gate
- Independent Mac audio-reference admission
- Universal two-slice candidate
- Apple JUCE restore-completion overlay (explicitly not enabled)

## Final assessment

**PARTIAL / BLOCKED** for qualification and release.

Source integration Stages A–F and CI identity Stage H are on the branch with fail-closed audio authority. Mandatory host, validator, hosted matrix, and audio-reference gates remain open.

---

## Amendment — local Intel plugin build

1. First compile failed: nested `third_party/shruthi-1/avrlib` was uninitialized (`avrlib/base.h` missing). Local copy of pinned SHA `af7266e5b48ae20c0f83d4352c75c1068545cffc` unblocked includes. Not committed.
2. `ninja -j2 SwaraXT_AU SwaraXT_VST3` Release x86_64 then **succeeded**. Bundles are x86_64-only, version 1.3.3 in Info.plist, ad-hoc sealed.
3. `auval -v aumu SwXT MnTr` **succeeded as a validator run** but reported `Component Version: 1.3.1 (0x10301)`. A system-installed `/Library/Audio/Plug-Ins/Components/Swara XT.component` still owns that four-character identity. The 1.3.3 candidate was **not** the unit auval loaded. The system 1.3.1 was not moved or overwritten.
4. REAPER 7.86 is installed. Owner must rescan and instantiate **VST3** `Swara XT 1.3.3-dev-intel` from the user VST3 folder. AU instantiation in REAPER may still bind the system 1.3.1. No human listening check is claimed.
5. Hosted Intel/ARM matrix was not dispatched from this session.
