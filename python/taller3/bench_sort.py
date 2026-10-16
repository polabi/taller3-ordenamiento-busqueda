"""
Punto 1 - Benchmark de ordenamiento en Python (lenguaje interpretado).

    cd python
    python3 -m taller3.bench_sort                       # corrida completa
    python3 -m taller3.bench_sort --sizes 1000 10000    # corrida rápida de prueba
    python3 -m taller3.bench_sort --algos MergeSort HeapSort --reps 3

Flujo por cada (n, algoritmo, variante):
  1. Si ya falló en un n menor (RecursionError) -> no se ejecuta; se ESTIMA.
  2. Si la predicción t(n_prev)·f(n)/f(n_prev) supera el límite -> se ESTIMA.
  3. Si no, 5 repeticiones; cada una sobre una copia nueva del arreglo,
     midiendo solo el algoritmo y verificando el resultado fuera del tiempo
     contra el arreglo ascendente de referencia (data/ascendente_n.txt).
     Comparar con la referencia comprueba a la vez que quedó ORDENADO y que
     es una PERMUTACIÓN de la entrada (no se perdió ni duplicó ningún valor).

CPython no tiene compilación JIT activa por defecto, por eso no se hace
calentamiento (el taller lo exige solo para lenguajes con JIT).
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

from taller3 import config
from taller3.common.dataio import load_dataset
from taller3.common.estimation import describe, extrapolate
from taller3.common.results import CsvResultWriter, ResultRecord
from taller3.common.stats import mean, sample_std
from taller3.common.timing import fmt_ns, time_inplace
from taller3.sorting import BY_NAME, SORTS, SortSpec

LANG = "Python"


class SortBenchmark:
    def __init__(self, reps: int, limit_s: float):
        self.reps = reps
        self.limit_ns = limit_s * 1e9
        self.limit_s = limit_s
        self.last_measured: dict[tuple[str, str], tuple[int, float]] = {}   # -> (n, promedio_ns)
        self.failed: dict[tuple[str, str], tuple[int, str]] = {}            # -> (n, causa)

    # -- estimación -----------------------------------------------------------
    def _estimated(self, spec: SortSpec, variant: str, n: int, causa: str) -> ResultRecord:
        key = (spec.name, variant)
        prev = self.last_measured.get(key)
        if prev is None:
            return ResultRecord(spec.name, LANG, variant, n, estado="fallido",
                                causa=causa + " | sin medición previa para estimar")
        n0, t0 = prev
        growth = spec.growth[variant]
        return ResultRecord(spec.name, LANG, variant, n,
                            promedio_ns=extrapolate(t0, n0, n, growth),
                            estado="estimado", causa=causa,
                            base_estimacion=describe(t0, n0, n, growth))

    # -- un caso --------------------------------------------------------------
    def run_case(self, spec: SortSpec, variant: str, n: int,
                 base: list[int], expected: list[int]) -> ResultRecord:
        key = (spec.name, variant)

        if key in self.failed:
            n_fail, cause = self.failed[key]
            return self._estimated(spec, variant, n,
                                   f"no ejecutado: falló con {cause} en n={n_fail} "
                                   f"y la profundidad de recursión crece con n")

        prev = self.last_measured.get(key)
        if prev is not None:
            predicted = extrapolate(prev[1], prev[0], n, spec.growth[variant])
            if predicted > self.limit_ns:
                return self._estimated(spec, variant, n,
                                       f"predicción {predicted / 1e9:,.0f} s > límite de "
                                       f"{self.limit_s:.0f} s por ejecución")

        times: list[int] = []
        note = ""
        for r in range(self.reps):
            try:
                t, work = time_inplace(spec.func, base)
            except RecursionError:
                self.failed[key] = (n, "RecursionError")
                return self._estimated(spec, variant, n,
                                       f"RecursionError en la repetición {r + 1} "
                                       f"(sys.getrecursionlimit() = {sys.getrecursionlimit()})")
            if work != expected:                       # verificación, fuera del tiempo
                raise AssertionError(f"{spec.name} NO ordenó bien: {variant}, n={n}")
            times.append(t)
            if t > self.limit_ns and r < self.reps - 1:
                note = (f"la repetición {r + 1} tardó {t / 1e9:.0f} s (> límite); "
                        f"se detuvieron las repeticiones restantes")
                break

        m = mean(times)
        self.last_measured[key] = (n, m)
        return ResultRecord(spec.name, LANG, variant, n, reps_ns=times,
                            promedio_ns=m, desv_estandar_ns=sample_std(times),
                            estado="medido", causa=note)


def write_environment(path: Path, args: argparse.Namespace, started: str) -> None:
    info = {
        "lenguaje": LANG,
        "implementacion": platform.python_implementation(),
        "version": sys.version,
        "plataforma": platform.platform(),
        "procesador": platform.processor() or platform.machine(),
        "limite_recursion": sys.getrecursionlimit(),
        "reloj": "time.perf_counter_ns()",
        "gc": "gc.collect() antes y gc.disable() durante cada medición (como timeit)",
        "repeticiones": args.reps,
        "limite_s": args.limit,
        "inicio_utc": started,
        "fin_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    path.write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Punto 1 - benchmark de ordenamiento (Python)")
    ap.add_argument("--sizes", type=int, nargs="+", default=list(config.SIZES))
    ap.add_argument("--algos", nargs="+", default=[s.name for s in SORTS],
                    choices=[s.name for s in SORTS])
    ap.add_argument("--variants", nargs="+", default=list(config.VARIANTS),
                    choices=list(config.VARIANTS))
    ap.add_argument("--reps", type=int, default=config.REPETITIONS)
    ap.add_argument("--limit", type=float, default=config.TIME_LIMIT_SECONDS,
                    help="límite en segundos por ejecución (por defecto 300)")
    ap.add_argument("--out", type=Path, default=config.RESULTS_DIR / "ordenamiento_python.csv")
    args = ap.parse_args()

    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    bench = SortBenchmark(args.reps, args.limit)
    specs = [BY_NAME[a] for a in args.algos]

    print(f"[{LANG}] {sys.version.split()[0]} | reps={args.reps} | límite={args.limit:.0f} s "
          f"| salida: {args.out}")
    with CsvResultWriter(args.out, args.reps) as writer:
        for n in sorted(args.sizes):
            ds = load_dataset(n)                       # carga fuera de toda medición
            expected = ds.ascendente
            for spec in specs:
                for variant in args.variants:
                    rec = bench.run_case(spec, variant, n, ds.get(variant), expected)
                    writer.write(rec)
                    if rec.promedio_ns is None:
                        shown = "—"
                    elif rec.estado == "medido":
                        shown = f"{fmt_ns(rec.promedio_ns)} ± {fmt_ns(rec.desv_estandar_ns)}"
                    else:
                        shown = f"~{fmt_ns(rec.promedio_ns)}"
                    extra = f"  [{rec.causa}]" if rec.causa else ""
                    print(f"  n={n:>9,}  {spec.name:<19} {variant:<11} {shown:>24}  "
                          f"{rec.estado}{extra}", flush=True)
            del ds

    write_environment(args.out.with_name("entorno_python.json"), args, started)
    print("Listo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
