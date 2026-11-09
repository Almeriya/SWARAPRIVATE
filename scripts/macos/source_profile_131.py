# SPDX-FileCopyrightText: 2026 MontroneDSP
# SPDX-License-Identifier: GPL-3.0-or-later
"""Pinned SWARA XT 1.3.1 source parity only; NO macOS audio-reference approval."""
import hashlib
import json
from pathlib import Path
import subprocess

UPSTREAM_131_SHA = 'e62bb3fd51f1c514c87781d9936093679fc5e7a7'
SW2_BASE_SHA = 'ae7b9a5c1c15098492aec48d45326007c679bdfd'
MANIFEST = Path(__file__).with_name('source_profile_131_manifest.json')
_ALLOWED_META = {
    'CMakeLists.txt', 'Tests/CMakeLists.txt', 'scripts/macos/policy.py',
    'scripts/macos/test_ci.py', 'scripts/macos/source_profile_131.py',
    'scripts/macos/source_profile_131_manifest.json',
    'scripts/macos/test_source_profile_131.py',
}
_BUILD_RECOVERY_META = {
    'scripts/macos/build_recovery_probe.py',
    '.github/workflows/macos-build-recovery.yml',
}

_APPLE_EXCEPTIONS = {
    'Source/Tuning/TuningTable.cpp', 'Source/Tuning/RealFromChars.h',
    'Source/Plugin/SwaraXtParameterLayout.cpp',
    'Source/Engine/SampleRate/HostResampler.cpp',
    'Source/Engine/SampleRate/PolyphaseFirResampler.h',
}

_EXPECTED_RC_META = {
    'CMakeLists.txt': 'b350b53b9bbcca3fc2ea85e82db167bbaa8ed50e',
    'README.md': 'ba03378ad6df4b091371bbd2f8345fe2a607869a',
    'BUILDING.md': '3d993804a9e23d8f5a253455b747bb92883472ee',
    'CHANGELOG.md': 'c7fb8a0dd18147a73ecad620df178039b99576ba',
    'docs/macos/QUALIFICATION.md': 'c74c405d847189424c67b7d8e5bdd574d92eb9a8',
    'packaging/SOURCE.txt': 'dd718cfedcd58590b79b69003333cdcef4841bb8',
    '.github/workflows/macos-qualification.yml': 'ca822fda5de7a84475f6b51eda1f5cc6521bed56',
    'scripts/macos/test_ci.py': '0e267ce9511076841aadfa2585a119feb256c15a',
    'scripts/macos/package_release_candidate.py': 'f0b3773f90160827e718b8db6b2f3b09c5331b4f',
    'scripts/macos/test_package_release_candidate.py': '9622cdb9625698a9fe4697fea1aad1b9b2aa6615',
    'packaging/macos/README.txt': 'b31a02eddc9e2b12008be4491083cba237a45681',
    'packaging/macos/README.md': '7f4637a632196425cbc8381e9e6935a80af42151',
    'resources/Skin/Examples/README.md': '46bc2045eb9bafc77fd6a32c4d64d82fae478e5e'
}

_EXPECTED_REMOVED_SOURCE = {
    'Source/Engine/Filter/Circuit/ActiveLoadPole.h': '845cb031bd6bd6b2de390828c8e31a31ae300510',
    'Source/Engine/Filter/Circuit/PassiveLoadPole.h': '88d6aa30fc1805065780629b7aee03a05ad38f1c',
    'Source/Engine/Filter/Circuit/ResonanceNetwork.h': 'd14d7c87c6faf2808138c353f92b967c57c04b7e',
    'Source/Engine/ShruthiPort/include_first/avrlib_hd/filter.h': '0ee0d2069c10f525bacf88bfbef83a701c9baee1'
}


def _check(ok, reason):
    if not ok:
        raise RuntimeError('1.3.1 source profile rejected: ' + reason)


def _blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + bytes([0]) + data).hexdigest()


