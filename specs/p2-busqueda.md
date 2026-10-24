# Punto 2 — Algoritmos de búsqueda

Estado por partes (actualizado 2026-10-22):

| Parte | Secciones | Estado |
|---|---|---|
| Algoritmos: pseudocódigo, interfaz, nombres, casos borde y casos de prueba de corrección | 2.1, 3, 4, 5, 8.1 | **APROBADA (2026-10-20)** → puede pasar a `aa-test-writer` |
| Protocolo de claves y benchmark: generación de claves, experimentos, CSV, gráficas | 6, 7, 8.2–8.4 | **APROBADA (2026-10-22)** (D1, D7, D9, D10 resueltas) → puede pasar a `aa-test-writer` e implementación |
| Prueba versionada de equivalencia Java ↔ Python | 8.5 | **APROBADA con condiciones (2026-10-22)**, rediseñada: constantes calculadas con oráculo independiente (`bisect`) → puede pasar a `aa-test-writer` |

Fecha: 2026-10-18 (creación) · 2026-10-20 (decisiones del estudiante incorporadas) ·
2026-10-21 (atribuciones de GfG en 3.5 corregidas por el coordinador) · 2026-10-22 (D1,
D7, D9, D10; secciones 6–8 aprobadas; 8.5 rediseñada según las condiciones del estudiante;
informe: índices de `centro`/`centro_alto` en el pie de la tabla de posición)

---

## 1. Requerimiento (literal del enunciado)

> Implemente los siguientes algoritmos de búsqueda: Búsqueda Lineal (como referencia),
> Búsqueda Binaria, Búsqueda Ternaria, Búsqueda por Saltos (Jump Search), Búsqueda por
> Interpolación, Búsqueda Exponencial.
>
> **Datos de entrada:** utilice los arreglos ordenados de forma ascendente del Punto 1, ya
> que la mayoría de estos algoritmos requieren un arreglo ordenado.
>
> **Claves de búsqueda:** una sola búsqueda tarda tan poco que medirla de forma aislada
> produce resultados dominados por el ruido del reloj. Genere una sola vez un conjunto de
> 1.000 claves (500 presentes en el arreglo y 500 ausentes), guárdelo en un archivo de
> texto plano, mida el tiempo total de buscarlas todas y reporte el tiempo promedio por
> búsqueda.
>
> **Posición de la clave:** repita la medición buscando 1.000 veces una clave ubicada al
> inicio, otra en el centro y otra al final del arreglo.
>
> **Resultados y análisis:** Crecimiento: una gráfica de líneas de n contra el tiempo
> promedio por búsqueda por cada lenguaje, con una línea por algoritmo y escala
> logarítmica en ambos ejes (2 gráficas). Compilado frente a interpretado: un gráfico de
> barras para n = 1.000.000 con dos barras por algoritmo, una por lenguaje (1 gráfica).
> Posición de la clave: una tabla por lenguaje con el tiempo promedio por búsqueda para
> n = 1.000.000, con una fila por algoritmo y una columna por posición de la clave
> (inicio, centro y final). Análisis: ¿en qué algoritmos cambia el tiempo según la
> posición de la clave y en cuáles no? Explique por qué, según el orden en que cada
> algoritmo revisa los elementos del arreglo.

Condiciones generales que aplican (literal): misma implementación en ambos lenguajes con
fuente citada; mida únicamente el tiempo del algoritmo; reloj de alta precisión; *"Repita
cada medición 5 veces y reporte el promedio y la desviación estándar"*; *"En lenguajes con
compilación en tiempo de ejecución (JIT), como Java […], realice antes una ejecución de
calentamiento que no se incluya en el promedio"*; límite de 5 min → estimar y marcar como
estimado; CSV con algoritmo, lenguaje, variante, n, cada repetición, promedio, desviación
y medido/estimado; gráficas con eje de tiempo logarítmico, estimados dibujados distinto,
valores visibles sobre cada barra.

## 2. Alcance

Entra: 6 algoritmos del enunciado **más una variante documentada de interpolación**
(división entera, sección 3.5.2) en Java y Python, generación del archivo de claves,
benchmark de claves (4 tamaños) y de posición (n = 1.000.000, 4 posiciones), CSV,
3 gráficas, 2 tablas de posición.

Se reutiliza del Punto 1 sin cambios de comportamiento:
`data/ascendente_{n}.txt`, `config.py`/`Config.java`, `common/` (lectura, `Stats`,
`Estimator`, escritor CSV), patrón de registro, calentamiento JIT y reglas del límite.

Cambios en código compartido (ver sección 7.1): agregar miembros a `Growth`, una lectura
de claves en `dataio`/`DataIO`, y generación de claves en `generate_data.py`. **Ninguno
puede alterar los archivos ni los resultados del Punto 1.**

No entra: ordenar datos (ya están), el Punto 3.

### 2.1 Nombres y firmas (APROBADO)

| | Java (`java/src/taller3/`) | Python (`python/taller3/`) |
|---|---|---|
| Contrato | `searching/SearchAlgorithm.java`: `String name(); int search(int[] arr, int x); Growth growth();` | `searching/__init__.py`: `SearchSpec(name, func, growth)`, `SEARCHES`, `BY_NAME`; `func(arr: list[int], x: int) -> int` |
| Registro | `searching/SearchRegistry.java` (`ALL`, `byName`) | `SEARCHES` (mismo orden que `SearchRegistry.ALL`) |
| Algoritmos | `LinearSearch`, `BinarySearch` (+ `static int searchRange(int[] arr, int lo, int hi, int x)`), `TernarySearch`, `JumpSearch`, `InterpolationSearch`, `ExponentialSearch`, `InterpolationSearchIntDiv` | `linear_search.py`, `binary_search.py` (+ `binary_search_range(arr, lo, hi, x)`), `ternary_search.py`, `jump_search.py`, `interpolation_search.py`, `exponential_search.py`, `interpolation_search_int_div.py` |
| Benchmark | `bench/SearchBenchmark.java` | `bench_search.py` |
| Gráficas | — | `plot_search.py` |
| Pruebas | `tests/SearchSelfTest.java` | `tests/test_searching.py` |
| Script de corrida | `run_punto2.sh` (raíz, ver 7.1) | |

Nombre en el CSV (`algoritmo`) y orden en registro, gráficas y tablas:
`LinearSearch`, `BinarySearch`, `TernarySearch`, `JumpSearch`, `InterpolationSearch`,
`ExponentialSearch`, `InterpolationSearchIntDiv`. La variante va **al final** para no
alterar el orden de los 6 del enunciado.

Etiquetas para gráficas/tablas: `InterpolationSearch` → "Interpolación";
`InterpolationSearchIntDiv` → "Interpolación (división entera, GfG Java)" con la marca
"variante" (ver 7.3).

Regla de capa (como `sorting`): `searching` **no lee archivos, no copia, no mide, no
modifica el arreglo**. Recibe un arreglo ascendente y devuelve un índice.

## 3. Algoritmos (APROBADO 2026-10-20)

### 3.0 Contrato común (todas)

- Entrada: `arr` ordenado de forma **no decreciente** (puede tener duplicados), `x` entero.
- Salida: un índice `i` con `0 ≤ i < n` y `arr[i] == x`, o `-1` si `x` no está.
- **Duplicados.** Los arreglos tienen valores repetidos (verificado con los datos
  versionados: n − distintos = 0 en 1.000, 0 en 10.000, **55** en 100.000 y **5.604** en
  1.000.000). Cada algoritmo devuelve *un* índice válido, no necesariamente el primero.
  **Regla de verificación: se acepta cualquier `i` con `arr[i] == x`.** Además, como la
  implementación es la misma línea a línea, el índice concreto devuelto debe ser
  **idéntico en Java y Python** (se comprueba con el checksum, sección 8).
- No modifica `arr`. Memoria extra O(1) (versión iterativa).
- `n = 0` → `-1` (D5, aprobada).
- En Python, `n = len(arr)` se calcula una vez dentro de la función (GfG lo recibe como
  parámetro; aquí se omite para que la firma sea igual en ambos lenguajes).
- En Python no se usan `min()`/`max()` incorporados (misma regla del Punto 1): se usa la
  expresión condicional `a if a < b else b` (D8, aprobada).

Pseudocódigo **normativo** (Java y Python deben seguirlo línea a línea; `//` = división
entera; en todas las divisiones enteras los operandos son ≥ 0, así que truncar (Java) y
piso (Python) coinciden). La única división en coma flotante es la de 3.5.1.

### 3.1 Búsqueda lineal — `LinearSearch`

Fuente: GfG, "Linear Search Algorithm", https://www.geeksforgeeks.org/dsa/linear-search/

```
for i in 0 .. n-1:
    if arr[i] == x: return i
return -1
```
No aprovecha el orden (no se detiene al ver `arr[i] > x`), igual que GfG. Con duplicados
devuelve la **primera** aparición.

### 3.2 Búsqueda binaria — `BinarySearch` (iterativa, D4 aprobada)

Fuente: GfG, "Binary Search", https://www.geeksforgeeks.org/dsa/binary-search/

```
search(arr, x) = searchRange(arr, 0, n-1, x)

searchRange(arr, lo, hi, x):
    while lo <= hi:
        mid = lo + (hi - lo) // 2          # forma de GfG; evita overflow de lo+hi
        if arr[mid] == x: return mid
        if arr[mid] < x: lo = mid + 1
        else:            hi = mid - 1
    return -1
```

### 3.3 Búsqueda ternaria — `TernarySearch` (iterativa, D4 aprobada)

Fuente: GfG, "Ternary Search", https://www.geeksforgeeks.org/dsa/ternary-search/

```
l = 0; r = n - 1
while r >= l:
    mid1 = l + (r - l) // 3
    mid2 = r - (r - l) // 3
    if arr[mid1] == x: return mid1
    if arr[mid2] == x: return mid2
    if x < arr[mid1]:   r = mid1 - 1
    elif x > arr[mid2]: l = mid2 + 1
    else:               l = mid1 + 1; r = mid2 - 1
return -1
```

### 3.4 Búsqueda por saltos — `JumpSearch`, m = ⌊√n⌋

Fuente: GfG, "Jump Search", https://www.geeksforgeeks.org/dsa/jump-search/

```
if n == 0: return -1
m = floor(sqrt(n))            # Java: (int) Math.floor(Math.sqrt(n)); Python: math.isqrt(n)
step = m; prev = 0
while arr[min(step, n) - 1] < x:
    prev = step
    step = step + m
    if prev >= n: return -1
while arr[prev] < x:
    prev = prev + 1
    if prev == min(step, n): return -1
if arr[prev] == x: return prev
return -1
```
Desviación documentada respecto a GfG Python: GfG usa `step = math.sqrt(n)` en coma
flotante e `int(...)` en cada acceso; aquí `m` es entero en ambos lenguajes (como en GfG
Java) para que la secuencia de índices sea idéntica. Valores: m = 31 (n = 1.000),
100, 316, 1.000 (n = 1.000.000). `math.isqrt` y `floor(Math.sqrt)` coinciden para
n ≤ 10⁶. `min(a, b)` se escribe `a if a < b else b` en Python (D8).

### 3.5 Búsqueda por interpolación — dos algoritmos del registro

Fuente: GfG, "Interpolation Search", https://www.geeksforgeeks.org/dsa/interpolation-search/
(artículo descargado el 2026-10-20; pestañas de código verificadas una por una el 2026-10-21). El artículo contiene
**tres** formas de la fórmula de `pos`:

| Dónde aparece en el artículo | Fórmula |
|---|---|
| Texto explicativo | `pos = lo + (x − arr[lo]) · (hi − lo) / (arr[hi] − arr[lo])` |
| Códigos **C++** y **C** (`double`), **PHP**, **Python iterativo** (`float`) y **C# iterativo** (`float`) | `pos = lo + (int)(((double)(hi − lo) / (arr[hi] − arr[lo])) * (x − arr[lo]))` |
| Códigos **Java** (ambas pestañas), **Python recursivo** y **C# recursivo** | `pos = lo + ((hi − lo) // (arr[hi] − arr[lo])) * (x − arr[lo])` (división entera **antes** de multiplicar) |
| JavaScript | misma forma que la entera, pero en JS `/` es división real, así que se comporta como la `double` |

