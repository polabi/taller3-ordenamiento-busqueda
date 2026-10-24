#!/usr/bin/env bash
# Punto 2 completo: claves -> compilación -> pruebas -> benchmark Java -> benchmark Python -> gráficas.
#
# Uso (desde la raíz del proyecto):
#   bash run_punto2.sh                    # corrida OFICIAL: solo en el Mac del Punto 1 (ver README)
#   bash run_punto2.sh --skip-env-check   # SOLO pruebas en otra máquina (alias: --no-medir):
#                                         # corrida corta (2 repeticiones, límite 5 s) y todas las
#                                         # salidas a un directorio temporal; NO toca results/ ni figures/.
#   bash run_punto2.sh --force            # medir de nuevo aunque ya existan results/busqueda_*.csv
#
# Duración de la corrida oficial: Python ≈ 40 min o más (lineal y variante entera en 10^6);
# Java, pocos minutos. Reserva ≈ 1 h y usa `caffeinate -i bash run_punto2.sh` para que el
# Mac no se duerma.
# Recomendación (corrida oficial): cargador conectado, sin otros programas abiertos.
set -euo pipefail
cd "$(dirname "$0")"
source scripts/entorno_medicion.sh

KEYS_SHA256="22fdc47fbcdd3e4b4d26fbcd3eae5010bb3becaa981337c9fe9fa41aaa0c965f"   # spec p2 6.1.1
SKIP_ENV=0
FORCE=0
for arg in "$@"; do
  case "$arg" in
    --skip-env-check|--no-medir) SKIP_ENV=1 ;;
    --force) FORCE=1 ;;
    *) echo "Argumento desconocido: $arg" >&2; exit 2 ;;
  esac
done

echo "== 0. Intérprete y entorno de medición =="
require_venv
echo "Python: $PY ($("$PY" --version 2>&1))"
require_matplotlib                                   # antes de medir, no al final
if [[ $SKIP_ENV -eq 1 ]]; then
  OUT_DIR="$(mktemp -d "${TMPDIR:-/tmp}/taller3_p2_prueba.XXXXXX")"
  JAVA_CSV="$OUT_DIR/prueba_busqueda_java.csv"
  PY_CSV="$OUT_DIR/prueba_busqueda_python.csv"
  FIG_DIR="$OUT_DIR/figures"
  BENCH_ARGS_JAVA=(--reps 2 --limit 5)
  BENCH_ARGS_PY=(--reps 2 --limit 5)
  echo "AVISO: --skip-env-check -> corrida de PRUEBA (no oficial). Salidas en $OUT_DIR"
else
  refuse_overwrite "$FORCE" results/busqueda_java.csv results/busqueda_python.csv \
                            results/entorno_busqueda_java.json results/entorno_busqueda_python.json
  check_measurement_env
  JAVA_CSV="results/busqueda_java.csv"
  PY_CSV="results/busqueda_python.csv"
  FIG_DIR="figures"
  BENCH_ARGS_JAVA=()
  BENCH_ARGS_PY=()
fi
ABS_JAVA_CSV="$(cd "$(dirname "$JAVA_CSV")" && pwd)/$(basename "$JAVA_CSV")"
ABS_PY_CSV="$(cd "$(dirname "$PY_CSV")" && pwd)/$(basename "$PY_CSV")"
mkdir -p "$FIG_DIR"
ABS_FIG_DIR="$(cd "$FIG_DIR" && pwd)"

echo "== 1. Claves de búsqueda (solo se generan si no existen; si existen se verifica su SHA-256) =="
(cd python && "$PY" -m taller3.generate_data)
actual_sha="$(shasum -a 256 data/claves_busqueda.txt | awk '{print $1}')"
if [[ "$actual_sha" != "$KEYS_SHA256" ]]; then
  echo "ERROR: SHA-256 de data/claves_busqueda.txt = $actual_sha; la spec exige $KEYS_SHA256" >&2
  exit 1
fi
echo "SHA-256 de las claves OK ($KEYS_SHA256)"

echo "== 2. Compilación Java =="
rm -rf java/out
javac -encoding UTF-8 -d java/out $(find java/src -name "*.java")

echo "== 3. Pruebas del Punto 2 =="
java -cp java/out taller3.tests.SearchSelfTest
java -cp java/out taller3.tests.SearchBenchSelfTest
java -cp java/out taller3.tests.SearchEquivalenceSelfTest
java -cp java/out taller3.tests.SearchPredictionSelfTest
(cd python && "$PY" -m unittest tests.test_searching tests.test_search_protocol \
                                tests.test_search_equivalence tests.test_plot_search \
                                tests.test_search_prediction)

echo "== 4. Benchmark Java (compilado) =="
# Heap fijo de 2 GB como en el Punto 1. NO se cambia -Xss.
java -Xms2g -Xmx2g -cp java/out taller3.bench.SearchBenchmark --out "$JAVA_CSV" ${BENCH_ARGS_JAVA[@]+"${BENCH_ARGS_JAVA[@]}"}

echo "== 5. Benchmark Python (interpretado) =="
(cd python && "$PY" -m taller3.bench_search --out "$ABS_PY_CSV" ${BENCH_ARGS_PY[@]+"${BENCH_ARGS_PY[@]}"})

echo "== 6. Equivalencia Java <-> Python, gráficas y tablas =="
(cd python && "$PY" -m taller3.plot_search --java "$ABS_JAVA_CSV" --python "$ABS_PY_CSV" --out "$ABS_FIG_DIR")
