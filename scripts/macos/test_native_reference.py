# SPDX-FileCopyrightText: 2026 MontroneDSP
# SPDX-License-Identifier: GPL-3.0-or-later
import tempfile
import unittest
from pathlib import Path

from native_reference import (
    APPROVED_REFERENCES, CLASSIC_CASES, CLASSIC_HEADER_BLOB, CLASSIC_HEADER_PATH,
    CLASSIC_OWNER_APPROVAL, CLASSIC_PROFILES, DUAL_INTEGRATION_BLOB, DUAL_INTEGRATION_PATH,
    DUAL_SECTION2_BLOB, DUAL_SECTION2_PATH, REFERENCE_FAMILIES, TESTS,
    classic_owner_status, require_approved_authority, verify_independent_references)

SOURCE = Path(__file__).resolve().parents[2]


def valid_evidence():
    return {
        'status': 'INDEPENDENT_REFERENCES_VERIFIED',
        'candidate_generated': False,
        'hashes_regenerated': False,
        'classic_header_blob': CLASSIC_HEADER_BLOB,
        'classic_public_133_sha': CLASSIC_OWNER_APPROVAL['public_133_sha'],
        'dual_svf_blobs': {
            DUAL_SECTION2_PATH: DUAL_SECTION2_BLOB,
            DUAL_INTEGRATION_PATH: DUAL_INTEGRATION_BLOB,
        },
        'families': {name: entry['classification'] for name, entry in REFERENCE_FAMILIES.items()},
        'REFERENCE_REVIEW_REQUIRED': False,
    }


class AuthorityTests(unittest.TestCase):
    def test_tree_provenance_verifies_on_source(self):
        evidence = verify_independent_references(SOURCE)
        self.assertEqual(evidence['status'], 'INDEPENDENT_REFERENCES_VERIFIED')
        self.assertFalse(evidence['candidate_generated'])
        self.assertEqual(evidence['classic_header_blob'], CLASSIC_HEADER_BLOB)

    def test_per_profile_passes_with_independent_evidence(self):
        evidence = valid_evidence()
        for arch in ('arm64', 'x86_64'):
            for profile in ('Release', 'Debug', 'asan-ubsan', 'tsan'):
                self.assertEqual(
                    require_approved_authority(None, arch, profile, evidence=evidence),
                    'INDEPENDENT_REFERENCES_VERIFIED')

    def test_full_gate_passes_with_independent_evidence(self):
        self.assertEqual(
            require_approved_authority(None, None, None, evidence=valid_evidence()),
            'INDEPENDENT_REFERENCES_VERIFIED')

    def test_missing_evidence_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, 'missing independent reference evidence'):
            require_approved_authority(None, 'arm64', 'Debug')
        with self.assertRaisesRegex(RuntimeError, 'missing independent reference evidence'):
            require_approved_authority(None, None, None)

    def test_unknown_configuration_fails_closed(self):
        evidence = valid_evidence()
        with self.assertRaisesRegex(RuntimeError, 'unknown macOS audio-reference architecture'):
            require_approved_authority(None, 'universal', 'Debug', evidence=evidence)
        with self.assertRaisesRegex(RuntimeError, 'unknown macOS audio-reference profile'):
            require_approved_authority(None, 'arm64', 'RelWithDebInfo', evidence=evidence)

    def test_unapproved_header_substitution_fails(self):
        evidence = valid_evidence()
        evidence['classic_header_blob'] = '0' * 40
        with self.assertRaisesRegex(RuntimeError, 'unapproved Classic/integrated reference'):
            require_approved_authority(None, 'arm64', 'Release', evidence=evidence)

    def test_candidate_generated_fails(self):
        evidence = valid_evidence()
        evidence['candidate_generated'] = True
        with self.assertRaisesRegex(RuntimeError, 'candidate-generated'):
            require_approved_authority(None, 'x86_64', 'Debug', evidence=evidence)

    def test_wrong_dual_blob_fails(self):
        evidence = valid_evidence()
        evidence['dual_svf_blobs'][DUAL_SECTION2_PATH] = '1' * 40
        with self.assertRaisesRegex(RuntimeError, 'Dual SVF section-2'):
            require_approved_authority(None, 'arm64', 'tsan', evidence=evidence)

    def test_substituted_header_file_fails_verify(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            header = root / CLASSIC_HEADER_PATH
            header.parent.mkdir(parents=True)
            header.write_text('// forged candidate golden\n')
            (root / DUAL_SECTION2_PATH).parent.mkdir(parents=True)
            (root / DUAL_SECTION2_PATH).write_bytes(b'x')
            (root / DUAL_INTEGRATION_PATH).write_bytes(b'y')
            with self.assertRaisesRegex(RuntimeError, 'unapproved reference substitution'):
                verify_independent_references(root)

    def test_classic_owner_approval_is_narrow(self):
        self.assertEqual(TESTS, {})
        self.assertEqual(APPROVED_REFERENCES, {'x86_64': {}, 'arm64': {}})
        self.assertEqual(len(CLASSIC_CASES), 8)
        self.assertEqual(CLASSIC_CASES['Test F filter low resonance'], 0x7cad43fd9155360d)
        self.assertEqual(CLASSIC_PROFILES, ('Debug', 'Release'))
        self.assertFalse(CLASSIC_OWNER_APPROVAL['hashes_regenerated'])
        self.assertEqual(CLASSIC_OWNER_APPROVAL['full_native_admission'], 'EVIDENCE_BASED_GATE')
        for arch in ('arm64', 'x86_64'):
            self.assertEqual(classic_owner_status(arch, 'Debug'), 'APPROVED_PUBLIC_133_CLASSIC')
            self.assertEqual(classic_owner_status(arch, 'Release'), 'APPROVED_PUBLIC_133_CLASSIC')
            self.assertEqual(classic_owner_status(arch, 'asan-ubsan'), 'INDEPENDENT_CLASSIC_HEADER_APPLIES')
            self.assertEqual(classic_owner_status(arch, 'tsan'), 'INDEPENDENT_CLASSIC_HEADER_APPLIES')
        self.assertTrue(all(
            entry['classification'] == 'REFERENCE_VERIFIED' for entry in REFERENCE_FAMILIES.values()))


if __name__ == '__main__':
    unittest.main()
