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
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.time.Instant;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

import taller3.common.Config;
import taller3.common.DataIO;
import taller3.common.Estimator;
import taller3.common.SearchCsvWriter;
import taller3.common.SearchResultRecord;
import taller3.common.Stats;
import taller3.searching.SearchAlgorithm;
import taller3.searching.SearchRegistry;

/**
 * Punto 2 - Benchmark de búsqueda en Java (lenguaje compilado con JIT).
 * Equivalente a python/taller3/bench_search.py.
 *
 * Ejecutar desde la RAÍZ del proyecto (ver run_punto2.sh):
 *   java -Xms2g -Xmx2g -cp java/out taller3.bench.SearchBenchmark
 *   java -cp java/out taller3.bench.SearchBenchmark --sizes 1000,10000 --out results/prueba_busq.csv
 *
 * Experimentos (spec p2 6.2), para cada n ascendente: `claves` (las 1.000 claves del archivo)
 * para cada algoritmo; si n = 1.000.000, además `inicio`, `centro`, `centro_alto`, `final`
 * (la misma clave 1.000 veces).
 *
 * Protocolo:
 *  1. Calentamiento GLOBAL del JIT: 10 pasadas por algoritmo sobre ascendente_10000 con el
 *     archivo de claves (como el Punto 1).
 *  2. Por caso: predicción (claves: t(n_prev)·f(n)/f(n_prev); posición: t_claves(10^6) x
 *     factor). Si supera 300 s -> estimado. Si no, calentamiento del caso (hasta 0,25 s o
 *     20 pasadas, omitido si la predicción supera 60 s) y 5 repeticiones.
 *  3. Cada pasada: System.gc() -> nanoTime -> out[j] = search(arr, keys[j]) -> nanoTime.
 *     Guardar cada resultado en out[] (que se usa después) impide que el JIT descarte las
 *     búsquedas como código muerto. Verificación y checksum, FUERA del tiempo, contra
 *     Arrays.binarySearch (oráculo independiente).
 *  4. El arreglo no se copia (la búsqueda no lo modifica); al terminar cada n se comprueba
 *     con Arrays.equals que sigue igual al archivo cargado.
 */
public final class SearchBenchmark {
    private static final String LANG = "Java";

    private final int reps;
    private final double limitNs;
    private final double limitS;
    private final Map<String, double[]> lastMeasured = new HashMap<>();   // claves: alg -> {n, promedio_ns}
    private final Map<String, Double> clavesAt = new HashMap<>();         // "alg|n" -> promedio_ns
    private final Map<String, String> clavesAtEstado = new HashMap<>();   // "alg|n" -> medido/estimado

    SearchBenchmark(int reps, double limitS) {
        this.reps = reps;
        this.limitS = limitS;
        this.limitNs = limitS * 1e9;
    }

    /** Índice de la clave de cada experimento de posición (spec 6.2). */
    public static int positionIndex(String variante, int n) {
        switch (variante) {
            case "inicio":      return 0;
            case "centro":      return (n - 1) / 2;
            case "centro_alto": return n / 2;
            case "final":       return n - 1;
            default: throw new IllegalArgumentException("Variante de posición desconocida: '" + variante + "'");
        }
    }

    /** entorno_<stem del CSV>.json junto al CSV (no pisa entorno_java.json del Punto 1). */
    public static Path environmentPath(Path out) {
        String name = out.getFileName().toString();
        int dot = name.lastIndexOf('.');
        String stem = dot > 0 ? name.substring(0, dot) : name;
        return out.resolveSibling("entorno_" + stem + ".json");
    }

    /**
     * Factor de la predicción de las posiciones = costo de la pasada `final` / pasada `claves`
     * (spec 6.5). Lineal: 10^9 / 748.440.213 = 1,336 ~ 4/3. Variante entera: 2. Resto: 4/3.
     */
    static double positionFactor(String alg) {
        if (alg.equals("InterpolationSearchIntDiv")) return 2.0;
        return 4.0 / 3.0;
    }

    static String positionFactorText(String alg) {
        return alg.equals("InterpolationSearchIntDiv") ? "2" : "4/3";
    }

    // ---------------------------------------------------------------- medición
    /** Mide UNA pasada: out[j] = search(arr, keys[j]). Devuelve ns. GC fuera del tiempo. */
    public static long timeSearches(SearchAlgorithm alg, int[] arr, int[] keys, int[] out) {
        int k = keys.length;
        System.gc();                                      // reduce la probabilidad de una pausa de GC dentro de la medición
        long t0 = System.nanoTime();
        for (int j = 0; j < k; j++) {
            out[j] = alg.search(arr, keys[j]);
        }
        long t1 = System.nanoTime();
        return t1 - t0;
    }

