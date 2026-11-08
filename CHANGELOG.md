# Changelog

## 1.3.1 — macOS release candidate (unqualified)

- Align active macOS AU/VST3 and source-provenance version to 1.3.1.
- Prepare Universal arm64/x86_64 QA ZIP and system installer PKG, plus
  corresponding source and license notices, without Developer ID signing.
- Carry forward the already merged 1.3.1 panel, sequencer, MIDI queue,
  Shruthi-warning and dead-filter cleanups, and production cutoff-CV tests.
- Native audio authority and independent full qualification remain required;
  this is not a public macOS release.

## 1.3.0 — Unreleased (historical engineering baseline)

- Align product and qualification package metadata for the feature-frozen 1.3.0 candidate.
- Native release qualification remains required before publication.

## 1.2.3

- Public Windows x64 and Linux x86_64 VST3 and Standalone release.
- 57 factory programs, including 40 official Shruthi patches.
- Native filter ENV/LFO controls, a 12-slot modulation matrix, and 16 DSP-board effects plus Off.
- Adriatica Next typography, five skins, fourteen decorations, and two manufacturer marks.

## 1.2.2

- Public Linux x86_64 release with VST3 and Standalone packages.

## 1.1.0

- Public repository and build workflow standardization.
- Preset/program selection no longer changes on editor open/close or ordinary MIDI notes.
- Filter CPU optimizations with High / Normal / Eco quality preference (default High).

## 1.0.0

- Initial Swara XT VST3 and Standalone codebase.
- Shruthi-derived monophonic voice at its native render cadence.
- Circuit-derived resonant four-pole filter and streaming host-rate conversion.
- Regression suites for timing, initialization, filtering, state, and instances.
