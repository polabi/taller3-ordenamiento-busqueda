"""
Generador ÚNICO de los datos de prueba (se ejecuta una sola vez).

    cd python
    python3 -m taller3.generate_data            # genera data/ si no existe (y las claves si faltan)
    python3 -m taller3.generate_data --force    # regenera (sobrescribe)

Decisiones de diseño:
- Un solo generador para ambos lenguajes: Java NO genera datos, solo los lee.
  Así es imposible que Java y Python midan con conjuntos distintos.
- Semilla fija (config.SEED) con random.Random (Mersenne Twister), que es
  determinista entre versiones de Python 3 para semillas enteras.
- Se genera UNA secuencia de 1.000.000 de valores y cada tamaño menor es su
  prefijo (los 1.000 primeros, los 10.000 primeros, ...). Los conjuntos quedan
  anidados, lo que reduce la variación entre tamaños debida a los datos.
- Muestreo CON reemplazo: con 90.000.000 de valores posibles y n = 10^6 se
  esperan ~5.500 repetidos (paradoja del cumpleaños). Es lo correcto para
  "enteros aleatorios" y obliga a que los algoritmos manejen duplicados.
- Las versiones ascendente y descendente se derivan con sorted() de Python
  (Timsort), una implementación independiente que además sirve de oráculo para
  verificar los ordenamientos.
- data/manifest.json guarda la semilla, los SHA-256 y estadísticas de cada
  archivo, para demostrar que los datos no cambiaron entre ejecuciones.

Punto 2 (spec p2 6.1): data/claves_busqueda.txt, 1.000 claves (500 presentes, 500
ausentes) con su propia semilla (config.SEARCH_KEYS_SEED). Se generan solo si el archivo
no existe; si existe, solo se comprueba su SHA-256. El manifiesto se ACTUALIZA (se agrega
una entrada), nunca se reescribe: las entradas del Punto 1 quedan byte a byte iguales.
"""
from __future__ import annotations

import argparse
import json
import platform
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

from taller3 import config
from taller3.common.dataio import dataset_path, read_ints, search_keys_path, sha256_of, write_ints


def generate_values(seed: int, count: int) -> list[int]:
    rng = random.Random(seed)
    return [rng.randint(config.MIN_VALUE, config.MAX_VALUE) for _ in range(count)]


MANIFEST_NAME = "manifest.json"


def _load_manifest(data_dir: Path) -> dict:
    return json.loads((data_dir / MANIFEST_NAME).read_text(encoding="utf-8"))


def _save_manifest(data_dir: Path, manifest: dict) -> None:
    # Mismo formato con el que se escribió en el Punto 1 (indent=2, sin escapar tildes,
    # sin salto final): recargar y volver a guardar deja las entradas existentes iguales.
    (data_dir / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2, ensure_ascii=False),
                                          encoding="utf-8")


def _read_verified(data_dir: Path, manifest: dict, name: str, n: int) -> list[int]:
    """Lee un archivo de datos solo si su SHA-256 coincide con el manifiesto."""
    path = data_dir / name
    expected = manifest["archivos"][name]["sha256"]
    actual = sha256_of(path)
    if actual != expected:
        raise ValueError(f"{name}: SHA-256 {actual} no coincide con el manifiesto ({expected}); "
                         f"no se generan las claves")
    return read_ints(path, n)


