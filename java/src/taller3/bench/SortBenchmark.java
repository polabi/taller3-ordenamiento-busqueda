package taller3.bench;

import java.io.FileDescriptor;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.PrintStream;
import java.lang.management.ManagementFactory;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import taller3.common.Config;
import taller3.common.CsvResultWriter;
import taller3.common.Dataset;
import taller3.common.Estimator;
import taller3.common.ResultRecord;
import taller3.common.Stats;
import taller3.common.Variant;
import taller3.sorting.SortAlgorithm;
import taller3.sorting.SortRegistry;

/**
 * Punto 1 - Benchmark de ordenamiento en Java (lenguaje compilado con JIT).
 *
 * Ejecutar desde la RAÍZ del proyecto (ver run_punto1.sh):
 *   java -Xms2g -Xmx2g -cp java/out taller3.bench.SortBenchmark
 *   java -cp java/out taller3.bench.SortBenchmark --sizes 1000,10000 --reps 3
 *
 * Protocolo de medición:
 *  1. Calentamiento GLOBAL del JIT: cada algoritmo se ejecuta 10 veces sobre la
 *     entrada aleatoria de n = 10.000 antes de medir nada. Así hasta n = 1.000 se
 *     mide código ya compilado por C2 y no el intérprete.
 *  2. Por cada caso (n, algoritmo, variante): ejecuciones de calentamiento que NO
 *     se promedian (hasta 0,25 s o 20 ejecuciones; perfil del JIT para ESA
 *     entrada), luego 5 repeticiones medidas.
 *  3. Cada ejecución: copia nueva con Arrays.copyOf -> System.gc() -> nanoTime ->
 *     sort -> nanoTime -> verificación con Arrays.equals contra la referencia.
 *     Copia, GC y verificación quedan FUERA del tiempo.
 *     La verificación además usa el resultado, lo que impide que el JIT elimine
 *     el ordenamiento como "código muerto".
 *  4. Límite: si la predicción t(n_prev)·f(n)/f(n_prev) supera 300 s, no se
 *     ejecuta y se estima. StackOverflowError se captura, se documenta y se estima.
 */
public final class SortBenchmark {
    private static final String LANG = "Java";

    private final int reps;
    private final double limitNs;
    private final double limitS;
    private final Map<String, double[]> lastMeasured = new HashMap<>();   // clave -> {n, promedio_ns}
    private final Map<String, String> failed = new HashMap<>();            // clave -> descripción del fallo

    SortBenchmark(int reps, double limitS) {
        this.reps = reps;
        this.limitS = limitS;
        this.limitNs = limitS * 1e9;
    }

    private static String key(SortAlgorithm a, Variant v) { return a.name() + "|" + v.label(); }

    // ---------------------------------------------------------------- medición
    /** Mide UNA ejecución. La copia, el GC y la verificación quedan fuera del tiempo. */
    static long timeOnce(SortAlgorithm a, int[] base, int[] expected) {
        int[] work = Arrays.copyOf(base, base.length);   // copia nueva
        System.gc();                                      // reduce la probabilidad de una pausa de GC dentro de la medición
        long t0 = System.nanoTime();
        a.sort(work);
        long t1 = System.nanoTime();
        if (!Arrays.equals(work, expected)) {
            throw new IllegalStateException(a.name() + " NO ordenó correctamente (n=" + base.length + ")");
        }
        return t1 - t0;
    }

    static void globalWarmup(List<SortAlgorithm> algos, Path dataDir) throws IOException {
        Dataset w = Dataset.load(dataDir, Config.GLOBAL_WARMUP_N);
        System.out.printf(Locale.ROOT, "[Java] Calentamiento global: %d rondas x %d algoritmos, n=%,d aleatoria...%n",
                Config.GLOBAL_WARMUP_ROUNDS, algos.size(), Config.GLOBAL_WARMUP_N);
        for (SortAlgorithm a : algos) {
            for (int r = 0; r < Config.GLOBAL_WARMUP_ROUNDS; r++) {
                timeOnce(a, w.get(Variant.ALEATORIA), w.expectedSorted());
            }
        }
    }

