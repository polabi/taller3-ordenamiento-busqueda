"""
Punto 2 - Benchmark de búsqueda en Python (lenguaje interpretado).

    cd python
    python3 -m taller3.bench_search                                  # corrida completa
    python3 -m taller3.bench_search --sizes 1000 10000 --out ../results/prueba_busq.csv
    python3 -m taller3.bench_search --algos BinarySearch JumpSearch --variants claves

Experimentos (spec p2 6.2), en este orden para cada n ascendente:
  1. `claves`: cada algoritmo busca las 1.000 claves de data/claves_busqueda.txt en
     data/ascendente_n.txt (1 pasada = 1 ejecución).
  2. Solo si n = 1.000.000: cada algoritmo busca 1.000 veces la clave de `inicio`,
     `centro` (índice (n-1)//2), `centro_alto` (n//2) y `final` (n-1).

Por cada caso:
  - Predicción del tiempo de una pasada; si supera el límite (300 s) -> ESTIMADO.
      claves:    t(n_prev)·f(n)/f(n_prev) con el mayor n medido (como el Punto 1).
      posición:  t(claves, n=10^6) x factor (costo de la pasada `final` / pasada `claves`).
  - Si no, 5 repeticiones con time_searches (gc.collect antes, gc.disable durante).
  - Cada pasada se verifica FUERA del tiempo contra un oráculo independiente (bisect):
    out[j] == -1 <=> la clave no está; si no, arr[out[j]] == clave. encontradas y
    checksum (Σ out[j], incluidos los -1) deben ser iguales en las 5 repeticiones.
  - El arreglo no se copia (la búsqueda no lo modifica); al terminar cada n se
    comprueba que sigue igual al archivo cargado.

CPython no tiene JIT activo por defecto: no hay calentamiento (como bench_sort.py).
"""
from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from bisect import bisect_left, bisect_right
from datetime import datetime, timezone
from pathlib import Path

from taller3 import config
from taller3.common.dataio import dataset_path, load_search_keys, read_ints, search_keys_path, sha256_of
from taller3.common.estimation import describe, extrapolate
from taller3.common.results import SearchCsvWriter, SearchResultRecord
from taller3.common.stats import mean, sample_std
from taller3.common.timing import fmt_ns, time_searches
from taller3.searching import BY_NAME, SEARCHES, SearchSpec

LANG = "Python"

# Factor de la predicción de las posiciones = costo de la pasada `final` / costo de la
# pasada `claves` (spec 6.5). El mismo factor, conservador, para las cuatro posiciones.
#   Lineal: final = 10^9 comparaciones; claves = 748.440.213 -> 1,336 ~ 4/3.
#   Interpolación div. entera: final ~ 10^9 iteraciones; claves ~ n/2 por clave -> 2.
#   Resto: 4/3 (irrelevante: sus pasadas duran microsegundos).
POSITION_FACTOR = {"LinearSearch": (4 / 3, "4/3"), "InterpolationSearchIntDiv": (2.0, "2")}
DEFAULT_POSITION_FACTOR = (4 / 3, "4/3")


def position_index(variante: str, n: int) -> int:
    """Índice de la clave de cada experimento de posición (spec 6.2)."""
    if variante == "inicio":
        return 0
    if variante == "centro":
        return (n - 1) // 2
    if variante == "centro_alto":
        return n // 2
    if variante == "final":
        return n - 1
    raise ValueError(f"Variante de posición desconocida: {variante!r}")


def environment_path(out: Path) -> Path:
    """entorno_<stem del CSV>.json junto al CSV (no pisa entorno_python.json del Punto 1)."""
    return out.with_name(f"entorno_{out.stem}.json")


def check_position_keys(arr: list[int]) -> None:
    """Las 4 claves de posición deben ser ÚNICAS en el arreglo (spec 6.2)."""
    for v in config.POSITION_VARIANTS:
        key = arr[position_index(v, len(arr))]
        count = bisect_right(arr, key) - bisect_left(arr, key)
        if count != 1:
            raise AssertionError(f"La clave de {v} ({key}) aparece {count} veces en el arreglo")


def presence(arr: list[int], keys: list[int]) -> list[bool]:
    """Oráculo independiente (bisect de la biblioteca estándar): ¿está cada clave?"""
    n = len(arr)
    result = []
    for k in keys:
        i = bisect_left(arr, k)
        result.append(i < n and arr[i] == k)
    return result


