---
id: META-TRACE
title: "Traceability Model"
owner: "Edgar Edmundo Coronel Navarrete"
status: approved
source_of_truth: true
tags: [meta, traceability]
---

# Traceability Model — Cómo se conecta todo

> El mecanismo central para que **nunca se pierda la relación** entre carpetas y cosas nuevas reportadas.
> → [[vault/_Meta/_index|Volver a _Meta]]

## La cadena de trazabilidad

```
PRD (01) → REQ (02) → US (02) → ADR/Diseño (03/04) → TASK (12)
        → Código (repo) → TEST (06) → SEC review (07) → CI Gate (08)
        → DevLog (_DevLog) → Release (08) → Report (13)
```

Cada eslabón enlaza al anterior (`traces_up`) y al siguiente (`traces_down`).

## Frontmatter de trazabilidad (estándar)

```yaml
---
id: REQ-014
title: "Excluir contenido ya visto en el feed"
owner: "Edgar Edmundo Coronel Navarrete"
status: approved
traces_up: ["PRD#7.2"]          # de dónde viene
traces_down: ["US-021", "TEST-033", "ADR-005"]  # qué lo cumple/prueba
related: ["RISK-004"]
last_reviewed: "2026-08-01"
---
```

## La matriz viva

[[vault/02_Requirements/Traceability_Matrix]] es la vista única de todo el estado:

| REQ | User Story | ADR | TASK | TEST | DevLog | Release | Estado |
|---|---|---|---|---|---|---|---|

**Regla de oro:** si una fila tiene una celda vacía en `TEST` o `DevLog`, ese requisito **no está Done**.
La matriz es el primer lugar que revisa el PM en cada cierre de sprint.

## Cómo se mantiene sin fricción

1. Al crear un `REQ`, se agrega su fila a la matriz (vacía).
2. Al crear US/ADR/TEST, se rellena su celda y se enlaza en el frontmatter.
3. El DevLog de cada sesión referencia los IDs tocados.
4. `vault_lint.py` alerta filas incompletas y links rotos.

## Backlinks (Obsidian)

Con `[[wikilinks]]`, Obsidian genera backlinks automáticos: desde cualquier `TEST-033` ves qué
`REQ` valida. No hace falta mantenerlo a mano si los enlaces existen.
