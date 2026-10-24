# Punto 3 — Análisis comparativo

Estado: **APROBADA (2026-10-22)**: D1–D5 resueltas y los valores de 10.3 confirmados por
el estudiante. No queda ninguna decisión pendiente que bloquee pruebas ni código; lo que
sigue en 11 son tareas del informe (verificar numeración de CLRS) y comportamientos ya
especificados.
Fecha: 2026-10-18 (creación) · 2026-10-22 (D1 resuelta) · 2026-10-22 (D2–D5 resueltas,
experimento de supuestos especificado) · 2026-10-22 (10.3 confirmada; entorno de medición
en 6.5)
Depende de: Punto 1 (implementado) y `specs/p2-busqueda.md` (secciones 6–8 aprobadas
2026-10-22). Para calcular k\* hacen falta `results/busqueda_{java,python}.csv` del Punto 2.

---

## 1. Requerimiento (literal del enunciado)

> **Comparativos frente a no comparativos.** Investigue cuál es el límite inferior teórico
> para los algoritmos de ordenamiento basados en comparaciones y explique por qué Radix
> Sort y Bucket Sort no están sujetos a él. Compare sus tiempos con los de los algoritmos
> basados en comparaciones: ¿qué supuesto hace cada uno de ellos sobre los datos de
> entrada y qué ocurriría si ese supuesto no se cumpliera (por ejemplo, números de 16
> dígitos para Radix Sort o valores concentrados en un rango pequeño para Bucket Sort)?
>
> **¿Ordenar o no ordenar?** Suponga que tiene un arreglo desordenado de 1.000.000 de
> elementos sobre el cual debe realizar k búsquedas. Con base en sus tiempos medidos,
> determine a partir de qué valor de k resulta más conveniente ordenar el arreglo (con el
> algoritmo que obtuvo el mejor tiempo) y luego usar búsqueda binaria, en lugar de
> realizar k búsquedas lineales sobre el arreglo desordenado. Muestre el cálculo.

Y de las condiciones generales: *"Todo análisis debe apoyarse en sus propias mediciones
(tablas, gráficas o cálculos) y no únicamente en la teoría."*

## 2. Alcance

Entra:

- **Parte A**: tablas del límite inferior y de comparación (desde los CSV de P1) y un
  **experimento de supuestos** (D3): Bucket Sort con distribuciones que rompen o no su
  supuesto (Java y Python, n = 10⁴ y 10⁵) y Radix Sort con valores de 16 dígitos (solo
  Python, n = 10⁴, 10⁵ y 10⁶). El caso de Radix de 16 dígitos en Java se **argumenta**,
  no se mide (4.4.2).
- **Parte B**: cálculo de k\* con los tiempos ya medidos de P1 (ordenamiento) y P2
  (búsqueda, n = 10⁶). No mide nada nuevo.
- El texto de análisis lo redacta el grupo; la spec da los datos y propuestas de texto.

No entra: algoritmos nuevos (no se escribe `RadixSortLong`); cambios a los algoritmos del
P1; regenerar o modificar los datos existentes de `data/`; k\* para n < 10⁶ (D5: como mucho
una frase en el informe, sin tabla).

### 2.1 Archivos, nombres y firmas

| Qué | Python | Java |
|---|---|---|
| Configuración | `config.py`: constantes de 6.1.1 | `Config.java`: réplica de 6.1.1 (solo las que usa Java) |
| Generación de datos | `generate_data.py`: paso nuevo (6.1.3) | — (Java no genera datos) |
| Ruta y lectura de datos | `common/dataio.py`: `supuestos_path`, `load_supuestos` (6.1.5) | `common/DataIO.java`: `supuestosPath`, `readSupuestos` (6.1.5) |
| Escritor CSV | `common/results.py`: `SupuestosCsvWriter` (7.2) | `common/SupuestosCsvWriter.java` (7.2) |
| Benchmark | `python/taller3/bench_supuestos.py` (módulo `taller3.bench_supuestos`) | `java/src/taller3/bench/SupuestosBenchmark.java` |
| Cálculos puros (probables) | `python/taller3/common/compare.py` (3.1) | — |
| Tablas y figuras | `python/taller3/plot_compare.py` (7.3) | — |
| Pruebas | `python/tests/test_compare.py` | `java/src/taller3/tests/SupuestosSelfTest.java` |
| Script de corrida | `run_punto3.sh` (raíz, 7.1) | |

Nada de lo anterior modifica el comportamiento del P1 ni del P2: el escritor CSV del P1
(`CsvResultWriter`) y `SortBenchmark` no se tocan (solo se **reutilizan**
`SortBenchmark.timeOnce` y `SortBenchmark.globalWarmup`, que son `static` de paquete en
`taller3.bench`, y `time_inplace` en Python).

## 3. Datos de entrada de la Parte B y cálculos puros

| Uso | Archivo | Filtro | Columna |
|---|---|---|---|
| Tiempos de ordenamiento, 6 algoritmos | `results/ordenamiento_{java,python}.csv` | `variante = aleatoria`, n ∈ {10³…10⁶} | `promedio_ns`, `desv_estandar_ns`, `estado` |
| t_ord (principal, D2) | ídem | `variante = aleatoria`, `n = 1000000`, `estado = medido`, **mínimo `promedio_ns`** por lenguaje | `promedio_ns`, `desv_estandar_ns` |
| t_ord (sensibilidad, D2) | `results/ordenamiento_python.csv` | `algoritmo = RadixSort`, `variante = aleatoria`, `n = 1000000` | `promedio_ns`, `desv_estandar_ns` |
| t_binaria | `results/busqueda_{java,python}.csv` | `algoritmo = BinarySearch`, `variante = claves`, `n = 1000000` | `promedio_por_busqueda_ns`, `desv_por_busqueda_ns` |
| t_lineal (principal, D1) | ídem | `algoritmo = LinearSearch`, `variante = claves`, `n = 1000000` | `promedio_por_busqueda_ns`, `desv_por_busqueda_ns`, `estado` |
| t_lineal, banda (D1) | ídem | `algoritmo = LinearSearch`, `variante ∈ {centro, final}`, `n = 1000000` | ídem |

Valores **ya medidos** de t_ord (CSV versionados, aleatoria, n = 10⁶):

| Lenguaje | Mejor (principal) | promedio_ns | desv_estandar_ns | Siguientes |
|---|---|---|---|---|
| Java | **RadixSort** | **16.087.758,4** (16,09 ms) | 79.882,0 | DualPivotQuickSort 48,95 ms; MergeSort 69,59 ms; BucketSort 76,86 ms; HeapSort 77,06 ms |
| Python | **BucketSort** | **457.194.941,8** (457,19 ms) | 5.669.578,5 | DualPivotQuickSort 1.065,37 ms; **RadixSort 1.775.541.275,0 (1,78 s; desv 62.373.495,9) ← sensibilidad**; MergeSort 2.445,60 ms; HeapSort 3.601,36 ms |

### 3.1 Funciones puras (`python/taller3/common/compare.py`)

No leen archivos ni miden. Son lo que prueba `test_compare.py`.

| Firma | Contrato |
|---|---|
| `k_star(t_ord: float, t_l: float, t_b: float) -> float \| None` | `t_ord / (t_l - t_b)`; `None` si `t_l <= t_b` |
| `k_min(t_ord: float, t_l: float, t_b: float) -> int \| None` | `floor(k_star) + 1`; `None` si `t_l <= t_b` |
| `k_interval(t_ord, s_ord, t_l, s_l, t_b, s_b) -> tuple[float \| None, float \| None]` | (k_bajo, k_alto) de 5.4; cada extremo `None` si su denominador es ≤ 0 |
| `lower_bound_comparisons(n: int) -> int` | ⌈log₂(n!)⌉ = menor h con 2ʰ ≥ n!; 0 para n ≤ 1. Implementación: `math.ceil(math.lgamma(n + 1) / math.log(2))` para n ≥ 2 |
| `bucket_profile(values: list[int]) -> tuple[int, int, int]` | (cubetas_no_vacias, cubeta_max, desplazamientos) del Bucket Sort **del repo** (k = n, `idx = (x − min)·k // (max − min + 1)`); desplazamientos = Σ por cubeta de los pares (i < j) con `b[i] > b[j]` **estricto** (= inversiones = número exacto de desplazamientos del Insertion estricto). Debe calcularse en O(m log m) por cubeta (conteo de inversiones por mezcla o Fenwick), **no** ejecutando Insertion (en 10⁵ concentrado serían 2,5·10⁸ iteraciones de Python). n = 0 → (0, 0, 0). No modifica `values` |
| `radix_passes(values: list[int]) -> int` | número de iteraciones de `while m // exp > 0` del Radix del repo con `m = máx(values)`, `exp = 1, 10, 100, …` (= cantidad de dígitos decimales de m; 0 si m = 0 o lista vacía) |

