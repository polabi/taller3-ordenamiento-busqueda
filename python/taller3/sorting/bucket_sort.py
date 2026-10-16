"""
Bucket Sort para enteros.
Fuente: GeeksforGeeks, "Bucket Sort", https://www.geeksforgeeks.org/dsa/bucket-sort-2/
Equivalente línea a línea: java/src/taller3/sorting/BucketSort.java

Adaptación documentada: la versión de GfG supone flotantes en [0, 1) y usa
n cubetas con índice floor(x · n). Para enteros se normaliza al mismo intervalo:

    número de cubetas:   k = n
    asignación:          idx(x) = floor( (x - min) · k / (max - min + 1) )

(max - min + 1) en el denominador garantiza 0 <= idx <= k-1. Con datos
uniformes cada cubeta recibe en promedio 1 elemento -> O(n) esperado.
Cada cubeta se ordena con Insertion Sort (como en GfG) y se concatenan en orden.
Es estable: la distribución conserva el orden de llegada e Insertion Sort es estable.
"""
from __future__ import annotations


def bucket_sort(arr: list[int]) -> None:
    n = len(arr)
    if n <= 1:
        return

    mn = arr[0]
    mx = arr[0]
    for i in range(1, n):
        if arr[i] < mn:
            mn = arr[i]
        if arr[i] > mx:
            mx = arr[i]

    k = n                          # número de cubetas
    rango = mx - mn + 1
    buckets: list[list[int]] = [[] for _ in range(k)]

    for i in range(n):
        idx = (arr[i] - mn) * k // rango
        buckets[idx].append(arr[i])

    pos = 0
    for b in buckets:
        _insertion_sort(b)
        for v in b:
            arr[pos] = v
            pos += 1


def _insertion_sort(b: list[int]) -> None:
    for i in range(1, len(b)):
        key = b[i]
        j = i - 1
        while j >= 0 and b[j] > key:
            b[j + 1] = b[j]
            j -= 1
        b[j + 1] = key
