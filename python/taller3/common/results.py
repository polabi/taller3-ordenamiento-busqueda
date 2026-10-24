"""
Registro de resultados en CSV (mismo esquema que CsvResultWriter.java).

Columnas:
    algoritmo, lenguaje, variante, n, rep_1_ns .. rep_5_ns,
    promedio_ns, desv_estandar_ns, estado, causa, base_estimacion

- estado: "medido" o "estimado" (lo exige el taller).
- causa:  por qué se estimó (límite de 5 min, RecursionError, ...). Vacía si se midió.
- Los tiempos se guardan en nanosegundos enteros; la conversión a ms/s se hace al graficar.
Cada fila se escribe y se vacía a disco apenas termina el caso, para no perder
resultados si la ejecución se interrumpe.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path

from taller3 import config


@dataclass
class ResultRecord:
    algoritmo: str
    lenguaje: str
    variante: str
    n: int
    reps_ns: list[int] = field(default_factory=list)
    promedio_ns: float | None = None
    desv_estandar_ns: float | None = None
    estado: str = "medido"
    causa: str = ""
    base_estimacion: str = ""


class CsvResultWriter:
    def __init__(self, path: Path, repetitions: int = config.REPETITIONS):
        self.path = path
        self.repetitions = repetitions
        path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(path, "w", encoding="utf-8", newline="")
        self._w = csv.writer(self._fh)
        self._w.writerow(
            ["algoritmo", "lenguaje", "variante", "n"]
            + [f"rep_{i}_ns" for i in range(1, repetitions + 1)]
            + ["promedio_ns", "desv_estandar_ns", "estado", "causa", "base_estimacion"]
        )
        self._fh.flush()

    def write(self, r: ResultRecord) -> None:
        reps = [str(t) for t in r.reps_ns] + [""] * (self.repetitions - len(r.reps_ns))
        self._w.writerow(
            [r.algoritmo, r.lenguaje, r.variante, r.n]
            + reps
            + ["" if r.promedio_ns is None else f"{r.promedio_ns:.1f}",
               "" if r.desv_estandar_ns is None else f"{r.desv_estandar_ns:.1f}",
               r.estado, r.causa, r.base_estimacion]
        )
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()

    def __enter__(self) -> "CsvResultWriter":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


# ======================================================================================
# Punto 2 (búsqueda): escritor NUEVO; el del Punto 1 queda sin cambios.
# Columnas (spec p2 7.2; mismo esquema que SearchCsvWriter.java):
#   algoritmo, lenguaje, variante, n, num_busquedas, clave, rep_1_ns .. rep_5_ns,
#   promedio_ns, desv_estandar_ns, promedio_por_busqueda_ns, desv_por_busqueda_ns,
#   encontradas, checksum, estado, causa, base_estimacion
# - rep_i_ns es el tiempo TOTAL de la pasada i (1.000 búsquedas).
# - Las columnas "por búsqueda" se calculan aquí (= total / num_busquedas) desde los
#   valores sin redondear, para que no dependan de quien llama.
# ======================================================================================
@dataclass
class SearchResultRecord:
    algoritmo: str
    lenguaje: str
    variante: str
    n: int
    num_busquedas: int = config.NUM_SEARCH_KEYS
    clave: int | None = None                 # None en "claves"; el valor buscado en posiciones
    reps_ns: list[int] = field(default_factory=list)
    promedio_ns: float | None = None
    desv_estandar_ns: float | None = None
    encontradas: int | None = None           # None si no se midió
    checksum: int | None = None              # Σ out[j], incluidos los -1
    estado: str = "medido"
    causa: str = ""
    base_estimacion: str = ""


def _opt(value, fmt: str = "") -> str:
    return "" if value is None else format(value, fmt)


class SearchCsvWriter:
    def __init__(self, path: Path, repetitions: int = config.REPETITIONS):
        self.path = path
        self.repetitions = repetitions
        path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(path, "w", encoding="utf-8", newline="")
        self._w = csv.writer(self._fh)
        self._w.writerow(
            ["algoritmo", "lenguaje", "variante", "n", "num_busquedas", "clave"]
            + [f"rep_{i}_ns" for i in range(1, repetitions + 1)]
            + ["promedio_ns", "desv_estandar_ns", "promedio_por_busqueda_ns",
               "desv_por_busqueda_ns", "encontradas", "checksum",
               "estado", "causa", "base_estimacion"]
        )
        self._fh.flush()

    def write(self, r: SearchResultRecord) -> None:
        reps = [str(t) for t in r.reps_ns] + [""] * (self.repetitions - len(r.reps_ns))
        k = r.num_busquedas
        per_mean = None if r.promedio_ns is None else r.promedio_ns / k
        per_std = None if r.desv_estandar_ns is None else r.desv_estandar_ns / k
        self._w.writerow(
            [r.algoritmo, r.lenguaje, r.variante, r.n, k, _opt(r.clave)]
            + reps
            + [_opt(r.promedio_ns, ".1f"), _opt(r.desv_estandar_ns, ".1f"),
               _opt(per_mean, ".3f"), _opt(per_std, ".3f"),
               _opt(r.encontradas), _opt(r.checksum),
               r.estado, r.causa, r.base_estimacion]
        )
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()

    def __enter__(self) -> "SearchCsvWriter":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


# ======================================================================================
# Punto 3 (experimento de supuestos): escritor NUEVO; los anteriores quedan sin cambios.
# Mismo esquema que el del Punto 1 + columna `distribucion` después de `variante`
# (spec p3 7.2; mismo esquema que SupuestosCsvWriter.java). Reutiliza ResultRecord.
# ======================================================================================
class SupuestosCsvWriter:
    def __init__(self, path: Path, repetitions: int = config.REPETITIONS):
        self.path = path
        self.repetitions = repetitions
        path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(path, "w", encoding="utf-8", newline="")
        self._w = csv.writer(self._fh)
        self._w.writerow(
            ["algoritmo", "lenguaje", "variante", "distribucion", "n"]
            + [f"rep_{i}_ns" for i in range(1, repetitions + 1)]
            + ["promedio_ns", "desv_estandar_ns", "estado", "causa", "base_estimacion"]
        )
        self._fh.flush()

    def write(self, record: ResultRecord, distribucion: str) -> None:
        r = record
        reps = [str(t) for t in r.reps_ns] + [""] * (self.repetitions - len(r.reps_ns))
        self._w.writerow(
            [r.algoritmo, r.lenguaje, r.variante, distribucion, r.n]
            + reps
            + [_opt(r.promedio_ns, ".1f"), _opt(r.desv_estandar_ns, ".1f"),
               r.estado, r.causa, r.base_estimacion]
        )
        self._fh.flush()

    def close(self) -> None:
        self._fh.close()

    def __enter__(self) -> "SupuestosCsvWriter":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
