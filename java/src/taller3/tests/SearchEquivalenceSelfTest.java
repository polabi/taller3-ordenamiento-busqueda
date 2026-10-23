package taller3.tests;

import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

import taller3.common.Config;
import taller3.common.DataIO;
import taller3.searching.SearchAlgorithm;
import taller3.searching.SearchRegistry;

/**
 * Prueba versionada de equivalencia Java <-> Python del Punto 2 (spec 8.5).
 *   java -cp java/out taller3.tests.SearchEquivalenceSelfTest      (desde la raíz)
 *
 * Java y Python (python/tests/test_search_equivalence.py) se comparan contra las MISMAS
 * constantes de specs/p2-busqueda.md 8.5, calculadas con un oráculo independiente
 * (bisect_left / fórmula cerrada) y recalculadas por el escritor de pruebas el 2026-10-22.
 *
 *   enc = #{j : out[j] != -1};   S1 = Σ out[j] (incluye los -1);   S2 = Σ (j+1)·out[j]   (long)
 *
 * Parte A: arreglo sintético N = 100.000, K = 200, claves recorridas en orden j = 0, 1, 2...
 *   Cada algoritmo corre en un hilo aparte con un máximo de 10 s: un ciclo infinito (p. ej.
 *   por desbordamiento int de "multiplicar primero" en la interpolación) se reporta como
 *   FALLA en vez de colgar la prueba. La primera excepción hace fallar el caso (no se captura
 *   por clave para continuar).
 * Parte C: data/claves_busqueda.txt sobre data/ascendente_1000.txt, leídas con
 *   DataIO.readSearchKeys (por reflexión mientras no exista). Si el archivo no existe, FALLA
 *   con "genera las claves: python3 -m taller3.generate_data" (spec 8.5: no se salta).
 */
public final class SearchEquivalenceSelfTest {
    static int failures = 0, total = 0;

    static void check(boolean ok, String msg) {
        total++;
        if (!ok) { failures++; System.out.println("FALLA  " + msg); }
    }

    static final String[] EXPECTED_ORDER = {
        "LinearSearch", "BinarySearch", "TernarySearch", "JumpSearch",
        "InterpolationSearch", "ExponentialSearch", "InterpolationSearchIntDiv"
    };
    static final long TIMEOUT_SECONDS = 10;

    // Parte A
    static final int N_A = 100_000, K_A = 200;
    static final long A_SUM = 1_201_713_770_300L, Q_SUM = 2_431_583_865L;
    static final int[] Q_FIRST6 = {10_000_000, 15_700_395, 10_236_788, 10_448_997, 10_723_916, 11_061_547};
    static final long[] A_EXPECTED = {120, 5_953_340L, 629_320_400L};      // enc, S1, S2

    // Parte C
    static final long[] C_EXPECTED = {500, 249_971L, 120_950_349L};
    static final String MISSING_KEYS_MSG = "genera las claves: python3 -m taller3.generate_data";

    static int[] buildA() {
        int[] a = new int[N_A];
        for (int i = 0; i < N_A; i++) a[i] = 10_000_500 + 7 * i + (int) ((long) i * i / 2000);
        return a;
    }

    static int[] buildQ(int[] a) {
        int[] q = new int[K_A];
        for (int j = 0; j < K_A; j++) {
            int p = (j * 7919) % N_A;
            int r = j % 10;
            if (r == 0)                q[j] = 10_000_000 + j;          // ausente, < mínimo
            else if (r == 1)           q[j] = a[N_A - 1] + 1 + j;      // ausente, > máximo
            else if (r == 2 || r == 3) q[j] = a[p] + 1;                // ausente interior
            else                       q[j] = a[p];                    // presente en p(j)
        }
        return q;
    }

    /** {enc, S1, S2} recorriendo las claves en orden j = 0..K-1. */
    static long[] runKeys(SearchAlgorithm alg, int[] arr, int[] keys) {
        long enc = 0, s1 = 0, s2 = 0;
        for (int j = 0; j < keys.length; j++) {
            int o = alg.search(arr, keys[j]);
            if (o != -1) enc++;
            s1 += o;
            s2 += (long) (j + 1) * o;
        }
        return new long[]{enc, s1, s2};
    }

    static String fmt(long[] v) { return "enc=" + v[0] + ", S1=" + v[1] + ", S2=" + v[2]; }

