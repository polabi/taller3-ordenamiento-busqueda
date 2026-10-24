package taller3.common;

import java.io.BufferedWriter;
import java.io.Closeable;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Locale;

/**
 * CSV del experimento de supuestos del Punto 3 (spec p3 7.2). Mismo esquema que
 * CsvResultWriter (Punto 1, sin cambios) + la columna distribucion después de variante:
 * algoritmo,lenguaje,variante,distribucion,n,rep_1_ns..rep_k_ns,promedio_ns,desv_estandar_ns,estado,causa,base_estimacion
 *
 * Reutiliza ResultRecord. Locale.ROOT en todos los números; cada fila se vacía a disco al escribirse.
 */
public final class SupuestosCsvWriter implements Closeable {
    private final BufferedWriter out;
    private final int repetitions;

    public SupuestosCsvWriter(Path path, int repetitions) throws IOException {
        this.repetitions = repetitions;
        if (path.getParent() != null) Files.createDirectories(path.getParent());
        this.out = Files.newBufferedWriter(path, StandardCharsets.UTF_8);
        StringBuilder h = new StringBuilder("algoritmo,lenguaje,variante,distribucion,n");
        for (int i = 1; i <= repetitions; i++) h.append(",rep_").append(i).append("_ns");
        h.append(",promedio_ns,desv_estandar_ns,estado,causa,base_estimacion");
        out.write(h.toString());
        out.newLine();
        out.flush();
    }

    public void write(ResultRecord r, String distribucion) throws IOException {
        StringBuilder sb = new StringBuilder();
        sb.append(esc(r.algoritmo)).append(',').append(esc(r.lenguaje)).append(',')
          .append(esc(r.variante)).append(',').append(esc(distribucion)).append(',').append(r.n);
        for (int i = 0; i < repetitions; i++) {
            sb.append(',');
            if (i < r.repsNs.length) sb.append(r.repsNs[i]);
        }
        sb.append(',').append(r.promedioNs == null ? "" : String.format(Locale.ROOT, "%.1f", r.promedioNs));
        sb.append(',').append(r.desvEstandarNs == null ? "" : String.format(Locale.ROOT, "%.1f", r.desvEstandarNs));
        sb.append(',').append(esc(r.estado))
          .append(',').append(esc(r.causa))
          .append(',').append(esc(r.baseEstimacion));
        out.write(sb.toString());
        out.newLine();
        out.flush();
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
