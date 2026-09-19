#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Merge completed timing cells into a post data.json without changing other fields."""
import argparse
import copy
import json
import math
import os
import pathlib
from build import ROOT
from benchmark import write_json

METRICS = {'bulk_Bpc': 'bulk_bytes_per_cycle', 'small_cycles': 'small_cycles'}
HOSTS = {'m2': 'M2Pro', 'xeon': 'Xeon8375C'}


def merge(data, records, manifest):
    data = copy.deepcopy(data)
    count = 0
    for item in manifest:
        row = next((r for r in data.get(item['group'], []) if r.get('id') == item['row_id']), None)
        if row is None:
            continue
        for short, host in HOSTS.items():
            source = records.get(item['name'], {}).get(host)
            if not source or source.get('status') != 'complete':
                continue
            if source.get('registered_name') != item['registered_names'][host]:
                raise ValueError('Registration mismatch for ' + item['row_id'] + '/' + host)
            for suffix, metric in METRICS.items():
                value = source[metric]
                if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value <= 0:
                    raise ValueError('Invalid completed metric: ' + item['name'] + '/' + metric)
                cell = dict(value=value, host=host, registered_name=source['registered_name'],
                    source='SMHasher3 reproduction: ' + source['aggregation'], source_short='SMHasher3 ' + host,
                    record=source['_record'], url=source['_file'], selection=source['aggregation'],
                    binary_sha256=source['binary_sha256'], verification=source.get('verification', {'status': 'not-run'}),
                    selected_run=source['bulk_selected_run' if suffix == 'bulk_Bpc' else 'small_selected_run'],
                    spread_percent=source['bulk_run_spread_percent' if suffix == 'bulk_Bpc' else 'small_run_spread_percent'])
                row.setdefault('speeds', {})['smh_' + short + '_' + suffix] = cell
                count += 1
    return data, count


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--data', type=pathlib.Path, default=ROOT / 'reference/data.json')
    ap.add_argument('--speeds', type=pathlib.Path, nargs='+', required=True)
    ap.add_argument('--output', type=pathlib.Path, default=ROOT / 'data.json')
    args = ap.parse_args()
    records = {}
    for path in args.speeds:
        doc = json.loads(path.read_text())
        for name, hosts in doc.items():
            if name == 'meta':
                continue
            for host, source in hosts.items():
                if host not in HOSTS.values():
                    continue
                source['_file'] = os.path.relpath(path.resolve(), args.output.resolve().parent)
                source['_record'] = source['_file'] + '#/' + name + '/' + host
                records.setdefault(name, {})[host] = source
    data, count = merge(json.loads(args.data.read_text()), records, json.loads((ROOT / 'manifest.json').read_text()))
    if count == 0:
        raise SystemExit('No completed speed cells matched the chart manifest')
    write_json(args.output, data)
    print('Updated', count, 'speed cells in', args.output.name)


if __name__ == '__main__':
    main()