    public static void main(String[] args) throws Exception {
        List<SearchAlgorithm> all = SearchRegistry.ALL;
        check(all.size() == EXPECTED_ORDER.length, "registro: se esperaban 7 algoritmos, hay " + all.size());
        for (int k = 0; k < Math.min(all.size(), EXPECTED_ORDER.length); k++) {
            check(EXPECTED_ORDER[k].equals(all.get(k).name()), "registro: posición " + k + " = " + all.get(k).name());
        }

        // ------------------------------------------------ Parte A: construcción
        int[] a = buildA();
        int[] q = buildQ(a);
        long sumA = 0, sumQ = 0;
        boolean increasing = true, inRange = true;
        for (int i = 0; i < N_A; i++) {
            sumA += a[i];
            if (i > 0 && a[i] <= a[i - 1]) increasing = false;
            if (a[i] < Config.MIN_VALUE || a[i] > Config.MAX_VALUE) inRange = false;
        }
        for (int v : q) sumQ += v;
        check(a[0] == 10_000_500 && a[1] == 10_000_507 && a[2] == 10_000_514, "8.5 A: A[0..2]");
        check(a[N_A - 1] == 15_700_393, "8.5 A: A[N-1] == 15700393, obtuvo " + a[N_A - 1]);
        check(sumA == A_SUM, "8.5 A: ΣA == " + A_SUM + ", obtuvo " + sumA);
        check(increasing && inRange, "8.5 A: estrictamente creciente y de 8 dígitos");
        check(Arrays.equals(Arrays.copyOf(q, 6), Q_FIRST6), "8.5 A: Q[0..5] = " + Arrays.toString(Arrays.copyOf(q, 6)));
        check(sumQ == Q_SUM, "8.5 A: ΣQ == " + Q_SUM + ", obtuvo " + sumQ);
        check(Arrays.stream(q).distinct().count() == K_A, "8.5 A: las 200 claves son distintas");

        // ------------------------------------------------ Parte A: 7 algoritmos con tiempo máximo
        ExecutorService ex = Executors.newSingleThreadExecutor(r -> {
            Thread t = new Thread(r, "parteA");
            t.setDaemon(true);                // un ciclo infinito no impide terminar la JVM
            return t;
        });
        int[] snapshot = a.clone();
        for (SearchAlgorithm alg : all) {
            String id = "8.5 A / " + alg.name();
            Future<long[]> f = ex.submit(() -> runKeys(alg, a, q));
            try {
                long[] got = f.get(TIMEOUT_SECONDS, TimeUnit.SECONDS);
                check(Arrays.equals(got, A_EXPECTED), id + ": esperado " + fmt(A_EXPECTED) + ", obtuvo " + fmt(got));
            } catch (TimeoutException e) {
                f.cancel(true);
                check(false, id + ": no terminó en " + TIMEOUT_SECONDS + " s (¿ciclo infinito por desbordamiento?)");
                // El hilo colgado sigue ocupando el ejecutor: se crea otro para los demás.
                ex.shutdownNow();
                ex = Executors.newSingleThreadExecutor(r -> { Thread t = new Thread(r, "parteA"); t.setDaemon(true); return t; });
            } catch (java.util.concurrent.ExecutionException e) {
                check(false, id + ": excepción " + e.getCause());
            }
        }
        ex.shutdownNow();
        check(Arrays.equals(a, snapshot), "8.5 A: algún algoritmo modificó el arreglo");

        // ------------------------------------------------ Parte C: archivo real
        Path keysFile = Config.DATA_DIR.resolve("claves_busqueda.txt");
        if (!Files.exists(keysFile)) {
            check(false, "8.5 C: no existe " + keysFile + ": " + MISSING_KEYS_MSG);
        } else {
            int[] keys = null;
            try {
                Method read = DataIO.class.getMethod("readSearchKeys", Path.class);
                keys = (int[]) read.invoke(null, Config.DATA_DIR);
            } catch (NoSuchMethodException e) {
                check(false, "8.5 C: falta public static int[] DataIO.readSearchKeys(Path) (spec 6.1.6)");
            } catch (InvocationTargetException e) {
                check(false, "8.5 C: readSearchKeys lanzó " + e.getCause());
            }
            if (keys != null) {
                check(keys.length == 1000, "8.5 C: 1000 claves, hay " + keys.length);
                int[] asc = DataIO.readInts(Config.DATA_DIR.resolve("ascendente_1000.txt"), 1000);
                int present = 0;
                for (int k : keys) if (Arrays.binarySearch(asc, k) >= 0) present++;
                check(present == 500, "8.5 C: reparto 500 presentes / 500 ausentes, presentes = " + present);
                for (SearchAlgorithm alg : all) {
                    long[] got;
                    try { got = runKeys(alg, asc, keys); }
                    catch (RuntimeException e) { check(false, "8.5 C / " + alg.name() + ": excepción " + e); continue; }
                    check(Arrays.equals(got, C_EXPECTED),
                            "8.5 C / " + alg.name() + ": esperado " + fmt(C_EXPECTED) + ", obtuvo " + fmt(got));
                }
            }
        }

        System.out.println(failures == 0
                ? "OK: " + total + " comprobaciones de equivalencia 8.5 superadas (partes A y C)"
                : failures + " de " + total + " comprobaciones fallaron");
        System.exit(failures > 0 ? 1 : 0);
    }
}
