# Xeon timing comparison

A clean public clone, the final eight common patches, and a GCC 11.5.0 Release
build completed on the Xeon Platinum 8375C. **All 10 bulk results meet ±5%
(maximum difference 3.20%); 19/20 metrics meet ±5%.** The sole exception is
rapidhash small keys, 26.12 versus 27.58 cycles/hash (−5.29%). The strict overall
check therefore returns failure. No value was rescaled, replaced or retried to
make it fit the tolerance.

Tolerance: ±5.0%. All differences are relative to the frozen published chart cells. No rescaling or outlier removal.

| Hash | Metric | Recorded | Reproduced | Difference | Within tolerance |
|---|---|---:|---:|---:|---|
| rapidhash | bulk_bytes_per_cycle | 10.67 | 10.74 | +0.66% | yes |
| rapidhash | small_cycles | 27.58 | 26.12 | -5.29% | NO |
| XXH3-64 | bulk_bytes_per_cycle | 19.69 | 19.89 | +1.02% | yes |
| XXH3-64 | small_cycles | 30.16 | 29.38 | -2.59% | yes |
| komihash | bulk_bytes_per_cycle | 7.35 | 7.37 | +0.27% | yes |
| komihash | small_cycles | 27.49 | 26.18 | -4.77% | yes |
| control-256 | bulk_bytes_per_cycle | 14.42 | 14.35 | -0.49% | yes |
| control-256 | small_cycles | 103.90 | 103.25 | -0.63% | yes |
| chainhash | bulk_bytes_per_cycle | 28.31 | 28.27 | -0.14% | yes |
| chainhash | small_cycles | 155.14 | 155.14 | +0.00% | yes |
| control-128 | bulk_bytes_per_cycle | 8.16 | 8.13 | -0.37% | yes |
| control-128 | small_cycles | 165.06 | 164.11 | -0.58% | yes |
| HalftimeHash24-shipped | bulk_bytes_per_cycle | 12.81 | 13.22 | +3.20% | yes |
| HalftimeHash24-shipped | small_cycles | 64.91 | 66.05 | +1.76% | yes |
| MuseAir-v2 | bulk_bytes_per_cycle | 7.53 | 7.51 | -0.27% | yes |
| MuseAir-v2 | small_cycles | 29.27 | 28.20 | -3.66% | yes |
| foldhash-fast | bulk_bytes_per_cycle | 9.07 | 9.06 | -0.11% | yes |
| foldhash-fast | small_cycles | 20.09 | 19.74 | -1.74% | yes |
| GoMapHash | bulk_bytes_per_cycle | 17.66 | 17.68 | +0.11% | yes |
| GoMapHash | small_cycles | 64.32 | 63.37 | -1.48% | yes |

Result: FAIL.

Registration names in the raw logs under `out/` and in `speeds.json` are those
printed at run time; this table, `diff.json` and `validation.json` use the
current names.

## Execution and evidence

The final experiment ran from `2026-09-19T07:58:54.639276+00:00` to `2026-09-19T08:20:29.321709+00:00`. It used exactly
20 accepted Speed invocations in two complete serial passes, with **zero
overlap exclusions**. Every invocation was prefixed with `taskset -c 32-39`;
the monitor also checked SMT siblings 80–87. Other jobs pinned elsewhere on
the host were allowed to continue. All 20 raw-file hashes, parsed metrics and
independent selections were checked after transfer.

Binary SHA-256: `a68b4ec78d08d3daeee4504436f297626d5ad5e59cdae8511ee7dc58b28be607`.

The commands used on `<xeon-host>` were:

```sh
python3 scripts/build.py --jobs 8
python3 scripts/sanity.py --host Xeon8375C --cpus 32-39
python3 scripts/benchmark.py --host Xeon8375C --subset --cpus 32-39 --skip-build
```

`make verify-xeon` runs this pipeline and the strict comparison.

[Collected timings](speeds.json), [machine-readable diff](diff.json),
[execution log](out/Xeon8375C/execution.json),
[hardware](out/Xeon8375C/hardware.json),
[build identity](out/Xeon8375C/build.json), and
[source file hashes](out/Xeon8375C/source-sha256.json) accompany every raw run.
The `raw_directory` paths in the collected JSON resolve relative to that file.

All 43 registrations were checked for native Sanity in the final Xeon binary.
Four report failures: foldhash-fast and foldhash-quality (sanity check 2),
HalftimeHash24-shipped (append zeroes), and Marvin32 (prepend zeroes). The logs
and [Sanity summary](out/Xeon8375C/sanity.json) preserve them. Timing these
implementations does not assert that they pass correctness/quality checks.

The archived and rebuilt SpeedTest, rapidhash, XXH3, komihash and control-256
object `.text` sections are byte-identical; see
[instruction comparison](instruction-comparison.json). This rules out changed
pre-link instruction bytes in those sections, but does not establish the cause
of the rapidhash small-key difference. Final link layout, runtime environment
and overhead calibration can affect small-key measurements. We did not alter
the two-pass rule or run extra trials to select a closer number.

The same patched repository also built on M2 with all 43 manifest
registrations present; see its [build identity](out/M2Pro/build.json) and
[check](out/M2Pro/check.json). That build carried one further arm64
build-system patch, since dropped because the registration list does not
depend on it.
No full M2 timing rerun was performed for this delivery.

`make chart-data SPEEDS=verification/speeds.json` updated exactly 20 speed cells.
A second merge into a copy of the complete post JSON changed only those same
20 Xeon cells; every other field was identical. Five protocol/merge unit tests
pass. [Validation summary](validation.json) records these checks.
