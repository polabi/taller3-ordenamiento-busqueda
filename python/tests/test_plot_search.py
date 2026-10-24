"""
Pruebas de las comprobaciones de plot_search.py (Punto 2): equivalencia Java <-> Python
(spec §8.3, con la tabla de control de §6.3) y avisos de plausibilidad (spec §8.4).
No grafican, no leen results/ ni corren benchmarks: usan filas sintéticas.

    cd python
    python3 -m unittest tests.test_plot_search -v

Fuente de los valores esperados: specs/p2-busqueda.md §6.3 (checksums de control), §7.2
(columnas del CSV), §8.3 y §8.4 (APROBADAS el 2026-10-22). Cada prueba lleva en el nombre
la sección que cubre.

Firmas fijadas por estas pruebas (aprobadas por el estudiante el 2026-10-22):

- taller3.plot_search.check_equivalence(rows_java, rows_python) -> list[str]
    rows_*: list[dict[str, str]], filas de un CSV de §7.2 tal como las da csv.DictReader.
    * LANZA ValueError si, para algún (algoritmo, variante, n) con estado = medido en
      AMBOS, difieren `checksum` o `encontradas`. El mensaje lista TODAS las diferencias
      (cada una con algoritmo, variante y n).
    * Si no lanza, DEVUELVE la lista de avisos (vacía si todo cuadra):
      - un aviso por cada caso omitido porque está `estimado` en algún lenguaje;
      - un aviso por cada fila medida cuyo checksum/encontradas difiere de la tabla de
        control de §6.3 (claves: tabla por n y algoritmo, encontradas = 500; posiciones
        en n = 10^6: checksum = 1000 x índice, encontradas = 1000).
      Cada aviso menciona algoritmo, variante y n.
- taller3.plot_search.plausibility_warnings(rows) -> list[str]
    rows: filas de UN CSV (un lenguaje). Usa `promedio_por_busqueda_ns` de las filas
    medidas. Devuelve un aviso por cada condición de §8.4 que se dispare (vacía si
    ninguna); cada aviso menciona el algoritmo implicado. No lanza.
- Ambas funciones se pueden importar SIN matplotlib (import perezoso de matplotlib dentro
  de las funciones que grafican): la comprobación no debe depender de la librería de
  gráficas.

Interpretación de los umbrales de §8.4 (límites inclusivos donde la spec dice "entre"):
- crecimiento lineal / variante entera: t(10n)/t(n) en [5, 20] es correcto; se prueba en
  el tramo 10^5 -> 10^6 (inequívocamente "n >= 10^4").
- Interpolación oficial: t_lineal / t_interp >= 100 en n = 10^6 (claves) es correcto.
- Variante entera: t_lineal / t_intdiv > 10 dispara aviso; exactamente 10 no.
- Binaria: aviso si t(centro) >= t(centro_alto). Saltos: aviso si t(centro) <= t(centro_alto).
- Lineal: t(final)/t(centro) en [1,5; 2,5] es correcto; aviso si t(final)/10^6 < 0,05 ns.
"""
from __future__ import annotations

import importlib
import unittest

LANGS = ("Java", "Python")
ALGOS = (
    "LinearSearch", "BinarySearch", "TernarySearch", "JumpSearch",
    "InterpolationSearch", "ExponentialSearch", "InterpolationSearchIntDiv",
)
SIZES = (1_000, 10_000, 100_000, 1_000_000)
POSITION_N = 1_000_000
K = 1000

COLUMNS = (
    "algoritmo,lenguaje,variante,n,num_busquedas,clave,rep_1_ns,rep_2_ns,rep_3_ns,rep_4_ns,"
    "rep_5_ns,promedio_ns,desv_estandar_ns,promedio_por_busqueda_ns,desv_por_busqueda_ns,"
    "encontradas,checksum,estado,causa,base_estimacion"
).split(",")                                                                     # §7.2

