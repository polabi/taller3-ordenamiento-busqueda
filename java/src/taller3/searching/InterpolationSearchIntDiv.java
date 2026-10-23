package taller3.searching;

import taller3.common.Growth;

/**
 * Búsqueda por interpolación (iterativa), VARIANTE con la fórmula de división entera de los
 * códigos Java (ambas pestañas) y Python recursivo de GfG: ((hi - lo) / (arr[hi] - arr[lo])) se calcula antes de multiplicar.
 * Con valores de 8 dígitos y n <= 10^6 ese cociente es 0, pos = lo y la búsqueda es O(n)
 * (specs/p2-busqueda.md, 3.5.2).
 * Fuente: GeeksforGeeks, "Interpolation Search",
 *         https://www.geeksforgeeks.org/dsa/interpolation-search/
 * Desviación: guarda arr[lo] == arr[hi] (regla G de la spec, 3.5).
 * Equivalente línea a línea: python/taller3/searching/interpolation_search_int_div.py
 */
public final class InterpolationSearchIntDiv implements SearchAlgorithm {
    @Override public String name() { return "InterpolationSearchIntDiv"; }

    @Override public Growth growth() { return Growth.N; }

    @Override public int search(int[] arr, int x) {
        int n = arr.length;
        int lo = 0;
        int hi = n - 1;
        while (lo <= hi && x >= arr[lo] && x <= arr[hi]) {
            // Guarda G: arr[lo] <= x <= arr[hi] == arr[lo] implica x == arr[lo]
            if (arr[lo] == arr[hi]) return lo;
            // División entera de int; operandos >= 0, así que trunca igual que // de Python
            int pos = lo + ((hi - lo) / (arr[hi] - arr[lo])) * (x - arr[lo]);
            if (arr[pos] == x) return pos;
            if (arr[pos] < x) lo = pos + 1;
            else hi = pos - 1;
        }
        return -1;
    }
}