Decisión del estudiante (2026-10-20): se implementan y miden **dos** algoritmos
distintos, en ambos lenguajes:

- `InterpolationSearch` ("Interpolación", **oficial**): fórmula `double` de los códigos
  C++/C de GfG, igual a la del Python iterativo con `float` (3.5.1). En Java se aparta de la
  pestaña Java de GfG, que usa división entera.
- `InterpolationSearchIntDiv` ("Interpolación (división entera, GfG Java)",
  **variante**): fórmula entera de los códigos Java y Python recursivo de GfG (3.5.2).

Ambos comparten el esqueleto iterativo (si el artículo presenta una forma recursiva, se
usa la iterativa equivalente, coherente con D4; en la variante entera una recursión de
profundidad O(n) desbordaría la pila):

```
lo = 0; hi = n - 1
while lo <= hi and x >= arr[lo] and x <= arr[hi]:
    if arr[lo] == arr[hi]:                 # (G) guarda; aquí arr[lo] <= x <= arr[hi] = arr[lo] ⇒ x == arr[lo]
        return lo
    pos = <fórmula de 3.5.1 o 3.5.2>
    if arr[pos] == x: return pos
    if arr[pos] < x: lo = pos + 1
    else:            hi = pos - 1
return -1
```

**Regla (G), guarda `arr[lo] == arr[hi]` (desviación respecto a GfG, obligatoria en
ambos).** GfG solo trata `lo == hi`. Con duplicados puede ocurrir `lo < hi` y
`arr[lo] == arr[hi]` (p. ej. `[3, 3]`, `x = 3`) → denominador 0. En Python, tanto
`float / 0` como `int // 0` lanzan `ZeroDivisionError`; en Java la división entera lanza
`ArithmeticException` y la de `double` daría `NaN` silenciosamente. La guarda cubre ambos
casos (incluye `lo == hi`) y mantiene ambos lenguajes idénticos.

#### 3.5.1 `InterpolationSearch` (oficial) — fórmula `double` de GfG C++/C (Python iterativo con `float`)

```
Java:   int pos = lo + (int) (((double) (hi - lo) / (arr[hi] - arr[lo])) * (x - arr[lo]));
Python: pos = lo + int(float(hi - lo) / (arr[hi] - arr[lo]) * (x - arr[lo]))
```

- **Mismo `pos` en ambos lenguajes.** Ambos hacen las mismas dos operaciones IEEE 754 de
  doble precisión en el mismo orden: `(hi−lo)/(arr[hi]−arr[lo])` y luego `· (x−arr[lo])`;
  los enteros involucrados (< 2⁵³) se convierten a `double` sin error, y `(int)`/`int()`
  truncan hacia cero (los valores son ≥ 0). JDK 17+ garantiza semántica estricta
  (JEP 306); en JDK 11 sobre x86-64/ARM64 se usa SSE2/NEON, mismo resultado. Verificado
  por ejecución sobre los 4 arreglos ascendentes con 1.000 claves de prueba: checksums
  Java = Python (256.380; 2.498.755; 24.082.603; 256.252.612). **El checksum del
  benchmark debe coincidir entre lenguajes.**
- **Sin `long` y sin overflow.** Ya no hay producto entero: `(x − arr[lo]) ≤ 89.999.999` y
  `(hi − lo) ≤ 999.999` se operan en `double`. `0 ≤ pos − lo ≤ hi − lo` (el factor
  `(x−arr[lo])/(arr[hi]−arr[lo]) ∈ [0, 1]` y el error de redondeo es de unos pocos ulp),
  así que el resultado cabe en `int` y es un índice válido.
- **Diferencia con la fórmula exacta del texto** (`(x−arr[lo])·(hi−lo) // (arr[hi]−arr[lo])`):
  cuando el cociente exacto es entero, el `double` puede quedar un ulp por debajo
  (p. ej. `(2/49)·49 = 1,9999999999999998`) y truncar a uno menos. El resultado sigue
  siendo correcto, pero cambia el índice sondeado (y con duplicados, el índice devuelto):
  ver caso 5.6-F1. **No se implementa la fórmula exacta**; la prueba F1 detecta si alguien
  la usa en lugar de la `double`.

#### 3.5.2 `InterpolationSearchIntDiv` (variante) — fórmula entera de GfG Java y Python recursivo

```
Java:   int pos = lo + ((hi - lo) / (arr[hi] - arr[lo])) * (x - arr[lo]);      // división entera de int
Python: pos = lo + ((hi - lo) // (arr[hi] - arr[lo])) * (x - arr[lo])
```

- Sin overflow en Java: si el cociente `q = (hi−lo) // (arr[hi]−arr[lo])` es ≥ 1, entonces
  `q·(x−arr[lo]) ≤ q·(arr[hi]−arr[lo]) ≤ hi − lo`; si es 0, el producto es 0.
- **Con estos datos `q = 0` siempre ⇒ `pos = lo` ⇒ búsqueda lineal O(n).** Los valores son
  de 8 dígitos (rango ≈ 9·10⁷) y n ≤ 10⁶, así que `arr[hi] − arr[lo] > hi − lo`. Mientras
  `q = 0`, `pos = lo` y, como el `while` garantiza `arr[lo] ≤ x`, nunca ocurre
  `arr[pos] > x`: `hi` no cambia y el algoritmo sondea `lo, lo+1, lo+2, …`. Verificado por
  ejecución en los 4 arreglos ascendentes: para ningún `lo` con `hi = n−1` se cumple
  `q ≥ 1` (fuera del caso de la guarda). Consecuencias:
  - **El resultado es correcto** (ninguna prueba de solo-resultado lo distingue de la
    oficial); devuelve la **primera** aparición, como la lineal.
  - Clave presente en índice `i`: `i + 1` iteraciones (o `i` iteraciones + guarda si
    `arr[i] == arr[n−1]`).
  - Clave ausente dentro del rango: se detiene en el punto de inserción (cuando
    `x < arr[lo]`), no en `n` como `LinearSearch`. Clave fuera del rango: 0 iteraciones.
  - Cada iteración es más cara que un paso de la lineal (3 comparaciones del `while`,
    1 división, 1 multiplicación, 2 comparaciones). Medición informal en Python (no es dato
    del informe): ≈ 81 ns por iteración en n = 10⁶.

### 3.6 Búsqueda exponencial — `ExponentialSearch`

Fuente: GfG, "Exponential Search", https://www.geeksforgeeks.org/dsa/exponential-search/

```
if n == 0: return -1
if arr[0] == x: return 0
i = 1
while i < n and arr[i] <= x:
    i = i * 2
return BinarySearch.searchRange(arr, i // 2, min(i, n - 1), x)
```
GfG llama a una binaria **recursiva**; aquí se reutiliza la binaria iterativa de 3.2
(D4 aprobada). `i ≤ 2²⁰` para n = 10⁶: sin overflow.

### 3.7 Complejidad

| Algoritmo | Mejor | Promedio | Peor | Memoria extra | Requisito |
|---|---|---|---|---|---|
| Lineal | O(1) (clave en `arr[0]`) | O(n) (≈ (n+1)/2 comparaciones si está; n si no) | O(n) (última o ausente) | O(1) | ninguno |
| Binaria | O(1) (clave en el primer `mid`) | O(log n) | O(log n) (≈ ⌊log₂ n⌋ + 1 iteraciones) | O(1) | ordenado |
| Ternaria | O(1) (clave en el primer `mid1`/`mid2`) | O(log₃ n) = O(log n) | O(log n) | O(1) | ordenado |
| Saltos (m = √n) | O(1) | O(√n) | O(√n) (≈ n/m saltos + m − 1 pasos) | O(1) | ordenado |
| Interpolación (oficial, `double`) | O(1) | O(log log n) **si las claves están distribuidas uniformemente** | O(n) (distribución muy sesgada, caso U de 5.3) | O(1) | ordenado (+ uniforme para el promedio) |
| Exponencial | O(1) (`arr[0]`) | O(log i), i = posición de la clave; ≤ O(log n) | O(log n) | O(1) (O(log n) de pila con la binaria recursiva de GfG) | ordenado |
| Interpolación, división entera (variante) | O(1) (clave en `arr[0]` o fuera de rango) | **O(n) con estos datos** (≈ posición de la clave + 1 iteraciones, presentes y ausentes) | O(n) | O(1) | ordenado |

La complejidad de la variante entera **no tiene fuente bibliográfica**: es una derivación
propia (3.5.2) verificada por ejecución; el artículo de GfG declara para la interpolación
O(log log n) promedio y O(n) peor, que corresponden a la fórmula del texto/Java.

Nota ternaria vs. binaria (derivación propia, verificable): la ternaria hace hasta 4
comparaciones por iteración y ≈ log₃ n iteraciones → ≈ 4·log₃ n = 2,52·log₂ n
comparaciones en el peor caso, frente a ≈ 2·log₂ n de la binaria. Es asintóticamente
igual pero con más comparaciones.

Fuentes de complejidad (las de libro **por confirmar edición y página** por el estudiante;
no se verificaron contra el ejemplar):

- Cada artículo de GfG citado arriba (sección "Complexity Analysis").
- Cormen, Leiserson, Rivest, Stein, *Introduction to Algorithms*, 3.ª ed., MIT Press,
  2009: ejercicio 2.1-3 (búsqueda lineal), 2.2-3 (casos promedio y peor de la lineal),
  2.3-5 (binaria Θ(lg n) en el peor caso). *Por confirmar numeración si el sílabo usa la 4.ª ed.*
- Knuth, *The Art of Computer Programming*, vol. 3, 2.ª ed., §6.1 (búsqueda secuencial)
  y §6.2.1 (binaria e interpolación). *Por confirmar.*
- Interpolación O(log log n): Perl, Itai, Avni, "Interpolation search — a log log N
  search", *Communications of the ACM* 21(7), 1978. *Por confirmar.*
- Saltos O(√n): Shneiderman, "Jump searching: a fast sequential search technique",
  *Communications of the ACM* 21(10), 1978. *Por confirmar.*
- Exponencial O(log i): Bentley, Yao, "An almost optimal algorithm for unbounded
  searching", *Information Processing Letters* 5(3), 1976. *Por confirmar.*

Razones teóricas t(10n)/t(n) para `figures/p2_razones_crecimiento.csv` (calculadas):

| Complejidad | Algoritmos | 10³→10⁴ | 10⁴→10⁵ | 10⁵→10⁶ |
|---|---|---|---|---|
| O(n) | Lineal, Interpolación div. entera | 10 | 10 | 10 |
| O(√n) | Saltos | 3,162 (con m entero: 100/31 = 3,226) | 3,162 (316/100 = 3,16) | 3,162 (1000/316 = 3,165) |
| O(log n) | Binaria, Ternaria, Exponencial | 1,333 | 1,250 | 1,200 |
| O(log log n) | Interpolación (oficial) | 1,125 | 1,086 | 1,065 |

## 4. Casos borde (obligatorios en las pruebas, para los 7 algoritmos)

| Caso | Comportamiento exigido |
|---|---|
| Arreglo vacío | `-1` en los 7, sin excepción (D5) |
| Arreglo de 1 elemento, clave presente / menor / mayor | `0` / `-1` / `-1` |
| Clave menor que `arr[0]` | `-1`; ambas interpolaciones salen sin calcular `pos` |
| Clave mayor que `arr[n-1]` | `-1`; saltos no accede fuera del arreglo (usa `min(step, n) − 1`) |
| Clave entre dos elementos consecutivos (ausente "interior") | `-1` |
| Primer y último elemento | índice `0` y `n − 1` (o cualquier índice válido si está repetido) |
| Duplicados | cualquier índice válido; el índice exacto de 5.2 y 5.6 debe coincidir |
| Todos iguales | presente → índice válido; ausente (menor/mayor) → `-1` |
| `arr[lo] == arr[hi]` con `lo < hi` (ambas interpolaciones) | no divide por cero (guarda G) |
| Valores de 8 dígitos con `(x − arr[lo])·(hi − lo)` > 2³¹ − 1 (caso O) | la oficial (`double`) no desborda ni produce índice negativo; la variante entera no multiplica cantidades grandes |
| Cociente `double` exacto entero que queda 1 ulp por debajo (caso F) | la oficial trunca al entero inferior; el resultado sigue siendo válido |
| Distribución no uniforme (interpolación) | resultado correcto aunque haga O(n) iteraciones |
| n no cuadrado perfecto (saltos) | correcto con m = ⌊√n⌋ |
| Valores reales de 8 dígitos (10.000.000 y 99.999.999) | correcto |

