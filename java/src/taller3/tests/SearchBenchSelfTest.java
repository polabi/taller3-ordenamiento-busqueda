package taller3.tests;

import java.io.IOException;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Comparator;
import java.util.List;
import java.util.Locale;
import java.util.stream.Stream;

import taller3.common.Config;
import taller3.common.CsvResultWriter;
import taller3.common.Growth;
import taller3.common.ResultRecord;
import taller3.searching.SearchAlgorithm;

/**
 * Pruebas del PROTOCOLO del Punto 2 en Java (no miden tiempos reales ni corren el benchmark).
 *   java -cp java/out taller3.tests.SearchBenchSelfTest
 * Valores esperados: specs/p2-busqueda.md, secciones 6 y 7 (APROBADAS 2026-10-22).
 *
 * Lo que todavía no existe (Config.SEARCH_*, DataIO.readSearchKeys, SearchBenchmark,
 * SearchResultRecord, SearchCsvWriter) se usa por REFLEXIÓN: así este archivo compila
 * aunque falte la implementación (no rompe la compilación de java/src ni run_punto1.sh) y
 * cada comprobación FALLA en ejecución diciendo qué falta. Mismos casos que
 * python/tests/test_search_protocol.py (salvo la generación de claves, que es solo Python).
 *
 * Contrato que fijan estas pruebas (además de las firmas de la spec 6.1.6, 6.2 y 6.3):
 *   - public static int[] DataIO.readSearchKeys(Path dataDir) throws IOException
 *   - public static int  SearchBenchmark.positionIndex(String variante, int n)  (IllegalArgumentException si no existe)
 *   - public static long SearchBenchmark.timeSearches(SearchAlgorithm, int[] arr, int[] keys, int[] out)
 *   - public static Path SearchBenchmark.environmentPath(Path out)  = entorno_<stem>.json junto a out
 *   - SearchResultRecord(String algoritmo, String lenguaje, String variante, int n) con campos públicos
 *     numBusquedas (int), clave (Integer), repsNs (long[]), promedioNs (Double), desvEstandarNs (Double),
 *     encontradas (Integer), checksum (Long), estado, causa, baseEstimacion (String)
 *   - SearchCsvWriter(Path, int repetitions) implements Closeable; write(SearchResultRecord)
 */
public final class SearchBenchSelfTest {
    static int failures = 0, total = 0;

    static void check(boolean ok, String msg) {
        total++;
        if (!ok) { failures++; System.out.println("FALLA  " + msg); }
    }

    static final String CSV_HEADER =
        "algoritmo,lenguaje,variante,n,num_busquedas,clave,rep_1_ns,rep_2_ns,rep_3_ns,rep_4_ns,"
        + "rep_5_ns,promedio_ns,desv_estandar_ns,promedio_por_busqueda_ns,desv_por_busqueda_ns,"
        + "encontradas,checksum,estado,causa,base_estimacion";
    static final String P1_CSV_HEADER =
        "algoritmo,lenguaje,variante,n,rep_1_ns,rep_2_ns,rep_3_ns,rep_4_ns,rep_5_ns,"
        + "promedio_ns,desv_estandar_ns,estado,causa,base_estimacion";

