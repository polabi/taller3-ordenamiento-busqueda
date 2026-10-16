package taller3.common;

import java.nio.file.Path;
import java.nio.file.Paths;

/**
 * Configuración central del lado Java. Replica python/taller3/config.py.
 * Java NO genera datos: solo los lee de data/ (generados una vez por Python).
 */
public final class Config {
    private Config() {}

    /** Rutas relativas a la raíz del proyecto (ejecutar desde la raíz). */
    public static final Path DATA_DIR = Paths.get("data");
    public static final Path RESULTS_DIR = Paths.get("results");

    public static final int MIN_VALUE = 10_000_000;
    public static final int MAX_VALUE = 99_999_999;
    public static final int[] SIZES = {1_000, 10_000, 100_000, 1_000_000};

    public static final int REPETITIONS = 5;
    public static final double TIME_LIMIT_SECONDS = 300;      // 5 min por ejecución

    /** Calentamiento global del JIT: rondas por algoritmo sobre la entrada aleatoria de este n. */
    public static final int GLOBAL_WARMUP_N = 10_000;
    public static final int GLOBAL_WARMUP_ROUNDS = 10;

    /**
     * Además del calentamiento global, cada caso (n, algoritmo, variante) se calienta
     * con ejecuciones que NO se promedian: se repiten hasta acumular 0,25 s o 20
     * ejecuciones (mínimo 1). Motivo: al cambiar de entrada (p. ej. de aleatoria a
     * ascendente) el JIT puede desoptimizar y recompilar; con una sola ejecución de
     * calentamiento esa recompilación caía dentro de una repetición medida en n = 1.000
     * (una repetición de 0,86 ms entre otras de 0,08 ms en las pruebas).
     *
     * Si la predicción del caso supera CASE_WARMUP_SKIP_ABOVE_SECONDS, el calentamiento
     * del caso se omite: en una ejecución de más de 60 s la compilación JIT (milisegundos)
     * es despreciable y repetirla solo alarga la corrida varios minutos.
     */
    public static final int CASE_WARMUP_MAX_RUNS = 20;
    public static final double CASE_WARMUP_TARGET_SECONDS = 0.25;
    public static final double CASE_WARMUP_SKIP_ABOVE_SECONDS = 60;
}
