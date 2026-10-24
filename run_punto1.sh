#!/usr/bin/env bash
# Punto 1 completo: datos -> pruebas -> benchmark Java -> benchmark Python -> gráficas.
#
# Uso (desde la raíz del proyecto):
#   bash run_punto1.sh                 # corrida OFICIAL: solo en el Mac del Punto 1 (ver README)
#   bash run_punto1.sh --solo-pruebas  # datos + compilación + pruebas, SIN medir (cualquier máquina)
#   bash run_punto1.sh --force         # medir de nuevo aunque ya existan los resultados oficiales
#
# Los resultados oficiales del Punto 1 ya están en results/ (ordenamiento_*.csv y
# entorno_{java,python}.json). Sin --force el script NO los sobrescribe.
# Recomendación (corrida oficial): cierra otros programas, conecta el cargador y no uses el
# equipo mientras corre.
set -euo pipefail
cd "$(dirname "$0")"
source scripts/entorno_medicion.sh

FORCE=0
SOLO_PRUEBAS=0
for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    --solo-pruebas) SOLO_PRUEBAS=1 ;;
    *) echo "Argumento desconocido: $arg" >&2; exit 2 ;;
  esac
done

echo "== 0. Intérprete y entorno de medición =="
require_venv                                   # SIEMPRE el .venv del proyecto
echo "Python: $PY ($("$PY" --version 2>&1))"
if [[ $SOLO_PRUEBAS -eq 0 ]]; then
  refuse_overwrite "$FORCE" results/ordenamiento_java.csv results/ordenamiento_python.csv \
                            results/entorno_java.json results/entorno_python.json
  require_matplotlib                           # antes de medir, no al final
  check_measurement_env                        # aborta si no es el Mac del Punto 1
fi

echo "== 1. Datos de prueba (solo se generan si no existen) =="
(cd python && "$PY" -m taller3.generate_data)

echo "== 2. Compilación Java =="
rm -rf java/out
javac -encoding UTF-8 -d java/out $(find java/src -name "*.java")

echo "== 3. Pruebas de corrección =="
# Solo las pruebas del Punto 1: las del Punto 2 tienen su propio script (run_punto2.sh).
java -cp java/out taller3.tests.SortSelfTest
(cd python && "$PY" -m unittest discover -s tests -p "test_sorting*.py")

if [[ $SOLO_PRUEBAS -eq 1 ]]; then
  echo "--solo-pruebas: no se mide (results/ y figures/ sin cambios)."
  exit 0
fi

echo "== 4. Benchmark Java (compilado) =="
# Heap fijo de 2 GB: evita que el tamaño del heap cambie durante la corrida.
# NO se cambia -Xss: el StackOverflowError del Dual-Pivot es parte de lo que se documenta.
java -Xms2g -Xmx2g -cp java/out taller3.bench.SortBenchmark

echo "== 5. Benchmark Python (interpretado) =="
(cd python && "$PY" -m taller3.bench_sort)

echo "== 6. Gráficas y tablas =="
(cd python && "$PY" -m taller3.plot_sort)
