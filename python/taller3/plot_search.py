"""
Punto 2 - Comprobaciones, gráficas y tablas a partir de los CSV de búsqueda.

    cd python
    python3 -m taller3.plot_search                         # lee results/busqueda_*.csv, escribe figures/
    python3 -m taller3.plot_search --java X.csv --python Y.csv --out /tmp/figs

Antes de graficar (spec p2 8.3 y 8.4):
  - check_equivalence: checksum y encontradas idénticos entre Java y Python en todo caso
    medido en ambos (si no, FALLA con la lista de diferencias); avisa los casos omitidos
    por estar estimados y las filas que difieren de la tabla de control de la spec 6.3.
  - plausibility_warnings: avisos (no errores) si los tiempos sugieren una desviación
    del pseudocódigo (fórmula de interpolación cambiada, JIT que eliminó trabajo, ...).

Genera (spec 7.3; eje de tiempo logarítmico, estimados dibujados distinto):
  p2_crecimiento_java.png, p2_crecimiento_python.png   líneas log-log, variante `claves`
  p2_java_vs_python_n1000000.png                        barras Java vs Python, n = 10^6
  p2_posicion_{java,python}.{csv,md}                    tablas de posición, n = 10^6
  p2_razones_crecimiento.csv, p2_resumen.csv            tablas de apoyo

Convención visual: línea continua = medido; línea PUNTEADA (:) con marcador hueco =
estimado; RAYA-PUNTO (-.) en tono OSCURO del color de Interpolación = variante
InterpolationSearchIntDiv (no es uno de los 6 del enunciado; el tono claro se confundía con
el fondo y con las barras estimadas). Barras estimadas: rayadas, más claras y con "~" en la etiqueta.

matplotlib se importa SOLO dentro de las funciones que grafican: las comprobaciones se
pueden importar y probar sin la librería de gráficas.
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

from taller3 import config
from taller3.bench_search import position_index
from taller3.searching import SEARCHES

ALGOS = [s.name for s in SEARCHES]
GROWTH = {s.name: s.growth for s in SEARCHES}
VARIANT_ALGO = "InterpolationSearchIntDiv"
OFFICIAL = [a for a in ALGOS if a != VARIANT_ALGO]
LABEL = {
    "LinearSearch": "Lineal",
    "BinarySearch": "Binaria",
    "TernarySearch": "Ternaria",
    "JumpSearch": "Saltos",
    "InterpolationSearch": "Interpolación",
    "ExponentialSearch": "Exponencial",
    "InterpolationSearchIntDiv": "Interpolación (división entera, GfG Java)",
}
LANGS = ("Java", "Python")

# --- Tabla de control (spec 6.3): checksum de `claves` por n y algoritmo ----------------
_CONTROL_BASE = {1_000: 249_971, 10_000: 2_493_210, 100_000: 24_852_292, 1_000_000: 248_439_213}
CONTROL_CLAVES = {(a, n): v for a in ALGOS for n, v in _CONTROL_BASE.items()}
# Las diferencias de 1–2 vienen de las presentes repetidas en 10^5 y 10^6 (spec 6.1.3).
CONTROL_CLAVES[("ExponentialSearch", 100_000)] = 24_852_293
CONTROL_CLAVES[("BinarySearch", 1_000_000)] = 248_439_214
CONTROL_CLAVES[("TernarySearch", 1_000_000)] = 248_439_214
CONTROL_CLAVES[("InterpolationSearch", 1_000_000)] = 248_439_215
CONTROL_ENCONTRADAS_CLAVES = config.NUM_PRESENT_KEYS


# ======================================================================================
# Comprobaciones (sin matplotlib)
# ======================================================================================
def _case(r: dict[str, str]) -> tuple[str, str, int]:
    return r["algoritmo"], r["variante"], int(r["n"])


def _name(case: tuple[str, str, int]) -> str:
    a, v, n = case
    return f"{a} / {v} / n={n}"


def _control(r: dict[str, str]) -> tuple[int, int] | None:
    """(checksum, encontradas) esperados según la spec 6.3, o None si no hay referencia."""
    a, v, n = _case(r)
    if v == "claves":
        if (a, n) not in CONTROL_CLAVES:
            return None
        return CONTROL_CLAVES[(a, n)], CONTROL_ENCONTRADAS_CLAVES
    k = int(r["num_busquedas"])
    return k * position_index(v, n), k


def check_equivalence(rows_java: list[dict[str, str]],
                      rows_python: list[dict[str, str]]) -> list[str]:
    """Spec 8.3: lanza ValueError si Java y Python difieren en algún caso medido en ambos;
    si no, devuelve los avisos (casos omitidos y desviaciones de la tabla de control)."""
    java = {_case(r): r for r in rows_java}
    py = {_case(r): r for r in rows_python}
    errors: list[str] = []
    warnings: list[str] = []

    for case in sorted(set(java) | set(py), key=lambda c: (c[2], ALGOS.index(c[0]) if c[0] in ALGOS else 99, c[1])):
        rj, rp = java.get(case), py.get(case)
        if rj is None or rp is None:
            falta = "Java" if rj is None else "Python"
            warnings.append(f"{_name(case)}: sin fila en {falta}; no se compara")
            continue
        if rj["estado"] != "medido" or rp["estado"] != "medido":
            warnings.append(f"{_name(case)}: omitido de la comparación (Java {rj['estado']}, "
                            f"Python {rp['estado']})")
            continue
        for col in ("checksum", "encontradas"):
            if rj[col] != rp[col]:
                errors.append(f"{_name(case)}: {col} Java={rj[col]} Python={rp[col]}")

    if errors:
        raise ValueError("Java y Python devolvieron resultados distintos (spec 8.3):\n  "
                         + "\n  ".join(errors))

    for lang, rows in (("Java", rows_java), ("Python", rows_python)):
        for r in rows:
            if r["estado"] != "medido":
                continue
            ref = _control(r)
            if ref is None:
                continue
            ck, enc = ref
            if int(r["checksum"]) != ck or int(r["encontradas"]) != enc:
                warnings.append(f"{_name(_case(r))} ({lang}): checksum={r['checksum']} "
                                f"encontradas={r['encontradas']}, la tabla de control de la "
                                f"spec 6.3 dice checksum={ck} encontradas={enc}")
    return warnings


def _measured_times(rows: list[dict[str, str]]) -> dict[tuple[str, str, int], float]:
    return {_case(r): float(r["promedio_por_busqueda_ns"]) for r in rows
            if r["estado"] == "medido" and r["promedio_por_busqueda_ns"]}


def plausibility_warnings(rows: list[dict[str, str]]) -> list[str]:
    """Spec 8.4: avisos sobre los tiempos medidos de UN lenguaje. Nunca lanza."""
    t = _measured_times(rows)
    big = config.POSITION_N
    out: list[str] = []

    # Lineal y variante entera son O(n): ×5–×20 por cada ×10 en n (para n >= 10^4).
    for a in ("LinearSearch", VARIANT_ALGO):
        for n0, n1 in ((10_000, 100_000), (100_000, 1_000_000)):
            t0, t1 = t.get((a, "claves", n0)), t.get((a, "claves", n1))
            if t0 and t1 is not None:
                ratio = t1 / t0
                if not 5 <= ratio <= 20:
                    out.append(f"{a}: crece x{ratio:.2f} de n={n0} a n={n1}; se esperaba "
                               f"entre x5 y x20 (O(n))")

    lin = t.get(("LinearSearch", "claves", big))
    interp = t.get(("InterpolationSearch", "claves", big))
    if lin is not None and interp:
        ratio = lin / interp
        if ratio < 100:
            out.append(f"InterpolationSearch: solo x{ratio:.1f} más rápida que LinearSearch en "
                       f"n={big} (se esperaba >= x100); ¿se usó la fórmula de división entera?")
    intdiv = t.get((VARIANT_ALGO, "claves", big))
    if lin is not None and intdiv:
        ratio = lin / intdiv
        if ratio > 10:
            out.append(f"{VARIANT_ALGO}: x{ratio:.1f} más rápida que LinearSearch en n={big} "
                       f"(se esperaba <= x10, es O(n)); ¿se usó la fórmula double?")

    bc, bca = t.get(("BinarySearch", "centro", big)), t.get(("BinarySearch", "centro_alto", big))
    if bc is not None and bca is not None and bc >= bca:
        out.append(f"BinarySearch: centro ({bc:.1f} ns) no es más rápida que centro_alto "
                   f"({bca:.1f} ns); el índice 499.999 es su primer mid (1 comparación)")
    jc, jca = t.get(("JumpSearch", "centro", big)), t.get(("JumpSearch", "centro_alto", big))
    if jc is not None and jca is not None and jc <= jca:
        out.append(f"JumpSearch: centro ({jc:.1f} ns) no es más lenta que centro_alto "
                   f"({jca:.1f} ns); se esperaba ≈ 3x (≈ 1.500 vs ≈ 502 pasos)")

    lc, lf = t.get(("LinearSearch", "centro", big)), t.get(("LinearSearch", "final", big))
    if lc and lf is not None:
        ratio = lf / lc
        if not 1.5 <= ratio <= 2.5:
            out.append(f"LinearSearch: final/centro = {ratio:.2f} (se esperaba entre 1,5 y 2,5)")
    if lf is not None:
        per_elem = lf / big
        if per_elem < 0.05:
            out.append(f"LinearSearch: {per_elem:.3f} ns por elemento recorrido en final "
                       f"(< 0,05 ns); ¿el JIT eliminó trabajo?")
    return out


# ======================================================================================
# Carga y formato
# ======================================================================================
def load_csv(path: Path) -> list[dict[str, str]]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def fmt_n(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def fmt_sig3(x: float) -> str:
    """3 cifras significativas sin notación científica, coma decimal y punto de miles."""
    if x == 0:
        return "0"
    decimals = 2 - int(math.floor(math.log10(abs(x))))
    v = round(x, decimals)
    txt = f"{v:,.{decimals}f}" if decimals > 0 else f"{int(round(v)):,}"
    return txt.replace(",", "_").replace(".", ",").replace("_", ".")


def fmt_us(us: float) -> str:
    """Etiqueta de un tiempo por búsqueda dado en µs (con unidad legible)."""
    if us < 1_000:
        return f"{fmt_sig3(us)} µs"
    if us < 1_000_000:
        return f"{fmt_sig3(us / 1e3)} ms"
    return f"{fmt_sig3(us / 1e6)} s"


def per_search_us(r: dict[str, str] | None) -> float | None:
    if r is None or not r.get("promedio_por_busqueda_ns"):
        return None
    return float(r["promedio_por_busqueda_ns"]) / 1e3


def lighten(hex_color: str, amount: float = 0.55) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return (r + (1 - r) * amount, g + (1 - g) * amount, b + (1 - b) * amount)


def darken(hex_color: str, amount: float = 0.4) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return (r * (1 - amount), g * (1 - amount), b * (1 - amount))


# Paleta categórica del Punto 1 (orden fijo); la variante usa el color de Interpolación oscurecido.
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
ALGO_COLOR = {a: PALETTE[i] for i, a in enumerate(OFFICIAL)}
ALGO_COLOR[VARIANT_ALGO] = darken(ALGO_COLOR["InterpolationSearch"])
LANG_COLOR = {"Java": PALETTE[0], "Python": PALETTE[1]}
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"


def _plt():
    """Import perezoso de matplotlib (backend sin ventana) con el estilo del Punto 1."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.size": 10,
        "axes.edgecolor": INK_2,
        "axes.labelcolor": INK,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "xtick.color": INK_2,
        "ytick.color": INK_2,
        "hatch.linewidth": 0.9,
        "savefig.dpi": 200,
        "savefig.bbox": "tight",
    })
    return plt


