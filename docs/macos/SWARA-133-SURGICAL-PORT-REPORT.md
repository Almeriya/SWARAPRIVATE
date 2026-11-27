# SWARA XT 1.3.3 macOS surgical port — engineering report

Status: **PARTIAL**. Engineering development only. Not a public macOS release.

This report records actual work on `port/swaraxt-133-macos-surgical`. Historical 1.3.1 Intel 134/136 and ARM 131/136 results remain original evidence. They are not 1.3.3 qualifications.

## Baselines

| Tree | Repository | Revision |
| --- | --- | --- |
| Destination Mac 1.3.1 | `Almeriya/SWARAPRIVATE` `main` | `64fa3f6640706db5ae7181bd9e694828b0284e3b` |
| Official product 1.3.3 | `montronedsp/SWARAXT` `v1.3.3` | `6ea598e47fb0347d23ffa538a64b02318187a7ed` |
| Integration HEAD | `Almeriya/SWARAPRIVATE` `port/swaraxt-133-macos-surgical` | `ca3ccf363d5706781a30a5310b1408f719b64ee3` |

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
| H CI identity | `5722f90` | Workflow/policy/gate point at `Almeriya/SWARAPRIVATE` | Corrected later to public visibility; `native_reference.py` fail-closed |
| H2 visibility + parity | `8b6a83e` | Fail-closed `SWARAXT_REPOSITORY_PRIVATE=false`; PatchBridge arp bounds; Shruthi Part; AVR vowel wrap; PNG import; `AvrlibHdVowelPhaseWrapTests` | Five Apple exceptions only |

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
| auval | Two `aumu SwXT MnTr` registrations. First pass loaded system 1.3.1. After registrar restart: **1.3.3 (`0x10303`) VALIDATION SUCCEEDED** |
| pluginval / Steinberg validator | NOT_RUN |
| REAPER AU/VST3 | NOT_RUN (manual owner step required) |

REAPER 7.86 is installed. No existing Swara XT AU/VST3 was found in `~/Library/Audio/Plug-Ins/{Components,VST3}` at the start of this work. A candidate must still use a reversible install path; this report does not claim an auditory check.

## ARM CI / full CI

**GitHub Actions is the only compilation and automated qualification path.** Local product/test compilation on this Intel Mac is stopped and must not be resumed for this mission.

`Almeriya/SWARAPRIVATE` is **public**. Fail-closed admission requires `GITHUB_REPOSITORY=Almeriya/SWARAPRIVATE` and `SWARAXT_REPOSITORY_PRIVATE=false` (matching `github.event.repository.private`). Repository settings were not changed. Secret-free. No Apple credentials, Developer ID, or notarization.

Push default execution mode is **`build`** (preflight + universal candidate), not `full`, so minor source pushes do not re-run smoke/native. One complete `full` qualification is reserved for the final source SHA after the targeted build is green.

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
PR: https://github.com/Almeriya/SWARAPRIVATE/pull/1 (keep unmerged while gates remain blocked)

## Remaining blockers

- Harness compile defect **fixed** on `f2c9433`; full matrix https://github.com/Almeriya/SWARAPRIVATE/actions/runs/45880728588 **FAILED** on assertions / timeouts (see amendment)
- ARM64 native: 15 CTest assertion failures (audio goldens, restore-completion overlay, Correctness/DualSvf/Workflow/Playback)
- Intel native + ARM64 ASan: **INTERRUPTED** (compile timeouts) — not product assertions; tests **NOT_RUN**
- Independent Mac audio-reference admission remains **REVIEW_REQUIRED**
- AU fourcc collision `aumu SwXT MnTr` with system 1.3.1 — owner confirmation required
- Interactive REAPER GUI / listening: **OWNER ACTION REQUIRED**
- Apple JUCE restore-completion overlay still not enabled

## Final assessment

**PARTIAL / BLOCKED** for merge and release.

Compile recovery for PresetRestore is complete on `f2c9433`. Merge remains blocked by audio authority **REVIEW_REQUIRED**, restore-completion overlay off on Apple, remaining host/assertion failures, and incomplete Intel/sanitizer native execution.

