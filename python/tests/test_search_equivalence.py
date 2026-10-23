"""
Prueba versionada de equivalencia Java <-> Python del Punto 2 (spec 8.5).

    cd python
    python3 -m unittest tests.test_search_equivalence -v

Ambos lenguajes (este archivo y java/src/taller3/tests/SearchEquivalenceSelfTest.java) se
comparan contra las MISMAS constantes escritas en specs/p2-busqueda.md, 8.5. Las
constantes se calcularon con un oráculo independiente (bisect_left / fórmula cerrada), no
ejecutando taller3.searching; el escritor de pruebas las recalculó de nuevo por su cuenta
el 2026-10-22 y coinciden.

Sobre out[j] = search(arr, Q[j]), j = 0..K-1 (en ese orden):
    enc = #{j : out[j] != -1};   S1 = Σ out[j] (incluye los -1);   S2 = Σ (j+1)·out[j]

Parte A: arreglo sintético N = 100.000 sin duplicados, K = 200 (sin archivos ni RNG).
Parte C: data/claves_busqueda.txt sobre data/ascendente_1000.txt. Si el archivo no existe
         la prueba FALLA (no se salta; spec 8.5 parte C: "el archivo estará versionado").
"""
from __future__ import annotations

import hashlib
import importlib
import unittest

from taller3 import config
from taller3.common.dataio import dataset_path, read_ints
from taller3.searching import SEARCHES

EXPECTED_ORDER = (
    "LinearSearch", "BinarySearch", "TernarySearch", "JumpSearch",
    "InterpolationSearch", "ExponentialSearch", "InterpolationSearchIntDiv",
)

# --- Parte A (spec 8.5) ----------------------------------------------------------------
N_A = 100_000
K_A = 200
A_CHECKS = {"A0_A1_A2": [10_000_500, 10_000_507, 10_000_514], "A_last": 15_700_393,
            "sum_A": 1_201_713_770_300,
            "Q0_5": [10_000_000, 15_700_395, 10_236_788, 10_448_997, 10_723_916, 11_061_547],
            "sum_Q": 2_431_583_865}
A_EXPECTED = {"enc": 120, "S1": 5_953_340, "S2": 629_320_400}

# --- Parte C (spec 8.5) ----------------------------------------------------------------
KEYS_SHA256 = "22fdc47fbcdd3e4b4d26fbcd3eae5010bb3becaa981337c9fe9fa41aaa0c965f"
C_EXPECTED = {"enc": 500, "S1": 249_971, "S2": 120_950_349}
MISSING_KEYS_MSG = "genera las claves: python3 -m taller3.generate_data"


def build_part_a() -> tuple[list[int], list[int]]:
    """Arreglo A y claves Q exactamente como en la spec 8.5, parte A."""
    a = [10_000_500 + 7 * i + (i * i) // 2000 for i in range(N_A)]

    def p(j: int) -> int:
        return (j * 7919) % N_A

    q = []
    for j in range(K_A):
        r = j % 10
        if r == 0:
            q.append(10_000_000 + j)          # ausente, menor que el mínimo
        elif r == 1:
            q.append(a[N_A - 1] + 1 + j)      # ausente, mayor que el máximo
        elif r in (2, 3):
            q.append(a[p(j)] + 1)             # ausente interior (huecos >= 7)
        else:
            q.append(a[p(j)])                 # presente en el índice p(j)
    return a, q


def run_keys(func, arr: list[int], keys: list[int]) -> dict[str, int]:
    out = [func(arr, x) for x in keys]        # orden j = 0, 1, 2, ...
    return {"enc": sum(1 for o in out if o != -1),
            "S1": sum(out),
            "S2": sum((j + 1) * o for j, o in enumerate(out))}


class TestEquivalenciaParteA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a, cls.q = build_part_a()

    def test_8_5_A_construccion(self):
        a, q = self.a, self.q
        self.assertEqual(a[:3], A_CHECKS["A0_A1_A2"])
        self.assertEqual(a[-1], A_CHECKS["A_last"])
        self.assertEqual(sum(a), A_CHECKS["sum_A"])
        self.assertTrue(all(a[i] < a[i + 1] for i in range(N_A - 1)), "A estrictamente creciente")
        self.assertTrue(all(config.MIN_VALUE <= v <= config.MAX_VALUE for v in a))
        self.assertEqual(q[:6], A_CHECKS["Q0_5"])
        self.assertEqual(sum(q), A_CHECKS["sum_Q"])
        self.assertEqual(len(set(q)), K_A)

    def test_8_5_A_registro_completo(self):
        self.assertEqual(tuple(s.name for s in SEARCHES), EXPECTED_ORDER)

    def test_8_5_A_constantes_7_algoritmos(self):
        snapshot = list(self.a)
        for spec in SEARCHES:
            with self.subTest(algoritmo=spec.name):
                self.assertEqual(run_keys(spec.func, self.a, self.q), A_EXPECTED)
        self.assertEqual(self.a, snapshot, "algún algoritmo modificó el arreglo")


class TestEquivalenciaParteC(unittest.TestCase):
    def _load(self):
        keys_path = config.DATA_DIR / getattr(config, "SEARCH_KEYS_FILE", "claves_busqueda.txt")
        if not keys_path.exists():
            self.fail(f"No existe {keys_path}: {MISSING_KEYS_MSG}")
        try:
            load = importlib.import_module("taller3.common.dataio").load_search_keys
        except AttributeError:
            self.fail("Falta implementar taller3.common.dataio.load_search_keys (spec 6.1.6)")
        return keys_path, load(config.DATA_DIR)

    def test_8_5_C_sha256_y_reparto(self):
        keys_path, keys = self._load()
        self.assertEqual(hashlib.sha256(keys_path.read_bytes()).hexdigest(), KEYS_SHA256)
        self.assertEqual(len(keys), 1000)
        self.assertEqual(len(set(keys)), 1000)
        asc = set(read_ints(dataset_path("ascendente", 1000), 1000))
        self.assertEqual(sum(1 for k in keys if k in asc), 500, "reparto 500 presentes / 500 ausentes")

    def test_8_5_C_constantes_7_algoritmos(self):
        _, keys = self._load()
        arr = read_ints(dataset_path("ascendente", 1000), 1000)
        for spec in SEARCHES:
            with self.subTest(algoritmo=spec.name):
                self.assertEqual(run_keys(spec.func, arr, keys), C_EXPECTED)


if __name__ == "__main__":
    unittest.main()