## 4. Parte A — Comparativos frente a no comparativos

**Bibliografía (4.ª edición, la que cita el informe del P1):** Cormen, T. H., Leiserson,
C. E., Rivest, R. L. y Stein, C. (2022). *Introduction to Algorithms* (4.ª ed.). MIT
Press. La numeración que sigue (Teorema 8.1, §8.1, §8.3, Lema 8.3, §8.4, ecuación de
lg(n!)) proviene de la 3.ª edición y, hasta donde se sabe, el capítulo 8 conserva su
estructura en la 4.ª; **verificar con el libro** cada número antes de citarlo en el
informe. La ecuación lg(n!) = Θ(n lg n) era la (3.19) en la 3.ª edición; en la 4.ª el
capítulo 3 se reorganizó y su número cambió (posiblemente (3.28): **verificar con el libro**).

### 4.1 Límite inferior Ω(n log n) (árbol de decisión)

Fuente: CLRS 4.ª ed., §8.1 "Lower bounds for sorting", **Teorema 8.1** (*verificar
numeración con el libro*): todo algoritmo de ordenamiento por comparaciones requiere
Ω(n lg n) comparaciones en el peor caso; y lg(n!) = Θ(n lg n) (cap. 3, aproximación de
Stirling; *número de ecuación: verificar con el libro*).

Argumento que debe aparecer en el informe:

1. Un ordenamiento por comparaciones se modela como un árbol de decisión binario: cada
   nodo interno es una comparación `aᵢ ≤ aⱼ`, cada hoja una permutación de salida.
2. Para ser correcto debe poder producir las n! permutaciones → al menos n! hojas
   alcanzables.
3. Un árbol binario de altura h tiene a lo sumo 2ʰ hojas → 2ʰ ≥ n! → h ≥ log₂(n!).
4. Stirling: log₂(n!) = n log₂ n − n log₂ e + ½ log₂(2πn) + O(1/n) = Θ(n log n).
   La altura es el número de comparaciones del peor caso → Ω(n log n).

Valores concretos (verificados: para n ≤ 10⁵ con el entero exacto `(n! − 1).bit_length()`
y con `lgamma`, idénticos; para 10⁶ con `lgamma` y con Stirling, 18.488.884,6):

| n | ⌈log₂(n!)⌉ (mín. comparaciones, peor caso) | n·log₂ n | cociente |
|---|---|---|---|
| 1.000 | 8.530 | 9.966 | 0,856 |
| 10.000 | 118.459 | 132.877 | 0,891 |
| 100.000 | 1.516.705 | 1.660.964 | 0,913 |
| 1.000.000 | 18.488.885 | 19.931.569 | 0,928 |

### 4.2 Por qué Radix y Bucket no están sujetos al límite

El límite solo vale en el **modelo de comparaciones** (la única información que se obtiene
de los datos es el resultado de `aᵢ ≤ aⱼ`). Radix y Bucket usan el **valor** de la clave
como índice de arreglo (dígito → contador; valor normalizado → cubeta), operación que no es
una comparación y extrae más de un bit de información por paso. Bucket sí compara dentro
de cada cubeta (Insertion Sort), pero con cubetas de tamaño esperado O(1).

| Algoritmo | Complejidad | Supuesto sobre los datos | Fuente |
|---|---|---|---|
| Radix Sort (LSD, base b = 10) | Θ(d·(n + b)) | claves enteras con **d dígitos acotado** (aquí d = 8 → 8 pasadas de Counting Sort) | CLRS 4.ª ed. §8.3, Lema 8.3 (*verificar numeración con el libro*) |
| Bucket Sort (k = n cubetas, Insertion por cubeta) | Θ(n) esperado; Θ(n²) peor | valores **distribuidos uniformemente** en [min, max] (aquí `randint` uniforme) | CLRS 4.ª ed. §8.4 (*verificar numeración con el libro*) |

Configuración real implementada (README §6): Bucket con `k = n` e índice
`⌊(x − min)·k / (max − min + 1)⌋`; Insertion Sort con comparación **estricta** `b[j] > key`.

### 4.3 Comparación con mediciones (P1)

Tabla `figures/p3_comparativos.{csv,md}` (7.3): por lenguaje y algoritmo, aleatoria,
n = 10⁶. Permite argumentar con datos: en Java Radix es 3,0× más rápido que el mejor
comparativo (16,09 vs 48,95 ms); en Python **no**: Radix (1,78 s) es más lento que
DualPivot (1,07 s) — el costo constante por operación del intérprete en las 8 pasadas
(≈ 4 recorridos de n cada una) pesa más que el log n que se ahorra. Bucket es el mejor en
Python (0,457 s) y de los peores en Java (boxing de `ArrayList<Integer>`). Estas
observaciones son para orientar; el análisis lo redacta el grupo.

### 4.4 ¿Qué pasa si el supuesto no se cumple? (respaldado por el experimento de 6)

#### 4.4.1 Radix con 16 dígitos — medido en Python

- d pasa de 8 a 16 → el doble de pasadas; por el modelo Θ(d·(n+b)) el tiempo se
  duplicaría. En CPython se espera **algo más que ×2**: los enteros de 8 dígitos
  (< 2³⁰) ocupan un "dígito" interno de 30 bits, los de 16 dígitos (≈ 2⁵³) ocupan dos, y
  `//` y `%` sobre ellos son más lentos. Prueba informal (2026-10-22, Python 3.9.6, no
  son datos del informe): 16 dígitos / 8 dígitos = 2,53 (10⁴), 2,48 (10⁵), 2,37 (10⁶).
- Comparado con n log₂ n: con n = 10⁶, log₂ n ≈ 19,9; 16 pasadas de ≈ 4 recorridos son
  ≈ 64n operaciones elementales frente a ≈ 20n comparaciones de Merge Sort → la ventaja se
  pierde o se invierte. En general, si d crece como log_b(rango) y el rango crece con n,
  Radix es Θ(n log n).
- La implementación Python ya soporta enteros de cualquier tamaño (el número de pasadas
  sale del máximo), así que se mide sin código nuevo de algoritmo.
- Los comparativos del P1 se midieron con 8 dígitos; con 16 dígitos también serían algo
  más lentos en CPython (comparar enteros de dos dígitos internos). La tabla 7.3 los usa
  como referencia con esa advertencia explícita (no se miden comparativos con 16 dígitos).

#### 4.4.2 Radix con 16 dígitos en Java — solo argumentado (texto para el informe)

> En Java el experimento no se puede hacer con nuestra implementación sin escribir otro
> algoritmo. `RadixSort` ordena un `int[]`, y un `int` es un entero de 32 bits con signo
> cuyo máximo es 2³¹ − 1 = 2.147.483.647 (10 dígitos): un número de 16 dígitos (hasta
> 9.999.999.999.999.999) no cabe. Haría falta una versión `RadixSortLong` sobre `long[]`
> (64 bits, máximo 9.223.372.036.854.775.807, 19 dígitos), con `getMax`, `exp` y el
> arreglo auxiliar `output` en `long`; además la lectura de datos (`DataIO.readInts`) y la
> interfaz `SortAlgorithm` (`sort(int[])`) solo manejan `int`, así que también habría que
> duplicarlas. Ese código ya no sería el mismo algoritmo del Punto 1 ni equivalente
> línea a línea al de Python, por eso no lo medimos. Lo que se espera: el número de
> pasadas sube de 8 a 16 y cada pasada sigue siendo Θ(n + 10), así que el tiempo crecería
> ≈ ×2 (≈ 32 ms en n = 10⁶ a partir de los 16,09 ms medidos), algo más por mover el doble
> de bytes (8 por elemento en vez de 4: `arr` y `output` pasan de 4 MB a 8 MB cada uno con
> n = 10⁶). Aun así seguiría cerca o por debajo del mejor comparativo medido en Java
> (Dual-Pivot, 48,95 ms con 8 dígitos). En Python, en cambio, medimos ×≈2,4 y Radix queda
> muy por detrás de los comparativos. (Estimación, no medición.)

#### 4.4.3 Bucket con valores concentrados — medido en Java y Python

Hay que distinguir dos casos, por cómo está implementado (normalización min–max e
Insertion estricto). Conteos **exactos** sobre los archivos definidos en 6.1 (calculados
ejecutando el Bucket del repo instrumentado; idénticos con Python 3.9.6 y 3.14.6):

