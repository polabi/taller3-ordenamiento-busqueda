# Taller 3 — Ordenamiento y búsqueda (Java + Python)

Comparación experimental de algoritmos de ordenamiento y búsqueda en un lenguaje
compilado (Java, `System.nanoTime()`) y uno interpretado (Python, `time.perf_counter_ns()`).

> Estado: **base común + Punto 1 (ordenamiento) + Punto 2 (búsqueda: código, pruebas y
> scripts; mediciones oficiales pendientes en el Mac del Punto 1)**. Punto 3 se agrega
> sobre esta misma estructura. Spec del Punto 2: `specs/p2-busqueda.md`.

---

## 1. Estructura

```
taller3/
├── run_punto1.sh                 # todo el Punto 1 de principio a fin
├── run_punto2.sh                 # todo el Punto 2 (verifica el entorno antes de medir)
├── scripts/entorno_medicion.sh   # helper: .venv obligatorio + verificación del equipo de medición
├── data/                         # datos de prueba (se generan UNA vez, se versionan en Git)
│   ├── aleatoria_{n}.txt         # n ∈ {1000, 10000, 100000, 1000000}
│   ├── ascendente_{n}.txt
│   ├── descendente_{n}.txt
│   ├── claves_busqueda.txt       # Punto 2: 1.000 claves (500 presentes, 500 ausentes)
│   └── manifest.json             # semilla, SHA-256 y estadísticas de cada archivo
├── results/                      # CSV de resultados + entorno de ejecución
│   ├── ordenamiento_java.csv
│   ├── ordenamiento_python.csv
│   ├── entorno_java.json
│   └── entorno_python.json
├── figures/                      # 6 gráficas del Punto 1 + tablas de apoyo
├── java/src/taller3/
│   ├── common/   Config, Variant, DataIO, Dataset, Stats, Growth, Estimator,
│   │             ResultRecord, CsvResultWriter
│   ├── sorting/  SortAlgorithm (interfaz), InsertionSort, DualPivotQuickSort,
│   │             MergeSort, HeapSort, RadixSort, BucketSort, SortRegistry
│   ├── bench/    SortBenchmark (Punto 1)
│   └── tests/    SortSelfTest
└── python/
    ├── taller3/
    │   ├── config.py             # única fuente de verdad (Java la replica en Config.java)
    │   ├── generate_data.py      # ÚNICO generador de datos
    │   ├── common/  dataio, stats, timing, estimation, results
    │   ├── sorting/ insertion_sort, dual_pivot_quicksort, merge_sort,
    │   │            heap_sort, radix_sort, bucket_sort, __init__ (registro)
    │   ├── bench_sort.py         # Punto 1
    │   └── plot_sort.py          # gráficas y tablas del Punto 1
    └── tests/test_sorting.py
```

Separación de responsabilidades (igual en ambos lenguajes):

| Capa | Qué hace | Nunca hace |
|---|---|---|
| `common` | leer/escribir datos, estadística, estimación, CSV | medir tiempo de algoritmos |
| `sorting` | ordenar **in situ** un arreglo | leer archivos, copiar, medir |
| `bench` | cargar → copiar → medir → verificar → registrar | implementar algoritmos |

## 2. Cómo ejecutar

Requisitos: JDK 11 o superior, Python 3.9 o superior y `pip install matplotlib` (solo para las gráficas).

```bash
bash run_punto1.sh                 # datos, pruebas, Java, Python y gráficas (solo en el Mac del Punto 1)
bash run_punto1.sh --solo-pruebas  # datos, compilación y pruebas, sin medir (cualquier máquina)
bash run_punto1.sh --force         # medir de nuevo aunque ya existan results/ordenamiento_*.csv
```

Los resultados oficiales del Punto 1 ya están en `results/`. Sin `--force`, `run_punto1.sh`
**no** los sobrescribe (ni `ordenamiento_*.csv` ni `entorno_{java,python}.json`), y antes
de medir verifica el entorno y que matplotlib esté instalado, igual que `run_punto2.sh`.

Paso a paso (desde la raíz):

```bash
(cd python && python3 -m taller3.generate_data)                      # una sola vez
javac -encoding UTF-8 -d java/out $(find java/src -name "*.java")
java -cp java/out taller3.tests.SortSelfTest                          # corrección
(cd python && python3 -m unittest discover -s tests)
java -Xms2g -Xmx2g -cp java/out taller3.bench.SortBenchmark          # benchmark Java
(cd python && python3 -m taller3.bench_sort)                          # benchmark Python
(cd python && python3 -m taller3.plot_sort)                           # gráficas
```

