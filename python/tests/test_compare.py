"""
Pruebas del Punto 3 (análisis comparativo): funciones puras, datos de data/p3/, lectura,
CSV del experimento de supuestos y cálculos de plot_compare. No miden tiempos reales ni
corren el benchmark.

    cd python
    python3 -m unittest tests.test_compare -v

Fuente de los valores esperados: specs/p3-comparativo.md (APROBADA 2026-10-22): casos
resueltos a mano de 5.6, SHA-256 de 6.1.3, perfiles de 4.4.3, tabla 4.1 y comprobaciones
de 8. Cada prueba lleva en el nombre la sección de la spec que cubre.

Reglas de estas pruebas:
- NUNCA escriben en data/ real: la generación se prueba en un directorio temporal con una
  copia de manifest.json.
- Las funciones aún no implementadas se importan dentro de cada prueba con _req(): si
  faltan, la prueba FALLA con el nombre de lo que hay que implementar.
- Si faltan los archivos de data/p3/, las pruebas sobre datos reales fallan con
  "genera los datos: python3 -m taller3.generate_data".

Contrato que fijan estas pruebas (además de las firmas explícitas de la spec 3.1 y 6.1.5):
- generate_data.generate_supuestos_data(data_dir: Path = config.DATA_DIR) -> None
  (6.1.3 + 6.1.4: escribe los 7 archivos de data_dir/p3/ y agrega sus 7 entradas al manifiesto).
- generate_data.check_supuestos_data(data_dir: Path = config.DATA_DIR) -> None
  (6.1.4: ValueError si algún SHA-256 no coincide con el manifiesto o falta su entrada).
- bench_supuestos.supuestos_growth(algoritmo, distribucion) -> Growth; ValueError si el par no existe.
- bench_supuestos.environment_path(out: Path) -> Path = out.with_name(f"entorno_{out.stem}.json").
- common.results.SupuestosCsvWriter(path, repetitions); write(record: ResultRecord, distribucion: str).
- plot_compare.lower_bound_rows() -> list[dict] (tabla 4.1 / p3_limite_inferior.csv).
- plot_compare.k_star_rows(ordenamiento, busqueda) -> list[dict]: ordenamiento y busqueda son
  {"Java": filas_csv, "Python": filas_csv}; devuelve las 7 filas de 7.3 (columnas de
  p3_k_estrella.csv, con números sin formatear); ValueError si falta t_ord, t_B o t_L.
- plot_compare.k_star_warnings(rows) -> list[str]: aviso de la regla de la banda (5.2).
- plot_compare.supuestos_warnings(supuestos, ordenamiento) -> list[str]: avisos de 8.
"""
from __future__ import annotations

import csv
import hashlib
import importlib
import json
import math
import shutil
import tempfile
import unittest
from pathlib import Path

from taller3 import config

GEN_MSG = "genera los datos: python3 -m taller3.generate_data"
P3_DIR = config.DATA_DIR / "p3"

# --- 6.1.3: archivos de data/p3/ ------------------------------------------------------
P3_SHA256 = {
    "rango_pequeno_10000.txt": "003a0b993de857ec96c4905b93e6e57bc1c24fd0ea711ce506fc1a3a163fcc76",
    "concentrado_extremos_10000.txt": "98faca8f71baf19fd0a9c38e92dd4bfa69b37f8c2cd2fb6c221a6dc074035fce",
    "rango_pequeno_100000.txt": "769ed52b6fa6c50f04e40cbc33587aea8f53ca1331162a9549a7620b1c5db22a",
    "concentrado_extremos_100000.txt": "6c229b3698df7ac7e1e7acf9fd2f7498692228070d1a311b2ca7e1f3cd77faa9",
    "digitos16_10000.txt": "e3070fb38fcd24158fc39f3df21321553c82798cfb88bd17dae04236691dc49b",
    "digitos16_100000.txt": "498749d81d819d233cfc59f743333278ea46470f79a0f870bb2179cba365e510",
    "digitos16_1000000.txt": "211b340833ed98ddb22c5e786a746d08313bff08fa3d571a016b8f0e8cae1317",
}
# nombre -> (mín, máx, distintos, primeros 3 o None)
P3_STATS = {
    "rango_pequeno_10000.txt": (10_000_000, 10_000_999, 1_000, None),
    "concentrado_extremos_10000.txt": (10_000_000, 99_999_999, 9_443,
                                       [55_010_207, 55_042_783, 55_073_867]),
    "rango_pequeno_100000.txt": (10_000_000, 10_000_999, 1_000, None),
    "concentrado_extremos_100000.txt": (10_000_000, 99_999_999, 9_002,
                                        [55_004_244, 55_001_577, 55_004_382]),
    "digitos16_10000.txt": (1_000_155_328_241_689, 9_999_529_235_286_674, 10_000, None),
    "digitos16_100000.txt": (1_000_030_654_373_518, 9_999_960_352_334_845, 100_000, None),
    "digitos16_1000000.txt": (1_000_005_417_451_910, 9_999_994_015_984_721, 1_000_000, None),
}
DIGITOS16_FIRST3 = [6_589_395_405_209_567, 3_818_904_597_604_050, 1_815_028_165_842_779]
P3_PARAMETROS = {
    "rango_pequeno": "randint(10000000, 10000999)",
    "concentrado_extremos_10000": "n-2 randint(55000000, 55089999) + 10000000 + 99999999, rng.shuffle",
    "concentrado_extremos_100000": "n-2 randint(55000000, 55008999) + 10000000 + 99999999, rng.shuffle",
    "digitos16": "randint(10**15, 10**16-1); prefijo de la secuencia de 1000000",
}

