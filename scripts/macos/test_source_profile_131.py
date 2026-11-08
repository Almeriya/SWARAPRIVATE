# SPDX-FileCopyrightText: 2026 MontroneDSP
# SPDX-License-Identifier: GPL-3.0-or-later
"""Negative controls: 1.3.1 source admission never approves generated audio."""
import copy
import json
import unittest
from source_profile_131 import MANIFEST, SW2_BASE_SHA, validate_tree

class SourceProfile131Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST.read_text())
        cls.base = dict(cls.manifest['source'])
        cls.base.update(cls.manifest['apple_source_exceptions'])
        cls.base.update(cls.manifest['removed_source'])
        cls.base.update(cls.manifest['protected_mac_tests'])
        cls.current = dict(cls.base)
        for path in cls.manifest['removed_source']:
            cls.current.pop(path)
        cls.current.update({p: v for p, v in cls.manifest['transport_tests'].items() if v is not None})
        for p, v in cls.manifest['transport_tests'].items():
            if v is None:
                cls.current.pop(p, None)
        for p in ('CMakeLists.txt','Tests/CMakeLists.txt','scripts/macos/policy.py',
                  'scripts/macos/test_ci.py','scripts/macos/source_profile_131.py',
                  'scripts/macos/source_profile_131_manifest.json',
                  'scripts/macos/test_source_profile_131.py'):
            cls.base.setdefault(p, 'baseline-sha')
            cls.current[p] = 'reviewed-sha'
        cls.base['third_party/shruthi-1'] = cls.current['third_party/shruthi-1'] = 'pinned'

    def test_approved_overlay_only(self):
        result = validate_tree(self.base, self.current, self.manifest)
        self.assertEqual(result['source_files'], 189)
        self.assertEqual(result['apple_exceptions'], 5)
        self.assertEqual(result['native_audio_reference'], 'REVIEW_REQUIRED')

    def test_real_committed_git_trees(self):
        """Positive admission using full git ls-tree output for exact committed refs."""
        import subprocess
        from policy import git_tree

        root = MANIFEST.resolve().parents[2]
        def git(*args):
            return subprocess.check_output(
                ['git', *args], cwd=root, text=True, timeout=60).strip()

        self.assertEqual(git('rev-parse', '--show-toplevel'), str(root))
        self.assertEqual(git('status', '--porcelain', '--untracked-files=all'), '',
                         'Real source admission requires a clean checkout')
        head = git('rev-parse', 'HEAD')
        self.assertNotEqual(head, SW2_BASE_SHA, 'Expected migrated commit')
        subprocess.run(['git', 'merge-base', '--is-ancestor', SW2_BASE_SHA, head],
                       cwd=root, check=True, timeout=60)
        baseline = {path: row.split()[-1]
                    for path, row in git_tree(root, SW2_BASE_SHA).items()}
        candidate = {path: row.split()[-1]
                     for path, row in git_tree(root, head).items()}
        report = validate_tree(baseline, candidate, self.manifest)
        self.assertEqual(report['source_files'], 189)
        self.assertEqual(report['native_audio_reference'], 'REVIEW_REQUIRED')
        for path, original_sha in self.manifest['removed_source'].items():
            self.assertEqual(baseline.get(path), original_sha)
            self.assertNotIn(path, candidate)

    def test_retired_source_deletion_negative_controls(self):
        """Both the original SHA and candidate absence are required for each header."""
        for path, original_sha in self.manifest['removed_source'].items():
            with self.subTest(kind='baseline_sha', path=path):
                tampered_baseline = dict(self.base)
                tampered_baseline[path] = '0' * 40
                with self.assertRaisesRegex(RuntimeError, 'retired source baseline mismatch'):
                    validate_tree(tampered_baseline, self.current, self.manifest)
            with self.subTest(kind='restored_in_candidate', path=path):
                restored = dict(self.current)
                restored[path] = original_sha
                with self.assertRaisesRegex(RuntimeError, 'retired source restored'):
                    validate_tree(self.base, restored, self.manifest)
        with self.subTest(kind='extra_arbitrary_source_deletion'):
            missing = dict(self.current)
            missing.pop('Source/Engine/Filter/Circuit/Ir3109BoardCore.h')
            with self.assertRaisesRegex(RuntimeError, 'Source/ blob manifest mismatch'):
                validate_tree(self.base, missing, self.manifest)
        with self.subTest(kind='manifest_extra_deletion'):
            enlarged = copy.deepcopy(self.manifest)
            enlarged['removed_source']['Source/Other.h'] = '0' * 40
            with self.assertRaisesRegex(RuntimeError, 'unreviewed source deletion inventory'):
                validate_tree(self.base, self.current, enlarged)
        with self.subTest(kind='manifest_wrong_old_sha'):
            tampered = copy.deepcopy(self.manifest)
            path = next(iter(tampered['removed_source']))
            tampered['removed_source'][path] = '0' * 40
            with self.assertRaisesRegex(RuntimeError, 'unreviewed source deletion inventory'):
                validate_tree(self.base, self.current, tampered)
        with self.subTest(kind='manifest_missing_deletion'):
            missing = copy.deepcopy(self.manifest)
            missing['removed_source'].pop(next(iter(missing['removed_source'])))
            with self.assertRaisesRegex(RuntimeError, 'unreviewed source deletion inventory'):
                validate_tree(self.base, self.current, missing)

    def test_negative_mutations(self):
        cases = [
            ('production IR3109 change', 'Source/Engine/Filter/Circuit/Ir3109BoardCore.h', 'BAD'),
            ('CV engine change', 'Source/Engine/SwaraXtEngine.cpp', 'BAD'),
            ('parser change', 'Source/Tuning/TuningTable.cpp', 'BAD'),
            ('Apple host FP guard change', 'Source/Engine/SampleRate/HostResampler.cpp', 'BAD'),
            ('missing UI', 'Source/Ui/SwaraXtSeqPanel.cpp', None),
            ('additional production source deleted', 'Source/Engine/SwaraXtEngine.h', None),
            ('legacy filter restored', 'Source/Engine/Filter/Circuit/ActiveLoadPole.h', 'BAD'),
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
        altered['upstream_commit'] = '0' * 40
        with self.assertRaises(RuntimeError):
            validate_tree(self.base, self.current, altered)
        altered = copy.deepcopy(self.manifest)
        altered['apple_source_exceptions']['Source/Engine/SwaraXtEngine.cpp'] = 'BAD'
        with self.assertRaises(RuntimeError):
            validate_tree(self.base, self.current, altered)

if __name__ == '__main__':
    unittest.main()
