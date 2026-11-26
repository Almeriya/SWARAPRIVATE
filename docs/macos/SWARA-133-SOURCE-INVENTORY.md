# SWARA XT 1.3.3 macOS surgical source inventory

Frozen inputs (do not track later `main` commits):

| Tree | Repository | Revision |
| --- | --- | --- |
| Destination Mac 1.3.1 | `Almeriya/SWARAPRIVATE` | `64fa3f6640706db5ae7181bd9e694828b0284e3b` |
| Official product 1.3.3 | `montronedsp/SWARAXT` `v1.3.3` | `6ea598e47fb0347d23ffa538a64b02318187a7ed` |

Public `main` after that revision is packaging/README/Linux-installer documentation only and is not a migration input.

Classification is against the two frozen trees. Git ancestry is not used as merge authority.

## 1. Identical source

389 files are byte-identical, including most Shruthi-port, UI, resources, licenses, presets and the majority of tests.

## 2. New 1.3.3 production / test functionality (public-only)

| Path | Stage | Expected Mac implementation |
| --- | --- | --- |
| `Source/Engine/GrooveClock.h` | E | Import public file |
| `Tests/DspBoard/DelayWrapTests.cpp` | D | Import |
| `Tests/DspBoard/LooperProductionTests.cpp` | D | Import |
| `Tests/Filter/CutoffAuthorityTests.cpp` | C | Import |
| `Tests/Host/DefensiveHardeningTestsMain.cpp` | F | Import if JUCE overlay applies |
| `Tests/Presets/HostStateSafetyTestsMain.cpp` | F | Import |
| `Tests/Presets/RestoreCompletionTestsMain.cpp` | F | Import only if `SWARAXT_JUCE_RESTORE_COMPLETION` is real |
| `Tests/Qualification/ClassicMatrixCapture.cpp` | C | Import as capture aid, not authority |
| `Tests/Sequencer/ArpAutomationRaceTestsMain.cpp` | E | Import |
| `Tests/Sequencer/GrooveClockTestsMain.cpp` | E | Import |
| `Tests/Sequencer/HostGrooveTestsMain.cpp` | E | Import |
| `Tests/Sequencer/MidiCc120EmergencySilenceTestsMain.cpp` | D | Import |
| `Tests/Sequencer/MidiCcNrpnAuthorityTestsMain.cpp` | D | Import |
| `Tests/Sequencer/SequencerSafety*.cpp` | E | Import |
| `Tests/Sequencer/ThrowingSequenceMutator.*` | E | Import |
| `Tests/avrlib_hd/VowelPhaseWrapTestsMain.cpp` | C/E | Import |
| `cmake/Juce901RestoreCompletion.*` | F | Evaluate for macOS JUCE 9.0.1 |
| `cmake/Juce901PngError.*` | F | Windows-oriented; inspect before Apple use |
| `docs/CUTOFF_FINE_PATH.md` | C | Import as engineering notes |

Linux/Windows package workflows and public native-reference JSON files are **not** Mac product source.

## 3. Mac-specific source exceptions (retain)

| Path | Reason |
| --- | --- |
| `Source/Tuning/RealFromChars.h` | Apple libc++ lacks floating `std::from_chars`; pinned `fast_float` fallback |
| `third_party/fast_float/**` | Pinned parser dependency |
| `Source/Tuning/TuningTable.cpp` | Keep `realFromChars`; overlay 1.3.3 degree/pitch math |
| `Source/Plugin/SwaraXtParameterLayout.cpp` | Keep `realFromChars`; no public `std::from_chars` |
| `Source/Engine/SampleRate/HostResampler.cpp` | Apple ARM `fp contract(off)` on DC blocker |
| `Source/Engine/SampleRate/PolyphaseFirResampler.h` | Apple ARM `fp contract(off)` on SRC |
| `enable_language(OBJC OBJCXX)` and AU format | Apple CMake foundation |
| `cmake/StandaloneMidiCapacity.cmake` Apple `.mm` overlay | Existing Mac JUCE module compile |
| `Tests/Apple/**`, `scripts/macos/**`, `docs/macos/**` | Qualification infrastructure |
| Dual SVF Apple reference selectors | Historical; do not rewrite failures as PASS |

## 4. Conflicting production files (semantic integration)

| Path | Stage | Final implementation | Qualification |
| --- | --- | --- | --- |
| `CMakeLists.txt` | A | Version 1.3.3; keep OBJC/OBJCXX, AU, Apple qualification include, no Standalone packaging | configure / source profile |
| `cmake/Dependencies.cmake` | F | Keep JUCE 9.0.1 pin; add restore overlay only if the patch applies on Apple | restore tests |
| `Source/Tuning/TuningTable.h` | B | Public `splitSignedPeriod` | Scala/KBM/SWT/negative degrees |
| `Source/Tuning/TuningTable.cpp` | B | Public overflow-safe period + finite Hz; retain Apple parser | parser + tuning tests |
| `Source/Tuning/PublishedTuning.h` | B | Use `splitSignedPeriod` | factory tunings |
| `Source/Engine/SequenceState.h` | B+E | Degree split in B; writer transaction in E | sequencer tests |
| `Source/Plugin/SwaraXtParameterLayout.cpp` | B | Public behaviour with Apple parser | cutoff text + parameter IDs |
| `Source/Engine/SwaraXtEngine.cpp/.h` | C/D/E | Classic cutoff, CC120, host clock | Classic + MIDI + transport |
| `Source/Engine/Filter/Circuit/Ir3109BoardCore.h` | C | Public continuous cutoff; keep MSVC `exp2` guard | Classic cutoff |
| `Source/Engine/Filter/SwaraXtFilter.h` | C | Public 1.3.3; Dual SVF unchanged | Classic vs Dual |
| `Source/Engine/DspBoard/BoardEffects.*` | D | Panic drain + delay wrap; keep looper content | CC120 / looper |
| `Source/Engine/DspBoard/BoardProcessor.*` | D | Coordinated panic | CC120 |
| `Source/Engine/SampleRate/InternalSampleQueue.h` | D | Panic-drain / SRC lookahead | CC120 |
| `Source/Plugin/PluginProcessor.*` `PluginEditor.*` | F | Bounded presets, restore results, LnF lifetime | session fixtures |
| Remaining engine/UI/test diffs | C–F | Port public behaviour; keep Apple arithmetic/tests | matching suite |

Windows-only IR3109 numerical correction stays platform-guarded.

## 5. Test and CI changes

Mac keeps historical 1.3.1 profile, goldens and original Dual SVF / ARM failures.

New 1.3.3 profile (`source_profile_133.py`) admits this surgical tree. `native_reference.py` stays fail-closed. Workflow repository identity `RIG-AUDIO/SW2` is updated in Stage H, not by string-replacing evidence.

## 6. Unrelated documentation / platform packaging

Public Linux/Windows package scripts, README screenshots and installer docs are not required for this port. Mac packaging remains unsigned Universal AU+VST3.

## Local toolchain note

Hosted qualification: Xcode 16.4 / Apple Clang 17 / macOS 15 runners.

This Intel Mac: macOS 13.7.8, Xcode 15.2, Apple Clang 15.0.0, SDK 14.2. The difference is recorded; CI identity checks are not relaxed.