    /** Oráculo independiente (Arrays.binarySearch de la biblioteca estándar): ¿está cada clave? */
    static boolean[] presence(int[] arr, int[] keys) {
        boolean[] present = new boolean[keys.length];
        for (int j = 0; j < keys.length; j++) present[j] = Arrays.binarySearch(arr, keys[j]) >= 0;
        return present;
    }

    /** Verifica una pasada (fuera del tiempo) y devuelve {encontradas, checksum}. */
    static long[] verifyPass(String name, String variant, int[] arr, int[] keys, boolean[] present, int[] out) {
        int n = arr.length;
        long found = 0;
        long checksum = 0;
        for (int j = 0; j < keys.length; j++) {
            int o = out[j];
            if (o == -1) {
                if (present[j]) {
                    throw new IllegalStateException(name + " no encontró la clave " + keys[j]
                            + " (" + variant + ", n=" + n + ")");
                }
            } else {
                if (o < 0 || o >= n || arr[o] != keys[j]) {
                    throw new IllegalStateException(name + " devolvió el índice " + o + " para la clave "
                            + keys[j] + " (" + variant + ", n=" + n + ")");
                }
                found++;
            }
            checksum += o;                                // incluye los -1 (spec 6.3)
        }
        return new long[]{found, checksum};
    }

    /** Las 4 claves de posición deben ser ÚNICAS en el arreglo (spec 6.2). */
    static void checkPositionKeys(int[] arr) {
        for (String v : Config.POSITION_VARIANTS) {
            int key = arr[positionIndex(v, arr.length)];
            int count = 0;
            for (int x : arr) if (x == key) count++;
            if (count != 1) {
                throw new IllegalStateException("La clave de " + v + " (" + key + ") aparece " + count + " veces");
            }
        }
    }

    static void globalWarmup(List<SearchAlgorithm> algos, Path dataDir, int[] keys) throws IOException {
        int[] w = DataIO.readInts(dataDir.resolve("ascendente_" + Config.GLOBAL_WARMUP_N + ".txt"), Config.GLOBAL_WARMUP_N);
        boolean[] present = presence(w, keys);
        int[] out = new int[keys.length];
        System.out.printf(Locale.ROOT, "[Java] Calentamiento global: %d pasadas x %d algoritmos, n=%,d ascendente...%n",
                Config.GLOBAL_WARMUP_ROUNDS, algos.size(), Config.GLOBAL_WARMUP_N);
        for (SearchAlgorithm a : algos) {
            for (int r = 0; r < Config.GLOBAL_WARMUP_ROUNDS; r++) {
                timeSearches(a, w, keys, out);
                verifyPass(a.name(), "calentamiento", w, keys, present, out);
            }
        }
    }

    // -------------------------------------------------------------- predicción
    /** {predicción_ns} y texto de la base, o null si no hay medición previa. */
    private Object[] predictClaves(SearchAlgorithm a, int n) {
        double[] prev = lastMeasured.get(a.name());
        if (prev == null) return null;
        int n0 = (int) prev[0];
        return new Object[]{Estimator.extrapolate(prev[1], n0, n, a.growth()),
                            Estimator.describe(prev[1], n0, n, a.growth())};
    }

    private Object[] predictPosition(SearchAlgorithm a, int n) {
        double factor = positionFactor(a.name());
        String factorTxt = positionFactorText(a.name());
        Double base = clavesAt.get(a.name() + "|" + n);
        if (base == null) {                               // sin `claves` en este n: se extrapola
            Object[] pred = predictClaves(a, n);
            if (pred == null) return null;
            return new Object[]{(double) pred[0] * factor,
                                "[" + pred[1] + "] x " + factorTxt + " (pasada final / pasada claves)"};
        }
        String estado = clavesAtEstado.get(a.name() + "|" + n);
        return new Object[]{base * factor, String.format(Locale.ROOT, "t_claves(%d)=%s s (%s) x %s (pasada final / pasada claves)",
                n, g6(base / 1e9), estado, factorTxt)};
    }

