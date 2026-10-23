package taller3.common;

/** Una fila del CSV de búsqueda del Punto 2 (mismo esquema que SearchResultRecord en results.py). */
public final class SearchResultRecord {
    public final String algoritmo;
    public final String lenguaje;
    public final String variante;
    public final int n;
    public int numBusquedas = Config.NUM_SEARCH_KEYS;
    public Integer clave;              // null en "claves"; el valor buscado en las posiciones
    public long[] repsNs = new long[0]; // tiempo TOTAL de cada pasada
    public Double promedioNs;          // null si no se pudo medir ni estimar
    public Double desvEstandarNs;      // null si es estimado
    public Integer encontradas;        // null si no se midió
    public Long checksum;              // Σ out[j] incluidos los -1 (long: en 10^6 supera 2^31)
    public String estado = "medido";   // "medido" | "estimado" | "fallido"
    public String causa = "";
    public String baseEstimacion = "";

    public SearchResultRecord(String algoritmo, String lenguaje, String variante, int n) {
        this.algoritmo = algoritmo;
        this.lenguaje = lenguaje;
        this.variante = variante;
        this.n = n;
    }
}
