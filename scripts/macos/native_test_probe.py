#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 MontroneDSP
# SPDX-License-Identifier: GPL-3.0-or-later
"""Targeted native CMake target + CTest probe. NEVER certifies audio authority."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from ci import Campaign, SOURCE
from policy import require, hosted_root, revision


class NativeTestProbe(Campaign):
    def execute(self):
        target = self.args.target
        require(re.fullmatch(r'[A-Za-z0-9_]+', target), 'Invalid CMake/CTest target name')
        regex = self.args.ctest_regex or ('^' + re.escape(target) + '$')
        require(re.fullmatch(r'\^?[A-Za-z0-9_$.|()\\-]+\$?', regex),
                'Invalid CTest regex')
        try:
            juce = self.prepare()
            build, config = self.configure(juce)
            listing = json.loads(subprocess.check_output(
                ['ctest', '--test-dir', build, '--show-only=json-v1'], text=True, timeout=60))
            names = {test['name'] for test in listing['tests']}
            require(target in names, 'Requested CTest name is not registered: ' + target)
            matched = sorted(name for name in names if re.search(regex, name))
            require(matched, 'CTest regex matched no registered tests: ' + regex)
            if self.args.classic_pcm_capture:
                require(target == 'SwaraXTAudioParityTests',
                        'Classic PCM capture is limited to SwaraXTAudioParityTests')
                self.run('enable-classic-pcm-capture', [
                    'cmake', '-S', str(SOURCE), '-B', str(build),
                    '-DSWARAXT_CLASSIC_PCM_CAPTURE=ON'])
            self.run('build-target', [
                'cmake', '--build', build, '--target', target, '--parallel', '2'], timeout=10800)
            ctest_expected = None if self.args.classic_pcm_capture else 0
            ctest_code = self.run('ctest-target', [
                'ctest', '--test-dir', build, '--output-on-failure', '--no-tests=error',
                '-R', regex], timeout=1800, expected=ctest_expected)
            require(not subprocess.check_output(
                ['git', 'status', '--porcelain'], cwd=SOURCE, text=True, timeout=120).strip(),
                'Source checkout modified during diagnostic')
            captures = []
            goldens = []
            if self.args.classic_pcm_capture:
                dest = self.root / 'classic-pcm' / self.args.arch
                dest.mkdir(parents=True, exist_ok=True)
                found = {}
                for root in (build, self.root):
                    for src in root.rglob('artifacts/audio-regression/f32/*.f32'):
                        found[src.name] = src
                for name, src in sorted(found.items()):
                    payload = src.read_bytes()
                    (dest / name).write_bytes(payload)
                    captures.append({
                        'file': name,
                        'sha256': hashlib.sha256(payload).hexdigest(),
                        'bytes': len(payload),
                    })
                require(len(captures) == 8,
                        'Classic PCM capture must retain all eight Classic cases, found '
                        + str(len(captures)))
                log = (self.root / 'ctest-target.log').read_text(errors='replace')
                goldens = [line.strip() for line in log.splitlines() if 'GOLDEN classic ' in line]
            self.report['decision'] = (
                'TARGETED_NATIVE_AUDIO_CAPTURE_NOT_QUALIFIED'
                if self.args.classic_pcm_capture else
                'TARGETED_NATIVE_TEST_PASS_NOT_QUALIFIED')
            self.report['targeted_native_test'] = {
                'target': target,
                'ctest_regex': regex,
                'matched_tests': matched,
                'architecture': self.args.arch,
                'profile': self.args.profile,
                'config': config,
                'ctest_exit_code': ctest_code,
                'classic_pcm_files': captures,
                'observed_classic_golden_lines': goldens,
                'audio_authority': 'REFERENCE_REVIEW_REQUIRED',
            }
        except BaseException as error:
            self.report['decision'] = 'TARGETED_NATIVE_TEST_FAILED'
            self.report['failure'] = str(error)
            raise
        finally:
            self.report['full_qualification'] = 'NOT_ESTABLISHED'
            self.report['reference_authority'] = 'REFERENCE_REVIEW_REQUIRED'
            self.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arch', choices=['x86_64', 'arm64'], required=True)
    parser.add_argument('--profile',
                        choices=['Release', 'Debug', 'asan-ubsan', 'tsan'], required=True)
    parser.add_argument('--target', required=True,
                        help='Exact registered CMake/CTest target name')
    parser.add_argument('--ctest-regex', default=None,
                        help='Optional registered CTest name regex; default is exact target')
    parser.add_argument('--classic-pcm-capture', action='store_true',
                        help='Write Classic float32 captures; never admits goldens')
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--source-sha', required=True)
    parser.add_argument('--base-source-sha',
                        default='5e7b967db0b52f773f382217a72c6c0c3ff6b8f7')
    args = parser.parse_args()
    require(revision(args.source_sha) == os.environ['GITHUB_SHA'], 'Source revision input mismatch')
    revision(args.base_source_sha)
    hosted_root(args.root, SOURCE)
    args.task = 'native-test-probe'
    args.mode = 'build'
    args.base_source_sha = args.base_source_sha
    NativeTestProbe(args).execute()


if __name__ == '__main__':
    main()
