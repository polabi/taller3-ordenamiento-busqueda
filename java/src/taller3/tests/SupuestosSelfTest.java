package taller3.tests;

import java.io.Closeable;
import java.io.IOException;
import java.lang.reflect.Constructor;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.stream.Stream;

import taller3.common.Config;
import taller3.common.Growth;
import taller3.common.ResultRecord;
import taller3.sorting.BucketSort;

/**
 * Pruebas del Punto 3 en Java (experimento de supuestos; no miden tiempos ni corren el benchmark).
 *   java -cp java/out taller3.tests.SupuestosSelfTest
 * Valores esperados: specs/p3-comparativo.md, secciones 6.1, 6.4, 7.2 y 8 (APROBADA 2026-10-22).
 *
 * Lo que todavía no existe (Config.SUPUESTOS_*, DataIO.supuestosPath/readSupuestos,
 * SupuestosCsvWriter, SupuestosBenchmark) se usa por REFLEXIÓN: así este archivo compila
 * aunque falte la implementación (no rompe la compilación de java/src ni run_punto1.sh) y
 * cada comprobación FALLA en ejecución diciendo qué falta.
 *
 * Contrato que fijan estas pruebas (además de las firmas de la spec 6.1.5, 6.4 y 7.2):
 *   - public static Path  DataIO.supuestosPath(Path dataDir, String distribucion, int n)
 *   - public static int[] DataIO.readSupuestos(Path dataDir, String distribucion, int n) throws IOException
 *   - public static Growth SupuestosBenchmark.growth(String algoritmo, String distribucion)
 *   - public static Path  SupuestosBenchmark.environmentPath(Path out) = entorno_<stem>.json junto a out
 *   - SupuestosCsvWriter(Path, int repetitions) implements Closeable; write(ResultRecord, String distribucion)
 */
public final class SupuestosSelfTest {
    static int failures = 0, total = 0;

    static void check(boolean ok, String msg) {
        total++;
        if (!ok) { failures++; System.out.println("FALLA  " + msg); }
    }

    static final String GEN_MSG = "genera los datos: python3 -m taller3.generate_data";
    static final String CSV_HEADER =
        "algoritmo,lenguaje,variante,distribucion,n,rep_1_ns,rep_2_ns,rep_3_ns,rep_4_ns,rep_5_ns,"
        + "promedio_ns,desv_estandar_ns,estado,causa,base_estimacion";

    // ------------------------------------------------------------- reflexión
    static final class Missing extends Exception {
        Missing(String m) { super(m); }
    }

    static Class<?> cls(String name) throws Missing {
        try { return Class.forName(name); }
        catch (ClassNotFoundException e) { throw new Missing("falta implementar la clase " + name); }
    }

    static Object staticField(Class<?> c, String name) throws Missing {
        try { return c.getField(name).get(null); }
        catch (NoSuchFieldException | IllegalAccessException e) {
            throw new Missing("falta " + c.getSimpleName() + "." + name + " (public static)");
        }
    }

    static Method method(Class<?> c, String name, Class<?>... types) throws Missing {
        try { return c.getMethod(name, types); }
        catch (NoSuchMethodException e) {
            StringBuilder sig = new StringBuilder();
            for (Class<?> t : types) sig.append(sig.length() == 0 ? "" : ", ").append(t.getSimpleName());
            throw new Missing("falta public " + c.getSimpleName() + "." + name + "(" + sig + ")");
        }
    }

    static Object invoke(Method m, Object target, Object... args) throws Throwable {
        try { return m.invoke(target, args); }
        catch (InvocationTargetException e) { throw e.getCause(); }
    }

    interface Body { void run() throws Throwable; }

    static void test(String name, Body b) {
        try { b.run(); }
        catch (Missing m) { check(false, name + ": " + m.getMessage()); }
        catch (Throwable t) { check(false, name + ": excepción inesperada " + t); }
    }

    static void expectIAE(Body b, String msg, String mustContain) {
        try {
            b.run();
            check(false, msg + " (no lanzó)");
        } catch (IllegalArgumentException e) {
            check(mustContain == null || String.valueOf(e.getMessage()).contains(mustContain),
                    msg + " (mensaje: " + e.getMessage() + ")");
        } catch (Throwable t) {
            check(false, msg + " (lanzó " + t + ")");
        }
    }

    static void deleteTree(Path p) {
        if (p == null || !Files.exists(p)) return;
        try (Stream<Path> s = Files.walk(p)) {
            s.sorted(Comparator.reverseOrder()).forEach(q -> { try { Files.delete(q); } catch (IOException ignored) {} });
        } catch (IOException ignored) {}
    }