| Distribución | n | cubetas no vacías | cubeta más grande | desplazamientos de Insertion |
|---|---|---|---|---|
| `uniforme` (= `aleatoria_n.txt`) | 10.000 | 6.331 | 7 | 2.537 |
| `uniforme` | 100.000 | 63.394 | 7 | 24.756 |
| `rango_pequeno` | 10.000 | 1.000 | 22 | **0** |
| `rango_pequeno` | 100.000 | 1.000 | 131 | **0** |
| `concentrado_extremos` | 10.000 | 12 | 1.045 | **2.466.064** (≈ 972× uniforme) |
| `concentrado_extremos` | 100.000 | 12 | 10.184 | **249.837.990** (≈ 10.092× uniforme) |

- *Rango pequeño sin valores extremos*: la normalización min–max reparte el rango sobre
  las k cubetas; como k = n ≥ 1.000 = tamaño del rango, cada valor distinto cae en su
  propia cubeta y los repetidos caen juntos; Insertion con `>` estricto no desplaza
  iguales → 0 desplazamientos, ≈ O(n). Con **esta** implementación el ejemplo del
  enunciado no degrada (degradaría con cubetas fijas sobre [10⁷, 10⁸), donde todo caería
  en ≈ 1 cubeta).
- *Concentrado con extremos*: el mínimo y el máximo fijan cubetas de ancho
  w = 9·10⁷ / n (9.000 con n = 10⁴; 900 con n = 10⁵); los n − 2 valores restantes caen en
  exactamente **10 cubetas** → m ≈ n/10 por cubeta → desplazamientos ≈ 10 · m²/4 = n²/40
  (2,5·10⁶ y 2,5·10⁸; exactos arriba, razón 101,3 ≈ 100 = (10⁵/10⁴)²). Es el peor caso
  Θ(n²): el tiempo de Bucket crece ×≈100 al multiplicar n por 10.
- Es una **entrada adversaria** construida a propósito contra esta implementación
  (confirmada por el estudiante, 2026-10-22): para cada n el cúmulo cubre siempre
  exactamente 10 cubetas, más el mínimo y el máximo del rango. **Admite valores
  repetidos** (opción A del estudiante).

**Texto propuesto para el informe (repetidos en el cúmulo):**

> La distribución concentrada admite valores repetidos. Con n = 10⁵ cada cubeta del
> cúmulo abarca 900 valores posibles, así que solo ≈ 1/900 ≈ 0,1 % de los pares de una
> cubeta son iguales; con n = 10⁴ cada cubeta abarca 9.000 valores y la fracción es
> ≈ 1/9.000 ≈ 0,01 %. Si una cubeta recibe m valores en orden aleatorio, los
> desplazamientos esperados del Insertion Sort son ≈ (m²/4)(1 − 1/w), con w el ancho de la
> cubeta, es decir ≈ m²/4. Los repetidos no se desplazan entre sí porque el Insertion
> compara con `>` estricto: el costo lo producen los pares de valores distintos, que son
> casi todos. Medido sobre nuestros archivos: pares iguales dentro de una misma cubeta =
> 555.297 de 499.988.104 (0,111 %) con n = 10⁵ y 577 de 4.998.770 (0,012 %) con n = 10⁴;
> desplazamientos exactos 249.837.990 y 2.466.064, frente a Σ m(m−1)/4·(1 − 1/w) =
> 249.716.281 y 2.499.107 (diferencias de +0,05 % y −1,3 %, ruido del muestreo).
>
> No usamos valores distintos porque con n = 10⁵ el tramo de 10 cubetas solo contiene
> 10 · 900 = 9.000 enteros, menos que los n − 2 = 99.998 valores que hay que colocar (con
> 10⁴ sí cabrían, 90.000 enteros, pero entonces los dos tamaños no se generarían igual).
> Tampoco medimos n = 10³: allí se esperan solo ≈ n²/40 = 25.000 desplazamientos y, como
> en el Punto 1, los costos fijos (crear las cubetas, recorrerlas, concatenar) dominan el
> tiempo y no dejan ver el crecimiento cuadrático.

(Verificado por ejecución el 2026-10-22, regenerando los archivos con 6.1.3 en un
directorio temporal: SHA-256 de 6.1.3 idénticos; 12 cubetas no vacías; cubeta máxima
1.045 y 10.184; desplazamientos 2.466.064 y 249.837.990, los de la tabla.)

## 5. Parte B — ¿Ordenar o no ordenar?

### 5.1 Modelo y fórmula

- Sin ordenar: costo(k) = k · t_L.
- Ordenar una vez y buscar con binaria: costo(k) = t_ord + k · t_B.
- Conviene ordenar cuando k · t_L > t_ord + k · t_B ⇔ **k > t_ord / (t_L − t_B) = k\***
  (válido si t_L > t_B; si t_L ≤ t_B nunca conviene).
- Como k es entero y en k = k\* hay empate, se reporta
  **k_min = ⌊t_ord / (t_L − t_B)⌋ + 1** (el menor k en que ordenar es *estrictamente* mejor).
- Tiempos por lenguaje (no se mezclan lenguajes), todos con n = 10⁶: t_ord de la sección 3;
  t_B = BinarySearch, `claves`, por búsqueda; t_L = LinearSearch, `claves`, por búsqueda
  (D1, 5.2).
- Supuestos a declarar en el informe: el arreglo se ordena in situ (no se necesita
  conservar el orden original; si se necesitara, habría que sumar una copia); no se cuenta
  la lectura de datos; los tiempos son promedios de 5 repeticiones.

### 5.2 La t_L: qué se usa y por qué (D1, resuelta 2026-10-22)

**Decisión.** t_L = tiempo promedio por búsqueda de `LinearSearch` en la variante
`claves` del Punto 2, n = 10⁶: las 1.000 claves de `claves_busqueda.txt` (500 presentes,
500 ausentes) sobre `ascendente_1000000.txt`. No se mide nada nuevo. Trabajo de esa
pasada (verificado por ejecución, p2 6.2): 748.440.213 comparaciones ⇒ ≈ 748.440 por
búsqueda ≈ **0,75·n** (presentes ≈ n/2 en promedio: posición media 0,497·n; ausentes n).

**Por qué el arreglo ordenado sirve de sustituto del desordenado.** La pregunta habla de
búsquedas lineales sobre el arreglo **desordenado**; el Punto 2 midió la lineal sobre el
**ascendente**. La sustitución es válida por tres razones:

1. **La lineal no depende del orden del arreglo, sino de la posición de la clave.** La
   implementación de GfG (p2 3.1) no aprovecha el orden (no se detiene en `arr[i] > x`):
   hace exactamente `i + 1` comparaciones si encuentra la clave en el índice `i`, y `n` si
   no está. El patrón de acceso a memoria es el mismo recorrido secuencial en ambos
   arreglos, así que el costo por comparación también es el mismo.
2. **En el ordenado, las presentes quedan repartidas uniformemente.** Sus valores son
   aleatorios uniformes en [10⁷, 10⁸), así que su posición en el ascendente es uniforme en
   [0, n): verificado, posición media 0,497·n, mínima 2.289, máxima 998.371. Eso es lo
   mismo que se espera de una clave presente cualquiera en un arreglo desordenado
   (posición uniforme). Las ausentes cuestan n en ambos arreglos.
3. **Medir en el desordenado con este archivo de claves sesgaría t_L.** Las presentes
   salen de `aleatoria_1000.txt`, que es el prefijo de `aleatoria_1000000.txt`: en el
   desordenado **todas están en los índices 0…999** (p2 6.1.4). Una lineal sobre él con
   estas claves haría 500.256.719 comparaciones por pasada (≈ **0,50·n** por búsqueda,
   calculado con los datos versionados) en lugar de ≈ 0,75·n: las presentes costarían
   casi nada y t_L quedaría ≈ ⅔ del valor representativo, lo que **subestimaría** el
   costo de no ordenar y **sobrestimaría** k\*.

**Texto propuesto para el informe** (el grupo puede ajustarlo):

