#!/usr/bin/env bash
# Punto 1 completo: datos -> pruebas -> benchmark Java -> benchmark Python -> gráficas.
# Uso (desde la raíz del proyecto):   bash run_punto1.sh
# Recomendación: cierra otros programas, conecta el cargador y no uses el equipo mientras corre.
set -euo pipefail
cd "$(dirname "$0")"

# Intérprete: SIEMPRE el .venv del proyecto (aborta si no existe; no usa python3 del PATH).
PY="$PWD/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "ERROR: no existe $PY. Crea el entorno: python3 -m venv .venv && .venv/bin/pip install matplotlib" >&2
  exit 1
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

echo "== 4. Benchmark Java (compilado) =="
# Heap fijo de 2 GB: evita que el tamaño del heap cambie durante la corrida.
# NO se cambia -Xss: el StackOverflowError del Dual-Pivot es parte de lo que se documenta.
java -Xms2g -Xmx2g -cp java/out taller3.bench.SortBenchmark

echo "== 5. Benchmark Python (interpretado) =="
(cd python && "$PY" -m taller3.bench_sort)

echo "== 6. Gráficas y tablas =="
(cd python && "$PY" -m taller3.plot_sort)
