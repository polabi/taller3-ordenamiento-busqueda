package taller3.sorting;

import java.util.ArrayList;

import taller3.common.Growth;
import taller3.common.Variant;

/**
 * Bucket Sort para enteros.
 * Fuente: GeeksforGeeks, "Bucket Sort", https://www.geeksforgeeks.org/dsa/bucket-sort-2/
 * Equivalente línea a línea: python/taller3/sorting/bucket_sort.py
 *
 * Adaptación documentada (GfG supone flotantes en [0,1) con índice floor(x·n)):
 *     número de cubetas:  k = n
 *     asignación:         idx(x) = floor( (x - min) · k / (max - min + 1) )
 * El producto se hace en long: (x - min) ≤ 9·10^7 y k ≤ 10^6 → hasta 9·10^13, no cabe en int.
 * Cada cubeta se ordena con Insertion Sort (como en GfG). Estable.
 *
 * Nota de rendimiento para el análisis: las cubetas son ArrayList<Integer> (como en
 * GfG Java), lo que implica "boxing" de cada int en un objeto Integer y ~n objetos
 * ArrayList. Ese costo constante NO aparece en la notación O(n) pero sí en el tiempo.
 */
public final class BucketSort implements SortAlgorithm {
    @Override public String name() { return "BucketSort"; }

    @Override public Growth growth(Variant v) { return Growth.N; }

    @Override public void sort(int[] arr) {
        int n = arr.length;
        if (n <= 1) return;

        int min = arr[0];
        int max = arr[0];
        for (int i = 1; i < n; i++) {
            if (arr[i] < min) min = arr[i];
            if (arr[i] > max) max = arr[i];
        }

        int k = n;                                  // número de cubetas
        long rango = (long) max - min + 1;
        @SuppressWarnings({"unchecked", "rawtypes"})
        ArrayList<Integer>[] buckets = new ArrayList[k];
        for (int i = 0; i < k; i++) buckets[i] = new ArrayList<>();

        for (int i = 0; i < n; i++) {
            int idx = (int) ((long) (arr[i] - min) * k / rango);
            buckets[idx].add(arr[i]);
        }

        int pos = 0;
        for (ArrayList<Integer> b : buckets) {
            insertionSort(b);
            for (int v : b) arr[pos++] = v;
        }
    }

    private static void insertionSort(ArrayList<Integer> b) {
        for (int i = 1; i < b.size(); i++) {
            int key = b.get(i);
            int j = i - 1;
            while (j >= 0 && b.get(j) > key) {
                b.set(j + 1, b.get(j));
                j--;
            }
            b.set(j + 1, key);
        }
    }
}
