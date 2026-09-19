# Third-party notices

The aggregate SMHasher3 build is distributed under GPL-3.0-or-later (root
LICENSE). Individual source notices remain applicable, and are retained in
patches. This repository distributes source, not OpenSSL or any compiled binary.

* Go memhash port: derived from Go go1.27.1, copyright The Go Authors,
  BSD 3-Clause (`Go-BSD-3-Clause.txt`).
* Abseil port: derived from abseil-cpp 73d2688, copyright The Abseil Authors,
  Apache 2.0 (`Abseil-Apache-2.0.txt`).
* Marvin port: derived from .NET runtime v10.0.12, copyright .NET Foundation
  and Contributors, MIT (`dotnet-MIT.txt`).
* foldhash port: copyright Orson Peters, Zlib (`foldhash-Zlib.txt`). The file's
  own notice identifies it as a port and describes the changed seed adapter.
* ChainHash headers and original benchmark wrappers: MIT
  (`Wrappers-MIT.txt` and source notices).
* MuseAir's original algorithm is CC0; its supplied C port carries an MIT
  notice. HalftimeHash carries its original MIT notice inside each header.
* Native ARM UMASH is MIT; native ARM CLHASH is Apache 2.0. Their complete
  LICENSE files are included in patch 0002, together with the original wrapper
  notices (including CLHASH's GPL-3.0-or-later wrapper).

The remaining upstream notices and licenses are fetched with the pinned
SMHasher3 source. Supplemental Go and .NET license texts are taken from the
exact upstream versions named above; Abseil and foldhash license texts come
from the archived source snapshots used for these ports.
