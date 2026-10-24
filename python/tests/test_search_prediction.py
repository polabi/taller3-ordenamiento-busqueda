"""
Pruebas del benchmark de búsqueda que faltaban (auditoría del Punto 2, 2026-10-23):

  1. verify_pass: la verificación de CADA pasada detecta índices malos, claves no
     encontradas y claves ausentes "encontradas" (spec 6.3, 8.2).
  2. Camino de los ESTIMADOS: si la predicción supera el límite, el caso no se ejecuta y
     queda `estimado` con causa y base; las posiciones usan ese estimado (spec 6.5).
  3. Predicción POR POSICIÓN: factor proporcional al trabajo de cada posición; `inicio`
     de la lineal se mide aunque `final` quede estimada (hallazgo A de la auditoría).

No miden tiempos reales ni leen data/: usan arreglos sintéticos y límites diminutos.
Equivalente Java: java/src/taller3/tests/SearchPredictionSelfTest.java (mismos casos).

    cd python
    python3 -m unittest tests.test_search_prediction -v
"""
from __future__ import annotations

import unittest

from taller3 import config
from taller3.bench_search import POSITION_WORK, SearchBenchmark, position_factor, presence, verify_pass
from taller3.searching import BY_NAME, SEARCHES

N = config.POSITION_N
K = config.NUM_SEARCH_KEYS
LINEAR = BY_NAME["LinearSearch"]
BINARY = BY_NAME["BinarySearch"]

# Mismo texto que debe producir SearchBenchmark.java (SearchPredictionSelfTest).
BASE_LINEAL_FINAL = ("t_claves(1000000)=1.2 s (medido) x 1000000/748440 = x1.33611 "
                     "(pasos de una búsqueda en final / pasos medios por clave en claves)")


class TestVerifyPass(unittest.TestCase):
    """6.3: out[j] == -1 <=> la clave no está; si no, 0 <= out[j] < n y arr[out[j]] == clave."""

    def setUp(self):
        self.arr = [10, 20, 30, 40, 50]
        self.keys = [20, 35, 50, 5, 10]                  # presentes: 20, 50, 10
        self.present = presence(self.arr, self.keys)

    def test_pasada_correcta_devuelve_encontradas_y_checksum(self):
        out = [1, -1, 4, -1, 0]
        self.assertEqual(verify_pass("X", "claves", self.arr, self.keys, self.present, out),
                         (3, 1 - 1 + 4 - 1 + 0))       # el checksum incluye los -1

    def test_presente_no_encontrada_falla(self):
        with self.assertRaisesRegex(AssertionError, "no encontró la clave 50"):
            verify_pass("X", "claves", self.arr, self.keys, self.present, [1, -1, -1, -1, 0])

    def test_indice_que_no_corresponde_a_la_clave_falla(self):
        with self.assertRaisesRegex(AssertionError, "índice 2 para la clave 20"):
            verify_pass("X", "claves", self.arr, self.keys, self.present, [2, -1, 4, -1, 0])

    def test_ausente_encontrada_falla(self):
        with self.assertRaisesRegex(AssertionError, "para la clave 35"):
            verify_pass("X", "claves", self.arr, self.keys, self.present, [1, 2, 4, -1, 0])

    def test_indice_fuera_de_rango_falla(self):
        for bad in (5, -2):
            with self.subTest(indice=bad), self.assertRaises(AssertionError):
                verify_pass("X", "claves", self.arr, self.keys, self.present, [bad, -1, 4, -1, 0])

    def test_run_case_aborta_si_el_algoritmo_devuelve_basura(self):
        from taller3.searching import SearchSpec
        malo = SearchSpec("Malo", lambda arr, x: 0, LINEAR.growth)    # siempre índice 0
        bench = SearchBenchmark(reps=2, limit_s=300)
        with self.assertRaises(AssertionError):
            bench.run_case(malo, "claves", self.arr, self.keys, self.present, None)


class TestCaminoEstimados(unittest.TestCase):
    """6.5: predicción > límite -> no se ejecuta; estado `estimado` con causa y base."""

    def test_claves_estimada_con_base_y_sin_repeticiones(self):
        bench = SearchBenchmark(reps=2, limit_s=1e-9)    # cualquier predicción lo supera
        keys = list(range(0, 2_000, 2))                  # 1.000 claves
        small = list(range(1_000))
        first = bench.run_case(LINEAR, "claves", small, keys, presence(small, keys), None)
        self.assertEqual(first.estado, "medido")         # sin n previo no hay predicción
        big = list(range(10_000))
        rec = bench.run_case(LINEAR, "claves", big, keys, presence(big, keys), None)
        self.assertEqual(rec.estado, "estimado")
        self.assertEqual(rec.reps_ns, [])
        self.assertIsNone(rec.encontradas)
        self.assertIsNone(rec.checksum)
        self.assertAlmostEqual(rec.promedio_ns, first.promedio_ns * 10, delta=1e-6 * first.promedio_ns)
        self.assertIn("> límite", rec.causa)
        self.assertTrue(rec.base_estimacion.startswith("t(1000)="), rec.base_estimacion)
        self.assertEqual(bench.claves_at[("LinearSearch", 10_000)], (rec.promedio_ns, "estimado"))

    def test_posicion_usa_el_claves_estimado(self):
        bench = SearchBenchmark(reps=2, limit_s=300)
        bench.claves_at[("LinearSearch", N)] = (600e9, "estimado")
        t, txt = bench.predict_position(LINEAR, "final", N)
        self.assertAlmostEqual(t, 600e9 * 1_000_000 / 748_440.213)
        self.assertIn("(estimado)", txt)

    def test_posicion_sin_claves_en_n_extrapola(self):
        bench = SearchBenchmark(reps=2, limit_s=300)
        bench.last_measured["LinearSearch"] = (100_000, 0.7e9)
        t, txt = bench.predict_position(LINEAR, "final", N)
        self.assertAlmostEqual(t, 7e9 * 1_000_000 / 748_440.213)
        self.assertTrue(txt.startswith("[t(100000)="), txt)


