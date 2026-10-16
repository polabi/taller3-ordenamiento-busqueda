package taller3.sorting;

import taller3.common.Growth;
import taller3.common.Variant;

/**
 * Insertion Sort.
 * Fuente: GeeksforGeeks, "Insertion Sort Algorithm",
 *         https://www.geeksforgeeks.org/dsa/insertion-sort-algorithm/
 * Equivalente línea a línea: python/taller3/sorting/insertion_sort.py
 */
public final class InsertionSort implements SortAlgorithm {
    @Override public String name() { return "InsertionSort"; }

    @Override public Growth growth(Variant v) {
        return v == Variant.ASCENDENTE ? Growth.N : Growth.N2;
    }

    @Override public void sort(int[] arr) {
        int n = arr.length;
        for (int i = 1; i < n; ++i) {
            int key = arr[i];
            int j = i - 1;
            // Desplaza a la derecha los mayores que key
            while (j >= 0 && arr[j] > key) {
                arr[j + 1] = arr[j];
                j = j - 1;
            }
            arr[j + 1] = key;
        }
    }
}
