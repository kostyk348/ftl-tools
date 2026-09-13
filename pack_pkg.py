#!/usr/bin/env python3
"""Упаковщик FTL PKG-архива (Steam ftl.dat).
Формат: "PKG\n" | u16BE 16 | u16BE 20 | u32BE entryCount | u32BE pathsSize
        | entries[20] | paths | data
entry: u32BE hash | u32BE pathOff|flags | u32BE dataOff | u32BE dataSize | u32BE unpackedSize
hash(path) = rotl32(hash,27) ^ ord(lower(c))   (см. PkgPack.calculatePathHash)
"""
import struct, sys, os

MASK = 0xFFFFFFFF

def path_hash(p: str) -> int:
    h = 0
    for ch in p:
        n = ord(ch.lower())
        h = ((h << 27) | (h >> 5)) & MASK
        h = (h ^ n) & MASK
    return h

def pack(src_dir, out_path, deflate=False):
    files = []
    for root, _, names in os.walk(src_dir):
        for n in sorted(names):
            full = os.path.join(root, n)
            rel = os.path.relpath(full, src_dir).replace(os.sep, '/')
            files.append((rel, full))
    files.sort()
    n = len(files)

    # paths region
    paths = bytearray()
    offs = {}
    for rel, _ in files:
        offs[rel] = len(paths)
        paths += rel.encode('utf-8') + b'\x00'

    data_region = bytearray()
    entries = []
    for rel, full in files:
        with open(full, 'rb') as f:
            raw = f.read()
        payload = raw
        flags = 0
        if deflate:
            import zlib
            comp = zlib.compress(raw)
            if len(comp) < len(raw):
                payload = comp
                flags = 1 << 24
        data_off = 16 + 20 * n + len(paths) + len(data_region)
        data_region += payload
        entries.append((path_hash(rel), offs[rel] | flags, data_off, len(payload), len(raw)))

    with open(out_path, 'wb') as f:
        f.write(b'PKG\n')
        f.write(struct.pack('>HH', 16, 20))
        f.write(struct.pack('>II', n, len(paths)))
        for e in entries:
            f.write(struct.pack('>IIIII', *e))
        f.write(bytes(paths))
        f.write(bytes(data_region))
    print(f"упаковано {n} файлов -> {out_path} ({os.path.getsize(out_path)} байт)")

if __name__ == '__main__':
    pack(sys.argv[1], sys.argv[2])
