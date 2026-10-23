package taller3.searching;

import taller3.common.Growth;

/**
 * Búsqueda por saltos, salto m = floor(sqrt(n)).
 * Fuente: GeeksforGeeks, "Jump Search",
 *         https://www.geeksforgeeks.org/dsa/jump-search/
 * Desviación: si n == 0 se devuelve -1 de inmediato (GfG Java leería arr[-1] y lanzaría
 *   ArrayIndexOutOfBoundsException).
 * Equivalente línea a línea: python/taller3/searching/jump_search.py
 */
public final class JumpSearch implements SearchAlgorithm {
    @Override public String name() { return "JumpSearch"; }

    @Override public Growth growth() { return Growth.SQRTN; }

    @Override public int search(int[] arr, int x) {
        int n = arr.length;
        if (n == 0) return -1;
        // m entero (como GfG Java) para que la secuencia de índices sea la misma en Python
        int m = (int) Math.floor(Math.sqrt(n));
        int step = m;
        int prev = 0;
        // Salta bloques mientras el último elemento del bloque sea menor que x
        while (arr[Math.min(step, n) - 1] < x) {
            prev = step;
            step = step + m;
            if (prev >= n) return -1;
        }
        // Recorrido lineal dentro del bloque [prev, min(step, n))
        while (arr[prev] < x) {
            prev = prev + 1;
            if (prev == Math.min(step, n)) return -1;
        }
        if (arr[prev] == x) return prev;
        return -1;
    }
}
