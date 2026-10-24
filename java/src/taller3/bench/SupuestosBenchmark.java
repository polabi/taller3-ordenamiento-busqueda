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
import java.util.Collections;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import taller3.common.Config;
import taller3.common.DataIO;
import taller3.common.Estimator;
import taller3.common.Growth;
import taller3.common.ResultRecord;
import taller3.common.Stats;
import taller3.common.SupuestosCsvWriter;
import taller3.sorting.BucketSort;
import taller3.sorting.SortAlgorithm;

/**
 * Punto 3 - Experimento de supuestos en Java: Bucket Sort con distribuciones que cumplen o
 * rompen su supuesto de datos uniformes (spec p3 6). Radix 16 dígitos NO se mide en Java:
 * no cabe en int (spec 4.4.2).
 *
 * Ejecutar desde la RAÍZ del proyecto (ver run_punto3.sh):
 *   java -Xms2g -Xmx2g -cp java/out taller3.bench.SupuestosBenchmark
 *   java -cp java/out taller3.bench.SupuestosBenchmark --sizes 10000 --reps 2 --out results/prueba_sup_java.csv
 *
 * Casos (6.2): BucketSort x {uniforme, rango_pequeno, concentrado_extremos} x n ∈ {10^4, 10^5};
 * n ascendente y, dentro de cada n, las distribuciones en el orden de Config.BUCKET_DISTRIBUTIONS.
 *
 * Protocolo (6.3, idéntico al Punto 1): calentamiento global SortBenchmark.globalWarmup
 * (10 rondas sobre aleatoria_10000) + calentamiento por caso (hasta 0,25 s o 20 ejecuciones,
 * no registradas); 5 repeticiones con SortBenchmark.timeOnce (copia -> System.gc() -> nanoTime
 * -> sort -> nanoTime -> Arrays.equals contra la referencia, calculada UNA vez fuera del tiempo
 * con Arrays.sort). Límite de 300 s con predicción t(n_prev)·f(n)/f(n_prev) según growth().
 */
public final class SupuestosBenchmark {
    private static final String LANG = "Java";

    private final int reps;
    private final double limitNs;
    private final double limitS;
    private final Map<String, double[]> lastMeasured = new HashMap<>();   // algoritmo|distribucion -> {n, promedio_ns}

    SupuestosBenchmark(int reps, double limitS) {
        this.reps = reps;
        this.limitS = limitS;
        this.limitNs = limitS * 1e9;
    }

    /** Complejidad para predecir/estimar (spec 6.4). Cualquier otro par -> IllegalArgumentException. */
    public static Growth growth(String algoritmo, String distribucion) {
        if (algoritmo.equals("BucketSort")) {
            switch (distribucion) {
                case "uniforme":
                case "rango_pequeno":        return Growth.N;
                case "concentrado_extremos": return Growth.N2;
                default: break;
            }
        } else if (algoritmo.equals("RadixSort")) {
            if (distribucion.equals("uniforme") || distribucion.equals("digitos16")) return Growth.N;
        }
        throw new IllegalArgumentException("Par sin complejidad declarada: " + algoritmo + " / " + distribucion);
    }

    /** entorno_<stem del CSV>.json junto al CSV (no pisa entorno_java.json del Punto 1). */
    public static Path environmentPath(Path out) {
        String name = out.getFileName().toString();
        String stem = name.endsWith(".csv") ? name.substring(0, name.length() - 4) : name;
        return out.resolveSibling("entorno_" + stem + ".json");
    }

    // -------------------------------------------------------------- estimación
    private ResultRecord estimated(SortAlgorithm a, String dist, int n, String causa) {
        ResultRecord r = new ResultRecord(a.name(), LANG, "aleatoria", n);
        double[] prev = lastMeasured.get(a.name() + "|" + dist);
        if (prev == null) {
            r.estado = "fallido";
            r.causa = causa + " | sin medición previa para estimar";
            return r;
        }
        Growth g = growth(a.name(), dist);
        int n0 = (int) prev[0];
        r.promedioNs = Estimator.extrapolate(prev[1], n0, n, g);
        r.estado = "estimado";
        r.causa = causa;
        r.baseEstimacion = Estimator.describe(prev[1], n0, n, g);
        return r;
    }

