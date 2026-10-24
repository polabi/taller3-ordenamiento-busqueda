# Experimento de supuestos (Bucket Sort y Radix Sort)

| Lenguaje | Algoritmo | Distribución | n | Tiempo | × uniforme | cubetas no vacías | cubeta máx. | desplazamientos | pasadas Radix | mejor comparativo (P1) |
|---|---|---|---|---|---|---|---|---|---|---|
| Java | BucketSort | uniforme | 10.000 | 243 µs | 1,00 | 6.331 | 7 | 2.537 | — | DualPivotQuickSort 238 µs |
| Java | BucketSort | rango_pequeno | 10.000 | 133 µs | 0,55 | 1.000 | 22 | 0 | — | DualPivotQuickSort 238 µs |
| Java | BucketSort | concentrado_extremos | 10.000 | 3,98 ms | 16,42 | 12 | 1.045 | 2.466.064 | — | DualPivotQuickSort 238 µs |
| Java | BucketSort | uniforme | 100.000 | 2,38 ms | 1,00 | 63.394 | 7 | 24.756 | — | DualPivotQuickSort 3,80 ms |
| Java | BucketSort | rango_pequeno | 100.000 | 1,28 ms | 0,54 | 1.000 | 131 | 0 | — | DualPivotQuickSort 3,80 ms |
| Java | BucketSort | concentrado_extremos | 100.000 | 430 ms | 180,35 | 12 | 10.184 | 249.837.990 | — | DualPivotQuickSort 3,80 ms |
| Python | BucketSort | uniforme | 10.000 | 2,86 ms | 1,00 | 6.331 | 7 | 2.537 | — | DualPivotQuickSort 6,75 ms |
| Python | BucketSort | rango_pequeno | 10.000 | 2,58 ms | 0,90 | 1.000 | 22 | 0 | — | DualPivotQuickSort 6,75 ms |
| Python | BucketSort | concentrado_extremos | 10.000 | 111 ms | 38,64 | 12 | 1.045 | 2.466.064 | — | DualPivotQuickSort 6,75 ms |
| Python | RadixSort | uniforme | 10.000 | 11,3 ms | 1,00 | — | — | — | 8 | DualPivotQuickSort 6,75 ms |
| Python | RadixSort | digitos16 | 10.000 | 26,5 ms | 2,36 | — | — | — | 16 | DualPivotQuickSort 6,75 ms (*) |
| Python | BucketSort | uniforme | 100.000 | 29,2 ms | 1,00 | 63.394 | 7 | 24.756 | — | DualPivotQuickSort 84,0 ms |
| Python | BucketSort | rango_pequeno | 100.000 | 26,2 ms | 0,90 | 1.000 | 131 | 0 | — | DualPivotQuickSort 84,0 ms |
| Python | BucketSort | concentrado_extremos | 100.000 | 11,4 s | 391,55 | 12 | 10.184 | 249.837.990 | — | DualPivotQuickSort 84,0 ms |
| Python | RadixSort | uniforme | 100.000 | 121 ms | 1,00 | — | — | — | 8 | DualPivotQuickSort 84,0 ms |
| Python | RadixSort | digitos16 | 100.000 | 284 ms | 2,34 | — | — | — | 16 | DualPivotQuickSort 84,0 ms (*) |
| Python | RadixSort | uniforme | 1.000.000 | 1,73 s | 1,00 | — | — | — | 8 | DualPivotQuickSort 1,07 s |
| Python | RadixSort | digitos16 | 1.000.000 | 4,05 s | 2,34 | — | — | — | 16 | DualPivotQuickSort 1,07 s (*) |

`~` = estimado (no ejecutado). (*) referencia medida con 8 dígitos: los comparativos del Punto 1 no se midieron con 16 dígitos (spec p3 4.4.1).
