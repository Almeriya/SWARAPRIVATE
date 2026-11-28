# SPDX-FileCopyrightText: 2026 MontroneDSP
# SPDX-License-Identifier: GPL-3.0-or-later
"""Architecture-specific Mac audio authority. Candidates never approve themselves."""
BASELINE_SHA = '5e7b967db0b52f773f382217a72c6c0c3ff6b8f7'
# gate.py imports TESTS as the historical empty admission table.
TESTS = {}
ARCHITECTURES = ('x86_64', 'arm64')
PROFILES = ('Release', 'Debug', 'asan-ubsan', 'tsan')
# Full native-reference maps stay empty. A non-empty table here would still be
# insufficient for the qualification gate; Classic owner approval is recorded
# separately and is never read by require_approved_authority.
APPROVED_REFERENCES = {
    'x86_64': {},
    'arm64': {},
}
# Owner-approved public SWARA XT 1.3.3 Classic Q23 goldens only.
# Scope: Intel/ARM64 Debug and Release. Not sanitizers, not Dual SVF / Host SRC /
# integrated FX, not full native-reference admission.
CLASSIC_PROFILES = ('Debug', 'Release')
CLASSIC_PUBLIC_133_SHA = '6ea598e47fb0347d23ffa538a64b02318187a7ed'
CLASSIC_HEADER_BLOB = '6ddd3aa0b143ab65acf7e8a962d798015fd1dcc0'
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
    'full_native_admission': 'REVIEW_REQUIRED',
}


def classic_owner_status(architecture, profile):
    if architecture not in ARCHITECTURES:
        raise RuntimeError('BLOCKED: unknown macOS audio-reference architecture: ' + str(architecture))
    if profile not in PROFILES:
        raise RuntimeError('BLOCKED: unknown macOS audio-reference profile: ' + str(profile))
    if profile not in CLASSIC_PROFILES:
        return 'REVIEW_REQUIRED'
    return 'APPROVED_PUBLIC_133_CLASSIC'


def require_approved_authority(source, architecture, profile):
    if architecture is None and profile is None:
        raise RuntimeError(
            'BLOCKED: full native qualification still requires independent owner review of every '
            'native-reference family; Classic Debug/Release public 1.3.3 goldens are owner-approved '
            'separately; remaining families and sanitizer profiles remain REFERENCE_REVIEW_REQUIRED')
    if architecture not in ARCHITECTURES:
        raise RuntimeError('BLOCKED: unknown macOS audio-reference architecture: ' + str(architecture))
    if profile not in PROFILES:
        raise RuntimeError('BLOCKED: unknown macOS audio-reference profile: ' + str(profile))
    table = APPROVED_REFERENCES[architecture]
    if not table:
        raise RuntimeError(
            'BLOCKED: current 1.3.3 macOS audio authority requires independent owner review; '
            + str(architecture) + ' has no admitted full-family references; Classic Debug/Release '
            'public 1.3.3 goldens are owner-approved separately; other families and sanitizer '
            'profiles remain REFERENCE_REVIEW_REQUIRED')
    raise RuntimeError(
        'BLOCKED: current 1.3.3 macOS audio authority requires independent owner review; '
        'admitted ' + str(architecture) + ' records exist but this candidate cannot self-approve')
