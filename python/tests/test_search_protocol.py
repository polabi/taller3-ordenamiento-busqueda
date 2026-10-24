"""
Pruebas del PROTOCOLO del Punto 2 (claves, lectura, medición, CSV, entorno). No miden
tiempos reales ni corren el benchmark.

    cd python
    python3 -m unittest tests.test_search_protocol -v

Fuente de los valores esperados: specs/p2-busqueda.md, secciones 6 y 7 (APROBADAS el
2026-10-22). Cada prueba lleva en el nombre la sección de la spec que cubre.

Reglas de estas pruebas:
- NUNCA escriben en data/ real: la generación de claves se hace en un directorio temporal
  con copias de aleatoria_1000.txt, aleatoria_1000000.txt y manifest.json. Una guarda
  comprueba al final que data/ real no cambió (y lo restaura si cambió, fallando).
- Los valores esperados (SHA-256, primeras claves, mín/máx, 12 SHA del manifiesto) vienen
  de la spec y del manifiesto versionado en git, no de ejecutar el código del repo.
- Las funciones aún no implementadas se importan dentro de cada prueba con _req(): si
  faltan, la prueba FALLA con el nombre de lo que hay que implementar (no da error de
  importación del módulo entero).

Contrato que fijan estas pruebas (además de las firmas explícitas de la spec 6.1.6 y 6.3):
- generate_data.generate_search_keys(data_dir: Path = config.DATA_DIR) -> list[int]
  (6.1.1 + 6.1.5: verifica SHA de entradas, genera, escribe y actualiza el manifiesto;
  ValueError si un SHA de entrada no coincide o el pool tiene repetidos, sin escribir nada).
- generate_data.check_search_keys(data_dir: Path = config.DATA_DIR) -> None
  (6.1.5 paso 2: ValueError si el SHA de claves_busqueda.txt no coincide con el manifiesto).
- bench_search.position_index(variante, n) -> int; ValueError si la variante no existe.
- bench_search.environment_path(out: Path) -> Path = out.with_name(f"entorno_{out.stem}.json").
- common.results.SearchResultRecord (dataclass) + SearchCsvWriter(path, repetitions);
  el escritor calcula las columnas por búsqueda = promedio/desv ÷ num_busquedas.
"""
from __future__ import annotations

import csv
import gc
import hashlib
import importlib
import json
import platform
import shutil
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest import mock

from taller3 import config

# --- Constantes de la spec -----------------------------------------------------------
KEYS_SHA256 = "22fdc47fbcdd3e4b4d26fbcd3eae5010bb3becaa981337c9fe9fa41aaa0c965f"   # 6.1.1
FIRST_5_KEYS = [40_484_834, 85_052_552, 51_204_555, 22_281_363, 16_722_397]       # 6.1.1
KEYS_MIN, KEYS_MAX = 10_070_741, 99_952_252                                        # 6.1.1

# Los 12 SHA-256 versionados (git show HEAD:data/manifest.json). 6.1.5: deben quedar
# con el mismo valor tras generar las claves.
DATA_SHA256 = {
    "aleatoria_1000.txt": "f8e4ccf06a8cd3b062044adc6ec31091136e58b8bb6bb5f8a2c883e9796ef01d",
    "ascendente_1000.txt": "279db487604be9a40da73ac7c7017f6f78f2301ba5da9c2bdf64ef280464de5a",
    "descendente_1000.txt": "26785da0f20e880aa9ea8a3fa95d116fab37cd987604d727a25f53460c39d5dd",
    "aleatoria_10000.txt": "836e336a052c979bdaa474dc583378efce15cbb4e8808869f73ab128f7aac040",
    "ascendente_10000.txt": "ad17487b35aca20d0697d0e1a0aaf524153501a6e36be35d37e9ba70af687418",
    "descendente_10000.txt": "131f170d4734c6abef57cfb4ffad49b90631b8f898ff3866666ecef97b3689a3",
    "aleatoria_100000.txt": "9f3b04e6f1a3ec1d6b01495c968036ba9d5bb81569f46c766018f5cc5336e884",
    "ascendente_100000.txt": "9cbf0b330dcf075b24fef926bc11770204d83415b15a1f38d11de54f1191ba77",
    "descendente_100000.txt": "68c77809b0171f000c836e49938edc3324670505a75543f423f2b512c7f34a4e",
    "aleatoria_1000000.txt": "89cc83d9bbd6c4f29e537c9962819fba024596fec42688835aa4f9d348cd8b85",
    "ascendente_1000000.txt": "4fc2f41e0018e569cba5e2965011ebfa7bcf13144c287ae5341f001bbbfbf695",
    "descendente_1000000.txt": "289eed29de4b939ee635448d6444977d684b7831aa879641f8b0f3530e78c3f9",
}

