#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""One-command source build and serial SMHasher3 Speed reproduction."""
import argparse
import datetime
import fcntl
import json
import math
import os
import pathlib
import platform
import re
import statistics
import subprocess
import time
from build import ROOT, build, sha, verify_build

MONITORED_CPUS = None
HOSTS = ('M2Pro', 'Xeon8375C')
SUBSET = ['rapidhash', 'XXH3-64', 'komihash', 'chainhash-256', 'chainhash-v3',
          'chainhash-128', 'HalftimeHash24-shipped', 'MuseAir-v2', 'foldhash-fast', 'GoMapHash']


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write_json(path, obj):
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n')
    temp.replace(path)


def parse(text):
    if 'Testing took ' not in text:
        raise ValueError('Speed output is incomplete')
    small = re.search(r'Small key speed test - \[1, 31\]-byte keys\s+(.*?)\n\s*Average\s*-\s*([\d.]+) cycles/hash', text, re.S)
    bulk = re.search(r'Bulk speed test - 262144-byte keys\s+(.*?)\n\s*Average\s*-\s*([\d.]+) bytes/cycle\s*-\s*([\d.]+) GiB/sec', text, re.S)
    if not small or not bulk:
        raise ValueError('Expected fixed 262144-byte and 1–31-byte sections')
    if len(re.findall(r'^\s*\d+-byte keys', small[1], re.M)) != 31:
        raise ValueError('Missing small-key measurements')
    if len(re.findall(r'^\s*Alignment\s+\d', bulk[1], re.M)) != 8:
        raise ValueError('Missing alignment measurements')
    metrics = dict(bulk_bytes_per_cycle=float(bulk[2]), bulk_gib_s=float(bulk[3]), small_cycles=float(small[2]))
    if not all(math.isfinite(v) and v > 0 for v in metrics.values()):
        raise ValueError('Invalid timing value')
    return metrics


def select(runs, host):
    if len(runs) != (3 if host == 'M2Pro' else 2):
        raise ValueError('Wrong number of passes')
    if host == 'M2Pro':
        bulk = sorted(runs, key=lambda r: (r['bulk_bytes_per_cycle'], r['run']))[1]
        small = sorted(runs, key=lambda r: (r['small_cycles'], r['run']))[1]
    else:
        bulk = max(runs, key=lambda r: (r['bulk_bytes_per_cycle'], r['bulk_gib_s'], -r['run']))
        small = min(runs, key=lambda r: (r['small_cycles'], r['run']))
    result = dict(status='complete', runs=runs, bulk_bytes_per_cycle=bulk['bulk_bytes_per_cycle'],
                  bulk_gib_s=bulk['bulk_gib_s'], small_cycles=small['small_cycles'],
                  bulk_selected_run=bulk['run'], small_selected_run=small['run'],
                  aggregation='median-of-three' if host == 'M2Pro' else 'higher-bulk-lower-small-of-two')
    result['variation'] = {}
    for key, prefix in [('bulk_bytes_per_cycle', 'bulk'), ('small_cycles', 'small')]:
        values = [r[key] for r in runs]
        median = statistics.median(values)
        spread = 100 * (max(values) / min(values) - 1)
        deviations = [100 * (v / median - 1) for v in values]
        result[prefix + '_run_spread_percent'] = spread
        result['variation'][key] = dict(median=median, values=values,
            deviations_from_median_percent=deviations, range_over_min_percent=spread,
            flag_over_15_percent=any(abs(d) > 15 for d in deviations) if host == 'M2Pro' else spread > 15)
    return result


def state():
    ps = subprocess.check_output(['ps', '-axo', 'pid=,comm='], text=True)
    processes = []
    for line in ps.splitlines():
        fields = line.strip().split(None, 1)
        if len(fields) == 2 and pathlib.Path(fields[1]).name.lower() == 'smhasher3':
            pid = int(fields[0])
            try:
                if MONITORED_CPUS is None or MONITORED_CPUS.intersection(os.sched_getaffinity(pid)):
                    processes.append(pid)
            except ProcessLookupError:
                pass
    return dict(timestamp=now(), load=list(os.getloadavg()), smhasher_pids=processes)


