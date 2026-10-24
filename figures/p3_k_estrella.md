# ¿Ordenar o no ordenar? — k* = t_ord / (t_L − t_B), n = 1.000.000

| Lenguaje | Rol | Ordenamiento | t_ord | t_L (fuente) | t_B | k* | k_min | intervalo ±1σ | Estado |
|---|---|---|---|---|---|---|---|---|---|
| Java | principal | RadixSort | 16,1 ms | 96,3 µs (claves) | 77,1 ns | 167,24 | 168 | [161,08; 173,83] | medido |
| Java | banda | RadixSort | 16,1 ms | 50,7 µs (solo_presentes) | 77,1 ns | 317,67 | 318 | [315,14; 320,21] | medido |
| Java | banda | RadixSort | 16,1 ms | 102 µs (solo_ausentes) | 77,1 ns | 157,51 | 158 | [156,42; 158,61] | medido |
| Python | principal | BucketSort | 457 ms | 12,9 ms (claves) | 1,81 µs | 35,57 | 36 | [34,55; 36,63] | medido |
| Python | banda | BucketSort | 457 ms | 8,88 ms (solo_presentes) | 1,81 µs | 51,52 | 52 | [49,38; 53,81] | medido |
| Python | banda | BucketSort | 457 ms | 17,2 ms (solo_ausentes) | 1,81 µs | 26,59 | 27 | [25,45; 27,81] | medido |
| Python | sensibilidad_orden — sensibilidad: Radix en lugar de Bucket (×3,88) | RadixSort | 1,78 s | 12,9 ms (claves) | 1,81 µs | 138,14 | 139 | [131,08; 145,44] | medido |

## Cálculo (filas principales)

- **Java** (RadixSort): k* = 16.087.758,4 ns / (96.271,250 − 77,066) ns = 16.087.758,4 / 96.194,184 = **167,2425** → conviene ordenar desde k = **168** búsquedas.
- **Python** (BucketSort): k* = 457.194.941,8 ns / (12.855.048,875 − 1.814,625) ns = 457.194.941,8 / 12.853.234,250 = **35,5704** → conviene ordenar desde k = **36** búsquedas.

Banda (`solo_presentes` = LinearSearch `centro`; `solo_ausentes` = LinearSearch `final`): es una APROXIMACIÓN del efecto de la mezcla de claves, no un intervalo de confianza (spec p3 5.2). Intervalo ±1σ según spec 5.5.
