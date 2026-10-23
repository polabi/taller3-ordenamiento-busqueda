package taller3.searching;

import taller3.common.Growth;

/**
 * Búsqueda binaria (iterativa).
 * Fuente: GeeksforGeeks, "Binary Search",
 *         https://www.geeksforgeeks.org/dsa/binary-search/
 * Equivalente línea a línea: python/taller3/searching/binary_search.py
 */
public final class BinarySearch implements SearchAlgorithm {
    @Override public String name() { return "BinarySearch"; }

    @Override public Growth growth() { return Growth.LOGN; }

    @Override public int search(int[] arr, int x) {
        return searchRange(arr, 0, arr.length - 1, x);
    }

    /** Binaria sobre el subrango cerrado [lo, hi]; la reutiliza ExponentialSearch. */
    public static int searchRange(int[] arr, int lo, int hi, int x) {
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;   // forma de GfG: evita el overflow de lo + hi
            if (arr[mid] == x) return mid;
            if (arr[mid] < x) lo = mid + 1;
            else hi = mid - 1;
        }
        return -1;
    }
}
