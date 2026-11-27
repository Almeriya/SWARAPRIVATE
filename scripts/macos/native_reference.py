# SPDX-FileCopyrightText: 2026 MontroneDSP
# SPDX-License-Identifier: GPL-3.0-or-later
"""Architecture-specific Mac audio authority. Candidates never approve themselves."""
BASELINE_SHA = '5e7b967db0b52f773f382217a72c6c0c3ff6b8f7'
# gate.py imports TESTS as the historical empty admission table.
TESTS = {}
ARCHITECTURES = ('x86_64', 'arm64')
PROFILES = ('Release', 'Debug', 'asan-ubsan', 'tsan')
# Owner-admitted references only. A candidate render must never write these maps.
# Intel and ARM64 are independent; a hash valid on one architecture is not
# authority for the other. Do not populate these tables from unreviewed output.
APPROVED_REFERENCES = {
    'x86_64': {},
    'arm64': {},
}


def require_approved_authority(source, architecture, profile):
    if architecture not in ARCHITECTURES:
        raise RuntimeError('BLOCKED: unknown macOS audio-reference architecture: ' + str(architecture))
    if profile not in PROFILES:
        raise RuntimeError('BLOCKED: unknown macOS audio-reference profile: ' + str(profile))
    table = APPROVED_REFERENCES[architecture]
    if not table:
        raise RuntimeError(
            'BLOCKED: current 1.3.3 macOS audio authority requires independent owner review; '
            + str(architecture) + ' has no admitted references; historical fingerprints cannot '
            'qualify this candidate; REFERENCE_REVIEW_REQUIRED')
    raise RuntimeError(
        'BLOCKED: current 1.3.3 macOS audio authority requires independent owner review; '
        'admitted ' + str(architecture) + ' records exist but this candidate cannot self-approve')
