package taller3.common;

import java.util.Locale;

/**
 * Estimación de tiempos no ejecutados (idéntica a estimation.py):
 *     t(n_obj) ≈ t(n_med) · f(n_obj) / f(n_med)
 * con n_med = mayor n MEDIDO de ese algoritmo y variante.
 */
public final class Estimator {
    private Estimator() {}

    public static double extrapolate(double tNs, int nFrom, int nTo, Growth g) {
        return tNs * g.f(nTo) / g.f(nFrom);
    }

    public static String describe(double tNs, int nFrom, int nTo, Growth g) {
        double ratio = g.f(nTo) / g.f(nFrom);
        return String.format(Locale.ROOT, "t(%d)=%s s x f(%d)/f(%d) = x%s con f=%s",
                nFrom, g6(tNs / 1e9), nTo, nFrom, g6(ratio), g.label());
    }

    /** 6 cifras significativas sin ceros sobrantes (igual que el formato :.6g de Python). */
    private static String g6(double x) {
        String s = String.format(Locale.ROOT, "%.6g", x);
        if (s.contains("e")) return s;
        return s.contains(".") ? s.replaceAll("0+$", "").replaceAll("\\.$", "") : s;
    }
}
