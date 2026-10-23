package taller3.searching;

import taller3.common.Growth;

/**
 * Contrato común: busca x en un int[] ordenado de forma no decreciente SIN modificarlo.
 * Devuelve un índice i con arr[i] == x, o -1 si x no está.
 */
public interface SearchAlgorithm {
    String name();

    int search(int[] arr, int x);

    /** Complejidad del caso promedio con las claves del taller (para predecir/estimar). */
    Growth growth();
}
