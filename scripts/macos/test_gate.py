# SPDX-FileCopyrightText: 2026 MontroneDSP
# SPDX-License-Identifier: GPL-3.0-or-later
"""Synthetic gate fixtures prove PASS is possible and fail-closed negatives remain."""
import hashlib
import json
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import xml.etree.ElementTree as ET

from gate import evaluate, inspect_ctest
from native_reference import (
    CLASSIC_HEADER_BLOB, DUAL_INTEGRATION_BLOB, DUAL_INTEGRATION_PATH,
    DUAL_SECTION2_BLOB, DUAL_SECTION2_PATH)
from policy import JUCE_SHA, PRODUCTION_PARITY, SDK_SHA, SEAL

SOURCE_SHA = 'a' * 40
BASE_SHA = '5e7b967db0b52f773f382217a72c6c0c3ff6b8f7'
OVERLAY = {'file': 'modules/juce_audio_basics/buffers/juce_AudioChannelSet.h', 'change': 'test'}
ARCHIVE = 'b' * 64
MANIFEST = 'c' * 64


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def provenance():
    return {
        'status': 'INDEPENDENT_REFERENCES_VERIFIED',
        'candidate_generated': False,
        'hashes_regenerated': False,
        'classic_header_blob': CLASSIC_HEADER_BLOB,
        'classic_public_133_sha': '6ea598e47fb0347d23ffa538a64b02318187a7ed',
        'dual_svf_blobs': {
            DUAL_SECTION2_PATH: DUAL_SECTION2_BLOB,
            DUAL_INTEGRATION_PATH: DUAL_INTEGRATION_BLOB,
        },
        'families': {
            'classic': 'REFERENCE_VERIFIED',
            'integrated_fx': 'REFERENCE_VERIFIED',
            'dual_svf_section2': 'REFERENCE_VERIFIED',
            'dual_svf_integration': 'REFERENCE_VERIFIED',
            'host_src': 'REFERENCE_VERIFIED',
        },
        'REFERENCE_REVIEW_REQUIRED': False,
    }


def write_ctest(path, count=60, failed=0, skipped=0):
    root = ET.Element('testsuite')
    for index in range(count):
        case = ET.SubElement(root, 'testcase', name='Case' + str(index), status='run')
        if index < failed:
            ET.SubElement(case, 'failure', message='audio hash')
        elif index < failed + skipped:
            ET.SubElement(case, 'skipped')
    path.write_bytes(ET.tostring(root))


def base_report(stage, arch, profile):
    return {
        'stage': stage,
        'architecture': arch,
        'profile': profile,
        'source_sha': SOURCE_SHA,
        'base_source_sha': BASE_SHA,
        'run_id': '1',
        'run_attempt': '1',
        'repository': 'Almeriya/SWARAPRIVATE',
        'execution_mode': 'full',
        'juce_sha': JUCE_SHA,
        'standalone': False,
        'source_parity': {
            'production_parity': PRODUCTION_PARITY,
            'base_source_sha': BASE_SHA,
            'checkout_sha': SOURCE_SHA,
        },
        'xcode_version': 'Xcode 16.4\nBuild version 16F6',
        'compiler_version': 'Apple clang version 17.0.0',
        'macos_version': '15.7.9',
        'commands': [{'name': 'ci-harness-regression', 'exit_code': 0}],
        'file_hashes': {},
        'dependency_overlay': OVERLAY,
        'candidate_archive_sha256': ARCHIVE,
        'candidate_manifest_sha256': MANIFEST,
    }


