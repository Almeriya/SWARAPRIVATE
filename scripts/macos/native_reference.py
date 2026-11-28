# SPDX-FileCopyrightText: 2026 MontroneDSP
# SPDX-License-Identifier: GPL-3.0-or-later
"""Mac audio-reference provenance. Candidates never admit their own hashes."""
import hashlib
import json
from pathlib import Path

BASELINE_SHA = '5e7b967db0b52f773f382217a72c6c0c3ff6b8f7'
# Historical empty admission table kept for import compatibility; unused for PASS.
TESTS = {}
ARCHITECTURES = ('x86_64', 'arm64')
PROFILES = ('Release', 'Debug', 'asan-ubsan', 'tsan')
APPROVED_REFERENCES = {
    'x86_64': {},
    'arm64': {},
}
# Owner-approved public SWARA XT 1.3.3 Classic Q23 goldens.
# Same independent header applies in every build profile; CTest failure is a real
# failure, not a separate approval gate.
CLASSIC_PROFILES = ('Debug', 'Release')
CLASSIC_PUBLIC_133_SHA = '6ea598e47fb0347d23ffa538a64b02318187a7ed'
CLASSIC_HEADER_BLOB = '6ddd3aa0b143ab65acf7e8a962d798015fd1dcc0'
CLASSIC_HEADER_PATH = 'Tests/Parity/CurrentAudioGoldens.h'
CLASSIC_CASES = {
    'Test A basic saw': 0xe49a2f5d8a7090f9,
    'Test B basic square': 0x608f87853120af8e,
    'Test C two oscillators': 0x2e5f9d73aeaa1820,
    'Test F filter low resonance': 0x7cad43fd9155360d,
    'Test G filter high resonance': 0xb583834c32a65866,
    'Test I normal envelope': 0xac2c238b499d0be4,
    'Test D noise only': 0xc473d3385b5767ba,
    'Test J silence': 0x81296f5b21ed7843,
}
CLASSIC_OWNER_APPROVAL = {
    'family': 'classic',
    'count': 8,
    'architectures': ARCHITECTURES,
    'profiles': CLASSIC_PROFILES,
    'public_133_sha': CLASSIC_PUBLIC_133_SHA,
    'header_blob': CLASSIC_HEADER_BLOB,
    'intel_pcm_run': '46062372695',
    'arm64_pcm_run': '46064526245',
    'intel_debug_parity_run': '46100887687',
    'arm64_debug_parity_run': '46100889871',
    'hashes_regenerated': False,
    'full_native_admission': 'EVIDENCE_BASED_GATE',
}
DUAL_SECTION2_PATH = 'Tests/Filter/DualSvfSection2TestsMain.cpp'
DUAL_INTEGRATION_PATH = 'Tests/Filter/DualSvfIntegrationAuditMain.cpp'
DUAL_SECTION2_BLOB = '59a37d98f4cf1f41e1e27008bf5f5c966a61fce2'
DUAL_INTEGRATION_BLOB = 'a9a4cab9dd087e040d84b668d242821ce340f09a'
# Family audit: independently established tree references vs unresolved cases.
REFERENCE_FAMILIES = {
    'classic': {
        'classification': 'REFERENCE_VERIFIED',
        'path': CLASSIC_HEADER_PATH,
        'blob': CLASSIC_HEADER_BLOB,
        'origin': 'public SWARA XT 1.3.3 CurrentAudioGoldens.h',
        'public_133_sha': CLASSIC_PUBLIC_133_SHA,
        'notes': 'Owner-approved Classic Q23; same independent header for all profiles',
    },
    'integrated_fx': {
        'classification': 'REFERENCE_VERIFIED',
        'path': CLASSIC_HEADER_PATH,
        'blob': CLASSIC_HEADER_BLOB,
        'origin': 'same protected CurrentAudioGoldens.h kIntegrated table',
        'notes': 'Independent Phase3/public table in protected header; CTest is authority',
    },
    'dual_svf_section2': {
        'classification': 'REFERENCE_VERIFIED',
        'path': DUAL_SECTION2_PATH,
        'blob': DUAL_SECTION2_BLOB,
        'origin': 'protected Mac Dual SVF selector → DualSvfCurrentLinuxGoldens.h',
        'notes': 'Tree-pinned independent selectors; mismatch fails CTest',
    },
    'dual_svf_integration': {
        'classification': 'REFERENCE_VERIFIED',
        'path': DUAL_INTEGRATION_PATH,
        'blob': DUAL_INTEGRATION_BLOB,
        'origin': 'protected Mac Dual SVF integration audit',
        'notes': 'Tree-pinned independent selectors; mismatch fails CTest',
    },
    'host_src': {
        'classification': 'REFERENCE_VERIFIED',
        'path': 'Tests/Parity/ExactParityGoldens.h',
        'origin': 'ExactParityGoldens.h kSrc (shared independent table)',
        'notes': 'Not candidate-generated; CTest enforces exact match',
    },
}


def _blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + bytes([0]) + data).hexdigest()


def classic_owner_status(architecture, profile):
    if architecture not in ARCHITECTURES:
        raise RuntimeError('BLOCKED: unknown macOS audio-reference architecture: ' + str(architecture))
    if profile not in PROFILES:
        raise RuntimeError('BLOCKED: unknown macOS audio-reference profile: ' + str(profile))
    if profile not in CLASSIC_PROFILES:
        return 'INDEPENDENT_CLASSIC_HEADER_APPLIES'
    return 'APPROVED_PUBLIC_133_CLASSIC'