# --- 4.4.3: perfiles exactos del Bucket Sort del repo ---------------------------------
BUCKET_PROFILES = {
    ("uniforme", 10_000): (6_331, 7, 2_537),
    ("uniforme", 100_000): (63_394, 7, 24_756),
    ("rango_pequeno", 10_000): (1_000, 22, 0),
    ("rango_pequeno", 100_000): (1_000, 131, 0),
    ("concentrado_extremos", 10_000): (12, 1_045, 2_466_064),
    ("concentrado_extremos", 100_000): (12, 10_184, 249_837_990),
}

SUPUESTOS_HEADER = (                                                                # 7.2
    "algoritmo,lenguaje,variante,distribucion,n,rep_1_ns,rep_2_ns,rep_3_ns,rep_4_ns,"
    "rep_5_ns,promedio_ns,desv_estandar_ns,estado,causa,base_estimacion"
)
K_STAR_COLUMNS = ["lenguaje", "rol", "algoritmo_orden", "t_ord_ns", "fuente_t_lineal",
                  "t_lineal_ns", "t_binaria_ns", "k_estrella", "k_min", "k_bajo", "k_alto",
                  "estado"]                                                        # 7.3


def _req(module: str, attr: str | None = None):
    """Importa algo que la spec exige; si falta, la prueba FALLA diciendo qué implementar."""
    try:
        m = importlib.import_module(module)
    except ImportError as e:
        raise AssertionError(f"Falta implementar el módulo {module} (spec p3): {e}") from None
    if attr is None:
        return m
    if not hasattr(m, attr):
        raise AssertionError(f"Falta implementar {module}.{attr} (spec p3)")
    return getattr(m, attr)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read(path: Path) -> list[int]:
    return [int(line) for line in path.read_text(encoding="ascii").splitlines()]


def _p3_file(test: unittest.TestCase, name: str) -> Path:
    path = P3_DIR / name
    if not path.exists():
        test.fail(f"No existe {path}: {GEN_MSG}")
    return path


