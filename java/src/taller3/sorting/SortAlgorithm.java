package taller3.sorting;

import taller3.common.Growth;
import taller3.common.Variant;

/** Contrato común: ordena IN SITU un int[] y declara la complejidad de cada caso. */
public interface SortAlgorithm {
    String name();

    void sort(int[] arr);

    /** Complejidad del caso que produce cada variante (para predecir/estimar). */
    Growth growth(Variant v);
}
