package taller3.tests;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Random;

import taller3.common.Config;
import taller3.searching.BinarySearch;
import taller3.searching.SearchAlgorithm;
import taller3.searching.SearchRegistry;

/**
 * Pruebas de corrección de los 7 algoritmos de búsqueda del Punto 2 (no miden tiempo).
 *   java -cp java/out taller3.tests.SearchSelfTest
 * Valores esperados: specs/p2-busqueda.md, secciones 4 y 5 (parte APROBADA 2026-10-20).
 * Cada caso lleva el nombre de la spec. Se comprueba validez (arr[i] == x o -1) e índice
 * exacto (D-extra), que el arreglo no se modifica, el orden del registro (2.1),
 * BinarySearch.searchRange (3.2) y la propiedad aleatoria de 5.7 contra Arrays.binarySearch.
 * Mismos casos que python/tests/test_searching.py.
 */
public final class SearchSelfTest {
    /** Orden del registro = columnas de la spec: Lin, Bin, Ter, Sal, Int (double), Exp, IDiv. */
    static final String[] EXPECTED_ORDER = {
        "LinearSearch", "BinarySearch", "TernarySearch", "JumpSearch",
        "InterpolationSearch", "ExponentialSearch", "InterpolationSearchIntDiv"
    };
    static final long PROPERTY_SEED = 20261020L;   // semilla fija de la prueba 5.7

    static final int[] A = {10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160};
    static final int[] D = {5, 7, 7, 7, 9, 12, 12, 15};
    static final int[] U = {1, 2, 3, 4, 5, 6, 7, 8, 9, 1000};
    static final int[] O = buildO();
    static final int[] F1 = {3, 52, 52};
    static final int[] F2 = {31, 54, 54, 59};
    static final int[] F3 = {1, 10, 20, 48};
    static final int[] ALL4 = {4, 4, 4, 4, 4};

    static int[] buildO() {
        int[] o = new int[100];
        for (int i = 0; i < 99; i++) o[i] = 10_000_000 + 909_090 * i;
        o[99] = 99_999_999;
        return o;
    }

    static final class Case {
        final String name; final int[] arr; final int x; final int[] expected;
        Case(String name, int[] arr, int x, int... expected) {
            this.name = name; this.arr = arr; this.x = x;
            this.expected = expected.length == 1 ? fill7(expected[0]) : expected;
        }
        static int[] fill7(int v) { int[] e = new int[7]; Arrays.fill(e, v); return e; }
    }

