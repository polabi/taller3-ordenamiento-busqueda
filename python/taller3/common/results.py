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
