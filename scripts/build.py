#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Fetch the pinned source, apply the published patches, and build locally."""
import argparse
import hashlib
import json
import os
import pathlib
import platform
import shutil
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[1]
COMMIT = '3de870c7ab449ad11cf450848d9270e3f54102d1'
URL = 'https://gitlab.com/lobais/smhasher3.git'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def patch_identity():
    series = (ROOT / 'patches/series').read_text()
    if platform.machine().lower() in ('arm64', 'aarch64'):
        series += (ROOT / 'patches/series.arm64').read_text()
    patches = [ROOT / 'patches' / n for n in series.splitlines() if n]
    return patches, {'commit': COMMIT, 'patches': {p.name: sha(p) for p in patches}}


def verify_build():
    work = ROOT / '.work'
    _, expected = patch_identity()
    if json.loads((work / 'source.json').read_text()) != expected:
        raise SystemExit('Build patch set differs from this checkout; rebuild in a fresh .work')
    info = json.loads((work / 'build.json').read_text())
    if info['patches'] != expected['patches'] or sha(work / 'build/SMHasher3') != info['binary_sha256']:
        raise SystemExit('Build identity changed')
    manifest = work / 'source-sha256.json'
    if sha(manifest) != info['source_manifest_sha256']:
        raise SystemExit('Source manifest changed')
    for name, digest in json.loads(manifest.read_text()).items():
        if sha(work / 'smhasher3' / name) != digest:
            raise SystemExit('Build source changed: ' + name)
    return info


def build(jobs):
    work = ROOT / '.work'
    source = work / 'smhasher3'
    output = work / 'build'
    work.mkdir(exist_ok=True)
    patches, identity = patch_identity()
    stamp = work / 'source.json'
    def run(cmd, log=None):
        print('+', ' '.join(str(x).replace(str(ROOT), '.') for x in cmd), flush=True)
        result = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        clean = result.stdout.replace(str(ROOT), '<reproduction>').replace(str(pathlib.Path.home()), '<home>')
        if log:
            (work / log).write_text(clean)
        if result.returncode:
            print(clean[-10000:])
            result.check_returncode()
        return result.stdout
    if not stamp.exists():
        if source.exists():
            raise SystemExit('Unmanaged .work/smhasher3 exists; move .work aside before rebuilding.')
        run(['git', 'clone', '--no-checkout', URL, str(source)], 'clone.log')
        run(['git', '-C', str(source), 'fetch', 'origin', COMMIT], 'fetch.log')
        run(['git', '-C', str(source), 'checkout', '--detach', COMMIT])
        for patch in patches:
            run(['git', '-C', str(source), 'apply', '--check', str(patch)])
            run(['git', '-C', str(source), 'apply', str(patch)])
        stamp.write_text(json.dumps(identity, indent=2) + '\n')
    elif json.loads(stamp.read_text()) != identity:
        raise SystemExit('Patch set changed; move .work aside to build a fresh source tree.')
    # Refuse silent source drift when reusing a build.
    files = subprocess.check_output(['git', '-C', str(source), 'ls-files', '--cached', '--others', '--exclude-standard'], text=True).splitlines()
    hashes = {p: sha(source / p) for p in sorted(set(files)) if (source / p).is_file()}
    source_stamp = work / 'source-sha256.json'
    if source_stamp.exists() and json.loads(source_stamp.read_text()) != hashes:
        raise SystemExit('Source files changed since patch application; move .work aside.')
    source_stamp.write_text(json.dumps(hashes, indent=2) + '\n')
    cmd = ['cmake', '-S', str(source), '-B', str(output), '-DCMAKE_BUILD_TYPE=Release',
           '-DCMAKE_EXPORT_COMPILE_COMMANDS=ON', '-DENDIAN_DETECT_BUILDTIME=OFF',
           '-DDETECTED_LITTLE_ENDIAN=ON', '-DCMAKE_POLICY_VERSION_MINIMUM=3.5']
    if platform.system() == 'Darwin':
        cmd += ['-DCMAKE_CXX_FLAGS=-Xclang -target-feature -Xclang +aes']
        if 'OPENSSL_ROOT_DIR' not in os.environ and shutil.which('brew'):
            brew = subprocess.run(['brew', '--prefix', 'openssl@3'], capture_output=True, text=True)
            if brew.returncode == 0:
                cmd += ['-DOPENSSL_ROOT_DIR=' + brew.stdout.strip()]
    if os.environ.get('OPENSSL_ROOT_DIR'):
        cmd += ['-DOPENSSL_ROOT_DIR=' + os.environ['OPENSSL_ROOT_DIR']]
    run(cmd, 'configure.log')
    run(['cmake', '--build', str(output), '--target', 'SMHasher3', '-j', str(jobs)], 'build.log')
    binary = output / 'SMHasher3'
    identity.update(binary_sha256=sha(binary), source_manifest_sha256=sha(source_stamp),
                    machine=platform.machine(), system=platform.system(),
                    compiler=run([os.environ.get('CXX', 'c++'), '--version']).splitlines()[0],
                    cmake=run(['cmake', '--version']).splitlines()[0])
    flags = output / 'CMakeFiles/SMHasher3Hashlib.dir/flags.make'
    if flags.exists():
        identity['compiler_flags'] = flags.read_text().replace(str(ROOT), '<reproduction>')
    (work / 'build.json').write_text(json.dumps(identity, indent=2) + '\n')
    return binary


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--jobs', type=int, default=min(os.cpu_count() or 2, 8))
    args = ap.parse_args()
    build(args.jobs)