---

## Amendment — local Intel plugin build (superseded for compilation)

Historical local x86_64 AU/VST3 work remains evidence only. **Do not resume local product or CTest compilation.** System `/Library/Audio/Plug-Ins/Components/Swara XT.component` (1.3.1) must stay installed.

## Amendment — GHA-only rebuild after PR review

Visibility `SWARAXT_REPOSITORY_PRIVATE=false`; production Source/ parity complete except five Apple exceptions; push default mode `build`.

## Amendment — final validation of hosted `ca3ccf3`

### Candidate

| Item | Value |
| --- | --- |
| Source SHA | `ca3ccf363d5706781a30a5310b1408f719b64ee3` |
| Build run (`mode=build`) | https://github.com/Almeriya/SWARAPRIVATE/actions/runs/45801959665 **success** |
| Full run (`mode=full`) | https://github.com/Almeriya/SWARAPRIVATE/actions/runs/45807588777 (in progress at report time) |
| Local test root | `~/Desktop/SWARA-XT-1.3.3-MAC-PRIVATE-TEST/` |
| Archive SHA-256 | `8a5a262580a90a2d29eda9c84a72af32d8f24193be1cbdc9ee0f633f3218834a` (matches `archive-sha256.txt`) |
| AU Mach-O SHA-256 | `912ebebfb5e289ab1c5f4f3c6076f2860e2a527aabf041578163a7534bfc7c06` |
| VST3 Mach-O SHA-256 | `17a48de53ac821cfc0e1794bca6b3ed2cb316dbfc82479f1710f8913c4d860dc` |
| Architectures | `x86_64` + `arm64` (`lipo`) |
| Signature | ad-hoc (`flags=0x2`), verified; **not** Developer ID |
| Provenance | `qualification_status=BUILD_PASS_UNQUALIFIED`, JUCE `e18f7f5…`, Xcode 16.4 |
| QA packages | ZIP/PKG/source hashes verified via `Packages/SHA256SUMS` — PKG **not** installed |

### Safe install

User-folder only (system 1.3.1 untouched):

- `~/Library/Audio/Plug-Ins/Components/Swara XT 1.3.3-hosted-universal.component`
- `~/Library/Audio/Plug-Ins/VST3/Swara XT 1.3.3-hosted-universal.vst3`

Prior `1.3.3-dev-intel` user copies preserved. Rollback: delete the two `hosted-universal` folders.

### Local validators (hosted binaries)

| Tool | Command / target | Result |
| --- | --- | --- |
| Steinberg VST3 validator 3.8.0 | path to hosted `.vst3` | **47 passed, 0 failed** |
| pluginval 1.0.4 | `--strictness-level 10` on hosted VST3 | **SUCCESS** |
| pluginval 1.0.4 | `--strictness-level 10` on hosted AU | **SUCCESS** (embedded auval reported Component Version **1.3.3 / 0x10303**) |
| `auval -v aumu SwXT MnTr` | fourcc (ambiguous with system 1.3.1) | Bound **1.3.3 (0x10303)**; **AU VALIDATION SUCCEEDED** |

Evidence: `Evidence/09-steinberg.txt`, `10-pluginval-vst3.txt`, `11-12-pluginval-au-auval.txt`.

### REAPER 7.86

Handmade RPP FX lines initially failed (“effects … not available”). Fixed by saving a project after `TrackFX_AddByName` so REAPER encodes:

`VST3i: Swara XT (MontroneDSP)` + `"Swara XT 1.3.3-hosted-universal.vst3"`.

| Project | Result |
| --- | --- |
| `REAPER/validation-vst3-working.rpp` | Hosted VST3 confirmed in FX chain |
| `REAPER/validation-vst3-hosted-{44100,48000,96000}.rpp` | Offline render **non-silent** |
| `REAPER/validation-au-working.rpp` | Offline render **non-silent**; AU identity still fourcc-ambiguous |

Offline render summary (`Evidence/21-render-analysis.txt`):

