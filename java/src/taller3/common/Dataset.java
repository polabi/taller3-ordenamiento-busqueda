package taller3.common;

import java.io.IOException;
import java.nio.file.Path;

/** Las tres variantes de entrada para un mismo n (mismos valores, distinto orden). */
public final class Dataset {
    public final int n;
    private final int[] aleatoria;
    private final int[] ascendente;
    private final int[] descendente;

    private Dataset(int n, int[] aleatoria, int[] ascendente, int[] descendente) {
        this.n = n;
        this.aleatoria = aleatoria;
        this.ascendente = ascendente;
        this.descendente = descendente;
    }

    public static Dataset load(Path dataDir, int n) throws IOException {
        return new Dataset(n,
                DataIO.readInts(dataDir.resolve(Variant.ALEATORIA.fileName(n)), n),
                DataIO.readInts(dataDir.resolve(Variant.ASCENDENTE.fileName(n)), n),
                DataIO.readInts(dataDir.resolve(Variant.DESCENDENTE.fileName(n)), n));
    }

    /** Arreglo ORIGINAL de la variante. No se ordena nunca: se copia antes de cada ejecución. */
    public int[] get(Variant v) {
        switch (v) {
            case ALEATORIA:   return aleatoria;
            case ASCENDENTE:  return ascendente;
            case DESCENDENTE: return descendente;
            default: throw new IllegalArgumentException(String.valueOf(v));
        }
    }

    /** Referencia ordenada (generada por Python con sorted()): oráculo de verificación. */
    public int[] expectedSorted() { return ascendente; }
}
