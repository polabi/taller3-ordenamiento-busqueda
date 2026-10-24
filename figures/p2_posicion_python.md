| Algoritmo | inicio (0) | centro (499.999) | centro (500.000) | final (999.999) |
|---|---|---|---|---|
| Lineal | 0,139 µs | 8,88 ms | 8,66 ms | 17,2 ms |
| Binaria | 1,34 µs | 0,136 µs | 1,46 µs | 1,44 µs |
| Ternaria | 1,51 µs | 1,70 µs | 1,72 µs | 1,68 µs |
| Saltos | 0,148 µs | 56,3 µs | 24,0 µs | 80,2 µs |
| Interpolación | 0,243 µs | 0,665 µs | 1,09 µs | 0,251 µs |
| Exponencial | 0,0700 µs | 1,94 µs | 1,61 µs | 1,98 µs |
| Interpolación (división entera, GfG Java) (variante) | 0,188 µs | 74,0 ms | 76,9 ms | 149 ms |

Tiempo promedio por búsqueda (3 cifras significativas, unidad en cada celda), Python, n = 1.000.000, 1.000 búsquedas de la misma clave por pasada, promedio de 5 pasadas. `~` = estimado (no ejecutado).

`centro` = índice 499.999 = ⌊(n−1)/2⌋ (valor 54.951.725); `centro_alto` = índice 500.000 = ⌊n/2⌋ (valor 54.951.967). 499.999 es el **mejor caso de la binaria**: es su primer `mid` (1 comparación), mientras que 500.000 requiere 19 iteraciones; en saltos ocurre lo contrario (499.999 es el último elemento de su bloque, ≈ 1.500 pasos; 500.000 el primero del siguiente, ≈ 502). Ver el análisis de posiciones (artefacto del centro, spec 6.2).
