# SPDX-FileCopyrightText: 2026 MontroneDSP
# SPDX-License-Identifier: GPL-3.0-or-later
import unittest
from native_reference import APPROVED_REFERENCES, TESTS, require_approved_authority
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
if __name__ == '__main__': unittest.main()
