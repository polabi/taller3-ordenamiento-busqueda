"""
Búsqueda por interpolación (iterativa), fórmula en coma flotante del código Python iterativo
de GfG (float(high - low) / ...), la misma que usan C++ y C con double. Ojo: las pestañas Java
de GfG usan división entera; esa fórmula está en interpolation_search_int_div.py.
Fuente: GeeksforGeeks, "Interpolation Search",
        https://www.geeksforgeeks.org/dsa/interpolation-search/
Desviación: guarda arr[lo] == arr[hi] (no solo lo == hi) para no dividir por 0 con
duplicados (specs/p2-busqueda.md, 3.5, regla G).
Equivalente línea a línea: java/src/taller3/searching/InterpolationSearch.java
"""
from __future__ import annotations


def interpolation_search(arr: list[int], x: int) -> int:
    n = len(arr)
    lo = 0
    hi = n - 1
    while lo <= hi and x >= arr[lo] and x <= arr[hi]:
        # Guarda G: arr[lo] <= x <= arr[hi] == arr[lo] implica x == arr[lo]
        if arr[lo] == arr[hi]:
            return lo
        # Mismas dos operaciones double que Java, en el mismo orden; int() trunca hacia cero
        pos = lo + int(float(hi - lo) / (arr[hi] - arr[lo]) * (x - arr[lo]))
        if arr[pos] == x:
            return pos
        if arr[pos] < x:
            lo = pos + 1
        else:
            hi = pos - 1
    return -1
