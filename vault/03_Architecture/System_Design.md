---
id: DOC-SYSDESIGN
title: "System Design"
owner: "Edgar Edmundo Coronel Navarrete"
status: draft
source_of_truth: true
traces_up: ["PRD#7"]
tags: [architecture, design]
---

# System Design — FARO

> → [[vault/03_Architecture/_index]]

## Diagrama de alto nivel
```mermaid
flowchart LR
  Client --> API --> DB[(Data Store)]
  API --> Ext[Servicios externos]
```

## Componentes
| Componente | Responsabilidad | Dueño |
|---|---|---|

## Decisiones clave
Ver [[vault/03_Architecture/ADRs/_index]].

## Requisitos no funcionales que impactan el diseño
<!-- Rendimiento, escalabilidad, seguridad → enlaza a 07_Security y 11_Operations -->