# --- §6.3 tabla de control (checksums de `claves`; encontradas = 500) -----------------
_C = {1_000: 249_971, 10_000: 2_493_210, 100_000: 24_852_292, 1_000_000: 248_439_213}
CONTROL_CLAVES = {(a, n): _C[n] for a in ALGOS for n in SIZES}
CONTROL_CLAVES[("ExponentialSearch", 100_000)] = 24_852_293
CONTROL_CLAVES[("BinarySearch", 1_000_000)] = 248_439_214
CONTROL_CLAVES[("TernarySearch", 1_000_000)] = 248_439_214
CONTROL_CLAVES[("InterpolationSearch", 1_000_000)] = 248_439_215
# §6.2 claves de posición y §6.3 checksum = 1000 x índice; encontradas = 1000
POSITIONS = {
    "inicio": (0, 10_000_033),
    "centro": (499_999, 54_951_725),
    "centro_alto": (500_000, 54_951_967),
    "final": (999_999, 99_999_964),
}

# --- Tiempos por búsqueda (ns) de un CSV "limpio" para §8.4 (sintéticos) --------------
CLEAN_CLAVES_NS = {
    "LinearSearch": (1_000.0, 10_000.0, 100_000.0, 1_000_000.0),       # x10 por década
    "BinarySearch": (100.0, 130.0, 160.0, 200.0),
    "TernarySearch": (120.0, 160.0, 200.0, 240.0),
    "JumpSearch": (300.0, 1_000.0, 3_000.0, 10_000.0),
    "InterpolationSearch": (100.0, 110.0, 120.0, 130.0),                # lineal/interp = 7692
    "ExponentialSearch": (150.0, 190.0, 230.0, 270.0),
    "InterpolationSearchIntDiv": (500.0, 5_000.0, 50_000.0, 500_000.0),  # lineal/intdiv = 2
}
CLEAN_POS_NS = {  # inicio, centro, centro_alto, final (n = 10^6)
    "LinearSearch": (50.0, 1_000_000.0, 1_000_002.0, 2_000_000.0),      # final/centro = 2; 2 ns/elem
    "BinarySearch": (190.0, 50.0, 200.0, 210.0),                        # centro < centro_alto
    "TernarySearch": (130.0, 120.0, 120.0, 130.0),
    "JumpSearch": (40.0, 1_500.0, 500.0, 2_000.0),                      # centro > centro_alto
    "InterpolationSearch": (60.0, 90.0, 110.0, 60.0),
    "ExponentialSearch": (40.0, 250.0, 220.0, 260.0),
    "InterpolationSearchIntDiv": (50.0, 500_000.0, 500_001.0, 1_000_000.0),
}


def _req(module: str, attr: str):
    """Importa lo que la spec exige; si falta, la prueba FALLA diciendo qué implementar."""
    try:
        m = importlib.import_module(module)
    except ImportError as e:
        raise AssertionError(
            f"Falta implementar {module} importable sin matplotlib (spec p2 §8.3/§8.4): {e}"
        ) from None
    if not hasattr(m, attr):
        raise AssertionError(f"Falta implementar {module}.{attr} (spec p2 §8.3/§8.4)")
    return getattr(m, attr)


def check_equivalence(rows_java, rows_python):
    return _req("taller3.plot_search", "check_equivalence")(rows_java, rows_python)


def plausibility_warnings(rows):
    return _req("taller3.plot_search", "plausibility_warnings")(rows)


def make_row(algoritmo, lenguaje, variante, n, por_busqueda_ns=1000.0, *,
             estado="medido", checksum=None, encontradas=None):
    """Fila de §7.2 como la daría csv.DictReader (todo str). Checksum/encontradas por
    defecto = tabla de control de §6.3."""
    if variante == "claves":
        clave = ""
        ck = CONTROL_CLAVES[(algoritmo, n)]
        enc = 500
    else:
        idx, clave = POSITIONS[variante]
        ck = K * idx
        enc = K
    ck = ck if checksum is None else checksum
    enc = enc if encontradas is None else encontradas
    total = por_busqueda_ns * K
    row = dict.fromkeys(COLUMNS, "")
    row.update(
        algoritmo=algoritmo, lenguaje=lenguaje, variante=variante, n=str(n),
        num_busquedas=str(K), clave=str(clave), promedio_ns=f"{total:.1f}",
        promedio_por_busqueda_ns=f"{por_busqueda_ns:.3f}", estado=estado,
    )
    if estado == "medido":
        for i in range(1, 6):
            row[f"rep_{i}_ns"] = str(int(total))
        row.update(desv_estandar_ns="0.0", desv_por_busqueda_ns="0.000",
                   encontradas=str(enc), checksum=str(ck))
    else:  # estimado: sin repeticiones, sin encontradas/checksum (§7.2)
        row.update(causa="predicción 400.0 s > límite 300 s",
                   base_estimacion=f"t(100000) x f({n})/f(100000) = x10 con f=O(n)")
    return row


