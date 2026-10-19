"""
Generador ÚNICO de los datos de prueba (se ejecuta una sola vez).

    cd python
    python3 -m taller3.generate_data            # genera data/ si no existe
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
"""
from __future__ import annotations

import argparse
import json
import platform
import random
import sys
from datetime import datetime, timezone

from taller3 import config
from taller3.common.dataio import dataset_path, sha256_of, write_ints


def generate_values(seed: int, count: int) -> list[int]:
    rng = random.Random(seed)
    return [rng.randint(config.MIN_VALUE, config.MAX_VALUE) for _ in range(count)]


def main() -> int:
    parser = argparse.ArgumentParser(description="Genera los datos de prueba del taller")
    parser.add_argument("--force", action="store_true",
                        help="sobrescribe los archivos si ya existen")
    args = parser.parse_args()

    existing = [dataset_path(v, n) for n in config.SIZES for v in config.VARIANTS
                if dataset_path(v, n).exists()]
    if existing and not args.force:
        print(f"Los datos ya existen en {config.DATA_DIR} ({len(existing)} archivos).")
        print("Los datos se generan una sola vez; para regenerarlos hay que pasar --force.")
        return 0

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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
