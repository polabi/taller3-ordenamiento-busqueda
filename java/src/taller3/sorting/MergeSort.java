package taller3.sorting;

import taller3.common.Growth;
import taller3.common.Variant;

/**
 * Merge Sort (top-down, recursivo).
 * Fuente: GeeksforGeeks, "Merge Sort", https://www.geeksforgeeks.org/dsa/merge-sort/
 * Equivalente línea a línea: python/taller3/sorting/merge_sort.py
 */
public final class MergeSort implements SortAlgorithm {
    @Override public String name() { return "MergeSort"; }

    @Override public Growth growth(Variant v) { return Growth.NLOGN; }

    @Override public void sort(int[] arr) {
        sort(arr, 0, arr.length - 1);
    }

    private static void sort(int[] arr, int l, int r) {
        if (l < r) {
            int m = l + (r - l) / 2;
            sort(arr, l, m);
            sort(arr, m + 1, r);
            merge(arr, l, m, r);
        }
    }

    private static void merge(int[] arr, int l, int m, int r) {
        int n1 = m - l + 1;
        int n2 = r - m;

        // Arreglos temporales
        int[] L = new int[n1];
        int[] R = new int[n2];
        for (int i = 0; i < n1; ++i) L[i] = arr[l + i];
        for (int j = 0; j < n2; ++j) R[j] = arr[m + 1 + j];

        int i = 0, j = 0;
        int k = l;
        while (i < n1 && j < n2) {
            if (L[i] <= R[j]) {          // <= -> estable
                arr[k] = L[i];
                i++;
            } else {
                arr[k] = R[j];
                j++;
            }
            k++;
        }
        while (i < n1) {
            arr[k] = L[i];
            i++;
            k++;
        }
        while (j < n2) {
            arr[k] = R[j];
            j++;
            k++;
        }
    }
}
