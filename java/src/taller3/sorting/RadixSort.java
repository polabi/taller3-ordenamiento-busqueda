package taller3.sorting;

import taller3.common.Growth;
import taller3.common.Variant;

/**
 * Radix Sort LSD en base 10, con Counting Sort estable por dígito.
 * Fuente: GeeksforGeeks, "Radix Sort", https://www.geeksforgeeks.org/dsa/radix-sort/
 * Equivalente línea a línea: python/taller3/sorting/radix_sort.py
 *
 * Con valores de 8 dígitos hace d = 8 pasadas. exp llega como máximo a 10^8 < 2^31: sin desbordamiento.
 */
public final class RadixSort implements SortAlgorithm {
    @Override public String name() { return "RadixSort"; }

    @Override public Growth growth(Variant v) { return Growth.N; }

    @Override public void sort(int[] arr) {
        int n = arr.length;
        if (n == 0) return;
        int m = getMax(arr, n);
        for (int exp = 1; m / exp > 0; exp *= 10) countSort(arr, n, exp);
    }

    private static int getMax(int[] arr, int n) {
        int mx = arr[0];
        for (int i = 1; i < n; i++) if (arr[i] > mx) mx = arr[i];
        return mx;
    }

    private static void countSort(int[] arr, int n, int exp) {
        int[] output = new int[n];
        int[] count = new int[10];

        for (int i = 0; i < n; i++) count[(arr[i] / exp) % 10]++;

        for (int i = 1; i < 10; i++) count[i] += count[i - 1];

        // De derecha a izquierda para que sea estable
        for (int i = n - 1; i >= 0; i--) {
            int d = (arr[i] / exp) % 10;
            output[count[d] - 1] = arr[i];
            count[d]--;
        }

        for (int i = 0; i < n; i++) arr[i] = output[i];
    }
}