**Duración de referencia.** En el equipo donde se hicieron las mediciones del informe
(MacBook Pro con Apple Silicon, 10 núcleos, macOS) la corrida completa tomó unos 9 min en Java
y unos 34 min en Python. La mayor parte del tiempo se va en Insertion Sort: con n = 10⁶ en Java
tarda unos 34 s por ejecución con entrada aleatoria y unos 66 s con descendente; con n = 10⁵
en Python, unos 2,1 min (aleatoria) y 4,2 min (descendente). Las mediciones deben hacerse con
el equipo conectado a la corriente y sin otras aplicaciones abiertas, porque agregan ruido.

Corridas parciales para depurar: `--sizes 1000,10000` (Java) / `--sizes 1000 10000` (Python),
`--algos`, `--variants`, `--reps`, `--limit`, `--out`.

### 2.1 Punto 2 (búsqueda)

```bash
bash run_punto2.sh                    # corrida OFICIAL (solo en el Mac del Punto 1)
bash run_punto2.sh --skip-env-check   # solo para probar en otra máquina (alias --no-medir)
bash run_punto2.sh --force            # medir de nuevo aunque ya existan results/busqueda_*.csv
```

`run_punto2.sh` hace: claves (las genera si faltan y verifica su SHA-256) → compilación →
pruebas del Punto 2 (`SearchSelfTest`, `SearchBenchSelfTest`, `SearchEquivalenceSelfTest`,
`SearchPredictionSelfTest`, `test_searching`, `test_search_protocol`,
`test_search_equivalence`, `test_plot_search`, `test_search_prediction`) →
benchmark Java (`-Xms2g -Xmx2g`) → benchmark Python → equivalencia Java ↔ Python, gráficas
y tablas. Salidas: `results/busqueda_{java,python}.csv`, `results/entorno_busqueda_{java,python}.json`,
`figures/p2_*`.

**Dónde se mide.** Las mediciones oficiales (Puntos 1, 2 y 3) se hacen en el **mismo
Mac del Punto 1** (macOS 26.6.2, 10 núcleos, Java 21.0.9, Python 3.9.6 del `.venv`), para
que los resultados sean comparables. Antes de medir, `run_punto1.sh` y `run_punto2.sh`
comparan el entorno actual con **valores fijos** (arm64, macOS 26.6.x, 10 núcleos,
Java 21.0.9, Python 3.9.6 del `.venv`, matplotlib instalado) y **abortan** si no coincide
(`scripts/entorno_medicion.sh`, reutilizable por `run_punto3.sh`; si solo cambia el parche
de macOS, avisan y siguen). Ya no se compara contra `results/entorno_*.json`, que una
corrida de `run_punto1.sh` podía reescribir. El modelo del Mac (`hw.model` y la CPU) queda
registrado en `results/entorno_busqueda_{java,python}.json`. Con
`--skip-env-check` no se verifica el entorno, pero la corrida es corta (2 repeticiones,
límite de 5 s, que fuerza algunos estimados) y **todas** sus salidas van a un directorio
temporal: nunca escribe en `results/` ni en `figures/`.

**Intérprete.** Todos los `run_punto*.sh` usan `.venv/bin/python` y abortan si no existe
(no caen al `python3` del PATH): `python3 -m venv .venv && .venv/bin/pip install matplotlib`.
`run_punto1.sh` corre solo las pruebas del Punto 1.

Paso a paso y corridas parciales (desde la raíz):

```bash
(cd python && ../.venv/bin/python -m taller3.generate_data)        # claves, si faltan
java -Xms2g -Xmx2g -cp java/out taller3.bench.SearchBenchmark --sizes 1000,10000 --out results/prueba_busq_java.csv
(cd python && ../.venv/bin/python -m taller3.bench_search --sizes 1000 10000 --out ../results/prueba_busq_python.csv)
(cd python && ../.venv/bin/python -m taller3.plot_search --java ../results/prueba_busq_java.csv \
                                     --python ../results/prueba_busq_python.csv --out /tmp/figs)
```

Flags de los benchmarks: `--sizes`, `--algos`, `--variants` (`claves`, `inicio`, `centro`,
`centro_alto`, `final`), `--reps`, `--limit`, `--out`. Con `--out X.csv` el entorno va a
`entorno_X.json` junto al CSV (ojo: `results/entorno_prueba_*.json` no está en `.gitignore`).
Duración estimada de la corrida oficial: el benchmark de Python puede tardar **≈ 40 min o
más** (la lineal y la variante de interpolación con división entera recorren hasta 10⁶
elementos por búsqueda; solo la variante suma ≈ 17 min según la estimación informal de la
spec 6.5, medida con otro Python en otro equipo); Java, pocos minutos. Reserva ≈ 1 h y
corre `caffeinate -i bash run_punto2.sh` para que el Mac no se duerma.

