#!/usr/bin/env bash
# Funciones compartidas por run_punto1.sh, run_punto2.sh y run_punto3.sh (se cargan con `source`).
#
#   require_venv            -> define PY=<raíz>/.venv/bin/python o aborta (no cae a python3 del PATH)
#   require_matplotlib      -> aborta si el .venv no tiene matplotlib (ANTES de medir, no al final)
#   check_measurement_env   -> aborta si esta máquina NO es la de las mediciones oficiales
#   refuse_overwrite F...   -> aborta si alguno de los archivos ya existe y no se pasó --force
#
# Las mediciones del informe se hacen en el Mac del Punto 1. Se compara contra valores FIJOS
# (no contra results/entorno_*.json: una corrida de run_punto1.sh podía reescribirlos y la
# verificación pasaría a compararse contra sí misma). Spec p2 6.6.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# --- Entorno de las mediciones oficiales (Mac del Punto 1) ------------------------------
EXPECTED_ARCH="arm64"
EXPECTED_MACOS="26.6.2"     # se exige 26.6.x; si solo cambia el parche, se avisa
EXPECTED_CORES="10"
EXPECTED_JAVA="21.0.9"
EXPECTED_PYTHON="3.9.6"

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

require_matplotlib() {
  if ! "$PY" -c "import matplotlib" >/dev/null 2>&1; then
    echo "ERROR: el .venv no tiene matplotlib; las gráficas fallarían DESPUÉS de medir." >&2
    echo "  Instálalo:  .venv/bin/pip install matplotlib" >&2
    exit 1
  fi
}

check_measurement_env() {
  local arch macos cores java_v py_v errors=0
  arch="$(uname -m 2>/dev/null || echo '?')"
  macos="$(sw_vers -productVersion 2>/dev/null || echo '?')"
  cores="$(sysctl -n hw.ncpu 2>/dev/null || echo '?')"
  java_v="$(java -XshowSettings:properties -version 2>&1 | awk -F'= ' '/^ *java.version =/{print $2; exit}')"
  py_v="$("$PY" -c 'import platform; print(platform.python_version())')"

  echo "Entorno exigido: arch=$EXPECTED_ARCH macOS=$EXPECTED_MACOS nucleos=$EXPECTED_CORES java=$EXPECTED_JAVA python=$EXPECTED_PYTHON"
  echo "Entorno actual:  arch=$arch macOS=$macos nucleos=$cores java=${java_v:-?} python=$py_v"
  echo "Equipo:          $(sysctl -n hw.model 2>/dev/null || echo '?') / $(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo '?')"

  _env_mismatch() { echo "ERROR: $1" >&2; errors=$((errors + 1)); }
  [[ "$arch" == "$EXPECTED_ARCH" ]]     || _env_mismatch "arquitectura $arch (se exige $EXPECTED_ARCH)"
  [[ "$cores" == "$EXPECTED_CORES" ]]   || _env_mismatch "núcleos $cores (se exigen $EXPECTED_CORES)"
  [[ "${java_v:-?}" == "$EXPECTED_JAVA" ]] || _env_mismatch "Java ${java_v:-?} (se exige $EXPECTED_JAVA)"
  [[ "$py_v" == "$EXPECTED_PYTHON" ]]   || _env_mismatch "Python $py_v (se exige $EXPECTED_PYTHON)"
  if [[ "${macos%.*}" != "${EXPECTED_MACOS%.*}" ]]; then
    _env_mismatch "macOS $macos (se exige ${EXPECTED_MACOS%.*}.x)"
  elif [[ "$macos" != "$EXPECTED_MACOS" ]]; then
    echo "AVISO: macOS $macos en vez de $EXPECTED_MACOS (solo cambió el parche); anótalo en el informe." >&2
  fi
  if [[ $errors -gt 0 ]]; then
    echo "ERROR: esta máquina no coincide con la de las mediciones oficiales (Mac del Punto 1)." >&2
    echo "  Corre las mediciones allí, o usa el modo de prueba del script (no escribe resultados oficiales)." >&2
    exit 1
  fi
}

# Uso: refuse_overwrite "$FORCE" archivo1 archivo2 ...
refuse_overwrite() {
  local force="$1"; shift
  [[ "$force" -eq 1 ]] && return 0
  local f existing=()
  for f in "$@"; do [[ -e "$ROOT/$f" ]] && existing+=("$f"); done
  if [[ ${#existing[@]} -gt 0 ]]; then
    echo "ERROR: ya existen resultados oficiales que esta corrida sobrescribiría:" >&2
    printf '  %s\n' "${existing[@]}" >&2
    echo "  Si de verdad quieres medir de nuevo, vuelve a correr con --force." >&2
    exit 1
  fi
}
