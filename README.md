# Reproduce the hash benchmark chart

Build the recorded SMHasher3 implementations and measure the 41 timed rows in
*Adversarial examples for fast hash functions*. This repository contains source
patches, a serial timing runner, the published speed cells for comparison, and a
chart-data merger. It needs no original scratch directories or cached binaries.
No upload or publication is performed.

## Run

Requirements: Git, Python 3.9+, CMake 3.16+, Make, a GCC/Clang C/C++ compiler,
and OpenSSL 3 development headers and libraries. Linux also needs `taskset`
(util-linux). The supported profiles are little-endian Linux x86-64 and macOS
arm64. Use the original Intel Xeon Platinum 8375C and Apple M2 Pro for numerical
comparison. Other CPUs can execute the profiles but are not equivalent hardware.
The runtime ports require AES/CLMUL or ARM crypto support. Rust and Go toolchains
are unnecessary: these measurements use C/C++ ports.

On macOS, install the command-line developer tools and, with Homebrew:

```sh
brew install cmake openssl@3
python3 scripts/benchmark.py --host M2Pro
```

On the Xeon, with GCC 11 and OpenSSL 3 development packages installed:

```sh
python3 scripts/benchmark.py --host Xeon8375C --cpus 32-39
```

Each command clones the source, checks out the pin, applies `patches/series`,
builds a Release binary, runs every manifest entry, and writes `speeds.json`.
`make benchmark` auto-selects the host profile. `make reproduce` also merges
the resulting timings into the included chart extract in one command. `--jobs 8` controls compilation
only. Measurements always use one process at a time. A full run takes hours;
the M2 load gate may extend that indefinitely.

For the preselected nine-hash verification panel, including scratch registrations:

```sh
make verify-xeon CPUS=32-39
```

This builds, records native Sanity outcomes, runs two complete passes and compares both metrics with the frozen chart,
exiting nonzero if any difference exceeds ±5%. The panel is rapidhash, XXH3-64,
komihash, ChainHash, ChainHash-128, HalftimeHash24 shipped, MuseAir v2,
foldhash-fast, and GoMapHash. Entries execute in manifest order, in complete passes, rather
than running a hash's repetitions consecutively.

To copy this checkout to the measurement host, for example:

```sh
rsync -az --exclude=.git --exclude=.work --exclude=out ./ '<xeon-host>:hash-benchmark-reproduction/'
ssh '<xeon-host>' 'cd hash-benchmark-reproduction && make verify-xeon CPUS=32-39'
```

A smaller custom experiment accepts manifest names or chart row IDs:

```sh
python3 scripts/benchmark.py --host Xeon8375C --names XXH3-64 chainhash --out out/custom --output custom-speeds.json
```

`--out` controls raw evidence; `--output` controls the collected JSON. Repeating
the same command resumes only with an identical configuration and binary hash,
and verifies the saved raw-file hashes. Completed timings are never silently
repeated. Use a new output directory for a new experiment. `--skip-build` uses
an existing build. Changing patches requires moving `.work` aside and rebuilding;
source drift is rejected. `OPENSSL_ROOT_DIR` can select a nonstandard OpenSSL
installation. Keep the same library version when comparing its two proxy hashes.

## Chart data

```sh
make chart-data
# Merge both independently measured hosts into the actual post:
make chart-data DATA=path/to/post/data.json SPEEDS='m2-speeds.json xeon-speeds.json' OUTPUT=updated-data.json
```

The default input, `reference/data.json`, is a **speed-cell extract**, containing
row IDs, names and the original SMHasher3 cells, not the complete article. Pass
the post's full `data.json` to preserve all its other content. Only completed,
matching manifest cells are replaced. Collision claims, proof fields, unrelated
metrics, unavailable rows, and unmeasured host cells are preserved. New cells
carry the fresh selection, spread, binary identity and verification status;
old correctness metadata is not copied onto a new binary. Input speed files are
processed in order, with later files taking precedence for duplicate hash/host
entries. The merger does not substitute another hash for an unavailable version.

`speeds.json` follows the post's `hash → host → metrics/runs` schema, with
`bulk_bytes_per_cycle`, `bulk_gib_s`, `small_cycles`, selections and variation.
The manifest uses canonical registration names as keys; `row_id` maps these to
the article's names.

