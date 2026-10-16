package taller3.common;

/** Variantes de entrada del Punto 1. El nombre es el prefijo del archivo en data/. */
public enum Variant {
    ALEATORIA("aleatoria"),
    ASCENDENTE("ascendente"),
    DESCENDENTE("descendente");

    private final String label;

    Variant(String label) { this.label = label; }

    public String label() { return label; }

    /** p. ej. aleatoria_1000.txt */
    public String fileName(int n) { return label + "_" + n + ".txt"; }

    public static Variant fromLabel(String s) {
        for (Variant v : values()) if (v.label.equalsIgnoreCase(s)) return v;
        throw new IllegalArgumentException("Variante desconocida: " + s);
    }
}