> Para t_L usamos el tiempo promedio por búsqueda de la búsqueda lineal medido en el
> Punto 2 con n = 1.000.000 (500 claves presentes y 500 ausentes), aunque esa medición se
> hizo sobre el arreglo ordenado y la pregunta plantea un arreglo desordenado. La búsqueda
> lineal no usa el orden: recorre el arreglo desde el inicio y hace i + 1 comparaciones si
> la clave está en la posición i, o n si no está. Por eso su costo depende solo de la
> posición de la clave, no de si el arreglo está ordenado. Como los valores de las claves
> presentes son aleatorios, en el arreglo ordenado sus posiciones quedan repartidas de
> manera uniforme (posición media 0,497·n), igual que en un arreglo desordenado típico, y
> el costo medio resulta ≈ 0,75·n comparaciones por búsqueda. No medimos directamente
> sobre nuestro arreglo desordenado porque las 500 claves presentes se tomaron de los
> primeros 1.000 elementos de la secuencia aleatoria (para que estuvieran presentes en los
> cuatro tamaños): allí todas aparecen en las primeras 1.000 posiciones y el costo medio
> bajaría a ≈ 0,50·n, un valor que no representa una búsqueda típica.

**Banda de sensibilidad de t_L (sin mediciones nuevas):**

| Escenario (`fuente_t_lineal`) | t_L tomada de (Punto 2, LinearSearch, n = 10⁶) | Trabajo por búsqueda | Interpretación |
|---|---|---|---|
| `claves` (principal) | `variante = claves` | ≈ 0,75·n | mezcla 500/500 |
| `solo_presentes` | `variante = centro` | n/2 = 500.000 | todas encuentran la clave (posición media n/2) |
| `solo_ausentes` | `variante = final` | n = 1.000.000 | ninguna encuentra la clave (recorre todo) |

`final` equivale a una ausente (n comparaciones). Se espera
k\*(`solo_ausentes`) < k\*(`claves`) < k\*(`solo_presentes`) (8). Con el modelo de
comparaciones, t_L(`solo_presentes`) ≈ ⅔·t_L(`claves`) y t_L(`solo_ausentes`) ≈ 4/3·t_L(`claves`).

**Estado: APROBADA por el estudiante (2026-10-22) como APROXIMACIÓN**, y así debe
declararse en el informe y en la tabla: `solo_presentes` se aproxima con la medición
`centro` (una sola clave repetida 1.000 veces en el índice 499.999, no 1.000 claves
distintas con posición media n/2) y `solo_ausentes` con `final` (índice 999.999: n
comparaciones, igual que una ausente, pero encontrando la clave). No son mediciones de
"solo presentes" ni "solo ausentes" reales; la banda indica el orden de magnitud del
efecto de la mezcla de claves, no un intervalo de confianza.

**Regla (aprobada):** si el k\* principal (`claves`) **no** queda entre los extremos de
la banda (k\*(`solo_ausentes`) ≤ k\*(`claves`) ≤ k\*(`solo_presentes`)), `plot_compare.py`
debe **avisar** de forma visible (mensaje en consola con los tres k\* y la columna
`aviso` de la tabla — o equivalente — marcada) y el resultado **se revisa antes de
escribir el informe**: no se publica la tabla ni la conclusión de la Parte B sin esa
revisión (causas probables: ruido en la lineal, JIT, o una medición `estimado`).

### 5.3 El algoritmo de ordenamiento (D2, resuelta 2026-10-22)

**Decisión (a).** t_ord = el mejor de **cada lenguaje** (lectura literal): Java
RadixSort (16.087.758,4 ns), Python BucketSort (457.194.941,8 ns), aleatoria, n = 10⁶.

**Más una fila de sensibilidad**: k\* en Python usando **RadixSort** (1.775.541.275,0 ns)
en vez de Bucket, con t_L = `claves`. Como t_B y t_L son las mismas, el cociente es
exactamente la razón de los t_ord:

k\*(Radix) / k\*(Bucket) = 1.775.541.275,0 / 457.194.941,8 = **3,8836**

**Frase propuesta para el informe:** "Si en Python ordenáramos con Radix Sort (1,78 s)
en lugar de Bucket Sort (0,457 s), k\* sería 3,88 veces mayor (de X a Y búsquedas): la
conveniencia de ordenar depende en proporción directa del algoritmo de ordenamiento
elegido." (X e Y salen de `p3_k_estrella.csv`.)

### 5.4 Ejemplo numérico con los valores ya medidos (t_L aún desconocida)

t_L y t_B salen del Punto 2; aquí se usan valores **hipotéticos** solo para mostrar el
cálculo (t_B = 100 ns hipotético). Java: k\* = 16.087.758,4 / (t_L − t_B).

| t_L hipotética | t_L − t_B | k\* | k_min | (con BucketSort Java, t_ord = 76.855.674,8 ns) |
|---|---|---|---|---|
| 0,1 ms = 100.000 ns | 99.900 | 161,04 | **162** | 769,33 → 770 |
| 0,3 ms | 299.900 | 53,64 | **54** | 256,27 → 257 |
| 0,5 ms | 499.900 | 32,18 | **33** | 153,74 → 154 |
| 1 ms = 1.000.000 ns | 999.900 | 16,09 | **17** | 76,86 → 77 |

Comprobación de la fila de 1 ms: k = 16 → sin ordenar 16 · 1.000.000 = 16.000.000 ns;
ordenando 16.087.758,4 + 16 · 100 = 16.089.358,4 ns → todavía conviene no ordenar.
k = 17 → 17.000.000 vs 16.089.458,4 → conviene ordenar. ✓

Python, con t_L hipotética de 7 ms y t_B de 5 µs:

- Principal (Bucket): 457.194.941,8 / 6.995.000 = 65,36 → k_min = 66.
- Sensibilidad (Radix): 1.775.541.275,0 / 6.995.000 = 253,83 → k_min = **254**.
  Comprobación: k = 253 → 253 · 7·10⁶ = 1.771.000.000 < 1.775.541.275 + 253 · 5.000 =
  1.776.806.275 → aún no conviene; k = 254 → 1.778.000.000 > 1.776.811.275 → conviene. ✓
  (65,36 · 3,8836 = 253,83 ✓.)

Observaciones para el análisis: como t_B ≪ t_L, k\* ≈ t_ord / t_L; y como t_ord ∝ n
(Radix) y t_L ∝ n, k\* es casi independiente de n para un ordenamiento lineal, mientras
que con un ordenamiento n log n crece como log n (D5: esto va, como mucho, en una frase
del informe; no se calcula k\* para n < 10⁶).

### 5.5 Incertidumbre

Se reporta un intervalo con ±1 desviación estándar:
k\*_bajo = (t_ord − s_ord) / ((t_L + s_L) − (t_B − s_B)),
k\*_alto = (t_ord + s_ord) / ((t_L − s_L) − (t_B + s_B)).
s_ord = `desv_estandar_ns` del P1; s_L, s_B = `desv_por_busqueda_ns` del P2.

### 5.6 Casos de prueba de las funciones puras (resueltos a mano)

**k\*** (`k_star`, `k_min`):

| t_ord | t_L | t_B | k\* | k_min | Nota |
|---|---|---|---|---|---|
| 16.087.758,4 | 1.000.000 | 100 | 16,0894 | 17 | verificado en 5.4 |
| 1.000 | 110 | 10 | 10 (exacto) | **11** | en k = 10 hay empate: 1.100 = 1.000 + 100 |
| 1.000 | 10 | 10 | `None` | `None` | t_L = t_B: nunca conviene ordenar |
| 1.000 | 5 | 10 | `None` | `None` | t_L < t_B |
| 457.194.941,8 | 7.000.000 | 5.000 | 65,36 | 66 | 65·7·10⁶ = 455·10⁶ < 457.194.941,8 + 325.000; 66·7·10⁶ = 462·10⁶ > 457.524.941,8 ✓ |
| 1.775.541.275,0 | 7.000.000 | 5.000 | 253,8301 | 254 | sensibilidad, verificado en 5.4 |
| 0 | 10 | 5 | 0 | 1 | ordenar no cuesta: conviene desde k = 1 |

**`k_interval`**: t_ord = 1.000, s_ord = 100, t_L = 110, s_L = 10, t_B = 10, s_B = 0 →
k_bajo = 900 / (120 − 10) = 8,1818…; k_alto = 1.100 / (100 − 10) = 12,2222…. Con s_L = 100
→ k_alto: denominador (110 − 100) − 10 = 0 → `None`.

**`lower_bound_comparisons`**: n = 0 → 0; 1 → 0; 2 → 1; 3 → 3 (log₂ 6 = 2,585); 4 → 5
(log₂ 24 = 4,585); 5 → 7 (log₂ 120 = 6,907); 1.000 → 8.530; 10⁶ → 18.488.885.

**`bucket_profile`** (traza con la fórmula del repo):

