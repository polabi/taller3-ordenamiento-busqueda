"""
Cálculos puros del Punto 3 (spec p3 3.1). No leen archivos ni miden tiempos.

Parte B (¿ordenar o no ordenar?), con t_ord = tiempo de ordenar una vez, t_l = tiempo
por búsqueda lineal y t_b = tiempo por búsqueda binaria:

    sin ordenar:          costo(k) = k · t_l
    ordenar + binaria:    costo(k) = t_ord + k · t_b
    conviene ordenar  ⇔   k > t_ord / (t_l − t_b) = k*        (si t_l > t_b)

Parte A: cota inferior ⌈log₂(n!)⌉ y perfiles exactos del Bucket Sort y del Radix Sort
del repo (cuántas cubetas, cuántos desplazamientos, cuántas pasadas), para explicar
los tiempos del experimento de supuestos.
"""
from __future__ import annotations

import math


# ======================================================================================
# Parte B: k*
# ======================================================================================
def k_star(t_ord: float, t_l: float, t_b: float) -> float | None:
    """t_ord / (t_l − t_b); None si t_l <= t_b (nunca conviene ordenar)."""
    if t_l <= t_b:
        return None
    return t_ord / (t_l - t_b)


def k_min(t_ord: float, t_l: float, t_b: float) -> int | None:
    """Menor k entero con el que ordenar es ESTRICTAMENTE mejor: ⌊k*⌋ + 1 (en k* hay empate)."""
    ks = k_star(t_ord, t_l, t_b)
    if ks is None:
        return None
    return math.floor(ks) + 1


def k_interval(t_ord: float, s_ord: float, t_l: float, s_l: float,
               t_b: float, s_b: float) -> tuple[float | None, float | None]:
    """(k_bajo, k_alto) con ±1 desviación estándar (spec 5.5).

    k_bajo = (t_ord − s_ord) / ((t_l + s_l) − (t_b − s_b))
    k_alto = (t_ord + s_ord) / ((t_l − s_l) − (t_b + s_b))
    Cada extremo es None si su denominador es <= 0.
    """
    den_lo = (t_l + s_l) - (t_b - s_b)
    den_hi = (t_l - s_l) - (t_b + s_b)
    lo = (t_ord - s_ord) / den_lo if den_lo > 0 else None
    hi = (t_ord + s_ord) / den_hi if den_hi > 0 else None
    return lo, hi


# ======================================================================================
# Parte A: cota inferior y perfiles de los no comparativos
# ======================================================================================
def lower_bound_comparisons(n: int) -> int:
    """⌈log₂(n!)⌉ = menor h con 2^h >= n! (altura mínima del árbol de decisión); 0 si n <= 1."""
    if n <= 1:
        return 0
    return math.ceil(math.lgamma(n + 1) / math.log(2))


def bucket_profile(values: list[int]) -> tuple[int, int, int]:
    """(cubetas_no_vacias, cubeta_max, desplazamientos) del Bucket Sort del repo.

    Misma distribución que sorting/bucket_sort.py: k = n cubetas e
    idx = (x − min)·k // (max − min + 1). Los desplazamientos del Insertion Sort estricto
    (b[j] > key) de cada cubeta son exactamente sus inversiones estrictas (pares i < j con
    b[i] > b[j]); se cuentan por mezcla en O(m log m), sin ejecutar el Insertion.
    No modifica values.
    """
    n = len(values)
    if n == 0:
        return 0, 0, 0
    mn = mx = values[0]
    for x in values:
        if x < mn:
            mn = x
        if x > mx:
            mx = x
    k = n
    rango = mx - mn + 1
    buckets: list[list[int]] = [[] for _ in range(k)]
    for x in values:
        buckets[(x - mn) * k // rango].append(x)

    non_empty = 0
    largest = 0
    shifts = 0
    for b in buckets:
        if b:
            non_empty += 1
            largest = max(largest, len(b))
            if len(b) > 1:
                shifts += _count_inversions(b)[1]
    return non_empty, largest, shifts


def _count_inversions(a: list[int]) -> tuple[list[int], int]:
    """Ordena por mezcla (copia) y cuenta los pares i < j con a[i] > a[j] (estricto)."""
    if len(a) <= 1:
        return list(a), 0
    mid = len(a) // 2
    left, inv_l = _count_inversions(a[:mid])
    right, inv_r = _count_inversions(a[mid:])
    merged: list[int] = []
    inv = inv_l + inv_r
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:              # iguales no son inversión (Insertion estricto)
            merged.append(left[i])
            i += 1
        else:
            merged.append(right[j])
            inv += len(left) - i
            j += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged, inv


def radix_passes(values: list[int]) -> int:
    """Iteraciones de `while m // exp > 0` del Radix Sort del repo (m = máximo, exp = 1, 10, …).

    = cantidad de dígitos decimales del máximo; 0 si la lista está vacía o el máximo es 0.
    """
    if not values:
        return 0
    m = values[0]
    for x in values:
        if x > m:
            m = x
    passes = 0
    exp = 1
    while m // exp > 0:
        passes += 1
        exp *= 10
    return passes