    // -------------------------------------------------------------- estimación
    private ResultRecord estimated(SortAlgorithm a, Variant v, int n, String causa) {
        ResultRecord r = new ResultRecord(a.name(), LANG, v.label(), n);
        double[] prev = lastMeasured.get(key(a, v));
        if (prev == null) {
            r.estado = "fallido";
            r.causa = causa + " | sin medición previa para estimar";
            return r;
        }
        int n0 = (int) prev[0];
        r.promedioNs = Estimator.extrapolate(prev[1], n0, n, a.growth(v));
        r.estado = "estimado";
        r.causa = causa;
        r.baseEstimacion = Estimator.describe(prev[1], n0, n, a.growth(v));
        return r;
    }

    // --------------------------------------------------------------- un caso
    ResultRecord runCase(SortAlgorithm a, Variant v, Dataset ds) {
        String k = key(a, v);
        int n = ds.n;

        if (failed.containsKey(k)) {
            return estimated(a, v, n, "no ejecutado: " + failed.get(k)
                    + " y la profundidad de recursión crece con n");
        }

        double predicted = -1;
        double[] prev = lastMeasured.get(k);
        if (prev != null) {
            predicted = Estimator.extrapolate(prev[1], (int) prev[0], n, a.growth(v));
            if (predicted > limitNs) {
                return estimated(a, v, n, String.format(Locale.ROOT,
                        "predicción %.0f s > límite de %.0f s por ejecución", predicted / 1e9, limitS));
            }
        }

        int[] base = ds.get(v);
        int[] expected = ds.expectedSorted();
        long[] times = new long[reps];
        int count = 0;
        String note = "";
        try {
            boolean caseWarmup = predicted < 0 || predicted <= Config.CASE_WARMUP_SKIP_ABOVE_SECONDS * 1e9;
            if (caseWarmup) {                              // calentamiento del caso: NO se registra
                long spent = 0;
                int runs = 0;
                do {
                    spent += timeOnce(a, base, expected);
                    runs++;
                } while (runs < Config.CASE_WARMUP_MAX_RUNS && spent < Config.CASE_WARMUP_TARGET_SECONDS * 1e9);
            } else {
                note = "sin calentamiento por caso (predicción > "
                        + (int) Config.CASE_WARMUP_SKIP_ABOVE_SECONDS + " s; JIT ya caliente)";
            }
            for (int r = 0; r < reps; r++) {
                long t = timeOnce(a, base, expected);
                times[count++] = t;
                if (t > limitNs && r < reps - 1) {
                    note = String.format(Locale.ROOT,
                            "la repetición %d tardó %.0f s (> límite); se detuvieron las restantes", r + 1, t / 1e9);
                    break;
                }
            }
        } catch (StackOverflowError e) {
            failed.put(k, "falló con StackOverflowError en n=" + n);
            return estimated(a, v, n, "StackOverflowError: pila del hilo agotada (recursión de profundidad ~n/2)");
        }

        ResultRecord rec = new ResultRecord(a.name(), LANG, v.label(), n);
        rec.repsNs = Arrays.copyOf(times, count);
        rec.promedioNs = Stats.mean(times, count);
        rec.desvEstandarNs = Stats.sampleStd(times, count);
        rec.estado = "medido";
        rec.causa = note;
        lastMeasured.put(k, new double[]{n, rec.promedioNs});
        return rec;
    }

