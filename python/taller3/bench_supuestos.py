"""
Punto 3 - Experimento de supuestos en Python (spec p3 6): qué pasa con Bucket Sort y Radix
Sort cuando los datos no cumplen el supuesto de cada uno.

    cd python
    python3 -m taller3.bench_supuestos                                # corrida completa
    python3 -m taller3.bench_supuestos --sizes 10000 --reps 2 --out ../results/prueba_sup.csv
    python3 -m taller3.bench_supuestos --algos RadixSort --distribuciones digitos16

Casos (6.2), en este orden: n ascendente; dentro de cada n, BucketSort y luego RadixSort;
dentro de cada algoritmo, las distribuciones en el orden de config:
  BucketSort  {uniforme, rango_pequeno, concentrado_extremos}  n ∈ SUPUESTOS_SIZES (10^4, 10^5)
  RadixSort   {uniforme, digitos16}                            n ∈ DIGITOS16_SIZES (10^4, 10^5, 10^6)
`uniforme` es data/aleatoria_{n}.txt del Punto 1 y se vuelve a medir aquí, para que la
comparación con las otras distribuciones sea en las mismas condiciones.
--sizes, --distribuciones y --algos solo FILTRAN esa tabla (las combinaciones que no
existen se saltan); falla si un valor no vale para ningún algoritmo o si no queda nada.

Por cada caso (6.3, igual que el Punto 1): la referencia sorted(base) se calcula UNA vez
fuera del tiempo; 5 repeticiones con time_inplace (copia -> gc.collect -> gc.disable ->
perf_counter_ns -> algoritmo -> perf_counter_ns), cada una verificada contra la referencia
fuera del tiempo. Límite de 300 s con predicción t(n_prev)·f(n)/f(n_prev) (6.4).

CPython no tiene JIT activo por defecto: no hay calentamiento (como bench_sort.py).
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

from taller3 import config
from taller3.common.dataio import load_supuestos, sha256_of, supuestos_path
from taller3.common.estimation import Growth, describe, extrapolate
from taller3.common.results import ResultRecord, SupuestosCsvWriter
from taller3.common.stats import mean, sample_std
from taller3.common.timing import fmt_ns, time_inplace
from taller3.sorting import BY_NAME, SortSpec

LANG = "Python"
ALGOS = ("BucketSort", "RadixSort")                   # orden de ejecución dentro de cada n (6.2)

# Complejidad para predecir/estimar (spec 6.4).
_GROWTH = {
    ("BucketSort", "uniforme"): Growth.N,
    ("BucketSort", "rango_pequeno"): Growth.N,
    ("BucketSort", "concentrado_extremos"): Growth.N2,
    ("RadixSort", "uniforme"): Growth.N,
    ("RadixSort", "digitos16"): Growth.N,
}


def supuestos_growth(algoritmo: str, distribucion: str) -> Growth:
    """Complejidad del par (algoritmo, distribución); ValueError si el par no existe."""
    try:
        return _GROWTH[(algoritmo, distribucion)]
    except KeyError:
        raise ValueError(f"Par sin complejidad declarada: {algoritmo} / {distribucion}") from None


def environment_path(out: Path) -> Path:
    """entorno_<stem del CSV>.json junto al CSV (no pisa entorno_python.json del Punto 1)."""
    return out.with_name(f"entorno_{out.stem}.json")


def plan(algos: list[str], sizes: list[int] | None,
         dists: list[str] | None) -> list[tuple[int, str, str]]:
    """Casos (n, algoritmo, distribución) en el orden de 6.2, filtrados por los flags."""
    table = {"BucketSort": (config.SUPUESTOS_SIZES, config.BUCKET_DISTRIBUTIONS),
             "RadixSort": (config.DIGITOS16_SIZES, config.RADIX_DISTRIBUTIONS)}
    valid_sizes = {n for s, _ in table.values() for n in s}
    valid_dists = {d for _, ds in table.values() for d in ds}
    for n in sizes or []:
        if n not in valid_sizes:
            raise ValueError(f"--sizes: {n} no vale para ningún algoritmo (válidos: {sorted(valid_sizes)})")
    for d in dists or []:
        if d not in valid_dists:
            raise ValueError(f"--distribuciones: {d!r} no existe (válidas: {sorted(valid_dists)})")
    cases = []
    for n in sorted(valid_sizes):
        if sizes is not None and n not in sizes:
            continue
        for algo in ALGOS:
            if algo not in algos:
                continue
            algo_sizes, algo_dists = table[algo]
            if n not in algo_sizes:
                continue
            for d in algo_dists:
                if dists is None or d in dists:
                    cases.append((n, algo, d))
    if not cases:
        raise ValueError("Los filtros --sizes/--distribuciones/--algos no dejan ningún caso")
    return cases


class SupuestosBenchmark:
    def __init__(self, reps: int, limit_s: float):
        self.reps = reps
        self.limit_ns = limit_s * 1e9
        self.limit_s = limit_s
        self.last_measured: dict[tuple[str, str], tuple[int, float]] = {}   # -> (n, promedio_ns)

    def _estimated(self, spec: SortSpec, dist: str, n: int, causa: str) -> ResultRecord:
        prev = self.last_measured.get((spec.name, dist))
        if prev is None:
            return ResultRecord(spec.name, LANG, "aleatoria", n, estado="fallido",
                                causa=causa + " | sin medición previa para estimar")
        n0, t0 = prev
        growth = supuestos_growth(spec.name, dist)
        return ResultRecord(spec.name, LANG, "aleatoria", n,
                            promedio_ns=extrapolate(t0, n0, n, growth),
                            estado="estimado", causa=causa,
                            base_estimacion=describe(t0, n0, n, growth))

    def run_case(self, spec: SortSpec, dist: str, base: list[int],
                 expected: list[int]) -> ResultRecord:
        n = len(base)
        key = (spec.name, dist)
        prev = self.last_measured.get(key)
        if prev is not None:
            predicted = extrapolate(prev[1], prev[0], n, supuestos_growth(spec.name, dist))
            if predicted > self.limit_ns:
                return self._estimated(spec, dist, n,
                                       f"predicción {predicted / 1e9:,.0f} s > límite de "
                                       f"{self.limit_s:.0f} s por ejecución")

        times: list[int] = []
        note = ""
        for r in range(self.reps):
            t, work = time_inplace(spec.func, base)
            if work != expected:                       # verificación, fuera del tiempo
                raise AssertionError(f"{spec.name} NO ordenó bien: {dist}, n={n}")
            times.append(t)
            if t > self.limit_ns and r < self.reps - 1:
                note = (f"la repetición {r + 1} tardó {t / 1e9:.0f} s (> límite); "
                        f"se detuvieron las repeticiones restantes")
                break

        m = mean(times)
        self.last_measured[key] = (n, m)
        return ResultRecord(spec.name, LANG, "aleatoria", n, reps_ns=times,
                            promedio_ns=m, desv_estandar_ns=sample_std(times),
                            estado="medido", causa=note)


def write_environment(path: Path, args: argparse.Namespace, started: str,
                      cases: list[tuple[int, str, str]], sha_used: dict[str, str]) -> None:
    from taller3.bench_search import sysctl
    info = {
        "lenguaje": LANG,
        "implementacion": platform.python_implementation(),
        "version": sys.version,
        "plataforma": platform.platform(),
        "procesador": platform.processor() or platform.machine(),
        "modelo": sysctl("hw.model"),
        "cpu": sysctl("machdep.cpu.brand_string"),
        "nucleos": os.cpu_count(),
        "reloj": "time.perf_counter_ns()",
        "gc": "gc.collect() antes y gc.disable() durante cada medición (como timeit)",
        "repeticiones": args.reps,
        "limite_s": args.limit,
        "tamanos": sorted({n for n, _, _ in cases}),
        "algoritmos": [a for a in ALGOS if any(c[1] == a for c in cases)],
        "distribuciones": list(dict.fromkeys(d for _, _, d in cases)),
        "datos_p3_sha256": sha_used,
        "inicio_utc": started,
        "fin_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    path.write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Punto 3 - experimento de supuestos (Python)")
    ap.add_argument("--sizes", type=int, nargs="+", default=None,
                    help="filtra los tamaños (por defecto los de cada algoritmo)")
    ap.add_argument("--distribuciones", nargs="+", default=None,
                    help="filtra las distribuciones (por defecto las de cada algoritmo)")
    ap.add_argument("--algos", nargs="+", default=list(ALGOS), choices=list(ALGOS))
    ap.add_argument("--reps", type=int, default=config.REPETITIONS)
    ap.add_argument("--limit", type=float, default=config.TIME_LIMIT_SECONDS,
                    help="límite en segundos por ejecución (por defecto 300)")
    ap.add_argument("--out", type=Path, default=config.RESULTS_DIR / "supuestos_python.csv")
    args = ap.parse_args()

    try:
        cases = plan(args.algos, args.sizes, args.distribuciones)
    except ValueError as e:
        ap.error(str(e))
    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    bench = SupuestosBenchmark(args.reps, args.limit)
    sha_used: dict[str, str] = {}

    print(f"[{LANG}] {sys.version.split()[0]} | reps={args.reps} | límite={args.limit:.0f} s "
          f"| salida: {args.out}")
    with SupuestosCsvWriter(args.out, args.reps) as writer:
        for n, algo, dist in cases:
            base = load_supuestos(dist, n)             # carga fuera de toda medición
            expected = sorted(base)                    # referencia independiente, una vez
            if dist != "uniforme":
                path = supuestos_path(dist, n)
                sha_used[path.relative_to(config.DATA_DIR).as_posix()] = sha256_of(path)
            rec = bench.run_case(BY_NAME[algo], dist, base, expected)
            writer.write(rec, dist)
            if rec.promedio_ns is None:
                shown = "—"
            elif rec.estado == "medido":
                shown = f"{fmt_ns(rec.promedio_ns)} ± {fmt_ns(rec.desv_estandar_ns)}"
            else:
                shown = f"~{fmt_ns(rec.promedio_ns)}"
            extra = f"  [{rec.causa}]" if rec.causa else ""
            print(f"  n={n:>9,}  {algo:<11} {dist:<21} {shown:>24}  {rec.estado}{extra}", flush=True)
            del base, expected

    write_environment(environment_path(args.out), args, started, cases, sha_used)
    print("Listo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
