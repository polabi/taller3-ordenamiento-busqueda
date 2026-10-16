"""
Pruebas de corrección de los 6 algoritmos (no miden tiempo).

    cd python
    python3 -m unittest discover -s tests -v

Casos borde: vacío, 1 y 2 elementos, todos iguales, duplicados, ya ordenado,
invertido y aleatorio con valores de 8 dígitos. El oráculo es sorted().
"""
from __future__ import annotations

import random
import unittest

from taller3 import config
from taller3.sorting import SORTS


def cases() -> dict[str, list[int]]:
    rng = random.Random(123)
    rand = [rng.randint(config.MIN_VALUE, config.MAX_VALUE) for _ in range(3000)]
    few_values = [rng.choice([10_000_000, 55_555_555, 99_999_999]) for _ in range(500)]
    asc = sorted(rand[:900])                       # 900: cabe en el límite de recursión
    return {
        "vacio": [],
        "uno": [42_000_000],
        "dos_invertidos": [99_999_999, 10_000_000],
        "todos_iguales": [12_345_678] * 300,
        "pocos_valores_distintos": few_values,
        "ascendente": asc,
        "descendente": asc[::-1],
        "aleatorio_3000": rand,
        "extremos_del_rango": [config.MAX_VALUE, config.MIN_VALUE] * 50,
    }


class TestSorting(unittest.TestCase):
    def test_all_algorithms(self) -> None:
        for spec in SORTS:
            for name, data in cases().items():
                with self.subTest(algoritmo=spec.name, caso=name):
                    work = list(data)
                    spec.func(work)
                    self.assertEqual(work, sorted(data))


if __name__ == "__main__":
    unittest.main()