| values | min, max, rango, k | idx de cada valor | cubetas | resultado |
|---|---|---|---|---|
| [10, 19, 13, 11, 13, 12] | 10, 19, 10, 6 | (x−10)·6//10: 10→0, 19→5, 13→1, 11→0, 13→1, 12→1 | b0 = [10, 11], b1 = [13, 13, 12], b5 = [19] | **(3, 3, 2)**: en b1, 13 > 12 dos veces; 13 vs 13 no cuenta (estricto) |
| [1, 100, 60, 59, 58, 57] | 1, 100, 100, 6 | (x−1)·6//100: 1→0, 100→5, 60→3, 59→3, 58→3, 57→3 | b3 = [60, 59, 58, 57] (invertida) | **(3, 4, 6)** = 4·3/2: peor caso en miniatura |
| [5, 5, 5, 5] | 5, 5, 1, 4 | todos → 0 | b0 = [5, 5, 5, 5] | **(1, 4, 0)** |
| [3, 1] | 1, 3, 3, 2 | 3→1, 1→0 | b0 = [1], b1 = [3] | **(2, 1, 0)** |
| [7] | — | — | — | **(1, 1, 0)** |
| [] | — | — | — | **(0, 0, 0)** |

Además, sobre los archivos de 6.1 (tras comprobar su SHA-256) debe dar exactamente la
tabla de 4.4.3.

**`radix_passes`**: [] → 0; [0] → 0; [5] → 1; [10] → 2; [99.999.999] → 8;
[10¹⁵] → 16; [10¹⁶ − 1] → 16; `aleatoria_10000.txt` → 8; `digitos16_*` → 16.

## 6. Protocolo del experimento de supuestos (D3, resuelta 2026-10-22)

### 6.1 Datos

Generados **una sola vez** por `generate_data.py`, semilla fija, en `data/p3/`, registrados
en `manifest.json` sin cambiar ninguna entrada existente.

#### 6.1.1 Constantes (confirmadas por el estudiante 2026-10-22, ver 10.3)

| Python (`config.py`) | Java (`Config.java`) | Valor |
|---|---|---|
| `SUPUESTOS_SEED` | — | `20261017` (independiente de `SEED` = 20261015 y `SEARCH_KEYS_SEED` = 20261016) |
| `SUPUESTOS_SUBDIR` | `public static final String SUPUESTOS_SUBDIR` | `"p3"` |
| `SUPUESTOS_SIZES` | `public static final int[] SUPUESTOS_SIZES` | `(10_000, 100_000)` (Bucket) |
| `DIGITOS16_SIZES` | — | `(10_000, 100_000, 1_000_000)` (Radix, solo Python) |
| `BUCKET_DISTRIBUTIONS` | `public static final String[] BUCKET_DISTRIBUTIONS` | `("uniforme", "rango_pequeno", "concentrado_extremos")`, en ese orden |
| `RADIX_DISTRIBUTIONS` | — | `("uniforme", "digitos16")`, en ese orden |
| `RANGO_PEQUENO` | — | `(10_000_000, 10_000_999)` (1.000 valores) |
| `CONCENTRADO_CUBETAS` | — | `10` |
| `DIGITOS16_RANGE` | — | `(10**15, 10**16 - 1)` |

`uniforme` **no tiene archivo nuevo**: es `data/aleatoria_{n}.txt` del P1 (prefijos de la
secuencia de 10⁶, uniformes en [10⁷, 10⁸ − 1]).

#### 6.1.2 Definición de las distribuciones

- `rango_pequeno` (n = 10⁴, 10⁵): n valores `randint(10.000.000, 10.000.999)` (con
  reemplazo). Idea del enunciado ("valores concentrados en un rango pequeño"); sin
  extremos.
- `concentrado_extremos` (n = 10⁴, 10⁵): n − 2 valores `randint(lo, hi)` + `MIN_VALUE`
  (10.000.000) + `MAX_VALUE` (99.999.999), barajados. Con w = (MAX − MIN + 1) / n
  (exacto: 9.000 y 900), lo = MIN + (n/2)·w = **55.000.000** para ambos n y
  hi = lo + `CONCENTRADO_CUBETAS`·w − 1 (**55.089.999** con n = 10⁴; **55.008.999** con
  n = 10⁵). Como el mínimo y el máximo del arreglo son exactamente MIN y MAX, el rango
  de la normalización es 9·10⁷ y el cúmulo cae en **exactamente 10 cubetas**
  (índices n/2 … n/2 + 9) para cualquier n que divida a 9·10⁷. Ajuste respecto a la
  propuesta anterior (cúmulo fijo [50.000.000, 50.009.999]): con un cúmulo de ancho fijo
  el número de cubetas ocupadas crece con n y el costo crece solo ≈ linealmente
  (≈ 1 cubeta con 10⁴, ≈ 11 con 10⁵); alineándolo a 10 cubetas se conserva la idea
  ("casi todo en pocas cubetas, porque los extremos estiran el rango") y se obtiene el
  Θ(n²) limpio, ×100 de 10⁴ a 10⁵. Es una **entrada adversaria** y **admite valores
  repetidos** (`randint` con reemplazo; 9.443 y 9.002 distintos); por qué repetidos y no
  distintos, y por qué no n = 10³: 4.4.3.
- `digitos16` (n = 10⁴, 10⁵, 10⁶, solo Python): una secuencia de 10⁶ valores
  `randint(10¹⁵, 10¹⁶ − 1)`; cada n es su **prefijo** (anidados, como en el P1).

#### 6.1.3 Algoritmo de generación (normativo; el orden de las llamadas al RNG importa)

```
rng = random.Random(SUPUESTOS_SEED)                       # 20261017
for n in SUPUESTOS_SIZES:                                  # 10_000, luego 100_000
    vals = [rng.randint(RANGO_PEQUENO[0], RANGO_PEQUENO[1]) for _ in range(n)]
    write_ints(data/p3/rango_pequeno_{n}.txt, vals)
    total = MAX_VALUE - MIN_VALUE + 1                      # 90_000_000
    assert total % n == 0
    w = total // n
    lo = MIN_VALUE + (n // 2) * w
    hi = lo + CONCENTRADO_CUBETAS * w - 1
    vals = [rng.randint(lo, hi) for _ in range(n - 2)] + [MIN_VALUE, MAX_VALUE]
    rng.shuffle(vals)
    write_ints(data/p3/concentrado_extremos_{n}.txt, vals)
big = [rng.randint(DIGITOS16_RANGE[0], DIGITOS16_RANGE[1]) for _ in range(max(DIGITOS16_SIZES))]
for n in DIGITOS16_SIZES:
    write_ints(data/p3/digitos16_{n}.txt, big[:n])
```

Resultado verificado por ejecución (2026-10-22) con Python **3.9.6** y **3.14.6**,
idéntico en ambos:

| Archivo (`data/p3/`) | SHA-256 | mín / máx | distintos | primeros 3 |
|---|---|---|---|---|
| `rango_pequeno_10000.txt` | `003a0b993de857ec96c4905b93e6e57bc1c24fd0ea711ce506fc1a3a163fcc76` | 10.000.000 / 10.000.999 | 1.000 | — |
| `concentrado_extremos_10000.txt` | `98faca8f71baf19fd0a9c38e92dd4bfa69b37f8c2cd2fb6c221a6dc074035fce` | 10.000.000 / 99.999.999 | 9.443 | 55.010.207, 55.042.783, 55.073.867 |
| `rango_pequeno_100000.txt` | `769ed52b6fa6c50f04e40cbc33587aea8f53ca1331162a9549a7620b1c5db22a` | 10.000.000 / 10.000.999 | 1.000 | — |
| `concentrado_extremos_100000.txt` | `6c229b3698df7ac7e1e7acf9fd2f7498692228070d1a311b2ca7e1f3cd77faa9` | 10.000.000 / 99.999.999 | 9.002 | 55.004.244, 55.001.577, 55.004.382 |
| `digitos16_10000.txt` | `e3070fb38fcd24158fc39f3df21321553c82798cfb88bd17dae04236691dc49b` | 1.000.155.328.241.689 / 9.999.529.235.286.674 | 10.000 | 6.589.395.405.209.567, 3.818.904.597.604.050, 1.815.028.165.842.779 |
| `digitos16_100000.txt` | `498749d81d819d233cfc59f743333278ea46470f79a0f870bb2179cba365e510` | 1.000.030.654.373.518 / 9.999.960.352.334.845 | 100.000 | ídem |
| `digitos16_1000000.txt` | `211b340833ed98ddb22c5e786a746d08313bff08fa3d571a016b8f0e8cae1317` | 1.000.005.417.451.910 / 9.999.994.015.984.721 | 1.000.000 | ídem |

Tamaño en disco: ≈ 1,0 MB (`rango_pequeno` + `concentrado_extremos`) + ≈ 18,9 MB
(`digitos16`, 17 bytes por línea) ≈ **20 MB** nuevos versionados (hoy `data/` ocupa 29 MB).