    // --------------------------------------------------------------- un caso
    ResultRecord runCase(SortAlgorithm a, String dist, int[] base, int[] expected) {
        String k = a.name() + "|" + dist;
        int n = base.length;
        Growth g = growth(a.name(), dist);

        double predicted = -1;
        double[] prev = lastMeasured.get(k);
        if (prev != null) {
            predicted = Estimator.extrapolate(prev[1], (int) prev[0], n, g);
            if (predicted > limitNs) {
                return estimated(a, dist, n, String.format(Locale.ROOT,
                        "predicción %.0f s > límite de %.0f s por ejecución", predicted / 1e9, limitS));
            }
        }

        long[] times = new long[reps];
        int count = 0;
        String note = "";
        boolean caseWarmup = predicted < 0 || predicted <= Config.CASE_WARMUP_SKIP_ABOVE_SECONDS * 1e9;
        if (caseWarmup) {                                  // calentamiento del caso: NO se registra
            long spent = 0;
            int runs = 0;
            do {
                spent += SortBenchmark.timeOnce(a, base, expected);
                runs++;
            } while (runs < Config.CASE_WARMUP_MAX_RUNS && spent < Config.CASE_WARMUP_TARGET_SECONDS * 1e9);
        } else {
            note = "sin calentamiento por caso (predicción > "
                    + (int) Config.CASE_WARMUP_SKIP_ABOVE_SECONDS + " s; JIT ya caliente)";
        }
        for (int r = 0; r < reps; r++) {
            long t = SortBenchmark.timeOnce(a, base, expected);
            times[count++] = t;
            if (t > limitNs && r < reps - 1) {
                note = String.format(Locale.ROOT,
                        "la repetición %d tardó %.0f s (> límite); se detuvieron las restantes", r + 1, t / 1e9);
                break;
            }
        }

        ResultRecord rec = new ResultRecord(a.name(), LANG, "aleatoria", n);
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
        System.setOut(new PrintStream(new FileOutputStream(FileDescriptor.out), true, "UTF-8"));
        List<Integer> sizes = new ArrayList<>();
        for (int n : Config.SUPUESTOS_SIZES) sizes.add(n);
        List<String> dists = new ArrayList<>(Arrays.asList(Config.BUCKET_DISTRIBUTIONS));
        int reps = Config.REPETITIONS;
        double limit = Config.TIME_LIMIT_SECONDS;
        Path dataDir = Config.DATA_DIR;
        Path out = Config.RESULTS_DIR.resolve("supuestos_java.csv");

        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--sizes":
                    sizes = filter(args[++i], toList(Config.SUPUESTOS_SIZES), "--sizes");
                    break;
                case "--distribuciones":
                    dists = filter(args[++i], Arrays.asList(Config.BUCKET_DISTRIBUTIONS), "--distribuciones");
                    break;
                case "--reps":  reps = Integer.parseInt(args[++i]); break;
                case "--limit": limit = Double.parseDouble(args[++i]); break;
                case "--out":   out = Paths.get(args[++i]); break;
                default: throw new IllegalArgumentException("Argumento desconocido: " + args[i]);
            }
        }

        String started = Instant.now().truncatedTo(ChronoUnit.SECONDS).toString();
        System.out.printf(Locale.ROOT, "[Java] %s %s | reps=%d | límite=%.0f s | salida: %s%n",
                System.getProperty("java.vm.name"), System.getProperty("java.version"), reps, limit, out);

        SortAlgorithm bucket = new BucketSort();
        SortBenchmark.globalWarmup(Collections.singletonList(bucket), dataDir);
        SupuestosBenchmark bench = new SupuestosBenchmark(reps, limit);
        Map<String, String> shaUsed = new LinkedHashMap<>();

        try (SupuestosCsvWriter writer = new SupuestosCsvWriter(out, reps)) {
            for (int n : sizes) {
                for (String dist : dists) {
                    Path file = DataIO.supuestosPath(dataDir, dist, n);
                    int[] base = DataIO.readSupuestos(dataDir, dist, n);      // carga fuera de toda medición
                    int[] expected = base.clone();                           // referencia independiente, una vez
                    Arrays.sort(expected);
                    if (!dist.equals("uniforme")) {
                        shaUsed.put(dataDir.relativize(file).toString().replace('\\', '/'), SearchBenchmark.sha256(file));
                    }
                    ResultRecord r = bench.runCase(bucket, dist, base, expected);
                    writer.write(r, dist);
                    print(r, dist);
                }
            }
        }
        writeEnvironment(environmentPath(out), reps, limit, started, sizes, dists, shaUsed);
        System.out.println("Listo.");
    }

    private static List<Integer> toList(int[] xs) {
        List<Integer> l = new ArrayList<>();
        for (int x : xs) l.add(x);
        return l;
    }

    /** Intersección (en el orden de la spec) con lo pedido; error si un valor no es válido o queda vacía. */
    private static <T> List<T> filter(String arg, List<T> valid, String flag) {
        List<String> asked = new ArrayList<>();
        for (String s : arg.split(",")) asked.add(s.trim());
        List<String> validText = new ArrayList<>();
        for (T v : valid) validText.add(String.valueOf(v));
        for (String s : asked) {
            if (!validText.contains(s)) {
                throw new IllegalArgumentException(flag + ": valor no válido " + s + " (válidos: " + validText + ")");
            }
        }
        List<T> res = new ArrayList<>();
        for (T v : valid) if (asked.contains(String.valueOf(v))) res.add(v);
        if (res.isEmpty()) throw new IllegalArgumentException(flag + ": la corrida quedaría vacía");
        return res;
    }

    private static void print(ResultRecord r, String dist) {
        String shown;
        if (r.promedioNs == null) shown = "—";
        else if (r.estado.equals("medido")) shown = SortBenchmark.fmt(r.promedioNs) + " ± " + SortBenchmark.fmt(r.desvEstandarNs);
        else shown = "~" + SortBenchmark.fmt(r.promedioNs);
        String extra = r.causa.isEmpty() ? "" : "  [" + r.causa + "]";
        System.out.printf(Locale.ROOT, "  n=%,9d  %-11s %-21s %24s  %s%s%n",
                r.n, r.algoritmo, dist, shown, r.estado, extra);
    }

    private static String q(String s) { return "\"" + s.replace("\\", "\\\\").replace("\"", "'") + "\""; }

    private static String qOrNull(String s) { return s == null ? "null" : q(s); }

    private static void writeEnvironment(Path path, int reps, double limit, String started, List<Integer> sizes,
                                         List<String> dists, Map<String, String> shaUsed) throws IOException {
        Runtime rt = Runtime.getRuntime();
        List<String> distNames = new ArrayList<>();
        for (String d : dists) distNames.add(q(d));
        StringBuilder sha = new StringBuilder();
        for (Map.Entry<String, String> e : shaUsed.entrySet()) {
            sha.append(sha.length() == 0 ? "" : ",\n").append("    ").append(q(e.getKey())).append(": ").append(q(e.getValue()));
        }
        String json = "{\n"
                + "  \"lenguaje\": \"Java\",\n"
                + "  \"vm\": " + q(System.getProperty("java.vm.name")) + ",\n"
                + "  \"version\": " + q(System.getProperty("java.version")) + ",\n"
                + "  \"so\": " + q(System.getProperty("os.name") + " " + System.getProperty("os.version")
                        + " (" + System.getProperty("os.arch") + ")") + ",\n"
                + "  \"modelo\": " + qOrNull(SearchBenchmark.sysctl("hw.model")) + ",\n"
                + "  \"cpu\": " + qOrNull(SearchBenchmark.sysctl("machdep.cpu.brand_string")) + ",\n"
                + "  \"procesadores\": " + rt.availableProcessors() + ",\n"
                + "  \"heap_max_mb\": " + rt.maxMemory() / (1024 * 1024) + ",\n"
                + "  \"argumentos_jvm\": " + q(String.join(" ", ManagementFactory.getRuntimeMXBean().getInputArguments())) + ",\n"
                + "  \"reloj\": \"System.nanoTime()\",\n"
                + "  \"calentamiento\": \"global " + Config.GLOBAL_WARMUP_ROUNDS + " rondas n=" + Config.GLOBAL_WARMUP_N
                        + " (BucketSort) + por caso hasta " + Config.CASE_WARMUP_TARGET_SECONDS + " s o "
                        + Config.CASE_WARMUP_MAX_RUNS + " ejecuciones (omitido si prediccion > "
                        + Config.CASE_WARMUP_SKIP_ABOVE_SECONDS + " s)\",\n"
                + "  \"repeticiones\": " + reps + ",\n"
                + "  \"limite_s\": " + limit + ",\n"
                + "  \"tamanos\": " + sizes + ",\n"
                + "  \"distribuciones\": [" + String.join(", ", distNames) + "],\n"
                + "  \"datos_p3_sha256\": {\n" + sha + "\n  },\n"
                + "  \"inicio_utc\": \"" + started + "\",\n"
                + "  \"fin_utc\": \"" + Instant.now().truncatedTo(ChronoUnit.SECONDS) + "\"\n"
                + "}\n";
        Files.write(path, json.getBytes(StandardCharsets.UTF_8));
    }
}