NEW_MANIFEST_ENTRY_FIXED = {                                                       # 6.1.5
    "n": 1000,
    "variante": "claves_busqueda",
    "sha256": KEYS_SHA256,
    "semilla": 20261016,
    "presentes": 500,
    "ausentes": 500,
    "origen_presentes": "rng.sample(aleatoria_1000.txt, 500)",
    "origen_ausentes": "randint(MIN, MAX) con rechazo si está en aleatoria_1000000.txt o repetida",
    "orden": "presentes + ausentes, luego rng.shuffle",
}

CSV_HEADER = (                                                                     # 7.2
    "algoritmo,lenguaje,variante,n,num_busquedas,clave,rep_1_ns,rep_2_ns,rep_3_ns,rep_4_ns,"
    "rep_5_ns,promedio_ns,desv_estandar_ns,promedio_por_busqueda_ns,desv_por_busqueda_ns,"
    "encontradas,checksum,estado,causa,base_estimacion"
)
P1_CSV_HEADER = (
    "algoritmo,lenguaje,variante,n,rep_1_ns,rep_2_ns,rep_3_ns,rep_4_ns,rep_5_ns,"
    "promedio_ns,desv_estandar_ns,estado,causa,base_estimacion"
)


def _req(module: str, attr: str | None = None):
    """Importa algo que la spec exige; si falta, la prueba FALLA diciendo qué implementar."""
    try:
        m = importlib.import_module(module)
    except ImportError as e:
        raise AssertionError(f"Falta implementar el módulo {module} (spec p2): {e}") from None
    if attr is None:
        return m
    if not hasattr(m, attr):
        raise AssertionError(f"Falta implementar {module}.{attr} (spec p2)")
    return getattr(m, attr)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read(path: Path) -> list[int]:
    return [int(line) for line in path.read_text(encoding="ascii").splitlines()]


def _copy_inputs(dst: Path) -> None:
    for name in ("aleatoria_1000.txt", "aleatoria_1000000.txt", "manifest.json"):
        shutil.copyfile(config.DATA_DIR / name, dst / name)


# ======================================================================================
# 7.1 Constantes de config.py
# ======================================================================================
class TestConfigBusqueda(unittest.TestCase):
    def test_7_1_constantes_config(self):
        expected = {
            "SEARCH_KEYS_FILE": "claves_busqueda.txt",
            "SEARCH_KEYS_SEED": 20261016,
            "NUM_SEARCH_KEYS": 1000,
            "NUM_PRESENT_KEYS": 500,
            "POSITION_N": 1_000_000,
            "POSITION_VARIANTS": ("inicio", "centro", "centro_alto", "final"),
            "SEARCH_VARIANTS": ("claves", "inicio", "centro", "centro_alto", "final"),
        }
        for name, value in expected.items():
            with self.subTest(constante=name):
                self.assertTrue(hasattr(config, name), f"Falta config.{name}")
                self.assertEqual(getattr(config, name), value)

    def test_7_1_semilla_claves_independiente_de_SEED(self):
        self.assertNotEqual(getattr(config, "SEARCH_KEYS_SEED", config.SEED), config.SEED)

    def test_6_5_growth_nuevos_miembros(self):
        from taller3.common.estimation import Growth
        self.assertAlmostEqual(Growth.LOGN.f(1024), 10.0)
        self.assertAlmostEqual(Growth.SQRTN.f(1_000_000), 1000.0)
        self.assertAlmostEqual(Growth.LOGLOGN.f(65536), 4.0)      # log2(log2(2^16)) = log2 16
        self.assertEqual(Growth.N.f(1000), 1000.0)                # Punto 1 sin cambios


