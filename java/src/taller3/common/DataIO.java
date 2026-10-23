package taller3.common;

import java.io.BufferedReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashSet;
import java.util.Set;

/**
 * Lectura de los archivos planos (un entero por línea, ASCII, sin encabezado).
 * Se usa siempre ANTES de medir; nunca dentro de una región cronometrada.
 */
public final class DataIO {
    private DataIO() {}

    /** Lee exactamente expectedN enteros y valida el rango de 8 dígitos (falla rápido). */
    public static int[] readInts(Path path, int expectedN) throws IOException {
        if (!Files.exists(path)) {
            throw new IOException("No existe " + path
                    + ". Genera los datos primero: cd python && python3 -m taller3.generate_data");
        }
        int[] values = new int[expectedN];
        int count = 0;
        try (BufferedReader br = Files.newBufferedReader(path, StandardCharsets.US_ASCII)) {
            String line;
            while ((line = br.readLine()) != null) {
                line = line.trim();
                if (line.isEmpty()) continue;
                if (count == expectedN) {
                    throw new IOException(path.getFileName() + ": tiene más de " + expectedN + " valores");
                }
                int v = Integer.parseInt(line);
                if (v < Config.MIN_VALUE || v > Config.MAX_VALUE) {
                    throw new IOException(path.getFileName() + ": valor fuera de rango " + v);
                }
                values[count++] = v;
            }
        }
        if (count != expectedN) {
            throw new IOException(path.getFileName() + ": se esperaban " + expectedN + " valores y hay " + count);
        }
        return values;
    }

    /**
     * Lee las 1.000 claves del Punto 2 (data/claves_busqueda.txt) en el orden del archivo.
     * Cantidad y rango los valida readInts; además falla si hay claves repetidas
     * (spec p2 6.1.2). No comprueba el SHA-256 (eso lo hace el generador de Python).
     */
    public static int[] readSearchKeys(Path dataDir) throws IOException {
        int[] keys = readInts(dataDir.resolve(Config.SEARCH_KEYS_FILE), Config.NUM_SEARCH_KEYS);
        Set<Integer> seen = new HashSet<>();
        for (int k : keys) {
            if (!seen.add(k)) throw new IOException(Config.SEARCH_KEYS_FILE + ": clave repetida " + k);
        }
        return keys;
    }
}
