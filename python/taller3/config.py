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

# --- Punto 2 (búsqueda) -------------------------------------------------------
# Claves: data/claves_busqueda.txt, generado UNA vez por generate_data.py (spec p2 6.1).
SEARCH_KEYS_FILE = "claves_busqueda.txt"
SEARCH_KEYS_SEED = 20261016          # independiente de SEED: no altera los datos del Punto 1
NUM_SEARCH_KEYS = 1000               # 1 pasada = 1.000 búsquedas = 1 "ejecución" (D9)
NUM_PRESENT_KEYS = 500               # las otras 500 son ausentes
# Experimento de posición: solo en n = 10^6 (D7). Dos centros porque n es par (D3).
POSITION_N = 1_000_000
POSITION_VARIANTS = ("inicio", "centro", "centro_alto", "final")
SEARCH_VARIANTS = ("claves",) + POSITION_VARIANTS