# ======================================================================================
# 6.1.1 / 6.1.2 / 6.1.5 Generación de claves (en directorio temporal)
# ======================================================================================
class TestGeneracionClaves(unittest.TestCase):
    """Se genera UNA vez (setUpClass) en un directorio temporal y cada prueba revisa algo."""

    @classmethod
    def setUpClass(cls):
        # Guarda: estado de data/ real antes de la prueba.
        cls.real_manifest = (config.DATA_DIR / "manifest.json").read_bytes()
        cls.real_keys_path = config.DATA_DIR / "claves_busqueda.txt"
        cls.real_keys_before = cls.real_keys_path.read_bytes() if cls.real_keys_path.exists() else None

        cls.tmp = Path(tempfile.mkdtemp(prefix="p2_claves_"))
        _copy_inputs(cls.tmp)
        # 6.1.5: se parte de un manifiesto "del Punto 1". El real versionado ya trae la
        # entrada claves_busqueda.txt (la spec manda agregarla), así que se quita de la copia
        # en tmp antes de generar; se guarda aparte para compararla con la que se genere.
        # (La entrada no añade campos raíz derivados: solo vive en archivos[...].)
        tmp_manifest = json.loads((cls.tmp / "manifest.json").read_text(encoding="utf-8"))
        cls.real_keys_entry = tmp_manifest["archivos"].pop("claves_busqueda.txt", None)
        # Las entradas "p3/..." del Punto 3 (spec p3 6.1.4) tampoco son parte del punto de partida.
        for name in [k for k in tmp_manifest["archivos"] if k.startswith("p3/")]:
            del tmp_manifest["archivos"][name]
        (cls.tmp / "manifest.json").write_text(
            json.dumps(tmp_manifest, indent=2, ensure_ascii=False), encoding="utf-8")
        cls.manifest_before = json.loads((cls.tmp / "manifest.json").read_text(encoding="utf-8"))
        cls.returned = None
        cls.error = None
        try:
            gen = _req("taller3.generate_data", "generate_search_keys")
            cls.returned = gen(cls.tmp)
        except Exception as e:          # se reporta en cada prueba que lo necesite
            cls.error = e
        cls.keys_path = cls.tmp / "claves_busqueda.txt"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)
        # Si la implementación escribió en data/ real, se restaura (y la prueba de abajo falla).
        if (config.DATA_DIR / "manifest.json").read_bytes() != cls.real_manifest:
            (config.DATA_DIR / "manifest.json").write_bytes(cls.real_manifest)
        if cls.real_keys_before is None and cls.real_keys_path.exists():
            cls.real_keys_path.unlink()

    def _generated(self) -> list[int]:
        if self.error is not None:
            self.fail(f"generate_search_keys(tmp) falló: {self.error!r}")
        self.assertTrue(self.keys_path.exists(), "no se escribió claves_busqueda.txt en data_dir")
        return _read(self.keys_path)

    def test_6_1_5_no_escribe_en_data_real(self):
        self.assertEqual((config.DATA_DIR / "manifest.json").read_bytes(), self.real_manifest,
                         "generate_search_keys(tmp) modificó data/manifest.json real")
        now = self.real_keys_path.read_bytes() if self.real_keys_path.exists() else None
        self.assertEqual(now, self.real_keys_before,
                         "generate_search_keys(tmp) escribió data/claves_busqueda.txt real")

    def test_6_1_1_sha256_claves(self):
        self._generated()
        self.assertEqual(_sha(self.keys_path), KEYS_SHA256,
                         "SHA-256 distinto: la implementación no sigue el pseudocódigo de 6.1.1 "
                         "(¿muestreó de un set, ordenó el pool o cambió el orden del RNG?)")

    def test_6_1_1_primeras_5_min_max(self):
        keys = self._generated()
        self.assertEqual(keys[:5], FIRST_5_KEYS)
        self.assertEqual(min(keys), KEYS_MIN)
        self.assertEqual(max(keys), KEYS_MAX)

    def test_6_1_1_formato_archivo(self):
        keys = self._generated()
        raw = self.keys_path.read_bytes()
        self.assertEqual(len(keys), 1000)
        self.assertEqual(raw, "".join(f"{k}\n" for k in keys).encode("ascii"),
                         "formato: un entero por línea, ASCII, '\\n' al final de cada línea, sin encabezado")

    def test_6_1_1_retorna_las_claves_en_orden_del_archivo(self):
        keys = self._generated()
        self.assertEqual(list(self.returned), keys)

    def test_6_1_2_sin_repetidas(self):
        keys = self._generated()
        self.assertEqual(len(set(keys)), 1000)

    def test_6_1_1_500_presentes_de_aleatoria_1000_y_500_ausentes_de_1e6(self):
        keys = self._generated()
        pool = set(_read(self.tmp / "aleatoria_1000.txt"))
        big = set(_read(self.tmp / "aleatoria_1000000.txt"))
        present = [k for k in keys if k in pool]
        absent = [k for k in keys if k not in big]
        self.assertEqual(len(present), 500)
        self.assertEqual(len(absent), 500)
        self.assertTrue(all(config.MIN_VALUE <= k <= config.MAX_VALUE for k in keys))

    def test_6_1_1_barajadas(self):
        # D2: si no se barajara, las 500 primeras serían todas presentes.
        keys = self._generated()
        pool = set(_read(self.tmp / "aleatoria_1000.txt"))
        self.assertLess(sum(k in pool for k in keys[:500]), 500)

    def test_6_1_5_manifest_conserva_entradas_existentes(self):
        self._generated()
        after = json.loads((self.tmp / "manifest.json").read_text(encoding="utf-8"))
        for key, value in self.manifest_before.items():
            if key == "archivos":
                continue
            with self.subTest(campo=key):
                self.assertEqual(after.get(key), value, f"cambió el campo raíz {key!r}")
        for name, entry in self.manifest_before["archivos"].items():
            with self.subTest(archivo=name):
                self.assertEqual(after["archivos"].get(name), entry, f"cambió la entrada {name}")
        self.assertEqual(set(after["archivos"]) - set(self.manifest_before["archivos"]),
                         {"claves_busqueda.txt"}, "solo se agrega la entrada claves_busqueda.txt")

    def test_6_1_5_manifest_parte_del_punto1(self):
        # Guarda del propio setUpClass: el manifiesto de partida tiene exactamente los 12
        # archivos del Punto 1 (si no, la prueba de "solo se agrega una entrada" no dice nada).
        self.assertEqual(set(self.manifest_before["archivos"]), set(DATA_SHA256))

    def test_6_1_5_entrada_generada_igual_a_la_versionada(self):
        # La entrada que se genera en tmp coincide con la del data/manifest.json real
        # (mismo SHA 22fdc47f..., mismos campos), salvo creado_utc. 'python' solo se compara
        # si la corrida usa la misma versión con la que se versionó (si no, ver entrada_nueva).
        self._generated()
        self.assertIsNotNone(self.real_keys_entry,
                             "data/manifest.json real no tiene archivos['claves_busqueda.txt'] (6.1.5)")
        after = json.loads((self.tmp / "manifest.json").read_text(encoding="utf-8"))
        entry = after["archivos"].get("claves_busqueda.txt")
        self.assertIsNotNone(entry, "falta archivos['claves_busqueda.txt'] en el manifiesto")
        self.assertEqual(self.real_keys_entry["sha256"], KEYS_SHA256)
        self.assertEqual(set(entry), set(self.real_keys_entry), "campos distintos a los versionados")
        for k, v in self.real_keys_entry.items():
            if k == "creado_utc":
                continue
            if k == "python" and v != platform.python_version():
                continue
            with self.subTest(campo=k):
                self.assertEqual(entry[k], v)

    def test_6_1_5_manifest_12_hashes_intactos(self):
        self._generated()
        after = json.loads((self.tmp / "manifest.json").read_text(encoding="utf-8"))
        for name, sha in DATA_SHA256.items():
            with self.subTest(archivo=name):
                self.assertEqual(after["archivos"][name]["sha256"], sha)

    def test_6_1_5_entrada_nueva_manifest(self):
        self._generated()
        after = json.loads((self.tmp / "manifest.json").read_text(encoding="utf-8"))
        entry = after["archivos"].get("claves_busqueda.txt")
        self.assertIsNotNone(entry, "falta archivos['claves_busqueda.txt'] en el manifiesto")
        for k, v in NEW_MANIFEST_ENTRY_FIXED.items():
            with self.subTest(campo=k):
                self.assertEqual(entry.get(k), v)
        self.assertIsInstance(entry.get("python"), str)
        self.assertTrue(entry["python"].startswith(platform.python_version()),
                        "'python' debe ser la versión de la corrida")
        datetime.fromisoformat(entry["creado_utc"])     # fecha ISO válida

    def test_6_1_5_check_search_keys_acepta_archivo_correcto(self):
        self._generated()
        check = _req("taller3.generate_data", "check_search_keys")
        check(self.tmp)                                 # no debe lanzar

    def test_6_1_5_check_search_keys_falla_si_el_sha_no_coincide(self):
        self._generated()
        check = _req("taller3.generate_data", "check_search_keys")
        bad = Path(tempfile.mkdtemp(prefix="p2_claves_bad_"))
        try:
            shutil.copyfile(self.tmp / "manifest.json", bad / "manifest.json")
            keys = _read(self.keys_path)
            keys[0], keys[1] = keys[1], keys[0]           # mismo contenido, otro orden
            (bad / "claves_busqueda.txt").write_text("".join(f"{k}\n" for k in keys), encoding="ascii")
            with self.assertRaises(ValueError):
                check(bad)
        finally:
            shutil.rmtree(bad, ignore_errors=True)