    /** 6 cifras significativas sin ceros sobrantes (como :.6g de Python y Estimator). */
    private static String g6(double x) {
        String s = String.format(Locale.ROOT, "%.6g", x);
        if (s.contains("e")) return s;
        return s.contains(".") ? s.replaceAll("0+$", "").replaceAll("\\.$", "") : s;
    }

    // --------------------------------------------------------------- un caso
    SearchResultRecord runCase(SearchAlgorithm a, String variant, int[] arr, int[] keys,
                               boolean[] present, Integer clave) {
        int n = arr.length;
        SearchResultRecord rec = new SearchResultRecord(a.name(), LANG, variant, n);
        rec.numBusquedas = keys.length;
        rec.clave = clave;
        Object[] pred = variant.equals("claves") ? predictClaves(a, n) : predictPosition(a, n);
        double predicted = pred == null ? -1 : (double) pred[0];
        if (predicted > limitNs) {
            rec.promedioNs = predicted;
            rec.estado = "estimado";
            rec.causa = String.format(Locale.ROOT, "predicción %.0f s > límite de %.0f s por ejecución",
                    predicted / 1e9, limitS);
            rec.baseEstimacion = (String) pred[1];
            if (variant.equals("claves")) {
                clavesAt.put(a.name() + "|" + n, predicted);
                clavesAtEstado.put(a.name() + "|" + n, "estimado");
            }
            return rec;
        }

        int[] out = new int[keys.length];                 // preasignado, fuera del tiempo
        long[] times = new long[reps];
        int count = 0;
        long[] result = null;
        String note = "";
        boolean caseWarmup = predicted < 0 || predicted <= Config.CASE_WARMUP_SKIP_ABOVE_SECONDS * 1e9;
        if (caseWarmup) {                                 // calentamiento del caso: NO se registra
            long spent = 0;
            int runs = 0;
            do {
                spent += timeSearches(a, arr, keys, out);
                verifyPass(a.name(), variant, arr, keys, present, out);
                runs++;
            } while (runs < Config.CASE_WARMUP_MAX_RUNS && spent < Config.CASE_WARMUP_TARGET_SECONDS * 1e9);
        } else {
            note = "sin calentamiento por caso (predicción > "
                    + (int) Config.CASE_WARMUP_SKIP_ABOVE_SECONDS + " s; JIT ya caliente)";
        }
        for (int r = 0; r < reps; r++) {
            long t = timeSearches(a, arr, keys, out);
            long[] check = verifyPass(a.name(), variant, arr, keys, present, out);   // fuera del tiempo
            if (result != null && !Arrays.equals(check, result)) {
                throw new IllegalStateException(a.name() + ": encontradas/checksum cambiaron entre repeticiones ("
                        + variant + ", n=" + n + "): " + Arrays.toString(result) + " vs " + Arrays.toString(check));
            }
            result = check;
            times[count++] = t;
            if (t > limitNs && r < reps - 1) {
                note = String.format(Locale.ROOT,
                        "la repetición %d tardó %.0f s (> límite); se detuvieron las restantes", r + 1, t / 1e9);
                break;
            }
        }

        rec.repsNs = Arrays.copyOf(times, count);
        rec.promedioNs = Stats.mean(times, count);
        rec.desvEstandarNs = Stats.sampleStd(times, count);
        rec.encontradas = (int) result[0];
        rec.checksum = result[1];
        rec.estado = "medido";
        rec.causa = note;
        if (variant.equals("claves")) {
            lastMeasured.put(a.name(), new double[]{n, rec.promedioNs});
            clavesAt.put(a.name() + "|" + n, rec.promedioNs);
            clavesAtEstado.put(a.name() + "|" + n, "medido");
        }
        return rec;
    }

    /** Mínima diferencia > 0 entre lecturas consecutivas de nanoTime (spec 6.5). */
    static long clockResolutionNs(int samples) {
        long[] reads = new long[samples];
        for (int i = 0; i < samples; i++) reads[i] = System.nanoTime();
        long best = 0;
        for (int i = 1; i < samples; i++) {
            long d = reads[i] - reads[i - 1];
            if (d > 0 && (best == 0 || d < best)) best = d;
        }
        return best;
    }

