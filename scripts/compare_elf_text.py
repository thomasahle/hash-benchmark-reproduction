#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""Optional audit of pre-link instruction sections against an archived ELF build."""
import argparse
import hashlib
import json
import pathlib
import struct

OBJECTS = [('SMHasher3Tests', 'tests/SpeedTest.cpp.o'),
           ('SMHasher3Hashlib', 'hashes/rapidhash.cpp.o'),
           ('SMHasher3Hashlib', 'hashes/xxhash.cpp.o'),
           ('SMHasher3Hashlib', 'hashes/komihash.cpp.o')]


def section(path, name):
    data = path.read_bytes()
    if data[:6] != b'\x7fELF\x02\x01':
        raise ValueError('Expected a little-endian ELF64 object')
    offset = struct.unpack_from('<Q', data, 40)[0]
    size, count, strings_index = struct.unpack_from('<HHH', data, 58)
    headers = [struct.unpack_from('<IIQQQQIIQQ', data, offset + i * size) for i in range(count)]
    header = headers[strings_index]
    strings = data[header[4]:header[4] + header[5]]
    for header in headers:
        found = strings[header[0]:].split(b'\0', 1)[0].decode()
        if found == name:
            return data[header[4]:header[4] + header[5]]
    raise ValueError('Missing section: ' + name)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('original_build', type=pathlib.Path)
    ap.add_argument('reproduction_build', type=pathlib.Path)
    args = ap.parse_args()
    result = {}
    for library, obj in OBJECTS:
        relative = pathlib.Path('CMakeFiles') / (library + '.dir') / obj
        a = section(args.original_build / relative, '.text')
        b = section(args.reproduction_build / relative, '.text')
        result[obj] = dict(original_text_sha256=hashlib.sha256(a).hexdigest(),
                          reproduction_text_sha256=hashlib.sha256(b).hexdigest(),
                          identical_instruction_section=a == b, original_bytes=len(a), reproduction_bytes=len(b))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