    // ------------------------------------------------------------- reflexión
    /** Excepción interna: "falta implementar X" (se reporta como FALLA, no aborta las demás). */
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
            throw new Missing("falta public static " + c.getSimpleName() + "." + name + "(" + sig + ")");
        }
    }

    /** Invoca un método estático y desenvuelve la excepción real. */
    static Object invoke(Method m, Object... args) throws Throwable {
        try { return m.invoke(null, args); }
        catch (InvocationTargetException e) { throw e.getCause(); }
    }

    static void setField(Object o, String name, Object value) throws Missing {
        try {
            Field f = o.getClass().getField(name);
            f.set(o, value);
        } catch (NoSuchFieldException | IllegalAccessException e) {
            throw new Missing("falta el campo público " + o.getClass().getSimpleName() + "." + name);
        }
    }

    interface Body { void run() throws Throwable; }

    static void test(String name, Body b) {
        try { b.run(); }
        catch (Missing m) { check(false, name + ": " + m.getMessage()); }
        catch (Throwable t) { check(false, name + ": excepción inesperada " + t); }
    }

    // ------------------------------------------------------------- utilidades
    static Path tmpDir(String prefix) throws IOException { return Files.createTempDirectory(prefix); }

    static void deleteTree(Path p) {
        if (p == null || !Files.exists(p)) return;
        try (Stream<Path> s = Files.walk(p)) {
            s.sorted(Comparator.reverseOrder()).forEach(q -> { try { Files.delete(q); } catch (IOException ignored) {} });
        } catch (IOException ignored) {}
    }

    static void writeInts(Path file, int[] values) throws IOException {
        StringBuilder sb = new StringBuilder();
        for (int v : values) sb.append(v).append('\n');
        Files.write(file, sb.toString().getBytes(StandardCharsets.US_ASCII));
    }

    static int[] validKeys(int count) {
        int[] v = new int[count];
        for (int i = 0; i < count; i++) v[i] = Config.MIN_VALUE + 7 * (count - 1 - i);   // distintas, en rango
        return v;
    }

    /** Búsqueda espía: cuenta llamadas y registra el orden de las claves. */
    static final class SpySearch implements SearchAlgorithm {
        final List<Integer> calls = new ArrayList<>();
        public String name() { return "Spy"; }
        public Growth growth() { return Growth.N; }
        public int search(int[] arr, int x) {
            calls.add(x);
            for (int i = 0; i < arr.length; i++) if (arr[i] == x) return i;
            return -1;
        }
    }

    // ------------------------------------------------------------------ main
    public static void main(String[] args) {
        // ---------------- 7.1 constantes de Config
        test("7.1 Config", () -> {
            Class<?> c = Config.class;
            check("claves_busqueda.txt".equals(staticField(c, "SEARCH_KEYS_FILE")), "Config.SEARCH_KEYS_FILE");
            check(Integer.valueOf(1000).equals(staticField(c, "NUM_SEARCH_KEYS")), "Config.NUM_SEARCH_KEYS == 1000");
            check(Integer.valueOf(500).equals(staticField(c, "NUM_PRESENT_KEYS")), "Config.NUM_PRESENT_KEYS == 500");
            check(Integer.valueOf(1_000_000).equals(staticField(c, "POSITION_N")), "Config.POSITION_N == 1000000");
            check(Arrays.equals((String[]) staticField(c, "POSITION_VARIANTS"),
                    new String[]{"inicio", "centro", "centro_alto", "final"}), "Config.POSITION_VARIANTS");
            check(Arrays.equals((String[]) staticField(c, "SEARCH_VARIANTS"),
                    new String[]{"claves", "inicio", "centro", "centro_alto", "final"}), "Config.SEARCH_VARIANTS");
        });

        // ---------------- 6.5 Growth (ya implementado; regresión)
        check(Math.abs(Growth.LOGN.f(1024) - 10.0) < 1e-12, "6.5 Growth.LOGN.f(1024) == 10");
        check(Math.abs(Growth.SQRTN.f(1_000_000) - 1000.0) < 1e-9, "6.5 Growth.SQRTN.f(10^6) == 1000");
        check(Math.abs(Growth.LOGLOGN.f(65536) - 4.0) < 1e-12, "6.5 Growth.LOGLOGN.f(2^16) == 4");
        check(Growth.N.f(1000) == 1000.0, "6.5 Growth.N sin cambios");

        // ---------------- 6.1.6 DataIO.readSearchKeys
        test("6.1.6 readSearchKeys", () -> {
            Method read = method(cls("taller3.common.DataIO"), "readSearchKeys", Path.class);
            Path tmp = tmpDir("p2_lectura_");
            try {
                Path f = tmp.resolve("claves_busqueda.txt");
                int[] valid = validKeys(1000);
                writeInts(f, valid);
                check(Arrays.equals((int[]) invoke(read, tmp), valid), "6.1.6 readSearchKeys válido conserva el orden");

                int[] dup = validKeys(1000); dup[999] = dup[0];
                writeInts(f, dup);
                expectIOException(read, tmp, "6.1.6 readSearchKeys con repetidas -> IOException");

                for (int count : new int[]{999, 1001}) {
                    writeInts(f, validKeys(count));
                    expectIOException(read, tmp, "6.1.6 readSearchKeys con " + count + " valores -> IOException");
                }
                for (int bad : new int[]{Config.MIN_VALUE - 1, Config.MAX_VALUE + 1}) {
                    int[] v = validKeys(1000); v[500] = bad;
                    writeInts(f, v);
                    expectIOException(read, tmp, "6.1.6 readSearchKeys fuera de rango (" + bad + ") -> IOException");
                }
                Files.delete(f);
                expectIOException(read, tmp, "6.1.6 readSearchKeys archivo inexistente -> IOException");
            } finally { deleteTree(tmp); }
        });

        // ---------------- 6.2 positionIndex
        test("6.2 positionIndex", () -> {
            Method pi = method(cls("taller3.bench.SearchBenchmark"), "positionIndex", String.class, int.class);
            int n = 1_000_000;
            check((int) invoke(pi, "inicio", n) == 0, "6.2 positionIndex(inicio, 10^6) == 0");
            check((int) invoke(pi, "centro", n) == 499_999, "6.2 positionIndex(centro, 10^6) == 499999");
            check((int) invoke(pi, "centro_alto", n) == 500_000, "6.2 positionIndex(centro_alto, 10^6) == 500000");
            check((int) invoke(pi, "final", n) == 999_999, "6.2 positionIndex(final, 10^6) == 999999");
            check((int) invoke(pi, "centro", 1000) == 499 && (int) invoke(pi, "centro_alto", 1000) == 500,
                    "6.2 positionIndex centros n=1000 -> 499 / 500");
            check((int) invoke(pi, "centro", 7) == 3 && (int) invoke(pi, "centro_alto", 7) == 3
                    && (int) invoke(pi, "final", 7) == 6, "6.2 positionIndex n=7 (impar) -> 3 / 3 / 6");
            for (String bad : new String[]{"claves", "medio", "Centro", ""}) {
                boolean threw = false;
                try { invoke(pi, bad, n); } catch (IllegalArgumentException e) { threw = true; }
                check(threw, "6.2 positionIndex(\"" + bad + "\") -> IllegalArgumentException");
            }
        });

        // ---------------- 6.3 timeSearches
        test("6.3 timeSearches", () -> {
            Method ts = method(cls("taller3.bench.SearchBenchmark"), "timeSearches",
                    SearchAlgorithm.class, int[].class, int[].class, int[].class);
            check(ts.getReturnType() == long.class, "6.3 timeSearches devuelve long (ns)");
            int[] arr = {10, 20, 30, 40, 50};
            int[] snapshot = arr.clone();
            int[] keys = {30, 5, 50, 10, 99, 40};
            int[] out = new int[keys.length];
            Arrays.fill(out, Integer.MIN_VALUE);
            SpySearch spy = new SpySearch();
            long ns = (long) invoke(ts, spy, arr, keys, out);
            check(ns >= 0, "6.3 timeSearches devuelve ns >= 0");
            check(Arrays.equals(out, new int[]{2, -1, 4, 0, -1, 3}), "6.3 out[j] = search(arr, keys[j]): " + Arrays.toString(out));
            List<Integer> expectedCalls = new ArrayList<>();
            for (int k : keys) expectedCalls.add(k);
            check(spy.calls.equals(expectedCalls), "6.3 una llamada por clave, en orden j = 0..K-1: " + spy.calls);
            check(Arrays.equals(arr, snapshot), "6.3 timeSearches no copia ni modifica arr");
        });

        // ---------------- 7.2 entorno
        test("7.2 environmentPath", () -> {
            Method ep = method(cls("taller3.bench.SearchBenchmark"), "environmentPath", Path.class);
            Path def = Paths.get("results", "busqueda_java.csv");
            check(Paths.get("results", "entorno_busqueda_java.json").equals(invoke(ep, def)),
                    "7.2 entorno por defecto = results/entorno_busqueda_java.json");
            check(Paths.get("results", "entorno_prueba_busq.json").equals(invoke(ep, Paths.get("results", "prueba_busq.csv"))),
                    "7.2 con --out results/prueba_busq.csv -> results/entorno_prueba_busq.json");
        });

        // ---------------- 7.2 CSV de búsqueda
        test("7.2 SearchCsvWriter", () -> {
            Class<?> recC = cls("taller3.common.SearchResultRecord");
            Class<?> wC = cls("taller3.common.SearchCsvWriter");
            Constructor<?> recNew;
            Constructor<?> wNew;
            try {
                recNew = recC.getConstructor(String.class, String.class, String.class, int.class);
                wNew = wC.getConstructor(Path.class, int.class);
            } catch (NoSuchMethodException e) {
                throw new Missing("constructores SearchResultRecord(String,String,String,int) / SearchCsvWriter(Path,int)");
            }
            Method write;
            try { write = wC.getMethod("write", recC); }
            catch (NoSuchMethodException e) { throw new Missing("SearchCsvWriter.write(SearchResultRecord)"); }

            Object medido = recNew.newInstance("BinarySearch", "Java", "claves", 1000);
            setField(medido, "numBusquedas", 1000);
            setField(medido, "clave", null);
            setField(medido, "repsNs", new long[]{1_000_000, 1_100_000, 1_200_000, 1_300_000, 1_400_000});
            setField(medido, "promedioNs", 1_234_567.89);
            setField(medido, "desvEstandarNs", 158_113.883);
            setField(medido, "encontradas", 500);
            setField(medido, "checksum", 249_971L);
            setField(medido, "estado", "medido");

            Object posicion = recNew.newInstance("LinearSearch", "Java", "final", 1_000_000);
            setField(posicion, "numBusquedas", 1000);
            setField(posicion, "clave", 99_999_964);
            setField(posicion, "repsNs", new long[]{5, 5, 5, 5, 5});
            setField(posicion, "promedioNs", 5.0);
            setField(posicion, "desvEstandarNs", 0.0);
            setField(posicion, "encontradas", 1000);
            setField(posicion, "checksum", 999_999_000L);
            setField(posicion, "estado", "medido");

            Object estimado = recNew.newInstance("LinearSearch", "Java", "claves", 1_000_000);
            setField(estimado, "numBusquedas", 1000);
            setField(estimado, "repsNs", new long[0]);
            setField(estimado, "promedioNs", 4.0e11);
            setField(estimado, "desvEstandarNs", null);
            setField(estimado, "encontradas", null);
            setField(estimado, "checksum", null);
            setField(estimado, "estado", "estimado");
            setField(estimado, "causa", "predicción 400.0 s > límite 300 s");
            setField(estimado, "baseEstimacion", "t(100000)=40.0 s x f(1000000)/f(100000) = x10 con f=O(n)");

            Object negativo = recNew.newInstance("LinearSearch", "Java", "claves", 1000);
            setField(negativo, "numBusquedas", 1000);
            setField(negativo, "repsNs", new long[]{1, 1, 1, 1, 1});
            setField(negativo, "promedioNs", 1.0);
            setField(negativo, "desvEstandarNs", 0.0);
            setField(negativo, "encontradas", 0);
            setField(negativo, "checksum", -1000L);
            setField(negativo, "estado", "medido");

            Locale prev = Locale.getDefault();
            Locale.setDefault(Locale.GERMANY);                 // coma decimal: debe usarse Locale.ROOT
            Path tmp = tmpDir("p2_csv_");
            try {
                Path csv = tmp.resolve("b.csv");
                Object w = wNew.newInstance(csv, 5);
                try {
                    write.invoke(w, medido);
                    List<String> afterOne = Files.readAllLines(csv, StandardCharsets.UTF_8);
                    check(afterOne.size() == 2, "7.2 la fila se vacía a disco al escribirse (antes de close)");
                    write.invoke(w, posicion);
                    write.invoke(w, estimado);
                    write.invoke(w, negativo);
                } finally {
                    ((java.io.Closeable) w).close();
                }
                List<String> lines = Files.readAllLines(csv, StandardCharsets.UTF_8);
                check(lines.size() == 5, "7.2 encabezado + 4 filas, hay " + lines.size());
                check(CSV_HEADER.equals(lines.get(0)), "7.2 encabezado exacto: " + lines.get(0));
                expectLine(lines, 1, "BinarySearch,Java,claves,1000,1000,,1000000,1100000,1200000,1300000,1400000,"
                        + "1234567.9,158113.9,1234.568,158.114,500,249971,medido,,", "7.2 fila claves medida");
                expectLine(lines, 2, "LinearSearch,Java,final,1000000,1000,99999964,5,5,5,5,5,"
                        + "5.0,0.0,0.005,0.000,1000,999999000,medido,,", "7.2 fila de posición con clave");
                expectLine(lines, 3, "LinearSearch,Java,claves,1000000,1000,,,,,,,400000000000.0,,400000000.000,,,,"
                        + "estimado,predicción 400.0 s > límite 300 s,t(100000)=40.0 s x f(1000000)/f(100000) = x10 con f=O(n)",
                        "7.2 fila estimada (reps, desv, encontradas y checksum vacíos)");
                expectLine(lines, 4, "LinearSearch,Java,claves,1000,1000,,1,1,1,1,1,1.0,0.0,0.001,0.000,0,-1000,medido,,",
                        "7.2 checksum negativo (incluye los -1)");
            } finally {
                Locale.setDefault(prev);
                deleteTree(tmp);
            }
        });

        // ---------------- 7.1 escritor del Punto 1 sin cambios (regresión)
        test("7.1 CsvResultWriter P1", () -> {
            Path tmp = tmpDir("p1_csv_");
            try {
                Path csv = tmp.resolve("p1.csv");
                try (CsvResultWriter w = new CsvResultWriter(csv, 5)) {
                    ResultRecord r = new ResultRecord("MergeSort", "Java", "aleatoria", 1000);
                    r.repsNs = new long[]{1, 2, 3, 4, 5};
                    r.promedioNs = 3.0;
                    r.desvEstandarNs = 1.58113883;
                    w.write(r);
                }
                List<String> lines = Files.readAllLines(csv, StandardCharsets.UTF_8);
                check(P1_CSV_HEADER.equals(lines.get(0)), "7.1 encabezado del Punto 1 sin cambios");
                check("MergeSort,Java,aleatoria,1000,1,2,3,4,5,3.0,1.6,medido,,".equals(lines.get(1)),
                        "7.1 fila del Punto 1 sin cambios: " + lines.get(1));
            } finally { deleteTree(tmp); }
        });

        System.out.println(failures == 0
                ? "OK: " + total + " comprobaciones de protocolo superadas"
                : failures + " de " + total + " comprobaciones fallaron");
        if (failures > 0) System.exit(1);
    }

    static void expectIOException(Method read, Path dir, String msg) {
        boolean threw = false;
        try { invoke(read, dir); }
        catch (IOException e) { threw = true; }
        catch (Throwable t) { check(false, msg + " (lanzó " + t + ")"); return; }
        check(threw, msg);
    }

    static void expectLine(List<String> lines, int i, String expected, String msg) {
        String got = i < lines.size() ? lines.get(i) : "<sin línea>";
        check(expected.equals(got), msg + "\n         esperado: " + expected + "\n         obtenido: " + got);
    }
}
