package taller3.searching;

import taller3.common.Growth;

/**
 * Búsqueda por interpolación (iterativa), fórmula en double de los códigos C++ y C de GfG
 * (el Python iterativo de GfG usa la misma con float). Ojo: las pestañas Java de GfG usan
 * división entera; esa fórmula está en InterpolationSearchIntDiv.
 * Fuente: GeeksforGeeks, "Interpolation Search",
 *         https://www.geeksforgeeks.org/dsa/interpolation-search/
 * Desviación: guarda arr[lo] == arr[hi] (no solo lo == hi) para no dividir por 0 con
 * duplicados (specs/p2-busqueda.md, 3.5, regla G).
 * Equivalente línea a línea: python/taller3/searching/interpolation_search.py
 */
public final class InterpolationSearch implements SearchAlgorithm {
    @Override public String name() { return "InterpolationSearch"; }

    @Override public Growth growth() { return Growth.LOGLOGN; }

    @Override public int search(int[] arr, int x) {
        int n = arr.length;
        int lo = 0;
        int hi = n - 1;
        while (lo <= hi && x >= arr[lo] && x <= arr[hi]) {
            // Guarda G: arr[lo] <= x <= arr[hi] == arr[lo] implica x == arr[lo]
            if (arr[lo] == arr[hi]) return lo;
            // En double no hay producto entero que desborde; (int) trunca hacia cero
            int pos = lo + (int) (((double) (hi - lo) / (arr[hi] - arr[lo])) * (x - arr[lo]));
            if (arr[pos] == x) return pos;
            if (arr[pos] < x) lo = pos + 1;
            else hi = pos - 1;
        }
        return -1;
    }
}
