# SPDX-FileCopyrightText: 2026 MontroneDSP
# SPDX-License-Identifier: GPL-3.0-or-later
"""Pinned SWARA XT 1.3.3 macOS source parity only; NO macOS audio-reference approval."""
import hashlib
import json
from pathlib import Path
import subprocess

PUBLIC_133_SHA = '6ea598e47fb0347d23ffa538a64b02318187a7ed'
MAC_131_SHA = '64fa3f6640706db5ae7181bd9e694828b0284e3b'
MANIFEST = Path(__file__).with_name('source_profile_133_manifest.json')
_ALLOWED_META = {
    'CMakeLists.txt', 'Tests/CMakeLists.txt', 'scripts/macos/policy.py',
    'scripts/macos/test_ci.py', 'scripts/macos/source_profile_131.py',
    'scripts/macos/source_profile_131_manifest.json',
    'scripts/macos/test_source_profile_131.py',
    'scripts/macos/source_profile_133.py',
    'scripts/macos/source_profile_133_manifest.json',
    'scripts/macos/test_source_profile_133.py',
    'docs/macos/SWARA-133-SOURCE-INVENTORY.md',
    'docs/macos/SWARA-133-SURGICAL-PORT-REPORT.md',
    'cmake/Dependencies.cmake',
    'cmake/Juce901RestoreCompletion.cmake',
    'cmake/Juce901RestoreCompletion.patch',
    'cmake/Juce901PngError.cmake',
    'scripts/macos/ci.py',
    'scripts/macos/gate.py',
    'scripts/macos/test_policy.py',
    '.github/workflows/macos-build-recovery.yml',
    '.github/workflows/macos-intel-native-diagnostics.yml',
    '.github/workflows/macos-development-build.yml',
    '.github/workflows/macos-native-test-probe.yml',
    'scripts/macos/native_test_probe.py',
    # One-line Current wrapper rename: ProgramChange → PresetSelection after prepare.
    'Tests/Current/PresetRestoreHeadlessTestsMain.cpp',
    # macOS assertion-recovery test contract fixes (not production Source/).
    'Tests/Correctness/CorrectnessTestsMain.cpp',
    'Tests/Dormancy/DualSvfDormancyTestsMain.cpp',
    'Tests/Sequencer/WorkflowTestsMain.cpp',
    'Tests/Sequencer/PlaybackRegressionTestsMain.cpp',
    'AGENTS.md',
    '.cursor/rules/macos-engineering.mdc',
    '.cursor/rules/ci-no-polling.mdc',
    '.gitignore',
}
_BUILD_RECOVERY_META = {
    'scripts/macos/build_recovery_probe.py',
    '.github/workflows/macos-build-recovery.yml',
    'scripts/macos/native_test_probe.py',
    '.github/workflows/macos-native-test-probe.yml',
}

_APPLE_EXCEPTIONS = {
    'Source/Tuning/TuningTable.cpp', 'Source/Tuning/RealFromChars.h',
    'Source/Plugin/SwaraXtParameterLayout.cpp',
    'Source/Engine/SampleRate/HostResampler.cpp',
    'Source/Engine/SampleRate/PolyphaseFirResampler.h',
}

_PARSER_MARKERS = (
    '#include "Tuning/RealFromChars.h"',
    'detail::realFromChars(',
)
_CUTOFF_MARKERS = (
    '#include "Tuning/RealFromChars.h"',
    'tuning::detail::realFromChars(',
)


def _check(ok, reason):
    if not ok:
        raise RuntimeError('1.3.3 source profile rejected: ' + reason)


def _blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + bytes([0]) + data).hexdigest()


def validate_tree(base, current, manifest):
    """Fail-closed tree comparison used by mutation tests and live admission."""
    _check(manifest['public_133_commit'] == PUBLIC_133_SHA
           and manifest['mac_131_baseline'] == MAC_131_SHA, 'wrong pinned revisions')
    expected = dict(manifest['source'])
    protected = manifest['apple_source_exceptions']
    _check(set(protected) == _APPLE_EXCEPTIONS, 'Apple exception inventory drift')
    for path, sha in protected.items():
        _check(path not in expected or expected[path] != sha, 'Non-exception: ' + path)
        expected[path] = sha
    pinned = json.loads(MANIFEST.read_text())
    removed = manifest.get('removed_source')
    _check(removed == pinned['removed_source'], 'unreviewed source deletion inventory')
    _check(set(removed).isdisjoint(expected), 'retired source still expected upstream')
    for path in removed:
        _check(path not in base, 'retired source present in 1.3.1 Mac baseline: ' + path)
        _check(path not in current, 'retired source restored: ' + path)
    release_metadata = manifest.get('release_metadata')
    _check(release_metadata == pinned['release_metadata'], 'unreviewed release metadata inventory')
    for path, blob in release_metadata.items():
        _check(current.get(path) == blob, 'reviewed release metadata changed: ' + path)
    actual_source = {p: sha for p, sha in current.items() if p.startswith('Source/')}
    _check(actual_source == expected, 'Source/ blob manifest mismatch')
    for path, sha in manifest['transport_tests'].items():
        if sha is None:
            _check(path not in current, 'retired transport test restored: ' + path)
        else:
            _check(current.get(path) == sha, 'migrated test mismatch: ' + path)
    for path, sha in manifest['protected_mac_tests'].items():
        _check(current.get(path) == sha, 'protected Mac test/golden mismatch: ' + path)
    allowed = (set(expected) | set(manifest['transport_tests']) | set(removed)
               | _ALLOWED_META | _BUILD_RECOVERY_META | set(release_metadata)
               | set(manifest.get('allowed_mac_docs', [])))
    for path in set(base) | set(current):
        if base.get(path) != current.get(path):
            _check(path in allowed, 'unreviewed repository difference: ' + path)
    return {'source_files': len(expected), 'apple_exceptions': len(protected),
            'transport_tests': len(manifest['transport_tests']),
            'native_audio_reference': 'REVIEW_REQUIRED'}


