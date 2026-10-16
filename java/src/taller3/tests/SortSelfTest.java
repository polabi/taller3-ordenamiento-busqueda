package taller3.tests;

import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Random;

import taller3.common.Config;
import taller3.sorting.SortAlgorithm;
import taller3.sorting.SortRegistry;

/**
 * Pruebas de corrección de los 6 algoritmos (no miden tiempo). Oráculo: Arrays.sort.
 *   java -cp java/out taller3.tests.SortSelfTest
 * Mismos casos borde que python/tests/test_sorting.py.
 */
public final class SortSelfTest {
    public static void main(String[] args) {
        Random rng = new Random(123);
        int[] rand = new int[3000];
        for (int i = 0; i < rand.length; i++) rand[i] = Config.MIN_VALUE + rng.nextInt(Config.MAX_VALUE - Config.MIN_VALUE + 1);
        int[] choices = {10_000_000, 55_555_555, 99_999_999};
        int[] few = new int[500];
        for (int i = 0; i < few.length; i++) few[i] = choices[rng.nextInt(3)];
        int[] asc = Arrays.copyOf(rand, 900);
        Arrays.sort(asc);
        int[] desc = new int[asc.length];
        for (int i = 0; i < asc.length; i++) desc[i] = asc[asc.length - 1 - i];
        int[] same = new int[300];
        Arrays.fill(same, 12_345_678);
        int[] extremes = new int[100];
        for (int i = 0; i < extremes.length; i++) extremes[i] = (i % 2 == 0) ? Config.MAX_VALUE : Config.MIN_VALUE;

        Map<String, int[]> cases = new LinkedHashMap<>();
        cases.put("vacio", new int[0]);
        cases.put("uno", new int[]{42_000_000});
        cases.put("dos_invertidos", new int[]{99_999_999, 10_000_000});
        cases.put("todos_iguales", same);
        cases.put("pocos_valores_distintos", few);
        cases.put("ascendente", asc);
        cases.put("descendente", desc);
        cases.put("aleatorio_3000", rand);
        cases.put("extremos_del_rango", extremes);

        int failures = 0, total = 0;
        for (SortAlgorithm a : SortRegistry.ALL) {
            for (Map.Entry<String, int[]> c : cases.entrySet()) {
                total++;
                int[] work = Arrays.copyOf(c.getValue(), c.getValue().length);
                int[] expected = Arrays.copyOf(c.getValue(), c.getValue().length);
                Arrays.sort(expected);
                a.sort(work);
                if (!Arrays.equals(work, expected)) {
                    failures++;
                    System.out.println("FALLA  " + a.name() + " / " + c.getKey());
                }
            }
        }
        System.out.println(failures == 0
                ? "OK: " + total + " pruebas superadas (" + SortRegistry.ALL.size() + " algoritmos x " + cases.size() + " casos)"
                : failures + " de " + total + " pruebas fallaron");
        if (failures > 0) System.exit(1);
    }
}