    // ------------------------------------------------------------------ main
    public static void main(String[] args) {
        // ---------------- 6.1.1 constantes de Config
        test("6.1.1 Config", () -> {
            Class<?> c = Config.class;
            check("p3".equals(staticField(c, "SUPUESTOS_SUBDIR")), "6.1.1 Config.SUPUESTOS_SUBDIR == \"p3\"");
            check(Arrays.equals((int[]) staticField(c, "SUPUESTOS_SIZES"), new int[]{10_000, 100_000}),
                    "6.1.1 Config.SUPUESTOS_SIZES == {10000, 100000}");
            check(Arrays.equals((String[]) staticField(c, "BUCKET_DISTRIBUTIONS"),
                    new String[]{"uniforme", "rango_pequeno", "concentrado_extremos"}),
                    "6.1.1 Config.BUCKET_DISTRIBUTIONS en orden");
        });

        // ---------------- 6.1.5 DataIO.supuestosPath
        test("6.1.5 supuestosPath", () -> {
            Method sp = method(cls("taller3.common.DataIO"), "supuestosPath", Path.class, String.class, int.class);
            Path d = Paths.get("data");
            check(d.resolve("aleatoria_10000.txt").equals(invoke(sp, null, d, "uniforme", 10_000)),
                    "6.1.5 supuestosPath(uniforme, 10000) == data/aleatoria_10000.txt");
            for (String dist : new String[]{"rango_pequeno", "concentrado_extremos"}) {
                check(d.resolve("p3").resolve(dist + "_100000.txt").equals(invoke(sp, null, d, dist, 100_000)),
                        "6.1.5 supuestosPath(" + dist + ", 100000) == data/p3/" + dist + "_100000.txt");
            }
            expectIAE(() -> invoke(sp, null, d, "digitos16", 10_000),
                    "6.1.5 supuestosPath(digitos16) -> IllegalArgumentException 'no cabe en int'", "no cabe en int");
            for (String bad : new String[]{"aleatoria", "Uniforme", "concentrado", ""}) {
                expectIAE(() -> invoke(sp, null, d, bad, 10_000),
                        "6.1.5 supuestosPath(\"" + bad + "\") -> IllegalArgumentException", null);
            }
        });

        // ---------------- 6.1.5 DataIO.readSupuestos (valida rango de 8 dígitos)
        test("6.1.5 readSupuestos", () -> {
            Method rs = method(cls("taller3.common.DataIO"), "readSupuestos", Path.class, String.class, int.class);
            Path tmp = Files.createTempDirectory("p3_lectura_");
            try {
                Files.createDirectories(tmp.resolve("p3"));
                Files.write(tmp.resolve("p3").resolve("rango_pequeno_3.txt"),
                        "10000000\n10000999\n10000500\n".getBytes(StandardCharsets.US_ASCII));
                check(Arrays.equals((int[]) invoke(rs, null, tmp, "rango_pequeno", 3),
                        new int[]{10_000_000, 10_000_999, 10_000_500}), "6.1.5 readSupuestos lee en orden");
                Files.write(tmp.resolve("p3").resolve("concentrado_extremos_2.txt"),
                        "10000000\n5\n".getBytes(StandardCharsets.US_ASCII));
                try {
                    invoke(rs, null, tmp, "concentrado_extremos", 2);
                    check(false, "6.1.5 readSupuestos fuera de rango -> IOException (no lanzó)");
                } catch (IOException e) {
                    check(true, "");
                }
            } finally { deleteTree(tmp); }
        });

        // ---------------- 7.2 SupuestosCsvWriter
        test("7.2 SupuestosCsvWriter", () -> {
            Class<?> wc = cls("taller3.common.SupuestosCsvWriter");
            Constructor<?> ctor;
            try { ctor = wc.getConstructor(Path.class, int.class); }
            catch (NoSuchMethodException e) { throw new Missing("falta SupuestosCsvWriter(Path, int)"); }
            Method write = method(wc, "write", ResultRecord.class, String.class);
            Path tmp = Files.createTempDirectory("p3_csv_");
            try {
                Path f = tmp.resolve("sup.csv");
                Object w = ctor.newInstance(f, 5);
                ResultRecord m = new ResultRecord("BucketSort", "Java", "aleatoria", 10_000);
                m.repsNs = new long[]{1, 2, 3, 4, 5};
                m.promedioNs = 3.0;
                m.desvEstandarNs = 1.5811388;
                invoke(write, w, m, "concentrado_extremos");
                ResultRecord e = new ResultRecord("BucketSort", "Java", "aleatoria", 100_000);
                e.promedioNs = 1234.56;
                e.estado = "estimado";
                e.causa = "predicción 400 s > límite, de 300 s";
                invoke(write, w, e, "rango_pequeno");
                ((Closeable) w).close();
                List<String> lines = Files.readAllLines(f, StandardCharsets.UTF_8);
                check(lines.size() == 3, "7.2 CSV con encabezado + 2 filas");
                check(CSV_HEADER.equals(lines.get(0)), "7.2 encabezado exacto: " + lines.get(0));
                check("BucketSort,Java,aleatoria,concentrado_extremos,10000,1,2,3,4,5,3.0,1.6,medido,,".equals(lines.get(1)),
                        "7.2 fila medida: " + lines.get(1));
                check("BucketSort,Java,aleatoria,rango_pequeno,100000,,,,,,1234.6,,estimado,\"predicción 400 s > límite, de 300 s\","
                        .equals(lines.get(2)), "7.2 fila estimada: " + lines.get(2));
            } finally { deleteTree(tmp); }
        });

        // ---------------- 6.4 growth
        test("6.4 SupuestosBenchmark.growth", () -> {
            Method g = method(cls("taller3.bench.SupuestosBenchmark"), "growth", String.class, String.class);
            check(invoke(g, null, "BucketSort", "uniforme") == Growth.N, "6.4 growth(BucketSort, uniforme) == N");
            check(invoke(g, null, "BucketSort", "rango_pequeno") == Growth.N, "6.4 growth(BucketSort, rango_pequeno) == N");
            check(invoke(g, null, "BucketSort", "concentrado_extremos") == Growth.N2,
                    "6.4 growth(BucketSort, concentrado_extremos) == N2");
            check(invoke(g, null, "RadixSort", "uniforme") == Growth.N, "6.4 growth(RadixSort, uniforme) == N");
            check(invoke(g, null, "RadixSort", "digitos16") == Growth.N, "6.4 growth(RadixSort, digitos16) == N");
            String[][] bad = {{"BucketSort", "digitos16"}, {"RadixSort", "rango_pequeno"}, {"MergeSort", "uniforme"}};
            for (String[] p : bad) {
                expectIAE(() -> invoke(g, null, p[0], p[1]),
                        "6.4 growth(" + p[0] + ", " + p[1] + ") -> IllegalArgumentException", null);
            }
        });

        // ---------------- 7.2 entorno
        test("7.2 SupuestosBenchmark.environmentPath", () -> {
            Method ep = method(cls("taller3.bench.SupuestosBenchmark"), "environmentPath", Path.class);
            check(Paths.get("results", "entorno_supuestos_java.json")
                    .equals(invoke(ep, null, Paths.get("results", "supuestos_java.csv"))),
                    "7.2 environmentPath(results/supuestos_java.csv) == results/entorno_supuestos_java.json");
            check(Paths.get("/tmp/x/entorno_prueba_sup.json").equals(invoke(ep, null, Paths.get("/tmp/x/prueba_sup.csv"))),
                    "7.2 environmentPath(--out distinto) == entorno_<stem>.json junto al CSV");
        });

        // ---------------- 8 BucketSort ordena los 4 archivos de 8 dígitos de data/p3/
        for (String dist : new String[]{"rango_pequeno", "concentrado_extremos"}) {
            for (int n : new int[]{10_000, 100_000}) {
                String name = "8 BucketSort " + dist + "_" + n;
                test(name, () -> {
                    Method rs = method(cls("taller3.common.DataIO"), "readSupuestos", Path.class, String.class, int.class);
                    Path f = Config.DATA_DIR.resolve("p3").resolve(dist + "_" + n + ".txt");
                    if (!Files.exists(f)) { check(false, name + ": no existe " + f + ": " + GEN_MSG); return; }
                    int[] base = (int[]) invoke(rs, null, Config.DATA_DIR, dist, n);
                    int[] expected = base.clone();
                    Arrays.sort(expected);
                    int[] work = base.clone();
                    new BucketSort().sort(work);
                    check(Arrays.equals(work, expected), name + " ordena igual que Arrays.sort");
                });
            }
        }

        System.out.printf("SupuestosSelfTest: %d/%d comprobaciones OK%n", total - failures, total);
        if (failures > 0) System.exit(1);
    }
}
