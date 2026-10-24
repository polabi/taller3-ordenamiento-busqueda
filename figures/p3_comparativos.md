# Comparativos frente a no comparativos — aleatoria, n = 1.000.000 (Punto 1)

| Lenguaje | Algoritmo | Tipo | Tiempo | ns / (n·log₂ n) | ns / elemento | t(10⁶)/t(10⁵) |
|---|---|---|---|---|---|---|
| Java | InsertionSort | comparativo | 33,7 s | 1.692,902 | 33.742,18 | 103,19 |
| Java | DualPivotQuickSort | comparativo | 49,0 ms | 2,456 | 48,95 | 12,89 |
| Java | MergeSort | comparativo | 69,6 ms | 3,491 | 69,59 | 12,78 |
| Java | HeapSort | comparativo | 77,1 ms | 3,866 | 77,06 | 13,41 |
| Java | RadixSort | no comparativo | 16,1 ms | 0,807 | 16,09 | 10,62 |
| Java | BucketSort | no comparativo | 76,9 ms | 3,856 | 76,86 | 31,24 |
| Python | InsertionSort | comparativo | ~12.600 s | 632.503,303 | 12.606.782,95 | 100,00 |
| Python | DualPivotQuickSort | comparativo | 1,07 s | 53,451 | 1.065,37 | 12,69 |
| Python | MergeSort | comparativo | 2,45 s | 122,700 | 2.445,60 | 11,75 |
| Python | HeapSort | comparativo | 3,60 s | 180,686 | 3.601,36 | 13,46 |
| Python | RadixSort | no comparativo | 1,78 s | 89,082 | 1.775,54 | 13,89 |
| Python | BucketSort | no comparativo | 457 ms | 22,938 | 457,19 | 14,80 |

`~` = estimado (no ejecutado, regla de 5 min del Punto 1). Teórico de t(10⁶)/t(10⁵): O(n) = 10; O(n log n) = 12; O(n²) = 100.
