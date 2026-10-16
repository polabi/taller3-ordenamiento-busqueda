"""
Registro de algoritmos de ordenamiento del Punto 1.

Cada algoritmo declara la complejidad de su caso por variante de entrada; el
benchmark la usa para PREDECIR si una ejecución superará el límite de 5 minutos
y para ESTIMAR los tiempos que no se ejecutan. El orden de SORTS es el mismo
que en SortRegistry.java (y el orden de las series en las gráficas).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from taller3.common.estimation import Growth
from taller3.sorting.bucket_sort import bucket_sort
from taller3.sorting.dual_pivot_quicksort import dual_pivot_quicksort
from taller3.sorting.heap_sort import heap_sort
from taller3.sorting.insertion_sort import insertion_sort
from taller3.sorting.merge_sort import merge_sort
from taller3.sorting.radix_sort import radix_sort

N, NLOGN, N2 = Growth.N, Growth.NLOGN, Growth.N2


@dataclass(frozen=True)
class SortSpec:
    name: str
    func: Callable[[list[int]], None]
    growth: dict[str, Growth]          # variante -> complejidad de ese caso


SORTS: tuple[SortSpec, ...] = (
    SortSpec("InsertionSort", insertion_sort,
             {"aleatoria": N2, "ascendente": N, "descendente": N2}),
    SortSpec("DualPivotQuickSort", dual_pivot_quicksort,
             {"aleatoria": NLOGN, "ascendente": N2, "descendente": N2}),
    SortSpec("MergeSort", merge_sort,
             {"aleatoria": NLOGN, "ascendente": NLOGN, "descendente": NLOGN}),
    SortSpec("HeapSort", heap_sort,
             {"aleatoria": NLOGN, "ascendente": NLOGN, "descendente": NLOGN}),
    SortSpec("RadixSort", radix_sort,
             {"aleatoria": N, "ascendente": N, "descendente": N}),        # d = 8 fijo
    SortSpec("BucketSort", bucket_sort,
             {"aleatoria": N, "ascendente": N, "descendente": N}),        # datos uniformes
)

BY_NAME = {s.name: s for s in SORTS}