def generate_search_keys(data_dir: Path = config.DATA_DIR) -> list[int]:
    """Genera data_dir/claves_busqueda.txt (spec p2 6.1.1) y agrega su entrada al manifiesto.

    El ORDEN de las llamadas al RNG es parte de la especificación: sample, randint en
    orden, shuffle. Cambiarlo (o muestrear de un set) cambia el SHA-256.
    Si algo no cuadra lanza ValueError ANTES de escribir nada.
    """
    manifest = _load_manifest(data_dir)
    n_big = max(config.SIZES)
    rng = random.Random(config.SEARCH_KEYS_SEED)
    pool = _read_verified(data_dir, manifest, "aleatoria_1000.txt", 1000)
    if len(set(pool)) != len(pool):
        raise ValueError("aleatoria_1000.txt tiene valores repetidos: las 500 presentes "
                         "no serían distintas (spec 6.1.2)")
    present = rng.sample(pool, config.NUM_PRESENT_KEYS)          # sobre la LISTA, en orden de archivo
    in_big = set(_read_verified(data_dir, manifest, f"aleatoria_{n_big}.txt", n_big))
    absent: list[int] = []
    seen: set[int] = set()
    while len(absent) < config.NUM_SEARCH_KEYS - config.NUM_PRESENT_KEYS:
        v = rng.randint(config.MIN_VALUE, config.MAX_VALUE)
        if v in in_big or v in seen:                              # rechazo
            continue
        seen.add(v)
        absent.append(v)
    keys = present + absent
    rng.shuffle(keys)                                             # D2: barajadas, mismo RNG

    path = search_keys_path(data_dir)
    write_ints(path, keys)
    manifest["archivos"][path.name] = {
        "n": config.NUM_SEARCH_KEYS,
        "variante": "claves_busqueda",
        "sha256": sha256_of(path),
        "semilla": config.SEARCH_KEYS_SEED,
        "presentes": config.NUM_PRESENT_KEYS,
        "ausentes": config.NUM_SEARCH_KEYS - config.NUM_PRESENT_KEYS,
        "origen_presentes": f"rng.sample(aleatoria_1000.txt, {config.NUM_PRESENT_KEYS})",
        "origen_ausentes": f"randint(MIN, MAX) con rechazo si está en aleatoria_{n_big}.txt o repetida",
        "orden": "presentes + ausentes, luego rng.shuffle",
        "python": sys.version.split()[0],
        "creado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    _save_manifest(data_dir, manifest)
    return keys


def check_search_keys(data_dir: Path = config.DATA_DIR) -> None:
    """ValueError si el SHA-256 de claves_busqueda.txt no coincide con el del manifiesto."""
    path = search_keys_path(data_dir)
    entry = _load_manifest(data_dir)["archivos"].get(path.name)
    if entry is None:
        raise ValueError(f"{path.name} existe pero no tiene entrada en {MANIFEST_NAME}")
    actual = sha256_of(path)
    if actual != entry["sha256"]:
        raise ValueError(f"{path.name}: SHA-256 {actual} no coincide con el manifiesto "
                         f"({entry['sha256']}); no lo edites a mano")


def generate_point1_data() -> None:
    """Datos del Punto 1 (sin cambios de comportamiento): reescribe data/ y el manifiesto."""
    max_n = max(config.SIZES)
    print(f"Generando {max_n:,} enteros de 8 dígitos con semilla {config.SEED} ...")
    base = generate_values(config.SEED, max_n)

    manifest = {
        "semilla": config.SEED,
        "generador": "random.Random(semilla).randint(MIN, MAX), muestreo con reemplazo",
        "rango": [config.MIN_VALUE, config.MAX_VALUE],
        "tamanos": list(config.SIZES),
        "tamanos_anidados": "cada tamaño es el prefijo de la secuencia de 1.000.000",
        "python": sys.version.split()[0],
        "plataforma": platform.platform(),
        "creado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "archivos": {},
    }

    for n in config.SIZES:
        aleatoria = base[:n]
        ascendente = sorted(aleatoria)
        descendente = ascendente[::-1]
        for variant, values in (("aleatoria", aleatoria),
                                ("ascendente", ascendente),
                                ("descendente", descendente)):
            path = dataset_path(variant, n)
            write_ints(path, values)
            manifest["archivos"][path.name] = {
                "n": n,
                "variante": variant,
                "sha256": sha256_of(path),
            }
        manifest["archivos"][f"aleatoria_{n}.txt"].update({
            "min": ascendente[0],
            "max": ascendente[-1],
            "valores_distintos": len(set(aleatoria)),
            "duplicados": n - len(set(aleatoria)),
        })
        print(f"  n={n:>9,}: 3 archivos escritos "
              f"(duplicados en la aleatoria: {n - len(set(aleatoria)):,})")

    manifest_path = config.DATA_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Listo. Manifiesto: {manifest_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera los datos de prueba del taller")
    parser.add_argument("--force", action="store_true",
                        help="sobrescribe los archivos si ya existen")
    args = parser.parse_args()

    # 1. Datos del Punto 1: si existen y no hay --force, NO se tocan (se sigue al paso 2).
    existing = [dataset_path(v, n) for n in config.SIZES for v in config.VARIANTS
                if dataset_path(v, n).exists()]
    if existing and not args.force:
        print(f"Los datos ya existen en {config.DATA_DIR} ({len(existing)} archivos).")
        print("Los datos se generan una sola vez; para regenerarlos hay que pasar --force.")
    else:
        generate_point1_data()

    # 2. Claves del Punto 2: se generan si faltan (o con --force); si existen, se verifican.
    keys_path = search_keys_path()
    if args.force or not keys_path.exists():
        keys = generate_search_keys()
        print(f"Claves de búsqueda escritas: {keys_path} ({len(keys)} claves, "
              f"SHA-256 {sha256_of(keys_path)})")
    else:
        check_search_keys()
        print(f"Las claves ya existen y su SHA-256 coincide con el manifiesto: {keys_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
