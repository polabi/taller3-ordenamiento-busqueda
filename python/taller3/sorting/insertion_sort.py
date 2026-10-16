"""
Insertion Sort.
Fuente: GeeksforGeeks, "Insertion Sort Algorithm",
        https://www.geeksforgeeks.org/dsa/insertion-sort-algorithm/
Equivalente línea a línea: java/src/taller3/sorting/InsertionSort.java
"""
from __future__ import annotations


def insertion_sort(arr: list[int]) -> None:
    n = len(arr)
    for i in range(1, n):
        key = arr[i]
        j = i - 1
        # Desplaza a la derecha los mayores que key
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
