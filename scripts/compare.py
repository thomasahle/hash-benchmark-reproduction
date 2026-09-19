#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Compare fresh timings with the frozen published chart cells; never normalize."""
import argparse
import json
import pathlib
import sys
from build import ROOT
from benchmark import SUBSET, write_json


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--speeds', type=pathlib.Path, default=ROOT / 'speeds.json')
    ap.add_argument('--reference', type=pathlib.Path, default=ROOT / 'reference/speeds.json')
    ap.add_argument('--host', default='Xeon8375C', choices=['Xeon8375C', 'M2Pro'])
    ap.add_argument('--tolerance', type=float, default=5.0)
    ap.add_argument('--subset', action='store_true', help='Require every preselected panel member')
    ap.add_argument('--output', type=pathlib.Path)
    ap.add_argument('--markdown', type=pathlib.Path)
    args = ap.parse_args()
    measured, reference = json.loads(args.speeds.read_text()), json.loads(args.reference.read_text())
    names = SUBSET if args.subset else [n for n in measured if n != 'meta' and args.host in measured[n]]
    rows = []
    failures = []
    for name in names:
        observed = measured.get(name, {}).get(args.host, {})
        baseline = reference.get(name, {}).get(args.host, {})
        if observed.get('status') != 'complete':
            failures.append(name + ': missing complete result')
            continue
        for metric in ['bulk_bytes_per_cycle', 'small_cycles']:
            old, new = baseline.get(metric), observed.get(metric)
            if old is None or new is None or old <= 0:
                failures.append(name + ': missing ' + metric)
                continue
            delta = 100 * (new / old - 1)
            rows.append(dict(name=name, metric=metric, recorded=old, measured=new, delta_percent=delta,
                             within_tolerance=abs(delta) <= args.tolerance))
    result = dict(host=args.host, tolerance_percent=args.tolerance, rows=rows, errors=failures,
                  passed=bool(rows) and not failures and all(r['within_tolerance'] for r in rows))
    lines = ['# Xeon timing comparison' if args.host == 'Xeon8375C' else '# M2 timing comparison', '',
             'Tolerance: ±' + str(args.tolerance) + '%. All differences are relative to the frozen published chart cells. No rescaling or outlier removal.', '',
             '| Hash | Metric | Recorded | Reproduced | Difference | Within tolerance |',
             '|---|---|---:|---:|---:|---|']
    for r in rows:
        lines.append('| {name} | {metric} | {recorded:.2f} | {measured:.2f} | {delta_percent:+.2f}% | {status} |'.format(**r, status='yes' if r['within_tolerance'] else 'NO'))
    lines += ['', 'Result: ' + ('PASS' if result['passed'] else 'FAIL') + '.']
    lines += failures
    report = '\n'.join(lines) + '\n'
    print(report)
    if args.output:
        write_json(args.output, result)
    if args.markdown:
        args.markdown.write_text(report)
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    sys.exit(main())
