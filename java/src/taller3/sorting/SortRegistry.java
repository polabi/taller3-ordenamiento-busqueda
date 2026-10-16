package taller3.sorting;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;

/** Lista de algoritmos del Punto 1, en el mismo orden que python/taller3/sorting/__init__.py. */
public final class SortRegistry {
    private SortRegistry() {}

    public static final List<SortAlgorithm> ALL = Collections.unmodifiableList(Arrays.asList(
            new InsertionSort(),
            new DualPivotQuickSort(),
            new MergeSort(),
            new HeapSort(),
            new RadixSort(),
            new BucketSort()
    ));

    public static SortAlgorithm byName(String name) {
        for (SortAlgorithm a : ALL) if (a.name().equalsIgnoreCase(name)) return a;
        throw new IllegalArgumentException("Algoritmo desconocido: " + name);
    }
}
