# Chart registration map

`manifest.json` is the machine-readable version. "Upstream" below means present at the pinned fork base; scratch additions and ARM adapter changes are supplied in patches. All rows use their original output variant.

| Chart row | Xeon registration | M2 registration | Source | Origin |
|---|---|---|---|---|
| city | `CityHash-64` | `CityHash-64` | `hashes/cityhash.cpp` | Upstream |
| farm | `FarmHash-64.NA` | `FarmHash-64.NA` | `hashes/farmhash.cpp` | Upstream |
| murmur | `MurmurHash3-128` | `MurmurHash3-128` | `hashes/murmurhash3.cpp` | Upstream |
| mx3 | `mx3.v3` | `mx3.v3` | `hashes/mx3.cpp` | Upstream |
| fasthash-64 | `fasthash-64` | `fasthash-64` | `hashes/fasthash.cpp` | Upstream |
| fasthash-32 | `fasthash-32` | `fasthash-32` | `hashes/fasthash.cpp` | Upstream |
| muse | `MuseAir` | `MuseAir` | `hashes/museair.cpp` | Upstream |
| muse-v2 | `MuseAir-v2` | `MuseAir-v2` | `hashes/museair_v2.cpp` | Scratch |
| komi | `komihash` | `komihash` | `hashes/komihash.cpp` | Upstream |
| t1ha | `t1ha2-64` | `t1ha2-64` | `hashes/t1ha.cpp` | Upstream |
| a5 | `a5hash` | `a5hash` | `hashes/a5hash.cpp` | Upstream |
| a5wide | `a5hash-128` | `a5hash-128` | `hashes/a5hash.cpp` | Upstream |
| rapid3 | `rapidhash` | `rapidhash` | `hashes/rapidhash.cpp` | Upstream |
| foldhash-fast | `foldhash-fast` | `foldhash-fast` | `hashes/foldhash.cpp` | Scratch C++ Rust port |
| foldhash-quality | `foldhash-quality` | `foldhash-quality` | `hashes/foldhash.cpp` | Scratch C++ Rust port |
| mum | `mum3.exact.unroll3` | `mum3.exact.unroll3` | `hashes/mum_mir.cpp` | Upstream |
| mir | `mir.exact` | `mir.exact` | `hashes/mum_mir.cpp` | Upstream |
| xxh3-64 | `XXH3-64` | `XXH3-64` | `hashes/xxhash.cpp` | Upstream |
| xxh3-128 | `XXH3-128` | `XXH3-128` | `hashes/xxhash.cpp` | Upstream |
| highway | `HighwayHash-64` | `HighwayHash-64` | `hashes/highwayhash.cpp` | Upstream |
| spooky | `SpookyHash2-64` | `SpookyHash2-64` | `hashes/spookyhash.cpp` | Upstream |
| pengyhash | `pengyhash` | `pengyhash` | `hashes/pengyhash.cpp` | Upstream |
| nmhash32 | `NMHASH` | `NMHASH` | `hashes/nmhash.cpp` | Upstream |
| nmhash32x | `NMHASHX` | `NMHASHX` | `hashes/nmhash.cpp` | Upstream |
| gx | `gxhash-64` | `gxhash-64` | `hashes/gxhash.cpp` | Upstream |
| ahash | `rust-ahash` | `rust-ahash` | `hashes/rust-ahash.cpp` | Upstream C++ Rust port |
| siphash-1-3 | `SipHash-1-3` | `SipHash-1-3` | `hashes/siphash.cpp` | Upstream |
| siphash-2-4 | `SipHash-2-4` | `SipHash-2-4` | `hashes/siphash.cpp` | Upstream |
| halftime24 | `HalftimeHash24-shipped` | `HalftimeHash24-shipped` | `hashes/halftimeshipped.cpp` | Scratch |
| go-maphash | `GoMapHash` | `GoMapHash` | `hashes/newhashes.cpp` | Scratch |
| abseil-hash | `AbseilHash-default` | `AbseilHash-default` | `hashes/newhashes.cpp` | Scratch |
| dotnet-marvin | `Marvin32` | `Marvin32` | `hashes/newhashes.cpp` | Scratch |
| polymur | `polymurhash` | `polymurhash` | `hashes/polymur.cpp` | Upstream |
| poly1305 | `poly1305-hash` | `poly1305-hash` | `hashes/classic_openssl.cpp` | Scratch |
| ghash | `ghash` | `ghash` | `hashes/classic_openssl.cpp` | Scratch |
| umash | `UMASH-64` | `UMASH-64` | `hashes/umash.cpp` | Upstream x86; scratch native ARM adapter |
| umash128 | `UMASH-128` | `UMASH-128` | `hashes/umash.cpp` | Upstream x86; scratch native ARM adapter |
| clhash | `CLhash` | `CLhash` | `hashes/clhash.cpp` | Upstream x86; scratch native ARM adapter |
| chain-v3 | `chainhash-v3` | `chainhash-v3` | `hashes/chainhash_v3.cpp` | Scratch |
| chain256 | `chainhash-256` | `chainhash-256` | `hashes/chainhash.cpp` | Scratch |
| halftime24-fixed | `HalftimeHash24-fixed` | `HalftimeHash24-fixed` | `hashes/halftimefixed.cpp` | Scratch |
| chain-v2 | `chainhash-x86` | `chainhash-adjacent-1k` | `hashes/chainhash_x86.cpp` | Scratch |
| chain128 | `chainhash-128` | `chainhash-128` | `hashes/chainhash_128.cpp` | Scratch |

The v2 M2 source is `hashes/chainhash_smhasher3_adjacent1024.cpp` with `chainhash_arm.h`; the Xeon source is `chainhash_x86.cpp`. The untimed/null rows in the reference extract have no mapping and stay unavailable. No wyhash/rapidhash version is substituted for a differently versioned row.
