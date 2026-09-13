#!/usr/bin/env python3
"""Распаковщик FTL PKG-архива (Steam-версия, ftl.dat).
Формат раскрыт из Slipstream Mod Manager (PkgPack.java):
  "PKG\n" | u16BE headerSize=16 | u16BE entrySize=20 | u32BE entryCount
  | u32BE pathsRegionSize | entries[20] | paths region | data region
  entry: u32BE innerPathHash | u32BE pathOffset|flags | u32BE dataOffset
         | u32BE dataSize | u32BE unpackedSize   (flags: 1<<24 = deflated)
"""
import struct, sys, os, zlib

def unpack(path, outdir):
    with open(path, 'rb') as f:
        sig = f.read(4)
        assert sig == b'PKG\n', f"не PKG: {sig!r}"
        header_size, entry_size = struct.unpack('>HH', f.read(4))
        assert header_size == 16 and entry_size == 20, (header_size, entry_size)
        entry_count, paths_size = struct.unpack('>II', f.read(8))
        print(f"entries={entry_count} paths_region={paths_size}")
        entries = []
        for _ in range(entry_count):
            h, pflags, doff, dsize, usize = struct.unpack('>IIIII', f.read(20))
            entries.append((pflags & 0x00FFFFFF, bool(pflags & (1 << 24)), doff, dsize, usize))
        paths = f.read(paths_size)

        def get_path(off):
            end = paths.find(b'\x00', off)
            return paths[off:end].decode('utf-8', 'replace') if end >= 0 else ''

        os.makedirs(outdir, exist_ok=True)
        n = 0
        for poff, deflated, doff, dsize, usize in entries:
            if doff == 0:
                continue
            name = get_path(poff)
            if not name:
                continue
            f.seek(doff)
            data = f.read(dsize)
            if deflated:
                try:
                    data = zlib.decompress(data)
                except Exception as e:
                    print(f"  ! inflate {name}: {e}")
                    continue
            target = os.path.join(outdir, name.lstrip('/'))
            os.makedirs(os.path.dirname(target), exist_ok=True)
            with open(target, 'wb') as g:
                g.write(data)
            n += 1
        print(f"извлечено: {n}")

if __name__ == '__main__':
    unpack(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'ftl_unpacked')