## 5. Casos de prueba resueltos a mano

Todos los valores esperados se verificaron además ejecutando una implementación de
referencia del pseudocódigo de la sección 3 (script temporal, fuera del repo; los valores
`double` se comprobaron en Java y en Python y coinciden). "Índice exacto" = lo que debe
devolver la implementación especificada; las pruebas comprueban **ambos**: que es válido y
que es exactamente ese (D-extra, aprobada).

Columnas de las tablas: Lin. = lineal, Bin. = binaria, Ter. = ternaria, Sal. = saltos,
Int. = `InterpolationSearch` (oficial, `double`), Exp. = exponencial,
IDiv = `InterpolationSearchIntDiv` (variante).

### 5.1 Arreglo A (n = 16, sin duplicados, uniforme)

`A = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160]` (índices 0–15)

**x = 70 (presente, índice 6)**

- Lineal: compara 0,1,…,6 → **6** (7 comparaciones).
- Binaria: (lo,hi)=(0,15) mid=7, A[7]=80>70 → hi=6; (0,6) mid=3, 40<70 → lo=4;
  (4,6) mid=5, 60<70 → lo=6; (6,6) mid=6, 70 → **6**.
- Ternaria: (l,r)=(0,15): mid1=0+15//3=5, mid2=15−5=10; A[5]=60, A[10]=110, 60<70<110 →
  l=6, r=9; mid1=6+3//3=7, mid2=9−1=8; A[7]=80, 70<80 → r=6; (6,6): mid1=mid2=6 → **6**.
- Saltos: m=⌊√16⌋=4. A[3]=40<70 → prev=4, step=8; A[7]=80 ≥ 70 para. Lineal desde 4:
  50<70→5, 60<70→6, A[6]=70 no es <70; A[6]==70 → **6**.
- Interpolación (oficial): pos = 0 + (int)((15/150)·(70−10)) = (int)(0,1·60) = (int)6,0 = 6
  → A[6]=70 → **6** (1 iteración).
- Interpolación div. entera: q = 15 // 150 = 0 → pos = lo. Sondea 0 (10<70, lo=1),
  1, 2, 3, 4, 5 (60<70, lo=6), 6 → A[6]=70 → **6** (7 iteraciones).
- Exponencial: A[0]≠70; i=1 (20≤70) → 2 (30) → 4 (50) → 8: A[8]=90>70 para. Binaria en
  [8//2, min(8,15)] = [4, 8]: mid=6 → 70 → **6**.

**x = 75 (ausente interior, entre A[6]=70 y A[7]=80)** → todos **−1**.

- Binaria: mid 7 (80>75, hi=6), 3 (40, lo=4), 5 (60, lo=6), 6 (70<75, lo=7) → lo>hi → −1.
- Ternaria: (0,15) → l=6,r=9 → mid1=7: 75<80 → r=6 → (6,6): 70≠75, 75>70 → l=7 → −1.
- Saltos: A[3]<75 → prev=4, step=8; A[7]=80≥75. Lineal: 4,5,6 (<75) → prev=7; A[7]=80
  no <75; A[7]≠75 → −1.
- Interpolación (oficial): pos = 0 + (int)(0,1·65) = (int)6,5 = 6; A[6]=70<75 → lo=7;
  ahora x=75 < A[7]=80 → sale del ciclo → −1 (1 iteración).
- Interpolación div. entera: sondea 0,…,6 (todos <75) → lo=7; 75 < A[7]=80 → sale → −1
  (7 iteraciones: se detiene en el punto de inserción, no en n).
- Exponencial: rango [4, 8]; mid=6 (70<75, lo=7); mid=7 (80>75, hi=6) → −1.

**Otros de A (esperado, verificado por ejecución):**

| x | Lin. | Bin. | Ter. | Sal. | Int. | Exp. | IDiv |
|---|---|---|---|---|---|---|---|
| 10 (primero) | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 160 (último) | 15 | 15 | 15 | 15 | 15 | 15 | 15 |
| 90 | 8 | 8 | 8 | 8 | 8 | 8 | 8 |
| 130 | 12 | 12 | 12 | 12 | 12 | 12 | 12 |
| 5 (< mínimo) | −1 | −1 | −1 | −1 | −1 | −1 | −1 |
| 200 (> máximo) | −1 | −1 | −1 | −1 | −1 | −1 | −1 |

Iteraciones de interpolación (informativas, no se prueban): oficial 1 en 10, 160, 90, 130
(`(15/150)·150 = 15,0`, `·80 = 8,0`, `·120 = 12,0`); variante entera 1, 16, 9, 13.

Trazas clave de los extremos: x=200 en saltos: prev/step = 4/8, 8/12, 12/16, A[15]=160<200
→ prev=16 ≥ 16 → −1 (nunca accede a A[16]). Exponencial x=200: i=1,2,4,8,16 (i<n falla)
→ binaria en [8, 15] → −1. Exponencial x=5: A[0]≠5, A[1]=20>5 → i=1 → binaria en [0, 1]:
mid=0, 10>5 → hi=−1 → −1. Ambas interpolaciones con x=5 y x=200: la condición del
`while` falla de entrada → −1 sin calcular `pos`.

### 5.2 Arreglo D (duplicados, n = 8)

`D = [5, 7, 7, 7, 9, 12, 12, 15]`

**x = 7** (índices válidos {1, 2, 3}): los algoritmos devuelven índices **distintos**,
todos válidos:

- Lineal → **1** (primera aparición).
- Binaria: mid = 0 + 7//2 = 3, D[3]=7 → **3**.
- Ternaria: mid1 = 0 + 7//3 = 2, D[2]=7 → **2**.
- Saltos: m=⌊√8⌋=2; D[1]=7 no <7 → no salta; lineal: D[0]=5<7 → prev=1; D[1]=7 → **1**.
- Interpolación (oficial): pos = 0 + (int)((7/10)·(7−5)) = (int)1,4 = 1 → D[1]=7 → **1**.
- Interpolación div. entera: q = 7//10 = 0 → pos=0 (5<7, lo=1); (1,7): q = 6//8 = 0 →
  pos=1 → D[1]=7 → **1** (2 iteraciones).
- Exponencial: D[0]≠7; i=1 (7≤7) → 2 (7≤7) → 4: D[4]=9>7. Binaria [2, 4]: mid=3 → **3**.

**x = 12** (válidos {5, 6}): todos devuelven **5**.
Interpolación (oficial): pos = 0 + (int)((7/10)·7) = (int)4,8999999999999995 = 4,
D[4]=9<12 → lo=5; pos = 5 + (int)((2/3)·0) = 5 → **5**. Variante entera: sondea 0,…,5 →
**5** (6 iteraciones). Saltos: D[1]=7<12 → prev=2, step=4; D[3]=7<12 → prev=4, step=6;
D[5]=12 para; lineal desde 4: 9<12 → 5; D[5]=12 → **5**. Exponencial: i=1,2,4,8 →
binaria [4, 7]: mid=5 → **5**.

**x = 5** → todos **0**. **x = 15** → todos **7** (variante entera: sondea 0,…,6 → lo=7=hi
→ guarda → 7).
**x = 8** (ausente interior) → todos **−1**. Interpolación (oficial):
pos = 0 + (int)((7/10)·3) = (int)2,0999999999999996 = 2 (D[2]=7<8, lo=3);
pos = 3 + (int)((4/8)·1) = 3 + (int)0,5 = 3 (D[3]=7<8, lo=4); 8 < D[4]=9 → sale → −1.
Variante entera: sondea 0,1,2,3 → lo=4 → sale → −1 (4 iteraciones).

### 5.3 Arreglo U (no uniforme: peor caso de interpolación, n = 10)

`U = [1, 2, 3, 4, 5, 6, 7, 8, 9, 1000]`

- x = 9 → todos **8**. Interpolación (oficial): pos = 0 + (int)((9/999)·8) = (int)0,072 = 0
  → lo=1; pos = 1 + (int)((8/998)·7) = 1 + (int)0,056 = 1 → lo=2; … avanza de a 1:
  **9 iteraciones** (pos = 0,1,…,8), comportamiento lineal O(n). La variante entera hace
  lo mismo (q = 0): 9 iteraciones. Binaria: mid 4, 7, 8 → 3 iteraciones.
- x = 1000 → todos **9**. Oficial: pos = 0 + (int)((9/999)·999) = (int)9,0 = 9,
  1 iteración. Variante entera: sondea 0,…,8 → lo=9=hi → guarda → 9.
- x = 500 (ausente) → todos **−1**. Oficial: pos = (int)((9/999)·499) = (int)4,4955 = 4
  (U[4]=5, lo=5); pos = 5 + (int)((4/995)·495) = 5 + (int)1,988 = 6 (lo=7);
  pos = 7 + (int)((2/993)·493) = 7 + (int)0,992 = 7 (lo=8); pos = 8 + (int)((1/992)·491)
  = 8 (lo=9); 500 < U[9]=1000 → sale → −1 (4 iteraciones). Variante entera: sondea 0,…,8
  → lo=9 → sale → −1 (9 iteraciones).

### 5.4 Arreglos mínimos y degenerados

| Arreglo | x | Lin. | Bin. | Ter. | Sal. | Int. | Exp. | IDiv |
|---|---|---|---|---|---|---|---|---|
| `[]` | 1 | −1 | −1 | −1 | −1 | −1 | −1 | −1 |
| `[42]` | 42 | 0 | 0 | 0 | 0 | 0 (guarda) | 0 | 0 (guarda) |
| `[42]` | 41 | −1 | −1 | −1 | −1 | −1 | −1 | −1 |
| `[42]` | 43 | −1 | −1 | −1 | −1 | −1 | −1 | −1 |
| `[3, 3]` | 3 | 0 | 0 | 0 | 0 | **0 (guarda; sin ella: división por cero)** | 0 | **0 (guarda)** |
| `[3, 3]` | 2 | −1 | −1 | −1 | −1 | −1 | −1 | −1 |
| `[3, 3]` | 4 | −1 | −1 | −1 | −1 | −1 | −1 | −1 |
| `[4, 4, 4, 4, 4]` | 4 | 0 | 2 | 1 | 0 | 0 (guarda) | 0 | 0 (guarda) |
| `[4, 4, 4, 4, 4]` | 3 | −1 | −1 | −1 | −1 | −1 | −1 | −1 |
| `[4, 4, 4, 4, 4]` | 5 | −1 | −1 | −1 | −1 | −1 | −1 | −1 |

Trazas: `[42]`, x=43, saltos: m=1, A[0]=42<43 → prev=1, step=2, prev ≥ 1 → −1.
`[3,3]`, x=4, saltos: m=1; A[0]<4 → prev=1; A[1]<4 → prev=2 ≥ 2 → −1. Exponencial:
i=1 (3≤4) → 2 → binaria [1, 1] → −1. `[4,4,4,4,4]`, x=4: binaria mid = 0 + 4//2 = 2;
ternaria mid1 = 0 + 4//3 = 1.

### 5.5 Arreglo O: valores de 8 dígitos, sin overflow (n = 100)

`O[i] = 10.000.000 + 909.090·i` para i = 0…98, y `O[99] = 99.999.999`
(O[23] = 30.909.070, O[24] = 31.818.160, O[98] = 99.090.820; estrictamente creciente).

Este caso queda como **prueba de que la versión `double` no desborda**: en la primera
iteración (lo=0, hi=99, x = O[24] = 31.818.160) el producto entero
(x − O[0])·(hi − lo) = 21.818.160 · 99 = **2.159.997.840 > 2³¹ − 1 = 2.147.483.647**
(en `int` daría −2.134.969.456, comprobado en Java). La fórmula oficial nunca forma ese
producto entero: opera en `double`.

x = O[24] = **31.818.160** → todos **24**.

- Interpolación (oficial): pos = 0 + (int)((99/89.999.999)·21.818.160) =
  (int)23,999976266666405 = 23 → O[23] < x → lo = 24; pos = 24 + (int)((75/…)·0) = 24 →
  **24** (2 iteraciones).
- Variante entera: q = 99 // 89.999.999 = 0 → sondea 0,…,24 → **24** (25 iteraciones;
  `q·(x−O[lo]) = 0`, sin productos grandes).
