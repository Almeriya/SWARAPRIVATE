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
_APPLE_EXCEPTIONS = {
    'Source/Tuning/TuningTable.cpp', 'Source/Tuning/RealFromChars.h',
    'Source/Plugin/SwaraXtParameterLayout.cpp',
    'Source/Engine/SampleRate/HostResampler.cpp',
    'Source/Engine/SampleRate/PolyphaseFirResampler.h',
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
    actual_source = {p: sha for p, sha in current.items() if p.startswith('Source/')}
    _check(actual_source == expected, 'Source/ blob manifest mismatch')
    for path, sha in manifest['transport_tests'].items():
        _check(current.get(path) == sha, 'migrated test mismatch: ' + path)
    for path, sha in manifest['protected_mac_tests'].items():
        _check(current.get(path) == sha, 'protected Mac test/golden mismatch: ' + path)
    allowed = set(expected) | set(manifest['transport_tests']) | _ALLOWED_META
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
    require('project(SwaraXT VERSION 1.3.0 LANGUAGES C CXX)' in root,
            'Prequalification product version must remain 1.3.0')
    require(new.get('third_party/shruthi-1') == old.get('third_party/shruthi-1'),
            'Shruthi submodule pin changed')
    return {'base_source_sha': original_base, 'checkout_sha': checkout_sha,
            'production_parity': production_parity,
            'source_profile': 'SWARAXT_1_3_1_SOURCE_ONLY',
            'source_overlay': result,
            'host_arithmetic_source_sha256': {p: digest(source / p) for p in host_arithmetic},
            'actual_parser_source_sha256': digest(source / 'Source/Tuning/TuningTable.cpp'),
            'actual_cutoff_source_sha256': digest(source / 'Source/Plugin/SwaraXtParameterLayout.cpp'),
            'version': '1.3.0', 'native_audio_reference': 'REVIEW_REQUIRED'}
