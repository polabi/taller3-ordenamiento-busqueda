package taller3.common;

/** Complejidad teórica de un caso, usada para predecir y estimar tiempos. */
public enum Growth {
    N("O(n)"),
    NLOGN("O(n log n)"),
    N2("O(n^2)");

    private final String label;

    Growth(String label) { this.label = label; }

    public String label() { return label; }

    public double f(long n) {
        switch (this) {
            case N:     return n;
            case NLOGN: return n * (Math.log(n) / Math.log(2));
            default:    return (double) n * n;
        }
    }
}