Si `generate_data.py` produce otro SHA-256, la implementación no sigue este pseudocódigo.

#### 6.1.4 Reglas para `generate_data.py` (mismas que P2 6.1.5)

- Flujo de `main()`: (1) datos del P1 igual que hoy; (2) claves del P2; (3) **nuevo**:
  archivos del P3. Si alguno de los 7 archivos de `data/p3/` no existe (o hay `--force`),
  se generan **los 7** con 6.1.3; si existen, se comprueba cada SHA-256 contra el
  manifiesto y se informa (falla si no coincide).
- `manifest.json` se **actualiza**, no se reescribe: todas las entradas y campos
  existentes quedan byte a byte con el mismo valor. Se agregan 7 entradas en
  `archivos` con clave = ruta relativa a `data/` (`"p3/rango_pequeno_10000.txt"`, …):

  ```json
  "p3/concentrado_extremos_100000.txt": {
    "n": 100000,
    "variante": "supuestos",
    "distribucion": "concentrado_extremos",
    "sha256": "6c229b3698df7ac7e1e7acf9fd2f7498692228070d1a311b2ca7e1f3cd77faa9",
    "semilla": 20261017,
    "parametros": "n-2 randint(55000000, 55008999) + 10000000 + 99999999, rng.shuffle",
    "min": 10000000,
    "max": 99999999,
    "valores_distintos": 9002,
    "python": "<sys.version de la corrida>",
    "creado_utc": "<fecha de la corrida>"
  }
  ```

  `rango_pequeno`: `"parametros": "randint(10000000, 10000999)"`; `digitos16`:
  `"parametros": "randint(10**15, 10**16-1); prefijo de la secuencia de 1000000"`.
- `--force` regenera todo; con las semillas fijas el resultado es idéntico.
- Prueba de no regresión: tras correr el generador, `git diff data/` solo muestra los 7
  archivos nuevos de `data/p3/` y las 7 entradas nuevas del manifiesto.

#### 6.1.5 Lectura (firmas exactas)

| | Python (`common/dataio.py`) | Java (`common/DataIO.java`) |
|---|---|---|
| Ruta | `supuestos_path(distribucion: str, n: int, data_dir: Path = config.DATA_DIR) -> Path` | `public static Path supuestosPath(Path dataDir, String distribucion, int n)` |
| Mapeo | `uniforme` → `data_dir / f"aleatoria_{n}.txt"`; `rango_pequeno`, `concentrado_extremos`, `digitos16` → `data_dir / "p3" / f"{distribucion}_{n}.txt"`; otro nombre → `ValueError` | ídem; `digitos16` → `IllegalArgumentException` ("no cabe en int; solo Python, ver spec P3 4.4.2"); otro nombre → `IllegalArgumentException` |
| Lectura | `load_supuestos(distribucion: str, n: int, data_dir: Path = config.DATA_DIR) -> list[int]` = `read_ints(path, n, check_range=(distribucion != "digitos16"))` | `public static int[] readSupuestos(Path dataDir, String distribucion, int n) throws IOException` = `readInts(supuestosPath(...), n)` (valida rango de 8 dígitos) |

No comprueban SHA-256 (eso lo hacen el generador y las pruebas).

### 6.2 Casos medidos

Orden de ejecución: n ascendente; dentro de cada n, algoritmo (BucketSort, luego
RadixSort); dentro de cada algoritmo, distribuciones en el orden de 6.1.1.

| Lenguaje | Algoritmo | Distribuciones | n | Filas |
|---|---|---|---|---|
| Java | BucketSort | `uniforme`, `rango_pequeno`, `concentrado_extremos` | 10⁴, 10⁵ | 6 |
| Python | BucketSort | ídem | 10⁴, 10⁵ | 6 |
| Python | RadixSort | `uniforme`, `digitos16` | 10⁴, 10⁵, 10⁶ | 6 |

- **Por qué Radix 16 dígitos hasta 10⁶** (confirmado 2026-10-22; `digitos16_{10⁴,10⁵,10⁶}`
  versionados, ≈ 19 MB): (1) es el n de la
  pregunta "¿ordenar o no ordenar?" y de la tabla 4.3, así que se compara directamente
  con los comparativos del P1 en 10⁶ (DualPivot 1,07 s, Merge 2,45 s, Heap 3,60 s) y con
  Radix 8 dígitos; (2) es barato: ≈ 5,2 s por repetición (≈ 26 s las 5), muy por debajo de
  300 s; (3) con tres tamaños se ve que la razón 16/8 dígitos es ≈ constante en n (Θ(d·n)).
  No se mide más allá de 10⁶ porque el enunciado no usa tamaños mayores.
- `RadixSort / uniforme` se vuelve a medir en la misma corrida (no se reutiliza el valor
  del P1) para que la razón 16/8 dígitos compare condiciones idénticas; lo mismo para
  `BucketSort / uniforme`. 8 comprueba que coinciden aproximadamente con el P1.
- Java no mide Radix (4.4.2).

### 6.3 Región medida, repeticiones, calentamiento, gc (idéntico al P1)

- Por cada caso: cargar el arreglo (fuera del tiempo) y calcular la referencia ordenada
  **una vez** fuera del tiempo con una implementación independiente: Python `sorted(base)`,
  Java `int[] expected = base.clone(); Arrays.sort(expected);`.
- 5 repeticiones (`REPETITIONS`); cada una sobre una copia nueva, midiendo solo el
  algoritmo y verificando contra la referencia fuera del tiempo:
  Python `time_inplace(spec.func, base)` (copia → `gc.collect()` → `gc.disable()` →
  `perf_counter_ns` → algoritmo → `perf_counter_ns` → `gc.enable()`), luego
  `work == expected`; Java `SortBenchmark.timeOnce(algoritmo, base, expected)`
  (`Arrays.copyOf` → `System.gc()` → `nanoTime` → sort → `nanoTime` → `Arrays.equals`).
- Estadístico: **promedio y desviación estándar muestral (n − 1)**, como el P1 (`stats` /
  `Stats`). Tiempos en ns enteros en el CSV.
- Java: calentamiento global `SortBenchmark.globalWarmup([BucketSort], dataDir)`
  (10 rondas sobre `aleatoria_10000`) + calentamiento por caso como el P1
  (`CASE_WARMUP_TARGET_SECONDS = 0,25 s` o `CASE_WARMUP_MAX_RUNS = 20`, mínimo 1, no
  registrados; se omite si la predicción supera `CASE_WARMUP_SKIP_ABOVE_SECONDS`).
  JVM `-Xms2g -Xmx2g`, sin cambiar `-Xss`. Python: sin calentamiento (CPython sin JIT).

### 6.4 Límite de 5 minutos y estimación (regla del P1)

- Complejidad para predecir/estimar (`supuestos_growth(algoritmo, distribucion)` en
  Python; `SupuestosBenchmark.growth(String, String)` en Java; otro par → error):

  | Algoritmo | Distribución | Growth |
  |---|---|---|
  | BucketSort | `uniforme`, `rango_pequeno` | `N` |
  | BucketSort | `concentrado_extremos` | `N2` |
  | RadixSort | `uniforme`, `digitos16` | `N` |

- Antes de cada caso con un n medido previamente para el mismo (algoritmo, distribución)
  se predice t(n_prev)·f(n)/f(n_prev); si supera 300 s → no se ejecuta, `estado =
  estimado` con `causa` y `base_estimacion` en el formato del P1 (`describe`). Si una
  repetición supera el límite, se detienen las restantes (nota en `causa`).
  `RecursionError`/`StackOverflowError` no aplican (algoritmos iterativos).
- Expectativa (pruebas informales del 2026-10-22, esta máquina; **no** son datos del
  informe): nada se acerca al límite. Caso más caro: Bucket `concentrado_extremos`
  n = 10⁵ en Python ≈ 12,9 s por repetición (predicción desde 10⁴: 0,121 s × 100 =
  12,1 s). Solo superaría 300 s en una máquina ≈ 23× más lenta.

| Caso (tiempo por repetición) | Java 25 | Python 3.9.6 |
|---|---|---|
| Bucket `uniforme` 10⁴ / 10⁵ | 0,29 ms / 3,0 ms | 3,15 ms / 34,4 ms |
| Bucket `rango_pequeno` 10⁴ / 10⁵ | 0,15 ms / 1,6 ms | 2,9 ms / 29,9 ms |
| Bucket `concentrado_extremos` 10⁴ / 10⁵ | 2,1 ms / **218 ms** | 121 ms / **12,9 s** |
| Radix `uniforme` 10⁴ / 10⁵ / 10⁶ | — | 12,5 ms / 133 ms / 2,20 s |
| Radix `digitos16` 10⁴ / 10⁵ / 10⁶ | — | 31,7 ms / 331 ms / **5,20 s** |