- x = 31.818.161 (ausente) → todos **−1**. Oficial: pos = (int)23,999977366666414 = 23
  (lo=24); pos = 24 + (int)((75/68.181.839)·1) = 24 + (int)1,1·10⁻⁶ = 24 (O[24]<x, lo=25);
  x < O[25] → sale → −1. Variante entera: 25 iteraciones → −1.
- x = O[98] = 99.090.820 → todos **98** (oficial: pos = (int)97,9999 = 97, luego 98;
  variante entera: 99 iteraciones).

### 5.6 Casos que distinguen las fórmulas (índice exacto con duplicados)

Sirven para detectar que se implementó la fórmula equivocada: el resultado es válido en
todas, pero el **índice exacto** cambia.

| Caso | Arreglo | x | Lin. | Bin. | Ter. | Sal. | Int. | Exp. | IDiv | Fórmula exacta (NO se implementa) |
|---|---|---|---|---|---|---|---|---|---|---|
| F1 | `[3, 52, 52]` | 52 | 1 | 1 | 2 | 1 | **1** | 2 | 1 | 2 |
| F2 | `[31, 54, 54, 59]` | 54 | 1 | 1 | 1 | 1 | **2** | 2 | **1** | 2 |
| F3 | `[1, 10, 20, 48]` | 48 | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3 |
| F3' | `[1, 10, 20, 48]` | 47 | −1 | −1 | −1 | −1 | −1 | −1 | −1 | −1 |
| F1' | `[3, 52, 52]` | 3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| F1'' | `[3, 52, 52]` | 51 | −1 | −1 | −1 | −1 | −1 | −1 | −1 | −1 |

Trazas:

- **F1, oficial vs. exacta.** lo=0, hi=2: (2/49)·(52−3) = (2/49)·49 = **1,9999999999999998**
  en IEEE 754 (Java y Python) → (int) = 1 → F1[1]=52 → **1**. La fórmula exacta daría
  2·49 // 49 = 2 → índice 2. Variante entera: q = 2 // 49 = 0 → pos 0 (3<52, lo=1); (1,2):
  F1[1] == F1[2] → guarda → **1**. Ternaria: mid1 = 0, mid2 = 2 − 0 = 2; F1[0]≠52,
  F1[2]=52 → 2. Saltos: m=1, F1[0]<52 → prev=1, step=2; F1[1]=52 no <52 → 1.
  Exponencial: i=1 → 2 → 4 → binaria [2, 2] → 2.
- **F2, oficial vs. variante entera.** Oficial: (3/28)·(54−31) = (3/28)·23 = 2,4643 → pos 2
  → F2[2]=54 → **2**. Variante entera: q = 3 // 28 = 0 → pos 0 (31<54, lo=1); (1,3):
  q = 2 // 5 = 0 → pos 1 → F2[1]=54 → **1**. Exponencial: i=1 (54≤54) → 2 (54≤54) → 4 →
  binaria [2, 3]: mid = 2 → 2.
- **F3 (iteraciones, mismo resultado).** Oficial: (3/47)·47 = 2,9999999999999996 → pos 2
  (20<48, lo=3) → lo=hi=3 → guarda → 3 (1 iteración + guarda; la exacta lo encontraría en
  1 iteración con pos=3). Variante entera: sondea 0, 1, 2 → lo=3 → guarda → 3.

### 5.7 Prueba aleatoria adicional (propiedad, no a mano)

Sobre un arreglo ascendente de 3.000 valores de 8 dígitos generado en la prueba con
semilla fija (como `test_sorting.py`), con duplicados forzados, para 2.000 claves (mitad
tomadas del arreglo, mitad aleatorias), para **los 7 algoritmos**: cada resultado es −1 ⇔
`bisect` (Python) / `Arrays.binarySearch` (Java) no la encuentra, y si no es −1 entonces
`arr[i] == x`. Para `LinearSearch` además: el índice es la **primera** aparición. (No se
exige lo mismo a `InterpolationSearchIntDiv` en esta prueba: con duplicados forzados
podría darse `q ≥ 1` cerca del final; su comportamiento lineal se comprueba en los casos
fijos de la sección 5 y con los datos reales en 6.2.)

## 6. Protocolo de medición — APROBADA (2026-10-22)

### 6.1 Datos

- Arreglos: `data/ascendente_{n}.txt`, n ∈ {1.000, 10.000, 100.000, 1.000.000} (Punto 1;
  **no se regeneran**).
- Claves: `data/claves_busqueda.txt` — 1.000 enteros, uno por línea, mismo formato que los
  demás archivos (ASCII, `\n` final en cada línea, sin encabezado). Generado **una sola
  vez** por `generate_data.py` (D1, aprobada 2026-10-22).

#### 6.1.1 Algoritmo de generación (normativo; el orden de las llamadas al RNG importa)

```
rng = random.Random(SEARCH_KEYS_SEED)                 # 20261016, independiente de SEED
pool = read_ints(data/aleatoria_1000.txt, 1000)        # tras comprobar su SHA-256
assert len(set(pool)) == 1000                          # el manifiesto dice duplicados = 0
present = rng.sample(pool, NUM_PRESENT_KEYS)           # 500, sin reemplazo, sobre la LISTA en orden de archivo
in_big = set(read_ints(data/aleatoria_1000000.txt, 1_000_000))   # tras comprobar su SHA-256
absent = []; seen = set()
while len(absent) < NUM_SEARCH_KEYS - NUM_PRESENT_KEYS:          # 500
    v = rng.randint(MIN_VALUE, MAX_VALUE)
    if v in in_big or v in seen: continue              # rechazo
    seen.add(v); absent.append(v)
keys = present + absent                                # presentes primero, luego ausentes
rng.shuffle(keys)                                      # D2: barajadas, mismo RNG
write_ints(data/claves_busqueda.txt, keys)
```

Resultado verificado por ejecución (2026-10-22) con Python **3.9.6** (el que generó los
datos) y **3.14.6**, idéntico en ambos:

| Dato | Valor |
|---|---|
| SHA-256 de `claves_busqueda.txt` | `22fdc47fbcdd3e4b4d26fbcd3eae5010bb3becaa981337c9fe9fa41aaa0c965f` |
| Primeras 5 claves | 40.484.834, 85.052.552, 51.204.555, 22.281.363, 16.722.397 |
| Mínimo / máximo | 10.070.741 / 99.952.252 |
| Valores distintos | 1.000 |
| Rechazos en ausentes | 4 por estar en el arreglo de 10⁶, 0 por repetidos |

Si `generate_data.py` produce otro SHA-256, la implementación no sigue este pseudocódigo
(p. ej. muestreó de un `set`, ordenó el pool, o cambió el orden de las llamadas al RNG).

#### 6.1.2 Unicidad de las claves (decisión documentada)

- **El archivo no tiene claves repetidas** (es "un conjunto" de 1.000 claves). Se
  garantiza por construcción: `aleatoria_1000` no tiene duplicados (manifiesto:
  `duplicados = 0`; el generador lo comprueba y falla si no) y `rng.sample` es sin
  reemplazo → 500 presentes distintas; las ausentes se rechazan si se repiten, y son
  disjuntas de las presentes porque no están en el arreglo de 10⁶ (que contiene
  a `aleatoria_1000` como prefijo).
- Por qué: una clave repetida pesaría doble en el promedio y en el checksum sin aportar
  información.
- Se valida también al leer (6.1.4).

#### 6.1.3 Interacción con los valores repetidos de los arreglos

Los arreglos tienen 0 / 0 / 55 / 5.604 repeticiones (n − distintos) en 10³…10⁶. Las 500
presentes son distintas entre sí, pero algunas aparecen **más de una vez en el arreglo**
porque el mismo valor volvió a salir más adelante en la secuencia de 10⁶ (verificado):

| n | presentes repetidas en `ascendente_n` |
|---|---|
| 1.000 | 0 |
| 10.000 | 0 |
| 100.000 | 1: 75.489.851 (×2) |
| 1.000.000 | 3: 14.782.552, 27.395.321, 75.489.851 (×2 cada una) |

Consecuencias: (1) la verificación acepta cualquier índice válido (3.0); (2) en 10⁵ y 10⁶
los algoritmos pueden devolver índices distintos para esas claves, por eso el checksum
cambia en 1–2 unidades entre algoritmos (tabla de 6.3); (3) Java y Python deben devolver
**el mismo** índice (8.3). El efecto en el tiempo es despreciable (3 de 1.000 claves).

#### 6.1.4 Consecuencia del muestreo sobre arreglos no ordenados (documentar en el informe)

Las presentes salen de `aleatoria_1000`, que es el prefijo de la secuencia: en
`aleatoria_1000000.txt` **todas las presentes están en los índices 0…999** (verificado:
índice máximo 999). **No afecta al Punto 2**, que busca en los arreglos ascendentes, donde
su posición es uniforme (los valores son aleatorios): en `ascendente_1000000` la posición
media de las presentes es 0,497·n, mínima 2.289, máxima 998.371. Sí importa si alguien
usara este archivo para una lineal sobre el arreglo aleatorio (ver Punto 3, 5.2).

#### 6.1.5 Reglas para `generate_data.py`

- Flujo de `main()`:
  1. Datos del Punto 1: igual que hoy (si existen y no hay `--force`, **no se tocan**;
     ya no se hace `return 0` en ese punto, se continúa al paso 2).
  2. Claves: si `claves_busqueda.txt` **no existe** (o hay `--force`), se generan con
     6.1.1; si existe, se comprueba su SHA-256 contra el manifiesto y se informa
     (falla si no coincide).
- Antes de leer `aleatoria_1000.txt`/`aleatoria_1000000.txt` comprueba su SHA-256 contra
  `manifest.json`; si no coincide, falla sin escribir nada.
- `manifest.json` se **actualiza**, no se reescribe: se carga, se agrega la entrada
  `archivos["claves_busqueda.txt"]` y se guarda. Todas las entradas y campos existentes
  (incluidos los 12 SHA-256 y `creado_utc` raíz) quedan **byte a byte con el mismo valor**.
  Entrada nueva:

  ```json
  "claves_busqueda.txt": {
    "n": 1000,
    "variante": "claves_busqueda",
    "sha256": "22fdc47fbcdd3e4b4d26fbcd3eae5010bb3becaa981337c9fe9fa41aaa0c965f",
    "semilla": 20261016,
    "presentes": 500,
    "ausentes": 500,
    "origen_presentes": "rng.sample(aleatoria_1000.txt, 500)",
    "origen_ausentes": "randint(MIN, MAX) con rechazo si está en aleatoria_1000000.txt o repetida",
    "orden": "presentes + ausentes, luego rng.shuffle",
    "python": "<sys.version de la corrida>",
    "creado_utc": "<fecha de la corrida>"
  }
  ```
- `--force` regenera todo (datos y claves); con las semillas fijas el resultado es idéntico.
- Prueba de no regresión: tras correr el generador, `git diff data/` solo muestra
  `claves_busqueda.txt` (nuevo) y la entrada nueva en `manifest.json`.

#### 6.1.6 Lectura (firmas exactas)

| | Python (`common/dataio.py`) | Java (`common/DataIO.java`) |
|---|---|---|
| Ruta | `search_keys_path(data_dir: Path = config.DATA_DIR) -> Path` → `data_dir / config.SEARCH_KEYS_FILE` | — (se usa `dataDir.resolve(Config.SEARCH_KEYS_FILE)`) |
| Lectura | `load_search_keys(data_dir: Path = config.DATA_DIR) -> list[int]` | `public static int[] readSearchKeys(Path dataDir) throws IOException` |
| Validación | `read_ints(path, config.NUM_SEARCH_KEYS)` (cantidad exacta y rango de 8 dígitos) + **falla con `ValueError` si hay valores repetidos** | `readInts(path, Config.NUM_SEARCH_KEYS)` + **`IOException` si hay valores repetidos** |

