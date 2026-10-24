| Algoritmo | inicio (0) | centro (499.999) | centro (500.000) | final (999.999) |
|---|---|---|---|---|
| Lineal | 0,00272 µs | 50,7 µs | 50,9 µs | 102 µs |
| Binaria | 0,0214 µs | 0,00268 µs | 0,0225 µs | 0,0234 µs |
| Ternaria | 0,0249 µs | 0,0247 µs | 0,0243 µs | 0,0246 µs |
| Saltos | 0,00312 µs | 0,554 µs | 0,265 µs | 0,841 µs |
| Interpolación | 0,00322 µs | 0,00718 µs | 0,0138 µs | 0,00336 µs |
| Exponencial | 0,0129 µs | 0,0323 µs | 0,0228 µs | 0,0331 µs |
| Interpolación (división entera, GfG Java) (variante) | 0,00301 µs | 1,72 ms | 1,75 ms | 3,48 ms |

Tiempo promedio por búsqueda (3 cifras significativas, unidad en cada celda), Java, n = 1.000.000, 1.000 búsquedas de la misma clave por pasada, promedio de 5 pasadas. `~` = estimado (no ejecutado).

`centro` = índice 499.999 = ⌊(n−1)/2⌋ (valor 54.951.725); `centro_alto` = índice 500.000 = ⌊n/2⌋ (valor 54.951.967). 499.999 es el **mejor caso de la binaria**: es su primer `mid` (1 comparación), mientras que 500.000 requiere 19 iteraciones; en saltos ocurre lo contrario (499.999 es el último elemento de su bloque, ≈ 1.500 pasos; 500.000 el primero del siguiente, ≈ 502). Ver el análisis de posiciones (artefacto del centro, spec 6.2).
