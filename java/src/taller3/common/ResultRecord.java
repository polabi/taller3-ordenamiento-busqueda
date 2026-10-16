package taller3.common;

/** Una fila del CSV de resultados (mismo esquema que results.py). */
public final class ResultRecord {
    public final String algoritmo;
    public final String lenguaje;
    public final String variante;
    public final int n;
    public long[] repsNs = new long[0];
    public Double promedioNs;          // null si no se pudo medir ni estimar
    public Double desvEstandarNs;      // null si es estimado
    public String estado = "medido";   // "medido" | "estimado" | "fallido"
    public String causa = "";
    public String baseEstimacion = "";

    public ResultRecord(String algoritmo, String lenguaje, String variante, int n) {
        this.algoritmo = algoritmo;
        this.lenguaje = lenguaje;
        this.variante = variante;
        this.n = n;
    }
}
