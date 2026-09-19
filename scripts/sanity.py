#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Record Sanity results without confusing Speed's trailer with verification."""
import argparse
import json
import pathlib
import re
import subprocess
from benchmark import HOSTS, ROOT, write_json
from build import verify_build, sha


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--host', choices=HOSTS, required=True)
    ap.add_argument('--cpus', default='32-39')
    ap.add_argument('--out', type=pathlib.Path, default=ROOT / 'out')
    args = ap.parse_args()
    info = verify_build()
    binary = ROOT / '.work/build/SMHasher3'
    out = args.out / args.host
    out.mkdir(parents=True, exist_ok=True)
    prefix = ['taskset', '-c', args.cpus] if args.host == 'Xeon8375C' else []
    summary = dict(binary_sha256=info['binary_sha256'], host=args.host, hashes={})
    for row in json.loads((ROOT / 'manifest.json').read_text()):
        name = row['registered_names'][args.host]
        result = subprocess.run(prefix + [str(binary), name, '--test=Sanity'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        raw = out / (name + '.sanity.txt')
        raw.write_text(result.stdout)
        failures = [line for line in result.stdout.splitlines() if 'FAIL' in line or 'Invalid hash' in line]
        status = 'FAIL' if result.returncode or failures else 'PASS'
        summary['hashes'][row['name']] = dict(status=status, registered_name=name,
            returncode=result.returncode, failures=failures, raw_file=raw.name, raw_sha256=sha(raw),
            verification_lines=[line for line in result.stdout.splitlines() if re.search('Verification|verification', line)])
        print(name, status, flush=True)
    if sha(binary) != info['binary_sha256']:
        raise SystemExit('Binary changed during Sanity')
    write_json(out / 'sanity.json', summary)
    # These are hash-quality observations, not a prerequisite for measuring Speed.
    print('Saved all Sanity outcomes; inspect failures in sanity.json.')


if __name__ == '__main__':
    main()
