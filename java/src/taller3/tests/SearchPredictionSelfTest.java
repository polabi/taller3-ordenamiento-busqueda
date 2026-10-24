package taller3.tests;

import java.io.FileDescriptor;
import java.io.FileOutputStream;
import java.io.PrintStream;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

import taller3.bench.SearchBenchmark;
import taller3.common.Config;
import taller3.common.Growth;
import taller3.common.SearchResultRecord;
import taller3.searching.SearchAlgorithm;
import taller3.searching.SearchRegistry;

/**
 * Pruebas del benchmark de búsqueda que faltaban (auditoría del Punto 2, 2026-10-23).
 * Mismos casos que python/tests/test_search_prediction.py:
 *   1. verifyPass: la verificación de CADA pasada (spec 6.3, 8.2).
 *   2. Camino de los ESTIMADOS (spec 6.5).
 *   3. Predicción POR POSICIÓN, proporcional al trabajo (hallazgo A).
 * No miden tiempos reales ni leen data/: arreglos sintéticos y límites diminutos.
 *
 *   java -cp java/out taller3.tests.SearchPredictionSelfTest
 */
public final class SearchPredictionSelfTest {
    static int failures = 0, total = 0;
    static final int N = Config.POSITION_N;
    static final int K = Config.NUM_SEARCH_KEYS;
    /** Mismo texto que produce bench_search.py. */
    static final String BASE_LINEAL_FINAL = "t_claves(1000000)=1.2 s (medido) x 1000000/748440 = x1.33611 "
            + "(pasos de una búsqueda en final / pasos medios por clave en claves)";

    static void check(boolean ok, String msg) {
        total++;
        if (!ok) { failures++; System.out.println("FALLA  " + msg); }
    }

    static boolean near(double a, double b, double relTol) {
        return Math.abs(a - b) <= relTol * Math.max(Math.abs(a), Math.abs(b));
    }

    static boolean throwsOn(Runnable r) {
        try { r.run(); return false; } catch (IllegalStateException e) { return true; }
    }

