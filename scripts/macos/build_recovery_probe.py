#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 MontroneDSP
# SPDX-License-Identifier: GPL-3.0-or-later
"""Focused 1.3.1 native build/CTest recovery. NEVER certifies audio authority."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

from ci import Campaign, SOURCE, JUCE_SHA
from policy import require, hosted_root
import compiler_cache


class BuildRecoveryProbe(Campaign):
    def configure(self, juce, universal=False):
        build, config = super().configure(juce, universal)
        require(not universal, 'Only native builds may use this diagnostic')
        self.run('runner-cpu-count', ['sysctl', '-n', 'hw.logicalcpu'])
        self.run('runner-memory', ['sysctl', '-n', 'hw.memsize'])
        before = json.loads((build / 'compile_commands.json').read_text())
        ctest_before = json.loads(subprocess.check_output(
            ['ctest', '--test-dir', build, '--show-only=json-v1'], text=True))
        self.cache_tool = compiler_cache.install(self.root / 'ccache-tool')
        namespace = '-'.join((self.args.arch, self.args.profile, JUCE_SHA,
                              self.report['source_sha']))
        self.env = compiler_cache.configure_cache(
            self.root / 'ccache-cache', self.env, namespace)
        compiler = subprocess.check_output(
            ['xcrun', '--find', 'clang++'], text=True).strip()
        controls = compiler_cache.equivalence_controls(
            self.cache_tool, self.root / 'cache-controls', compiler, self.env,
            apple=True, arch=self.args.arch)
        require(controls['decision'] == 'PASS', 'Cache equivalence controls failed')
        (self.root / 'cache-controls.json').write_text(
            json.dumps(controls, indent=2) + '\n')
        cmake_controls = compiler_cache.cmake_control(
            self.cache_tool, self.root / 'cmake-cache-controls',
            compiler, self.env, arch=self.args.arch)
        (self.root / 'cmake-cache-controls.json').write_text(
            json.dumps(cmake_controls, indent=2) + '\n')
        launcher = compiler_cache.write_launcher(
            self.root / 'compiler-launcher', self.cache_tool, juce,
            build / 'generated/midi-capacity/juce_audio_utils.mm')
        self.run('configure-cache-launcher', [
            'cmake', '-S', SOURCE, '-B', build,
            *['-DCMAKE_' + lang + '_COMPILER_LAUNCHER=' + launcher
              for lang in ('C', 'CXX', 'OBJC', 'OBJCXX')]])
        after = json.loads((build / 'compile_commands.json').read_text())
        ctest_after = json.loads(subprocess.check_output(
            ['ctest', '--test-dir', build, '--show-only=json-v1'], text=True))
        require(before == after, 'Cache launcher changed compiler inputs')
        require(ctest_before == ctest_after, 'Cache launcher changed registered tests')
        inventory = compiler_cache.inventory(after)
        (self.root / 'compile-inventory.json').write_text(
            json.dumps(inventory, indent=2) + '\n')
        (self.root / 'ctest-configured.json').write_text(
            json.dumps(ctest_after, indent=2) + '\n')
        self.report['build_recovery'] = {
            'scope': 'JUCE_ONLY_CACHE; UNQUALIFIED_DIAGNOSTIC',
            'source_sha': self.report['source_sha'],
            'compiler_cache': compiler_cache.VERSION,
            'cache_namespace': namespace,
            'cache_semantics_controls': controls['decision'],
            'cmake_equivalence': cmake_controls['decision'],
            'original_compiler_commands_preserved': True,
            'registered_ctest_inventory_preserved': True,
            'compile_commands': inventory['commands'],
            'unique_translation_units': inventory['unique_translation_units'],
            'source_recompilations': inventory['recompilations'],
            'logical_cpus': int((self.root / 'runner-cpu-count.log').read_text()),
            'physical_memory_bytes': int((self.root / 'runner-memory.log').read_text()),
            'parallelism': 2,
            'audio_authority': 'REFERENCE_REVIEW_REQUIRED',
        }
        self.save()
        return build, config

    def run(self, name, argv, **kwargs):
        if name != 'build-native-tests':
            return super().run(name, argv, **kwargs)
        build = self.root / 'build'
        self.run('ninja-dry-run', [
            'ninja', '-C', build, '-n', 'SwaraXTQualificationTests'])
        self.report['build_recovery']['ninja_dry_run'] = compiler_cache.ninja_progress(
            (self.root / 'ninja-dry-run.log').read_text(errors='replace'))
        self.run('cache-before', [self.cache_tool, '--print-stats'])
        error = None
        try:
            return super().run(name, ['/usr/bin/time', '-l', *argv], **kwargs)
        except BaseException as exc:
            error = exc
            raise
        finally:
            try:
                log = (build / '.ninja_log')
                if log.is_file():
                    shutil.copy2(log, self.root / 'ninja-build-timings.log')
                self.run('cache-after', [self.cache_tool, '--print-stats'])
                def counters(filename):
                    return dict(line.split() for line in (
                        self.root / (filename + '.log')).read_text().splitlines())
                first, second = counters('cache-before'), counters('cache-after')
                self.report['build_recovery']['cache_delta'] = {
                    key: int(second.get(key, '0')) - int(first.get(key, '0'))
                    for key in ('cache_miss', 'preprocessed_cache_hit',
                                'direct_cache_hit', 'preprocessed_cache_miss')}
                text = (self.root / (name + '.log')).read_text(errors='replace')
                memory = re.findall(r'(\d+)\s+maximum resident set size', text)
                self.report['build_recovery']['max_rss_bytes'] = (
                    int(memory[-1]) if memory else None)
                self.report['build_recovery']['ninja_progress'] = (
                    compiler_cache.ninja_progress(text))
                self.save()
            except BaseException as evidence_error:
                self.report['cache_evidence_failure'] = str(evidence_error)
                self.save()
                if error is None:
                    raise

    def native_reference(self, juce, config):
        # The original authority deliberately BLOCKS. This probe records only
        # CTest technical execution and is never consumed by the release gate.
        self.report['reference_authority'] = 'REFERENCE_REVIEW_REQUIRED'
        self.report['full_qualification'] = 'NOT_ESTABLISHED'
        self.save()

    def execute(self):
        try:
            juce = self.prepare()
            build, config = self.configure(juce)
            self.run('build-platform-preflight', [
                'cmake', '--build', build, '--target',
                'AvrlibHdUpperRegisterOscillatorTests', '--parallel', '2'])
            self.run('platform-preflight', [
                'ctest', '--test-dir', build, '--output-on-failure',
                '--no-tests=error', '-R', '^AvrlibHdUpperRegisterOscillatorTests$'])
            self.regressions(build, juce, config)
            require(not subprocess.check_output(
                ['git', 'status', '--porcelain'], cwd=SOURCE, text=True).strip(),
                'Source checkout modified during diagnostic')
            self.finish_evidence()
            self.report['decision'] = 'BUILD_PROBE_PASS_NOT_QUALIFIED'
        except BaseException as error:
            self.report['decision'] = 'BUILD_PROBE_FAILED'
            self.report['failure'] = str(error)
            raise
        finally:
            self.report['full_qualification'] = 'NOT_ESTABLISHED'
            self.save()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--arch', choices=['x86_64', 'arm64'], required=True)
    parser.add_argument('--profile',
                        choices=['Release', 'Debug', 'asan-ubsan', 'tsan'], required=True)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    hosted_root(args.root, SOURCE)
    args.task = 'build-probe'
    args.mode = 'full'
    args.base_source_sha = '5e7b967db0b52f773f382217a72c6c0c3ff6b8f7'
    BuildRecoveryProbe(args).execute()


if __name__ == '__main__':
    main()