def validate_tree(base, current, manifest):
    """Pure fail-closed tree comparison used by mutation regression tests."""
    _check(manifest['upstream_commit'] == UPSTREAM_131_SHA
           and manifest['sw2_baseline'] == SW2_BASE_SHA, 'wrong pinned revisions')
    expected = dict(manifest['source'])
    protected = manifest['apple_source_exceptions']
    _check(set(protected) == _APPLE_EXCEPTIONS, 'Apple exception inventory drift')
    for path, sha in protected.items():
        _check(path not in expected or expected[path] != sha, 'Non-exception: ' + path)
        expected[path] = sha
    removed = manifest.get('removed_source')
    _check(removed == _EXPECTED_REMOVED_SOURCE, 'unreviewed source deletion inventory')
    _check(set(removed).isdisjoint(expected), 'retired source still expected upstream')
    for path, old_sha in removed.items():
        _check(base.get(path) == old_sha, 'retired source baseline mismatch: ' + path)
        _check(path not in current, 'retired source restored: ' + path)
    release_metadata = manifest.get('release_metadata')
    _check(release_metadata == _EXPECTED_RC_META, 'unreviewed release metadata inventory')
    for path, blob in release_metadata.items():
        _check(current.get(path) == blob, 'reviewed release metadata changed: ' + path)
    actual_source = {p: sha for p, sha in current.items() if p.startswith('Source/')}
    _check(actual_source == expected, 'Source/ blob manifest mismatch')
    for path, sha in manifest['transport_tests'].items():
        _check(current.get(path) == sha, 'migrated test mismatch: ' + path)
    for path, sha in manifest['protected_mac_tests'].items():
        _check(current.get(path) == sha, 'protected Mac test/golden mismatch: ' + path)
    allowed = set(expected) | set(manifest['transport_tests']) | set(removed) | _ALLOWED_META | _BUILD_RECOVERY_META | set(release_metadata)
    for p in set(base) | set(current):
        if base.get(p) != current.get(p):
            _check(p in allowed, 'unreviewed repository difference: ' + p)
    return {'source_files': len(expected), 'apple_exceptions': len(protected),
            'transport_tests': len(manifest['transport_tests']),
            'native_audio_reference': 'REVIEW_REQUIRED'}


def compare_source_131(source, checkout_sha, base_sha, git_tree, original_base,
                       production_parity, host_arithmetic):
    from policy import (require, digest, verify_apple_guard_test,
                        verify_dual_reference_selection, verify_dual_integration_selection)
    source = Path(source)
    require(base_sha == original_base, 'Approved historical SW2 base required')
    require(subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source,
                                    text=True).strip() == checkout_sha, 'Checkout SHA mismatch')
    manifest = json.loads(MANIFEST.read_text())
    old = {p: v.split()[-1] for p, v in git_tree(source, SW2_BASE_SHA).items()}
    new = {p: v.split()[-1] for p, v in git_tree(source, checkout_sha).items()}
    result = validate_tree(old, new, manifest)
    for path, sha in new.items():
        if path.startswith('Source/') or path in manifest['transport_tests'] or path in manifest['protected_mac_tests']:
            file = source / path
            require(file.is_file() and not file.is_symlink() and _blob(file.read_bytes()) == sha,
                    'Working tree changed: ' + path)
    for path in _ALLOWED_META:
        file = source / path
        require(file.is_file() and not file.is_symlink() and _blob(file.read_bytes()) == new[path],
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
    require('project(SwaraXT VERSION 1.3.1 LANGUAGES C CXX)' in root,
            'Reviewed macOS release-candidate product version must be 1.3.1')
    require(new.get('third_party/shruthi-1') == old.get('third_party/shruthi-1'),
            'Shruthi submodule pin changed')
    return {'base_source_sha': original_base, 'checkout_sha': checkout_sha,
            'production_parity': production_parity,
            'source_profile': 'SWARAXT_1_3_1_SOURCE_ONLY',
            'source_overlay': result,
            'host_arithmetic_source_sha256': {p: digest(source / p) for p in host_arithmetic},
            'actual_parser_source_sha256': digest(source / 'Source/Tuning/TuningTable.cpp'),
            'actual_cutoff_source_sha256': digest(source / 'Source/Plugin/SwaraXtParameterLayout.cpp'),
            'version': '1.3.1', 'native_audio_reference': 'REVIEW_REQUIRED'}