No comprueban el SHA-256 (eso lo hacen el generador y la prueba 8.5).

### 6.2 Experimentos

| `variante` | n | Claves buscadas (1 pasada = 1 ejecución) |
|---|---|---|
| `claves` | 1.000, 10.000, 100.000, 1.000.000 | las 1.000 de `claves_busqueda.txt`, en el orden del archivo |
| `inicio` | 1.000.000 (D7) | `arr[0]` = **10.000.033**, 1.000 veces |
| `centro` | 1.000.000 (D7) | `arr[(n−1)//2]` = `arr[499.999]` = **54.951.725**, 1.000 veces |
| `centro_alto` | 1.000.000 (D7) | `arr[n//2]` = `arr[500.000]` = **54.951.967**, 1.000 veces |
| `final` | 1.000.000 (D7) | `arr[n−1]` = `arr[999.999]` = **99.999.964**, 1.000 veces |

- **Dos centros (decisión del estudiante, 2026-10-20).** Con n par hay dos índices
  centrales y se miden **ambos**. El nombre `centro` se conserva para 499.999 porque
  `p3-comparativo.md` ya lo usa (la lineal cuesta 500.000 vs. 500.001 comparaciones: para
  el Punto 3 son equivalentes).
- Los índices de posición se calculan con `position_index(variante, n)` (Python, en
  `bench_search.py`) / `SearchBenchmark.positionIndex(String, int)` (Java): `inicio` → 0,
  `centro` → `(n−1)//2`, `centro_alto` → `n//2`, `final` → `n−1`; cualquier otro nombre →
  error. La clave se toma del arreglo cargado y se registra en la columna `clave`.
- Las **cuatro** claves son **únicas** en `ascendente_1000000.txt` (verificado
  2026-10-20). El benchmark lo comprueba al arrancar y falla si alguna aparece repetida.
- Orden de ejecución (ambos lenguajes): para cada n de `--sizes` ascendente, para cada
  algoritmo en orden de registro → `claves`; después, si n = `POSITION_N`, para cada
  algoritmo → `inicio`, `centro`, `centro_alto`, `final`.

Trabajo esperado con la implementación especificada, sobre los datos reales de n = 10⁶
(calculado ejecutando la referencia; sirve como comprobación de plausibilidad y para el
análisis):

| Algoritmo | inicio (idx 0) | centro (idx 499.999) | centro_alto (idx 500.000) | final (idx 999.999) |
|---|---|---|---|---|
| Lineal (comparaciones) | 1 | 500.000 | 500.001 | 1.000.000 |
| Binaria (iteraciones) | 19 | **1** | 19 | 20 |
| Ternaria (iteraciones) | 13 | 12 | 12 | 13 |
| Saltos (comparaciones del salto + del paso lineal) | 1 + 1 | **500 + 1.000** | **501 + 1** | 1.000 + 1.000 |
| Interpolación oficial (iteraciones) | 1 | 3 | 5 | 1 |
| Exponencial (duplicaciones + iter. binaria) | 0 + 1 (`arr[0]`) | 19 + 18 | 19 + 13 | 20 + 19 |
| Interpolación div. entera (iteraciones) | 1 | 500.000 | 500.001 | 999.999 + guarda |

En `claves`, n = 10⁶, la lineal hace en total **748.440.213** comparaciones por pasada
(≈ 748.440 = 0,748·n por búsqueda: presentes Σ(índice+1) = 248.440.213, ausentes
500 × 10⁶), verificado por ejecución.

**Artefacto del centro (a explicar en el informe).** Que el tiempo dependa de cuál de los
dos centros se elija es un efecto del orden de revisión, no ruido:

- Binaria: el primer `mid` es `0 + 999.999 // 2 = 499.999` → la clave del `centro` se
  encuentra en la **1.ª comparación** (mejor caso); la de `centro_alto` necesita
  **19 iteraciones**, casi el peor caso.
- Saltos (m = 1.000): 499.999 es el **último** elemento de su bloque [499.000, 499.999] →
  500 comparaciones de salto + 1.000 pasos lineales ≈ **1.500**; 500.000 es el **primero**
  del bloque siguiente → 501 + 1 ≈ **502**.
- Ternaria, interpolación oficial y exponencial cambian poco; lineal y variante entera
  difieren en 1 paso.

### 6.3 Región medida (idéntica en ambos lenguajes)

```
out = arreglo/lista de K enteros, preasignado                 # fuera del tiempo
[Java: System.gc()]   [Python: gc.collect(); gc.disable()]    # fuera del tiempo
t0 = reloj()
for j in 0 .. K-1:
    out[j] = search(arr, keys[j])
t1 = reloj()
[Python: gc.enable()]
verificar(out)                                               # fuera del tiempo
```

- Reloj: `System.nanoTime()` / `time.perf_counter_ns()`. K = `NUM_SEARCH_KEYS` = 1.000.
- `keys` es un `int[]`/`list[int]` de 1.000 elementos (para posición: la misma clave
  repetida 1.000 veces, armado fuera del tiempo).
- Funciones: Python `common/timing.py`:
  `time_searches(func, arr: list[int], keys: list[int], out: list[int]) -> int` (devuelve
  ns, escribe en `out`); Java: `static long timeSearches(SearchAlgorithm alg, int[] arr,
  int[] keys, int[] out)` en `SearchBenchmark`.
- **Anti-eliminación por el JIT (D6, aprobada):** cada resultado se guarda en `out[j]`
  (arreglo que escapa y se usa después), no se descarta. Tras la medición, fuera del
  tiempo: `checksum = Σ_j out[j]` **incluyendo los −1** (en `long` en Java) y
  `encontradas = #{j : out[j] ≠ −1}`.
- **No se copia** el arreglo (la búsqueda no lo modifica). Al final de todas las
  repeticiones de un n se comprueba una vez, fuera del tiempo, que `arr` sigue igual al
  archivo cargado (`Arrays.equals` / `==` contra una copia hecha al cargar).
- **Verificación** (fuera del tiempo, en cada repetición): para cada j,
  `out[j] == −1` ⇔ la clave no está (oráculo independiente: `Arrays.binarySearch(arr, k) < 0`
  en Java, `bisect.bisect_left` en Python); si `out[j] ≠ −1`: `0 ≤ out[j] < n` y
  `arr[out[j]] == keys[j]`. Además `encontradas` y `checksum` deben ser iguales en las
  5 repeticiones. Si algo falla → excepción y el benchmark aborta (como en el Punto 1).

**Valores de control (verificados por ejecución 2026-10-22: referencia propia del
pseudocódigo, implementación Python y Java del repo, los tres iguales).**

`encontradas = 500` en `claves` para todo n y algoritmo; `encontradas = 1.000` en las
posiciones. Checksum de `claves`:

| n | Lineal | Binaria | Ternaria | Saltos | Interp. | Exponencial | Interp. div. entera |
|---|---|---|---|---|---|---|---|
| 1.000 | 249.971 | 249.971 | 249.971 | 249.971 | 249.971 | 249.971 | 249.971 |
| 10.000 | 2.493.210 | 2.493.210 | 2.493.210 | 2.493.210 | 2.493.210 | 2.493.210 | 2.493.210 |
| 100.000 | 24.852.292 | 24.852.292 | 24.852.292 | 24.852.292 | 24.852.292 | **24.852.293** | 24.852.292 |
| 1.000.000 | 248.439.213 | **248.439.214** | **248.439.214** | 248.439.213 | **248.439.215** | 248.439.213 | 248.439.213 |

(Las diferencias de 1–2 vienen de las presentes repetidas de 6.1.3.) Checksum de
posición = `1.000 × índice`: 0 (`inicio`), 499.999.000 (`centro`), 500.000.000
(`centro_alto`), 999.999.000 (`final`) para los 7 algoritmos.

Uso: `plot_search.py` **falla** si Java ≠ Python (8.3) y **avisa** si un valor medido
difiere de esta tabla (indicaría desviación del pseudocódigo no detectada por las pruebas).

### 6.4 Repeticiones, estadístico, calentamiento

- 5 repeticiones (`REPETITIONS`); cada repetición = una pasada de las 1.000 búsquedas.
- Se reporta **promedio y desviación estándar muestral (n−1)** del **tiempo total** de
  la pasada (reutilizar `stats`/`Stats` del Punto 1), y el **tiempo promedio por
  búsqueda** = promedio_total / 1.000 (desviación por búsqueda = desviación total / 1.000),
  calculados desde los valores sin redondear.
- Java: calentamiento **global** (`GLOBAL_WARMUP_ROUNDS = 10` pasadas por algoritmo sobre
  `ascendente_{GLOBAL_WARMUP_N}` = `ascendente_10000.txt` con el archivo de claves) +
  calentamiento **por caso** igual que el Punto 1 (hasta `CASE_WARMUP_TARGET_SECONDS =
  0,25 s` o `CASE_WARMUP_MAX_RUNS = 20` pasadas, mínimo 1, no registradas; se omite si la
  predicción supera `CASE_WARMUP_SKIP_ABOVE_SECONDS`). Se reutilizan las constantes
  existentes. JVM con `-Xms2g -Xmx2g`, sin cambiar `-Xss`.
- Python: sin calentamiento (CPython sin JIT), con `gc.collect()` antes y `gc.disable()`
  durante la medición, como `time_inplace`.

### 6.5 Límite de 5 minutos y estimación

- "Ejecución" = una pasada de 1.000 búsquedas (D9, recomendación aceptada).
- `Growth` (Java y Python) con los miembros `LOGN`, `SQRTN`, `LOGLOGN` (`f(n)` = log₂ n,
  √n, log₂ log₂ n). Agregar miembros no cambia el Punto 1.
- Complejidad declarada por algoritmo (para predecir/estimar en `claves`):
  Lineal `N`, Binaria `LOGN`, Ternaria `LOGN`, Saltos `SQRTN`, Interpolación `LOGLOGN`,
  Exponencial `LOGN`, **Interpolación div. entera `N`**.
- `claves`: antes de cada n se predice `t(n_prev)·f(n)/f(n_prev)` con el mayor n medido;
  si supera 300 s → `estado = estimado` con `base_estimacion` (mismo formato que el Punto 1).
  Si una repetición supera el límite, se detienen las restantes (como en el Punto 1).
- Posiciones (solo n = 10⁶) — **corregido 2026-10-23 (auditoría, hallazgo A)**: cada
  posición se predice y decide **por separado**, con un factor **proporcional a su
  trabajo**:

  `predicción(posición) = promedio_total de claves del mismo algoritmo a 10⁶ × pasos(posición) / (pasos(claves) / 1.000)`

  Antes se usaba un solo factor (el de `final`) para las cuatro columnas; con eso, si la
  pasada `final` de la lineal superaba 300 s, también `inicio` (1 comparación) quedaba
  "estimada" con el tiempo de `final`, lo que es falso. Ahora, en la lineal, `inicio` se
  predice ≈ 1/748.440 de `claves` y siempre se mide; solo la posición cara puede quedar
  estimada.

  Pasos = iteraciones del bucle principal, contadas ejecutando el pseudocódigo sobre
  `ascendente_1000000.txt` (2026-10-23; coinciden con la tabla de 6.2). Constantes
  `POSITION_WORK` en `bench_search.py` y `SearchBenchmark.java` (no en `config`):

  | Algoritmo | pasos de la pasada `claves` | inicio | centro | centro_alto | final |
  |---|---|---|---|---|---|
  | Lineal | 748.440.213 | 1 | 500.000 | 500.001 | 1.000.000 |
  | Binaria | 19.430 | 19 | 1 | 19 | 20 |
  | Ternaria | 12.582 | 13 | 12 | 12 | 13 |
  | Saltos | 993.639 | 2 | 1.500 | 502 | 2.000 |
  | Interpolación oficial | 4.079 | 1 | 3 | 5 | 1 |
  | Exponencial (incluye la revisión de `arr[0]`) | 37.357 | 1 | 38 | 33 | 40 |
  | Interpolación div. entera (incluye la guarda final) | 504.349.278 | 1 | 500.000 | 500.001 | 1.000.000 |

  Ejemplos de factor: lineal `final` = 1.000.000 / 748.440,213 = ×1,336; lineal `centro`
  = ×0,668; lineal `inicio` = ×1,34·10⁻⁶; variante entera `final` = ×1,983.
  El factor ignora el costo fijo de cada llamada, así que **subestima** las posiciones
  baratas; no importa, porque solo decide si una pasada supera 300 s y en ese rango el
  trabajo domina. `base_estimacion` registra `t_claves(10⁶)`, su estado y el cociente de
  pasos. Si `claves` a 10⁶ quedó estimada, la predicción usa ese valor estimado; si no se
  corrió `claves` en 10⁶, se extrapola desde el mayor n medido. Para n ≠ 10⁶ no hay
  predicción de posición (no se corren).
