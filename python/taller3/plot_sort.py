"""
Punto 1 - Gráficas y tablas a partir de los CSV de resultados.

    cd python
    pip install matplotlib                      # única dependencia externa
    python3 -m taller3.plot_sort                # lee results/, escribe figures/

Genera (todas con eje de tiempo logarítmico, como exige el taller):
  p1_crecimiento_java.png, p1_crecimiento_python.png         (2) líneas log-log, entrada aleatoria
  p1_orden_entrada_java_n1000/10000/100000.png               (3) barras: aleatoria/ascendente/descendente
  p1_java_vs_python_n1000000.png                             (1) barras: Java vs Python, aleatoria
Tablas de apoyo para el informe:
  p1_resumen.csv              promedio, desviación y coeficiente de variación de cada caso
  p1_razones_crecimiento.csv  t(10n)/t(n) observado vs. teórico (pregunta de "Crecimiento")

Convención visual de los valores ESTIMADOS: línea punteada con marcador hueco
(líneas) y barra rayada más clara con el prefijo "~" en la etiqueta (barras).
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402
from matplotlib.lines import Line2D                   # noqa: E402
from matplotlib.patches import Patch                  # noqa: E402
from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter  # noqa: E402

from taller3 import config                            # noqa: E402
from taller3.sorting import SORTS                     # noqa: E402

ALGOS = [s.name for s in SORTS]
GROWTH = {s.name: s.growth for s in SORTS}
SHORT = {
    "InsertionSort": "Insertion",
    "DualPivotQuickSort": "Dual-Pivot QS",
    "MergeSort": "Merge",
    "HeapSort": "Heap",
    "RadixSort": "Radix",
    "BucketSort": "Bucket",
}
# Paleta categórica validada (orden fijo, nunca ciclado): azul, naranja, aqua, amarillo, magenta, verde
PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
VARIANT_COLOR = {"aleatoria": PALETTE[0], "ascendente": PALETTE[1], "descendente": PALETTE[2]}
LANG_COLOR = {"Java": PALETTE[0], "Python": PALETTE[1]}
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e4e3df"

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


# ----------------------------------------------------------------- datos
def load_rows(results_dir: Path) -> list[dict]:
    rows: list[dict] = []
    for name in ("ordenamiento_java.csv", "ordenamiento_python.csv"):
        path = results_dir / name
        if not path.exists():
            print(f"  (aviso) no existe {path}; se omite")
            continue
        with open(path, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                r["n"] = int(r["n"])
                r["mean_s"] = float(r["promedio_ns"]) / 1e9 if r["promedio_ns"] else None
                r["std_s"] = float(r["desv_estandar_ns"]) / 1e9 if r["desv_estandar_ns"] else None
                rows.append(r)
    return rows


def lookup(rows: list[dict]) -> dict[tuple, dict]:
    return {(r["lenguaje"], r["algoritmo"], r["variante"], r["n"]): r for r in rows}


# ------------------------------------------------------------- formato
def fmt_time(s: float) -> str:
    """Tiempo legible con coma decimal, como en el informe (p. ej. 1,37 s)."""
    if s < 1e-3:
        txt = f"{s * 1e6:.3g} µs"
    elif s < 1:
        txt = f"{s * 1e3:.3g} ms"
    elif s < 120:
        txt = f"{s:.3g} s"
    elif s < 7200:
        txt = f"{s / 60:.3g} min"
    else:
        txt = f"{s / 3600:.3g} h"
    return txt.replace(".", ",")


def fmt_n(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _decade_label(y: float, _pos=None) -> str:
    """Rótulos del eje: µs/ms por debajo de 1 s y segundos con separador de miles por
    encima (1 s, 10 s, ..., 10.000 s), para que cada década tenga un número redondo."""
    if y <= 0:
        return ""
    if y < 1:
        return fmt_time(y)
    return f"{y:,.0f} s".replace(",", ".")


def style_log_time_axis(ax) -> None:
    ax.set_yscale("log")
    ax.yaxis.set_major_locator(LogLocator(base=10))
    ax.yaxis.set_major_formatter(FuncFormatter(_decade_label))
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.grid(True, which="major", axis="y", color=GRID, linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)


def lighten(hex_color: str, amount: float = 0.6) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    return (r + (1 - r) * amount, g + (1 - g) * amount, b + (1 - b) * amount)


# ------------------------------------------------- 1) crecimiento (líneas)
def plot_growth(rows: list[dict], lang: str, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 6))
    any_est = False
    for i, algo in enumerate(ALGOS):
        pts = sorted((r["n"], r["mean_s"], r["estado"]) for r in rows
                     if r["lenguaje"] == lang and r["algoritmo"] == algo
                     and r["variante"] == "aleatoria" and r["mean_s"])
        if not pts:
            continue
        color = PALETTE[i]
        meas = [(n, t) for n, t, e in pts if e == "medido"]
        est = [(n, t) for n, t, e in pts if e == "estimado"]
        if meas:
            ax.plot([p[0] for p in meas], [p[1] for p in meas], "-o", color=color,
                    lw=2, ms=7, mec="white", mew=1.2, zorder=3)
        if est:
            any_est = True
            chain = ([meas[-1]] if meas else []) + est
            ax.plot([p[0] for p in chain], [p[1] for p in chain], "--", color=color, lw=2, zorder=2)
            ax.plot([p[0] for p in est], [p[1] for p in est], "o", color=color,
                    mfc="white", mew=2, ms=7, zorder=4)

    ax.set_xscale("log")
    ax.set_xticks(list(config.SIZES))
    ax.set_xticklabels([fmt_n(n) for n in config.SIZES])
    ax.xaxis.set_minor_formatter(NullFormatter())
    style_log_time_axis(ax)
    ax.grid(True, which="major", axis="x", color=GRID, linewidth=0.8)
    ax.set_xlabel("n (tamaño del arreglo, escala log)")
    ax.set_ylabel("Tiempo promedio de 5 repeticiones (escala log)")
    ax.set_title(f"Crecimiento del tiempo de ordenamiento — {lang}, entrada aleatoria",
                 loc="left", color=INK)

    handles = [Line2D([], [], color=PALETTE[i], lw=2, marker="o", mec="white", label=SHORT[a])
               for i, a in enumerate(ALGOS)]
    handles.append(Line2D([], [], color=INK_2, lw=2, marker="o", mec="white", label="medido"))
    if any_est:
        handles.append(Line2D([], [], color=INK_2, lw=2, ls="--", marker="o", mfc="white",
                              label="estimado (no ejecutado)"))
    ax.legend(handles=handles, loc="upper left", frameon=False, fontsize=9)
    fig.savefig(out)
    plt.close(fig)


# ------------------------------------------------- barras agrupadas (genérico)
def grouped_bars(ax, groups: list[str], series: list[str], colors: dict[str, str],
                 get) -> None:
    """get(grupo, serie) -> (valor_s | None, estado)."""
    width = 0.8 / len(series)
    values = [get(g, s)[0] for g in groups for s in series]
    values = [v for v in values if v]
    if not values:
        return
    ymin, ymax = min(values), max(values)
    decades = max(1.0, math.log10(ymax / ymin))
    bottom = ymin / 10 ** (0.15 * decades + 0.3)
    top = ymax * 10 ** (0.2 * decades + 0.6)           # espacio para las etiquetas verticales

    for j, s in enumerate(series):
        color = colors[s]
        for i, g in enumerate(groups):
            v, estado = get(g, s)
            x = i + (j - (len(series) - 1) / 2) * width
            if v is None:
                ax.text(x, bottom * 1.6, "sin dato" if estado != "fallido" else "falló",
                        rotation=90, ha="center", va="bottom", fontsize=7.5, color=INK_2)
                continue
            if estado == "estimado":
                ax.bar(x, v - bottom, width * 0.9, bottom=bottom, color=lighten(color),
                       edgecolor=color, hatch="////", linewidth=1.0, zorder=2)
                label = "~" + fmt_time(v)
            else:
                ax.bar(x, v - bottom, width * 0.9, bottom=bottom, color=color,
                       edgecolor="white", linewidth=1.0, zorder=2)
                label = fmt_time(v)
            ax.text(x, v * 1.12, label, rotation=90, ha="center", va="bottom",
                    fontsize=7.5, color=INK, zorder=3)

    ax.set_ylim(bottom, top)
    ax.set_xticks(range(len(groups)))
    ax.set_xticklabels([SHORT.get(g, g) for g in groups])
    ax.set_xlim(-0.6, len(groups) - 0.4)
    style_log_time_axis(ax)


def bars_legend(ax, series: list[str], colors: dict[str, str], any_est: bool) -> None:
    handles = [Patch(facecolor=colors[s], edgecolor="white", label=s) for s in series]
    if any_est:
        handles.append(Patch(facecolor=lighten(INK_2, 0.75), edgecolor=INK_2, hatch="////",
                             label="estimado (no ejecutado)"))
    ax.legend(handles=handles, loc="upper left", frameon=False, ncol=len(handles), fontsize=9)


# ------------------------------------------------- 2) efecto del orden de entrada
def plot_input_order(idx: dict, lang: str, n: int, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(11, 5.8))
    variants = list(config.VARIANTS)

    def get(algo: str, variant: str):
        r = idx.get((lang, algo, variant, n))
        return (r["mean_s"], r["estado"]) if r else (None, "")

    grouped_bars(ax, ALGOS, variants, VARIANT_COLOR, get)
    any_est = any(get(a, v)[1] == "estimado" for a in ALGOS for v in variants)
    bars_legend(ax, variants, VARIANT_COLOR, any_est)
    ax.set_ylabel("Tiempo promedio (escala log)")
    ax.set_title(f"Efecto del orden de entrada — {lang}, n = {fmt_n(n)}", loc="left", color=INK)
    fig.savefig(out)
    plt.close(fig)


# ------------------------------------------------- 3) compilado vs interpretado
def plot_languages(idx: dict, n: int, out: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 6.2))
    langs = ["Java", "Python"]

    def get(algo: str, lang: str):
        r = idx.get((lang, algo, "aleatoria", n))
        return (r["mean_s"], r["estado"]) if r else (None, "")

    grouped_bars(ax, ALGOS, langs, LANG_COLOR, get)
    # Segunda línea del rótulo: cuántas veces más lento es Python que Java
    labels = []
    for a in ALGOS:
        (tj, ej), (tp, ep) = get(a, "Java"), get(a, "Python")
        ratio = ""
        if tj and tp:
            approx = "~" if "estimado" in (ej, ep) else ""
            ratio = f"\nPy/Java {approx}{tp / tj:,.0f}×".replace(",", ".")
        labels.append(SHORT[a] + ratio)
    ax.set_xticklabels(labels)
    any_est = any(get(a, l)[1] == "estimado" for a in ALGOS for l in langs)
    bars_legend(ax, langs, LANG_COLOR, any_est)
    ax.set_ylabel("Tiempo promedio (escala log)")
    ax.set_title(f"Compilado (Java) frente a interpretado (Python) — n = {fmt_n(n)}, entrada aleatoria",
                 loc="left", color=INK)
    fig.savefig(out)
    plt.close(fig)


# ------------------------------------------------- tablas
def write_summary(rows: list[dict], out: Path) -> None:
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["lenguaje", "algoritmo", "variante", "n", "promedio_ms",
                    "desv_estandar_ms", "cv_porcentaje", "estado", "causa"])
        for r in sorted(rows, key=lambda r: (r["lenguaje"], ALGOS.index(r["algoritmo"]),
                                             config.VARIANTS.index(r["variante"]), r["n"])):
            m, s = r["mean_s"], r["std_s"]
            w.writerow([r["lenguaje"], r["algoritmo"], r["variante"], r["n"],
                        "" if m is None else f"{m * 1e3:.4f}",
                        "" if s is None else f"{s * 1e3:.4f}",
                        "" if (m is None or s is None or m == 0) else f"{100 * s / m:.1f}",
                        r["estado"], r["causa"]])


def write_growth_ratios(idx: dict, out: Path) -> None:
    sizes = list(config.SIZES)
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["lenguaje", "algoritmo", "variante", "n_desde", "n_hasta",
                    "razon_observada", "razon_teorica", "complejidad_caso", "estados"])
        for lang in ("Java", "Python"):
            for algo in ALGOS:
                for variant in config.VARIANTS:
                    g = GROWTH[algo][variant]
                    for a, b in zip(sizes, sizes[1:]):
                        ra, rb = idx.get((lang, algo, variant, a)), idx.get((lang, algo, variant, b))
                        if not ra or not rb or not ra["mean_s"] or not rb["mean_s"]:
                            continue
                        w.writerow([lang, algo, variant, a, b,
                                    f"{rb['mean_s'] / ra['mean_s']:.2f}",
                                    f"{g.f(b) / g.f(a):.2f}", g.value,
                                    f"{ra['estado']}->{rb['estado']}"])


def main() -> int:
    ap = argparse.ArgumentParser(description="Punto 1 - gráficas y tablas")
    ap.add_argument("--results", type=Path, default=config.RESULTS_DIR)
    ap.add_argument("--out", type=Path, default=config.FIGURES_DIR)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    rows = load_rows(args.results)
    if not rows:
        print("No hay resultados. Ejecuta primero los benchmarks.")
        return 1
    idx = lookup(rows)
    langs = sorted({r["lenguaje"] for r in rows})

    for lang in langs:
        plot_growth(rows, lang, args.out / f"p1_crecimiento_{lang.lower()}.png")
    if "Java" in langs:
        for n in (1_000, 10_000, 100_000):
            plot_input_order(idx, "Java", n, args.out / f"p1_orden_entrada_java_n{n}.png")
    plot_languages(idx, 1_000_000, args.out / "p1_java_vs_python_n1000000.png")
    write_summary(rows, args.out / "p1_resumen.csv")
    write_growth_ratios(idx, args.out / "p1_razones_crecimiento.csv")

    for p in sorted(args.out.glob("p1_*")):
        print(f"  {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