def full_csv(lenguaje, claves_ns=None, pos_ns=None):
    """CSV completo (7 algoritmos x (4 n de claves + 4 posiciones)), en el orden de §6.2."""
    claves_ns = claves_ns or CLEAN_CLAVES_NS
    pos_ns = pos_ns or CLEAN_POS_NS
    rows = []
    for i, n in enumerate(SIZES):
        for a in ALGOS:
            rows.append(make_row(a, lenguaje, "claves", n, claves_ns[a][i]))
        if n == POSITION_N:
            for a in ALGOS:
                for j, v in enumerate(POSITIONS):
                    rows.append(make_row(a, lenguaje, v, n, pos_ns[a][j]))
    return rows


def find(rows, algoritmo, variante, n):
    for r in rows:
        if (r["algoritmo"], r["variante"], r["n"]) == (algoritmo, variante, str(n)):
            return r
    raise KeyError((algoritmo, variante, n))


def replace(rows, new_row):
    i = rows.index(find(rows, new_row["algoritmo"], new_row["variante"], int(new_row["n"])))
    rows[i] = new_row


def mentions(text, algoritmo, variante, n):
    return algoritmo in text and variante in text and str(n) in text


# ======================================================================================
# §8.3 Equivalencia Java <-> Python (+ tabla de control de §6.3)
# ======================================================================================
class TestCheckEquivalence(unittest.TestCase):

    def test_8_3_limpio_sin_excepcion_ni_avisos(self):
        avisos = check_equivalence(full_csv("Java"), full_csv("Python"))
        self.assertIsInstance(avisos, list)
        self.assertEqual(avisos, [], "checksums = tabla de control de §6.3: no debe avisar")

    def test_8_3_orden_de_filas_irrelevante(self):
        avisos = check_equivalence(full_csv("Java"), list(reversed(full_csv("Python"))))
        self.assertEqual(avisos, [])

    def test_8_3_checksum_distinto_lanza(self):
        java, py = full_csv("Java"), full_csv("Python")
        replace(py, make_row("BinarySearch", "Python", "claves", 100_000, 160.0,
                             checksum=24_852_293))
        with self.assertRaises(ValueError) as cm:
            check_equivalence(java, py)
        self.assertTrue(mentions(str(cm.exception), "BinarySearch", "claves", 100_000),
                        f"el mensaje debe identificar el caso: {cm.exception}")

    def test_8_3_encontradas_distintas_lanza(self):
        java, py = full_csv("Java"), full_csv("Python")
        replace(java, make_row("JumpSearch", "Java", "claves", 1_000, 300.0, encontradas=499))
        with self.assertRaises(ValueError) as cm:
            check_equivalence(java, py)
        self.assertTrue(mentions(str(cm.exception), "JumpSearch", "claves", 1_000))

    def test_8_3_diferencia_en_posicion_lanza(self):
        java, py = full_csv("Java"), full_csv("Python")
        replace(py, make_row("TernarySearch", "Python", "centro_alto", POSITION_N, 120.0,
                             checksum=499_999_000))
        with self.assertRaises(ValueError) as cm:
            check_equivalence(java, py)
        self.assertTrue(mentions(str(cm.exception), "TernarySearch", "centro_alto", POSITION_N))

    def test_8_3_lista_todas_las_diferencias(self):
        java, py = full_csv("Java"), full_csv("Python")
        replace(py, make_row("LinearSearch", "Python", "claves", 10_000, 10_000.0,
                             checksum=2_493_211))
        replace(py, make_row("ExponentialSearch", "Python", "final", POSITION_N, 260.0,
                             encontradas=999))
        with self.assertRaises(ValueError) as cm:
            check_equivalence(java, py)
        msg = str(cm.exception)
        self.assertTrue(mentions(msg, "LinearSearch", "claves", 10_000), msg)
        self.assertTrue(mentions(msg, "ExponentialSearch", "final", POSITION_N), msg)

    def test_8_3_estimado_se_omite_y_se_informa(self):
        java, py = full_csv("Java"), full_csv("Python")
        replace(py, make_row("InterpolationSearchIntDiv", "Python", "final", POSITION_N,
                             1_000_000.0, estado="estimado"))
        avisos = check_equivalence(java, py)          # no debe lanzar
        self.assertTrue(
            any(mentions(a, "InterpolationSearchIntDiv", "final", POSITION_N) for a in avisos),
            f"debe informar el caso omitido: {avisos}")

    def test_8_3_estimado_en_ambos_se_omite(self):
        java, py = full_csv("Java"), full_csv("Python")
        for rows, lang in ((java, "Java"), (py, "Python")):
            replace(rows, make_row("LinearSearch", lang, "claves", POSITION_N, 1e6,
                                   estado="estimado"))
        avisos = check_equivalence(java, py)
        self.assertTrue(any(mentions(a, "LinearSearch", "claves", POSITION_N) for a in avisos))

    def test_6_3_iguales_pero_distintos_de_la_tabla_avisa(self):
        java, py = full_csv("Java"), full_csv("Python")
        for rows, lang in ((java, "Java"), (py, "Python")):
            replace(rows, make_row("LinearSearch", lang, "claves", POSITION_N, 1e6,
                                   checksum=248_439_214))
        avisos = check_equivalence(java, py)          # Java == Python: no lanza
        self.assertTrue(any(mentions(a, "LinearSearch", "claves", POSITION_N) for a in avisos),
                        f"debe avisar la desviación de la tabla de §6.3: {avisos}")

    def test_6_3_encontradas_distintas_de_500_avisa(self):
        java, py = full_csv("Java"), full_csv("Python")
        for rows, lang in ((java, "Java"), (py, "Python")):
            replace(rows, make_row("BinarySearch", lang, "claves", 1_000, 100.0,
                                   encontradas=499))
        avisos = check_equivalence(java, py)
        self.assertTrue(any(mentions(a, "BinarySearch", "claves", 1_000) for a in avisos))

    def test_6_3_posicion_checksum_distinto_de_1000_por_indice_avisa(self):
        java, py = full_csv("Java"), full_csv("Python")
        for rows, lang in ((java, "Java"), (py, "Python")):
            replace(rows, make_row("JumpSearch", lang, "centro", POSITION_N, 1_500.0,
                                   checksum=500_000_000))
        avisos = check_equivalence(java, py)
        self.assertTrue(any(mentions(a, "JumpSearch", "centro", POSITION_N) for a in avisos))

    def test_6_3_tabla_es_por_algoritmo(self):
        """Las diferencias de 1–2 de §6.3 son legítimas: si se usara un solo valor por n
        (el de la lineal), avisaría de Binaria/Ternaria/Interp. en 10^6 y Exponencial en 10^5."""
        self.assertEqual(check_equivalence(full_csv("Java"), full_csv("Python")), [])


