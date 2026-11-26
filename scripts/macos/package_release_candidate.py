#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 MontroneDSP
# SPDX-License-Identifier: GPL-3.0-or-later
"""Produce and verify unnotarized macOS QA ZIP, PKG, and complete source archive.

Consumes ONLY the sealed immutable CI universal candidate. Never installs plug-ins.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import plistlib
import re
import shutil
import stat
import subprocess
import tarfile
import tempfile
import xml.etree.ElementTree as ET
import zipfile

from policy import check_bundle, digest, files_manifest, SEAL

VERSION = '1.3.3'
JUCE_SHA = 'e18f7f506c0b96f2c738a0bcd7fe6467a5005ad8'
FORMATS = ('Swara XT.component', 'Swara XT.vst3')
PKG_ID = 'com.montronedsp.swaraxt.macosinstaller'
PACKAGE_ROOT = 'Swara XT 1.3.3 macOS'


def require(ok, message):
    if not ok:
        raise RuntimeError('macOS QA packaging: ' + message)


def run(*argv, cwd=None):
    return subprocess.check_output([str(x) for x in argv], cwd=cwd,
                                   text=True, stderr=subprocess.STDOUT, timeout=900)


def git(repo, *args):
    return run('git', '-C', repo, *args).strip()


def inventory(root):
    """Relative paths, file hashes, symlink targets and execute bits."""
    root = Path(root).resolve()
    found = {}
    for current, dirs, files in os.walk(root, followlinks=False):
        for name in sorted(dirs + files):
            path = Path(current) / name
            relative = path.relative_to(root).as_posix()
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode):
                target = os.readlink(path)
                require(not os.path.isabs(target) and
                        (path.parent / target).resolve().is_relative_to(root),
                        'escaping symlink: ' + relative)
                found[relative] = ['symlink', target]
                if name in dirs:
                    dirs.remove(name)
            elif stat.S_ISDIR(mode):
                found[relative] = ['directory']
            elif stat.S_ISREG(mode):
                found[relative] = ['file', digest(path), bool(mode & 0o111)]
            else:
                raise RuntimeError('unsupported package object: ' + relative)
    return found


def verify_candidate(candidate, source_sha, version):
    candidate = Path(candidate)
    require(candidate.is_dir() and not candidate.is_symlink() and
            candidate.name == 'unsigned-universal', 'must use CI universal candidate directory')
    provenance = json.loads((candidate / 'provenance.json').read_text())
    for key, value in {
        'source_sha': source_sha, 'version': version, 'formats': ['AU', 'VST3'],
        'standalone': False, 'ci_bundle_signature': SEAL,
        'distribution_status': 'UNSIGNED_UNQUALIFIED_CANDIDATE',
    }.items():
        require(provenance.get(key) == value, 'candidate provenance mismatch: ' + key)
    require(provenance.get('qualification_status') == 'BUILD_PASS_UNQUALIFIED',
            'unqualified build status mismatch')
    require(provenance.get('juce_sha') == JUCE_SHA, 'JUCE pin changed')
    require(set(provenance.get('binaries', {})) == set(FORMATS), 'AU and VST3 only')
    require(files_manifest(candidate) == provenance['files'], 'candidate inventory or hashes changed')
    bundles = {}
    for name in FORMATS:
        bundle = candidate / name
        require(bundle.is_dir() and not bundle.is_symlink(), 'missing bundle: ' + name)
        info = check_bundle(bundle, version, ['arm64', 'x86_64'])
        require(info == provenance['binaries'][name], 'candidate binary provenance mismatch')
        run('codesign', '--verify', '--deep', '--strict', bundle)
        signature = subprocess.run(['codesign', '-dv', '--verbose=4', str(bundle)],
                                   text=True, capture_output=True, timeout=60)
        require(signature.returncode == 0 and
                'Signature=adhoc' in signature.stdout + signature.stderr,
                'QA bundles must have ad-hoc seals, not Developer ID signatures')
        bundles[name] = info
    require(set(p.name for p in candidate.iterdir()) ==
            set(FORMATS) | {'compiled-source-manifest.json', 'provenance.json'},
            'unexpected candidate files')
    return provenance, bundles


def copy_documentation(repo, destination, sha):
    destination.mkdir()
    docs = {
        'LICENSE.txt': 'COPYING',
        'COPYRIGHT.txt': 'COPYRIGHT',
        'THIRD_PARTY_NOTICES.txt': 'THIRD_PARTY_NOTICES.md',
        'PANEL_ARTWORK_ATTRIBUTION.txt': 'resources/Skin/ATTRIBUTION.md',
        'PANEL_ARTWORK_LICENSE.txt': 'resources/Skin/CC-BY-SA-3.0.txt',
        'FONT_LICENSE.txt': 'resources/Fonts/OFL-1.1.txt',
        'MIT_LICENSE.txt': 'LICENSES/MIT.txt',
        'SKIN_EXAMPLES_README.md': 'resources/Skin/Examples/README.md',
        'README.txt': 'packaging/macos/README.txt',
        'BUILDING.md': 'BUILDING.md',
    }
    for target, path in docs.items():
        shutil.copy2(repo / path, destination / target)
    source_text = (repo / 'packaging/SOURCE.txt').read_text()
    (destination / 'SOURCE.txt').write_text(
        source_text + '\nQA candidate source revision: ' + sha +
        '\nCanonical source: https://github.com/RIG-AUDIO/SW2/tree/' + sha +
        '\nMac JUCE 9.0.1 pinned source: https://github.com/juce-framework/JUCE/tree/' +
        JUCE_SHA + '\nSee the separate complete corresponding-source QA archive.\n')
    require((destination / 'LICENSE.txt').stat().st_size > 5000, 'GPL license missing')


def make_zip(package_tree, output):
    run('ditto', '-c', '-k', '--norsrc', '--noextattr', '--keepParent', package_tree, output)
    with zipfile.ZipFile(output) as archive:
        items = archive.infolist()
        require(items and archive.testzip() is None, 'ZIP CRC invalid')
        names = set()
        for item in items:
            path = item.filename.rstrip('/')
            require(path not in names, 'duplicate ZIP entry')
            names.add(path)
            parts = path.split('/')
            require(not path.startswith('/') and '..' not in parts and
                    '\\' not in path and parts[0] == PACKAGE_ROOT, 'unsafe ZIP path')
            kind = (item.external_attr >> 16) & 0o170000
            if kind == stat.S_IFLNK:
                target = archive.read(item).decode('utf-8')
                resolved = (Path('/') / path).parent.joinpath(target)
                require(not Path(target).is_absolute() and
                        os.path.commonpath(['/'.join(('/', PACKAGE_ROOT)),
                                            os.path.normpath(str(resolved))]) ==
                        '/' + PACKAGE_ROOT, 'escaping ZIP symlink')
            else:
                require(kind in (0, stat.S_IFDIR, stat.S_IFREG), 'unsafe ZIP member type')
    with tempfile.TemporaryDirectory() as temp:
        run('ditto', '-x', '-k', output, temp)
        actual = Path(temp) / PACKAGE_ROOT
        require(actual.is_dir() and inventory(actual) == inventory(package_tree),
                'ZIP roundtrip changed package contents')


def make_pkg(payload_root, output):
    run('pkgbuild', '--root', payload_root, '--identifier', PKG_ID,
        '--version', VERSION, '--install-location', '/', '--ownership',
        'recommended', output)
    with tempfile.TemporaryDirectory() as temp:
        expanded = Path(temp) / 'expanded'
        run('pkgutil', '--expand-full', output, expanded)
        infos = list(expanded.rglob('PackageInfo'))
        require(len(infos) == 1, 'unexpected PKG components')
        attrs = ET.parse(infos[0]).getroot().attrib
        require(attrs.get('identifier') == PKG_ID and
                attrs.get('version') == VERSION and
                attrs.get('install-location') == '/', 'PKG receipt/version mismatch')
        require(not list(expanded.rglob('Scripts')), 'PKG must not include installer scripts')
        roots = [p.parent for p in expanded.rglob('Library')
                 if p.is_dir() and (p / 'Audio/Plug-Ins/Components').exists()]
        require(len(roots) == 1, 'PKG payload extraction missing or ambiguous')
        require(inventory(roots[0]) == inventory(payload_root),
                'PKG payload differs from staged plug-ins')


def _git_archive(writer, repository, prefix):
    require((Path(repository) / '.git').exists() or
            (Path(repository) / '.git').is_file(), 'missing Git checkout: ' + str(repository))
    with tempfile.NamedTemporaryFile(suffix='.tar') as buffer:
        subprocess.run(['git', '-C', str(repository), 'archive',
                        '--format=tar', '-o', buffer.name, 'HEAD'],
                       check=True, timeout=600)
        with tarfile.open(buffer.name, 'r') as archive:
            for member in archive:
                require(not member.name.startswith('/') and
                        '..' not in Path(member.name).parts, 'unsafe source archive path')
                member.name = prefix + '/' + member.name
                writer.addfile(member, archive.extractfile(member) if member.isfile() else None)


def make_corresponding_source(repo, juce, source_sha, output):
    require(git(repo, 'rev-parse', 'HEAD') == source_sha,
            'source archive checkout revision mismatch')
    require(git(juce, 'rev-parse', 'HEAD') == JUCE_SHA, 'source archive JUCE pin mismatch')
    require(git(repo, 'status', '--porcelain') == '', 'source checkout is dirty')
    subs = run('git', '-C', repo, 'submodule', 'status', '--recursive')
    parsed = []
    for line in subs.splitlines():
        require(line.startswith(' '), 'missing or modified source submodule')
        fields = line[1:].split()
        require(len(fields) >= 2, 'malformed submodule record')
        relative = fields[1]
        require(git(repo / relative, 'rev-parse', 'HEAD') == fields[0],
                'submodule pin mismatch: ' + relative)
        parsed.append(relative)
    require('third_party/shruthi-1' in parsed and
            'third_party/shruthi-1/avrlib' in parsed,
            'required Shruthi and avrlib sources not initialized')
    with tarfile.open(output, 'w:gz', format=tarfile.PAX_FORMAT) as writer:
        _git_archive(writer, repo, 'SwaraXT-source-' + VERSION)
        for relative in parsed:
            _git_archive(writer, repo / relative,
                         'SwaraXT-source-' + VERSION + '/' + relative)
        _git_archive(writer, juce, 'SwaraXT-source-' + VERSION + '/third_party/JUCE')
        data = ('SWARA XT corresponding source (QA)\nCommit: ' + source_sha +
                '\nJUCE: ' + JUCE_SHA + '\nSubmodules:\n' +
                '\n'.join(parsed) + '\n').encode()
        info = tarfile.TarInfo('SwaraXT-source-' + VERSION + '/QA_SOURCE_PROVENANCE.txt')
        info.size = len(data)
        info.mode = 0o644
        writer.addfile(info, io.BytesIO(data))


def package(args):
    require(os.uname().sysname == 'Darwin', 'package production requires native macOS tools')
    require(args.version == VERSION and re.fullmatch('[0-9a-f]{40}', args.source_sha),
            'unsupported version or source SHA')
    repo = args.repo_root.resolve()
    require(git(repo, 'rev-parse', 'HEAD') == args.source_sha, 'checkout not candidate SHA')
    require(git(repo, 'status', '--porcelain') == '', 'source checkout is dirty')
    candidate = args.candidate_dir.resolve()
    output = args.output_dir.resolve()
    require(not output.exists() and not args.output_dir.is_symlink(),
            'output directory must not exist')
    require(not output.is_relative_to(candidate) and
            not candidate.is_relative_to(output) and
            not output.is_relative_to(repo), 'unsafe output ownership')
    provenance, binary_info = verify_candidate(candidate, args.source_sha, args.version)
    before = inventory(candidate)
    output.mkdir(parents=True)
    basename = 'SwaraXT-macOS-Universal-v' + VERSION
    zip_file = output / (basename + '.zip')
    pkg_file = output / (basename + '.pkg')
    source_file = output / (basename + '-corresponding-source.tar.gz')
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        display = root / PACKAGE_ROOT
        display.mkdir()
        au = display / 'AU'
        vst = display / 'VST3'
        au.mkdir()
        vst.mkdir()
        shutil.copytree(candidate / FORMATS[0], au / FORMATS[0], symlinks=True)
        shutil.copytree(candidate / FORMATS[1], vst / FORMATS[1], symlinks=True)
        examples = display / 'Skin Examples'
        shutil.copytree(repo / 'resources/Skin/Examples', examples)
        shutil.copytree(repo / 'resources/Skin/Decorations', examples / 'Decorations')
        copy_documentation(repo, display / 'Documentation', args.source_sha)
        (display / 'Documentation' / 'QA-PROVENANCE.json').write_text(json.dumps({
            'version': VERSION, 'source_sha': args.source_sha,
            'candidate_provenance_sha256': digest(candidate / 'provenance.json'),
            'binary_info': binary_info,
            'approval': 'UNQUALIFIED_AD_HOC_SIGNED_NOT_NOTARIZED',
        }, indent=2) + '\n')
        make_zip(display, zip_file)
        payload = root / 'payload'
        for fmt, target in [
            (FORMATS[0], 'Library/Audio/Plug-Ins/Components'),
            (FORMATS[1], 'Library/Audio/Plug-Ins/VST3'),
        ]:
            destination = payload / target
            destination.mkdir(parents=True, exist_ok=True)
            shutil.copytree(candidate / fmt, destination / fmt, symlinks=True)
        make_pkg(payload, pkg_file)
    require(inventory(candidate) == before, 'immutable universal candidate was modified')
    make_corresponding_source(repo, args.juce_dir.resolve(), args.source_sha, source_file)
    files = [zip_file, pkg_file, source_file]
    (output / 'SHA256SUMS').write_text(''.join(
        digest(path) + '  ' + path.name + '\n' for path in files))
    manifest = {
        'status': 'QA_ONLY_UNNOTARIZED_NOT_FOR_PUBLIC_RELEASE',
        'version': VERSION, 'source_sha': args.source_sha,
        'candidate_provenance_sha256': digest(candidate / 'provenance.json'),
        'binary_info': binary_info, 'pkg_identifier': PKG_ID,
        'files': {p.name: digest(p) for p in files},
    }
    (output / 'package-qa-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate-dir', type=Path, required=True)
    p.add_argument('--repo-root', type=Path, required=True)
    p.add_argument('--juce-dir', type=Path, required=True)
    p.add_argument('--source-sha', required=True)
    p.add_argument('--version', required=True)
    p.add_argument('--output-dir', type=Path, required=True)
    package(p.parse_args())


if __name__ == '__main__':
    main()