| Render | sr | peak | rms | notes |
| --- | --- | --- | --- | --- |
| VST3 hosted 44.1 kHz | 44100 | 0.322377 | 0.033395 | finite; tiny DC |
| VST3 hosted 48 kHz | 48000 | 0.322114 | 0.033395 | finite |
| VST3 hosted 96 kHz | 96000 | 0.322822 | 0.033394 | finite |
| AU working 44.1 kHz | 44100 | 0.322421 | 0.038212 | finite; MIDI includes CC120 |
| VST3 44.1 kHz pass1 vs pass2 | — | — | — | **PCM identical** (byte SHA may differ in non-PCM RIFF fields) |

**OWNER ACTION REQUIRED:** GUI open/close, multi-instance, transport seek/loop/tempo, Classic vs Dual SVF listening, presets/Scala, confirm AU instance is 1.3.3 while system 1.3.1 remains installed.

### Audio authority

Still **REVIEW_REQUIRED**. No goldens regenerated. Historical Dual SVF / ARM fingerprint failures preserved.

### Security

No Apple credentials, Developer ID, notarization, or keychain access. CI secret-free; candidate ad-hoc only. QA PKG not published.

## Amendment — CI recovery after `full` native compile failure

Failed run: https://github.com/Almeriya/SWARAPRIVATE/actions/runs/45807588777 (source `ca3ccf3`)

Preflight Intel/ARM, universal, and smoke Intel/ARM: **PASS** (still attributed to `ca3ccf3`).

### Root cause (verified compiler)

`Tests/Current/PresetRestoreHeadlessTestsMain.cpp` called stale
`testExplicitProgramChangeAfterPrepare()`; implementation is
`testExplicitPresetSelectionAfterPrepare()` in
`Tests/Presets/PresetStateRestoreTestsMain.cpp`.

First diagnostic (ARM64 Debug `build-native-tests.log`):

`error: use of undeclared identifier 'testExplicitProgramChangeAfterPrepare'`

Other Current headless wrappers: no analogous missing symbols.

### Minimal fix

```diff
-    testExplicitProgramChangeAfterPrepare();
+    testExplicitPresetSelectionAfterPrepare();
```

Allowlisted in `source_profile_133._ALLOWED_META` (harness-only; not a production Source/ change).

No production DSP / golden / JUCE changes. Coverage preserved (explicit preset selection after `prepareToPlay()`).

Recovery commits (do not mix with `ca3ccf3` binaries):

| SHA | Role |
| --- | --- |
| `5f315ef261d79deed8b12cf7043f354775be7444` | Harness rename + probe script — preflight **FAIL** (path not allowlisted) |
| `d20b12ac001bccb940f2184dadbb616011309b1d` | Recovery `workflow_dispatch` wiring — same preflight **FAIL** |
| `f2c9433e677c37c0c86e7837236a212e239117be` | Allowlist + recovery HEAD for Stage A/C |

Stage A probe (failed allowlist): https://github.com/Almeriya/SWARAPRIVATE/actions/runs/45875899928 — **FAIL** (source profile; compile **NOT_RUN**)

Stage A probe (ARM64 Debug, `SwaraXTCurrentPresetRestoreHeadlessTests`): https://github.com/Almeriya/SWARAPRIVATE/actions/runs/45876762118 — **PASS** (`TARGETED_NATIVE_TEST_PASS_NOT_QUALIFIED`; not a full matrix)

Stage C universal `build` on `f2c9433`: https://github.com/Almeriya/SWARAPRIVATE/actions/runs/45876750850 — **PASS** (preflight Intel/ARM + universal + gate; smoke/native skipped in `mode=build`)

Stage C full matrix on exact SHA `f2c9433` (one dispatch; not mixed with `ca3ccf3`): https://github.com/Almeriya/SWARAPRIVATE/actions/runs/45880728588 — **FAIL** (gate)

`SwaraXTCurrentPresetRestoreHeadlessTests` on ARM64 Debug/Release/TSan full inventory: **PASS** (compile defect recovered).