**Límite de 5 min en las posiciones.** Cada posición (`inicio`, `centro`, `centro_alto`,
`final`) se predice por separado: tiempo de `claves` en 10⁶ × (pasos de una búsqueda en esa
posición / pasos medios por clave en `claves`), con los pasos contados de la spec 6.5. Así,
si la pasada `final` de una búsqueda O(n) superara 300 s, solo esa quedaría estimada; `inicio`
(1 paso) se mide siempre.

## 3. Datos de prueba: decisiones de diseño

- **Un solo generador** (`generate_data.py`). Java no genera nada: solo lee. Así es
  imposible que los dos lenguajes midan con datos distintos.
- **Semilla fija** `20261015` con `random.Random` (Mersenne Twister), determinista en Python 3.
- **Tamaños anidados**: se genera una secuencia de 1.000.000 y cada n menor es su prefijo.
  Reduce la variación entre tamaños causada por los datos mismos.
- **Muestreo con reemplazo** en [10.000.000, 99.999.999]: con n = 10⁶ aparecen ~5.600
  repetidos (lo esperado por la paradoja del cumpleaños: n²/(2·9·10⁷) ≈ 5.556). Los
  algoritmos deben manejar duplicados.
- **Variantes ordenadas** (`ascendente`, `descendente`) generadas con `sorted()` de Python,
  una implementación independiente que además es el **oráculo de verificación**.
- **Formato**: un entero por línea, ASCII, `\n`, sin encabezado. Los lectores validan
  cantidad y rango y fallan de inmediato si algo no cuadra.
- **`manifest.json`**: SHA-256 de cada archivo; demuestra que los datos no cambiaron.
- Todos los valores caben en `int` de Java (99.999.999 < 2³¹ − 1).

## 4. Protocolo de medición

| | Java | Python |
|---|---|---|
| Reloj | `System.nanoTime()` | `time.perf_counter_ns()` |
| Carga de archivos | antes de medir | antes de medir |
| Copia del arreglo | `Arrays.copyOf`, fuera del tiempo | `list.copy()`, fuera del tiempo |
| Antes de cada medición | `System.gc()` | `gc.collect()` |
| Durante la medición | — | `gc.disable()` (como `timeit`) |
| Calentamiento | global (10 rondas por algoritmo, n = 10.000) + por caso (hasta 0,25 s o 20 ejecuciones) | no aplica (CPython sin JIT) |
| Repeticiones | 5 → promedio y desviación estándar **muestral** (n − 1) | igual |
| Verificación | `Arrays.equals` con el arreglo ascendente, fuera del tiempo | `==` con la lista ascendente, fuera del tiempo |

Comparar contra el arreglo de referencia verifica a la vez que el resultado está
**ordenado** y que es una **permutación** de la entrada. En Java, además, usar el
resultado impide que el JIT elimine el ordenamiento como código muerto.

El calentamiento por caso existe porque, al pasar de la entrada aleatoria a la
ascendente, el JIT puede desoptimizar y recompilar: en las pruebas, con una sola
ejecución de calentamiento, una repetición de Heap Sort con n = 1.000 tardó 0,86 ms
frente a ~0,07 ms de las demás. Se omite cuando la predicción del caso supera 60 s
(ahí la compilación JIT es despreciable).

## 5. Límite de 5 minutos, fallos y estimación

Antes de ejecutar un caso se **predice** su tiempo a partir del mayor n ya medido:

    t(n) ≈ t(n_med) · f(n) / f(n_med),   f ∈ { n, n·log₂n, n² } según el caso

- Si la predicción supera 300 s → no se ejecuta, `estado = estimado`, `causa = "predicción X s > límite…"`.
- Si el algoritmo falla (`StackOverflowError` en Java, `RecursionError` en Python) → se
  captura, `estado = estimado`, se documenta la causa y los n mayores se estiman sin
  intentarlos (la profundidad de recursión crece con n).
- La columna `base_estimacion` deja el cálculo exacto, p. ej.
  `t(10000)=0.0226 s x f(100000)/f(10000) = x100 con f=O(n^2)`.

**No se aumentan** `-Xss` ni `sys.setrecursionlimit()`: el taller pide documentar el fallo,
no ocultarlo.

Fallos esperados del Dual-Pivot QuickSort con pivotes extremos sobre entradas
ordenadas (profundidad de recursión ≈ n/2):

