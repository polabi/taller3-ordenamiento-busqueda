"""
Registro de algoritmos de búsqueda del Punto 2.

Cada algoritmo declara la complejidad de su caso promedio con las claves del taller; el
benchmark la usará para PREDECIR si una pasada superará el límite de 5 minutos y para
ESTIMAR los tiempos que no se ejecuten. El orden de SEARCHES es el mismo que en
SearchRegistry.java (y el de las series en gráficas y tablas). La variante
InterpolationSearchIntDiv va al final para no alterar el orden del enunciado.

Regla de capa: searching no lee archivos, no copia, no mide y no modifica el arreglo.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from taller3.common.estimation import Growth
from taller3.searching.binary_search import binary_search
from taller3.searching.exponential_search import exponential_search
from taller3.searching.interpolation_search import interpolation_search
from taller3.searching.interpolation_search_int_div import interpolation_search_int_div
from taller3.searching.jump_search import jump_search
from taller3.searching.linear_search import linear_search
from taller3.searching.ternary_search import ternary_search


@dataclass(frozen=True)
class SearchSpec:
    name: str
    func: Callable[[list[int], int], int]
    growth: Growth


SEARCHES: tuple[SearchSpec, ...] = (
    SearchSpec("LinearSearch", linear_search, Growth.N),
    SearchSpec("BinarySearch", binary_search, Growth.LOGN),
    SearchSpec("TernarySearch", ternary_search, Growth.LOGN),
    SearchSpec("JumpSearch", jump_search, Growth.SQRTN),
    SearchSpec("InterpolationSearch", interpolation_search, Growth.LOGLOGN),
    SearchSpec("ExponentialSearch", exponential_search, Growth.LOGN),
    SearchSpec("InterpolationSearchIntDiv", interpolation_search_int_div, Growth.N),  # variante
)

BY_NAME = {s.name: s for s in SEARCHES}
