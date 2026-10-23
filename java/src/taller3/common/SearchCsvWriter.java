package taller3.common;

import java.io.BufferedWriter;
import java.io.Closeable;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;

/**
 * CSV de búsqueda del Punto 2 (mismo esquema que SearchCsvWriter en results.py):
 * algoritmo,lenguaje,variante,n,num_busquedas,clave,rep_1_ns..rep_k_ns,promedio_ns,
 * desv_estandar_ns,promedio_por_busqueda_ns,desv_por_busqueda_ns,encontradas,checksum,
 * estado,causa,base_estimacion
 *
 * Las columnas "por búsqueda" se calculan aquí (= total / numBusquedas) desde los valores
 * sin redondear. Locale.ROOT en todos los números (con la configuración regional en
 * español String.format escribiría "123,4"). Cada fila se vacía a disco al escribirse.
 * El escritor del Punto 1 (CsvResultWriter) no se toca.
 */
public final class SearchCsvWriter implements Closeable {
    private final BufferedWriter out;
    private final int repetitions;

    public SearchCsvWriter(Path path, int repetitions) throws IOException {
        this.repetitions = repetitions;
        if (path.getParent() != null) Files.createDirectories(path.getParent());
        this.out = Files.newBufferedWriter(path, StandardCharsets.UTF_8);
        StringBuilder h = new StringBuilder("algoritmo,lenguaje,variante,n,num_busquedas,clave");
        for (int i = 1; i <= repetitions; i++) h.append(",rep_").append(i).append("_ns");
        h.append(",promedio_ns,desv_estandar_ns,promedio_por_busqueda_ns,desv_por_busqueda_ns");
        h.append(",encontradas,checksum,estado,causa,base_estimacion");
        out.write(h.toString());
        out.newLine();
        out.flush();
    }

    public void write(SearchResultRecord r) throws IOException {
        int k = r.numBusquedas;
        StringBuilder sb = new StringBuilder();
        sb.append(esc(r.algoritmo)).append(',').append(esc(r.lenguaje)).append(',')
          .append(esc(r.variante)).append(',').append(r.n).append(',').append(k)
          .append(',').append(r.clave == null ? "" : r.clave.toString());
        for (int i = 0; i < repetitions; i++) {
            sb.append(',');
            if (i < r.repsNs.length) sb.append(r.repsNs[i]);
        }
        sb.append(',').append(fmt("%.1f", r.promedioNs));
        sb.append(',').append(fmt("%.1f", r.desvEstandarNs));
        sb.append(',').append(fmt("%.3f", r.promedioNs == null ? null : r.promedioNs / k));
        sb.append(',').append(fmt("%.3f", r.desvEstandarNs == null ? null : r.desvEstandarNs / k));
        sb.append(',').append(r.encontradas == null ? "" : r.encontradas.toString());
        sb.append(',').append(r.checksum == null ? "" : r.checksum.toString());
        sb.append(',').append(esc(r.estado))
          .append(',').append(esc(r.causa))
          .append(',').append(esc(r.baseEstimacion));
        out.write(sb.toString());
        out.newLine();
        out.flush();
    }

    private static String fmt(String pattern, Double v) {
        return v == null ? "" : String.format(Locale.ROOT, pattern, v);
    }

    /** Escapado CSV estándar (RFC 4180), igual que CsvResultWriter. */
    private static String esc(String s) {
        if (s == null) return "";
        if (s.indexOf(',') >= 0 || s.indexOf('"') >= 0 || s.indexOf('\n') >= 0) {
            return '"' + s.replace("\"", "\"\"") + '"';
        }
        return s;
    }

    @Override
    public void close() throws IOException { out.close(); }
}
