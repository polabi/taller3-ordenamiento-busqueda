"""
Merge Sort (top-down, recursivo).
Fuente: GeeksforGeeks, "Merge Sort", https://www.geeksforgeeks.org/dsa/merge-sort/
Equivalente línea a línea: java/src/taller3/sorting/MergeSort.java

Se usa m = l + (r - l) // 2 (la forma de la versión Java de GfG) para que ambos
lenguajes dividan exactamente igual. La comparación L[i] <= R[j] lo hace estable.
"""
from __future__ import annotations


def merge_sort(arr: list[int]) -> None:
    _sort(arr, 0, len(arr) - 1)


def _sort(arr: list[int], l: int, r: int) -> None:
    if l < r:
        m = l + (r - l) // 2
        _sort(arr, l, m)
        _sort(arr, m + 1, r)
        _merge(arr, l, m, r)


def _merge(arr: list[int], l: int, m: int, r: int) -> None:
    n1 = m - l + 1
    n2 = r - m

    # Arreglos temporales (igual que en Java: new int[n1], new int[n2])
    L = [0] * n1
    R = [0] * n2
    for i in range(n1):
        L[i] = arr[l + i]
    for j in range(n2):
        R[j] = arr[m + 1 + j]

    i = 0
    j = 0
    k = l
    while i < n1 and j < n2:
        if L[i] <= R[j]:
            arr[k] = L[i]
            i += 1
        else:
            arr[k] = R[j]
            j += 1
        k += 1

    while i < n1:
        arr[k] = L[i]
        i += 1
        k += 1

    while j < n2:
        arr[k] = R[j]
        j += 1
        k += 1
