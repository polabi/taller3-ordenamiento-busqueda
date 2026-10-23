package taller3.searching;

import taller3.common.Growth;

/**
 * Búsqueda lineal (referencia).
 * Fuente: GeeksforGeeks, "Linear Search Algorithm",
 *         https://www.geeksforgeeks.org/dsa/linear-search/
 * Equivalente línea a línea: python/taller3/searching/linear_search.py
 */
public final class LinearSearch implements SearchAlgorithm {
    @Override public String name() { return "LinearSearch"; }

    @Override public Growth growth() { return Growth.N; }

    @Override public int search(int[] arr, int x) {
        int n = arr.length;
        // No aprovecha el orden (como GfG): con duplicados devuelve la primera aparición
        for (int i = 0; i < n; i++) {
            if (arr[i] == x) return i;
        }
        return -1;
    }
}