    public static void main(String[] args) {
        System.setOut(new PrintStream(new FileOutputStream(FileDescriptor.out), true, StandardCharsets.UTF_8));
        SearchAlgorithm linear = SearchRegistry.byName("LinearSearch");
        SearchAlgorithm binary = SearchRegistry.byName("BinarySearch");

        // ---------------------------------------------------------- 1. verifyPass
        int[] arr = {10, 20, 30, 40, 50};
        int[] keys = {20, 35, 50, 5, 10};                         // presentes: 20, 50, 10
        boolean[] present = SearchBenchmark.presence(arr, keys);
        long[] ok = SearchBenchmark.verifyPass("X", "claves", arr, keys, present, new int[]{1, -1, 4, -1, 0});
        check(Arrays.equals(ok, new long[]{3, 1 - 1 + 4 - 1 + 0}), "verifyPass correcta -> {encontradas, checksum con los -1}: " + Arrays.toString(ok));
        check(throwsOn(() -> SearchBenchmark.verifyPass("X", "claves", arr, keys, present, new int[]{1, -1, -1, -1, 0})),
                "verifyPass: presente no encontrada -> excepción");
        check(throwsOn(() -> SearchBenchmark.verifyPass("X", "claves", arr, keys, present, new int[]{2, -1, 4, -1, 0})),
                "verifyPass: índice que no corresponde a la clave -> excepción");
        check(throwsOn(() -> SearchBenchmark.verifyPass("X", "claves", arr, keys, present, new int[]{1, 2, 4, -1, 0})),
                "verifyPass: ausente 'encontrada' -> excepción");
        for (int bad : new int[]{5, -2}) {
            check(throwsOn(() -> SearchBenchmark.verifyPass("X", "claves", arr, keys, present, new int[]{bad, -1, 4, -1, 0})),
                    "verifyPass: índice fuera de rango " + bad + " -> excepción");
        }
        SearchAlgorithm malo = new SearchAlgorithm() {
            public String name() { return "Malo"; }
            public int search(int[] a, int x) { return 0; }
            public Growth growth() { return Growth.N; }
        };
        check(throwsOn(() -> new SearchBenchmark(2, 300).runCase(malo, "claves", arr, keys, present, null)),
                "runCase aborta si el algoritmo devuelve basura");

        // ------------------------------------------------- 2. camino de estimados
        {
            SearchBenchmark bench = new SearchBenchmark(2, 1e-9);   // cualquier predicción lo supera
            int[] k = new int[1000];
            for (int i = 0; i < k.length; i++) k[i] = 2 * i;
            int[] small = new int[1000];
            for (int i = 0; i < small.length; i++) small[i] = i;
            SearchResultRecord first = bench.runCase(linear, "claves", small, k, SearchBenchmark.presence(small, k), null);
            check(first.estado.equals("medido"), "estimados: sin n previo se mide (" + first.estado + ")");
            int[] big = new int[10_000];
            for (int i = 0; i < big.length; i++) big[i] = i;
            SearchResultRecord rec = bench.runCase(linear, "claves", big, k, SearchBenchmark.presence(big, k), null);
            check(rec.estado.equals("estimado"), "estimados: predicción > límite -> estimado (" + rec.estado + ")");
            check(rec.repsNs.length == 0 && rec.encontradas == null && rec.checksum == null,
                    "estimados: sin repeticiones, encontradas ni checksum");
            check(near(rec.promedioNs, first.promedioNs * 10, 1e-9), "estimados: t(10^4) = t(10^3) x 10 (O(n))");
            check(rec.causa.contains("> límite"), "estimados: causa: " + rec.causa);
            check(rec.baseEstimacion.startsWith("t(1000)="), "estimados: base: " + rec.baseEstimacion);
        }
        {
            SearchBenchmark bench = new SearchBenchmark(2, 300);
            bench.recordClaves("LinearSearch", N, 600e9, "estimado");
            Object[] p = bench.predictPosition(linear, "final", N);
            check(near((double) p[0], 600e9 * 1_000_000 / 748_440.213, 1e-12), "posición usa el claves estimado: " + p[0]);
            check(((String) p[1]).contains("(estimado)"), "posición: base menciona (estimado): " + p[1]);
        }
        {
            SearchBenchmark bench = new SearchBenchmark(2, 300);
            bench.recordClaves("LinearSearch", 100_000, 0.7e9, "medido");
            Object[] p = bench.predictPosition(linear, "final", N);
            check(near((double) p[0], 7e9 * 1_000_000 / 748_440.213, 1e-12), "posición sin claves en 10^6 extrapola: " + p[0]);
            check(((String) p[1]).startsWith("[t(100000)="), "posición extrapolada: base " + p[1]);
        }

        // --------------------------------------------- 3. predicción por posición
        double[][] expected = {
            {SearchBenchmark.positionFactor("LinearSearch", "inicio"), 1 / 748_440.213},
            {SearchBenchmark.positionFactor("LinearSearch", "centro"), 500_000 / 748_440.213},
            {SearchBenchmark.positionFactor("LinearSearch", "centro_alto"), 500_001 / 748_440.213},
            {SearchBenchmark.positionFactor("LinearSearch", "final"), 1_000_000 / 748_440.213},
            {SearchBenchmark.positionFactor("InterpolationSearchIntDiv", "final"), 1_000_000 / 504_349.278},
            {SearchBenchmark.positionFactor("BinarySearch", "centro"), 1 / 19.43},
            {SearchBenchmark.positionFactor("JumpSearch", "centro"), 1_500 / 993.639},
        };
        for (double[] e : expected) check(near(e[0], e[1], 1e-12), "factor de la spec 6.5: " + e[0] + " vs " + e[1]);
        for (SearchAlgorithm a : SearchRegistry.ALL) {
            for (String v : Config.POSITION_VARIANTS) {
                boolean fine;
                try { fine = SearchBenchmark.positionFactor(a.name(), v) > 0; } catch (RuntimeException ex) { fine = false; }
                check(fine, "tabla de trabajo cubre " + a.name() + " / " + v);
            }
        }
        {
            SearchBenchmark bench = new SearchBenchmark(2, 300);
            bench.recordClaves("LinearSearch", N, 1.2e9, "medido");
            double ini = (double) bench.predictPosition(linear, "inicio", N)[0];
            double cen = (double) bench.predictPosition(linear, "centro", N)[0];
            double fin = (double) bench.predictPosition(linear, "final", N)[0];
            check(ini < 1e4, "lineal inicio ≈ 1,6 µs, no 1,6 s: " + ini);
            check(near(fin / cen, 2.0, 1e-9), "lineal final/centro = 2: " + fin / cen);
            String txt = (String) bench.predictPosition(linear, "final", N)[1];
            check(BASE_LINEAL_FINAL.equals(txt), "texto de la base igual al de Python:\n         " + txt);
            bench.recordClaves("LinearSearch", 1000, 1e6, "medido");
            check(bench.predictPosition(linear, "final", 1000) == null, "sin predicción de posición fuera de 10^6");
        }
        {
            int[] a = new int[N];                                     // 10^6 valores únicos, sin archivos
            for (int i = 0; i < N; i++) a[i] = 2 * i;
            SearchBenchmark bench = new SearchBenchmark(2, 1.0);
            bench.recordClaves("LinearSearch", N, 1.2e9, "medido");   // final -> 1,6 s > 1 s
            boolean[] all = new boolean[K];
            Arrays.fill(all, true);
            int[] kIni = new int[K];
            Arrays.fill(kIni, a[0]);
            int[] kFin = new int[K];
            Arrays.fill(kFin, a[N - 1]);
            SearchResultRecord ini = bench.runCase(linear, "inicio", a, kIni, all, a[0]);
            SearchResultRecord fin = bench.runCase(linear, "final", a, kFin, all, a[N - 1]);
            check(ini.estado.equals("medido") && ini.encontradas == K && ini.checksum == 0,
                    "lineal inicio se MIDE aunque final se estime (" + ini.estado + ")");
            check(fin.estado.equals("estimado") && BASE_LINEAL_FINAL.equals(fin.baseEstimacion),
                    "lineal final se estima con su propio factor (" + fin.estado + ", " + fin.baseEstimacion + ")");
        }
        {
            SearchBenchmark bench = new SearchBenchmark(2, 300);
            bench.recordClaves("BinarySearch", N, 2e5, "medido");
            double c = (double) bench.predictPosition(binary, "centro", N)[0];
            double ca = (double) bench.predictPosition(binary, "centro_alto", N)[0];
            check(near(ca / c, 19.0, 1e-12), "binaria centro_alto/centro = 19: " + ca / c);
        }

        System.out.println(failures == 0
                ? "OK: " + total + " comprobaciones de predicción/estimación/verificación superadas"
                : failures + " de " + total + " comprobaciones fallaron");
        if (failures > 0) System.exit(1);
    }
}