- Expectativa: la **lineal y la variante entera en 10⁶ sí deben medirse** en ambos
  lenguajes. Órdenes de magnitud de pruebas informales (no son datos del informe):
  - Lineal, Python: ≈ 9 ms por búsqueda ausente en 10⁶ → ≈ 7 s por pasada de `claves` y
    ≈ 9 s por pasada `final`.
  - Variante entera, Python: ≈ 81 ns por iteración → ≈ 5·10⁸ iteraciones por pasada de
    `claves` en 10⁶ ≈ **40 s**; `centro`/`centro_alto` ≈ 40 s; `final` ≈ **81 s** por
    pasada. Todas < 300 s → se miden. (Estimación original: ≈ 17 min al benchmark de
    Python; **superada**, ver el punto siguiente.) En Java se espera del orden de segundos.
  - **Duración total (corregido 2026-10-23, auditoría, hallazgo C):** esos órdenes vienen
    de pruebas informales en otro equipo y con otro Python. Una corrida de prueba en el Mac
    oficial (Python 3.9.6, 2026-10-23) predijo por pasada en 10⁶: lineal ≈ 13 s (`claves`),
    ≈ 8,6 s (`centro`), ≈ 17 s (`final`); variante entera ≈ 76 s (`claves`, `centro`,
    `centro_alto`) y ≈ 151 s (`final`). Con 5 repeticiones: variante ≈ 32 min, lineal
    ≈ 4 min → benchmark de Python **≈ 40 min**; reservar ≈ 1 h para `run_punto2.sh`.
    Todas las pasadas quedan < 300 s, así que se espera medir todo. Si en esa máquina la pasada `final` de la variante entera supera
    300 s, queda estimada (solo esa posición; ver arriba).
  - El mecanismo de estimación existe por la regla del taller; con estos órdenes no
    debería activarse, pero si la máquina de la corrida es ≈ 4× más lenta, la pasada
    `final` de la variante entera en Python sí podría superar 300 s y quedaría estimada.
- Resolución del reloj (D10, recomendación aceptada): K = 1.000 también en posición,
  aunque la pasada más corta (p. ej. lineal o exponencial en `inicio`, Java) dure µs. Se
  registra en el entorno la resolución observada (mínima diferencia > 0 entre 1.000
  lecturas consecutivas del reloj) y se reporta el CV en `p2_resumen.csv`.

### 6.6 Entorno de medición (nota, 2026-10-22)

Las mediciones oficiales se corren en el Mac del P1 (`~/Downloads/taller3`, `.venv` con
Python 3.9.6 + matplotlib). En la máquina de desarrollo solo pruebas de corrección; nada de
lo medido allí entra al informe.

Verificación (corregida 2026-10-23, auditoría, hallazgo B): `scripts/entorno_medicion.sh`
compara contra **valores fijos** —no contra `results/entorno_*.json`, que una corrida de
`run_punto1.sh` podía reescribir—:

| Qué | Valor exigido | Si difiere |
|---|---|---|
| Arquitectura (`uname -m`) | `arm64` | aborta |
| macOS (`sw_vers -productVersion`) | `26.6.x` | aborta si cambia 26.6; **solo avisa** si cambia el parche (x ≠ 2) |
| Núcleos (`sysctl -n hw.ncpu`) | 10 | aborta |
| Java (`java.version`) | 21.0.9 | aborta |
| Python del `.venv` | 3.9.6 | aborta |
| matplotlib en el `.venv` | importable | aborta (antes de medir, no al final) |

Lo usan `run_punto1.sh`, `run_punto2.sh` y `run_punto3.sh` (`require_venv`,
`require_matplotlib`, `check_measurement_env`). Además ninguno sobrescribe resultados
oficiales existentes (`results/ordenamiento_*.csv`, `results/busqueda_*.csv` y sus
`entorno_*.json`) sin `--force`. El modelo del equipo (`hw.model`,
`machdep.cpu.brand_string`) se registra en `entorno_busqueda_{java,python}.json`.

## 7. Salidas — APROBADA (2026-10-22)

### 7.1 Cambios de código compartido (resumen para el implementador)

- `config.py` (fuente de verdad) + `Config.java` (réplica):

  | Python (`config.py`) | Java (`Config.java`) | Valor |
  |---|---|---|
  | `SEARCH_KEYS_FILE` | `public static final String SEARCH_KEYS_FILE` | `"claves_busqueda.txt"` |
  | `SEARCH_KEYS_SEED` | — (Java no genera datos; `Config.java` tampoco replica `SEED`) | `20261016` |
  | `NUM_SEARCH_KEYS` | `public static final int NUM_SEARCH_KEYS` | `1000` |
  | `NUM_PRESENT_KEYS` | `public static final int NUM_PRESENT_KEYS` | `500` |
  | `POSITION_N` | `public static final int POSITION_N` | `1_000_000` |
  | `POSITION_VARIANTS` (tupla) | `public static final String[] POSITION_VARIANTS` | `("inicio", "centro", "centro_alto", "final")`, en ese orden |
  | `SEARCH_VARIANTS` (tupla) | `public static final String[] SEARCH_VARIANTS` | `("claves",) + POSITION_VARIANTS` |

- `Growth` / `estimation.Growth`: + `LOGN`, `SQRTN`, `LOGLOGN` (ya presentes en el árbol
  de trabajo, sin commit).
- `dataio` / `DataIO`: `search_keys_path`, `load_search_keys` / `readSearchKeys` (6.1.6).
- `timing.py`: `time_searches` (6.3).
- `results.py` / Java `common/`: **escritor nuevo**, sin tocar el del Punto 1:
  Python `SearchResultRecord` + `SearchCsvWriter` en `common/results.py`; Java
  `common/SearchResultRecord.java` + `common/SearchCsvWriter.java` (`Locale.ROOT`).
- `generate_data.py`: 6.1.5.
- `run_punto2.sh` (nuevo, raíz; mismo estilo que `run_punto1.sh`, `set -euo pipefail`):
  1. `(cd python && python3 -m taller3.generate_data)` — genera las claves si faltan.
  2. `rm -rf java/out && javac -encoding UTF-8 -d java/out $(find java/src -name "*.java")`
  3. `java -cp java/out taller3.tests.SearchSelfTest` y
     `(cd python && python3 -m unittest tests.test_searching)`
  4. `java -Xms2g -Xmx2g -cp java/out taller3.bench.SearchBenchmark`
  5. `(cd python && python3 -m taller3.bench_search)`
  6. `(cd python && python3 -m taller3.plot_search)`
- Flags de los benchmarks (como el Punto 1): `--sizes`, `--algos`, `--variants`
  (subconjunto de `SEARCH_VARIANTS`), `--reps`, `--limit`, `--out`. Por defecto
  `--out results/busqueda_{java,python}.csv`.
- `.gitignore`: sin cambios necesarios (`results/prueba_*.csv` ya se ignora).

### 7.2 CSV `results/busqueda_{java,python}.csv`

Mismo estilo que el Punto 1 (UTF-8, coma, sin espacios, encabezado en la primera línea,
fila escrita y vaciada al terminar cada caso). Columnas, en este orden:

```
algoritmo,lenguaje,variante,n,num_busquedas,clave,rep_1_ns,rep_2_ns,rep_3_ns,rep_4_ns,rep_5_ns,promedio_ns,desv_estandar_ns,promedio_por_busqueda_ns,desv_por_busqueda_ns,encontradas,checksum,estado,causa,base_estimacion
```

| Columna | Tipo / formato | Contenido |
|---|---|---|
| `algoritmo` | texto | uno de los 7 nombres de 2.1 |
| `lenguaje` | texto | `Java` / `Python` (igual que el Punto 1) |
| `variante` | texto | `claves`, `inicio`, `centro`, `centro_alto`, `final` |
| `n` | entero | tamaño del arreglo |
| `num_busquedas` | entero | 1000 |
| `clave` | entero o vacío | vacío en `claves`; el valor buscado en las posiciones |
| `rep_i_ns` | entero (ns) | tiempo **total** de la pasada i; vacío si no se midió |
| `promedio_ns`, `desv_estandar_ns` | `%.1f` | del tiempo total; desviación muestral (n−1) |
| `promedio_por_busqueda_ns`, `desv_por_busqueda_ns` | `%.3f` | anteriores / `num_busquedas` |
| `encontradas`, `checksum` | entero | vacíos si `estado = estimado` |
| `estado` | texto | `medido`, `estimado` o `fallido` (mismo significado que en el Punto 1, README) |
| `causa`, `base_estimacion` | texto | mismo formato que el Punto 1; vacíos si se midió |

Entorno: `results/entorno_busqueda_{java,python}.json` (**no** sobrescribir
`entorno_{java,python}.json` del Punto 1); con `--out` distinto se escribe
`entorno_<stem del --out>.json` junto al CSV. Contenido como el del Punto 1, más
`resolucion_reloj_ns` (6.5) y el SHA-256 de `claves_busqueda.txt` usado.

### 7.3 Figuras y tablas (`plot_search.py`)

Exigidas por el enunciado:

1. `figures/p2_crecimiento_java.png` y 2. `figures/p2_crecimiento_python.png`: líneas,
   x = n, y = tiempo promedio por búsqueda (µs), **log-log**, una línea por algoritmo, solo
   `variante = claves`; puntos estimados con línea punteada y marcador distinto.
   **Línea extra** para `InterpolationSearchIntDiv`, marcada como variante: estilo
   raya-punto (`-.`), mismo color que "Interpolación" en tono **más oscuro** (corregido
   2026-10-23: el tono claro casi no se veía), leyenda
   "Interpolación (división entera, GfG Java) — variante". (El punteado `:` queda
   reservado para estimados.)
3. `figures/p2_java_vs_python_n1000000.png`: barras, n = 10⁶, `claves`, dos barras por
   algoritmo (Java, Python), eje y logarítmico, **valor sobre cada barra**, estimados con
   barra rayada. La variante va como 7.º grupo, al final, separada por una línea vertical
   tenue y con la etiqueta "(variante)".
4. `figures/p2_posicion_java.{csv,md}` y 5. `figures/p2_posicion_python.{csv,md}`:
   n = 10⁶, una fila por algoritmo (7, en orden de registro, la variante al final marcada
   "(variante)").
   - CSV: `algoritmo,etiqueta,inicio_ns,centro_ns,centro_alto_ns,final_ns,estimados`
     (tiempo promedio por búsqueda en ns, `%.1f`; `estimados` = lista separada por `;` de
     las variantes con `estado = estimado`, vacía si ninguna).
   - `.md`: columnas `Algoritmo | inicio (0) | centro (499.999) | centro (500.000) |
     final (999.999)`, valores con 3 cifras significativas **y su unidad en cada celda**
     (µs, ms o s; corregido 2026-10-23: "18.100 µs" se leía como 18,1 µs), prefijo `~` si es
     estimado; nota al pie remitiendo al artefacto del centro (6.2).
   - **Pie de la tabla (obligatorio, `.md` y la tabla del informe)**, aprobado 2026-10-22:
     declarar qué índice se usó como cada centro y por qué difieren, p. ej.:
     "`centro` = índice 499.999 = ⌊(n−1)/2⌋ (valor 54.951.725); `centro_alto` = índice
     500.000 = ⌊n/2⌋ (valor 54.951.967). 499.999 es el **mejor caso de la binaria**: es su
     primer `mid` (1 comparación), mientras que 500.000 requiere 19 iteraciones; en saltos
     ocurre lo contrario (499.999 es el último elemento de su bloque, ≈ 1.500 pasos;
     500.000 el primero del siguiente, ≈ 502). Ver análisis de posiciones." El texto exacto
     lo redacta el estudiante; los índices, valores y conteos deben ser estos.