def verify_independent_references(source):
    """Situation A: immutable tree references. Situation B would set candidate_generated."""
    root = Path(source)
    if CLASSIC_OWNER_APPROVAL.get('hashes_regenerated'):
        raise RuntimeError('BLOCKED: Classic goldens were regenerated from candidate output')
    classic = root / CLASSIC_HEADER_PATH
    if not classic.is_file() or classic.is_symlink():
        raise RuntimeError('BLOCKED: missing independent Classic/integrated golden header')
    classic_blob = _blob(classic.read_bytes())
    if classic_blob != CLASSIC_HEADER_BLOB:
        raise RuntimeError(
            'BLOCKED: unapproved reference substitution in ' + CLASSIC_HEADER_PATH
            + '; expected ' + CLASSIC_HEADER_BLOB + ' observed ' + classic_blob)
    text = classic.read_text()
    for name, value in CLASSIC_CASES.items():
        token = '0x' + format(value, 'x') + 'ull'
        if name not in text or token not in text:
            raise RuntimeError('BLOCKED: Classic case missing from independent header: ' + name)
    dual = {}
    for path, expected in (
            (DUAL_SECTION2_PATH, DUAL_SECTION2_BLOB),
            (DUAL_INTEGRATION_PATH, DUAL_INTEGRATION_BLOB)):
        file = root / path
        if not file.is_file() or file.is_symlink():
            raise RuntimeError('BLOCKED: missing independent Dual SVF reference: ' + path)
        observed = _blob(file.read_bytes())
        if observed != expected:
            raise RuntimeError(
                'BLOCKED: unapproved Dual SVF reference substitution in ' + path
                + '; expected ' + expected + ' observed ' + observed)
        dual[path] = observed
    families = {name: entry['classification'] for name, entry in REFERENCE_FAMILIES.items()}
    unresolved = [name for name, status in families.items() if status == 'REFERENCE_REVIEW_REQUIRED']
    if unresolved:
        raise RuntimeError(
            'BLOCKED: native-reference families still require owner review: '
            + ', '.join(unresolved))
    return {
        'status': 'INDEPENDENT_REFERENCES_VERIFIED',
        'candidate_generated': False,
        'hashes_regenerated': False,
        'classic_header_blob': classic_blob,
        'classic_public_133_sha': CLASSIC_PUBLIC_133_SHA,
        'dual_svf_blobs': dual,
        'families': families,
        'REFERENCE_REVIEW_REQUIRED': False,
    }


def require_approved_authority(source, architecture, profile, evidence=None):
    """Pass only when independent reference provenance is verified. Never auto-admits hashes."""
    if architecture is None and profile is None:
        if evidence is None and source not in (None, ''):
            evidence = verify_independent_references(source)
        if evidence is None:
            raise RuntimeError(
                'BLOCKED: full native qualification missing independent reference evidence')
        if evidence.get('candidate_generated') or evidence.get('hashes_regenerated'):
            raise RuntimeError('BLOCKED: candidate-generated or regenerated references are not authority')
        if evidence.get('status') != 'INDEPENDENT_REFERENCES_VERIFIED':
            raise RuntimeError('BLOCKED: independent reference provenance incomplete for full gate')
        if evidence.get('classic_header_blob') != CLASSIC_HEADER_BLOB:
            raise RuntimeError('BLOCKED: Classic/integrated header provenance mismatch for full gate')
        return evidence['status']
    if architecture not in ARCHITECTURES:
        raise RuntimeError('BLOCKED: unknown macOS audio-reference architecture: ' + str(architecture))
    if profile not in PROFILES:
        raise RuntimeError('BLOCKED: unknown macOS audio-reference profile: ' + str(profile))
    if evidence is None:
        if source in (None, ''):
            raise RuntimeError(
                'BLOCKED: ' + str(architecture) + '/' + str(profile)
                + ' missing independent reference evidence')
        evidence = verify_independent_references(source)
    if evidence.get('candidate_generated') or evidence.get('hashes_regenerated'):
        raise RuntimeError('BLOCKED: candidate-generated or regenerated references are not authority')
    if evidence.get('status') != 'INDEPENDENT_REFERENCES_VERIFIED':
        raise RuntimeError(
            'BLOCKED: independent reference provenance incomplete for '
            + str(architecture) + '/' + str(profile))
    if evidence.get('classic_header_blob') != CLASSIC_HEADER_BLOB:
        raise RuntimeError('BLOCKED: unapproved Classic/integrated reference substitution')
    dual = evidence.get('dual_svf_blobs') or {}
    if dual.get(DUAL_SECTION2_PATH) != DUAL_SECTION2_BLOB:
        raise RuntimeError('BLOCKED: unapproved Dual SVF section-2 reference substitution')
    if dual.get(DUAL_INTEGRATION_PATH) != DUAL_INTEGRATION_BLOB:
        raise RuntimeError('BLOCKED: unapproved Dual SVF integration reference substitution')
    return evidence['status']


def family_audit():
    return json.loads(json.dumps(REFERENCE_FAMILIES))
