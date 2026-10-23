"""
Búsqueda ternaria (iterativa).
Fuente: GeeksforGeeks, "Ternary Search",
        https://www.geeksforgeeks.org/dsa/ternary-search/
Desviaciones respecto a GfG: (1) GfG devuelve un booleano con
  if arr[mid1] == x or arr[mid2] == x: return True; aquí se devuelve el índice, así que
  la condición se separa en dos if (primero mid1, luego mid2), lo que fija qué índice se
  devuelve cuando hay duplicados; (2) si no se encuentra se devuelve -1.
Equivalente línea a línea: java/src/taller3/searching/TernarySearch.java
"""
from __future__ import annotations


def ternary_search(arr: list[int], x: int) -> int:
    n = len(arr)
    l = 0
    r = n - 1
    while r >= l:
        mid1 = l + (r - l) // 3
        mid2 = r - (r - l) // 3
        if arr[mid1] == x:
            return mid1
        if arr[mid2] == x:
            return mid2
        if x < arr[mid1]:
            r = mid1 - 1
        elif x > arr[mid2]:
            l = mid2 + 1
        else:
            l = mid1 + 1
            r = mid2 - 1
    return -1
