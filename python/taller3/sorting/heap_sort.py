"""
Heap Sort (max-heap, heapify recursivo).
Fuente: GeeksforGeeks, "Heap Sort", https://www.geeksforgeeks.org/dsa/heap-sort/
Equivalente línea a línea: java/src/taller3/sorting/HeapSort.java

La recursión de heapify tiene profundidad O(log n) (~20 para n = 10^6),
así que no hay riesgo de RecursionError.
"""
from __future__ import annotations


def heap_sort(arr: list[int]) -> None:
    n = len(arr)
    # Construir el max-heap desde el último nodo interno hacia la raíz
    for i in range(n // 2 - 1, -1, -1):
        _heapify(arr, n, i)
    # Extraer el máximo uno por uno
    for i in range(n - 1, 0, -1):
        arr[0], arr[i] = arr[i], arr[0]
        _heapify(arr, i, 0)


def _heapify(arr: list[int], n: int, i: int) -> None:
    largest = i
    l = 2 * i + 1
    r = 2 * i + 2
    if l < n and arr[l] > arr[largest]:
        largest = l
    if r < n and arr[r] > arr[largest]:
        largest = r
    if largest != i:
        arr[i], arr[largest] = arr[largest], arr[i]
        _heapify(arr, n, largest)