De apoyo (como en el Punto 1):

- `figures/p2_razones_crecimiento.csv`:
  `lenguaje,algoritmo,complejidad,n_desde,n_hasta,razon_observada,razon_teorica`
  (t(10n)/t(n) de `promedio_por_busqueda_ns`, `claves`; teórica de 3.7). Solo entre dos
  puntos **medidos** (corregido 2026-10-23): con un estimado la razón observada sería la
  teórica por construcción.
- `figures/p2_resumen.csv`:
  `lenguaje,algoritmo,variante,n,promedio_ns,desv_estandar_ns,cv,promedio_por_busqueda_ns,estado`
  (`cv` = desv / promedio).

Unidad en las gráficas: µs por búsqueda (eje log), con la etiqueta de unidad explícita.

## 8. Cómo se verifica

### 8.1 Pruebas unitarias (APROBADA 2026-10-20)

`aa-test-writer`: todos los casos de la sección 5 para los 7 algoritmos en ambos
lenguajes, comprobando índice exacto y validez (D-extra); propiedad aleatoria contra
oráculo independiente (`bisect` / `Arrays.binarySearch`). Los casos 5.6-F1 y F2 son
obligatorios: distinguen la fórmula `double` de la exacta y de la entera.

### 8.2 Verificación en el benchmark — APROBADA (2026-10-22)

Cada pasada medida se verifica fuera del tiempo (6.3); si falla, el benchmark aborta.
Al arrancar: claves de posición únicas (6.2); al terminar cada n: arreglo sin modificar.

### 8.3 Equivalencia Java ↔ Python en los resultados — APROBADA (2026-10-22)

Para cada (algoritmo, variante, n) con `estado = medido` en **ambos** CSV, `checksum` y
`encontradas` deben ser **idénticos**. `plot_search.py` lo comprueba antes de graficar y
**falla** (excepción con la lista de diferencias) si no; si un caso está estimado en un
lenguaje, se omite de la comparación y se informa. Además avisa si difieren de la tabla
de control de 6.3.

**Firmas fijadas por las pruebas (aprobadas por el estudiante 2026-10-22)**
(`python/tests/test_plot_search.py`):

- `plot_search.check_equivalence(rows_java: list[dict[str, str]], rows_python: list[dict[str, str]]) -> list[str]`
  — filas de §7.2 tal como las da `csv.DictReader`. **Lanza `ValueError`** si algún
  (algoritmo, variante, n) medido en ambos difiere en `checksum` o `encontradas`; el
  mensaje lista **todas** las diferencias. Si no lanza, **devuelve los avisos**: un aviso
  por cada caso omitido por estar `estimado` en algún lenguaje y uno por cada fila medida
  que difiere de la tabla de control de 6.3 (claves: por n y algoritmo, `encontradas` =
  500; posiciones: `checksum` = 1.000 × índice, `encontradas` = 1.000). Cada mensaje
  nombra algoritmo, variante y n (entero sin separadores). Orden de filas irrelevante.
- Ambas funciones (8.3 y 8.4) se importan **sin matplotlib** (import perezoso dentro de las
  funciones que grafican).

### 8.4 Plausibilidad (avisos, no errores) — APROBADA (2026-10-22)

`plot_search.py` imprime un aviso (no falla) si:

- La lineal o la variante entera no crecen entre ×5 y ×20 por cada ×10 en n, para n ≥ 10⁴.
- En n = 10⁶, `InterpolationSearch` no es ≥ 100× más rápida que la lineal (sospechar que se
  implementó la fórmula de división entera en la oficial).
- `InterpolationSearchIntDiv` es más de 10× más rápida que la lineal (sospechar que se
  implementó la fórmula `double` en la variante).
- La binaria en `centro` no es más rápida que la binaria en `centro_alto`; saltos en
  `centro` no es más lenta que saltos en `centro_alto` (esperado ≈ 3×: ≈ 1.500 vs ≈ 502
  pasos).
- La lineal-`final` no está entre 1,5× y 2,5× la lineal-`centro`, o su tiempo por
  elemento recorrido (t por búsqueda / 10⁶) baja de 0,05 ns: sospechar que el JIT eliminó
  trabajo.

**Firma fijada por las pruebas (aprobada por el estudiante 2026-10-22)**
(`python/tests/test_plot_search.py`):

- `plot_search.plausibility_warnings(rows: list[dict[str, str]]) -> list[str]` — filas de
  **un** CSV (un lenguaje); usa `promedio_por_busqueda_ns` **solo de filas medidas**;
  devuelve un aviso por condición disparada (lista vacía si ninguna), cada uno nombra el
  algoritmo implicado; nunca lanza. Límites: crecimiento en [5, 20] (inclusivo, se prueba
  en el tramo 10⁵ → 10⁶); interpolación: t_lineal / t_interp ≥ 100 no avisa; variante
  entera: t_lineal / t_intdiv > 10 avisa (= 10 no); binaria: avisa si t(centro) ≥
  t(centro_alto); saltos: avisa si t(centro) ≤ t(centro_alto); lineal: final/centro en
  [1,5; 2,5] no avisa y t(final)/10⁶ = 0,05 ns no avisa.

### 8.5 Prueba versionada de equivalencia Java ↔ Python — APROBADA con condiciones (2026-10-22)

Motivo: la auditoría marcó que la equivalencia solo se comprobaba al final, en
`plot_search.py`, tras ~1 h de benchmark. Esta prueba la adelanta a `SearchSelfTest` y
`test_searching.py`, no requiere correr el otro lenguaje y **ambos lenguajes se comparan
contra las mismas constantes** escritas en esta spec.

**Condición del estudiante: las constantes se calculan de forma INDEPENDIENTE de la
implementación del repo.** Se obtienen con `bisect.bisect_left` de la biblioteca estándar
de Python (oráculo) o con fórmula cerrada, nunca ejecutando `taller3.searching`. Por eso
solo se usan arreglos **sin duplicados**, donde el índice correcto es único y cualquier
algoritmo correcto debe devolverlo.

Sobre `out[j] = search(arr, Q[j])`, j = 0…K−1, se calculan (en Java con `long`):

- `S1 = Σ out[j]` (**checksum**; el −1 de cada ausente **se incluye** en la suma),
- `enc = #{j : out[j] ≠ −1}` (segunda constante: evita que un −1 espurio compense otro error),
- `S2 = Σ (j + 1) · out[j]` (sensible al orden de las claves; detecta índices permutados
  entre claves que `S1` no ve).

Las tres deben coincidir **exactamente** y son **iguales para los 7 algoritmos**.

#### Parte A — arreglo sintético grande sin duplicados (sin RNG, sin archivos)

Definición exacta (`//` = división entera, operandos ≥ 0):

```
N = 100_000; K = 200
A[i] = 10_000_500 + 7*i + (i*i) // 2000                       para i = 0 … N−1
p(j) = (j * 7919) % N                                           (7919 primo, coprimo con N)
Q[j] = 10_000_000 + j          si j % 10 == 0   (ausente, menor que el mínimo)
     = A[N−1] + 1 + j          si j % 10 == 1   (ausente, mayor que el máximo)
     = A[p(j)] + 1             si j % 10 ∈ {2, 3} (ausente interior: los huecos son ≥ 7)
     = A[p(j)]                 si j % 10 ≥ 4    (presente en el índice p(j))
```

**Java:** `i*i` llega a 9.999.800.001 > 2³¹−1, así que se escribe
`(int) ((long) i * i / 2000)`; el resultado cabe en `int`. `j*7919 ≤ 1.575.881` cabe en
`int`. Python no tiene este problema.

Comprobaciones de construcción (para que el implementador detecte un arreglo mal generado):

| Dato | Valor |
|---|---|
| `A[0]`, `A[1]`, `A[2]` | 10.000.500, 10.000.507, 10.000.514 |
| `A[N−1]` | 15.700.393 (todos los valores son de 8 dígitos) |
| Estrictamente creciente | sí; hueco mínimo 7, máximo 107 |
| `ΣA` | 1.201.713.770.300 |
| `Q[0..5]` | 10.000.000, 15.700.395, 10.236.788, 10.448.997, 10.723.916, 11.061.547 |
| `ΣQ` (K = 200) | 2.431.583.865; las 200 claves son distintas |
| Reparto de claves | 20 < mín, 20 > máx, 40 ausentes interiores (p ∈ [2.947, 98.897]), 120 presentes (índices ∈ [741, 98.716]) |

**Constantes esperadas (los 7 algoritmos, ambos lenguajes):**

| Constante | Valor |
|---|---|
| `enc` | **120** |
| `S1` (checksum) | **5.953.340** |
| `S2` | **629.320.400** |

Cómo se calcularon (2026-10-22, script propio en Python 3.14.6 que **no importa** el repo):
`out[j] = i` si `i = bisect_left(A, Q[j])` cumple `i < N and A[i] == Q[j]`, si no −1.
Comprobación por fórmula cerrada de `S1`: las presentes son las j con `j % 10 ≥ 4`
(120 claves) y su índice es `p(j)`; `Σ p(j) = 5.953.420`; las 80 ausentes aportan −80;
`5.953.420 − 80 = 5.953.340` ✓. (A posteriori, la implementación Python del repo da los
mismos tres valores para los 7 algoritmos; esto es confirmación, no la fuente.)

**Guarda de regresión del desbordamiento `int` en Java (documentado).** La fórmula
oficial (3.5.1) opera en `double` y no desborda. Si alguien la reemplazara por la del
texto, "multiplicar primero", en `int`:
`pos = lo + ((x − arr[lo]) * (hi − lo)) / (arr[hi] − arr[lo])`,
con N = 10⁵ el producto supera 2³¹−1 = 2.147.483.647 en cuanto `x − arr[lo] > 21.475`
(con `lo = 0`, `hi = 99.999`). Ejemplo concreto, primera iteración con `Q[4] = 10.723.916`
(presente en el índice 31.676):

```
x − arr[0]          = 10.723.916 − 10.000.500 = 723.416
(x − arr[0])·(hi−lo) = 723.416 · 99.999 = 72.340.876.584      > 2³¹−1
en int (mód 2³²)    = −673.567.448
/ (arr[hi]−arr[lo]) = −673.567.448 / 5.699.893 = −118 (trunca hacia 0)
pos                 = −118  → ArrayIndexOutOfBoundsException
(correcto, double o exacto: pos = 12.691)
```

Simulando esa variante con aritmética de 32 bits sobre las 200 claves: 44 correctas
(las 40 ausentes fuera de rango, que no entran al ciclo, y 4 más), 88 lanzan
`ArrayIndexOutOfBoundsException` y 68 entrarían en **ciclo infinito** (`pos < lo` hace
retroceder `lo`). La primera clave afectada en orden es `Q[2]` (ausente interior) →
excepción con `pos = −375`, así que la prueba **falla** antes de llegar a un ciclo
infinito si recorre las claves en orden j = 0, 1, 2, … y no captura la excepción para
continuar. Regla para `aa-test-writer`: en Java, recorrer las claves en ese orden y dejar
que la primera excepción haga fallar el caso (opcional: ejecutar la parte A de cada
algoritmo con un tiempo máximo de 10 s para que un ciclo infinito también se reporte
como fallo y no como cuelgue). Con n = 1.000 (parte B) el producto máximo,
≈ 9·10⁷ · 999 ≈ 9·10¹⁰, también desbordaría, pero la parte A además cubre el tamaño de
los datos reales (10⁵) y no depende de archivos.

