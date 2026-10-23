"""
Búsqueda por interpolación (iterativa), VARIANTE con la fórmula de división entera de los
códigos Java (ambas pestañas) y Python recursivo de GfG: (hi - lo) // (arr[hi] - arr[lo]) se calcula antes de multiplicar.
Con valores de 8 dígitos y n <= 10^6 ese cociente es 0, pos = lo y la búsqueda es O(n)
(specs/p2-busqueda.md, 3.5.2).
Fuente: GeeksforGeeks, "Interpolation Search",
        https://www.geeksforgeeks.org/dsa/interpolation-search/
Desviación: guarda arr[lo] == arr[hi] (regla G de la spec, 3.5).
Equivalente línea a línea: java/src/taller3/searching/InterpolationSearchIntDiv.java
"""
from __future__ import annotations


def interpolation_search_int_div(arr: list[int], x: int) -> int:
    n = len(arr)
    lo = 0
    hi = n - 1
    while lo <= hi and x >= arr[lo] and x <= arr[hi]:
        # Guarda G: arr[lo] <= x <= arr[hi] == arr[lo] implica x == arr[lo]
        if arr[lo] == arr[hi]:
            return lo
        # Operandos >= 0: // (piso) coincide con la división entera de Java (trunca)
        pos = lo + ((hi - lo) // (arr[hi] - arr[lo])) * (x - arr[lo])
        if arr[pos] == x:
            return pos
        if arr[pos] < x:
            lo = pos + 1
        else:
            hi = pos - 1
    return -1
