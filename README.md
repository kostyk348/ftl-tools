# ftl-tools — распаковка и упаковка FTL `ftl.dat` (PKG-формат, Steam)

Формат полностью раскрыт из [Slipstream Mod Manager](https://github.com/Vhati/Slipstream-Mod-Manager) (`PkgPack.java`).
Игровые данные (XML: `blueprints.xml`, `events_*.xml`, `img/`, `audio/`) лежат **открыто** внутри архива.

## Формат

```
"PKG\n"                 4 байта подпись
u16 BE headerSize = 16
u16 BE entrySize  = 20
u32 BE entryCount
u32 BE pathsRegionSize
entries[entryCount]     по 20 байт:
    u32 BE innerPathHash
    u32 BE pathOffset | flags      (pathOffset = & 0x00FFFFFF; flags: 1<<24 = deflated)
    u32 BE dataOffset
    u32 BE dataSize
    u32 BE unpackedSize
paths region            строки путей, \0-терминированные
data region             данные файлов (zlib, если flags)
```

hash(path) = rotl32(hash, 27) ^ ord(lower(c)) — `pack_pkg.path_hash`
(проверено: 3219/3219 хешей совпадают с оригиналом).

## Использование

```bash
# распаковать (3219 файлов за ~1 сек)
python3 unpack_pkg.py "/path/FTL Faster Than Light/data/ftl.dat" ./ftl_unpacked

# править данные игры
$EDITOR ftl_unpacked/data/blueprints.xml

# запаковать обратно
python3 pack_pkg.py ./ftl_unpacked ./ftl_new.dat
cp ./ftl_new.dat "/path/FTL Faster Than Light/data/ftl.dat"
```

## Быстрый мод без repack (in-place patch)

Если значение меняется на ту же длину — можно патчить архив напрямую:
найти `dataOffset` нужного файла и записать байт по `dataOffset + смещение_в_XML`.
Пример: `LASER_BURST_3` damage `1` → `3` (см. историю сессии).

## Итоги разбора

- 3219 записей, 119 XML данных игры.
- `blueprints.xml` — оружие/корабли/дроны/системы (баланс).
- `events_*.xml` — события (квесты, бои, торговцы).
- Данные не шифрованы (только флаг zlib для части файлов).