def verify_pass(name: str, variant: str, arr: list[int], keys: list[int],
                present: list[bool], out: list[int]) -> tuple[int, int]:
    """Verifica una pasada (fuera del tiempo) y devuelve (encontradas, checksum)."""
    n = len(arr)
    found = 0
    checksum = 0
    for j in range(len(keys)):
        o = out[j]
        if o == -1:
            if present[j]:
                raise AssertionError(f"{name} no encontró la clave {keys[j]} ({variant}, n={n})")
        else:
            if not (0 <= o < n) or arr[o] != keys[j]:
                raise AssertionError(f"{name} devolvió el índice {o} para la clave {keys[j]} "
                                     f"({variant}, n={n})")
            found += 1
        checksum += o                                 # incluye los -1 (spec 6.3)
    return found, checksum


class SearchBenchmark:
    def __init__(self, reps: int, limit_s: float):
        self.reps = reps
        self.limit_ns = limit_s * 1e9
        self.limit_s = limit_s
        self.last_measured: dict[str, tuple[int, float]] = {}       # claves: alg -> (n, promedio_ns)
        self.claves_at: dict[tuple[str, int], tuple[float, str]] = {}  # (alg, n) -> (promedio_ns, estado)

    # -- predicción -----------------------------------------------------------
    def predict_claves(self, spec: SearchSpec, n: int) -> tuple[float, str] | None:
        prev = self.last_measured.get(spec.name)
        if prev is None:
            return None
        n0, t0 = prev
        return extrapolate(t0, n0, n, spec.growth), describe(t0, n0, n, spec.growth)

    def predict_position(self, spec: SearchSpec, n: int) -> tuple[float, str] | None:
        factor, factor_txt = POSITION_FACTOR.get(spec.name, DEFAULT_POSITION_FACTOR)
        base = self.claves_at.get((spec.name, n))
        if base is None:                              # sin `claves` en este n: se extrapola
            pred = self.predict_claves(spec, n)
            if pred is None:
                return None
            t, txt = pred
            return t * factor, f"[{txt}] x {factor_txt} (pasada final / pasada claves)"
        t, estado = base
        return t * factor, (f"t_claves({n})={t / 1e9:.6g} s ({estado}) x {factor_txt} "
                            f"(pasada final / pasada claves)")

    # -- un caso --------------------------------------------------------------
    def run_case(self, spec: SearchSpec, variant: str, arr: list[int],
                 keys: list[int], present: list[bool], clave: int | None) -> SearchResultRecord:
        n = len(arr)
        rec = SearchResultRecord(spec.name, LANG, variant, n, num_busquedas=len(keys), clave=clave)
        pred = self.predict_claves(spec, n) if variant == "claves" else self.predict_position(spec, n)
        if pred is not None and pred[0] > self.limit_ns:
            rec.promedio_ns = pred[0]
            rec.estado = "estimado"
            rec.causa = (f"predicción {pred[0] / 1e9:,.0f} s > límite de "
                         f"{self.limit_s:.0f} s por ejecución")
            rec.base_estimacion = pred[1]
            if variant == "claves":
                self.claves_at[(spec.name, n)] = (pred[0], "estimado")
            return rec

        out = [0] * len(keys)                         # preasignado, fuera del tiempo
        times: list[int] = []
        result = None
        note = ""
        for r in range(self.reps):
            t = time_searches(spec.func, arr, keys, out)
            check = verify_pass(spec.name, variant, arr, keys, present, out)   # fuera del tiempo
            if result is not None and check != result:
                raise AssertionError(f"{spec.name}: encontradas/checksum cambiaron entre "
                                     f"repeticiones ({variant}, n={n}): {result} vs {check}")
            result = check
            times.append(t)
            if t > self.limit_ns and r < self.reps - 1:
                note = (f"la repetición {r + 1} tardó {t / 1e9:.0f} s (> límite); "
                        f"se detuvieron las repeticiones restantes")
                break

        m = mean(times)
        rec.reps_ns = times
        rec.promedio_ns = m
        rec.desv_estandar_ns = sample_std(times)
        rec.encontradas, rec.checksum = result
        rec.causa = note
        if variant == "claves":
            self.last_measured[spec.name] = (n, m)
            self.claves_at[(spec.name, n)] = (m, "medido")
        return rec


def clock_resolution_ns(samples: int = 1000) -> int:
    """Mínima diferencia > 0 entre lecturas consecutivas de perf_counter_ns (spec 6.5)."""
    reads = [time.perf_counter_ns() for _ in range(samples)]
    diffs = [b - a for a, b in zip(reads, reads[1:]) if b > a]
    best = diffs[0] if diffs else 0
    for d in diffs:
        if d < best:
            best = d
    return best