Costo por desplazamiento implícito: Python ≈ 50 ns, Java ≈ 0,87 ns (≈ 59×).
(Radix `uniforme` 10⁶ dio 2,20 s frente a 1,78 s en el P1: la máquina estaba ≈ 1,2× más
cargada; por eso la corrida oficial debe hacerse en las mismas condiciones del P1, 6.5.)
Estas pruebas informales se hicieron en la máquina de desarrollo; no entran al informe.

**Costo estimado de la corrida oficial:** Java < 15 s en total (calentamientos +
5 × ≈ 0,23 s + carga). Python ≈ 2 min (Bucket ≈ 5 × 13,1 s ≈ 66 s; Radix ≈ 5 × 7,9 s ≈
40 s; carga, `sorted` y verificación ≈ 10 s). Generación de datos: segundos (una vez).

### 6.5 Entorno de medición (regla, 2026-10-22)

- Las mediciones **oficiales** del P3 (las que entran al informe) se corren en el **Mac
  del P1** (`~/Downloads/taller3`, con `.venv` de Python 3.9.6 + matplotlib), para que
  sean comparables con `results/ordenamiento_*.csv` y `results/busqueda_*.csv`.
- Antes de medir se verifica el entorno contra los **valores fijos** del Mac del P1
  (corrección B de la auditoría del P2, 2026-10-23; antes se leían de
  `results/entorno_{java,python}.json`, que una corrida de `run_punto1.sh` podía
  reescribir): macOS 26.6.x en arm64, 10 núcleos, Java 21.0.9, Python 3.9.6. Si algo no
  coincide, la corrida **aborta** con un mensaje que diga qué difiere (`scripts/entorno_medicion.sh`).
- En la máquina de desarrollo solo se corren pruebas de corrección (y corridas parciales
  con `--out results/prueba_*.csv`); **nada** de lo medido allí entra al informe.
- `run_punto3.sh` usa `.venv/bin/python` (no `python3` del sistema) y **reutiliza** el
  helper de verificación de entorno que crea el implementador del P2 (nombre y ruta a
  definir por él, p. ej. `scripts/check_env.sh`); el P3 no escribe uno propio.

## 7. Salidas

### 7.1 Script `run_punto3.sh` (raíz, mismo estilo que `run_punto1.sh`, `set -euo pipefail`)

Python = `.venv/bin/python` de la raíz (6.5), escrito abajo como `$PY`.

0. Verificación de entorno con el helper del P2 (`source scripts/entorno_medicion.sh`,
   `require_venv`, `require_matplotlib`, `check_measurement_env`); aborta si no coincide
   con los valores fijos de 6.5.
1. `(cd python && $PY -m taller3.generate_data)` — genera `data/p3/` si falta.
2. `rm -rf java/out && javac -encoding UTF-8 -d java/out $(find java/src -name "*.java")`
3. `java -cp java/out taller3.tests.SupuestosSelfTest` y
   `(cd python && $PY -m unittest tests.test_compare)`
4. `java -Xms2g -Xmx2g -cp java/out taller3.bench.SupuestosBenchmark`
5. `(cd python && $PY -m taller3.bench_supuestos)`
6. `(cd python && $PY -m taller3.plot_compare)` — falla con mensaje claro si faltan
   `results/ordenamiento_*` o `results/busqueda_*` ("corre run_punto1.sh / run_punto2.sh").

Flags de los benchmarks (como el P1): `--sizes` (Java `10000,100000`; Python
`10000 100000`), `--distribuciones` (subconjunto válido), `--reps`, `--limit`, `--out`;
Python además `--algos` (`BucketSort`, `RadixSort`). Por defecto
`--out results/supuestos_{java,python}.csv`. `.gitignore`: sin cambios
(`results/prueba_*.csv` ya se ignora).

### 7.2 CSV `results/supuestos_java.csv` y `results/supuestos_python.csv`

Mismo esquema que `ordenamiento_*.csv` + columna `distribucion` después de `variante`
(UTF-8, coma, encabezado en la primera línea, fila escrita y vaciada al terminar cada
caso, `Locale.ROOT` en Java). Encabezado exacto:

```
algoritmo,lenguaje,variante,distribucion,n,rep_1_ns,rep_2_ns,rep_3_ns,rep_4_ns,rep_5_ns,promedio_ns,desv_estandar_ns,estado,causa,base_estimacion
```

| Columna | Contenido |
|---|---|
| `algoritmo` | `BucketSort` o `RadixSort` |
| `lenguaje` | `Java` / `Python` |
| `variante` | siempre `aleatoria` (orden de entrada desordenado, como en el P1) |
| `distribucion` | `uniforme`, `rango_pequeno`, `concentrado_extremos`, `digitos16` |
| `n` | entero |
| `rep_i_ns` | entero (ns); vacío si no se midió |
| `promedio_ns`, `desv_estandar_ns` | `%.1f`; vacíos si no hay valor |
| `estado`, `causa`, `base_estimacion` | mismo significado y formato que el P1 |

Implementación: Python `SupuestosCsvWriter(path, repetitions)` con
`write(record: ResultRecord, distribucion: str)` (reutiliza `ResultRecord`); Java
`SupuestosCsvWriter` con `write(ResultRecord r, String distribucion)`. Filas: Java 6,
Python 12 (6.2). Entorno: `results/entorno_supuestos_{java,python}.json` (como los del
P1, más los SHA-256 de los archivos de `data/p3/` usados); con `--out` distinto,
`entorno_<stem del --out>.json` junto al CSV.

### 7.3 Tablas y figuras (`plot_compare.py`)

1. `figures/p3_limite_inferior.csv`: `n,cota_inferior_comparaciones,n_log2_n,cociente`
   (n ∈ {10³…10⁶}, tabla 4.1).
2. `figures/p3_comparativos.{csv,md}`: `lenguaje,algoritmo,tipo,promedio_ns,ns_por_nlog2n,ns_por_elemento,razon_10e6_10e5,estado`
   (aleatoria, n = 10⁶, 6 algoritmos por lenguaje; `tipo` ∈ {`comparativo`,
   `no_comparativo`}).
3. `figures/p3_k_estrella.{csv,md}`:
   `lenguaje,rol,algoritmo_orden,t_ord_ns,fuente_t_lineal,t_lineal_ns,t_binaria_ns,k_estrella,k_min,k_bajo,k_alto,estado`.
   Filas en este orden (7):

   | lenguaje | rol | algoritmo_orden | fuente_t_lineal |
   |---|---|---|---|
   | Java | `principal` | RadixSort (mínimo medido) | `claves` |
   | Java | `banda` | ídem | `solo_presentes` (= `centro`) |
   | Java | `banda` | ídem | `solo_ausentes` (= `final`) |
   | Python | `principal` | BucketSort (mínimo medido) | `claves` |
   | Python | `banda` | ídem | `solo_presentes` |
   | Python | `banda` | ídem | `solo_ausentes` |
   | Python | `sensibilidad_orden` | **RadixSort** | `claves` |

   Formatos: `t_ord_ns` `%.1f`; `t_lineal_ns`, `t_binaria_ns` `%.3f`; `k_estrella`,
   `k_bajo`, `k_alto` `%.4f`; `k_min` entero. `estado`: `medido` si todas las entradas
   tienen `estado = medido`; `estimado` si alguna es estimada; `nunca_conviene` si
   t_L ≤ t_B (k vacíos). `algoritmo_orden` de las filas `principal`/`banda` se elige por
   código (mínimo `promedio_ns` medido), no se escribe a mano. El `.md` marca la fila de
   sensibilidad con la nota "sensibilidad: Radix en lugar de Bucket (×3,88)" e incluye el
   cálculo mostrado (k\* = t_ord / (t_L − t_B) con los números) de cada fila principal.
4. `figures/p3_supuestos.{csv,md}`:
   `lenguaje,algoritmo,distribucion,n,promedio_ns,desv_estandar_ns,estado,razon_vs_uniforme,cubetas_no_vacias,cubeta_max,desplazamientos,pasadas_radix,ref_comparativo,ref_comparativo_ns`.
   `razon_vs_uniforme` = promedio / promedio de (`uniforme`, mismo lenguaje, algoritmo y n)
   del CSV de supuestos; `cubetas_no_vacias`, `cubeta_max`, `desplazamientos` de
   `bucket_profile` (solo Bucket, vacío en Radix); `pasadas_radix` de `radix_passes`
   (solo Radix); `ref_comparativo` / `_ns` = el comparativo (InsertionSort, MergeSort,
   HeapSort, DualPivotQuickSort) con menor `promedio_ns` medido en
   `ordenamiento_{lenguaje}.csv`, aleatoria, mismo n (en `digitos16` el `.md` advierte
   "referencia medida con 8 dígitos").
