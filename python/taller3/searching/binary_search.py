"""
Búsqueda binaria (iterativa).
Fuente: GeeksforGeeks, "Binary Search",
        https://www.geeksforgeeks.org/dsa/binary-search/
Equivalente línea a línea: java/src/taller3/searching/BinarySearch.java
"""
from __future__ import annotations


def binary_search(arr: list[int], x: int) -> int:
    return binary_search_range(arr, 0, len(arr) - 1, x)


def binary_search_range(arr: list[int], lo: int, hi: int, x: int) -> int:
    """Binaria sobre el subrango cerrado [lo, hi]; la reutiliza exponential_search."""
    while lo <= hi:
        mid = lo + (hi - lo) // 2   # forma de GfG (en Java evita el overflow de lo + hi)
        if arr[mid] == x:
            return mid
        if arr[mid] < x:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1