class TestGeneracionClavesFallos(unittest.TestCase):
    """6.1.5: si un SHA de entrada no coincide (o el pool tiene repetidos), falla SIN escribir."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="p2_claves_fallo_"))
        _copy_inputs(self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _assert_fails_without_writing(self):
        gen = _req("taller3.generate_data", "generate_search_keys")
        manifest_bytes = (self.tmp / "manifest.json").read_bytes()
        with self.assertRaises(ValueError):
            gen(self.tmp)
        self.assertFalse((self.tmp / "claves_busqueda.txt").exists(), "escribió claves pese al fallo")
        self.assertEqual((self.tmp / "manifest.json").read_bytes(), manifest_bytes,
                         "modificó el manifiesto pese al fallo")

    def _set_manifest_sha(self, name: str, sha: str):
        m = json.loads((self.tmp / "manifest.json").read_text(encoding="utf-8"))
        m["archivos"][name]["sha256"] = sha
        (self.tmp / "manifest.json").write_text(json.dumps(m, indent=2, ensure_ascii=False),
                                                encoding="utf-8")

    def test_6_1_5_sha_de_aleatoria_1000_no_coincide(self):
        self._set_manifest_sha("aleatoria_1000.txt", "0" * 64)
        self._assert_fails_without_writing()

    def test_6_1_5_sha_de_aleatoria_1000000_no_coincide(self):
        self._set_manifest_sha("aleatoria_1000000.txt", "0" * 64)
        self._assert_fails_without_writing()

    def test_6_1_1_pool_con_repetidos_falla(self):
        # aleatoria_1000 con un valor repetido pero con su SHA actualizado en el manifiesto:
        # pasa la comprobación de SHA y debe fallar en assert len(set(pool)) == 1000.
        pool = _read(self.tmp / "aleatoria_1000.txt")
        pool[1] = pool[0]
        (self.tmp / "aleatoria_1000.txt").write_text("".join(f"{v}\n" for v in pool), encoding="ascii")
        self._set_manifest_sha("aleatoria_1000.txt", _sha(self.tmp / "aleatoria_1000.txt"))
        self._assert_fails_without_writing()


class TestManifestReal(unittest.TestCase):
    """No regresión sobre data/ real (solo lectura)."""

    def test_6_1_5_manifest_real_conserva_12_hashes(self):
        m = json.loads((config.DATA_DIR / "manifest.json").read_text(encoding="utf-8"))
        for name, sha in DATA_SHA256.items():
            with self.subTest(archivo=name):
                self.assertEqual(m["archivos"][name]["sha256"], sha)


# ======================================================================================
# 6.1.6 Lectura de claves
# ======================================================================================
class TestLecturaClaves(unittest.TestCase):
    VALID = [config.MIN_VALUE + 7 * i for i in range(1000)][::-1]    # 1.000 distintas, en rango

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="p2_lectura_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, values):
        (self.tmp / "claves_busqueda.txt").write_text("".join(f"{v}\n" for v in values), encoding="ascii")

    def test_6_1_6_search_keys_path(self):
        path_fn = _req("taller3.common.dataio", "search_keys_path")
        self.assertEqual(path_fn(self.tmp), self.tmp / "claves_busqueda.txt")
        self.assertEqual(path_fn(), config.DATA_DIR / "claves_busqueda.txt")

    def test_6_1_6_load_valido_conserva_orden(self):
        load = _req("taller3.common.dataio", "load_search_keys")
        self._write(self.VALID)
        self.assertEqual(load(self.tmp), self.VALID)

    def test_6_1_6_load_repetidas_valueerror(self):
        load = _req("taller3.common.dataio", "load_search_keys")
        vals = list(self.VALID)
        vals[999] = vals[0]
        self._write(vals)
        with self.assertRaises(ValueError):
            load(self.tmp)

    def test_6_1_6_load_cantidad_incorrecta_valueerror(self):
        load = _req("taller3.common.dataio", "load_search_keys")
        for count in (999, 1001):
            with self.subTest(cantidad=count):
                vals = [config.MIN_VALUE + 7 * i for i in range(count)]
                self._write(vals)
                with self.assertRaises(ValueError):
                    load(self.tmp)

    def test_6_1_6_load_fuera_de_rango_valueerror(self):
        load = _req("taller3.common.dataio", "load_search_keys")
        for bad in (config.MIN_VALUE - 1, config.MAX_VALUE + 1):
            with self.subTest(valor=bad):
                vals = list(self.VALID)
                vals[500] = bad
                self._write(vals)
                with self.assertRaises(ValueError):
                    load(self.tmp)

    def test_6_1_6_load_archivo_inexistente(self):
        load = _req("taller3.common.dataio", "load_search_keys")
        with self.assertRaises(FileNotFoundError):
            load(self.tmp)


# ======================================================================================
# 6.3 Región medida: time_searches
# ======================================================================================
class TestTimeSearches(unittest.TestCase):
    ARR = [10, 20, 30, 40, 50]
    KEYS = [30, 5, 50, 10, 99, 40]

    @staticmethod
    def _oracle(arr, x):
        return arr.index(x) if x in arr else -1

    def test_6_3_llena_out_en_orden_y_devuelve_int(self):
        ts = _req("taller3.common.timing", "time_searches")
        arr = list(self.ARR)
        out = [None] * len(self.KEYS)
        out_id = id(out)
        calls = []

        def func(a, x):
            calls.append(x)
            return self._oracle(a, x)

        ns = ts(func, arr, list(self.KEYS), out)
        self.assertIsInstance(ns, int)
        self.assertGreaterEqual(ns, 0)
        self.assertEqual(id(out), out_id)
        self.assertEqual(out, [2, -1, 4, 0, -1, 3], "out[j] = search(arr, keys[j])")
        self.assertEqual(calls, self.KEYS, "una llamada por clave, en orden j = 0..K-1")
        self.assertEqual(arr, self.ARR, "no copia ni modifica arr")

    def test_6_3_reloj_perf_counter_ns_solo_alrededor_del_ciclo(self):
        ts = _req("taller3.common.timing", "time_searches")
        events = []
        ticks = iter([1_000_000, 1_000_777] + list(range(2_000_000, 2_000_100)))

        def fake_clock():
            events.append("reloj")
            return next(ticks)

        def func(a, x):
            events.append("busqueda")
            return -1

        out = [None] * 3
        with mock.patch("time.perf_counter_ns", fake_clock):
            ns = ts(func, [1, 2, 3], [7, 8, 9], out)
        self.assertEqual(events, ["reloj", "busqueda", "busqueda", "busqueda", "reloj"],
                         "dos lecturas del reloj: t0 antes de la 1.ª búsqueda y t1 después de la última")
        self.assertEqual(ns, 777)

    def test_6_3_gc_collect_antes_y_desactivado_durante(self):
        ts = _req("taller3.common.timing", "time_searches")
        events = []
        real_collect = gc.collect

        def spy_collect(*a, **k):
            events.append("collect")
            return real_collect(*a, **k)

        def func(a, x):
            events.append(("gc_activo", gc.isenabled()))
            return -1

        self.assertTrue(gc.isenabled())
        with mock.patch("gc.collect", spy_collect):
            ts(func, [1], [5, 6], [None, None])
        self.assertIn("collect", events)
        self.assertLess(events.index("collect"), events.index(("gc_activo", False)),
                        "gc.collect() antes de medir")
        self.assertNotIn(("gc_activo", True), events, "gc debe estar desactivado durante la medición")
        self.assertTrue(gc.isenabled(), "gc se reactiva al terminar")

    def test_6_3_gc_se_reactiva_si_la_busqueda_lanza(self):
        ts = _req("taller3.common.timing", "time_searches")

        def boom(a, x):
            raise RuntimeError("falla de prueba")

        with self.assertRaises(RuntimeError):
            ts(boom, [1], [1], [None])
        self.assertTrue(gc.isenabled(), "como time_inplace: gc se reactiva aunque falle")


# ======================================================================================
# 6.2 position_index y 7.2 nombre del entorno (bench_search.py)
# ======================================================================================
class TestBenchSearchFunciones(unittest.TestCase):
    def test_6_2_position_index_n_1e6(self):
        pi = _req("taller3.bench_search", "position_index")
        n = 1_000_000
        self.assertEqual(pi("inicio", n), 0)
        self.assertEqual(pi("centro", n), 499_999)
        self.assertEqual(pi("centro_alto", n), 500_000)
        self.assertEqual(pi("final", n), 999_999)

    def test_6_2_position_index_n_impar_y_pequeno(self):
        pi = _req("taller3.bench_search", "position_index")
        self.assertEqual([pi(v, 1000) for v in config.POSITION_VARIANTS], [0, 499, 500, 999])
        self.assertEqual([pi(v, 7) for v in ("inicio", "centro", "centro_alto", "final")], [0, 3, 3, 6])

    def test_6_2_position_index_variante_desconocida(self):
        pi = _req("taller3.bench_search", "position_index")
        for bad in ("claves", "medio", "Centro", ""):
            with self.subTest(variante=bad):
                with self.assertRaises(ValueError):
                    pi(bad, 1_000_000)

    def test_6_2_claves_de_posicion_en_datos_reales(self):
        # Valores de la tabla de 6.2 (usa position_index sobre ascendente_1000000 real).
        pi = _req("taller3.bench_search", "position_index")
        from taller3.common.dataio import dataset_path, read_ints
        arr = read_ints(dataset_path("ascendente", 1_000_000), 1_000_000)
        expected = {"inicio": 10_000_033, "centro": 54_951_725,
                    "centro_alto": 54_951_967, "final": 99_999_964}
        for v, key in expected.items():
            with self.subTest(variante=v):
                self.assertEqual(arr[pi(v, len(arr))], key)
                self.assertEqual(arr.count(key), 1, "las 4 claves de posición son únicas (6.2)")

    def test_7_2_entorno_por_defecto(self):
        ep = _req("taller3.bench_search", "environment_path")
        out = config.RESULTS_DIR / "busqueda_python.csv"
        self.assertEqual(ep(out), config.RESULTS_DIR / "entorno_busqueda_python.json")
        self.assertNotEqual(ep(out).name, "entorno_python.json", "no pisa el entorno del Punto 1")

    def test_7_2_entorno_con_out(self):
        ep = _req("taller3.bench_search", "environment_path")
        self.assertEqual(ep(Path("/tmp/x/prueba_busq.csv")), Path("/tmp/x/entorno_prueba_busq.json"))


# ======================================================================================
# 7.2 CSV de búsqueda (escritor nuevo) y no regresión del escritor del Punto 1
# ======================================================================================
class TestSearchCsvWriter(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="p2_csv_"))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _classes(self):
        return (_req("taller3.common.results", "SearchResultRecord"),
                _req("taller3.common.results", "SearchCsvWriter"))

    def test_7_2_encabezado_exacto(self):
        _, W = self._classes()
        path = self.tmp / "b.csv"
        with W(path):
            pass
        self.assertEqual(path.read_text(encoding="utf-8").splitlines()[0], CSV_HEADER)

    def test_7_2_fila_claves_medida(self):
        R, W = self._classes()
        path = self.tmp / "b.csv"
        rec = R(algoritmo="BinarySearch", lenguaje="Python", variante="claves", n=1000,
                num_busquedas=1000, clave=None, reps_ns=[1_000_000, 1_100_000, 1_200_000, 1_300_000, 1_400_000],
                promedio_ns=1_234_567.89, desv_estandar_ns=158_113.883, encontradas=500,
                checksum=249_971, estado="medido", causa="", base_estimacion="")
        with W(path) as w:
            w.write(rec)
            # 7.2: fila escrita y vaciada al terminar cada caso (antes de cerrar).
            self.assertEqual(len(path.read_text(encoding="utf-8").splitlines()), 2,
                             "la fila debe vaciarse a disco al escribirse")
        row = path.read_text(encoding="utf-8").splitlines()[1]
        self.assertEqual(row, "BinarySearch,Python,claves,1000,1000,,1000000,1100000,1200000,1300000,1400000,"
                              "1234567.9,158113.9,1234.568,158.114,500,249971,medido,,")

    def test_7_2_fila_posicion_con_clave(self):
        R, W = self._classes()
        path = self.tmp / "b.csv"
        rec = R(algoritmo="LinearSearch", lenguaje="Python", variante="final", n=1_000_000,
                num_busquedas=1000, clave=99_999_964, reps_ns=[5, 5, 5, 5, 5],
                promedio_ns=5.0, desv_estandar_ns=0.0, encontradas=1000,
                checksum=999_999_000, estado="medido", causa="", base_estimacion="")
        with W(path) as w:
            w.write(rec)
        row = path.read_text(encoding="utf-8").splitlines()[1]
        self.assertEqual(row, "LinearSearch,Python,final,1000000,1000,99999964,5,5,5,5,5,"
                              "5.0,0.0,0.005,0.000,1000,999999000,medido,,")

    def test_7_2_fila_estimada(self):
        R, W = self._classes()
        path = self.tmp / "b.csv"
        rec = R(algoritmo="LinearSearch", lenguaje="Python", variante="claves", n=1_000_000,
                num_busquedas=1000, clave=None, reps_ns=[], promedio_ns=4.0e11, desv_estandar_ns=None,
                encontradas=None, checksum=None, estado="estimado",
                causa="predicción 400.0 s > límite 300 s",
                base_estimacion="t(100000)=40.0 s x f(1000000)/f(100000) = x10 con f=O(n)")
        with W(path) as w:
            w.write(rec)
        with open(path, encoding="utf-8", newline="") as f:
            rows = list(csv.reader(f))
        self.assertEqual(len(rows[1]), 20)
        r = dict(zip(rows[0], rows[1]))
        for c in ("clave", "rep_1_ns", "rep_5_ns", "desv_estandar_ns", "desv_por_busqueda_ns",
                  "encontradas", "checksum"):
            with self.subTest(columna=c):
                self.assertEqual(r[c], "")
        self.assertEqual(r["promedio_ns"], "400000000000.0")
        self.assertEqual(r["promedio_por_busqueda_ns"], "400000000.000")
        self.assertEqual(r["estado"], "estimado")
        self.assertEqual(r["causa"], "predicción 400.0 s > límite 300 s")
        self.assertEqual(r["base_estimacion"], "t(100000)=40.0 s x f(1000000)/f(100000) = x10 con f=O(n)")

    def test_7_2_checksum_negativo_y_grande(self):
        # Σ out incluye los -1: puede ser negativo; en n = 10^6 supera 2^31.
        R, W = self._classes()
        path = self.tmp / "b.csv"
        with W(path) as w:
            w.write(R(algoritmo="LinearSearch", lenguaje="Python", variante="claves", n=1000,
                      num_busquedas=1000, clave=None, reps_ns=[1, 1, 1, 1, 1], promedio_ns=1.0,
                      desv_estandar_ns=0.0, encontradas=0, checksum=-1000, estado="medido",
                      causa="", base_estimacion=""))
            w.write(R(algoritmo="LinearSearch", lenguaje="Python", variante="final", n=1_000_000,
                      num_busquedas=1000, clave=99_999_964, reps_ns=[1, 1, 1, 1, 1], promedio_ns=1.0,
                      desv_estandar_ns=0.0, encontradas=1000, checksum=248_439_213_000, estado="medido",
                      causa="", base_estimacion=""))
        with open(path, encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        self.assertEqual(rows[0]["checksum"], "-1000")
        self.assertEqual(rows[1]["checksum"], "248439213000")

    def test_7_1_escritor_punto1_sin_cambios(self):
        from taller3.common.results import CsvResultWriter, ResultRecord
        path = self.tmp / "p1.csv"
        with CsvResultWriter(path) as w:
            w.write(ResultRecord("MergeSort", "Python", "aleatoria", 1000, [1, 2, 3, 4, 5], 3.0, 1.58113883,
                                 "medido", "", ""))
        lines = path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(lines[0], P1_CSV_HEADER)
        self.assertEqual(lines[1], "MergeSort,Python,aleatoria,1000,1,2,3,4,5,3.0,1.6,medido,,")


if __name__ == "__main__":
    unittest.main()
