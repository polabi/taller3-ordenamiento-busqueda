package taller3.common;

/** Estadística descriptiva de las repeticiones (idéntica a stats.py). */
public final class Stats {
    private Stats() {}

    public static double mean(long[] xs, int count) {
        double s = 0;
        for (int i = 0; i < count; i++) s += xs[i];
        return s / count;
    }

    /** Desviación estándar MUESTRAL (divide entre n-1). Con una sola muestra devuelve 0. */
    public static double sampleStd(long[] xs, int count) {
        if (count < 2) return 0.0;
        double m = mean(xs, count);
        double acc = 0;
        for (int i = 0; i < count; i++) {
            double d = xs[i] - m;
            acc += d * d;
        }
        return Math.sqrt(acc / (count - 1));
    }
}
