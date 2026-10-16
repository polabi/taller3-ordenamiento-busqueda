package taller3.sorting;

import taller3.common.Growth;
import taller3.common.Variant;

/**
 * Heap Sort (max-heap, heapify recursivo).
 * Fuente: GeeksforGeeks, "Heap Sort", https://www.geeksforgeeks.org/dsa/heap-sort/
 * Equivalente línea a línea: python/taller3/sorting/heap_sort.py
 */
public final class HeapSort implements SortAlgorithm {
    @Override public String name() { return "HeapSort"; }

    @Override public Growth growth(Variant v) { return Growth.NLOGN; }

    @Override public void sort(int[] arr) {
        int n = arr.length;
        // Construir el max-heap desde el último nodo interno hacia la raíz
        for (int i = n / 2 - 1; i >= 0; i--) heapify(arr, n, i);
        // Extraer el máximo uno por uno
        for (int i = n - 1; i > 0; i--) {
            int t = arr[0];
            arr[0] = arr[i];
            arr[i] = t;
            heapify(arr, i, 0);
        }
    }

    private static void heapify(int[] arr, int n, int i) {
        int largest = i;
        int l = 2 * i + 1;
        int r = 2 * i + 2;
        if (l < n && arr[l] > arr[largest]) largest = l;
        if (r < n && arr[r] > arr[largest]) largest = r;
        if (largest != i) {
            int t = arr[i];
            arr[i] = arr[largest];
            arr[largest] = t;
            heapify(arr, n, largest);
        }
    }
}
