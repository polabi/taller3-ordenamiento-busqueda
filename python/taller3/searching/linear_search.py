"""
Búsqueda lineal (referencia).
Fuente: GeeksforGeeks, "Linear Search Algorithm",
        https://www.geeksforgeeks.org/dsa/linear-search/
Equivalente línea a línea: java/src/taller3/searching/LinearSearch.java
"""
from __future__ import annotations


def linear_search(arr: list[int], x: int) -> int:
    n = len(arr)
    # No aprovecha el orden (como GfG): con duplicados devuelve la primera aparición
    for i in range(n):
        if arr[i] == x:
            return i
    return -1
