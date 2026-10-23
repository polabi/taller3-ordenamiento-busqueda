#!/usr/bin/env bash
# Funciones compartidas por run_punto2.sh y run_punto3.sh (se cargan con `source`).
#
#   require_venv            -> define PY=<raíz>/.venv/bin/python o aborta (no cae a python3 del PATH)
#   check_measurement_env   -> aborta si esta máquina NO es la de las mediciones oficiales
#
# Las mediciones del informe se hicieron en el Mac del Punto 1. Su entorno quedó en
# results/entorno_java.json y results/entorno_python.json; medir en otra máquina (otro SO,
# otra JVM, otro Python u otro número de núcleos) haría incomparables los puntos.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

require_venv() {
  PY="$ROOT/.venv/bin/python"
  if [[ ! -x "$PY" ]]; then
    echo "ERROR: no existe $PY." >&2
    echo "  Crea el entorno:  python3 -m venv .venv && .venv/bin/pip install matplotlib" >&2
    echo "  (no se usa el python3 del PATH: la versión de Python es parte del entorno medido)" >&2
    exit 1
  fi
  export PY
}

# Compara SO, núcleos, Java y Python con los JSON de entorno del Punto 1.
check_measurement_env() {
  local ref_java="$ROOT/results/entorno_java.json" ref_py="$ROOT/results/entorno_python.json"
  if [[ ! -f "$ref_java" || ! -f "$ref_py" ]]; then
    echo "ERROR: faltan $ref_java o $ref_py (entorno de referencia del Punto 1)." >&2
    exit 1
  fi
  local expected actual
  expected="$("$PY" - "$ref_java" "$ref_py" <<'PYEOF'
import json, re, sys
j = json.load(open(sys.argv[1], encoding="utf-8"))
p = json.load(open(sys.argv[2], encoding="utf-8"))
so = re.search(r"(\d+(?:\.\d+)+)", j["so"]).group(1)          # "Mac OS X 26.6.2 (aarch64)" -> 26.6.2
print(f"macOS={so} nucleos={j['procesadores']} java={j['version']} python={p['version'].split()[0]}")
PYEOF
)"
  local java_v
  java_v="$(java -XshowSettings:properties -version 2>&1 | awk -F'= ' '/^ *java.version =/{print $2; exit}')"
  actual="macOS=$(sw_vers -productVersion 2>/dev/null || echo '?') nucleos=$(sysctl -n hw.ncpu 2>/dev/null || echo '?') java=${java_v:-?} python=$("$PY" -c 'import platform; print(platform.python_version())')"
  echo "Entorno de referencia: $expected"
  echo "Entorno actual:        $actual"
  if [[ "$expected" != "$actual" ]]; then
    echo "ERROR: esta máquina no coincide con la de las mediciones oficiales (Mac del Punto 1)." >&2
    echo "  Corre las mediciones allí, o usa --skip-env-check SOLO para probar (no escribe en results/ ni figures/)." >&2
    exit 1
  fi
}
