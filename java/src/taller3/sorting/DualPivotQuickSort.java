package taller3.sorting;

import taller3.common.Growth;
import taller3.common.Variant;

/**
 * Dual-Pivot QuickSort con pivotes en el PRIMER y el ÚLTIMO elemento.
 * Fuente: GeeksforGeeks, "Dual pivot Quicksort",
 *         https://www.geeksforgeeks.org/dsa/dual-pivot-quicksort/
 * Equivalente línea a línea: python/taller3/sorting/dual_pivot_quicksort.py
 *
 * OJO: NO es Arrays.sort(int[]) (que usa el Dual-Pivot de Yaroslavskiy con pivotes
 * elegidos entre 5 candidatos). Aquí los pivotes son los extremos, como pide el taller.
 * Con entrada ascendente o descendente la recursión llega a profundidad ~n/2 y el
 * tiempo es O(n²). Con la pila por defecto del hilo (-Xss, típicamente 1 MB en macOS/Linux de 64 bits)
 * se espera StackOverflowError a partir de algún n entre 10^4 y 10^5. NO se
 * aumenta -Xss a propósito: el taller pide documentar el fallo.
 */
public final class DualPivotQuickSort implements SortAlgorithm {
    @Override public String name() { return "DualPivotQuickSort"; }

    @Override public Growth growth(Variant v) {
        return v == Variant.ALEATORIA ? Growth.NLOGN : Growth.N2;
    }

    @Override public void sort(int[] arr) {
        sort(arr, 0, arr.length - 1);
    }

    private static void sort(int[] arr, int low, int high) {
        if (low < high) {
            int[] piv = partition(arr, low, high);
            sort(arr, low, piv[0] - 1);
            sort(arr, piv[0] + 1, piv[1] - 1);
            sort(arr, piv[1] + 1, high);
        }
    }

    private static int[] partition(int[] arr, int low, int high) {
        if (arr[low] > arr[high]) swap(arr, low, high);

        int j = low + 1;          // fin de la zona  < p
        int g = high - 1;         // inicio de la zona >= q
        int k = low + 1;          // elemento que se examina
        int p = arr[low];
        int q = arr[high];

        while (k <= g) {
            if (arr[k] < p) {                     // va a la zona izquierda
                swap(arr, k, j);
                j++;
            } else if (arr[k] >= q) {             // va a la zona derecha
                while (arr[g] > q && k < g) g--;
                swap(arr, k, g);
                g--;
                if (arr[k] < p) {
                    swap(arr, k, j);
                    j++;
                }
            }
            k++;
        }

        j--;
        g++;
        // Lleva los pivotes a su posición final
        swap(arr, low, j);
        swap(arr, high, g);
        return new int[]{j, g};
    }

    private static void swap(int[] arr, int i, int j) {
        int t = arr[i];
        arr[i] = arr[j];
        arr[j] = t;
    }
}