**Tiempo.** Lineal y variante entera son O(n) por clave: ≈ 1,40·10⁷ pasos de la lineal
(las 80 ausentes recorren los 10⁵ elementos) y ≈ 7,9·10⁶ iteraciones de la variante
entera. Medido con la implementación Python del repo (3.14.6, solo para dimensionar K):
lineal 0,13 s, variante entera 0,58 s, las otras cinco < 0,002 s; **total ≈ 0,7 s**. Con
Python 3.9 (≈ 1,5–2× más lento) se estima ≈ 1,1–1,4 s, dentro del objetivo de ≲ 2 s. Por
eso K = 200 y no 1.000 (≈ 3,5 s). En Java, < 0,1 s.

#### Parte B — duplicados: por qué no hay checksum constante

Con valores repetidos, cada algoritmo correcto puede devolver un índice **distinto**
entre las apariciones (la lineal, saltos y la variante entera devuelven la primera; la
binaria, la ternaria, la exponencial y la interpolación oficial, la que encuentren
primero según su orden de sondeo). `bisect` solo da la primera aparición, así que no
sirve de oráculo independiente para un checksum por algoritmo; obtenerlo exigiría
ejecutar la implementación del repo (o una copia de su pseudocódigo), que es justo lo que
la condición prohíbe. Por eso los duplicados se cubren así:

1. **Propiedad** (todos los algoritmos, ambos lenguajes): si `out ≠ −1`, entonces
   `arr[out] == x`; si `out == −1`, `x` no está en el arreglo (comprobado con `bisect` /
   `Arrays.binarySearch`). Ver 5.7.
2. **Índices exactos** de los casos a mano de §5 con duplicados (5.2 arreglo D, 5.6-F1 y
   F2), resueltos sin ejecutar la implementación. Como Java y Python deben pasar los
   mismos casos con el mismo índice exacto, la equivalencia entre lenguajes sobre
   duplicados queda probada en esos casos.
3. En el benchmark, la igualdad de `checksum`/`encontradas` entre los CSV de Java y
   Python (8.3) cubre los 3 valores repetidos reales de 10⁵/10⁶ (6.1.3).

(Se elimina el arreglo sintético E con duplicados de la versión anterior de esta
sección: sus constantes por algoritmo se habían obtenido con referencias que reproducían
el pseudocódigo del repo, no con un oráculo independiente.)

#### Parte C — archivo real: `claves_busqueda.txt` sobre `ascendente_1000.txt` (se mantiene)

Se mantiene separada de la parte A porque prueba **otra cosa**: la cadena real de
lectura (`load_search_keys`/`readSearchKeys`, `read_ints`/`readInts`), la validación de
cantidad, rango y unicidad, el reparto 500/500 y, en Python, el SHA-256 del archivo
(= el de 6.1.1). La parte A no toca archivos. Cuesta < 0,05 s (n = 1.000).

Para los **7** algoritmos: `enc = 500`, `S1 = 249.971`, `S2 = 120.950.349` (iguales entre
algoritmos porque `ascendente_1000` no tiene duplicados). **Recalculado de forma
independiente el 2026-10-22**: claves regeneradas con el pseudocódigo de 6.1.1 en un
script propio (SHA-256 = `22fdc47f…0c965f`, coincide) y búsqueda con `bisect_left`; da los
mismos tres valores. Si el archivo no existe, la prueba **falla** con el mensaje "genera
las claves: python3 -m taller3.generate_data" (no se salta: el archivo estará versionado).

## 9. Preguntas de análisis que la salida debe permitir responder

- (Enunciado) ¿En qué algoritmos cambia el tiempo según la posición de la clave y en
  cuáles no? ¿Por qué, según el orden en que cada uno revisa los elementos? — usar las
  tablas de posición y la tabla de trabajo esperado de 6.2.
- ¿Por qué la binaria y los saltos dan tiempos tan distintos en los dos centros
  (499.999 vs. 500.000)? (artefacto de 6.2: primer `mid` de la binaria, fin/inicio de
  bloque en saltos).
- (Aprobado 2026-10-22) En el análisis de posiciones el informe debe **decir qué índice se
  usó como "centro" (499.999 = ⌊(n−1)/2⌋) y como "centro_alto" (500.000 = ⌊n/2⌋)** y
  explicar que 499.999 es el **mejor caso de la binaria** (es su primer `mid`: 1
  comparación frente a 19), de modo que la columna `centro` sola haría parecer a la
  binaria más rápida de lo que es para un elemento "del medio"; y que en saltos el efecto
  es el inverso. Conclusión que debe quedar escrita: "el centro" no es una posición
  neutra; depende de cómo cada algoritmo parte el intervalo.
- Al multiplicar n por 10, ¿cuántas veces aumenta el tiempo por búsqueda de cada
  algoritmo y cómo se compara con O(n), O(√n), O(log n), O(log log n)? (`p2_razones_crecimiento.csv`)
- ¿Por qué la ternaria no supera a la binaria pese a dividir en tres?
- ¿Por qué la interpolación funciona tan bien con estos datos (uniformes) y cuándo
  degeneraría (caso U)?
- ¿Por qué la versión de división entera publicada en GfG Java y Python recursivo, siendo "la misma"
  búsqueda por interpolación, se comporta como una búsqueda lineal con estos datos?
  ¿Por qué ninguna prueba de corrección lo detecta? (3.5.2)
- ¿Por qué la diferencia Java/Python es mayor o menor según el algoritmo? (en los
  logarítmicos domina el costo fijo de la llamada en Python; en la lineal, el costo por
  elemento del intérprete).
- ¿Cómo se estimaron los casos que no terminaron (si los hubo)?

## 10. Decisiones del estudiante

### 10.1 Resueltas el 2026-10-20

| Decisión | Resolución |
|---|---|
| Fórmula de interpolación (antes 3.5-2, "por confirmar") | **Dos algoritmos medidos por separado**: `InterpolationSearch` (oficial, fórmula `double` de GfG C++/C; Python con `float` como el Python iterativo de GfG) e `InterpolationSearchIntDiv` (variante, fórmula de división entera de GfG Java y Python recursivo; en Java división entera de `int`). Sin `long`. |
| D3. Índice de "centro" | **Medir ambos**: `centro` = 499.999 = (n−1)//2 y `centro_alto` = 500.000 = n//2. Tabla de posición con 4 columnas; el artefacto se explica en el informe. |
| D2. Orden de las claves | Aceptada la recomendación: **barajadas** con el mismo RNG. |
| D4. Variante de binaria/ternaria/exponencial | Aceptada: **todas iterativas**; la exponencial reutiliza `searchRange`. |
| D5. Arreglo vacío | Aceptada: `n == 0 → −1` explícito en saltos y exponencial. |
| D6. Anti-eliminación JIT | Aceptada: `out[j]` dentro del tiempo, checksum fuera. |
| D8. `min()` en Python | Aceptada: expresión condicional `a if a < b else b`. |
| D-extra. Pruebas con índice exacto | Aceptada: pruebas unitarias con índice exacto + validez; benchmark con validez + igualdad de checksum. |

### 10.2 Resueltas el 2026-10-22

| Decisión | Resolución |
|---|---|
| D1. Origen de las 500 presentes | **Opción A**: 500 sin reemplazo de `aleatoria_1000.txt` (presentes en los 4 tamaños por ser prefijos); 500 ausentes de 8 dígitos verificadas ausentes en el arreglo de 10⁶; un solo archivo `data/claves_busqueda.txt`, semilla fija 20261016, generado una vez por `generate_data.py` sin regenerar ni cambiar los hashes de los datos existentes (6.1). Claves sin repetidos (6.1.2). Consecuencia documentada: en el arreglo aleatorio de 10⁶ las presentes están en índices < 1.000 (6.1.4). Descartadas: B (un archivo por n) y C (presentes de `aleatoria_1000000`). |
| D7. Posición solo en n = 10⁶ | **Resuelta (recomendación aceptada)**: el experimento de posición se corre solo en n = 1.000.000 (lo que pide la tabla); no en los 4 tamaños. |
| D9. Unidad del límite de 5 min | **Resuelta (recomendación aceptada)**: una ejecución = una pasada de 1.000 búsquedas (no una búsqueda individual). |
| D10. K en posición | **Resuelta (recomendación aceptada)**: K = 1.000 también en posición (literal del enunciado), sin repetir internamente la pasada; se reportan CV y resolución del reloj. |

### 10.3 Confirmaciones del 2026-10-22 (con condiciones)

| Decisión | Resolución |
|---|---|
| 8.5 Prueba versionada de equivalencia | **APROBADA con condiciones, incorporadas**: constantes calculadas de forma independiente (`bisect` / fórmula cerrada, sin importar el repo). Parte A: arreglo sintético N = 10⁵ sin duplicados por fórmula, K = 200 claves (presentes, ausentes < mín, > máx e interiores) → `enc = 120`, `S1 = 5.953.340`, `S2 = 629.320.400`, iguales para los 7; actúa como guarda del desbordamiento `int` de "multiplicar primero" en Java (ejemplo concreto en 8.5). Parte B: duplicados sin checksum constante, cubiertos por la propiedad `arr[i] == x`, los índices exactos de §5 y 8.3. Parte C (archivo real, antes "(b)") se mantiene y se recalculó con `bisect`. Se elimina el arreglo E con duplicados. Tiempo ≈ 0,7 s en Python 3.14. |
| Umbrales de 8.4, formato `%.3f`, `entorno_<stem>.json` | **APROBADOS** sin cambios. |
| Índices del centro en el informe | **APROBADO**: pie obligatorio en la tabla de posición (7.3) y pregunta de análisis (§9). |
| Banda de sensibilidad del Punto 3 | **APROBADA** como aproximación; se documenta en `p3-comparativo.md`. |

### 10.4 Correcciones de la auditoría del 2026-10-23

| Hallazgo | Resolución |
|---|---|
| A. Factor único de posición | **Corregido**: factor por posición proporcional al trabajo, con la tabla de pasos de 6.5; cada posición decide medir o estimar por separado. |
| B. Entorno | **Corregido**: `scripts/entorno_medicion.sh` compara contra valores **fijos** (macOS 26.6.x en arm64, 10 núcleos, Java 21.0.9, Python 3.9.6) y lo usan `run_punto1.sh` y `run_punto2.sh`; ninguno sobrescribe los resultados oficiales sin `--force`. El modelo del Mac (`hw.model`, `machdep.cpu.brand_string`) queda en `entorno_busqueda_*.json`. |
| C. Duración | **Corregido**: Python ≈ 40 min o más (6.5 y README). |
| Menores | matplotlib se comprueba antes de medir; razones de crecimiento solo entre puntos medidos; valores de las tablas de posición con su unidad (µs/ms/s) en vez de "18.100 µs"; color de la variante oscurecido; 3 pruebas nuevas (verificación de cada pasada, camino de los estimados, predicción por posición) en Python y Java. |

## 11. Preguntas abiertas

Resueltas el 2026-10-22 (ver 10.3): prueba 8.5 (rediseñada con oráculo independiente),
umbrales de 8.4, `%.3f`, `entorno_<stem>.json`, índices del centro en el informe y banda
de sensibilidad del Punto 3.

Pendientes:

- (Menor, para `aa-test-writer`) ¿Se envuelve la parte A de 8.5 en Java con un tiempo
  máximo (p. ej. 10 s por algoritmo) para que un ciclo infinito por desbordamiento se
  reporte como fallo y no como cuelgue? Recomendado; con el orden de claves actual la
  primera clave afectada ya lanza excepción.
- ¿El profesor acepta incluir en la tabla de posición una 4.ª columna (`centro_alto`) y
  en las gráficas una 7.ª línea (variante de interpolación) además de lo pedido? Si no,
  ambas se mueven a un anexo sin cambiar las mediciones.
- Las referencias de libro de 3.7 (edición/página del sílabo) siguen *por confirmar*.
- ¿Se quiere también la mediana en `p2_resumen.csv`? El taller pide promedio y
  desviación; la mediana sería solo informativa.
- Costo de tiempo de la variante entera: ≈ 32 min del benchmark de Python, que en total
  tarda ≈ 40 min (6.5, corrección C del 2026-10-23). Para depurar se puede excluir con `--algos`; en la corrida
  oficial (`run_punto2.sh`) se incluye.