class GateFixture:
    def __init__(self, root):
        self.root = Path(root)
        self.args = SimpleNamespace(mode='full', source_sha=SOURCE_SHA, base_source_sha=BASE_SHA)

    def add_preflight(self, arch):
        folder = self.root / ('preflight-' + arch)
        folder.mkdir()
        report = base_report('preflight', arch, 'Release')
        report['decision'] = 'PREFLIGHT_PASS'
        (folder / 'report.json').write_text(json.dumps(report) + '\n')

    def add_universal(self):
        folder = self.root / 'universal'
        folder.mkdir()
        report = base_report('universal', 'x86_64', 'Release')
        report['decision'] = 'BUILD_PASS_UNQUALIFIED'
        report['universal_build'] = {
            'ci_bundle_signature': SEAL,
            'qualification_status': 'BUILD_PASS_UNQUALIFIED',
            'base_source_sha': BASE_SHA,
            'source_sha': SOURCE_SHA,
            'binaries': {
                'Swara XT.component': {'architectures': ['arm64', 'x86_64']},
                'Swara XT.vst3': {'architectures': ['arm64', 'x86_64']},
            },
        }
        (folder / 'report.json').write_text(json.dumps(report) + '\n')

    def add_smoke(self, arch):
        folder = self.root / ('smoke-' + arch)
        folder.mkdir()
        report = base_report('smoke', arch, 'Release')
        report['decision'] = 'SMOKE_PASS_NOT_FULLY_QUALIFIED'
        report['native_host'] = {'architecture': arch, 'profile': 'Release'}
        report['actual_hosts'] = {'AU': 'PASS', 'VST3': 'PASS'}
        report['au_discovery_exact'] = True
        report['au_discovery_host'] = 'MATCHING_NATIVE_PROFILE_HOST'
        report['commands'] = [
            {'name': 'ci-harness-regression', 'exit_code': 0},
            {'name': 'actual-AU', 'exit_code': 0},
            {'name': 'actual-VST3', 'exit_code': 0},
        ]
        for name in ('actual-AU.log', 'actual-VST3.log'):
            (folder / name).write_text(
                'PASS: actual plugin two-instance audio/editor/state/reopen lifecycle\n')
            report['file_hashes'][name] = digest(folder / name)
        (folder / 'au-cleanup.json').write_text('{}\n')
        login = folder / 'owned-login-1'
        login.mkdir()
        (login / 'cleanup.json').write_text(json.dumps({'exit_code': 0}) + '\n')
        (folder / 'report.json').write_text(json.dumps(report) + '\n')

    def add_tests(self, arch, profile, *, provenance_data=None, test_count=60,
                  failed=0, skipped=0, source_sha=None, omit_provenance=False,
                  wrong_arch_host=False):
        folder = self.root / ('tests-' + arch + '-' + profile)
        folder.mkdir()
        report = base_report('tests', arch, profile)
        if source_sha:
            report['source_sha'] = source_sha
            report['source_parity']['checkout_sha'] = source_sha
        report['decision'] = 'NATIVE_PROFILE_PASS_NOT_FULLY_QUALIFIED'
        report['native_host'] = {
            'architecture': ('arm64' if wrong_arch_host else arch),
            'profile': profile,
        }
        report['actual_hosts'] = {'AU': 'PASS', 'VST3': 'PASS'}
        report['au_discovery_exact'] = True
        report['au_discovery_host'] = 'MATCHING_NATIVE_PROFILE_HOST'
        report['compile_commands_audit'] = 'PASS'
        report['production_compile_commands_count'] = 20
        report['test_count'] = test_count
        report['executed_test_count'] = test_count - skipped
        report['failed_test_count'] = failed
        report['skipped_test_count'] = skipped
        if not omit_provenance:
            report['audio_reference_provenance'] = provenance_data or provenance()
        commands = [
            {'name': 'ci-harness-regression', 'exit_code': 0},
            {'name': 'actual-AU', 'exit_code': 0},
            {'name': 'actual-VST3', 'exit_code': 0},
            {'name': 'ctest', 'exit_code': 0 if failed == 0 and skipped == 0 else 8},
            {'name': 'build-native-tests', 'exit_code': 0},
        ]
        if profile in ('asan-ubsan', 'tsan'):
            report['sanitizer_negative_controls'] = 'PASS'
        if profile == 'Release':
            report['actual_universal_candidate_checked'] = True
            report['external_validators'] = {
                'AU': {'strictness': 10, 'repeat': 2, 'gui_tests': True, 'pluginval_exit_code': 0},
                'VST3': {
                    'strictness': 10, 'repeat': 2, 'gui_tests': True, 'pluginval_exit_code': 0,
                    'sdk_sha': SDK_SHA, 'sdk_exit_code': 0,
                },
            }
            commands.extend([
                {'name': 'auval', 'exit_code': 0},
                {'name': 'pluginval-AU', 'exit_code': 0},
                {'name': 'pluginval-VST3', 'exit_code': 0},
                {'name': 'validator-selftest', 'exit_code': 0},
                {'name': 'validator-extensive', 'exit_code': 0},
            ])
            (folder / 'auval.log').write_text('AU VALIDATION SUCCEEDED\n')
            (folder / 'pluginval-AU.log').write_text('SUCCESS\n')
            (folder / 'pluginval-VST3.log').write_text('SUCCESS\n')
            (folder / 'validator-extensive.log').write_text(
                'Result: 120 tests passed, 0 tests failed\n')
            for name in ('auval.log', 'pluginval-AU.log', 'pluginval-VST3.log',
                         'validator-extensive.log'):
                report['file_hashes'][name] = digest(folder / name)
        report['commands'] = commands
        for name in ('actual-AU.log', 'actual-VST3.log'):
            (folder / name).write_text(
                'PASS: actual plugin two-instance audio/editor/state/reopen lifecycle\n')
            report['file_hashes'][name] = digest(folder / name)
        write_ctest(folder / 'ctest.xml', count=test_count, failed=failed, skipped=skipped)
        report['file_hashes']['ctest.xml'] = digest(folder / 'ctest.xml')
        # Keep inspect_ctest counts aligned with report fields after write.
        counts = {
            'executed_test_count': test_count,
            'failed_test_count': failed,
            'skipped_test_count': skipped,
        }
        report.update(counts)
        (folder / 'au-cleanup.json').write_text('{}\n')
        login = folder / 'owned-login-1'
        login.mkdir()
        (login / 'cleanup.json').write_text(json.dumps({'exit_code': 0}) + '\n')
        (folder / 'report.json').write_text(json.dumps(report) + '\n')

    def complete_matrix(self, **kwargs):
        self.add_preflight('arm64')
        self.add_preflight('x86_64')
        self.add_universal()
        self.add_smoke('arm64')
        self.add_smoke('x86_64')
        for arch in ('arm64', 'x86_64'):
            for profile in ('Release', 'Debug', 'asan-ubsan', 'tsan'):
                self.add_tests(arch, profile, **kwargs)


class GateAuthorityTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.env = patch.dict(os.environ, {
            'GITHUB_ACTIONS': 'false',
            'GITHUB_RUN_ID': '1',
            'GITHUB_RUN_ATTEMPT': '1',
        }, clear=False)
        self.env.start()
        self.addCleanup(self.env.stop)

    def test_complete_synthetic_fixture_can_pass_full(self):
        fixture = GateFixture(self.directory.name)
        fixture.complete_matrix()
        evaluate(self.directory.name, fixture.args)
        decision = json.loads((Path(self.directory.name) / 'qualification-gate.json').read_text())
        self.assertEqual(decision['decision'], 'FULL_NATIVE_QUALIFICATION_PASS')

    def test_wrong_source_sha_fails(self):
        fixture = GateFixture(self.directory.name)
        fixture.complete_matrix()
        fixture.args.source_sha = 'd' * 40
        with self.assertRaisesRegex(RuntimeError, 'Report source mismatch'):
            evaluate(self.directory.name, fixture.args)

    def test_missing_ctest_inventory_fails(self):
        fixture = GateFixture(self.directory.name)
        fixture.complete_matrix(test_count=10)
        with self.assertRaisesRegex(RuntimeError, 'Incomplete native CTest inventory'):
            evaluate(self.directory.name, fixture.args)

    def test_failed_audio_hash_fails(self):
        fixture = GateFixture(self.directory.name)
        fixture.complete_matrix(failed=1)
        with self.assertRaisesRegex(RuntimeError, 'Failed or skipped native CTest'):
            evaluate(self.directory.name, fixture.args)

    def test_skipped_native_test_fails(self):
        fixture = GateFixture(self.directory.name)
        fixture.complete_matrix(skipped=1)
        with self.assertRaisesRegex(RuntimeError, 'Failed or skipped native CTest'):
            evaluate(self.directory.name, fixture.args)

    def test_unapproved_reference_substitution_fails(self):
        bad = provenance()
        bad['classic_header_blob'] = '0' * 40
        fixture = GateFixture(self.directory.name)
        fixture.complete_matrix(provenance_data=bad)
        with self.assertRaisesRegex(RuntimeError, 'unapproved Classic/integrated reference'):
            evaluate(self.directory.name, fixture.args)

    def test_wrong_architecture_host_fails(self):
        fixture = GateFixture(self.directory.name)
        fixture.add_preflight('arm64')
        fixture.add_preflight('x86_64')
        fixture.add_universal()
        fixture.add_smoke('arm64')
        fixture.add_smoke('x86_64')
        for arch in ('arm64', 'x86_64'):
            for profile in ('Release', 'Debug', 'asan-ubsan', 'tsan'):
                fixture.add_tests(arch, profile, wrong_arch_host=(arch == 'x86_64' and profile == 'Debug'))
        with self.assertRaisesRegex(RuntimeError, 'Incorrect native instrumented host'):
            evaluate(self.directory.name, fixture.args)

    def test_wrong_profile_matrix_incomplete_fails(self):
        fixture = GateFixture(self.directory.name)
        fixture.add_preflight('arm64')
        fixture.add_preflight('x86_64')
        fixture.add_universal()
        fixture.add_smoke('arm64')
        fixture.add_smoke('x86_64')
        for arch in ('arm64', 'x86_64'):
            for profile in ('Release', 'Debug', 'asan-ubsan'):
                fixture.add_tests(arch, profile)
        with self.assertRaisesRegex(RuntimeError, 'Failed, missing, skipped or cancelled required stage'):
            evaluate(self.directory.name, fixture.args)

    def test_altered_reference_provenance_across_profiles_fails(self):
        fixture = GateFixture(self.directory.name)
        fixture.add_preflight('arm64')
        fixture.add_preflight('x86_64')
        fixture.add_universal()
        fixture.add_smoke('arm64')
        fixture.add_smoke('x86_64')
        altered = provenance()
        altered['classic_header_blob'] = CLASSIC_HEADER_BLOB  # same blob...
        # Change a dual blob only on one profile.
        for arch in ('arm64', 'x86_64'):
            for profile in ('Release', 'Debug', 'asan-ubsan', 'tsan'):
                data = provenance()
                if arch == 'arm64' and profile == 'Debug':
                    data['dual_svf_blobs'] = dict(data['dual_svf_blobs'])
                    data['dual_svf_blobs'][DUAL_SECTION2_PATH] = '2' * 40
                fixture.add_tests(arch, profile, provenance_data=data)
        with self.assertRaisesRegex(RuntimeError, 'Dual SVF section-2|disagree on independent reference'):
            evaluate(self.directory.name, fixture.args)

    def test_missing_sanitizer_negative_control_fails(self):
        fixture = GateFixture(self.directory.name)
        fixture.complete_matrix()
        path = Path(self.directory.name) / 'tests-arm64-tsan' / 'report.json'
        data = json.loads(path.read_text())
        data['sanitizer_negative_controls'] = 'MISSING'
        path.write_text(json.dumps(data) + '\n')
        with self.assertRaisesRegex(RuntimeError, 'Sanitizer sensitivity controls missing'):
            evaluate(self.directory.name, fixture.args)

    def test_incomplete_native_matrix_fails(self):
        fixture = GateFixture(self.directory.name)
        fixture.args.mode = 'full'
        fixture.add_preflight('arm64')
        fixture.add_preflight('x86_64')
        fixture.add_universal()
        fixture.add_smoke('arm64')
        fixture.add_smoke('x86_64')
        with self.assertRaisesRegex(RuntimeError, 'Failed, missing, skipped or cancelled required stage'):
            evaluate(self.directory.name, fixture.args)

    def test_missing_auvst3_candidate_fails(self):
        fixture = GateFixture(self.directory.name)
        fixture.complete_matrix()
        path = Path(self.directory.name) / 'universal' / 'report.json'
        data = json.loads(path.read_text())
        data['universal_build']['binaries'] = {'Swara XT.component': {'architectures': ['arm64', 'x86_64']}}
        path.write_text(json.dumps(data) + '\n')
        with self.assertRaisesRegex(RuntimeError, 'AU/VST3 candidate inventory required'):
            evaluate(self.directory.name, fixture.args)

    def test_mismatched_candidate_hashes_fails(self):
        fixture = GateFixture(self.directory.name)
        fixture.complete_matrix()
        path = Path(self.directory.name) / 'tests-arm64-Release' / 'report.json'
        data = json.loads(path.read_text())
        data['candidate_archive_sha256'] = 'e' * 64
        path.write_text(json.dumps(data) + '\n')
        with self.assertRaisesRegex(RuntimeError, 'Different candidates across native jobs'):
            evaluate(self.directory.name, fixture.args)

    def test_missing_provenance_fails(self):
        fixture = GateFixture(self.directory.name)
        fixture.complete_matrix(omit_provenance=True)
        with self.assertRaisesRegex(RuntimeError, 'Missing audio-reference provenance'):
            evaluate(self.directory.name, fixture.args)

    def test_inspect_ctest_rejects_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'ctest.xml'
            write_ctest(path, count=60, failed=1)
            with self.assertRaisesRegex(RuntimeError, 'Failed or skipped'):
                inspect_ctest(path, 60)


if __name__ == '__main__':
    unittest.main()
