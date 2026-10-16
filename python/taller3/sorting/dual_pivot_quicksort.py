"""
Dual-Pivot QuickSort con pivotes en el PRIMER y el ÚLTIMO elemento.
Fuente: GeeksforGeeks, "Dual pivot Quicksort",
        https://www.geeksforgeeks.org/dsa/dual-pivot-quicksort/
Equivalente línea a línea: java/src/taller3/sorting/DualPivotQuickSort.java

Nota para el análisis: con entrada ascendente o descendente, p = mínimo y
q = máximo del subarreglo, así que la partición central recibe n-2 elementos
y las laterales quedan vacías. Resultado: O(n²) en tiempo y profundidad de
recursión ~n/2. En Python eso supera el límite de recursión por defecto
(sys.getrecursionlimit() = 1000) desde n = 10.000 -> RecursionError.
NO se sube el límite a propósito: el taller pide documentar el fallo.
"""
from __future__ import annotations


def dual_pivot_quicksort(arr: list[int]) -> None:
    _sort(arr, 0, len(arr) - 1)


def _sort(arr: list[int], low: int, high: int) -> None:
    if low < high:
        lp, rp = _partition(arr, low, high)
        _sort(arr, low, lp - 1)
        _sort(arr, lp + 1, rp - 1)
        _sort(arr, rp + 1, high)


def _partition(arr: list[int], low: int, high: int) -> tuple[int, int]:
    if arr[low] > arr[high]:
        arr[low], arr[high] = arr[high], arr[low]

    j = low + 1          # fin de la zona  < p
    g = high - 1         # inicio de la zona >= q
    k = low + 1          # elemento que se examina
    p = arr[low]
    q = arr[high]

    while k <= g:
        if arr[k] < p:                       # va a la zona izquierda
            arr[k], arr[j] = arr[j], arr[k]
            j += 1
        elif arr[k] >= q:                    # va a la zona derecha
            while arr[g] > q and k < g:
                g -= 1
            arr[k], arr[g] = arr[g], arr[k]
            g -= 1
            if arr[k] < p:
                arr[k], arr[j] = arr[j], arr[k]
                j += 1
        k += 1

    j -= 1
    g += 1
    # Lleva los pivotes a su posición final
    arr[low], arr[j] = arr[j], arr[low]
    arr[high], arr[g] = arr[g], arr[high]
    return j, g
