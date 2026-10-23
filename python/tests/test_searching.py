"""
Pruebas de corrección de los 7 algoritmos de búsqueda del Punto 2 (no miden tiempo).

    cd python
    python3 -m unittest tests.test_searching -v

Fuente de los valores esperados: specs/p2-busqueda.md, secciones 4 y 5 (parte
APROBADA el 2026-10-20). Cada caso lleva el nombre de la spec (A_x70, D_x7, F1...)
para poder rastrearlo. Para cada caso se comprueban DOS cosas (decisión D-extra):
  1. validez: -1 si x no está; si no, 0 <= i < n y arr[i] == x;
  2. índice exacto: el que devuelve el pseudocódigo normativo de la sección 3
     (con duplicados los algoritmos devuelven índices distintos, todos válidos).
Además: el arreglo no se modifica, orden/nombres del registro (2.1),
binary_search_range (3.2) y la propiedad aleatoria de 5.7 contra bisect.

Mismos casos que java/src/taller3/tests/SearchSelfTest.java.
"""
from __future__ import annotations

import bisect
import random
import unittest

from taller3 import config
from taller3.searching import BY_NAME, SEARCHES
from taller3.searching.binary_search import binary_search_range

# Orden del registro = orden de las columnas de las tablas de la spec (2.1 y 5):
# Lin., Bin., Ter., Sal., Int. (oficial, double), Exp., IDiv (variante).
EXPECTED_ORDER = (
    "LinearSearch",
    "BinarySearch",
    "TernarySearch",
    "JumpSearch",
    "InterpolationSearch",
    "ExponentialSearch",
    "InterpolationSearchIntDiv",
)

# --- Arreglos de la sección 5 --------------------------------------------------
A = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160]   # 5.1
D = [5, 7, 7, 7, 9, 12, 12, 15]                                                # 5.2
U = [1, 2, 3, 4, 5, 6, 7, 8, 9, 1000]                                          # 5.3
O = [10_000_000 + 909_090 * i for i in range(99)] + [99_999_999]               # 5.5
F1 = [3, 52, 52]                                                               # 5.6
F2 = [31, 54, 54, 59]
F3 = [1, 10, 20, 48]
ALL4 = [4, 4, 4, 4, 4]


def _all(v: int) -> tuple[int, ...]:
    return (v,) * 7


# (nombre del caso en la spec, arreglo, x, esperado en el orden de EXPECTED_ORDER)
CASES: tuple[tuple[str, list[int], int, tuple[int, ...]], ...] = (
    # 5.1 Arreglo A
    ("A_x70_presente", A, 70, _all(6)),
    ("A_x75_ausente_interior", A, 75, _all(-1)),
    ("A_x10_primero", A, 10, _all(0)),
    ("A_x160_ultimo", A, 160, _all(15)),
    ("A_x90", A, 90, _all(8)),
    ("A_x130", A, 130, _all(12)),
    ("A_x5_menor_que_minimo", A, 5, _all(-1)),
    ("A_x200_mayor_que_maximo", A, 200, _all(-1)),
    # 5.2 Arreglo D (duplicados)
    ("D_x7_duplicado", D, 7, (1, 3, 2, 1, 1, 3, 1)),
    ("D_x12_duplicado", D, 12, _all(5)),
    ("D_x5_primero", D, 5, _all(0)),
    ("D_x15_ultimo", D, 15, _all(7)),
    ("D_x8_ausente_interior", D, 8, _all(-1)),
    # 5.3 Arreglo U (no uniforme)
    ("U_x9", U, 9, _all(8)),
    ("U_x1000", U, 1000, _all(9)),
    ("U_x500_ausente", U, 500, _all(-1)),
    # 5.4 Mínimos y degenerados
    ("vacio_x1", [], 1, _all(-1)),
    ("uno_x42_presente", [42], 42, _all(0)),
    ("uno_x41_menor", [42], 41, _all(-1)),
    ("uno_x43_mayor", [42], 43, _all(-1)),
    ("dos_iguales_x3_guarda", [3, 3], 3, _all(0)),
    ("dos_iguales_x2", [3, 3], 2, _all(-1)),
    ("dos_iguales_x4", [3, 3], 4, _all(-1)),
    ("todos_iguales_x4", ALL4, 4, (0, 2, 1, 0, 0, 0, 0)),
    ("todos_iguales_x3", ALL4, 3, _all(-1)),
    ("todos_iguales_x5", ALL4, 5, _all(-1)),
    # 5.5 Arreglo O (8 dígitos, sin overflow)
    ("O_x31818160_sin_overflow", O, 31_818_160, _all(24)),
    ("O_x31818161_ausente", O, 31_818_161, _all(-1)),
    ("O_x99090820", O, 99_090_820, _all(98)),
    # Sección 4 sobre O: primer/último elemento con valores reales extremos de 8 dígitos
    ("O_x10000000_primero", O, 10_000_000, _all(0)),
    ("O_x99999999_ultimo", O, 99_999_999, _all(99)),
    ("O_x9999999_menor", O, 9_999_999, _all(-1)),
    ("O_x100000000_mayor", O, 100_000_000, _all(-1)),
    # 5.6 Casos que distinguen las fórmulas (obligatorios F1 y F2, sección 8.1)
    ("F1", F1, 52, (1, 1, 2, 1, 1, 2, 1)),
    ("F2", F2, 54, (1, 1, 1, 1, 2, 2, 1)),
    ("F3", F3, 48, _all(3)),
    ("F3_prima", F3, 47, _all(-1)),
    ("F1_prima", F1, 3, _all(0)),
    ("F1_biprima", F1, 51, _all(-1)),
)

