"""Estadística descriptiva de las repeticiones (idéntica a Stats.java)."""
from __future__ import annotations

import math
from typing import Sequence


def mean(xs: Sequence[float]) -> float:
    return sum(xs) / len(xs)


def sample_std(xs: Sequence[float]) -> float:
    """Desviación estándar MUESTRAL (divide entre n-1). Con una sola muestra devuelve 0."""
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1))