## Source and build identity

The exact base is commit `3de870c7ab449ad11cf450848d9270e3f54102d1` from
[the public author fork](https://gitlab.com/lobais/smhasher3/-/tree/3de870c7ab449ad11cf450848d9270e3f54102d1).
It adds a poly-mersenne default-block tuning commit to upstream `7ad8939d`.
The upstream GitHub mirror does not contain this fork commit. The pin alone
never identified the recorded dirty builds: the patches are also necessary.

The ordered patch set supplies:

1. `arm64` recognition in `platform/family.cmake`, enabling ARM backend detection.
2. foldhash, OpenSSL proxies, and native ARM UMASH/CLHASH adapters.
3. Go runtime memhash, Abseil and Marvin C/C++ ports, the captured Go key,
   and the archived architecture-specific Go/Abseil verification constants.
4. MuseAir v2, ported from crate 0.6.0.
5. HalftimeHash24 shipped and fixed headers and their distinct registrations.
6. ChainHash and ChainHash-128: the registration adapter and the two public
   headers, copied unchanged from the ChainHash repository.
7. Build integration and a 192-bit Speed/Sanity dispatch for fixed HalftimeHash24.
8. The Darwin RNG counter type correction (`size_t` to `uint64_t`).

The same eight patches build on x86-64 and on arm64; the registration list is
identical on both.

See [REGISTRATIONS.md](REGISTRATIONS.md) for every chart mapping and
[patches/sources.json](patches/sources.json) for source-snapshot hashes and
relative experiment labels. The latter labels document origin only; no script
reads those locations. aHash is the C++ Rust port already present at the pin,
not another added patch or a new Rust binary. foldhash is the added Rust-to-C++
port. Default upstream hashes retain the pinned implementation.

Release uses SMHasher3's native CPU optimization (`-O3 -march=native`, its
existing diagnostic/debug flags, and `-DNDEBUG`). Harness and ordinary hash
objects remain C++11. Go/Abseil/Marvin, MuseAir v2, and HalftimeHash24 translation
units use C++17, matching their scratch builds; shipped HalftimeHash24 additionally
uses `-fwrapv`. Apple compilation enables AES explicitly and permits the existing
Halftime vector conversions. ARM vendor C files use C11 and
`-march=armv8-a+crypto`. Runtime little-endian detection is configured explicitly
to avoid the missing `TestEndianess.c.in` issue seen with CMake 4. Build logs,
compiler identity/flags, a complete source SHA-256 manifest and the binary hash
are saved under `.work/`.

This is one combined clean build of the archived registrations. The article
used several separately linked scratch binaries and sometimes reused existing
objects. Layout and toolchain changes can move timings, particularly small-key
costs. The reproduction does not promise identical binary bytes.

## Timing protocol

Every invocation is `SMHasher3 REGISTERED_NAME --test=Speed`, with no seed,
trial-count, buffer-size, frequency, or hash-loop overrides. The upstream
`tests/SpeedTest.cpp` and timer implementations are unchanged. The harness's
own warmups, repeated trials and internal filtering remain in effect. At this
pin the normal bulk path uses 1920 trials per timing and 80 runs per alignment;
small inputs use 600 timings of 15000 repeated hashes each. Slow/very-slow hash
flags reduce bulk trials and repetitions as upstream specifies. The harness
subtracts measured `donothing-32` call overhead before its own filtering, uses
its deterministic `Rand(164200)` seed selection and `Rand(256765, callcount)`
input generation, and runs small tests before the two bulk sections.

* **Bulk:** the printed Average of eight alignments, 7 through 0, of exactly
  262144-byte keys. This is an arithmetic mean of the reported alignment speeds.
  The additional varying-length `[262017,262144]` section is saved but not selected.
* **Small:** the printed arithmetic Average over lengths 1–31 bytes. The extra
  varying-small-length measurement is likewise not used.
* **Xeon:** two complete serial passes. Higher bulk B/cycle wins; rounded ties
  use higher reported GiB/s, then the earlier pass. GiB/s comes from that same
  pass. Lower small cycles/hash wins independently, with earlier-pass ties.
* **M2:** three complete serial passes. Bulk and small are independently the
  middle observations in ascending order; ties retain run order. GiB/s comes
  from the selected bulk observation. All three accepted observations remain
  in the JSON, including calibration outliers.
