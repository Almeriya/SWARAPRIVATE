# Building Swara XT

The macOS product metadata targets **1.3.3 (engineering candidate, unqualified)**.
The historical 1.3.1 and 1.3.0 qualification evidence remains unchanged. Hosted
CI continues to require Xcode 16.4; this local Intel Mac currently provides
Xcode 15.2 and is not a substitute for that identity. The latest published
Windows/Linux release is [1.3.3](https://github.com/montronedsp/SWARAXT/releases/tag/v1.3.3).
No public macOS archive is authorized from this branch.

## Requirements

- CMake 3.22 or newer
- A C++17 compiler (Visual Studio 2022 on Windows; GCC/Clang on Linux; Apple Clang on macOS)
- Git
- The exact platform JUCE pin below at `.cache/JUCE` (or set `SWARAXT_JUCE_DIR`)
- The pinned Shruthi and avrlib submodules

```bash
git submodule update --init third_party/shruthi-1
git -C third_party/shruthi-1 -c submodule.avrlib.url=https://github.com/pichenettes/avril.git submodule update --init avrlib
```

The obsolete `git://` URL in the pinned Shruthi revision is overridden only for
the avrlib checkout. The nested Shruthi `tools` submodule is not required to
build or test Swara XT and need not be initialized.

Use a separate immutable JUCE checkout for each selected platform:

| Platform | JUCE | Required revision |
| --- | --- | --- |
| Linux | 9.0.4 | `3fb5cbc0340758596dac39f7c8de47d562b4896e` |
| Windows/macOS | 9.0.1 | `e18f7f506c0b96f2c738a0bcd7fe6467a5005ad8` |

For Linux, obtain the source with:

```bash
git clone --branch 9.0.4 --depth 1 https://github.com/juce-framework/JUCE.git .cache/JUCE
git -C .cache/JUCE rev-parse HEAD
```

Windows/macOS use the same clone command with `--branch 9.0.1`. Check the
reported revision against the table before configuring. Linux CMake rejects
unexpected revisions and source drift, and generates the complete ChannelType
and signed WAVE-sentinel corrections inside the build directory. Keep the input
checkout pristine; the MIDI player reserve overlay is also build-owned. Linux
VST3 links isolate only the SharedCode archive's bundled implementation symbols.
Use separate out-of-source trees for compilers, build types and sanitizers.

Public CMake presets contain no machine-specific paths. Local overrides belong in
an ignored `CMakeUserPresets.json` or in environment/`-D` cache variables.

## Release vs development

| Preset | Tests | Purpose |
|--------|-------|---------|
| `*-release` | `SWARA_BUILD_TESTS=OFF` | Product plugin/standalone only |
| `*-dev` | `SWARA_BUILD_TESTS=ON` | Development + test executables |

Each preset uses its own directory under `build/` (for example `build/win-release`).
Do not reuse a Windows build tree for Linux or another configuration.

## Windows

```powershell
cmake --preset win-release
cmake --build --preset win-release
```

Or:

```powershell
.\scripts\build_release.ps1
```

Development with tests:

```powershell
cmake --preset win-dev
cmake --build --preset win-dev
```

## Linux

```bash
cmake --preset linux-release
cmake --build --preset linux-release
```

Or:

```bash
./scripts/build_release.sh
```

## macOS

For the reviewed macOS release candidate, build **only Universal AU and VST3**
with Xcode 16.4 and pinned JUCE 9.0.1. Standalone and Skin Editor are disabled.

```bash
cmake -S . -B build/mac-131-universal -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_OSX_ARCHITECTURES='x86_64;arm64' \
  -DCMAKE_OSX_DEPLOYMENT_TARGET=11.0 \
  -DSWARAXT_JUCE_DIR=/absolute/path/to/JUCE-9.0.1 \
  -DSWARA_BUILD_STANDALONE=OFF \
  -DSWARA_BUILD_SKIN_EDITOR=OFF \
  -DSWARA_BUILD_TESTS=OFF
cmake --build build/mac-131-universal --target SwaraXT_AU SwaraXT_VST3
```

The full CI campaign uses [`macos-qualification.yml`](.github/workflows/macos-qualification.yml)
with `mode=full`, and the same immutable universal candidate is used for
native host checks and [unnotarized QA packaging](packaging/macos/README.md).
The existing native audio-reference authority remains fail-closed.


## Tests

Tests are opt-in. Configure a `*-dev` preset (or pass `-DSWARA_BUILD_TESTS=ON`),
then build/run only when explicitly requested:

```bash
ctest --test-dir build/win-dev -C Debug --output-on-failure
```

Do not run CTest, pluginval, or other validators as part of a normal release build.

## Artifacts

Primary artifacts (multi-config generators use a `Release`/`Debug` subdirectory):

- `build/<preset>/SwaraXT_artefacts/.../VST3/Swara XT.vst3`
- `build/<preset>/SwaraXT_artefacts/.../Standalone/Swara XT`

Set `SWARAXT_JUCE_DIR` at configure time if JUCE is stored outside `.cache/JUCE`.

## Release-candidate qualification

Run the existing eight-profile Linux qualification workflow on its Ubuntu 24.04
GitHub Actions infrastructure after owner approval. SteamOS is the separate
compatibility and real-host acceptance environment; it does not need a copy of
the hosted Ubuntu toolchain. Local Python preflight success does not establish
native qualification or release approval.

Before any hosted Windows qualification run, verify the actual `windows-2022`
runner's selected `cl.exe` identity against the current Windows reference
admission in `scripts/ci/windows_current_reference.py`. Fresh hosted qualification
admits standard MSVC 19.44.35229.0 / toolset 14.44.35207, SHA-256
`fe251ef50a1545b1b0835ee17b1e785459712b38d79e45b5c1d3d28970a36619`.
Use the normal Visual Studio environment; no old-toolset installation is needed.
The preflight records and verifies the actual compiler version, path and hash;
native compile commands and the final gate independently enforce the same hash.
A runner label alone cannot establish that identity. A mismatch requires review,
not a bypass or automatic reference regeneration.

The immutable 72-case Windows audio package keeps its original MSVC 19.38
provenance and all expected values. Admitting the hosted compiler permits fresh
execution; it does not prove those audio results. Release, Debug, ASan, native
host/validators and the final gate must pass on the new candidate. Existing
Windows evidence remains bound to its original source revision.
