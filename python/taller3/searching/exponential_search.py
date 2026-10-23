"""
Búsqueda exponencial; la binaria final es la iterativa de binary_search_range.
Desviaciones respecto a GfG: (1) GfG C++/C/Python usan una binaria recursiva; aquí es
  iterativa (sin riesgo de pila y la misma que binary_search). (2) La pestaña Java de GfG
  llama a Arrays.binarySearch(arr, i/2, Math.min(i, n-1), x), cuyo límite superior es
  EXCLUSIVO: nunca revisa arr[n-1] (con {2,3,4,10,40} y x = 40 devuelve un negativo).
  Aquí el rango [i/2, min(i, n-1)] es cerrado, así que sí encuentra el último elemento.
  (3) Si n == 0 se devuelve -1 de inmediato.
Fuente: GeeksforGeeks, "Exponential Search",
        https://www.geeksforgeeks.org/dsa/exponential-search/
Equivalente línea a línea: java/src/taller3/searching/ExponentialSearch.java
"""
from __future__ import annotations

from taller3.searching.binary_search import binary_search_range


def exponential_search(arr: list[int], x: int) -> int:
    n = len(arr)
    if n == 0:
        return -1
    if arr[0] == x:
        return 0
    i = 1
    # Duplica i hasta pasarse de x o del arreglo
    while i < n and arr[i] <= x:
        i = i * 2
    # x, si está, queda en [i // 2, min(i, n - 1)]
    return binary_search_range(arr, i // 2, i if i < n - 1 else n - 1, x)