* **M2 gate:** before preparation and each timing start, require no other
  SMHasher3 process and one-minute load strictly below 4.5. Poll every 60 seconds
  with no timeout bypass. No timing affinity or priority adjustment is applied.
* **Xeon affinity:** `taskset -c 32-39` by default, configurable with `--cpus`.
  This allows scheduling within that set; it does not run eight hash workers.
  The gate waits for other SMHasher3 processes whose affinity intersects these
  CPUs or their SMT siblings. Jobs pinned elsewhere are recorded by the machine's
  load but do not block the gate. No governor or priority changes are made.
* **Overlap:** every five seconds the runner samples load and relevant SMHasher3
  PIDs. A sampled overlapping run is archived with its metrics and retried; it
  is never counted among the two/three accepted runs. Sampling cannot detect
  every short overlap. Other programs' load is not excluded. A gate establishes
  only the start condition, not sustained quiet execution.
* **Variation:** report `100 × (max/min − 1)` for both metrics and each observation's
  deviation from the median. Flag Xeon spreads above 15% and M2 observations
  more than 15% from their median. Flags do not delete observations, trigger
  performance-based retries, or modify the selected values.

The original Xeon uses RDTSC/RDTSCP **TSC ticks**. M2 uses a per-process calibrated
monotonic-clock cycle estimate. Neither column should be interpreted as directly
comparable physical core cycles. The printed GiB/s assumes **3.5 GHz** on both
hosts; it is a conversion of B/cycle, not measured wall-clock throughput. No
frequency normalization or wall-clock replacement is applied here. Start/end
load, raw text, per-run hashes and selected pass numbers are retained in `out/`.
The Speed trailer's `0x00000001` is not an implementation verification code.

## Historical M2 calibration and protocol differences

The chart is an accumulation of experiments, not one uniform original run.
Its older corrected M2 panel used best-of-two after an initial load gate below
3.0, with a three-hour timeout; load later rose substantially. Selected unstable
rows were then measured three more times, and the chart used the median of all
five observations. The retiming gate was relaxed to 4.5. In some of those early
runs one pass reported a bulk figure two to three times higher than its
companion pass, with the small-key cost moving inversely. That correlated
change is consistent with a calibration/frequency-scheduling artefact, not a
corresponding change in hashing throughput. The calibration multiplier was not
printed, so its exact cause cannot be reconstructed from the logs.

Newer additions used the three-run M2 median rule. Fixed HalftimeHash24 originally
used medians of three on **both** hosts. Earlier Xeon jobs also used different
single-core affinities or no affinity. This repository deliberately implements
the requested consistent fresh protocol (Xeon two passes, M2 three), while
comparing against the **actual published values**, not recalculating the old
chart to make agreement easier. In particular, M2 ±5% agreement is not assured.
The frozen reference cells retain their original record citations. They are
comparison data and are never passed to the timing runner as observations.

## Seed adapters and implementation scope

SMHasher3 calls its seed-expansion hook before entering the timed loops. A
64-bit seed expanded into many words still describes at most 2^64 keys; these
measurements do not establish the ideal independent-key hypotheses used by
collision verifiers or transfer collision bounds to the seeded subfamily.

