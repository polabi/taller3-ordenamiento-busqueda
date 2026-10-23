"""
Búsqueda por saltos, salto m = floor(sqrt(n)).
Fuente: GeeksforGeeks, "Jump Search",
        https://www.geeksforgeeks.org/dsa/jump-search/
Desviación respecto a GfG Python: m es entero (math.isqrt), como en GfG Java, para que
la secuencia de índices sea la misma en ambos lenguajes.
Desviación: si n == 0 se devuelve -1 de inmediato (con una lista vacía GfG accedería a
arr[-1] y lanzaría IndexError).
Equivalente línea a línea: java/src/taller3/searching/JumpSearch.java
"""
from __future__ import annotations

import math


def jump_search(arr: list[int], x: int) -> int:
    n = len(arr)
    if n == 0:
        return -1
    m = math.isqrt(n)
    step = m
    prev = 0
    # Salta bloques mientras el último elemento del bloque sea menor que x
    while arr[(step if step < n else n) - 1] < x:
        prev = step
        step = step + m
        if prev >= n:
            return -1
    # Recorrido lineal dentro del bloque [prev, min(step, n))
    while arr[prev] < x:
        prev = prev + 1
        if prev == (step if step < n else n):
            return -1
    if arr[prev] == x:
        return prev
    return -1