def gate(host, out):
    while True:
        snapshot = state()
        with (out / 'gate.jsonl').open('a') as f:
            f.write(json.dumps(snapshot) + '\n')
        if not snapshot['smhasher_pids'] and (host != 'M2Pro' or snapshot['load'][0] < 4.5):
            return snapshot
        print(now(), 'waiting for no SMHasher3 process' + (' and load1 < 4.5' if host == 'M2Pro' else ''), flush=True)
        time.sleep(60)


def cpu_set(spec):
    result = set()
    for item in spec.split(','):
        bounds = [int(x) for x in item.split('-')]
        result.update(range(bounds[0], bounds[-1] + 1))
    if not result:
        raise ValueError('Empty CPU set')
    return result


def main():
    global MONITORED_CPUS
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--host', choices=HOSTS)
    ap.add_argument('--names', nargs='+', help='Manifest names or chart row IDs; default: all 43 timed rows')
    ap.add_argument('--subset', action='store_true', help='The preselected ten-hash verification panel')
    ap.add_argument('--cpus', default='32-39', help='Xeon taskset CPU set (default: 32-39)')
    ap.add_argument('--jobs', type=int, default=min(os.cpu_count() or 2, 8))
    ap.add_argument('--skip-build', action='store_true', help='Use the existing verified build')
    ap.add_argument('--out', type=pathlib.Path, default=ROOT / 'out')
    ap.add_argument('--output', type=pathlib.Path, default=ROOT / 'speeds.json')
    args = ap.parse_args()
    host = args.host or ('M2Pro' if platform.system() == 'Darwin' and platform.machine() == 'arm64' else 'Xeon8375C')
    if (host == 'M2Pro' and (platform.system(), platform.machine()) != ('Darwin', 'arm64')) or (host == 'Xeon8375C' and (platform.system(), platform.machine()) != ('Linux', 'x86_64')):
        ap.error('Host profile requires macOS arm64 or Linux x86_64 respectively')
    if host == 'Xeon8375C':
        MONITORED_CPUS = cpu_set(args.cpus)
        for cpu in list(MONITORED_CPUS):
            siblings = pathlib.Path('/sys/devices/system/cpu/cpu' + str(cpu) + '/topology/thread_siblings_list')
            if siblings.exists():
                MONITORED_CPUS.update(cpu_set(siblings.read_text().strip()))
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    requested = SUBSET if args.subset else args.names
    rows = [r for r in manifest if requested is None or r['name'] in requested or r['row_id'] in requested]
    if requested and set(requested) - {s for r in rows for s in [r['name'], r['row_id']]}:
        ap.error('Unknown name or row ID')
    if args.subset and args.names:
        ap.error('Use --subset or --names, not both')
    out = args.out.resolve() / host
    out.mkdir(parents=True, exist_ok=True)
    args.output = args.output.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # One runner per checkout; other checkouts are observed by the process gate.
    with (ROOT / '.benchmark.lock').open('w') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise SystemExit('Another reproduction runner holds this checkout lock')
        gate(host, out)
        binary = ROOT / '.work/build/SMHasher3' if args.skip_build else build(args.jobs)
        build_info = verify_build()
        if sha(binary) != build_info['binary_sha256']:
            raise SystemExit('Binary differs from build manifest')
        prefix = ['taskset', '-c', args.cpus] if host == 'Xeon8375C' else []
        listing = subprocess.check_output(prefix + [str(binary), '--list'], text=True, stderr=subprocess.STDOUT)
        (out / 'registrations.txt').write_text(listing)
        registrations = {line.split()[0]: line.strip() for line in listing.splitlines() if line.split()}
        for row in rows:
            if row['registered_names'][host] not in registrations:
                raise SystemExit('Missing registration: ' + row['registered_names'][host])
        config = dict(host=host, names=[r['name'] for r in rows], registered_names=[r['registered_names'][host] for r in rows],
                      cpus=args.cpus if host == 'Xeon8375C' else None, binary_sha256=sha(binary),
                      passes=3 if host == 'M2Pro' else 2, protocol_version=1, monitored_cpus=sorted(MONITORED_CPUS) if MONITORED_CPUS else None)
        execution = dict(config=config, started=now(), build=build_info, runs=[], excluded_runs=[])
        execution_file = out / 'execution.json'
        if execution_file.exists():
            execution = json.loads(execution_file.read_text())
            if execution['config'] != config:
                raise SystemExit('Existing output has another configuration; use a fresh --out directory')
            for run in execution['runs'] + execution['excluded_runs']:
                if sha(out / run['raw_file']) != run['raw_sha256']:
                    raise SystemExit('Saved raw output changed: ' + run['raw_file'])
        for rep in range(1, config['passes'] + 1):
            for row in rows:
                name, registered = row['name'], row['registered_names'][host]
                if any(r['name'] == name and r['run'] == rep for r in execution['runs']):
                    continue
                while True:
                    before = gate(host, out)
                    if sha(binary) != config['binary_sha256']:
                        raise SystemExit('Binary changed during experiment')
                    raw = out / (registered + '.run' + str(rep) + '.txt')
                    command = prefix + [str(binary), registered, '--test=Speed']
                    run = dict(name=name, registered_name=registered, run=rep, started=now(), load_before=before,
                               command=prefix + ['.work/build/SMHasher3', registered, '--test=Speed'], samples=[], overlaps=[])
                    print(now(), host, registered, 'pass', rep, flush=True)
                    start = time.monotonic()
                    with raw.open('w') as f:
                        process = subprocess.Popen(command, stdout=f, stderr=subprocess.STDOUT)
                        while process.poll() is None:
                            snapshot = state()
                            run['samples'].append(snapshot)
                            others = [pid for pid in snapshot['smhasher_pids'] if pid != process.pid]
                            if others:
                                run['overlaps'].append(dict(timestamp=snapshot['timestamp'], pids=others))
                            time.sleep(5)
                    run.update(returncode=process.returncode, elapsed_seconds=time.monotonic() - start,
                               finished=now(), load_after=state(), raw_file=raw.name, raw_sha256=sha(raw))
                    if process.returncode:
                        write_json(execution_file, execution)
                        raise SystemExit('Speed command failed; see ' + str(raw))
                    run.update(parse(raw.read_text()))
                    if run['overlaps']:
                        archived = raw.with_name(raw.stem + '.excluded-' + str(time.time_ns()) + '.txt')
                        raw.rename(archived)
                        run['raw_file'] = archived.name
                        execution['excluded_runs'].append(run)
                        write_json(execution_file, execution)
                        continue
                    execution['runs'].append(run)
                    write_json(execution_file, execution)
                    break
        if sha(binary) != config['binary_sha256']:
            raise SystemExit('Binary changed during experiment')
        execution['finished'] = now()
        write_json(execution_file, execution)
        result = json.loads(args.output.read_text()) if args.output.exists() else {}
        for row in rows:
            name = row['name']
            entry = select([r for r in execution['runs'] if r['name'] == name], host)
            entry.update(registered_name=row['registered_names'][host], binary_sha256=config['binary_sha256'],
                         registration=registrations[row['registered_names'][host]],
                         raw_directory=os.path.relpath(out, args.output.parent),
                         verification={'status': 'not-run', 'note': 'Speed is not a correctness test'})
            sanity_file = out / 'sanity.json'
            if sanity_file.exists():
                sanity = json.loads(sanity_file.read_text())
                if sanity['binary_sha256'] == config['binary_sha256'] and name in sanity['hashes']:
                    checked = sanity['hashes'][name]
                    if sha(out / checked['raw_file']) != checked['raw_sha256']:
                        raise SystemExit('Sanity raw output changed')
                    entry['verification'] = checked
            result.setdefault(name, {})[host] = entry
        result.setdefault('meta', {}).setdefault('hosts', {})[host] = dict(config=config, build=build_info,
            started=execution['started'], finished=execution['finished'], excluded_overlap_runs=len(execution['excluded_runs']))
        result['meta']['protocol'] = 'Fixed 262144-byte alignment Average; small 1–31-byte Average; Xeon best of two independently, M2 independent median of three; GiB/s assumes 3.5 GHz.'
        write_json(args.output, result)
        print('Wrote', args.output.name, flush=True)


if __name__ == '__main__':
    main()