class TestPrediccionPorPosicion(unittest.TestCase):
    """Hallazgo A: un factor por posición, proporcional a su trabajo (tabla de la spec 6.5)."""

    def test_tabla_cubre_los_7_algoritmos_y_las_4_posiciones(self):
        self.assertEqual(set(POSITION_WORK), {s.name for s in SEARCHES})
        for name, (_, per) in POSITION_WORK.items():
            with self.subTest(algoritmo=name):
                self.assertEqual(tuple(per), config.POSITION_VARIANTS)

    def test_factores_de_la_spec(self):
        expected = {
            ("LinearSearch", "inicio"): 1 / 748_440.213,
            ("LinearSearch", "centro"): 500_000 / 748_440.213,
            ("LinearSearch", "centro_alto"): 500_001 / 748_440.213,
            ("LinearSearch", "final"): 1_000_000 / 748_440.213,          # 1,336
            ("InterpolationSearchIntDiv", "final"): 1_000_000 / 504_349.278,   # 1,983
            ("BinarySearch", "centro"): 1 / 19.43,
            ("JumpSearch", "centro"): 1_500 / 993.639,
        }
        for (a, v), f in expected.items():
            with self.subTest(algoritmo=a, posicion=v):
                self.assertAlmostEqual(position_factor(a, v)[0], f, places=12)
        self.assertAlmostEqual(position_factor("LinearSearch", "final")[0], 1.336, places=3)
        self.assertAlmostEqual(position_factor("InterpolationSearchIntDiv", "final")[0], 1.983, places=3)

    def test_cada_posicion_tiene_su_prediccion(self):
        bench = SearchBenchmark(reps=2, limit_s=300)
        bench.claves_at[("LinearSearch", N)] = (1.2e9, "medido")
        preds = {v: bench.predict_position(LINEAR, v, N)[0] for v in config.POSITION_VARIANTS}
        self.assertLess(preds["inicio"], 1e4)                          # ≈ 1,6 µs, no 1,6 s
        self.assertLess(preds["centro"], preds["final"])
        self.assertAlmostEqual(preds["final"] / preds["centro"], 2.0, places=5)
        self.assertEqual(bench.predict_position(LINEAR, "final", N)[1], BASE_LINEAL_FINAL)

    def test_sin_prediccion_fuera_de_10_a_la_6(self):
        bench = SearchBenchmark(reps=2, limit_s=300)
        bench.claves_at[("LinearSearch", 1_000)] = (1e6, "medido")
        self.assertIsNone(bench.predict_position(LINEAR, "final", 1_000))

    def test_inicio_se_mide_y_final_se_estima(self):
        """Con el factor único de antes, `inicio` también quedaba estimada (y con el tiempo de final)."""
        arr = list(range(0, 2 * N, 2))                   # 10^6 valores únicos, sin archivos
        bench = SearchBenchmark(reps=2, limit_s=1.0)
        bench.claves_at[("LinearSearch", N)] = (1.2e9, "medido")      # final -> 1,6 s > 1 s
        recs = {}
        for v in ("inicio", "final"):
            key = arr[{"inicio": 0, "final": N - 1}[v]]
            recs[v] = bench.run_case(LINEAR, v, arr, [key] * K, [True] * K, key)
        self.assertEqual(recs["inicio"].estado, "medido")
        self.assertEqual(recs["inicio"].encontradas, K)
        self.assertEqual(recs["inicio"].checksum, 0)
        self.assertEqual(recs["final"].estado, "estimado")
        self.assertEqual(recs["final"].base_estimacion, BASE_LINEAL_FINAL)

    def test_binaria_centro_se_predice_menor_que_centro_alto(self):
        bench = SearchBenchmark(reps=2, limit_s=300)
        bench.claves_at[("BinarySearch", N)] = (2e5, "medido")
        c = bench.predict_position(BINARY, "centro", N)[0]
        ca = bench.predict_position(BINARY, "centro_alto", N)[0]
        self.assertAlmostEqual(ca / c, 19.0)


if __name__ == "__main__":
    unittest.main()
