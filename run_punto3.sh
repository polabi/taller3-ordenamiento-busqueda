#!/usr/bin/env bash
# Punto 3 completo: datos de data/p3/ -> compilación -> pruebas -> benchmark Java ->
# benchmark Python -> tablas y gráficas (spec p3 7.1).
#
# Uso (desde la raíz del proyecto):
#   bash run_punto3.sh                    # corrida OFICIAL: solo en el Mac del Punto 1 (ver README)
#   bash run_punto3.sh --skip-env-check   # SOLO pruebas en otra máquina (alias: --no-medir):
#                                         # corrida corta (2 repeticiones, límite 5 s) y todas las
#                                         # salidas a un directorio temporal; NO toca results/ ni figures/.
#   bash run_punto3.sh --force            # medir de nuevo aunque ya existan results/supuestos_*.csv
#
# Necesita los resultados oficiales del Punto 1 (results/ordenamiento_*.csv) y del Punto 2
# (results/busqueda_*.csv): k* se calcula con ellos, no se miden de nuevo.
# Duración de la corrida oficial: pocos minutos (Python ≈ 2 min, Java < 15 s; spec 6.4).
# Usa `caffeinate -i bash run_punto3.sh | tee results/log_punto3.txt`.
# Recomendación (corrida oficial): cargador conectado, sin otros programas abiertos.
set -euo pipefail
cd "$(dirname "$0")"
source scripts/entorno_medicion.sh

# SHA-256 de los 7 archivos de data/p3/ (spec p3 6.1.3)
P3_SHA256=(
  "rango_pequeno_10000.txt 003a0b993de857ec96c4905b93e6e57bc1c24fd0ea711ce506fc1a3a163fcc76"
  "concentrado_extremos_10000.txt 98faca8f71baf19fd0a9c38e92dd4bfa69b37f8c2cd2fb6c221a6dc074035fce"
  "rango_pequeno_100000.txt 769ed52b6fa6c50f04e40cbc33587aea8f53ca1331162a9549a7620b1c5db22a"
  "concentrado_extremos_100000.txt 6c229b3698df7ac7e1e7acf9fd2f7498692228070d1a311b2ca7e1f3cd77faa9"
  "digitos16_10000.txt e3070fb38fcd24158fc39f3df21321553c82798cfb88bd17dae04236691dc49b"
  "digitos16_100000.txt 498749d81d819d233cfc59f743333278ea46470f79a0f870bb2179cba365e510"
  "digitos16_1000000.txt 211b340833ed98ddb22c5e786a746d08313bff08fa3d571a016b8f0e8cae1317"
)
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
for f in results/ordenamiento_java.csv results/ordenamiento_python.csv \
         results/busqueda_java.csv results/busqueda_python.csv; do
  if [[ ! -f "$f" ]]; then
    echo "ERROR: falta $f; corre run_punto1.sh / run_punto2.sh antes del Punto 3." >&2
    exit 1
  fi
done
if [[ $SKIP_ENV -eq 1 ]]; then
  OUT_DIR="$(mktemp -d "${TMPDIR:-/tmp}/taller3_p3_prueba.XXXXXX")"
  JAVA_CSV="$OUT_DIR/prueba_supuestos_java.csv"
  PY_CSV="$OUT_DIR/prueba_supuestos_python.csv"
  FIG_DIR="$OUT_DIR/figures"
  BENCH_ARGS_JAVA=(--reps 2 --limit 5)
  BENCH_ARGS_PY=(--reps 2 --limit 5)
  echo "AVISO: --skip-env-check -> corrida de PRUEBA (no oficial). Salidas en $OUT_DIR"
else
  refuse_overwrite "$FORCE" results/supuestos_java.csv results/supuestos_python.csv \
                            results/entorno_supuestos_java.json results/entorno_supuestos_python.json
  check_measurement_env
  JAVA_CSV="results/supuestos_java.csv"
  PY_CSV="results/supuestos_python.csv"
  FIG_DIR="figures"
  BENCH_ARGS_JAVA=()
  BENCH_ARGS_PY=()
fi
ABS_JAVA_CSV="$(cd "$(dirname "$JAVA_CSV")" && pwd)/$(basename "$JAVA_CSV")"
ABS_PY_CSV="$(cd "$(dirname "$PY_CSV")" && pwd)/$(basename "$PY_CSV")"
mkdir -p "$FIG_DIR"
ABS_FIG_DIR="$(cd "$FIG_DIR" && pwd)"
ABS_RESULTS="$(pwd)/results"

echo "== 1. Datos del Punto 3 (solo se generan si faltan; si existen se verifica su SHA-256) =="
(cd python && "$PY" -m taller3.generate_data)
for entry in "${P3_SHA256[@]}"; do
  name="${entry%% *}"; expected="${entry##* }"
  actual="$(shasum -a 256 "data/p3/$name" | awk '{print $1}')"
  if [[ "$actual" != "$expected" ]]; then
    echo "ERROR: SHA-256 de data/p3/$name = $actual; la spec exige $expected" >&2
    exit 1
  fi
done
echo "SHA-256 de los 7 archivos de data/p3/ OK"

echo "== 2. Compilación Java =="
rm -rf java/out
javac -encoding UTF-8 -d java/out $(find java/src -name "*.java")

echo "== 3. Pruebas del Punto 3 =="
java -cp java/out taller3.tests.SupuestosSelfTest
(cd python && "$PY" -m unittest tests.test_compare)

echo "== 4. Benchmark Java (compilado) =="
# Heap fijo de 2 GB como en el Punto 1. NO se cambia -Xss.
java -Xms2g -Xmx2g -cp java/out taller3.bench.SupuestosBenchmark --out "$JAVA_CSV" ${BENCH_ARGS_JAVA[@]+"${BENCH_ARGS_JAVA[@]}"}

echo "== 5. Benchmark Python (interpretado) =="
(cd python && "$PY" -m taller3.bench_supuestos --out "$ABS_PY_CSV" ${BENCH_ARGS_PY[@]+"${BENCH_ARGS_PY[@]}"})

echo "== 6. Tablas, k* y gráficas =="
(cd python && "$PY" -m taller3.plot_compare --java "$ABS_JAVA_CSV" --python "$ABS_PY_CSV" \
                                           --results "$ABS_RESULTS" --out "$ABS_FIG_DIR")