    static List<Case> cases() {
        List<Case> c = new ArrayList<>();
        // 5.1 Arreglo A
        c.add(new Case("A_x70_presente", A, 70, 6));
        c.add(new Case("A_x75_ausente_interior", A, 75, -1));
        c.add(new Case("A_x10_primero", A, 10, 0));
        c.add(new Case("A_x160_ultimo", A, 160, 15));
        c.add(new Case("A_x90", A, 90, 8));
        c.add(new Case("A_x130", A, 130, 12));
        c.add(new Case("A_x5_menor_que_minimo", A, 5, -1));
        c.add(new Case("A_x200_mayor_que_maximo", A, 200, -1));
        // 5.2 Arreglo D (duplicados)
        c.add(new Case("D_x7_duplicado", D, 7, 1, 3, 2, 1, 1, 3, 1));
        c.add(new Case("D_x12_duplicado", D, 12, 5));
        c.add(new Case("D_x5_primero", D, 5, 0));
        c.add(new Case("D_x15_ultimo", D, 15, 7));
        c.add(new Case("D_x8_ausente_interior", D, 8, -1));
        // 5.3 Arreglo U (no uniforme)
        c.add(new Case("U_x9", U, 9, 8));
        c.add(new Case("U_x1000", U, 1000, 9));
        c.add(new Case("U_x500_ausente", U, 500, -1));
        // 5.4 Mínimos y degenerados
        c.add(new Case("vacio_x1", new int[0], 1, -1));
        c.add(new Case("uno_x42_presente", new int[]{42}, 42, 0));
        c.add(new Case("uno_x41_menor", new int[]{42}, 41, -1));
        c.add(new Case("uno_x43_mayor", new int[]{42}, 43, -1));
        c.add(new Case("dos_iguales_x3_guarda", new int[]{3, 3}, 3, 0));
        c.add(new Case("dos_iguales_x2", new int[]{3, 3}, 2, -1));
        c.add(new Case("dos_iguales_x4", new int[]{3, 3}, 4, -1));
        c.add(new Case("todos_iguales_x4", ALL4, 4, 0, 2, 1, 0, 0, 0, 0));
        c.add(new Case("todos_iguales_x3", ALL4, 3, -1));
        c.add(new Case("todos_iguales_x5", ALL4, 5, -1));
        // 5.5 Arreglo O (8 dígitos, sin overflow)
        c.add(new Case("O_x31818160_sin_overflow", O, 31_818_160, 24));
        c.add(new Case("O_x31818161_ausente", O, 31_818_161, -1));
        c.add(new Case("O_x99090820", O, 99_090_820, 98));
        // Sección 4 sobre O: primer/último con valores reales extremos de 8 dígitos
        c.add(new Case("O_x10000000_primero", O, 10_000_000, 0));
        c.add(new Case("O_x99999999_ultimo", O, 99_999_999, 99));
        c.add(new Case("O_x9999999_menor", O, 9_999_999, -1));
        c.add(new Case("O_x100000000_mayor", O, 100_000_000, -1));
        // 5.6 Casos que distinguen las fórmulas (F1 y F2 obligatorios, 8.1)
        c.add(new Case("F1", F1, 52, 1, 1, 2, 1, 1, 2, 1));
        c.add(new Case("F2", F2, 54, 1, 1, 1, 1, 2, 2, 1));
        c.add(new Case("F3", F3, 48, 3));
        c.add(new Case("F3_prima", F3, 47, -1));
        c.add(new Case("F1_prima", F1, 3, 0));
        c.add(new Case("F1_biprima", F1, 51, -1));
        return c;
    }

    static int failures = 0, total = 0;

    static void check(boolean ok, String msg) {
        total++;
        if (!ok) { failures++; System.out.println("FALLA  " + msg); }
    }

    static boolean contains(int[] arr, int x) {
        for (int v : arr) if (v == x) return true;
        return false;
    }

