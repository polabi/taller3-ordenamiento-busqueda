# Specs (SDD) del Taller 3

Cada punto pendiente del taller se especifica aquí **antes** de escribir pruebas o código.
Flujo: `borrador` → el estudiante resuelve las *Decisiones pendientes* → `aprobada` →
`aa-test-writer` escribe las pruebas → implementación → `implementada`.

| Spec | Punto | Estado |
|---|---|---|
| [p2-busqueda.md](p2-busqueda.md) | Punto 2 — Algoritmos de búsqueda | algoritmos y pruebas de corrección: **implementada (2026-10-20)**; protocolo de claves/benchmark: **aprobada (2026-10-22)** |
| [p3-comparativo.md](p3-comparativo.md) | Punto 3 — Análisis comparativo | **aprobada (2026-10-22)**, salvo valores «propuestos por la spec» (10.3) por confirmar |

Una spec en `borrador` **no** se implementa. Solo el estudiante la pasa a `aprobada`.

---

## Plantilla

```markdown
# <Punto N> — <tema>

Estado: borrador | aprobada | implementada        Fecha: AAAA-MM-DD

## 1. Requerimiento (copiado literal del enunciado)
> ...

## 2. Alcance
Qué entra y qué no. Qué se reutiliza del Punto 1.

## 3. Algoritmos / cálculos
Para cada uno: fuente (GfG + libro), firma Java/Python, contrato de entrada/salida,
reglas de comportamiento, complejidad (mejor / promedio / peor, memoria) con fuente.
Si una cita no está verificada: "por confirmar".

## 4. Casos borde

## 5. Casos de prueba resueltos a mano
Entrada concreta → traza del cálculo → resultado esperado.
(Los valores se verifican con cálculo o con una implementación de referencia.)

## 6. Protocolo de medición
Datos, repeticiones, estadístico, calentamiento, qué queda dentro y fuera del tiempo,
unidad, límite de 5 min y estimación, verificación.

## 7. Salidas
Archivos (CSV/JSON), esquema de columnas, figuras y tablas.

## 8. Cómo se verifica
Oráculo independiente, equivalencia Java ↔ Python, comprobaciones de plausibilidad.

## 9. Preguntas de análisis que la salida debe permitir responder

## 10. Decisiones pendientes del estudiante
Cada una con opciones, pros/contras y recomendación. **Deben aprobarse antes de pasar a pruebas.**

## 11. Preguntas abiertas
```

## Convenciones comunes (heredadas del Punto 1, ver `README.md` y `CLAUDE.md`)

- Java y Python **equivalentes línea a línea**; fuente principal GeeksforGeeks.
- `python/taller3/config.py` es la fuente de verdad; `Config.java` la replica a mano.
- Solo `generate_data.py` genera archivos en `data/`; Java solo lee.
- Tiempos en **nanosegundos enteros** en el CSV; ms/µs solo al graficar.
- 5 repeticiones → promedio y desviación estándar **muestral** (n − 1).
- Límite de 300 s por ejecución → `estado = estimado` con `base_estimacion`.
- Figuras en `figures/pN_*.png`, resultados en `results/`.
