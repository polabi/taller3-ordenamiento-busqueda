package taller3.searching;

import taller3.common.Growth;

/**
 * Búsqueda ternaria (iterativa).
 * Fuente: GeeksforGeeks, "Ternary Search",
 *         https://www.geeksforgeeks.org/dsa/ternary-search/
 * Desviaciones respecto a GfG: (1) GfG devuelve boolean con
 *   if (arr[mid1] == x || arr[mid2] == x) return true; aquí se devuelve el índice, así que
 *   la condición se separa en dos if (primero mid1, luego mid2), lo que fija qué índice se
 *   devuelve cuando hay duplicados; (2) si no se encuentra se devuelve -1.
 * Equivalente línea a línea: python/taller3/searching/ternary_search.py
 */
public final class TernarySearch implements SearchAlgorithm {
    @Override public String name() { return "TernarySearch"; }

    @Override public Growth growth() { return Growth.LOGN; }

    @Override public int search(int[] arr, int x) {
        int n = arr.length;
        int l = 0;
        int r = n - 1;
        while (r >= l) {
            int mid1 = l + (r - l) / 3;
            int mid2 = r - (r - l) / 3;
            if (arr[mid1] == x) return mid1;
            if (arr[mid2] == x) return mid2;
            if (x < arr[mid1]) {
                r = mid1 - 1;
            } else if (x > arr[mid2]) {
                l = mid2 + 1;
            } else {
                l = mid1 + 1;
                r = mid2 - 1;
            }
        }
        return -1;
    }
}