### Classification of native jobs (`45807588777`, source `ca3ccf3`)

| Profile | Result | Class |
| --- | --- | --- |
| ARM64 Debug | FAIL | **COMPILER** — undeclared identifier above |
| ARM64 Release | FAIL | **COMPILER** — same |
| ARM64 TSan | FAIL | **COMPILER** — same |
| ARM64 ASan/UBSan | FAIL | **INTERRUPTED** — not executed to assertion |
| Intel Debug | FAIL | **COMPILER** — same |
| Intel Release | FAIL | **INTERRUPTED** |
| Intel TSan | FAIL | **INTERRUPTED** |
| Intel ASan/UBSan | FAIL | **INTERRUPTED** |

Interrupted profiles are **not** product regressions and are **not** PASS.

### Classification of native jobs (`45880728588`, source `f2c9433`)

| Profile | Result | Class |
| --- | --- | --- |
| ARM64 Debug | FAIL | **TEST ASSERTION** — compile **PASS**; 15/154 CTest failures |
| ARM64 Release | FAIL | **TEST ASSERTION** — same 15 failures |
| ARM64 TSan | FAIL | **TEST ASSERTION** — same 15; no TSan race in failure list |
| ARM64 ASan/UBSan | FAIL | **INTERRUPTED** — timeout ~10800s ~3553/5587; tests **NOT_RUN** |
| Intel Debug | FAIL | **INTERRUPTED** — timeout ~10800s ~4645/5587; tests **NOT_RUN** |
| Intel Release | FAIL | **INTERRUPTED** — timeout ~10800s ~3934/5587; tests **NOT_RUN** |
| Intel TSan | FAIL | **INTERRUPTED** — timeout ~10800s ~3975/5587; tests **NOT_RUN** |
| Intel ASan/UBSan | FAIL | **INTERRUPTED** — timeout ~10800s ~2088/5587; tests **NOT_RUN** |

ARM64 Debug/Release/TSan shared failing CTest names (not compile):

| Test | Class | First FAIL signal |
| --- | --- | --- |
| `SwaraXTAudioParityTests` | **AUDIO REFERENCE** | classic Tests F/G/I golden mismatch; hashes printed; authority **REVIEW_REQUIRED** |
| `SwaraXTRestoreCompletion*` (6) | **HOST / OVERLAY** | restore cohort / notification; Apple JUCE restore-completion overlay still off |
| `SwaraXTHostRestoreFault-{parameter,sequence,post,metadata}` | **HOST / OVERLAY** | exceptional restore containment |
| `SwaraXTCorrectnessTests` | **ASSERTION** | `dedicated native LFO2 depth reaches board CV exactly once` |
| `SwaraXTDualSvfDormancyTests` | **ASSERTION** | `real processor FIFO matches an independently indexed stream` |
| `SwaraXTWorkflowTests` | **ASSERTION** | `locked pattern/extended arp preserved` |
| `SwaraXTPlaybackRegressionTests` | **ASSERTION** | `old retained index remaps by saved name` |

No goldens regenerated. No production DSP changed for these.

### Focused hosted diagnostics (`9eef8d3`, docs/probe-wiring only; same harness fix)

Sequential ARM64 Debug single-target probes: https://github.com/Almeriya/SWARAPRIVATE/actions/runs/45928712715

| Target | Compile | CTest | Class |
| --- | --- | --- | --- |
| `SwaraXTCorrectnessTests` | PASS | FAIL | ASSERTION — LFO2 board CV once |
| `SwaraXTDualSvfDormancyTests` | PASS | FAIL | ASSERTION — FIFO indexed stream (496 reported) |
| `SwaraXTWorkflowTests` | PASS | FAIL | ASSERTION — locked pattern/extended arp |
| `SwaraXTPlaybackRegressionTests` | PASS | FAIL | ASSERTION — old retained index remaps (4) |

Universal `build` on `9eef8d3`: https://github.com/Almeriya/SWARAPRIVATE/actions/runs/45928704349 — **PASS** (docs/workflow only; do not treat as qualifying product delta vs `f2c9433` natives)