PROPERTY_SEED = 20261020        # semilla fija de la prueba aleatoria 5.7 (documentada)


def property_data() -> tuple[list[int], list[int]]:
    """5.7: 3.000 valores de 8 dígitos ascendentes con duplicados forzados + 2.000 claves."""
    rng = random.Random(PROPERTY_SEED)
    arr = sorted(rng.randint(config.MIN_VALUE, config.MAX_VALUE) for _ in range(3000))
    for _ in range(300):                       # duplicados forzados: arr[j] = arr[j-1]
        j = rng.randrange(1, len(arr))
        arr[j] = arr[j - 1]
    for j in range(1500, 1520):                # un bloque largo de iguales en el centro
        arr[j] = arr[1499]
    for j in range(2990, 3000):                # y al final (arr[lo] == arr[hi] cerca de n-1)
        arr[j] = arr[2989]
    keys = [rng.choice(arr) for _ in range(1000)]
    keys += [rng.randint(config.MIN_VALUE, config.MAX_VALUE) for _ in range(1000)]
    keys += [arr[0], arr[-1], config.MIN_VALUE, config.MAX_VALUE]
    return arr, keys


class TestSearching(unittest.TestCase):
    def test_registro_orden_y_nombres(self) -> None:
        """2.1: SEARCHES en el orden de SearchRegistry.ALL; BY_NAME indexa por nombre."""
        self.assertEqual(tuple(s.name for s in SEARCHES), EXPECTED_ORDER)
        for s in SEARCHES:
            self.assertIs(BY_NAME[s.name], s)

    def test_casos_a_mano(self) -> None:
        """Secciones 4 y 5: validez + índice exacto, para los 7 algoritmos."""
        self.assertEqual(len(SEARCHES), 7)
        for name, arr, x, expected in CASES:
            for spec, exp in zip(SEARCHES, expected):
                with self.subTest(caso=name, algoritmo=spec.name, x=x):
                    work = list(arr)
                    got = spec.func(work, x)
                    self.assertEqual(work, arr, "el algoritmo modificó el arreglo")
                    self.assertIsInstance(got, int)
                    if exp == -1:
                        self.assertNotIn(x, arr)          # sanidad de la propia spec
                        self.assertEqual(got, -1)
                    else:
                        self.assertTrue(0 <= got < len(arr), f"índice fuera de rango: {got}")
                        self.assertEqual(work[got], x, "índice inválido")
                        self.assertEqual(got, exp, "índice válido pero no el exacto de la spec")

    def test_binary_search_range(self) -> None:
        """3.2: subrango [lo, hi] usado por la exponencial (traza de 5.1, rango [4, 8])."""
        self.assertEqual(binary_search_range(A, 4, 8, 70), 6)
        self.assertEqual(binary_search_range(A, 4, 8, 75), -1)
        self.assertEqual(binary_search_range(A, 4, 8, 10), -1)   # presente fuera del rango
        self.assertEqual(binary_search_range(A, 0, -1, 10), -1)  # rango vacío
        self.assertEqual(binary_search_range(D, 2, 4, 7), 3)     # traza de D, x = 7

    def test_propiedad_aleatoria(self) -> None:
        """5.7: -1 <=> bisect no la encuentra; si no, arr[i] == x; lineal = primera aparición."""
        arr, keys = property_data()
        snapshot = list(arr)
        n = len(arr)
        for spec in SEARCHES:
            with self.subTest(algoritmo=spec.name):
                for x in keys:
                    k = bisect.bisect_left(arr, x)
                    present = k < n and arr[k] == x
                    got = spec.func(arr, x)
                    if not present:
                        self.assertEqual(got, -1, f"x={x} ausente")
                        continue
                    self.assertTrue(0 <= got < n and arr[got] == x, f"x={x} -> {got}")
                    if spec.name == "LinearSearch":
                        self.assertEqual(got, k, f"x={x}: no es la primera aparición")
        self.assertEqual(arr, snapshot, "algún algoritmo modificó el arreglo")


if __name__ == "__main__":
    unittest.main()