    // ------------------------------------------------------------------- main
    public static void main(String[] args) throws IOException {
        // Consola en UTF-8 (tildes, µ, ±) sin depender de la configuración regional
        System.setOut(new PrintStream(new FileOutputStream(FileDescriptor.out), true, "UTF-8"));
        int[] sizes = Config.SIZES;
        List<SearchAlgorithm> algos = new ArrayList<>(SearchRegistry.ALL);
        List<String> requested = new ArrayList<>(Arrays.asList(Config.SEARCH_VARIANTS));
        int reps = Config.REPETITIONS;
        double limit = Config.TIME_LIMIT_SECONDS;
        Path dataDir = Config.DATA_DIR;
        Path out = Config.RESULTS_DIR.resolve("busqueda_java.csv");

        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--sizes":
                    sizes = Arrays.stream(args[++i].split(",")).mapToInt(s -> Integer.parseInt(s.trim())).sorted().toArray();
                    break;
                case "--algos":
                    algos.clear();
                    for (String s : args[++i].split(",")) algos.add(SearchRegistry.byName(s.trim()));
                    break;
                case "--variants":
                    requested.clear();
                    for (String s : args[++i].split(",")) {
                        if (!Arrays.asList(Config.SEARCH_VARIANTS).contains(s.trim())) {
                            throw new IllegalArgumentException("Variante desconocida: " + s);
                        }
                        requested.add(s.trim());
                    }
                    break;
                case "--reps":  reps = Integer.parseInt(args[++i]); break;
                case "--limit": limit = Double.parseDouble(args[++i]); break;
                case "--data":  dataDir = Paths.get(args[++i]); break;
                case "--out":   out = Paths.get(args[++i]); break;
                default: throw new IllegalArgumentException("Argumento desconocido: " + args[i]);
            }
        }
        List<String> variants = new ArrayList<>();       // orden de la spec
        for (String v : Config.SEARCH_VARIANTS) if (requested.contains(v)) variants.add(v);
        List<String> positions = new ArrayList<>(variants);
        positions.remove("claves");
        boolean withPositionN = Arrays.stream(sizes).anyMatch(s -> s == Config.POSITION_N);

        String started = Instant.now().truncatedTo(ChronoUnit.SECONDS).toString();
        int[] keys = DataIO.readSearchKeys(dataDir);       // carga fuera de toda medición
        String keysSha = sha256(dataDir.resolve(Config.SEARCH_KEYS_FILE));
        long resolution = clockResolutionNs(1000);
        if (!positions.isEmpty() && withPositionN) {      // al arrancar: claves de posición únicas
            checkPositionKeys(DataIO.readInts(dataDir.resolve("ascendente_" + Config.POSITION_N + ".txt"), Config.POSITION_N));
        }
        System.out.printf(Locale.ROOT, "[Java] %s %s | reps=%d | límite=%.0f s | resolución del reloj ≈ %d ns | salida: %s%n",
                System.getProperty("java.vm.name"), System.getProperty("java.version"), reps, limit, resolution, out);

        globalWarmup(algos, dataDir, keys);
        SearchBenchmark bench = new SearchBenchmark(reps, limit);

        try (SearchCsvWriter writer = new SearchCsvWriter(out, reps)) {
            for (int n : sizes) {
                int[] arr = DataIO.readInts(dataDir.resolve("ascendente_" + n + ".txt"), n);
                int[] snapshot = arr.clone();             // para comprobar que nadie lo modificó
                if (variants.contains("claves")) {
                    boolean[] present = presence(arr, keys);
                    for (SearchAlgorithm a : algos) {
                        SearchResultRecord r = bench.runCase(a, "claves", arr, keys, present, null);
                        writer.write(r);
                        print(r);
                    }
                }
                if (n == Config.POSITION_N) {
                    boolean[] allPresent = new boolean[Config.NUM_SEARCH_KEYS];
                    Arrays.fill(allPresent, true);
                    for (SearchAlgorithm a : algos) {
                        for (String v : positions) {
                            int key = arr[positionIndex(v, n)];
                            int[] posKeys = new int[Config.NUM_SEARCH_KEYS];   // armado fuera del tiempo
                            Arrays.fill(posKeys, key);
                            SearchResultRecord r = bench.runCase(a, v, arr, posKeys, allPresent, key);
                            writer.write(r);
                            print(r);
                        }
                    }
                }
                if (!Arrays.equals(arr, snapshot)) {
                    throw new IllegalStateException("Algún algoritmo modificó el arreglo (n=" + n + ")");
                }
            }
        }
        writeEnvironment(environmentPath(out), reps, limit, started, keysSha, resolution, sizes, algos, variants);
        System.out.println("Listo.");
    }

    private static void print(SearchResultRecord r) {
        String shown;
        if (r.promedioNs == null) shown = "—";
        else if (r.estado.equals("medido")) {
            shown = fmt(r.promedioNs / r.numBusquedas) + " ± " + fmt(r.desvEstandarNs / r.numBusquedas) + " /búsq.";
        } else shown = "~" + fmt(r.promedioNs / r.numBusquedas) + " /búsq.";
        String extra = r.causa.isEmpty() ? "" : "  [" + r.causa + "]";
        System.out.printf(Locale.ROOT, "  n=%,9d  %-25s %-11s %30s  %s%s%n",
                r.n, r.algoritmo, r.variante, shown, r.estado, extra);
    }

    /** Como en el Punto 1, pero en ns por debajo de 1 µs (una búsqueda binaria dura decenas de ns). */
    static String fmt(double ns) {
        if (ns < 1e3) return String.format(Locale.ROOT, "%.1f ns", ns);
        if (ns < 1e6) return String.format(Locale.ROOT, "%.1f µs", ns / 1e3);
        if (ns < 1e9) return String.format(Locale.ROOT, "%.2f ms", ns / 1e6);
        if (ns < 120e9) return String.format(Locale.ROOT, "%.2f s", ns / 1e9);
        return String.format(Locale.ROOT, "%.1f min", ns / 60e9);
    }

    static String sha256(Path path) throws IOException {
        try {
            byte[] d = MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path));
            StringBuilder sb = new StringBuilder();
            for (byte b : d) sb.append(String.format(Locale.ROOT, "%02x", b));
            return sb.toString();
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException(e);
        }
    }

    private static String q(String s) { return "\"" + s.replace("\\", "\\\\").replace("\"", "'") + "\""; }

    private static void writeEnvironment(Path path, int reps, double limit, String started, String keysSha,
                                         long resolution, int[] sizes, List<SearchAlgorithm> algos,
                                         List<String> variants) throws IOException {
        Runtime rt = Runtime.getRuntime();
        List<String> algoNames = new ArrayList<>();
        for (SearchAlgorithm a : algos) algoNames.add(q(a.name()));
        List<String> variantNames = new ArrayList<>();
        for (String v : variants) variantNames.add(q(v));
        String json = "{\n"
                + "  \"lenguaje\": \"Java\",\n"
                + "  \"vm\": " + q(System.getProperty("java.vm.name")) + ",\n"
                + "  \"version\": " + q(System.getProperty("java.version")) + ",\n"
                + "  \"so\": " + q(System.getProperty("os.name") + " " + System.getProperty("os.version")
                        + " (" + System.getProperty("os.arch") + ")") + ",\n"
                + "  \"procesadores\": " + rt.availableProcessors() + ",\n"
                + "  \"heap_max_mb\": " + rt.maxMemory() / (1024 * 1024) + ",\n"
                + "  \"argumentos_jvm\": " + q(String.join(" ", ManagementFactory.getRuntimeMXBean().getInputArguments())) + ",\n"
                + "  \"reloj\": \"System.nanoTime()\",\n"
                + "  \"resolucion_reloj_ns\": " + resolution + ",\n"
                + "  \"calentamiento\": \"global " + Config.GLOBAL_WARMUP_ROUNDS + " pasadas n=" + Config.GLOBAL_WARMUP_N
                        + " + por caso hasta " + Config.CASE_WARMUP_TARGET_SECONDS + " s o "
                        + Config.CASE_WARMUP_MAX_RUNS + " pasadas (omitido si prediccion > "
                        + Config.CASE_WARMUP_SKIP_ABOVE_SECONDS + " s)\",\n"
                + "  \"claves\": " + q(Config.SEARCH_KEYS_FILE) + ",\n"
                + "  \"claves_sha256\": " + q(keysSha) + ",\n"
                + "  \"num_busquedas\": " + Config.NUM_SEARCH_KEYS + ",\n"
                + "  \"repeticiones\": " + reps + ",\n"
                + "  \"limite_s\": " + limit + ",\n"
                + "  \"tamanos\": " + Arrays.toString(sizes) + ",\n"
                + "  \"algoritmos\": [" + String.join(", ", algoNames) + "],\n"
                + "  \"variantes\": [" + String.join(", ", variantNames) + "],\n"
                + "  \"inicio_utc\": \"" + started + "\",\n"
                + "  \"fin_utc\": \"" + Instant.now().truncatedTo(ChronoUnit.SECONDS) + "\"\n"
                + "}\n";
        Files.write(path, json.getBytes(StandardCharsets.UTF_8));
    }
}