def _load_csv(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# ======================================================================================
# 5.6 Funciones puras (common/compare.py)
# ======================================================================================
class TestKStar(unittest.TestCase):
    # (t_ord, t_L, t_B, k*, k_min, tolerancia de k*)
    CASES = [
        (16_087_758.4, 1_000_000, 100, 16.0894, 17, 5e-5),
        (1_000, 110, 10, 10.0, 11, 0.0),
        (457_194_941.8, 7_000_000, 5_000, 65.36, 66, 5e-3),
        (1_775_541_275.0, 7_000_000, 5_000, 253.8301, 254, 5e-5),
        (0, 10, 5, 0.0, 1, 0.0),
    ]

    def test_5_6_k_star_y_k_min(self):
        k_star = _req("taller3.common.compare", "k_star")
        k_min = _req("taller3.common.compare", "k_min")
        for t_ord, t_l, t_b, ks, km, tol in self.CASES:
            with self.subTest(t_ord=t_ord, t_l=t_l, t_b=t_b):
                self.assertAlmostEqual(k_star(t_ord, t_l, t_b), ks, delta=tol)
                self.assertEqual(k_min(t_ord, t_l, t_b), km)
                self.assertIsInstance(k_min(t_ord, t_l, t_b), int)

    def test_5_6_empate_exacto_en_k_10_da_11(self):
        k_star = _req("taller3.common.compare", "k_star")
        k_min = _req("taller3.common.compare", "k_min")
        self.assertEqual(k_star(1_000, 110, 10), 10)
        self.assertEqual(k_min(1_000, 110, 10), 11)
        # en k = 10 empatan (1.100 = 1.000 + 100); en k = 11 ordenar es estrictamente mejor
        self.assertEqual(10 * 110, 1_000 + 10 * 10)
        self.assertGreater(11 * 110, 1_000 + 11 * 10)

    def test_5_6_nunca_conviene_si_t_l_no_supera_t_b(self):
        k_star = _req("taller3.common.compare", "k_star")
        k_min = _req("taller3.common.compare", "k_min")
        for t_l, t_b in ((10, 10), (5, 10)):
            with self.subTest(t_l=t_l, t_b=t_b):
                self.assertIsNone(k_star(1_000, t_l, t_b))
                self.assertIsNone(k_min(1_000, t_l, t_b))

    def test_5_4_comprobacion_de_k_min_con_1_ms(self):
        # k = 16 todavía conviene no ordenar; k = 17 conviene ordenar
        k_min = _req("taller3.common.compare", "k_min")
        t_ord, t_l, t_b = 16_087_758.4, 1_000_000, 100
        km = k_min(t_ord, t_l, t_b)
        self.assertLessEqual((km - 1) * t_l, t_ord + (km - 1) * t_b)
        self.assertGreater(km * t_l, t_ord + km * t_b)

    def test_5_3_sensibilidad_es_la_razon_de_los_t_ord(self):
        k_star = _req("taller3.common.compare", "k_star")
        ratio = k_star(1_775_541_275.0, 7e6, 5e3) / k_star(457_194_941.8, 7e6, 5e3)
        self.assertAlmostEqual(ratio, 1_775_541_275.0 / 457_194_941.8, delta=1e-12)
        self.assertEqual(round(ratio, 4), 3.8836)


class TestKInterval(unittest.TestCase):
    def test_5_6_k_interval(self):
        k_interval = _req("taller3.common.compare", "k_interval")
        lo, hi = k_interval(1_000, 100, 110, 10, 10, 0)
        self.assertAlmostEqual(lo, 900 / 110, delta=1e-12)      # 8,1818…
        self.assertAlmostEqual(hi, 1_100 / 90, delta=1e-12)     # 12,2222…

    def test_5_6_k_interval_denominador_cero_da_none(self):
        k_interval = _req("taller3.common.compare", "k_interval")
        lo, hi = k_interval(1_000, 100, 110, 100, 10, 0)
        self.assertAlmostEqual(lo, 900 / 200, delta=1e-12)
        self.assertIsNone(hi)                                   # (110 − 100) − 10 = 0


class TestLowerBound(unittest.TestCase):
    def test_5_6_lower_bound_comparisons(self):
        lb = _req("taller3.common.compare", "lower_bound_comparisons")
        expected = {0: 0, 1: 0, 2: 1, 3: 3, 4: 5, 5: 7, 1_000: 8_530, 10_000: 118_459,
                    100_000: 1_516_705, 1_000_000: 18_488_885}
        for n, v in expected.items():
            with self.subTest(n=n):
                self.assertEqual(lb(n), v)
                self.assertIsInstance(lb(n), int)

    def test_4_1_coincide_con_el_entero_exacto_para_n_pequenos(self):
        lb = _req("taller3.common.compare", "lower_bound_comparisons")
        for n in list(range(2, 60)) + [1_000]:
            with self.subTest(n=n):
                self.assertEqual(lb(n), (math.factorial(n) - 1).bit_length())


class TestBucketProfile(unittest.TestCase):
    CASES = [
        ([10, 19, 13, 11, 13, 12], (3, 3, 2)),
        ([1, 100, 60, 59, 58, 57], (3, 4, 6)),
        ([5, 5, 5, 5], (1, 4, 0)),
        ([3, 1], (2, 1, 0)),
        ([7], (1, 1, 0)),
        ([], (0, 0, 0)),
    ]

    def test_5_6_bucket_profile_casos_a_mano(self):
        bp = _req("taller3.common.compare", "bucket_profile")
        for values, expected in self.CASES:
            with self.subTest(values=values):
                self.assertEqual(tuple(bp(values)), expected)

    def test_5_6_bucket_profile_no_modifica_la_entrada(self):
        bp = _req("taller3.common.compare", "bucket_profile")
        values = [10, 19, 13, 11, 13, 12]
        bp(values)
        self.assertEqual(values, [10, 19, 13, 11, 13, 12])

    def test_3_1_desplazamientos_igual_a_insertion_estricto_instrumentado(self):
        # Oráculo independiente: el Bucket del repo con un contador en el while del Insertion.
        bp = _req("taller3.common.compare", "bucket_profile")
        import random
        rng = random.Random(3)
        for trial in range(30):
            n = rng.randint(2, 300)
            values = [rng.randint(0, rng.choice([5, 50, 10_000])) for _ in range(n)]
            if trial % 5 == 0:                                   # cúmulo con extremos
                values = [rng.randint(500, 520) for _ in range(n - 2)] + [0, 1_000]
            with self.subTest(trial=trial):
                self.assertEqual(tuple(bp(values)), _instrumented_bucket(values))


def _instrumented_bucket(arr: list[int]) -> tuple[int, int, int]:
    n = len(arr)
    mn, mx = min(arr), max(arr)
    k, rango = n, mx - mn + 1
    buckets: list[list[int]] = [[] for _ in range(k)]
    for x in arr:
        buckets[(x - mn) * k // rango].append(x)
    shifts = 0
    for b in buckets:
        for i in range(1, len(b)):
            key, j = b[i], i - 1
            while j >= 0 and b[j] > key:
                b[j + 1] = b[j]
                j -= 1
                shifts += 1
            b[j + 1] = key
    return sum(1 for b in buckets if b), max(len(b) for b in buckets), shifts


class TestRadixPasses(unittest.TestCase):
    def test_5_6_radix_passes_casos_a_mano(self):
        rp = _req("taller3.common.compare", "radix_passes")
        expected = [([], 0), ([0], 0), ([5], 1), ([10], 2), ([99_999_999], 8),
                    ([10 ** 15], 16), ([10 ** 16 - 1], 16)]
        for values, v in expected:
            with self.subTest(values=values):
                self.assertEqual(rp(values), v)

    def test_5_6_radix_passes_sobre_archivos(self):
        rp = _req("taller3.common.compare", "radix_passes")
        self.assertEqual(rp(_read(config.DATA_DIR / "aleatoria_10000.txt")), 8)
        for n in (10_000, 100_000, 1_000_000):
            with self.subTest(n=n):
                self.assertEqual(rp(_read(_p3_file(self, f"digitos16_{n}.txt"))), 16)


# ======================================================================================
# 6.1.1 Constantes
# ======================================================================================
class TestConfigSupuestos(unittest.TestCase):
    def test_6_1_1_constantes_config(self):
        expected = {
            "SUPUESTOS_SEED": 20261017,
            "SUPUESTOS_SUBDIR": "p3",
            "SUPUESTOS_SIZES": (10_000, 100_000),
            "DIGITOS16_SIZES": (10_000, 100_000, 1_000_000),
            "BUCKET_DISTRIBUTIONS": ("uniforme", "rango_pequeno", "concentrado_extremos"),
            "RADIX_DISTRIBUTIONS": ("uniforme", "digitos16"),
            "RANGO_PEQUENO": (10_000_000, 10_000_999),
            "CONCENTRADO_CUBETAS": 10,
            "DIGITOS16_RANGE": (10 ** 15, 10 ** 16 - 1),
        }
        for name, value in expected.items():
            with self.subTest(constante=name):
                self.assertTrue(hasattr(config, name), f"Falta config.{name}")
                self.assertEqual(getattr(config, name), value)

    def test_6_1_1_semilla_independiente(self):
        seed = getattr(config, "SUPUESTOS_SEED", config.SEED)
        self.assertNotIn(seed, (config.SEED, config.SEARCH_KEYS_SEED))


# ======================================================================================
# 6.1.5 Lectura
# ======================================================================================
class TestLecturaSupuestos(unittest.TestCase):
    def test_6_1_5_supuestos_path_mapeo(self):
        sp = _req("taller3.common.dataio", "supuestos_path")
        d = Path("/x/data")
        self.assertEqual(sp("uniforme", 10_000, d), d / "aleatoria_10000.txt")
        for dist in ("rango_pequeno", "concentrado_extremos", "digitos16"):
            with self.subTest(dist=dist):
                self.assertEqual(sp(dist, 100_000, d), d / "p3" / f"{dist}_100000.txt")
        self.assertEqual(sp("uniforme", 10_000), config.DATA_DIR / "aleatoria_10000.txt")

    def test_6_1_5_supuestos_path_nombre_desconocido(self):
        sp = _req("taller3.common.dataio", "supuestos_path")
        for bad in ("aleatoria", "concentrado", "Uniforme", ""):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    sp(bad, 10_000)

    def test_6_1_5_load_supuestos(self):
        load = _req("taller3.common.dataio", "load_supuestos")
        _p3_file(self, "digitos16_10000.txt")
        u = load("uniforme", 10_000)
        self.assertEqual(u, _read(config.DATA_DIR / "aleatoria_10000.txt"))
        d16 = load("digitos16", 10_000)                         # sin validar rango de 8 dígitos
        self.assertEqual(d16[:3], DIGITOS16_FIRST3)
        self.assertEqual(len(d16), 10_000)

    def test_6_1_5_load_supuestos_valida_cantidad_y_rango(self):
        load = _req("taller3.common.dataio", "load_supuestos")
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "p3").mkdir()
            (d / "p3" / "rango_pequeno_10.txt").write_text("1\n" * 10, encoding="ascii")
            with self.assertRaises(ValueError):                 # fuera del rango de 8 dígitos
                load("rango_pequeno", 10, d)
            (d / "p3" / "digitos16_10.txt").write_text(f"{10 ** 15}\n" * 9, encoding="ascii")
            with self.assertRaises(ValueError):                 # 9 valores, se esperan 10
                load("digitos16", 10, d)


# ======================================================================================
# 6.1.3 / 6.1.4 Datos reales y manifiesto
# ======================================================================================
class TestDatosP3(unittest.TestCase):
    def test_6_1_3_sha256(self):
        for name, sha in P3_SHA256.items():
            with self.subTest(archivo=name):
                self.assertEqual(_sha(_p3_file(self, name)), sha)

    def test_6_1_3_estadisticas(self):
        for name, (lo, hi, distinct, first3) in P3_STATS.items():
            with self.subTest(archivo=name):
                vals = _read(_p3_file(self, name))
                n = int(name.rsplit("_", 1)[1].split(".")[0])
                self.assertEqual(len(vals), n)
                self.assertEqual((min(vals), max(vals), len(set(vals))), (lo, hi, distinct))
                if first3:
                    self.assertEqual(vals[:3], first3)
                if name.startswith("digitos16"):
                    self.assertEqual(vals[:3], DIGITOS16_FIRST3)

    def test_6_1_2_digitos16_anidados(self):
        big = _read(_p3_file(self, "digitos16_1000000.txt"))
        for n in (10_000, 100_000):
            with self.subTest(n=n):
                self.assertEqual(_read(_p3_file(self, f"digitos16_{n}.txt")), big[:n])

    def test_4_4_3_perfiles_bucket(self):
        bp = _req("taller3.common.compare", "bucket_profile")
        for (dist, n), expected in BUCKET_PROFILES.items():
            with self.subTest(dist=dist, n=n):
                name = f"aleatoria_{n}.txt" if dist == "uniforme" else f"{dist}_{n}.txt"
                path = config.DATA_DIR / name if dist == "uniforme" else _p3_file(self, name)
                self.assertEqual(tuple(bp(_read(path))), expected)

    def test_6_1_4_manifiesto_real(self):
        manifest = json.loads((config.DATA_DIR / "manifest.json").read_text(encoding="utf-8"))
        archivos = manifest["archivos"]
        p2 = importlib.import_module("tests.test_search_protocol")
        for name, sha in p2.DATA_SHA256.items():                # 12 del Punto 1, sin cambios
            with self.subTest(archivo=name):
                self.assertEqual(archivos[name]["sha256"], sha)
        self.assertEqual(archivos["claves_busqueda.txt"]["sha256"], p2.KEYS_SHA256)
        self.assertEqual(len(archivos), 13 + 7)
        for name, sha in P3_SHA256.items():
            with self.subTest(archivo=name):
                key = f"p3/{name}"
                self.assertIn(key, archivos, f"falta la entrada {key} en el manifiesto: {GEN_MSG}")
                _check_manifest_entry(self, name, archivos[key])


def _check_manifest_entry(test: unittest.TestCase, name: str, e: dict) -> None:
    stem = name[:-4]
    dist, n = stem.rsplit("_", 1)
    lo, hi, distinct, _ = P3_STATS[name]
    test.assertEqual(e["n"], int(n))
    test.assertEqual(e["variante"], "supuestos")
    test.assertEqual(e["distribucion"], dist)
    test.assertEqual(e["sha256"], P3_SHA256[name])
    test.assertEqual(e["semilla"], 20261017)
    test.assertEqual(e["parametros"], P3_PARAMETROS.get(stem, P3_PARAMETROS.get(dist)))
    test.assertEqual((e["min"], e["max"], e["valores_distintos"]), (lo, hi, distinct))
    test.assertIn("python", e)
    test.assertIn("creado_utc", e)


class TestGeneracionSupuestos(unittest.TestCase):
    """6.1.3 + 6.1.4 en un directorio temporal: no toca data/ real."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="p3_gen_"))
        cls.original_text = (config.DATA_DIR / "manifest.json").read_text(encoding="utf-8")
        original = json.loads(cls.original_text)
        # el manifiesto de partida es el del Punto 2: sin las entradas p3/
        original["archivos"] = {k: v for k, v in original["archivos"].items()
                                if not k.startswith("p3/")}
        cls.original = original
        (cls.tmp / "manifest.json").write_text(json.dumps(original, indent=2, ensure_ascii=False),
                                               encoding="utf-8")
        cls.error = None
        try:
            gen = _req("taller3.generate_data", "generate_supuestos_data")
            gen(cls.tmp)
        except AssertionError as e:
            cls.error = str(e)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def setUp(self):
        if self.error:
            self.fail(self.error)

    def test_6_1_3_sha256_generados(self):
        for name, sha in P3_SHA256.items():
            with self.subTest(archivo=name):
                self.assertEqual(_sha(self.tmp / "p3" / name), sha)

    def test_6_1_4_entradas_nuevas(self):
        archivos = json.loads((self.tmp / "manifest.json").read_text(encoding="utf-8"))["archivos"]
        for name in P3_SHA256:
            with self.subTest(archivo=name):
                _check_manifest_entry(self, name, archivos[f"p3/{name}"])

    def test_6_1_4_entradas_existentes_sin_cambios(self):
        after = json.loads((self.tmp / "manifest.json").read_text(encoding="utf-8"))
        for k, v in self.original.items():
            if k != "archivos":
                self.assertEqual(after[k], v, f"campo raíz {k} cambió")
        for k, v in self.original["archivos"].items():
            with self.subTest(entrada=k):
                self.assertEqual(after["archivos"][k], v)
        self.assertEqual(set(after["archivos"]) - set(self.original["archivos"]),
                         {f"p3/{name}" for name in P3_SHA256})

    def test_6_1_4_check_supuestos_data(self):
        check = _req("taller3.generate_data", "check_supuestos_data")
        check(self.tmp)                                          # coincide: no lanza
        path = self.tmp / "p3" / "rango_pequeno_10000.txt"
        original = path.read_bytes()
        try:
            path.write_bytes(original.replace(b"1", b"2", 1))
            with self.assertRaises(ValueError):
                check(self.tmp)
        finally:
            path.write_bytes(original)

    def test_6_1_4_data_real_sin_cambios(self):
        self.assertEqual((config.DATA_DIR / "manifest.json").read_text(encoding="utf-8"),
                         self.original_text)


# ======================================================================================
# 6.4 / 7.2 Benchmark: growth, entorno y CSV
# ======================================================================================
class TestBenchSupuestos(unittest.TestCase):
    def test_6_4_supuestos_growth(self):
        growth = _req("taller3.bench_supuestos", "supuestos_growth")
        from taller3.common.estimation import Growth
        expected = {
            ("BucketSort", "uniforme"): Growth.N,
            ("BucketSort", "rango_pequeno"): Growth.N,
            ("BucketSort", "concentrado_extremos"): Growth.N2,
            ("RadixSort", "uniforme"): Growth.N,
            ("RadixSort", "digitos16"): Growth.N,
        }
        for (algo, dist), g in expected.items():
            with self.subTest(algo=algo, dist=dist):
                self.assertIs(growth(algo, dist), g)

    def test_6_4_supuestos_growth_par_invalido(self):
        growth = _req("taller3.bench_supuestos", "supuestos_growth")
        for algo, dist in (("BucketSort", "digitos16"), ("RadixSort", "rango_pequeno"),
                           ("RadixSort", "concentrado_extremos"), ("MergeSort", "uniforme")):
            with self.subTest(algo=algo, dist=dist):
                with self.assertRaises(ValueError):
                    growth(algo, dist)

    def test_7_2_environment_path(self):
        ep = _req("taller3.bench_supuestos", "environment_path")
        self.assertEqual(ep(Path("results/supuestos_python.csv")),
                         Path("results/entorno_supuestos_python.json"))
        self.assertEqual(ep(Path("/tmp/x/prueba_sup.csv")), Path("/tmp/x/entorno_prueba_sup.json"))


class TestSupuestosCsvWriter(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="p3_csv_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_7_2_encabezado_y_filas(self):
        Writer = _req("taller3.common.results", "SupuestosCsvWriter")
        from taller3.common.results import ResultRecord
        path = self.tmp / "sup.csv"
        with Writer(path, 5) as w:
            w.write(ResultRecord("BucketSort", "Python", "aleatoria", 10_000,
                                 reps_ns=[1, 2, 3, 4, 5], promedio_ns=3.0,
                                 desv_estandar_ns=1.5811388), "concentrado_extremos")
            w.write(ResultRecord("RadixSort", "Python", "aleatoria", 1_000_000,
                                 promedio_ns=1234.56, estado="estimado",
                                 causa="predicción 400 s > límite, de 300 s",
                                 base_estimacion="t(100000)=0.1 s x f(1000000)/f(100000) = x10 con f=O(n)"),
                    "digitos16")
        lines = path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], SUPUESTOS_HEADER)
        self.assertEqual(lines[1], "BucketSort,Python,aleatoria,concentrado_extremos,10000,"
                                   "1,2,3,4,5,3.0,1.6,medido,,")
        rows = _load_csv(path)
        self.assertEqual(rows[1]["distribucion"], "digitos16")
        self.assertEqual(rows[1]["rep_1_ns"], "")
        self.assertEqual(rows[1]["promedio_ns"], "1234.6")
        self.assertEqual(rows[1]["desv_estandar_ns"], "")
        self.assertEqual(rows[1]["causa"], "predicción 400 s > límite, de 300 s")


# ======================================================================================
# 4.1 / 7.3 / 8 plot_compare (cálculos, sin matplotlib)
# ======================================================================================
def _real_inputs() -> tuple[dict, dict]:
    ordenamiento, busqueda = {}, {}
    for lang in ("Java", "Python"):
        ordenamiento[lang] = _load_csv(config.RESULTS_DIR / f"ordenamiento_{lang.lower()}.csv")
        busqueda[lang] = _load_csv(config.RESULTS_DIR / f"busqueda_{lang.lower()}.csv")
    return ordenamiento, busqueda


def _per_search(rows: list[dict], algo: str, variante: str) -> float:
    for r in rows:
        if r["algoritmo"] == algo and r["variante"] == variante and r["n"] == "1000000":
            return float(r["promedio_por_busqueda_ns"])
    raise KeyError((algo, variante))


class TestPlotCompare(unittest.TestCase):
    def test_4_1_lower_bound_rows(self):
        rows = _req("taller3.plot_compare", "lower_bound_rows")()
        got = [(r["n"], r["cota_inferior_comparaciones"], round(r["n_log2_n"]), round(r["cociente"], 3))
               for r in rows]
        self.assertEqual(got, [(1_000, 8_530, 9_966, 0.856), (10_000, 118_459, 132_877, 0.891),
                               (100_000, 1_516_705, 1_660_964, 0.913),
                               (1_000_000, 18_488_885, 19_931_569, 0.928)])

    def test_7_3_k_star_filas_con_los_csv_versionados(self):
        k_rows = _req("taller3.plot_compare", "k_star_rows")
        ordenamiento, busqueda = _real_inputs()
        rows = k_rows(ordenamiento, busqueda)
        self.assertEqual([(r["lenguaje"], r["rol"], r["fuente_t_lineal"]) for r in rows], [
            ("Java", "principal", "claves"), ("Java", "banda", "solo_presentes"),
            ("Java", "banda", "solo_ausentes"), ("Python", "principal", "claves"),
            ("Python", "banda", "solo_presentes"), ("Python", "banda", "solo_ausentes"),
            ("Python", "sensibilidad_orden", "claves")])
        for r in rows:
            self.assertEqual(set(r), set(K_STAR_COLUMNS))
        self.assertEqual([r["algoritmo_orden"] for r in rows], ["RadixSort"] * 3 + ["BucketSort"] * 3
                         + ["RadixSort"])
        self.assertEqual([r["t_ord_ns"] for r in rows], [16_087_758.4] * 3 + [457_194_941.8] * 3
                         + [1_775_541_275.0])
        fuente = {"claves": "claves", "solo_presentes": "centro", "solo_ausentes": "final"}
        for r in rows:
            with self.subTest(lenguaje=r["lenguaje"], fuente=r["fuente_t_lineal"]):
                rs = busqueda[r["lenguaje"]]
                t_l = _per_search(rs, "LinearSearch", fuente[r["fuente_t_lineal"]])
                t_b = _per_search(rs, "BinarySearch", "claves")
                self.assertAlmostEqual(r["t_lineal_ns"], t_l, delta=1e-3)
                self.assertAlmostEqual(r["t_binaria_ns"], t_b, delta=1e-3)
                ks = r["t_ord_ns"] / (r["t_lineal_ns"] - r["t_binaria_ns"])
                self.assertAlmostEqual(r["k_estrella"], ks, delta=1e-9 * ks)
                self.assertEqual(r["k_min"], math.floor(ks) + 1)
                self.assertLess(r["k_bajo"], r["k_estrella"])
                self.assertGreater(r["k_alto"], r["k_estrella"])
                self.assertEqual(r["estado"], "medido")

    def test_5_3_sensibilidad_3_8836(self):
        k_rows = _req("taller3.plot_compare", "k_star_rows")
        rows = k_rows(*_real_inputs())
        principal = next(r for r in rows if r["lenguaje"] == "Python" and r["rol"] == "principal")
        sens = next(r for r in rows if r["rol"] == "sensibilidad_orden")
        self.assertEqual(round(sens["k_estrella"] / principal["k_estrella"], 4), 3.8836)

    def _synthetic(self, t_l: dict[str, float], t_b: float = 100.0,
                   estado_l: str = "medido") -> tuple[dict, dict]:
        ordenamiento, busqueda = {}, {}
        for lang in ("Java", "Python"):
            o = []
            for algo, t in (("InsertionSort", 9e9), ("DualPivotQuickSort", 5e6), ("MergeSort", 6e6),
                            ("HeapSort", 7e6), ("RadixSort", 2e6), ("BucketSort", 1e6)):
                o.append({"algoritmo": algo, "lenguaje": lang, "variante": "aleatoria", "n": "1000000",
                          "promedio_ns": str(t), "desv_estandar_ns": "10.0", "estado": "medido"})
            o.append({"algoritmo": "MergeSort", "lenguaje": lang, "variante": "aleatoria", "n": "1000",
                      "promedio_ns": "1.0", "desv_estandar_ns": "0.1", "estado": "medido"})
            b = [{"algoritmo": "BinarySearch", "lenguaje": lang, "variante": "claves", "n": "1000000",
                  "promedio_por_busqueda_ns": str(t_b), "desv_por_busqueda_ns": "1.0", "estado": "medido"}]
            for var, t in t_l.items():
                b.append({"algoritmo": "LinearSearch", "lenguaje": lang, "variante": var, "n": "1000000",
                          "promedio_por_busqueda_ns": str(t), "desv_por_busqueda_ns": "1.0",
                          "estado": estado_l if var == "claves" else "medido"})
            ordenamiento[lang], busqueda[lang] = o, b
        return ordenamiento, busqueda

    def test_7_3_t_ord_principal_elegido_por_codigo_y_estado_estimado(self):
        k_rows = _req("taller3.plot_compare", "k_star_rows")
        rows = k_rows(*self._synthetic({"claves": 7.5e5, "centro": 5e5, "final": 1e6},
                                       estado_l="estimado"))
        principal = [r for r in rows if r["rol"] == "principal"]
        self.assertEqual([r["algoritmo_orden"] for r in principal], ["BucketSort", "BucketSort"])
        self.assertEqual([r["estado"] for r in principal], ["estimado", "estimado"])
        self.assertTrue(all(r["estado"] == "medido" for r in rows if r["rol"] == "banda"))

    def test_7_3_nunca_conviene(self):
        k_rows = _req("taller3.plot_compare", "k_star_rows")
        rows = k_rows(*self._synthetic({"claves": 50.0, "centro": 5e5, "final": 1e6}))
        r = next(r for r in rows if r["lenguaje"] == "Java" and r["rol"] == "principal")
        self.assertEqual(r["estado"], "nunca_conviene")
        for col in ("k_estrella", "k_min", "k_bajo", "k_alto"):
            self.assertIsNone(r[col])

    def test_8_error_si_falta_una_entrada(self):
        k_rows = _req("taller3.plot_compare", "k_star_rows")
        ordenamiento, busqueda = self._synthetic({"claves": 7.5e5, "centro": 5e5})   # falta final
        with self.assertRaises(ValueError):
            k_rows(ordenamiento, busqueda)

    def test_5_2_aviso_si_k_principal_fuera_de_la_banda(self):
        k_rows = _req("taller3.plot_compare", "k_star_rows")
        warn = _req("taller3.plot_compare", "k_star_warnings")
        ok = k_rows(*self._synthetic({"claves": 7.5e5, "centro": 5e5, "final": 1e6}))
        self.assertEqual([w for w in warn(ok) if "banda" in w], [])
        bad = k_rows(*self._synthetic({"claves": 1.2e6, "centro": 5e5, "final": 1e6}))
        msgs = [w for w in warn(bad) if "banda" in w]
        self.assertEqual(len(msgs), 2)                           # Java y Python
        for r in bad:                                            # el aviso muestra los tres k*
            if r["rol"] in ("principal", "banda") and r["lenguaje"] == "Java":
                self.assertIn(f"{r['k_estrella']:.4f}", msgs[0])

    def test_8_aviso_proporcion_lineal(self):
        k_rows = _req("taller3.plot_compare", "k_star_rows")
        warn = _req("taller3.plot_compare", "k_star_warnings")
        ok = k_rows(*self._synthetic({"claves": 7.5e5, "centro": 5e5, "final": 1e6}))
        self.assertEqual(warn(ok), [])
        bad = k_rows(*self._synthetic({"claves": 9e5, "centro": 3e5, "final": 1e6}))
        self.assertTrue(any("claves" in w and "final" in w for w in warn(bad)))
        self.assertTrue(any("centro" in w and "final" in w for w in warn(bad)))

    def _sup_rows(self, lang: str, values: dict[tuple[str, str, int], float]) -> list[dict]:
        return [{"algoritmo": a, "lenguaje": lang, "variante": "aleatoria", "distribucion": d,
                 "n": str(n), "promedio_ns": str(t), "estado": "medido"}
                for (a, d, n), t in values.items()]

    def test_8_avisos_del_experimento_de_supuestos(self):
        warn = _req("taller3.plot_compare", "supuestos_warnings")
        ordenamiento, _ = _real_inputs()

        def p1(lang, algo, n):
            return next(float(r["promedio_ns"]) for r in ordenamiento[lang]
                        if r["algoritmo"] == algo and r["variante"] == "aleatoria" and int(r["n"]) == n)

        good = {}
        for lang in ("Java", "Python"):
            v = {("BucketSort", "uniforme", n): p1(lang, "BucketSort", n) for n in (10_000, 100_000)}
            v[("BucketSort", "concentrado_extremos", 10_000)] = 1e6
            v[("BucketSort", "concentrado_extremos", 100_000)] = 1e8
            if lang == "Python":
                for n in (10_000, 100_000, 1_000_000):
                    v[("RadixSort", "uniforme", n)] = p1(lang, "RadixSort", n)
                    v[("RadixSort", "digitos16", n)] = 2.4 * p1(lang, "RadixSort", n)
            good[lang] = self._sup_rows(lang, v)
        self.assertEqual(warn(good, ordenamiento), [])

        bad = {lang: [dict(r) for r in rows] for lang, rows in good.items()}
        for r in bad["Java"]:
            if r["distribucion"] == "concentrado_extremos" and r["n"] == "100000":
                r["promedio_ns"] = "3e7"                         # razón 30 < 50
            if r["distribucion"] == "uniforme" and r["n"] == "10000":
                r["promedio_ns"] = str(float(r["promedio_ns"]) * 1.5)   # +50 % vs P1
        for r in bad["Python"]:
            if r["distribucion"] == "digitos16" and r["n"] == "100000":
                r["promedio_ns"] = str(float(r["promedio_ns"]) / 2.4 * 4.0)   # razón 4 > 3,5
        msgs = warn(bad, ordenamiento)
        self.assertEqual(len(msgs), 3, msgs)
        self.assertTrue(any("concentrado_extremos" in m and "Java" in m for m in msgs))
        self.assertTrue(any("digitos16" in m and "Python" in m for m in msgs))
        self.assertTrue(any("uniforme" in m and "Java" in m for m in msgs))


if __name__ == "__main__":
    unittest.main()
