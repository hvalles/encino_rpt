# Estrategia de uso de GSD

Estrategia híbrida para decidir cuándo usar la ceremonia completa de GSD y cuándo implementar directo, maximizando valor por costo.

## Principio

El valor de GSD está en el **análisis y la verificación**, no en la ceremonia de ejecución. Usa siempre lo barato y de alto valor (análisis estático, review, verificación); usa la ceremonia completa sólo cuando el cambio es nuevo, ambiguo o transversal.

## Triage por riesgo

| Situación | Acción |
|-----------|--------|
| Antes de decidir *qué* hacer | `map-codebase` (análisis estático / CONCERNS) |
| Bug difícil, no reproducible a simple vista | `/gsd-debug` |
| Feature nueva con decisiones de diseño, refactor transversal, trabajo sensible a seguridad, infra (CI) | `/gsd-execute-phase` (ceremonia completa) |
| Cambio mecánico, bien entendido, low-risk | Implementación directa |
| Después de terminar cualquier trabajo | `code-review` + `verifier` |
| Al terminar trabajo directo | Sincronizar `.planning/ROADMAP.md`, `STATE.md`, `PROJECT.md` (vía `/gsd-quick` o edición directa) |

## Reglas

1. **Nunca saltes el análisis.** `map-codebase` cazó 15+ bugs que la suite en verde no veía; `code-review` cazó WR-01/WR-02 post-hoc. Son read-only y baratos.
2. **Ceremonia completa sólo con ambigüedad o riesgo.** Para trabajo mecánico, la ceremonia (plan→research→patterns→plan-check→executor→verify→review) tiene overhead que no se paga solo.
3. **Reconciliación obligatoria tras trabajo directo.** Si implementas directo y no sincronizas ROADMAP/STATE/PROJECT, GSD queda ciego y la deriva de estado se acumula (fue el costo real de hacer los puntos 1–6 "sin GSD").

## Estado actual (2026-09-16)

- Fases 1–7 del roadmap están **implementadas** (Fase 1 vía GSD; Fases 2–7 vía implementación directa).
- Restante real: **Fase 8 (Tests & CI)** + 2 hardenings menores (ver `ROADMAP.md` y `PROJECT.md`).
