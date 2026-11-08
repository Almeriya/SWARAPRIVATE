# SPDX-FileCopyrightText: 2026 MontroneDSP
# SPDX-License-Identifier: GPL-3.0-or-later
"""Portable negative controls for candidate provenance and packaging inventory."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from package_release_candidate import VERSION, FORMATS, PKG_ID, inventory, require


class MacQaPackagingTests(unittest.TestCase):
    def test_product_constants(self):
        self.assertEqual(VERSION, '1.3.1')
        self.assertEqual(FORMATS, ('Swara XT.component', 'Swara XT.vst3'))
        self.assertEqual(PKG_ID, 'com.montronedsp.swaraxt.macosinstaller')

    def test_manifest_hash_and_executable_ownership(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            a = root / 'AU'
            a.mkdir()
            binary = a / 'synth'
            binary.write_bytes(b'synthetic-binary-not-for-distribution')
            binary.chmod(0o755)
            state = inventory(root)
            self.assertEqual(state['AU'], ['directory'])
            self.assertEqual(state['AU/synth'][0], 'file')
            self.assertTrue(state['AU/synth'][2])
            binary.write_bytes(b'tampered')
            self.assertNotEqual(state, inventory(root))

    def test_escaping_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'escape').symlink_to('../outside')
            with self.assertRaisesRegex(RuntimeError, 'escaping symlink'):
                inventory(root)

    def test_unexpected_file_type_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'entry').mkdir()
            self.assertEqual(inventory(root), {'entry': ['directory']})

    def test_provenance_check_rejects_bogus_candidate(self):
        from package_release_candidate import verify_candidate
        with tempfile.TemporaryDirectory() as tmp:
            candidate = Path(tmp) / 'unsigned-universal'
            candidate.mkdir()
            (candidate / 'provenance.json').write_text(json.dumps({
                'source_sha': '0' * 40, 'version': VERSION, 'formats': ['AU', 'VST3'],
                'standalone': False, 'ci_bundle_signature': 'fake',
            }))
            with self.assertRaisesRegex(RuntimeError, 'provenance mismatch'):
                verify_candidate(candidate, '1' * 40, VERSION)

    def test_pkg_identifier_is_not_plugin_bundle_identifier(self):
        self.assertNotEqual(PKG_ID, 'com.MontroneDSP.SwaraXT')
        self.assertNotEqual(PKG_ID, 'com.MontroneDSP.SwaraXT.component')


if __name__ == '__main__':
    unittest.main()
