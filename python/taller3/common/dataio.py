"""
Lectura y escritura de los archivos planos de datos.

Formato: un entero por línea, codificación ASCII, fin de línea '\\n', sin encabezado.
Es el formato más simple posible para que Java y Python lo lean igual.

Nada de este módulo se ejecuta dentro de una región medida.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from taller3 import config


def dataset_path(variant: str, n: int, data_dir: Path = config.DATA_DIR) -> Path:
    """Ruta del archivo de una variante y tamaño, p. ej. data/aleatoria_1000.txt."""
    if variant not in config.VARIANTS:
        raise ValueError(f"Variante desconocida: {variant!r}")
    return data_dir / f"{variant}_{n}.txt"


def write_ints(path: Path, values: Iterable[int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="ascii", newline="\n") as f:
        for v in values:
            f.write(f"{v}\n")


def read_ints(path: Path, expected_n: int | None = None,
              check_range: bool = True) -> list[int]:
    """Lee un archivo de enteros y valida tamaño y rango (falla rápido si algo no cuadra)."""
    if not path.exists():
        raise FileNotFoundError(
            f"No existe {path}. Genera los datos primero: "
            f"python3 -m taller3.generate_data"
        )
    with open(path, "r", encoding="ascii") as f:
        values = [int(line) for line in f if line.strip()]

    if expected_n is not None and len(values) != expected_n:
        raise ValueError(f"{path.name}: se esperaban {expected_n} valores y hay {len(values)}")
    if check_range and values:
        lo, hi = min(values), max(values)
        if lo < config.MIN_VALUE or hi > config.MAX_VALUE:
            raise ValueError(f"{path.name}: valores fuera de rango [{lo}, {hi}]")
    return values


def search_keys_path(data_dir: Path = config.DATA_DIR) -> Path:
    """Ruta del archivo de claves del Punto 2: data/claves_busqueda.txt."""
    return data_dir / config.SEARCH_KEYS_FILE


def load_search_keys(data_dir: Path = config.DATA_DIR) -> list[int]:
    """Lee las 1.000 claves en el orden del archivo (cantidad y rango los valida read_ints).

    Además exige que no haya repetidas (spec p2 6.1.2): una clave repetida pesaría doble
    en el promedio y en el checksum. No comprueba el SHA-256 (eso lo hace el generador).
    """
    keys = read_ints(search_keys_path(data_dir), config.NUM_SEARCH_KEYS)
    if len(set(keys)) != len(keys):
        raise ValueError(f"{config.SEARCH_KEYS_FILE}: hay {len(keys) - len(set(keys))} claves repetidas")
    return keys


def supuestos_path(distribucion: str, n: int, data_dir: Path = config.DATA_DIR) -> Path:
    """Ruta del archivo del experimento de supuestos del Punto 3 (spec p3 6.1.5).

    `uniforme` es la entrada aleatoria del Punto 1 (data/aleatoria_{n}.txt); las demás
    distribuciones están en data/p3/{distribucion}_{n}.txt.
    """
    if distribucion == "uniforme":
        return data_dir / f"aleatoria_{n}.txt"
    if distribucion in ("rango_pequeno", "concentrado_extremos", "digitos16"):
        return data_dir / config.SUPUESTOS_SUBDIR / f"{distribucion}_{n}.txt"
    raise ValueError(f"Distribución desconocida: {distribucion!r}")


def load_supuestos(distribucion: str, n: int, data_dir: Path = config.DATA_DIR) -> list[int]:
    """Lee n enteros; valida el rango de 8 dígitos salvo en digitos16 (16 dígitos a propósito).

    No comprueba el SHA-256 (eso lo hacen el generador y las pruebas).
    """
    return read_ints(supuestos_path(distribucion, n, data_dir), n,
                     check_range=(distribucion != "digitos16"))


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass(frozen=True)
class Dataset:
    """Las tres variantes de entrada para un mismo n (mismos valores, distinto orden)."""
    n: int
    aleatoria: list[int]
    ascendente: list[int]
    descendente: list[int]

    def get(self, variant: str) -> list[int]:
        return getattr(self, variant)


def load_dataset(n: int, data_dir: Path = config.DATA_DIR) -> Dataset:
    return Dataset(
        n=n,
        aleatoria=read_ints(dataset_path("aleatoria", n, data_dir), n),
        ascendente=read_ints(dataset_path("ascendente", n, data_dir), n),
        descendente=read_ints(dataset_path("descendente", n, data_dir), n),
    )
