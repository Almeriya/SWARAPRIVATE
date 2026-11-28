# SPDX-FileCopyrightText: 2026 MontroneDSP
# SPDX-License-Identifier: GPL-3.0-or-later
import unittest
from native_reference import (
    APPROVED_REFERENCES, CLASSIC_CASES, CLASSIC_OWNER_APPROVAL, CLASSIC_PROFILES,
    TESTS, classic_owner_status, require_approved_authority)
class AuthorityTests(unittest.TestCase):
    def test_unapproved_authority_fails_closed(self):
        self.assertEqual(TESTS, {})
        self.assertEqual(APPROVED_REFERENCES, {'x86_64': {}, 'arm64': {}})
        for arch in ('arm64', 'x86_64'):
            for profile in ('Release', 'Debug', 'asan-ubsan', 'tsan'):
                with self.assertRaisesRegex(RuntimeError, 'BLOCKED'):
                    require_approved_authority('.', arch, profile)
    def test_unknown_configuration_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, 'unknown macOS audio-reference architecture'):
            require_approved_authority('.', 'universal', 'Debug')
        with self.assertRaisesRegex(RuntimeError, 'unknown macOS audio-reference profile'):
            require_approved_authority('.', 'arm64', 'RelWithDebInfo')
        with self.assertRaisesRegex(RuntimeError, 'full native qualification still requires'):
            require_approved_authority(None, None, None)
    def test_classic_owner_approval_is_narrow(self):
        self.assertEqual(len(CLASSIC_CASES), 8)
        self.assertEqual(CLASSIC_CASES['Test F filter low resonance'], 0x7cad43fd9155360d)
        self.assertEqual(CLASSIC_CASES['Test G filter high resonance'], 0xb583834c32a65866)
        self.assertEqual(CLASSIC_CASES['Test I normal envelope'], 0xac2c238b499d0be4)
        self.assertEqual(CLASSIC_PROFILES, ('Debug', 'Release'))
        self.assertFalse(CLASSIC_OWNER_APPROVAL['hashes_regenerated'])
        self.assertEqual(CLASSIC_OWNER_APPROVAL['full_native_admission'], 'REVIEW_REQUIRED')
        for arch in ('arm64', 'x86_64'):
            self.assertEqual(classic_owner_status(arch, 'Debug'), 'APPROVED_PUBLIC_133_CLASSIC')
            self.assertEqual(classic_owner_status(arch, 'Release'), 'APPROVED_PUBLIC_133_CLASSIC')
            self.assertEqual(classic_owner_status(arch, 'asan-ubsan'), 'REVIEW_REQUIRED')
            self.assertEqual(classic_owner_status(arch, 'tsan'), 'REVIEW_REQUIRED')
if __name__ == '__main__': unittest.main()
