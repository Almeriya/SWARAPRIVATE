# SPDX-FileCopyrightText: 2026 MontroneDSP
# SPDX-License-Identifier: GPL-3.0-or-later
"""Negative controls: 1.3.3 source admission never approves generated audio."""
import copy
import json
import unittest
from source_profile_133 import MANIFEST, MAC_131_SHA, PUBLIC_133_SHA, validate_tree


class SourceProfile133Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST.read_text())
        cls.base = dict(cls.manifest['source'])
        cls.base.update(cls.manifest['apple_source_exceptions'])
        cls.base.update(cls.manifest['protected_mac_tests'])
        cls.current = dict(cls.base)
        cls.current.update({p: v for p, v in cls.manifest['transport_tests'].items() if v is not None})
        for p, v in cls.manifest['transport_tests'].items():
            if v is None:
                cls.current.pop(p, None)
        for p in ('CMakeLists.txt', 'Tests/CMakeLists.txt', 'scripts/macos/policy.py',
                  'scripts/macos/test_ci.py', 'scripts/macos/source_profile_133.py',
                  'scripts/macos/source_profile_133_manifest.json',
                  'scripts/macos/test_source_profile_133.py'):
            cls.base.setdefault(p, 'baseline-sha')
            cls.current[p] = 'reviewed-sha'
        cls.base['third_party/shruthi-1'] = cls.current['third_party/shruthi-1'] = 'pinned'
        for path, blob in cls.manifest['release_metadata'].items():
            cls.base.setdefault(path, 'historical-blob')
            cls.current[path] = blob

    def test_approved_overlay_only(self):
        result = validate_tree(self.base, self.current, self.manifest)
        self.assertEqual(result['source_files'], 189)
        self.assertEqual(result['apple_exceptions'], 5)
        self.assertEqual(result['native_audio_reference'], 'REVIEW_REQUIRED')

    def test_pinned_revisions(self):
        self.assertEqual(self.manifest['public_133_commit'], PUBLIC_133_SHA)
        self.assertEqual(self.manifest['mac_131_baseline'], MAC_131_SHA)

    def test_retired_source_stays_absent(self):
        for path in self.manifest['removed_source']:
            with self.subTest(path=path):
                self.assertNotIn(path, self.base)
                self.assertNotIn(path, self.current)
                restored = dict(self.current)
                restored[path] = self.manifest['removed_source'][path]
                with self.assertRaisesRegex(RuntimeError, 'retired source restored'):
                    validate_tree(self.base, restored, self.manifest)

    def test_reviewed_release_metadata(self):
        self.assertGreaterEqual(len(self.manifest['release_metadata']), 13)
        self.assertEqual(self.current['CMakeLists.txt'],
                         self.manifest['release_metadata']['CMakeLists.txt'])
        report = validate_tree(self.base, self.current, self.manifest)
        self.assertEqual(report['native_audio_reference'], 'REVIEW_REQUIRED')
        for path in self.manifest['release_metadata']:
            with self.subTest(path=path):
                modified = dict(self.current)
                modified[path] = '0' * 40
                with self.assertRaisesRegex(RuntimeError, 'reviewed release metadata changed'):
                    validate_tree(self.base, modified, self.manifest)
        mutated = copy.deepcopy(self.manifest)
        mutated['release_metadata']['packaging/macos/unreviewed.sh'] = '0' * 40
        with self.assertRaisesRegex(RuntimeError, 'unreviewed release metadata'):
            validate_tree(self.base, self.current, mutated)
        changed = dict(self.current)
        changed['packaging/macos/unreviewed.sh'] = '0' * 40
        with self.assertRaisesRegex(RuntimeError, 'unreviewed repository difference'):
            validate_tree(self.base, changed, self.manifest)

    def test_negative_mutations(self):
        cases = [
            ('production IR3109 change', 'Source/Engine/Filter/Circuit/Ir3109BoardCore.h', 'BAD'),
            ('CV engine change', 'Source/Engine/SwaraXtEngine.cpp', 'BAD'),
            ('parser change', 'Source/Tuning/TuningTable.cpp', 'BAD'),
            ('Apple host FP guard change', 'Source/Engine/SampleRate/HostResampler.cpp', 'BAD'),
            ('missing UI', 'Source/Ui/SwaraXtSeqPanel.cpp', None),
            ('unrecognized source', 'Source/Unexpected.cpp', 'BAD'),
            ('golden rewritten', 'Tests/Parity/CurrentAudioGoldens.h', 'BAD'),
            ('Apple reference changed', 'Tests/Filter/DualSvfSection2TestsMain.cpp', 'BAD'),
            ('cutoff contract mutated', 'Tests/Filter/CutoffContractTestsMain.cpp', 'BAD'),
        ]
        for name, path, sha in cases:
            with self.subTest(name=name):
                modified = dict(self.current)
                if sha is None:
                    modified.pop(path, None)
                else:
                    modified[path] = sha
                with self.assertRaisesRegex(RuntimeError, 'rejected'):
                    validate_tree(self.base, modified, self.manifest)

    def test_revision_and_exception_inventory_cannot_expand(self):
        altered = copy.deepcopy(self.manifest)
        altered['public_133_commit'] = '0' * 40
        with self.assertRaises(RuntimeError):
            validate_tree(self.base, self.current, altered)
        altered = copy.deepcopy(self.manifest)
        altered['apple_source_exceptions']['Source/Engine/SwaraXtEngine.cpp'] = 'BAD'
        with self.assertRaises(RuntimeError):
            validate_tree(self.base, self.current, altered)

    def test_audio_authority_never_self_approved(self):
        report = validate_tree(self.base, self.current, self.manifest)
        self.assertEqual(report['native_audio_reference'], 'REVIEW_REQUIRED')


if __name__ == '__main__':
    unittest.main()