| Registration | Adapter / timed scope |
|---|---|
| ChainHash | The header's own `chainhash_key_from_seed`: SplitMix64 outputs become the 64 key bytes, outside timing; 256-byte blocks, Horner chain over GF(2^64), run-time dispatch of the PCLMUL/VPCLMUL or PMULL path. |
| ChainHash-128 | `chainhash128_key_from_seed`: SplitMix64 outputs become the 128 key bytes, outside timing; 512-byte blocks, Horner chain over GF(2^128). |
| HalftimeHash24 | SplitMix seeds the four-word generator, then ten warmup rounds and 9000 entropy words, outside timing. Both use `advanced::V4<3>`. Shipped computes three words and copies the first eight bytes into a 64-bit registration; fixed returns all 24 bytes through the added 192-bit dispatch. |
| GoMapHash | Direct map seed, one captured 128-byte random process AES key in `go_key.inc`, identical across hosts and installed outside timing. This is the runtime byte-string `memhash` C++ intrinsic port, not Go assembly, integer-key hashing or the long-input `hash/maphash.Bytes` chaining API. |
| AbseilHash-default | Direct seed and byte-string port pinned to `73d2688300440c8af028eec865ee0dcd85e93025`: default scalar multiply on Xeon, native ARM crypto on M2, CRC strategy disabled. It is separate from upstream SMHasher3's older Abseil registrations. |
| Marvin32 | Direct seed (`p0=lo32`, `p1=hi32`), raw bytes, .NET 10.0.12 port. UTF-16 encoding is not timed. |
| MuseAir-v2 | Direct 64-bit seed, standard 64-bit one-shot hash from crate 0.6.0; not bfast or 128-bit. |
| foldhash-fast/quality | Per-hasher seed S and `SharedSeed::from_u64(S)`; shared expansion outside timing. Matches the Rust algorithm, compiled as C++. |
| rust-ahash | Pinned upstream C++ port: four state words are PI2 constants XOR seed, set up outside timing. Native shared AES backend. |
| CLhash | xorshift128plus key generation seeded with `(S, ~S)` outside timing. M2 uses vendor PMULL; Xeon keeps upstream CLMUL. |
| UMASH | Pinned fixed parameter initialization plus per-call seed; reseed registrations also exist but are not chart substitutes. M2 uses vendor PMULL. |
| poly1305-hash | SplitMix seed expansion, clamping, key setup, EVP processing and finalization inside the timed call. |
| ghash | Inherited fixed-IV OpenSSL GMAC proxy, including AES-128 key setup and the seed-dependent tag mask; not bare GHASH. |

ARM UMASH preserves the scratch second-fingerprint-accumulator fixup for inputs
at least 1024 bytes; swapped UMASH disables the long-input optimization. CLHASH
preserves the original wrapper's swapped-tail convention. Inherited `hwclmul`
labels on M2 execute PMULL. Shipped HalftimeHash24 has a broken upstream NEON
dispatch, so its unmodified header deliberately uses the scalar fallback on ARM;
the fixed header enables the repaired native implementation.

Speed is not a correctness suite. Historical scalar M2 NMHASH/NMHASHX verification
codes differ from registered constants; Marvin's direct zero seed fails the
prepend-zeroes Sanity check. In this combined Xeon build, both foldhash
registrations fail sanity check 2 and shipped HalftimeHash24 fails append-zeroes.
HalftimeHash24 wrappers have unspecified (zero) verification constants. These facts are not repaired or hidden by timing.
Consult the separate collision verifiers and source-specific validation records
for mathematical and native equivalence checks.

## Checks and evidence

`make test` checks raw-output parsing (including rejection of partial outputs),
the independent selection rules, outlier retention, and preservation of other
chart content. After a build, `python3 scripts/sanity.py --host Xeon8375C`
records every chart registration's native Sanity result. It retains failures
as observations and does not abort or remap seeds; it is not a pass/fail CI gate.
A later timing run picks up those results only when the binary and raw hashes match. `make compare` reports signed differences in both metrics and
fails outside ±5%. See [verification/REPORT.md](verification/REPORT.md) for a
clean-build Xeon run of ten hashes (eight panel members and two control
constructions) with raw evidence. All ten bulk results met ±5%
(maximum difference 3.20%); 19/20 metrics met ±5%. Rapidhash small keys was
5.29% lower, so the archived strict comparison exits nonzero. Compilation
and registration availability are also checked on the M2; a full M2 timing run
is not part of this delivery's end-to-end Xeon check.

The optional `scripts/compare_elf_text.py ORIGINAL_BUILD REPRODUCTION_BUILD`
audit compares pre-link `.text` sections of SpeedTest and three original control
objects with an archived Xeon build. Its saved output is
`verification/instruction-comparison.json`. Equality excludes a changed
instruction section for those objects; it does not assert identical final
link layout, relocations, data sections, or performance.

The reproduction scripts are GPL-3.0-or-later; see [LICENSE](LICENSE). Patches
retain the licenses/notices of their underlying files. Supplemental Go, Abseil,
.NET, foldhash and wrapper license texts are in `licenses/`. Vendored UMASH and
CLHASH licenses are included in their patch. No prebuilt executable is distributed.