# ======================================================================================
# §8.4 Plausibilidad (avisos, no errores)
# ======================================================================================
def _claves(**cambios):
    d = {a: list(v) for a, v in CLEAN_CLAVES_NS.items()}
    for a, v in cambios.items():
        d[a] = list(v)
    return d


def _pos(**cambios):
    d = {a: list(v) for a, v in CLEAN_POS_NS.items()}
    for a, v in cambios.items():
        d[a] = list(v)
    return d


class TestPlausibilityWarnings(unittest.TestCase):

    def assertAvisa(self, rows, algoritmo):
        avisos = plausibility_warnings(rows)
        self.assertIsInstance(avisos, list)
        self.assertTrue(avisos, "debía disparar un aviso")
        for a in avisos:
            self.assertIn(algoritmo, a, f"aviso inesperado (sin {algoritmo}): {avisos}")

    def assertSinAvisos(self, rows):
        self.assertEqual(plausibility_warnings(rows), [])

    # --- CSV limpio ------------------------------------------------------------------
    def test_8_4_limpio_python_sin_avisos(self):
        self.assertSinAvisos(full_csv("Python"))

    def test_8_4_limpio_java_sin_avisos(self):
        self.assertSinAvisos(full_csv("Java"))

    def test_8_4_ignora_filas_estimadas(self):
        # §8.4 habla de tiempos medidos; una fila estimada de la lineal en 10^6 con un
        # valor absurdo no debe disparar avisos de crecimiento ni de interpolación.
        rows = full_csv("Python")
        replace(rows, make_row("LinearSearch", "Python", "claves", POSITION_N, 1.0,
                               estado="estimado"))
        self.assertSinAvisos(rows)

    # --- Crecimiento de la lineal / variante entera (×5–×20 por década, n >= 10^4) ---
    def test_8_4_lineal_crece_poco(self):
        self.assertAvisa(full_csv("Python", _claves(
            LinearSearch=(1_000.0, 10_000.0, 100_000.0, 400_000.0))), "LinearSearch")   # ×4

    def test_8_4_lineal_crece_demasiado(self):
        self.assertAvisa(full_csv("Python", _claves(
            LinearSearch=(1_000.0, 10_000.0, 100_000.0, 2_500_000.0))), "LinearSearch")  # ×25

    def test_8_4_lineal_crecimiento_en_los_limites_5_y_20(self):
        self.assertSinAvisos(full_csv("Python", _claves(
            LinearSearch=(1_000.0, 10_000.0, 50_000.0, 1_000_000.0))))   # ×5 y ×20

    def test_8_4_intdiv_crece_poco(self):
        self.assertAvisa(full_csv("Python", _claves(
            InterpolationSearchIntDiv=(500.0, 5_000.0, 50_000.0, 200_000.0))),        # ×4
            "InterpolationSearchIntDiv")

    def test_8_4_intdiv_crece_demasiado(self):
        self.assertAvisa(full_csv("Python", _claves(
            InterpolationSearchIntDiv=(500.0, 5_000.0, 50_000.0, 1_250_000.0))),      # ×25
            "InterpolationSearchIntDiv")

    # --- Interpolación oficial >= 100× más rápida que la lineal en 10^6 ---------------
    def test_8_4_interpolacion_no_100x_mas_rapida(self):
        self.assertAvisa(full_csv("Python", _claves(
            InterpolationSearch=(100.0, 110.0, 120.0, 20_000.0))),                    # ×50
            "InterpolationSearch")

    def test_8_4_interpolacion_exactamente_100x_no_avisa(self):
        self.assertSinAvisos(full_csv("Python", _claves(
            InterpolationSearch=(100.0, 110.0, 120.0, 10_000.0))))

    # --- Variante entera no > 10× más rápida que la lineal ----------------------------
    def test_8_4_intdiv_mas_de_10x_mas_rapida(self):
        self.assertAvisa(full_csv("Python", _claves(
            InterpolationSearchIntDiv=(50.0, 500.0, 5_000.0, 50_000.0))),             # ×20
            "InterpolationSearchIntDiv")

    def test_8_4_intdiv_exactamente_10x_no_avisa(self):
        self.assertSinAvisos(full_csv("Python", _claves(
            InterpolationSearchIntDiv=(100.0, 1_000.0, 10_000.0, 100_000.0))))

    # --- Artefacto del centro ---------------------------------------------------------
    def test_8_4_binaria_centro_no_mas_rapida_que_centro_alto(self):
        self.assertAvisa(full_csv("Python", pos_ns=_pos(
            BinarySearch=(190.0, 200.0, 200.0, 210.0))), "BinarySearch")              # igual

    def test_8_4_binaria_centro_mas_lenta(self):
        self.assertAvisa(full_csv("Python", pos_ns=_pos(
            BinarySearch=(190.0, 300.0, 200.0, 210.0))), "BinarySearch")

    def test_8_4_saltos_centro_no_mas_lenta_que_centro_alto(self):
        self.assertAvisa(full_csv("Python", pos_ns=_pos(
            JumpSearch=(40.0, 500.0, 500.0, 2_000.0))), "JumpSearch")                 # igual

    def test_8_4_saltos_centro_mas_rapida(self):
        self.assertAvisa(full_csv("Python", pos_ns=_pos(
            JumpSearch=(40.0, 300.0, 500.0, 2_000.0))), "JumpSearch")

    # --- Lineal final/centro en [1,5; 2,5] y >= 0,05 ns por elemento -----------------
    def test_8_4_lineal_final_centro_menor_que_1_5(self):
        self.assertAvisa(full_csv("Python", pos_ns=_pos(
            LinearSearch=(50.0, 1_000_000.0, 1_000_002.0, 1_200_000.0))), "LinearSearch")

    def test_8_4_lineal_final_centro_mayor_que_2_5(self):
        self.assertAvisa(full_csv("Python", pos_ns=_pos(
            LinearSearch=(50.0, 1_000_000.0, 1_000_002.0, 3_000_000.0))), "LinearSearch")

    def test_8_4_lineal_final_centro_en_los_limites(self):
        self.assertSinAvisos(full_csv("Python", pos_ns=_pos(
            LinearSearch=(50.0, 2_000_000.0, 2_000_002.0, 3_000_000.0))))   # 1,5
        self.assertSinAvisos(full_csv("Python", pos_ns=_pos(
            LinearSearch=(50.0, 1_000_000.0, 1_000_002.0, 2_500_000.0))))   # 2,5

    def test_8_4_lineal_menos_de_0_05_ns_por_elemento(self):
        # final = 40.000 ns / 10^6 elementos = 0,04 ns (razón final/centro = 2, correcta)
        self.assertAvisa(full_csv("Java", pos_ns=_pos(
            LinearSearch=(5.0, 20_000.0, 20_002.0, 40_000.0))), "LinearSearch")

    def test_8_4_lineal_exactamente_0_05_ns_por_elemento_no_avisa(self):
        self.assertSinAvisos(full_csv("Java", pos_ns=_pos(
            LinearSearch=(5.0, 25_000.0, 25_002.0, 50_000.0))))

    # --- No lanza ---------------------------------------------------------------------
    def test_8_4_varios_avisos_a_la_vez_no_lanza(self):
        rows = full_csv("Python",
                        _claves(InterpolationSearch=(100.0, 110.0, 120.0, 20_000.0)),
                        _pos(BinarySearch=(190.0, 300.0, 200.0, 210.0),
                             JumpSearch=(40.0, 300.0, 500.0, 2_000.0)))
        avisos = plausibility_warnings(rows)
        for alg in ("InterpolationSearch", "BinarySearch", "JumpSearch"):
            self.assertTrue(any(alg in a for a in avisos), f"falta aviso de {alg}: {avisos}")


