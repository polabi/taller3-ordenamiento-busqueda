"""
Punto 3 - Tablas y figuras del análisis comparativo (spec p3 7.3), a partir de los CSV del
Punto 1 (ordenamiento), del Punto 2 (búsqueda) y del experimento de supuestos.

    cd python
    python3 -m taller3.plot_compare                          # lee results/, escribe figures/
    python3 -m taller3.plot_compare --java X.csv --python Y.csv --out /tmp/figs

    --java / --python   CSV de supuestos (por defecto results/supuestos_{java,python}.csv)
    --results           carpeta con ordenamiento_*.csv y busqueda_*.csv (por defecto results/)
    --out               carpeta de salida (por defecto figures/)

Genera:
  p3_limite_inferior.csv           ⌈log₂(n!)⌉ frente a n·log₂ n (tabla 4.1)
  p3_comparativos.{csv,md}         los 6 algoritmos del P1, aleatoria, n = 10^6 (4.3)
  p3_k_estrella.{csv,md}           k* de "¿ordenar o no ordenar?" (5): 7 filas
  p3_supuestos.{csv,md}            experimento de supuestos + perfiles de Bucket/Radix (4.4)
  p3_supuestos.png                 barras log: Bucket (Java/Python) y Radix 16 dígitos (Python)
  p3_costo_vs_k_{java,python}.png  costo(k) de ambas estrategias y cruce en k*

Comprobaciones (spec 8): ERROR si falta t_ord, t_B o t_L, o si la fila de sensibilidad no
da exactamente t_ord(Radix)/t_ord(Bucket) veces el k* principal; AVISOS (no errores) si
k*(claves) queda fuera de la banda [k*(solo_ausentes), k*(solo_presentes)] — revisión
obligatoria antes del informe —, si los tiempos de la lineal no son proporcionales a sus
comparaciones, o si el experimento de supuestos se aleja de lo esperado.

matplotlib se importa SOLO dentro de las funciones que grafican: los cálculos se pueden
importar y probar sin la librería de gráficas.
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

from taller3 import config
from taller3.common.compare import (bucket_profile, k_interval, k_min, k_star,
                                    lower_bound_comparisons, radix_passes)
from taller3.common.dataio import load_supuestos
from taller3.sorting import SORTS

LANGS = ("Java", "Python")
N_BIG = 1_000_000
SORT_ALGOS = [s.name for s in SORTS]
NON_COMPARATIVE = ("RadixSort", "BucketSort")
COMPARATIVE = [a for a in SORT_ALGOS if a not in NON_COMPARATIVE]
# fuente_t_lineal -> variante del Punto 2 de donde sale t_L (spec 5.2)
T_LINEAL_SOURCE = {"claves": "claves", "solo_presentes": "centro", "solo_ausentes": "final"}
K_STAR_COLUMNS = ["lenguaje", "rol", "algoritmo_orden", "t_ord_ns", "fuente_t_lineal",
                  "t_lineal_ns", "t_binaria_ns", "k_estrella", "k_min", "k_bajo", "k_alto",
                  "estado"]
SUPUESTOS_COLUMNS = ["lenguaje", "algoritmo", "distribucion", "n", "promedio_ns",
                     "desv_estandar_ns", "estado", "razon_vs_uniforme", "cubetas_no_vacias",
                     "cubeta_max", "desplazamientos", "pasadas_radix", "ref_comparativo",
                     "ref_comparativo_ns"]
SENS_TOLERANCE = 1e-9


# ======================================================================================
# Lectura
# ======================================================================================
def load_csv(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _num(s: str | None) -> float | None:
    return float(s) if s not in (None, "") else None


def _sort_row(rows: list[dict[str, str]], algo: str, n: int) -> dict[str, str] | None:
    for r in rows:
        if r["algoritmo"] == algo and r["variante"] == "aleatoria" and int(r["n"]) == n:
            return r
    return None


def _search_row(rows: list[dict[str, str]], algo: str, variante: str) -> dict[str, str]:
    for r in rows:
        if r["algoritmo"] == algo and r["variante"] == variante and int(r["n"]) == N_BIG:
            if _num(r.get("promedio_por_busqueda_ns")) is None:
                break
            return r
    raise ValueError(f"No se encuentra {algo} / {variante} / n={N_BIG} con tiempo en los CSV "
                     f"de búsqueda (corre run_punto2.sh)")


# ======================================================================================
# 4.1 Cota inferior
# ======================================================================================
def lower_bound_rows() -> list[dict]:
    rows = []
    for n in config.SIZES:
        lb = lower_bound_comparisons(n)
        nlogn = n * math.log2(n)
        rows.append({"n": n, "cota_inferior_comparaciones": lb, "n_log2_n": nlogn,
                     "cociente": lb / nlogn})
    return rows


# ======================================================================================
# 4.3 Comparativos frente a no comparativos (P1, aleatoria, n = 10^6)
# ======================================================================================
def comparativos_rows(ordenamiento: dict[str, list[dict[str, str]]]) -> list[dict]:
    rows = []
    for lang in LANGS:
        for algo in SORT_ALGOS:
            r = _sort_row(ordenamiento[lang], algo, N_BIG)
            r5 = _sort_row(ordenamiento[lang], algo, N_BIG // 10)
            t = _num(r["promedio_ns"]) if r else None
            t5 = _num(r5["promedio_ns"]) if r5 else None
            rows.append({
                "lenguaje": lang, "algoritmo": algo,
                "tipo": "no_comparativo" if algo in NON_COMPARATIVE else "comparativo",
                "promedio_ns": t,
                "ns_por_nlog2n": t / (N_BIG * math.log2(N_BIG)) if t else None,
                "ns_por_elemento": t / N_BIG if t else None,
                "razon_10e6_10e5": t / t5 if t and t5 else None,
                "estado": r["estado"] if r else "",
            })
    return rows


# ======================================================================================
# 5 / 7.3 k*
# ======================================================================================
def _best_sort(rows: list[dict[str, str]], lang: str) -> dict[str, str]:
    """Algoritmo con menor promedio_ns MEDIDO, aleatoria, n = 10^6 (D2: se elige por código)."""
    cands = [r for r in rows if r["variante"] == "aleatoria" and int(r["n"]) == N_BIG
             and r["estado"] == "medido" and _num(r["promedio_ns"]) is not None]
    if not cands:
        raise ValueError(f"No hay t_ord medido para {lang} (aleatoria, n={N_BIG}); corre run_punto1.sh")
    return min(cands, key=lambda r: float(r["promedio_ns"]))


def _k_row(lang: str, rol: str, sort_r: dict[str, str], fuente: str,
           lin_r: dict[str, str], bin_r: dict[str, str]) -> dict:
    t_ord, s_ord = float(sort_r["promedio_ns"]), _num(sort_r["desv_estandar_ns"]) or 0.0
    t_l, s_l = float(lin_r["promedio_por_busqueda_ns"]), _num(lin_r["desv_por_busqueda_ns"]) or 0.0
    t_b, s_b = float(bin_r["promedio_por_busqueda_ns"]), _num(bin_r["desv_por_busqueda_ns"]) or 0.0
    ks = k_star(t_ord, t_l, t_b)
    if ks is None:
        estado = "nunca_conviene"
        lo = hi = None
    else:
        lo, hi = k_interval(t_ord, s_ord, t_l, s_l, t_b, s_b)
        medidos = all(r["estado"] == "medido" for r in (sort_r, lin_r, bin_r))
        estado = "medido" if medidos else "estimado"
    return {"lenguaje": lang, "rol": rol, "algoritmo_orden": sort_r["algoritmo"],
            "t_ord_ns": t_ord, "fuente_t_lineal": fuente, "t_lineal_ns": t_l, "t_binaria_ns": t_b,
            "k_estrella": ks, "k_min": k_min(t_ord, t_l, t_b), "k_bajo": lo, "k_alto": hi,
            "estado": estado}


def k_star_rows(ordenamiento: dict[str, list[dict[str, str]]],
                busqueda: dict[str, list[dict[str, str]]]) -> list[dict]:
    """Las 7 filas de p3_k_estrella (7.3). ValueError si falta t_ord, t_B o t_L."""
    rows = []
    for lang in LANGS:
        best = _best_sort(ordenamiento[lang], lang)
        bin_r = _search_row(busqueda[lang], "BinarySearch", "claves")
        for fuente, variante in T_LINEAL_SOURCE.items():
            lin_r = _search_row(busqueda[lang], "LinearSearch", variante)
            rows.append(_k_row(lang, "principal" if fuente == "claves" else "banda",
                               best, fuente, lin_r, bin_r))
    radix = _sort_row(ordenamiento["Python"], "RadixSort", N_BIG)
    if radix is None or _num(radix["promedio_ns"]) is None:
        raise ValueError(f"No hay t_ord de RadixSort en Python (aleatoria, n={N_BIG}); corre run_punto1.sh")
    rows.append(_k_row("Python", "sensibilidad_orden", radix, "claves",
                       _search_row(busqueda["Python"], "LinearSearch", "claves"),
                       _search_row(busqueda["Python"], "BinarySearch", "claves")))
    _check_sensitivity(rows)
    return rows


def _check_sensitivity(rows: list[dict]) -> None:
    """k*(sensibilidad)/k*(principal Python) = t_ord(Radix)/t_ord(Bucket) exactamente (8)."""
    principal = next(r for r in rows if r["lenguaje"] == "Python" and r["rol"] == "principal")
    sens = next(r for r in rows if r["rol"] == "sensibilidad_orden")
    if principal["k_estrella"] is None or sens["k_estrella"] is None:
        return
    got = sens["k_estrella"] / principal["k_estrella"]
    expected = sens["t_ord_ns"] / principal["t_ord_ns"]
    if abs(got - expected) > SENS_TOLERANCE * expected:
        raise RuntimeError(f"Error de cálculo: k*(sensibilidad)/k*(principal) = {got!r} "
                           f"≠ t_ord(Radix)/t_ord(Bucket) = {expected!r}")


def _fmt_k(x: float | None) -> str:
    return "—" if x is None else f"{x:.4f}"


def k_star_warnings(rows: list[dict]) -> list[str]:
    """Avisos de 5.2 (regla de la banda) y de 8 (proporción de la lineal)."""
    msgs = []
    for lang in LANGS:
        by = {r["fuente_t_lineal"]: r for r in rows
              if r["lenguaje"] == lang and r["rol"] in ("principal", "banda")}
        k_cl, k_pr, k_au = (by[f]["k_estrella"] for f in ("claves", "solo_presentes", "solo_ausentes"))
        if None in (k_cl, k_pr, k_au) or not (k_au < k_cl < k_pr):
            msgs.append(f"{lang}: k*(claves) = {_fmt_k(k_cl)} NO queda dentro de la banda "
                        f"k*(solo_ausentes) = {_fmt_k(k_au)} < k*(claves) < k*(solo_presentes) = "
                        f"{_fmt_k(k_pr)}. REVISIÓN OBLIGATORIA antes de escribir el informe "
                        f"(ruido en la lineal, JIT o una medición estimada).")
        t_fin = by["solo_ausentes"]["t_lineal_ns"]
        for fuente, var, (lo, hi) in (("claves", "claves", (0.65, 0.85)),
                                      ("solo_presentes", "centro", (0.4, 0.6))):
            ratio = by[fuente]["t_lineal_ns"] / t_fin
            if not lo <= ratio <= hi:
                msgs.append(f"{lang}: t_L({var})/t_L(final) = {ratio:.3f} fuera de "
                            f"[{lo}, {hi}]: el costo de la lineal no sería proporcional a sus "
                            f"comparaciones.")
    return msgs


# ======================================================================================
# 4.4 / 7.3 Experimento de supuestos
# ======================================================================================
def _sup_index(rows: list[dict[str, str]]) -> dict[tuple[str, str, int], dict[str, str]]:
    return {(r["algoritmo"], r["distribucion"], int(r["n"])): r for r in rows}


def supuestos_warnings(supuestos: dict[str, list[dict[str, str]]],
                       ordenamiento: dict[str, list[dict[str, str]]]) -> list[str]:
    """Avisos de 8 sobre el experimento de supuestos (no son errores)."""
    msgs = []
    for lang, rows in supuestos.items():
        idx = _sup_index(rows)

        def t(algo, dist, n):
            r = idx.get((algo, dist, n))
            return _num(r["promedio_ns"]) if r else None

        a, b = t("BucketSort", "concentrado_extremos", 10_000), t("BucketSort", "concentrado_extremos", 100_000)
        if a and b and not 50 <= b / a <= 200:
            msgs.append(f"{lang}: BucketSort concentrado_extremos t(10^5)/t(10^4) = {b / a:.1f} "
                        f"fuera de [50, 200] (teórico ≈ 101).")
        for n in config.DIGITOS16_SIZES:
            u, d = t("RadixSort", "uniforme", n), t("RadixSort", "digitos16", n)
            if u and d and not 1.5 <= d / u <= 3.5:
                msgs.append(f"{lang}: RadixSort digitos16/uniforme = {d / u:.2f} en n={n} "
                            f"fuera de [1,5; 3,5].")
        for (algo, dist, n), r in idx.items():
            if dist != "uniforme" or _num(r["promedio_ns"]) is None:
                continue
            p1 = _sort_row(ordenamiento.get(lang, []), algo, n)
            if p1 is None or _num(p1["promedio_ns"]) is None:
                continue
            diff = float(r["promedio_ns"]) / float(p1["promedio_ns"]) - 1
            if abs(diff) > 0.30:
                msgs.append(f"{lang}: {algo} uniforme n={n} difiere {diff:+.0%} del Punto 1 "
                            f"(> 30 %: condiciones de la máquina distintas).")
    return msgs


def supuestos_rows(supuestos: dict[str, list[dict[str, str]]],
                   ordenamiento: dict[str, list[dict[str, str]]],
                   data_dir: Path = config.DATA_DIR) -> list[dict]:
    profiles: dict[tuple[str, int], tuple[int, int, int]] = {}
    passes: dict[tuple[str, int], int] = {}
    out = []
    for lang in LANGS:
        rows = supuestos.get(lang, [])
        idx = _sup_index(rows)
        for r in rows:
            algo, dist, n = r["algoritmo"], r["distribucion"], int(r["n"])
            t = _num(r["promedio_ns"])
            u = _num(idx[(algo, "uniforme", n)]["promedio_ns"]) if (algo, "uniforme", n) in idx else None
            row = {"lenguaje": lang, "algoritmo": algo, "distribucion": dist, "n": n,
                   "promedio_ns": t, "desv_estandar_ns": _num(r["desv_estandar_ns"]),
                   "estado": r["estado"], "razon_vs_uniforme": t / u if t and u else None,
                   "cubetas_no_vacias": None, "cubeta_max": None, "desplazamientos": None,
                   "pasadas_radix": None, "ref_comparativo": "", "ref_comparativo_ns": None}
            if algo == "BucketSort":
                if (dist, n) not in profiles:
                    profiles[(dist, n)] = bucket_profile(load_supuestos(dist, n, data_dir))
                row["cubetas_no_vacias"], row["cubeta_max"], row["desplazamientos"] = profiles[(dist, n)]
            else:
                if (dist, n) not in passes:
                    passes[(dist, n)] = radix_passes(load_supuestos(dist, n, data_dir))
                row["pasadas_radix"] = passes[(dist, n)]
            cands = [c for c in (_sort_row(ordenamiento[lang], a, n) for a in COMPARATIVE)
                     if c and c["estado"] == "medido" and _num(c["promedio_ns"]) is not None]
            if cands:
                best = min(cands, key=lambda c: float(c["promedio_ns"]))
                row["ref_comparativo"], row["ref_comparativo_ns"] = best["algoritmo"], float(best["promedio_ns"])
            out.append(row)
    return out


# ======================================================================================
# Escritura de tablas
# ======================================================================================
def _cell(v, fmt: str = "") -> str:
    return "" if v is None else format(v, fmt)


def write_csv(path: Path, columns: list[str], rows: list[dict], fmts: dict[str, str]) -> None:
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(columns)
        for r in rows:
            w.writerow([_cell(r[c], fmts.get(c, "")) for c in columns])


def fmt_n(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def fmt_es(x: float, decimals: int) -> str:
    """Número con punto de miles y coma decimal (como el informe)."""
    return f"{x:,.{decimals}f}".replace(",", "_").replace(".", ",").replace("_", ".")


def fmt_time(ns: float) -> str:
    from taller3.plot_search import fmt_sig3
    if ns < 1e3:
        return f"{fmt_sig3(ns)} ns"
    if ns < 1e6:
        return f"{fmt_sig3(ns / 1e3)} µs"
    if ns < 1e9:
        return f"{fmt_sig3(ns / 1e6)} ms"
    return f"{fmt_sig3(ns / 1e9)} s"


def write_comparativos(rows: list[dict], out_dir: Path) -> None:
    cols = ["lenguaje", "algoritmo", "tipo", "promedio_ns", "ns_por_nlog2n", "ns_por_elemento",
            "razon_10e6_10e5", "estado"]
    write_csv(out_dir / "p3_comparativos.csv", cols, rows,
              {"promedio_ns": ".1f", "ns_por_nlog2n": ".4f", "ns_por_elemento": ".4f",
               "razon_10e6_10e5": ".2f"})
    lines = ["# Comparativos frente a no comparativos — aleatoria, n = 1.000.000 (Punto 1)", "",
             "| Lenguaje | Algoritmo | Tipo | Tiempo | ns / (n·log₂ n) | ns / elemento | t(10⁶)/t(10⁵) |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        t = r["promedio_ns"]
        pre = "~" if r["estado"] == "estimado" else ""
        lines.append(f"| {r['lenguaje']} | {r['algoritmo']} | {r['tipo'].replace('_', ' ')} | "
                     f"{pre + fmt_time(t) if t else '—'} | "
                     f"{fmt_es(r['ns_por_nlog2n'], 3) if t else '—'} | "
                     f"{fmt_es(r['ns_por_elemento'], 2) if t else '—'} | "
                     f"{fmt_es(r['razon_10e6_10e5'], 2) if r['razon_10e6_10e5'] else '—'} |")
    lines += ["", "`~` = estimado (no ejecutado, regla de 5 min del Punto 1). Teórico de "
              "t(10⁶)/t(10⁵): O(n) = 10; O(n log n) = 12; O(n²) = 100.", ""]
    (out_dir / "p3_comparativos.md").write_text("\n".join(lines), encoding="utf-8")


def write_k_star(rows: list[dict], warnings: list[str], out_dir: Path) -> None:
    write_csv(out_dir / "p3_k_estrella.csv", K_STAR_COLUMNS, rows,
              {"t_ord_ns": ".1f", "t_lineal_ns": ".3f", "t_binaria_ns": ".3f",
               "k_estrella": ".4f", "k_bajo": ".4f", "k_alto": ".4f"})
    principal_py = next(r for r in rows if r["lenguaje"] == "Python" and r["rol"] == "principal")
    lines = ["# ¿Ordenar o no ordenar? — k* = t_ord / (t_L − t_B), n = 1.000.000", ""]
    band = [w for w in warnings if "banda" in w]
    if band:
        lines += ["> **⚠ AVISO — REVISIÓN OBLIGATORIA ANTES DE ESCRIBIR EL INFORME (spec p3 5.2).**",
                  ">"] + [f"> {w}" for w in band] + [""]
    lines += ["| Lenguaje | Rol | Ordenamiento | t_ord | t_L (fuente) | t_B | k* | k_min | "
              "intervalo ±1σ | Estado |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        rol = r["rol"]
        if rol == "sensibilidad_orden" and r["k_estrella"] and principal_py["k_estrella"]:
            rol += f" — sensibilidad: Radix en lugar de Bucket (×{fmt_es(r['k_estrella'] / principal_py['k_estrella'], 2)})"
        k = r["k_estrella"]
        interval = (f"[{fmt_es(r['k_bajo'], 2) if r['k_bajo'] is not None else '—'}; "
                    f"{fmt_es(r['k_alto'], 2) if r['k_alto'] is not None else '—'}]")
        lines.append(f"| {r['lenguaje']} | {rol} | {r['algoritmo_orden']} | {fmt_time(r['t_ord_ns'])} | "
                     f"{fmt_time(r['t_lineal_ns'])} ({r['fuente_t_lineal']}) | {fmt_time(r['t_binaria_ns'])} | "
                     f"{fmt_es(k, 2) if k is not None else '—'} | "
                     f"{r['k_min'] if r['k_min'] is not None else '—'} | "
                     f"{interval if k is not None else '—'} | {r['estado']} |")
    lines += ["", "## Cálculo (filas principales)", ""]
    for r in rows:
        if r["rol"] != "principal":
            continue
        if r["k_estrella"] is None:
            lines.append(f"- **{r['lenguaje']}**: t_L ≤ t_B → nunca conviene ordenar.")
            continue
        den = r["t_lineal_ns"] - r["t_binaria_ns"]
        lines.append(f"- **{r['lenguaje']}** ({r['algoritmo_orden']}): k* = "
                     f"{fmt_es(r['t_ord_ns'], 1)} ns / ({fmt_es(r['t_lineal_ns'], 3)} − "
                     f"{fmt_es(r['t_binaria_ns'], 3)}) ns = {fmt_es(r['t_ord_ns'], 1)} / "
                     f"{fmt_es(den, 3)} = **{fmt_es(r['k_estrella'], 4)}** → conviene ordenar "
                     f"desde k = **{r['k_min']}** búsquedas.")
    lines += ["", "Banda (`solo_presentes` = LinearSearch `centro`; `solo_ausentes` = LinearSearch "
              "`final`): es una APROXIMACIÓN del efecto de la mezcla de claves, no un intervalo "
              "de confianza (spec p3 5.2). Intervalo ±1σ según spec 5.5.", ""]
    (out_dir / "p3_k_estrella.md").write_text("\n".join(lines), encoding="utf-8")


def write_supuestos(rows: list[dict], out_dir: Path) -> None:
    write_csv(out_dir / "p3_supuestos.csv", SUPUESTOS_COLUMNS, rows,
              {"promedio_ns": ".1f", "desv_estandar_ns": ".1f", "razon_vs_uniforme": ".3f",
               "ref_comparativo_ns": ".1f"})
    lines = ["# Experimento de supuestos (Bucket Sort y Radix Sort)", "",
             "| Lenguaje | Algoritmo | Distribución | n | Tiempo | × uniforme | cubetas no vacías | "
             "cubeta máx. | desplazamientos | pasadas Radix | mejor comparativo (P1) |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        t = r["promedio_ns"]
        pre = "~" if r["estado"] == "estimado" else ""
        ref = (f"{r['ref_comparativo']} {fmt_time(r['ref_comparativo_ns'])}"
               + (" (*)" if r["distribucion"] == "digitos16" else "")) if r["ref_comparativo"] else "—"
        lines.append(" | ".join([
            f"| {r['lenguaje']}", r["algoritmo"], r["distribucion"], fmt_n(r["n"]),
            pre + fmt_time(t) if t else "—",
            fmt_es(r["razon_vs_uniforme"], 2) if r["razon_vs_uniforme"] else "—",
            *(fmt_n(r[c]) if r[c] is not None else "—"
              for c in ("cubetas_no_vacias", "cubeta_max", "desplazamientos", "pasadas_radix")),
            ref]) + " |")
    lines += ["", "`~` = estimado (no ejecutado). (*) referencia medida con 8 dígitos: los "
              "comparativos del Punto 1 no se midieron con 16 dígitos (spec p3 4.4.1).", ""]
    (out_dir / "p3_supuestos.md").write_text("\n".join(lines), encoding="utf-8")


# ======================================================================================
# Figuras
# ======================================================================================
def _bar(ax, x, v, width, color, estimado, bottom):
    from taller3.plot_search import INK, lighten
    if estimado:
        ax.bar(x, v - bottom, width, bottom=bottom, color=lighten(color), edgecolor=color,
               hatch="////", linewidth=1.0, zorder=2)
    else:
        ax.bar(x, v - bottom, width, bottom=bottom, color=color, edgecolor="white",
               linewidth=1.0, zorder=2)
    ax.text(x, v * 1.12, ("~" if estimado else "") + fmt_time(v), rotation=90, ha="center",
            va="bottom", fontsize=7.5, color=INK, zorder=3)


def _style_log_time_axis(ax, values: list[float]) -> float:
    from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter
    from taller3.plot_search import GRID
    ymin, ymax = min(values), max(values)
    decades = max(1.0, math.log10(ymax / ymin))
    bottom = ymin / 10 ** (0.15 * decades + 0.3)
    ax.set_yscale("log")
    ax.set_ylim(bottom, ymax * 10 ** (0.2 * decades + 0.7))
    ax.yaxis.set_major_locator(LogLocator(base=10))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda y, _p: fmt_time(y) if y > 0 else ""))
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.grid(True, which="major", axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    return bottom


def plot_supuestos(supuestos: dict[str, list[dict[str, str]]], out: Path) -> None:
    from matplotlib.patches import Patch
    from taller3.plot_search import INK, INK_2, LANG_COLOR, PALETTE, _plt, lighten
    plt = _plt()
    idx = {(lang, r["algoritmo"], r["distribucion"], int(r["n"])): r
           for lang, rows in supuestos.items() for r in rows}

    def get(lang, algo, dist, n):
        r = idx.get((lang, algo, dist, n))
        v = _num(r["promedio_ns"]) if r else None
        return (v, r["estado"] == "estimado") if v else (None, False)

    fig, (ax_b, ax_r) = plt.subplots(1, 2, figsize=(14, 6.4), gridspec_kw={"width_ratios": [2, 1]})
    any_est = False

    # Panel 1: Bucket, grupos n × distribución, barras Java/Python
    groups = [(n, d) for n in config.SUPUESTOS_SIZES for d in config.BUCKET_DISTRIBUTIONS]
    vals = [get(l, "BucketSort", d, n)[0] for n, d in groups for l in LANGS]
    vals = [v for v in vals if v]
    if vals:
        bottom = _style_log_time_axis(ax_b, vals)
        w = 0.8 / len(LANGS)
        for j, lang in enumerate(LANGS):
            for i, (n, d) in enumerate(groups):
                v, est = get(lang, "BucketSort", d, n)
                if v:
                    any_est |= est
                    _bar(ax_b, i + (j - 0.5) * w, v, w * 0.9, LANG_COLOR[lang], est, bottom)
        ax_b.set_xticks(range(len(groups)))
        ax_b.set_xticklabels([f"{d.replace('_', ' ')}\nn = {fmt_n(n)}" for n, d in groups], fontsize=8.5)
        ax_b.axvline(len(config.BUCKET_DISTRIBUTIONS) - 0.5, color=INK_2, lw=0.8, ls=(0, (2, 3)), alpha=0.6)
        handles = [Patch(facecolor=LANG_COLOR[l], edgecolor="white", label=l) for l in LANGS]
        ax_b.legend(handles=handles, loc="upper left", frameon=False, ncol=2, fontsize=9)
    ax_b.set_ylabel("Tiempo promedio por ejecución (escala log)")
    ax_b.set_title("Bucket Sort: ¿qué pasa si los datos no son uniformes?", loc="left", color=INK)

    # Panel 2: Radix Python, grupos n, barras uniforme/digitos16
    dist_color = {"uniforme": PALETTE[2], "digitos16": PALETTE[3]}
    dist_label = {"uniforme": "uniforme (8 dígitos)", "digitos16": "16 dígitos"}
    vals = [get("Python", "RadixSort", d, n)[0] for n in config.DIGITOS16_SIZES for d in dist_color]
    vals = [v for v in vals if v]
    if vals:
        bottom = _style_log_time_axis(ax_r, vals)
        w = 0.8 / 2
        for j, d in enumerate(dist_color):
            for i, n in enumerate(config.DIGITOS16_SIZES):
                v, est = get("Python", "RadixSort", d, n)
                if v:
                    any_est |= est
                    _bar(ax_r, i + (j - 0.5) * w, v, w * 0.9, dist_color[d], est, bottom)
        labels = []
        for n in config.DIGITOS16_SIZES:
            u, d16 = get("Python", "RadixSort", "uniforme", n)[0], get("Python", "RadixSort", "digitos16", n)[0]
            labels.append(f"n = {fmt_n(n)}" + (f"\n16/8 díg. ×{fmt_es(d16 / u, 2)}" if u and d16 else ""))
        ax_r.set_xticks(range(len(config.DIGITOS16_SIZES)))
        ax_r.set_xticklabels(labels, fontsize=8.5)
        handles = [Patch(facecolor=c, edgecolor="white", label=dist_label[d]) for d, c in dist_color.items()]
        ax_r.legend(handles=handles, loc="upper left", frameon=False, fontsize=9)
    ax_r.set_title("Radix Sort (Python): 8 frente a 16 dígitos", loc="left", color=INK)

    if any_est:
        fig.legend(handles=[Patch(facecolor=lighten(INK_2, 0.75), edgecolor=INK_2, hatch="////",
                                  label="estimado (no ejecutado)")],
                   loc="lower right", frameon=False, fontsize=9)
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


def plot_cost_vs_k(row: dict, out: Path) -> None:
    from taller3.plot_search import GRID, INK, INK_2, PALETTE, _plt
    plt = _plt()
    t_ord, t_l, t_b, ks = row["t_ord_ns"], row["t_lineal_ns"], row["t_binaria_ns"], row["k_estrella"]
    k_hi = 10 ** math.ceil(math.log10(max(ks or 1.0, 1.0)) + 2)
    ks_axis = [10 ** (i / 50) for i in range(int(50 * math.log10(k_hi)) + 1)]
    lineal = [k * t_l / 1e9 for k in ks_axis]
    ordenar = [(t_ord + k * t_b) / 1e9 for k in ks_axis]

    fig, ax = plt.subplots(figsize=(8.5, 5.4))
    ax.plot(ks_axis, lineal, color=PALETTE[0], lw=2, label="k búsquedas lineales (sin ordenar)")
    ax.plot(ks_axis, ordenar, color=PALETTE[1], lw=2,
            label=f"ordenar ({row['algoritmo_orden']}) + k búsquedas binarias")
    ax.set_xscale("log")
    ax.set_yscale("log")
    if ks:
        y = ks * t_l / 1e9
        ax.axvline(ks, color=INK_2, lw=0.9, ls=(0, (3, 3)), zorder=1)
        ax.plot([ks], [y], "o", ms=8, color=INK, mec="white", mew=2, zorder=3)
        ax.annotate(f"k* = {fmt_es(ks, 2)}  (conviene ordenar desde k = {row['k_min']})",
                    (ks, y), xytext=(10, -18), textcoords="offset points", fontsize=9, color=INK)
    ax.grid(True, which="major", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.set_xlabel("k (número de búsquedas, escala log)")
    ax.set_ylabel("Costo total (s, escala log)")
    ax.legend(loc="upper left", frameon=False, fontsize=9)
    ax.set_title(f"¿Ordenar o no ordenar? — {row['lenguaje']}, n = 1.000.000", loc="left", color=INK)
    fig.savefig(out)
    plt.close(fig)


# ======================================================================================
# main
# ======================================================================================
def main() -> int:
    ap = argparse.ArgumentParser(description="Punto 3 - tablas y figuras del análisis comparativo")
    ap.add_argument("--java", type=Path, default=config.RESULTS_DIR / "supuestos_java.csv")
    ap.add_argument("--python", type=Path, default=config.RESULTS_DIR / "supuestos_python.csv")
    ap.add_argument("--results", type=Path, default=config.RESULTS_DIR,
                    help="carpeta con ordenamiento_*.csv y busqueda_*.csv")
    ap.add_argument("--out", type=Path, default=config.FIGURES_DIR)
    args = ap.parse_args()

    ordenamiento, busqueda = {}, {}
    missing = []
    for lang in LANGS:
        for kind, store, script in (("ordenamiento", ordenamiento, "run_punto1.sh"),
                                    ("busqueda", busqueda, "run_punto2.sh")):
            path = args.results / f"{kind}_{lang.lower()}.csv"
            if path.exists():
                store[lang] = load_csv(path)
            else:
                missing.append(f"{path} (corre {script})")
    if missing:
        print("ERROR: faltan resultados de los Puntos 1/2; corre run_punto1.sh / run_punto2.sh:")
        for m in missing:
            print(f"  {m}")
        return 1

    supuestos = {}
    for lang, path in (("Java", args.java), ("Python", args.python)):
        if path.exists():
            supuestos[lang] = load_csv(path)
        else:
            print(f"  (aviso) no existe {path}; se omite {lang} en el experimento de supuestos")

    args.out.mkdir(parents=True, exist_ok=True)
    write_csv(args.out / "p3_limite_inferior.csv",
              ["n", "cota_inferior_comparaciones", "n_log2_n", "cociente"], lower_bound_rows(),
              {"n_log2_n": ".1f", "cociente": ".4f"})
    write_comparativos(comparativos_rows(ordenamiento), args.out)

    k_rows = k_star_rows(ordenamiento, busqueda)          # ValueError / RuntimeError -> falla
    k_warn = k_star_warnings(k_rows)
    write_k_star(k_rows, k_warn, args.out)
    for r in k_rows:
        if r["rol"] == "principal":
            print(f"  k* {r['lenguaje']:<6} ({r['algoritmo_orden']}): {_fmt_k(r['k_estrella'])} "
                  f"-> k_min = {r['k_min']}  [{r['estado']}]")
            plot_cost_vs_k(r, args.out / f"p3_costo_vs_k_{r['lenguaje'].lower()}.png")
    band = [w for w in k_warn if "banda" in w]
    if band:
        print("\n" + "!" * 88)
        print("AVISO (spec p3 5.2): k*(claves) fuera de la banda. NO publicar la tabla ni la "
              "conclusión de la Parte B sin revisar:")
        for w in band:
            print(f"  {w}")
        print("!" * 88 + "\n")
    for w in k_warn:
        if w not in band:
            print(f"  (aviso de plausibilidad) {w}")

    if supuestos:
        for w in supuestos_warnings(supuestos, ordenamiento):
            print(f"  (aviso de plausibilidad) {w}")
        write_supuestos(supuestos_rows(supuestos, ordenamiento), args.out)
        plot_supuestos(supuestos, args.out / "p3_supuestos.png")

    for p in sorted(args.out.glob("p3_*")):
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
