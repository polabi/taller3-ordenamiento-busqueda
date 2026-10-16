"""
Estimación de tiempos que no se ejecutan (regla de los 5 minutos o fallos).

Método (idéntico en Estimator.java):
    t(n_obj) ≈ t(n_med) · f(n_obj) / f(n_med)

donde n_med es el MAYOR tamaño realmente medido para ese algoritmo y variante,
t(n_med) su promedio, y f la complejidad teórica del caso correspondiente
(O(n), O(n log n) u O(n²)). Se usa el mayor n medido porque en n pequeños
dominan costos constantes (llamadas, caché, temporizador) y la razón sería
menos representativa.

Antes de ejecutar un caso se PREDICE su tiempo con la misma fórmula; si la
predicción supera el límite, el caso no se ejecuta y se marca "estimado".
"""
from __future__ import annotations

import math
from enum import Enum


class Growth(Enum):
    N = "O(n)"
    NLOGN = "O(n log n)"
    N2 = "O(n^2)"

    def f(self, n: int) -> float:
        if self is Growth.N:
            return float(n)
        if self is Growth.NLOGN:
            return n * math.log2(n)
        return float(n) * n


def extrapolate(t_ns: float, n_from: int, n_to: int, growth: Growth) -> float:
    """Extrapola un tiempo medido en n_from a n_to según la complejidad teórica."""
    return t_ns * growth.f(n_to) / growth.f(n_from)


def describe(t_ns: float, n_from: int, n_to: int, growth: Growth) -> str:
    """Texto para la columna 'base_estimacion' del CSV (trazabilidad del cálculo)."""
    ratio = growth.f(n_to) / growth.f(n_from)
    return (f"t({n_from})={t_ns / 1e9:.6g} s x f({n_to})/f({n_from}) "
            f"= x{ratio:.6g} con f={growth.value}")