Do not redispatch a concurrent full matrix until surgical root causes are identified for the non-audio assertions. AudioParity remains **REVIEW_REQUIRED**. Restore-completion remains blocked by Apple overlay off.

### Recovery tooling

Added fail-closed, secret-free:

- `scripts/macos/native_test_probe.py`
- `.github/workflows/macos-native-test-probe.yml`
- `workflow_dispatch` on registered `macos-build-recovery.yml` → sequential single-target probes

Audio authority remains **REVIEW_REQUIRED**. PR #1 stays unmerged. Merge readiness: **BLOCKED**.

## Amendment — permanent agent instructions + four assertion contract fixes

### Tracked agent policy (committed)

| File | Role |
| --- | --- |
| `AGENTS.md` | Root agent instructions incl. GITHUB ACTIONS NO-WAIT POLICY |
| `.cursor/rules/ci-no-polling.mdc` | alwaysApply: no CI polling / watch / sleep-wait |
| `.cursor/rules/macos-engineering.mdc` | alwaysApply: parity, no local compile, Apple security, PR discipline |

`.gitignore` updated so these are **not** excluded. Verified with `git check-ignore` / `git add`.

### Fix A — LFO2 board CV (`SwaraXTCorrectnessTests`)

- **Assertion:** `dedicated native LFO2 depth reaches board CV exactly once`
- **Classification:** **TEST BUG** (stale expectation)
- **Root cause:** Classic `boardCutoffCvVolts` includes intentional `knobCutoffTrimBytes_`; test compared against `voice.cutoff()*5/255` only. LFO2 still applied once in firmware.
- **Correction:** Expect board CV = `(cutoff + knobCutoffTrimBytes_) * 5/255`. Production DSP unchanged.
- **CI:** focused ARM64 Debug — **PENDING**

### Fix B — Dual SVF FIFO (`SwaraXTDualSvfDormancyTests`)

- **Assertion:** `real processor FIFO matches an independently indexed stream`
- **Classification:** **TEST BUG**
- **Root cause:** CC120 `applyEmergencySilence()` resets production Dual delay while awake; Trace only cleared on dormancy → model desync.
- **Correction:** `armPanicResync` on CC120 host blocks; clear independent FIFO at next tap. Production panic reset preserved.
- **CI:** focused ARM64 Debug — **PENDING**

### Fix C — Sequence lock (`SwaraXTWorkflowTests`)

- **Assertion:** `locked pattern/extended arp preserved`
- **Classification:** **TEST BUG**
- **Root cause:** Fixture set APVTS `arp.pattern=6` then `SequenceState.arpPattern=15`. Host restore re-applies APVTS ARP authority over SEQUENCE arp (intentional).
- **Correction:** Align APVTS arp pattern with sequence (`15`). Lock/preset product paths unchanged.
- **CI:** focused ARM64 Debug — **PENDING**

### Fix D — Historical preset remap (`SwaraXTPlaybackRegressionTests`)

- **Assertion:** `old retained index remaps by saved name`
- **Classification:** **TEST BUG**
- **Root cause:** After `setStateInformation`, `setCurrentProgram` is intentionally a no-op (`hostSessionStateRestored_`). Later iterations never re-selected the intended factory program.
- **Correction:** Use public `loadPresetEntry` (factory entry) for explicit selection before remap capture — `loadFactoryPreset` is private. Product remapping loop unchanged.
- **CI:** focused ARM64 Debug — **PENDING** (follow-up commit after private-API catch)

### Still blocked (unchanged)

- AudioParity goldens → **REVIEW_REQUIRED** (no golden regen)
- RestoreCompletion / HostRestoreFault → Apple JUCE restore-completion overlay still off (Windows CRLF overlay not applied to Apple)
- Intel/sanitizer full-matrix compile timeouts → **INTERRUPTED** / **NOT_RUN**

Focused dispatch after this amendment: recovery workflow ARM64 Debug matrix of the four targets — results **PENDING** (no-wait policy).
