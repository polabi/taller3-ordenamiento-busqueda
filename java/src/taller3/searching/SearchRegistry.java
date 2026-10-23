package taller3.searching;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;

/**
 * Lista de algoritmos del Punto 2, en el mismo orden que python/taller3/searching/__init__.py.
 * La variante InterpolationSearchIntDiv va al final para no alterar el orden del enunciado.
 */
public final class SearchRegistry {
    private SearchRegistry() {}

    public static final List<SearchAlgorithm> ALL = Collections.unmodifiableList(Arrays.asList(
            new LinearSearch(),
            new BinarySearch(),
            new TernarySearch(),
            new JumpSearch(),
            new InterpolationSearch(),
            new ExponentialSearch(),
            new InterpolationSearchIntDiv()
    ));

    public static SearchAlgorithm byName(String name) {
        for (SearchAlgorithm a : ALL) if (a.name().equalsIgnoreCase(name)) return a;
        throw new IllegalArgumentException("Algoritmo desconocido: " + name);
    }
}