def compare_source_133(source, checkout_sha, base_sha, git_tree, original_base,
                       production_parity, host_arithmetic):
    from policy import (require, digest, verify_apple_guard_test,
                        verify_dual_reference_selection, verify_dual_integration_selection)
    source = Path(source)
    require(base_sha == original_base, 'Approved historical SW2 base required')
    require(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source,
                                    text=True).strip() == checkout_sha, 'Checkout SHA mismatch')
    manifest = json.loads(MANIFEST.read_text())
    old = {p: v.split()[-1] for p, v in git_tree(source, MAC_131_SHA).items()}
    new = {p: v.split()[-1] for p, v in git_tree(source, checkout_sha).items()}
    result = validate_tree(old, new, manifest)
    for path, sha in new.items():
        if (path.startswith('Source/') or path in manifest['transport_tests']
                or path in manifest['protected_mac_tests']):
            file = source / path
            require(file.is_file() and not file.is_symlink() and _blob(file.read_bytes()) == sha,
                    'Working tree changed: ' + path)
    for path in _ALLOWED_META:
        file = source / path
        if file.is_file() and not file.is_symlink() and path in new:
            require(_blob(file.read_bytes()) == new[path],
                    'Unreviewed worktree metadata: ' + path)
    verify_apple_guard_test(source)
    verify_dual_reference_selection(source)
    verify_dual_integration_selection(source)
    root = (source / 'CMakeLists.txt').read_text()
    tests = (source / 'Tests/CMakeLists.txt').read_text()
    require(all(token in root for token in (
        'enable_language(OBJC OBJCXX)', 'list(APPEND SWARAXT_PLUGIN_FORMATS AU)',
        'CMAKE_OSX_DEPLOYMENT_TARGET "11.0"',
        'Source/Ui/SwaraXtSeqPanel.cpp')), 'Apple CMake build protections changed')
    require('add_subdirectory(Apple)' in tests and tests.count('add_test(NAME SwaraXTUnitTests') == 1,
            'Apple/native test registration changed')
    require('SwaraXTCutoffContractTests' in tests and 'SwaraXTSmoothingAuditTests' in tests,
            'Production regression suite missing')
    require('SwaraXTGrooveClockTests' in tests and 'SwaraXTHostGrooveTests' in tests
            and 'SwaraXTSequencerSafetyTests' in tests and 'SwaraXTArpAutomationRaceTests' in tests,
            '1.3.3 sequencer/groove regression suite missing')
    require('project(SwaraXT VERSION 1.3.3 LANGUAGES C CXX)' in root,
            'Reviewed macOS engineering product version must be 1.3.3')
    require('SWARA_BUILD_STANDALONE' in root, 'Standalone option must remain explicit')
    tuning = (source / 'Source/Tuning/TuningTable.cpp').read_text()
    cutoff = (source / 'Source/Plugin/SwaraXtParameterLayout.cpp').read_text()
    require(all(marker in tuning for marker in _PARSER_MARKERS),
            'Apple RealFromChars tuning parser exception missing')
    require('std::from_chars(first, last, value, std::chars_format::general)' not in tuning,
            'Public floating std::from_chars must not replace the Apple parser')
    require('splitSignedPeriod(' in (source / 'Source/Tuning/TuningTable.h').read_text(),
            '1.3.3 overflow-safe splitSignedPeriod missing')
    require('splitSignedPeriod(degree, period, periodIndex, inside)' in tuning,
            'TuningTable must use overflow-safe period indexing')
    require(all(marker in cutoff for marker in _CUTOFF_MARKERS),
            'Apple RealFromChars cutoff parser exception missing')
    require((source / 'Source/Tuning/RealFromChars.h').is_file(),
            'Pinned Apple RealFromChars helper missing')
    require((source / 'Source/Engine/GrooveClock.h').is_file(),
            '1.3.3 GrooveClock.h missing')
    sequence_state = (source / 'Source/Engine/SequenceState.h').read_text()
    engine = (source / 'Source/Engine/SwaraXtEngine.cpp').read_text()
    require('struct WriterGate' in sequence_state and 'void revise(' in sequence_state,
            '1.3.3 SequenceState writer transaction missing')
    require('groove::unitsBeforeTick(' in engine and 'hostClockTickAtPpq(' in engine
            and 'currentHostTimingKey(' in engine,
            '1.3.3 host groove clock mapping missing')
    processor = (source / 'Source/Plugin/PluginProcessor.cpp').read_text()
    editor = (source / 'Source/Plugin/PluginEditor.cpp').read_text()
    deps = (source / 'cmake/Dependencies.cmake').read_text()
    require('isBusesLayoutSupported(' in processor and 'maxUserPresetFileBytes' in processor
            and 'publishRestoreNotification(' in processor,
            '1.3.3 processor restore/preset/bus contracts missing')
    require('std::shared_ptr<swaraxt::ui::SwaraXtLookAndFeel>' in
            (source / 'Source/Plugin/PluginEditor.h').read_text()
            and 'refreshRestoreNotification(' in editor,
            '1.3.3 editor LookAndFeel lifetime / restore notification missing')
    require('SwaraXTHostStateSafetyTests' in tests and 'SwaraXTDefensiveHardeningTests' in tests
            and 'AvrlibHdVowelPhaseWrapTests' in tests,
            '1.3.3 host-state / defensive / vowel-wrap tests missing')
    require('pngDeclaredSizeAllowed' in (source / 'Source/Ui/SwaraXtSkin.h').read_text(),
            '1.3.3 PNG import size preflight missing')
    require('jlimit(1, 4, ParameterCache::loadInt(cache.arpOctaves))' in
            (source / 'Source/Engine/PatchBridge.cpp').read_text(),
            '1.3.3 PatchBridge arp_range clamp missing')
    require('ClampArpeggiatorRange' in
            (source / 'Source/Engine/ShruthiPort/adapted/shruthi/part.cc').read_text()
            and 'static_cast<uint16_t>(phase_noise)' in
            (source / 'Source/Engine/ShruthiPort/include_first/avrlib_hd/vowel.h').read_text(),
            '1.3.3 Shruthi Part / AVR vowel phase-wrap contracts missing')
    require('elseif(WIN32)' in deps
            and 'include("${CMAKE_CURRENT_LIST_DIR}/Juce901RestoreCompletion.cmake")' in deps,
            'Windows restore-completion overlay wiring missing')
    # Comment text may mention the macro; Apple must not get a second include path.
    require(deps.count('Juce901RestoreCompletion.cmake') == 1
            and 'if(APPLE)' not in deps
            and 'elseif(APPLE)' not in deps,
            'Apple must not enable unverified SWARAXT_JUCE_RESTORE_COMPLETION')
    workflow = (source / '.github/workflows/macos-qualification.yml').read_text()
    policy_text = (source / 'scripts/macos/policy.py').read_text()
    require("github.repository == 'Almeriya/SWARAPRIVATE'" in workflow
            and 'RIG-AUDIO/SW2' not in workflow
            and "test \"$SWARAXT_REPOSITORY_PRIVATE\" = false" in workflow,
            'macOS qualification workflow still uses retired repository identity')
    require("REPOSITORY = 'Almeriya/SWARAPRIVATE'" in policy_text
            and "REPOSITORY_PRIVATE = 'false'" in policy_text
            and "SWARAXT_REPOSITORY_PRIVATE') == REPOSITORY_PRIVATE" in policy_text,
            'macOS CI policy must pin Almeriya/SWARAPRIVATE at its authorized public visibility')
    require(new.get('third_party/shruthi-1') == old.get('third_party/shruthi-1'),
            'Shruthi submodule pin changed')
    return {'base_source_sha': original_base, 'checkout_sha': checkout_sha,
            'public_133_sha': PUBLIC_133_SHA, 'mac_131_sha': MAC_131_SHA,
            'production_parity': production_parity,
            'source_profile': 'SWARAXT_1_3_3_MAC_SURGICAL',
            'source_overlay': result,
            'host_arithmetic_source_sha256': {p: digest(source / p) for p in host_arithmetic},
            'actual_parser_source_sha256': digest(source / 'Source/Tuning/TuningTable.cpp'),
            'actual_cutoff_source_sha256': digest(source / 'Source/Plugin/SwaraXtParameterLayout.cpp'),
            'version': '1.3.3', 'native_audio_reference': 'REVIEW_REQUIRED'}