    // ------------------------------------------------------------------- main
    public static void main(String[] args) throws IOException {
        // Consola en UTF-8 (tildes, µ, ±) sin depender de la configuración regional
        System.setOut(new PrintStream(new FileOutputStream(FileDescriptor.out), true, "UTF-8"));
        int[] sizes = Config.SIZES;
        List<SortAlgorithm> algos = new ArrayList<>(SortRegistry.ALL);
        List<Variant> variants = new ArrayList<>(Arrays.asList(Variant.values()));
        int reps = Config.REPETITIONS;
        double limit = Config.TIME_LIMIT_SECONDS;
        Path dataDir = Config.DATA_DIR;
        Path out = Config.RESULTS_DIR.resolve("ordenamiento_java.csv");

        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--sizes":
                    sizes = Arrays.stream(args[++i].split(",")).mapToInt(s -> Integer.parseInt(s.trim())).sorted().toArray();
                    break;
                case "--algos":
                    algos.clear();
                    for (String s : args[++i].split(",")) algos.add(SortRegistry.byName(s.trim()));
                    break;
                case "--variants":
                    variants.clear();
                    for (String s : args[++i].split(",")) variants.add(Variant.fromLabel(s.trim()));
                    break;
                case "--reps":  reps = Integer.parseInt(args[++i]); break;
                case "--limit": limit = Double.parseDouble(args[++i]); break;
                case "--data":  dataDir = Paths.get(args[++i]); break;
                case "--out":   out = Paths.get(args[++i]); break;
                default: throw new IllegalArgumentException("Argumento desconocido: " + args[i]);
            }
        }

        String started = Instant.now().truncatedTo(ChronoUnit.SECONDS).toString();
        System.out.printf(Locale.ROOT, "[Java] %s %s | reps=%d | límite=%.0f s | salida: %s%n",
                System.getProperty("java.vm.name"), System.getProperty("java.version"), reps, limit, out);

        globalWarmup(algos, dataDir);
        SortBenchmark bench = new SortBenchmark(reps, limit);

        try (CsvResultWriter writer = new CsvResultWriter(out, reps)) {
            for (int n : sizes) {
                Dataset ds = Dataset.load(dataDir, n);     // carga fuera de toda medición
                for (SortAlgorithm a : algos) {
                    for (Variant v : variants) {
                        ResultRecord r = bench.runCase(a, v, ds);
                        writer.write(r);
                        print(r);
                    }
                }
            }
        }
        writeEnvironment(out.resolveSibling("entorno_java.json"), reps, limit, started);
        System.out.println("Listo.");
    }

    private static void print(ResultRecord r) {
        String shown;
        if (r.promedioNs == null) shown = "—";
        else if (r.estado.equals("medido")) shown = fmt(r.promedioNs) + " ± " + fmt(r.desvEstandarNs);
        else shown = "~" + fmt(r.promedioNs);
        String extra = r.causa.isEmpty() ? "" : "  [" + r.causa + "]";
        System.out.printf(Locale.ROOT, "  n=%,9d  %-19s %-11s %24s  %s%s%n",
                r.n, r.algoritmo, r.variante, shown, r.estado, extra);
    }

    static String fmt(double ns) {
        if (ns < 1e6) return String.format(Locale.ROOT, "%.1f µs", ns / 1e3);
        if (ns < 1e9) return String.format(Locale.ROOT, "%.2f ms", ns / 1e6);
        if (ns < 120e9) return String.format(Locale.ROOT, "%.2f s", ns / 1e9);
        return String.format(Locale.ROOT, "%.1f min", ns / 60e9);
    }

    private static void writeEnvironment(Path path, int reps, double limit, String started) throws IOException {
        Runtime rt = Runtime.getRuntime();
        String json = "{\n"
                + "  \"lenguaje\": \"Java\",\n"
                + "  \"vm\": \"" + System.getProperty("java.vm.name") + "\",\n"
                + "  \"version\": \"" + System.getProperty("java.version") + "\",\n"
                + "  \"so\": \"" + System.getProperty("os.name") + " " + System.getProperty("os.version")
                + " (" + System.getProperty("os.arch") + ")\",\n"
                + "  \"procesadores\": " + rt.availableProcessors() + ",\n"
                + "  \"heap_max_mb\": " + rt.maxMemory() / (1024 * 1024) + ",\n"
                + "  \"argumentos_jvm\": \"" + String.join(" ", ManagementFactory.getRuntimeMXBean().getInputArguments())
                        .replace("\\", "\\\\").replace("\"", "'") + "\",\n"
                + "  \"reloj\": \"System.nanoTime()\",\n"
                + "  \"calentamiento\": \"global " + Config.GLOBAL_WARMUP_ROUNDS + " rondas n=" + Config.GLOBAL_WARMUP_N
                        + " + por caso hasta " + Config.CASE_WARMUP_TARGET_SECONDS + " s o "
                        + Config.CASE_WARMUP_MAX_RUNS + " ejecuciones (omitido si prediccion > "
                        + Config.CASE_WARMUP_SKIP_ABOVE_SECONDS + " s)\",\n"
                + "  \"repeticiones\": " + reps + ",\n"
                + "  \"limite_s\": " + limit + ",\n"
                + "  \"inicio_utc\": \"" + started + "\",\n"
                + "  \"fin_utc\": \"" + Instant.now().truncatedTo(ChronoUnit.SECONDS) + "\"\n"
                + "}\n";
        Files.write(path, json.getBytes(StandardCharsets.UTF_8));
    }
}
