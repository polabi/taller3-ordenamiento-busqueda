"""
Configuración central del taller (única fuente de verdad para Python).

Java replica estos mismos valores en java/src/taller3/common/Config.java.
Si cambias algo aquí, cámbialo también allá.
"""
from __future__ import annotations

from pathlib import Path

# --- Rutas ------------------------------------------------------------------
# python/taller3/config.py -> parents[2] = raíz del proyecto
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
FIGURES_DIR = PROJECT_ROOT / "figures"

# --- Datos de prueba ----------------------------------------------------------
SEED = 20261015                      # semilla fija -> datos reproducibles
MIN_VALUE = 10_000_000               # menor entero de 8 dígitos
MAX_VALUE = 99_999_999               # mayor entero de 8 dígitos
SIZES = (1_000, 10_000, 100_000, 1_000_000)

# Variantes de entrada del Punto 1. El nombre es también el prefijo del archivo:
#   data/aleatoria_1000.txt, data/ascendente_1000.txt, data/descendente_1000.txt
VARIANTS = ("aleatoria", "ascendente", "descendente")

# --- Medición -----------------------------------------------------------------
REPETITIONS = 5
TIME_LIMIT_SECONDS = 300             # 5 minutos por ejecución (regla del taller)