def write_environment(path: Path, args: argparse.Namespace, started: str, keys_sha: str,
                      resolution_ns: int) -> None:
    info = {
        "lenguaje": LANG,
        "implementacion": platform.python_implementation(),
        "version": sys.version,
        "plataforma": platform.platform(),
        "procesador": platform.processor() or platform.machine(),
        "reloj": "time.perf_counter_ns()",
        "resolucion_reloj_ns": resolution_ns,
        "gc": "gc.collect() antes y gc.disable() durante cada pasada (como timeit)",
        "claves": config.SEARCH_KEYS_FILE,
        "claves_sha256": keys_sha,
        "num_busquedas": config.NUM_SEARCH_KEYS,
        "repeticiones": args.reps,
        "limite_s": args.limit,
        "tamanos": sorted(args.sizes),
        "algoritmos": args.algos,
        "variantes": args.variants,
        "inicio_utc": started,
        "fin_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    path.write_text(json.dumps(info, indent=2, ensure_ascii=False), encoding="utf-8")


def fmt_search_ns(ns: float) -> str:
    """Como fmt_ns, pero en ns por debajo de 1 µs (una búsqueda binaria dura decenas de ns)."""
    return f"{ns:.1f} ns" if ns < 1e3 else fmt_ns(ns)


def print_record(rec: SearchResultRecord) -> None:
    if rec.promedio_ns is None:
        shown = "—"
    elif rec.estado == "medido":
        shown = (f"{fmt_search_ns(rec.promedio_ns / rec.num_busquedas)} ± "
                 f"{fmt_search_ns(rec.desv_estandar_ns / rec.num_busquedas)} /búsq.")
    else:
        shown = f"~{fmt_search_ns(rec.promedio_ns / rec.num_busquedas)} /búsq."
    extra = f"  [{rec.causa}]" if rec.causa else ""
    print(f"  n={rec.n:>9,}  {rec.algoritmo:<25} {rec.variante:<11} {shown:>30}  "
          f"{rec.estado}{extra}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="Punto 2 - benchmark de búsqueda (Python)")
    ap.add_argument("--sizes", type=int, nargs="+", default=list(config.SIZES))
    ap.add_argument("--algos", nargs="+", default=[s.name for s in SEARCHES],
                    choices=[s.name for s in SEARCHES])
    ap.add_argument("--variants", nargs="+", default=list(config.SEARCH_VARIANTS),
                    choices=list(config.SEARCH_VARIANTS))
    ap.add_argument("--reps", type=int, default=config.REPETITIONS)
    ap.add_argument("--limit", type=float, default=config.TIME_LIMIT_SECONDS,
                    help="límite en segundos por pasada de 1.000 búsquedas (por defecto 300)")
    ap.add_argument("--out", type=Path, default=config.RESULTS_DIR / "busqueda_python.csv")
    args = ap.parse_args()

    started = datetime.now(timezone.utc).isoformat(timespec="seconds")
    specs = [BY_NAME[a] for a in args.algos]
    variants = [v for v in config.SEARCH_VARIANTS if v in args.variants]   # orden de la spec
    positions = [v for v in variants if v != "claves"]
    sizes = sorted(args.sizes)

    keys = load_search_keys()                         # carga fuera de toda medición
    keys_sha = sha256_of(search_keys_path())
    resolution = clock_resolution_ns()
    if positions and config.POSITION_N in sizes:      # al arrancar: claves de posición únicas
        check_position_keys(read_ints(dataset_path("ascendente", config.POSITION_N),
                                      config.POSITION_N))

    print(f"[{LANG}] {sys.version.split()[0]} | reps={args.reps} | límite={args.limit:.0f} s "
          f"| resolución del reloj ≈ {resolution} ns | salida: {args.out}")
    bench = SearchBenchmark(args.reps, args.limit)
    with SearchCsvWriter(args.out, args.reps) as writer:
        for n in sizes:
            arr = read_ints(dataset_path("ascendente", n), n)
            snapshot = list(arr)                      # para comprobar que nadie lo modificó
            if "claves" in variants:
                present = presence(arr, keys)
                for spec in specs:
                    rec = bench.run_case(spec, "claves", arr, keys, present, None)
                    writer.write(rec)
                    print_record(rec)
            if n == config.POSITION_N:
                for spec in specs:
                    for v in positions:
                        key = arr[position_index(v, n)]
                        pos_keys = [key] * config.NUM_SEARCH_KEYS     # armado fuera del tiempo
                        rec = bench.run_case(spec, v, arr, pos_keys,
                                             [True] * config.NUM_SEARCH_KEYS, key)
                        writer.write(rec)
                        print_record(rec)
            if arr != snapshot:
                raise AssertionError(f"Algún algoritmo modificó el arreglo (n={n})")
            del arr, snapshot

    write_environment(environment_path(args.out), args, started, keys_sha, resolution)
    print("Listo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
