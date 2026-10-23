"""
Medición de UNA ejecución de un algoritmo que modifica su arreglo in situ.

Reglas que garantiza esta función:
1. La copia del arreglo se hace ANTES de iniciar el reloj (no se mide).
2. Reloj de alta precisión: time.perf_counter_ns() (monótono, en ns).
3. El recolector cíclico de basura (gc) se desactiva SOLO durante la región
   medida, igual que hace el módulo estándar timeit. Antes se fuerza un
   gc.collect() para empezar siempre desde el mismo estado. Esto evita que
   una pausa del GC caiga aleatoriamente dentro de una repetición y aumente
   la desviación estándar. (El conteo de referencias de CPython sigue
   liberando memoria normalmente; solo se pausa el detector de ciclos.)
4. La verificación del resultado la hace quien llama, fuera del tiempo.

time_searches (Punto 2) aplica las mismas reglas a una pasada de búsquedas.
"""
from __future__ import annotations

import gc
import time
from typing import Callable


def time_inplace(func: Callable[[list[int]], None], base: list[int]) -> tuple[int, list[int]]:
    work = base.copy()                 # copia nueva (fuera del tiempo)
    gc.collect()
    gc_was_enabled = gc.isenabled()
    gc.disable()
    try:
        t0 = time.perf_counter_ns()
        func(work)
        t1 = time.perf_counter_ns()
    finally:
        if gc_was_enabled:
            gc.enable()
    return t1 - t0, work


def time_searches(func: Callable[[list[int], int], int], arr: list[int],
                  keys: list[int], out: list[int]) -> int:
    """Mide UNA pasada: out[j] = func(arr, keys[j]) para j = 0..K-1 (Punto 2, spec 6.3).

    - No copia arr: la búsqueda no lo modifica (el benchmark lo comprueba al final de cada n).
    - out viene preasignado por quien llama (fuera del tiempo) y guarda cada resultado:
      así el trabajo no se descarta y la verificación/checksum se hacen después, fuera
      del tiempo. Mismo manejo del gc que time_inplace.
    """
    k = len(keys)
    gc.collect()
    gc_was_enabled = gc.isenabled()
    gc.disable()
    try:
        t0 = time.perf_counter_ns()
        for j in range(k):
            out[j] = func(arr, keys[j])
        t1 = time.perf_counter_ns()
    finally:
        if gc_was_enabled:
            gc.enable()
    return t1 - t0


def fmt_ns(ns: float) -> str:
    """Formato legible: 532 µs, 12.3 ms, 4.56 s, 3.2 min."""
    if ns < 1e6:
        return f"{ns / 1e3:.1f} µs"
    if ns < 1e9:
        return f"{ns / 1e6:.2f} ms"
    if ns < 120e9:
        return f"{ns / 1e9:.2f} s"
    return f"{ns / 60e9:.1f} min"