def _us_label(y: float, _pos=None) -> str:
    if y <= 0:
        return ""
    return fmt_sig3(y)


def style_log_us_axis(ax) -> None:
    from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter
    ax.set_yscale("log")
    ax.yaxis.set_major_locator(LogLocator(base=10))
    ax.yaxis.set_major_formatter(FuncFormatter(_us_label))
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.grid(True, which="major", axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


# ======================================================================================
# 1-2) Crecimiento (líneas log-log)
# ======================================================================================
def plot_growth(rows: list[dict[str, str]], lang: str, out: Path) -> None:
    plt = _plt()
    from matplotlib.lines import Line2D
    from matplotlib.ticker import NullFormatter

    fig, ax = plt.subplots(figsize=(9.5, 6.2))
    any_est = False
    sizes_seen: set[int] = set()
    for algo in ALGOS:
        pts = sorted((int(r["n"]), per_search_us(r), r["estado"]) for r in rows
                     if r["algoritmo"] == algo and r["variante"] == "claves" and per_search_us(r))
        if not pts:
            continue
        sizes_seen.update(p[0] for p in pts)
        color = ALGO_COLOR[algo]
        ls = "-." if algo == VARIANT_ALGO else "-"
        meas = [(n, t) for n, t, e in pts if e == "medido"]
        est = [(n, t) for n, t, e in pts if e == "estimado"]
        if meas:
            ax.plot([p[0] for p in meas], [p[1] for p in meas], ls, color=color, marker="o",
                    lw=2, ms=7, mec="white", mew=1.2, zorder=3)
        if est:
            any_est = True
            chain = ([meas[-1]] if meas else []) + est
            ax.plot([p[0] for p in chain], [p[1] for p in chain], ":", color=color, lw=2.2, zorder=2)
            ax.plot([p[0] for p in est], [p[1] for p in est], "D", color=color,
                    mfc="white", mew=2, ms=7, zorder=4)

    sizes = sorted(sizes_seen) or list(config.SIZES)
    ax.set_xscale("log")
    ax.set_xticks(sizes)
    ax.set_xticklabels([fmt_n(n) for n in sizes])
    ax.xaxis.set_minor_formatter(NullFormatter())
    style_log_us_axis(ax)
    ax.grid(True, which="major", axis="x", color=GRID, linewidth=0.8)
    ax.set_xlabel("n (tamaño del arreglo ascendente, escala log)")
    ax.set_ylabel("Tiempo promedio por búsqueda (µs, escala log)")
    ax.set_title(f"Crecimiento del tiempo de búsqueda — {lang}, 1.000 claves (500 presentes, 500 ausentes)",
                 loc="left", color=INK)

    handles = []
    for a in ALGOS:
        if a == VARIANT_ALGO:
            handles.append(Line2D([], [], color=ALGO_COLOR[a], lw=2, ls="-.", marker="o", mec="white",
                                  label=LABEL[a] + " — variante"))
        else:
            handles.append(Line2D([], [], color=ALGO_COLOR[a], lw=2, marker="o", mec="white",
                                  label=LABEL[a]))
    if any_est:
        handles.append(Line2D([], [], color=INK_2, lw=2, ls=":", marker="D", mfc="white",
                              label="estimado (no ejecutado)"))
    ax.legend(handles=handles, loc="upper left", frameon=False, fontsize=9)
    fig.savefig(out)
    plt.close(fig)


# ======================================================================================
# 3) Compilado frente a interpretado (barras, n = 10^6)
# ======================================================================================
def plot_languages(idx: dict[tuple[str, str, str, int], dict[str, str]], n: int, out: Path) -> None:
    plt = _plt()
    from matplotlib.patches import Patch

    fig, ax = plt.subplots(figsize=(13, 6.4))
    width = 0.8 / len(LANGS)

    def get(algo: str, lang: str):
        r = idx.get((lang, algo, "claves", n))
        return (per_search_us(r), r["estado"]) if r else (None, "")

    values = [get(a, l)[0] for a in ALGOS for l in LANGS]
    values = [v for v in values if v]
    if not values:
        plt.close(fig)
        print(f"  (aviso) no hay datos de claves en n={n}; se omite {out.name}")
        return
    ymin, ymax = min(values), max(values)
    decades = max(1.0, math.log10(ymax / ymin))
    bottom = ymin / 10 ** (0.15 * decades + 0.3)
    top = ymax * 10 ** (0.2 * decades + 0.6)              # espacio para las etiquetas verticales

    any_est = False
    for j, lang in enumerate(LANGS):
        color = LANG_COLOR[lang]
        for i, algo in enumerate(ALGOS):
            v, estado = get(algo, lang)
            x = i + (j - (len(LANGS) - 1) / 2) * width
            if v is None:
                ax.text(x, bottom * 1.6, "sin dato", rotation=90, ha="center", va="bottom",
                        fontsize=7.5, color=INK_2)
                continue
            if estado == "estimado":
                any_est = True
                ax.bar(x, v - bottom, width * 0.9, bottom=bottom, color=lighten(color),
                       edgecolor=color, hatch="////", linewidth=1.0, zorder=2)
                label = "~" + fmt_us(v)
            else:
                ax.bar(x, v - bottom, width * 0.9, bottom=bottom, color=color,
                       edgecolor="white", linewidth=1.0, zorder=2)
                label = fmt_us(v)
            ax.text(x, v * 1.12, label, rotation=90, ha="center", va="bottom",
                    fontsize=7.5, color=INK, zorder=3)

    # La variante va como 7.º grupo, separada por una línea vertical tenue.
    vi = ALGOS.index(VARIANT_ALGO)
    ax.axvline(vi - 0.5, color=INK_2, lw=0.8, ls=(0, (2, 3)), alpha=0.6, zorder=1)
    labels = []
    for a in ALGOS:
        (tj, ej), (tp, ep) = get(a, "Java"), get(a, "Python")
        name = LABEL[a].replace(" (división entera, GfG Java)", "\n(división entera, GfG Java)")
        if a == VARIANT_ALGO:
            name += "\n(variante)"
        if tj and tp:
            approx = "~" if "estimado" in (ej, ep) else ""
            name += f"\nPy/Java {approx}{tp / tj:,.0f}×".replace(",", ".")
        labels.append(name)
    ax.set_ylim(bottom, top)
    ax.set_xticks(range(len(ALGOS)))
    ax.set_xticklabels(labels, fontsize=8.5)
    ax.set_xlim(-0.6, len(ALGOS) - 0.4)
    style_log_us_axis(ax)
    handles = [Patch(facecolor=LANG_COLOR[l], edgecolor="white", label=l) for l in LANGS]
    if any_est:
        handles.append(Patch(facecolor=lighten(INK_2, 0.75), edgecolor=INK_2, hatch="////",
                             label="estimado (no ejecutado)"))
    ax.legend(handles=handles, loc="upper left", frameon=False, ncol=len(handles), fontsize=9)
    ax.set_ylabel("Tiempo promedio por búsqueda (µs, escala log)")
    ax.set_title(f"Compilado (Java) frente a interpretado (Python) — n = {fmt_n(n)}, 1.000 claves",
                 loc="left", color=INK)
    fig.savefig(out)
    plt.close(fig)


# ======================================================================================
# 4-5) Tablas de posición (n = 10^6)
# ======================================================================================
def position_footer(idx: dict, lang: str, n: int) -> str:
    keys = {}
    for v in ("centro", "centro_alto"):
        r = next((idx[k] for k in idx if k[0] == lang and k[2] == v and k[3] == n), None)
        keys[v] = int(r["clave"]) if r and r["clave"] else None
    ic, ica = position_index("centro", n), position_index("centro_alto", n)
    vc = f" (valor {fmt_n(keys['centro'])})" if keys["centro"] is not None else ""
    vca = f" (valor {fmt_n(keys['centro_alto'])})" if keys["centro_alto"] is not None else ""
    return (f"`centro` = índice {fmt_n(ic)} = ⌊(n−1)/2⌋{vc}; `centro_alto` = índice "
            f"{fmt_n(ica)} = ⌊n/2⌋{vca}. {fmt_n(ic)} es el **mejor caso de la binaria**: es su "
            f"primer `mid` (1 comparación), mientras que {fmt_n(ica)} requiere 19 iteraciones; "
            f"en saltos ocurre lo contrario ({fmt_n(ic)} es el último elemento de su bloque, "
            f"≈ 1.500 pasos; {fmt_n(ica)} el primero del siguiente, ≈ 502). Ver el análisis "
            f"de posiciones (artefacto del centro, spec 6.2).")


def write_position_tables(idx: dict, lang: str, n: int, out_dir: Path) -> None:
    variants = list(config.POSITION_VARIANTS)
    if not any((lang, a, v, n) in idx for a in ALGOS for v in variants):
        print(f"  (aviso) no hay filas de posición de {lang} en n={n}; se omite la tabla")
        return
    stem = out_dir / f"p2_posicion_{lang.lower()}"
    md = ["| Algoritmo | " + " | ".join(
        f"{'centro' if v == 'centro_alto' else v} ({fmt_n(position_index(v, n))})" for v in variants) + " |",
        "|---|" + "---|" * len(variants)]
    with open(stem.with_suffix(".csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["algoritmo", "etiqueta"] + [f"{v}_ns" for v in variants] + ["estimados"])
        for a in ALGOS:
            label = LABEL[a] + (" (variante)" if a == VARIANT_ALGO else "")
            cells_csv, cells_md, est = [], [], []
            for v in variants:
                r = idx.get((lang, a, v, n))
                ns = float(r["promedio_por_busqueda_ns"]) if r and r["promedio_por_busqueda_ns"] else None
                if r and r["estado"] == "estimado":
                    est.append(v)
                cells_csv.append("" if ns is None else f"{ns:.1f}")
                if ns is None:
                    cells_md.append("—")
                else:
                    # Con unidad en cada celda (µs/ms/s): "18.100 µs" se leía como 18,1 µs.
                    cells_md.append(("~" if r["estado"] == "estimado" else "") + fmt_us(ns / 1e3))
            w.writerow([a, label] + cells_csv + [";".join(est)])
            md.append(f"| {label} | " + " | ".join(cells_md) + " |")
    reps = max((sum(1 for c in r if c.startswith("rep_") and r[c]) for k, r in idx.items()
                if k[0] == lang and k[3] == n and r["estado"] == "medido"), default=0)
    md += ["",
           f"Tiempo promedio por búsqueda (3 cifras significativas, unidad en cada celda), {lang}, n = {fmt_n(n)}, "
           f"{fmt_n(config.NUM_SEARCH_KEYS)} búsquedas de la misma clave por pasada, promedio de "
           f"{reps} pasadas. "
           f"`~` = estimado (no ejecutado).",
           "",
           position_footer(idx, lang, n),
           ""]
    stem.with_suffix(".md").write_text("\n".join(md), encoding="utf-8")


# ======================================================================================
# Tablas de apoyo
# ======================================================================================
def _order(r: dict[str, str]) -> tuple:
    a = r["algoritmo"]
    return (r["lenguaje"], ALGOS.index(a) if a in ALGOS else 99,
            config.SEARCH_VARIANTS.index(r["variante"]), int(r["n"]))


def write_summary(rows: list[dict[str, str]], out: Path) -> None:
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["lenguaje", "algoritmo", "variante", "n", "promedio_ns", "desv_estandar_ns",
                    "cv", "promedio_por_busqueda_ns", "estado"])
        for r in sorted(rows, key=_order):
            m = float(r["promedio_ns"]) if r["promedio_ns"] else None
            s = float(r["desv_estandar_ns"]) if r["desv_estandar_ns"] else None
            w.writerow([r["lenguaje"], r["algoritmo"], r["variante"], r["n"], r["promedio_ns"],
                        r["desv_estandar_ns"],
                        "" if (m is None or s is None or m == 0) else f"{s / m:.4f}",
                        r["promedio_por_busqueda_ns"], r["estado"]])


def write_growth_ratios(idx: dict, out: Path) -> None:
    """t(10n)/t(n) solo entre puntos MEDIDOS: con un estimado la razón observada sería la
    teórica (el estimado se calculó con ella) y no aportaría evidencia."""
    sizes = list(config.SIZES)
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["lenguaje", "algoritmo", "complejidad", "n_desde", "n_hasta",
                    "razon_observada", "razon_teorica"])
        for lang in LANGS:
            for a in ALGOS:
                g = GROWTH[a]
                for n0, n1 in zip(sizes, sizes[1:]):
                    r0, r1 = idx.get((lang, a, "claves", n0)), idx.get((lang, a, "claves", n1))
                    if r0 is None or r1 is None or "medido" != r0["estado"] or "medido" != r1["estado"]:
                        continue
                    t0, t1 = per_search_us(r0), per_search_us(r1)
                    if not t0 or not t1:
                        continue
                    w.writerow([lang, a, g.value, n0, n1, f"{t1 / t0:.3f}", f"{g.f(n1) / g.f(n0):.3f}"])


# ======================================================================================
def main() -> int:
    ap = argparse.ArgumentParser(description="Punto 2 - comprobaciones, gráficas y tablas")
    ap.add_argument("--java", type=Path, default=config.RESULTS_DIR / "busqueda_java.csv")
    ap.add_argument("--python", type=Path, default=config.RESULTS_DIR / "busqueda_python.csv")
    ap.add_argument("--out", type=Path, default=config.FIGURES_DIR)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    by_lang: dict[str, list[dict[str, str]]] = {}
    for lang, path in (("Java", args.java), ("Python", args.python)):
        if path.exists():
            by_lang[lang] = load_csv(path)
        else:
            print(f"  (aviso) no existe {path}; se omite {lang}")
    if not by_lang:
        print("No hay resultados. Ejecuta primero los benchmarks.")
        return 1

    if len(by_lang) == 2:
        avisos = check_equivalence(by_lang["Java"], by_lang["Python"])   # lanza si difieren
        print(f"Equivalencia Java <-> Python (spec 8.3): OK"
              + (f", {len(avisos)} aviso(s):" if avisos else ""))
        for a in avisos:
            print(f"  (aviso) {a}")
    else:
        print("  (aviso) solo hay un lenguaje: no se comprueba la equivalencia (spec 8.3)")
    for lang, rows in by_lang.items():
        for a in plausibility_warnings(rows):
            print(f"  (aviso de plausibilidad, {lang}) {a}")

    rows = [r for rs in by_lang.values() for r in rs]
    idx = {(r["lenguaje"], r["algoritmo"], r["variante"], int(r["n"])): r for r in rows}
    for lang, lrows in by_lang.items():
        plot_growth(lrows, lang, args.out / f"p2_crecimiento_{lang.lower()}.png")
        write_position_tables(idx, lang, config.POSITION_N, args.out)
    plot_languages(idx, config.POSITION_N, args.out / f"p2_java_vs_python_n{config.POSITION_N}.png")
    write_summary(rows, args.out / "p2_resumen.csv")
    write_growth_ratios(idx, args.out / "p2_razones_crecimiento.csv")

    for p in sorted(args.out.glob("p2_*")):
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