    public static void main(String[] args) {
        // 2.1 Registro: orden y nombres
        List<SearchAlgorithm> all = SearchRegistry.ALL;
        check(all.size() == EXPECTED_ORDER.length, "registro: se esperaban 7 algoritmos, hay " + all.size());
        for (int k = 0; k < Math.min(all.size(), EXPECTED_ORDER.length); k++) {
            check(EXPECTED_ORDER[k].equals(all.get(k).name()),
                    "registro: posición " + k + " es " + all.get(k).name() + ", se esperaba " + EXPECTED_ORDER[k]);
            check(SearchRegistry.byName(EXPECTED_ORDER[k]) == all.get(k), "registro: byName(" + EXPECTED_ORDER[k] + ")");
        }

        // Secciones 4 y 5: validez + índice exacto
        List<Case> cs = cases();
        for (Case c : cs) {
            for (int k = 0; k < Math.min(all.size(), 7); k++) {
                SearchAlgorithm a = all.get(k);
                int exp = c.expected[k];
                int[] work = Arrays.copyOf(c.arr, c.arr.length);
                String id = a.name() + " / " + c.name + " (x=" + c.x + ")";
                int got;
                try {
                    got = a.search(work, c.x);
                } catch (RuntimeException e) {
                    check(false, id + ": excepción " + e);
                    continue;
                }
                check(Arrays.equals(work, c.arr), id + ": modificó el arreglo");
                if (exp == -1) {
                    check(!contains(c.arr, c.x), id + ": la spec dice -1 pero x está (error de la prueba)");
                    check(got == -1, id + ": esperado -1, obtuvo " + got);
                } else {
                    boolean valid = got >= 0 && got < c.arr.length && c.arr[got] == c.x;
                    check(valid, id + ": índice inválido " + got);
                    check(got == exp, id + ": esperado índice exacto " + exp + ", obtuvo " + got);
                }
            }
        }

        // 3.2 searchRange (traza de 5.1, rango [4, 8], y de 5.2)
        check(BinarySearch.searchRange(A, 4, 8, 70) == 6, "searchRange(A,4,8,70) == 6");
        check(BinarySearch.searchRange(A, 4, 8, 75) == -1, "searchRange(A,4,8,75) == -1");
        check(BinarySearch.searchRange(A, 4, 8, 10) == -1, "searchRange(A,4,8,10) == -1 (fuera del rango)");
        check(BinarySearch.searchRange(A, 0, -1, 10) == -1, "searchRange(A,0,-1,10) == -1 (rango vacío)");
        check(BinarySearch.searchRange(D, 2, 4, 7) == 3, "searchRange(D,2,4,7) == 3");

        // 5.7 Propiedad aleatoria contra Arrays.binarySearch
        Random rng = new Random(PROPERTY_SEED);
        int span = Config.MAX_VALUE - Config.MIN_VALUE + 1;
        int[] arr = new int[3000];
        for (int i = 0; i < arr.length; i++) arr[i] = Config.MIN_VALUE + rng.nextInt(span);
        Arrays.sort(arr);
        for (int t = 0; t < 300; t++) { int j = 1 + rng.nextInt(arr.length - 1); arr[j] = arr[j - 1]; }
        for (int j = 1500; j < 1520; j++) arr[j] = arr[1499];
        for (int j = 2990; j < 3000; j++) arr[j] = arr[2989];
        int[] keys = new int[2004];
        for (int i = 0; i < 1000; i++) keys[i] = arr[rng.nextInt(arr.length)];
        for (int i = 1000; i < 2000; i++) keys[i] = Config.MIN_VALUE + rng.nextInt(span);
        keys[2000] = arr[0]; keys[2001] = arr[arr.length - 1];
        keys[2002] = Config.MIN_VALUE; keys[2003] = Config.MAX_VALUE;
        int[] snapshot = Arrays.copyOf(arr, arr.length);
        for (SearchAlgorithm a : all) {
            int bad = 0;
            String first = null;
            for (int x : keys) {
                boolean present = Arrays.binarySearch(arr, x) >= 0;
                int got;
                try { got = a.search(arr, x); } catch (RuntimeException e) { got = Integer.MIN_VALUE; }
                boolean ok = present ? (got >= 0 && got < arr.length && arr[got] == x) : got == -1;
                if (ok && present && a.name().equals("LinearSearch")) ok = got == firstIndex(arr, x);
                if (!ok) { bad++; if (first == null) first = "x=" + x + " -> " + got; }
            }
            check(bad == 0, a.name() + " / aleatorio_5.7: " + bad + " claves fallaron (p. ej. " + first + ")");
        }
        check(Arrays.equals(arr, snapshot), "aleatorio_5.7: algún algoritmo modificó el arreglo");

        System.out.println(failures == 0
                ? "OK: " + total + " comprobaciones superadas (" + all.size() + " algoritmos x " + cs.size()
                  + " casos a mano + searchRange + aleatorio 5.7)"
                : failures + " de " + total + " comprobaciones fallaron");
        if (failures > 0) System.exit(1);
    }

    /** Primera aparición (oráculo propio para LinearSearch: cota inferior). */
    static int firstIndex(int[] arr, int x) {
        int lo = 0, hi = arr.length;
        while (lo < hi) { int m = (lo + hi) >>> 1; if (arr[m] < x) lo = m + 1; else hi = m; }
        return lo;
    }
}