5. `figures/p3_supuestos.png`: barras, eje y logarítmico, valor sobre cada barra; un panel
   por (algoritmo): Bucket (grupos n × distribución, barras Java/Python) y Radix Python
   (grupos n, barras `uniforme`/`digitos16`); estimados con barra rayada.
6. `figures/p3_costo_vs_k_{java,python}.png`: costo(k) de ambas estrategias frente a k
   (log-log), cruce marcado en k\* (fila `principal`). Se genera siempre; el grupo decide
   si la incluye en el informe.

## 8. Cómo se verifica

- Funciones puras: casos de 5.6 (`test_compare.py`).
- Datos: SHA-256 de 6.1.3 y perfiles de 4.4.3 sobre los archivos reales; si faltan los
  archivos, la prueba falla con "genera los datos: python3 -m taller3.generate_data".
  `SupuestosSelfTest` (Java): mapeo de `supuestosPath` (incluido el rechazo de
  `digitos16` y de nombres desconocidos), encabezado exacto del CSV, tabla `growth`, y que
  `BucketSort` ordena correctamente los 4 archivos de `data/p3/` de 8 dígitos contra
  `Arrays.sort`.
- Benchmark: cada repetición se verifica contra `sorted()` / `Arrays.sort` fuera del
  tiempo; si falla, se aborta (como el P1).
- `plot_compare.py` (avisos, no errores, salvo donde se indica):
  - **Error** si t_ord, t_B o t_L no se encuentran en los CSV.
  - t_ord principal es el mínimo entre los `medido`; t_L y t_B `medido`, si no → `estado`.
  - k\*(`solo_ausentes`) < k\*(`claves`) < k\*(`solo_presentes`); si no, aviso visible y
    **revisión obligatoria antes de escribir el informe** (regla aprobada 2026-10-22, 5.2).
  - t_L(`claves`)/t_L(`final`) ∈ [0,65; 0,85] y t_L(`centro`)/t_L(`final`) ∈ [0,4; 0,6];
    si no, aviso (el costo no sería proporcional a las comparaciones).
  - k\*(sensibilidad)/k\*(principal Python) = t_ord(Radix)/t_ord(Bucket) (3,8836 con los
    CSV actuales) con tolerancia relativa 10⁻⁹; si no, **error** (bug de cálculo).
  - Bucket `concentrado_extremos`: t(10⁵)/t(10⁴) ∈ [50, 200] (teórico ≈ 101) en cada
    lenguaje; Radix `digitos16`/`uniforme` ∈ [1,5; 3,5] en cada n; si no, aviso.
  - Filas `uniforme` del experimento vs P1 (BucketSort/RadixSort aleatoria, mismo n y
    lenguaje): diferencia relativa > 30 % → aviso (condiciones de la máquina distintas).

## 9. Preguntas de análisis que la salida debe permitir responder

- ¿Cuál es el límite inferior y por qué? ¿Por qué Radix y Bucket no están sujetos a él?
- ¿Los no comparativos fueron más rápidos que los comparativos en ambos lenguajes? ¿Por
  qué no en Python (Radix)? ¿Por qué Bucket es tan distinto entre Java y Python?
- ¿Qué supuesto hace cada uno y qué pasa si no se cumple? Radix 16 dígitos: ¿cuánto más
  lento (medido en Python, argumentado en Java) y queda por encima de los comparativos?
  Bucket: ¿por qué el rango pequeño **no** lo degrada con esta implementación y el cúmulo
  con extremos sí (×100 al multiplicar n por 10)? ¿Cuánto cuesta un desplazamiento en
  cada lenguaje?
- ¿A partir de qué k conviene ordenar, en cada lenguaje? ¿Cuánto cambia si las búsquedas
  son todas de claves presentes o todas ausentes? ¿Y si en Python se ordenara con Radix?

## 10. Decisiones del estudiante

### 10.1 Resueltas (2026-10-22)

| Decisión | Resolución |
|---|---|
| D1. Qué t_L usar | **(a) + banda (c)**: t_L = LinearSearch `claves`, n = 10⁶ del Punto 2 (sobre el ascendente, ≈ 0,75·n comparaciones); justificación y texto en 5.2; banda con `centro` y `final`. Sin mediciones nuevas. Descartada (b). |
| D2. "El algoritmo que obtuvo el mejor tiempo" | **(a)** el mejor de cada lenguaje (Java RadixSort, Python BucketSort, aleatoria 10⁶) **+** fila de sensibilidad en Python con RadixSort (1,78 s): k\* × 3,8836 (5.3, 7.3). |
| D3. Experimento de supuestos | **(b)**: Bucket en Java y Python con n = 10⁴ y 10⁵ (`uniforme`, `rango_pequeno`, `concentrado_extremos`); Radix 16 dígitos solo en Python (10⁴, 10⁵, 10⁶); Java 16 dígitos solo argumentado (4.4.2). Datos una vez por `generate_data.py` en `data/p3/`; 5 repeticiones con el protocolo del P1; CSV `results/supuestos_{java,python}.csv` (6, 7.2). |
| D4. Parámetros de las distribuciones | Resuelta por D3; valores concretos confirmados en 10.3. |
| Entorno de medición | Mediciones oficiales en el Mac del P1 con verificación previa y aborto si no coincide; desarrollo solo corrección (6.5). |
| D5. k\* para n < 10⁶ | **No**: como mucho una frase en el informe; sin tabla. |
| Tiempos de búsqueda para k\* | Los del Punto 2 con n = 10⁶ (D1). |
| Bibliografía | CLRS **4.ª ed. (2022)**; numeración marcada "verificar con el libro" (4). |

### 10.2 Opciones que se presentaron (registro)

- D1: (a)+(c) elegida; (b) medir la lineal sobre `aleatoria_1000000` con claves nuevas;
  (a) sola.
- D2: (a) mejor de cada lenguaje (elegida, con fila de sensibilidad); mismo algoritmo en
  ambos lenguajes.
- D3: solo argumentativo; Bucket Java+Python + Radix 16 Python (elegida); completo con
  `RadixSortLong` en Java.

### 10.3 Valores propuestos por la spec — RESUELTA (confirmados por el estudiante, 2026-10-22)

1. ✅ `SUPUESTOS_SEED = 20261017`.
2. ✅ `rango_pequeno` = uniforme en [10.000.000, 10.000.999] (1.000 valores), sin extremos.
3. ✅ `concentrado_extremos` = n − 2 uniformes en un cúmulo alineado a **10 cubetas**
   ([55.000.000, 55.089.999] con 10⁴; [55.000.000, 55.008.999] con 10⁵) + 10.000.000 +
   99.999.999, barajados. Redactada como **entrada adversaria**; **admite repetidos**
   (opción A, n = 10⁴ y 10⁵); argumento para el informe en 4.4.3.
4. ✅ `digitos16` = uniformes en [10¹⁵, 10¹⁶ − 1], prefijos de una secuencia de 10⁶, con
   **n = 10⁴, 10⁵ y 10⁶**, **versionados** (opción a, ≈ 19 MB en el repo).
5. ✅ Ruta `data/p3/` y claves del manifiesto `"p3/<archivo>"`.
6. ✅ Tolerancias de los avisos de 8 (±30 % vs P1; [50, 200]; [1,5; 3,5]).

Ningún valor cambió: los SHA-256 de 6.1.3 y los conteos de 4.4.3 siguen vigentes
(reverificados por ejecución el 2026-10-22).

## 11. Pendientes para el informe (no bloquean pruebas ni código)

- Confirmar contra el libro la numeración de CLRS 4.ª ed. (Teorema 8.1, §8.3 Lema 8.3,
  §8.4, ecuación de lg(n!)) antes de citarla.
- Comportamiento ya especificado: si alguna medición de P2 (lineal en Python a 10⁶)
  terminara `estimado`, el k\* se calcula igual y la fila queda `estado = estimado` (7.3);
  el grupo decide al redactar si repite la corrida. (Según la estimación de P2 no debería
  ocurrir.)
- Fuera de alcance (decidido): no se miden comparativos con 16 dígitos en Python (4.4.1);
  la comparación Radix-16 vs comparativos usa los tiempos de 8 dígitos como referencia,
  con advertencia.