class TestTablasDeApoyo(unittest.TestCase):
    """Correcciones menores de la auditoría (2026-10-23): razones solo entre medidos y
    unidad explícita en las tablas de posición."""

    def _idx(self, rows):
        return {(r["lenguaje"], r["algoritmo"], r["variante"], int(r["n"])): r for r in rows}

    def test_7_3_razones_de_crecimiento_omiten_estimados(self):
        import csv as _csv
        import tempfile
        from pathlib import Path
        ps = importlib.import_module("taller3.plot_search")
        rows = full_csv("Python")
        replace(rows, make_row("LinearSearch", "Python", "claves", 1_000_000, 9_000_000.0,
                               estado="estimado"))
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "razones.csv"
            ps.write_growth_ratios(self._idx(rows), out)
            got = list(_csv.DictReader(open(out, encoding="utf-8")))
        lin = [(r["n_desde"], r["n_hasta"]) for r in got if r["algoritmo"] == "LinearSearch"]
        self.assertEqual(lin, [("1000", "10000"), ("10000", "100000")])   # sin 10^5 -> 10^6
        self.assertTrue(any(r["algoritmo"] == "BinarySearch" and r["n_hasta"] == "1000000"
                            for r in got))

    def test_7_3_tabla_de_posicion_con_unidad_en_cada_celda(self):
        import tempfile
        from pathlib import Path
        ps = importlib.import_module("taller3.plot_search")
        rows = full_csv("Python")
        replace(rows, make_row("LinearSearch", "Python", "final", 1_000_000, 18_100_000.0,
                               estado="estimado"))
        with tempfile.TemporaryDirectory() as d:
            ps.write_position_tables(self._idx(rows), "Python", 1_000_000, Path(d))
            md = (Path(d) / "p2_posicion_python.md").read_text(encoding="utf-8")
        self.assertIn("~18,1 ms", md)
        self.assertNotIn("18.100", md)


if __name__ == "__main__":
    unittest.main()
