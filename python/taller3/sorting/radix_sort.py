"""
Radix Sort LSD en base 10, con Counting Sort estable por dígito.
Fuente: GeeksforGeeks, "Radix Sort", https://www.geeksforgeeks.org/dsa/radix-sort/
Equivalente línea a línea: java/src/taller3/sorting/RadixSort.java

Con valores de 8 dígitos hace exactamente d = 8 pasadas: O(d·(n + b)), b = 10.
El máximo se busca con un ciclo explícito (no con max()) para que la
implementación sea la misma que en Java y no use una función escrita en C.
"""
from __future__ import annotations


def radix_sort(arr: list[int]) -> None:
    n = len(arr)
    if n == 0:
        return
    m = _get_max(arr, n)
    exp = 1
    while m // exp > 0:
        _count_sort(arr, n, exp)
        exp *= 10


def _get_max(arr: list[int], n: int) -> int:
    mx = arr[0]
    for i in range(1, n):
        if arr[i] > mx:
            mx = arr[i]
    return mx


def _count_sort(arr: list[int], n: int, exp: int) -> None:
    output = [0] * n
    count = [0] * 10

    for i in range(n):
        count[(arr[i] // exp) % 10] += 1

    for i in range(1, 10):
        count[i] += count[i - 1]

    # De derecha a izquierda para que sea estable
    for i in range(n - 1, -1, -1):
        d = (arr[i] // exp) % 10
        output[count[d] - 1] = arr[i]
        count[d] -= 1

    for i in range(n):
        arr[i] = output[i]