| Lenguaje | Límite | n = 1.000 (prof. ~500) | n = 10.000 (~5.000) | n = 100.000 (~50.000) |
|---|---|---|---|---|
| Python | 1.000 marcos | ejecuta | `RecursionError` | estimado |
| Java | pila de 1 MB (típico; depende de JVM/SO) | ejecuta | ejecuta | `StackOverflowError` |

## 6. Algoritmos (Punto 1)

Misma implementación en ambos lenguajes, línea a línea, siguiendo GeeksforGeeks.
En Python el mínimo y el máximo se calculan con ciclos explícitos (no con `min()`/`max()`,
que están escritos en C) para mantener la equivalencia.

| Algoritmo | Mejor | Promedio | Peor | Estable | In-place | Memoria extra |
|---|---|---|---|---|---|---|
| Insertion Sort | O(n) | O(n²) | O(n²) | Sí | Sí | O(1) |
| Dual-Pivot QuickSort (pivotes extremos) | O(n log n) | O(n log n) | O(n²) — entrada ya ordenada o invertida | No | Sí | O(log n) pila prom., O(n) peor |
| Merge Sort | O(n log n) | O(n log n) | O(n log n) | Sí | No | O(n) |
| Heap Sort | O(n log n) | O(n log n) | O(n log n) | No | Sí | O(1) (+ O(log n) pila del heapify recursivo) |
| Radix Sort (LSD, base 10) | O(d·(n+b)) | O(d·(n+b)) | O(d·(n+b)) | Sí | No | O(n + b) |
| Bucket Sort (k = n, Insertion por cubeta) | O(n + k) | O(n + n²/k + k) = O(n) con datos uniformes | O(n²) — todo en una cubeta | Sí | No | O(n + k) |

Con estos datos d = 8 dígitos y b = 10.

**Bucket Sort — configuración**: `k = n` cubetas; cada valor x va a la cubeta
`⌊(x − min) · k / (max − min + 1)⌋` (normalización a [0,1) de la versión de GfG para flotantes).
El `+1` garantiza índices en [0, k−1]. En Java el producto se hace en `long`
(hasta 9·10¹³). Cada cubeta se ordena con Insertion Sort y se concatenan en orden.
En Java las cubetas son `ArrayList<Integer>` (como en GfG): el *boxing* es un costo
constante real que la notación O(n) no muestra.

## 7. Esquema de resultados (CSV)

`algoritmo, lenguaje, variante, n, rep_1_ns … rep_5_ns, promedio_ns, desv_estandar_ns, estado, causa, base_estimacion`

`estado` ∈ {`medido`, `estimado`, `fallido`}. `fallido` solo aparece si no hay ninguna
medición previa con la cual estimar.

## 8. Gráficas y tablas para el análisis

`python3 -m taller3.plot_sort` produce las 6 gráficas que pide el taller (eje de tiempo
logarítmico, estimados punteados o rayados, valores visibles sobre las barras) y dos tablas:

- `figures/p1_razones_crecimiento.csv`: para cada salto n → 10n, la razón observada
  t(10n)/t(n) junto a la teórica. Referencias teóricas:

  | Complejidad | 10³→10⁴ | 10⁴→10⁵ | 10⁵→10⁶ |
  |---|---|---|---|
  | O(n) | 10 | 10 | 10 |
  | O(n log n) | 13,3 | 12,5 | 12 |
  | O(n²) | 100 | 100 | 100 |

  Cuando la razón observada se aleja de la teórica, las causas habituales son los términos
  de menor orden y los costos fijos con n pequeño, el tamaño de los datos frente a la caché,
  el JIT o el GC (Java) y el *boxing* (Bucket Sort en Java). Las filas `medido->estimado` reproducen la
  razón teórica por construcción: no sirven como evidencia, solo muestran la extrapolación.
- `figures/p1_resumen.csv`: promedio, desviación y coeficiente de variación (CV) de
  cada caso, listo para las tablas del informe. Un CV alto en n = 1.000 es esperable:
  esas ejecuciones duran microsegundos y el ruido del sistema pesa más.

## 9. Fuentes

- Insertion Sort — https://www.geeksforgeeks.org/dsa/insertion-sort-algorithm/
- Dual-Pivot QuickSort — https://www.geeksforgeeks.org/dsa/dual-pivot-quicksort/
- Merge Sort — https://www.geeksforgeeks.org/dsa/merge-sort/
- Heap Sort — https://www.geeksforgeeks.org/dsa/heap-sort/
- Radix Sort — https://www.geeksforgeeks.org/dsa/radix-sort/
- Bucket Sort — https://www.geeksforgeeks.org/dsa/bucket-sort-2/
