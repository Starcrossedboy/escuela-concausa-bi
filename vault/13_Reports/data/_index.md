---
id: MOC-13-DATA
title: "Datos generados del tablero PM"
owner: "Edgar Edmundo Coronel Navarrete"
status: active
source_of_truth: false
traces_up: ["13_Reports/PM_Dashboard_Spec"]
tags: [reports, generated, dashboard, data]
---

# Datos generados del tablero PM

> Salidas regenerables; no son fuentes de verdad y no se editan manualmente.
> → [[13_Reports/_index]] · [[13_Reports/PM_Dashboard_Spec]]

| Archivo | Propósito |
|---|---|
| [`pm-dashboard.json`](pm-dashboard.json) | Snapshot consolidado que se incrusta en el HTML; incluye directorio, US y conteos derivados de PR |
| [`pm-dashboard-history.json`](pm-dashboard-history.json) | Serie temporal para burndown, burn-up, WIP y bloqueos |
| `github-activity.json` | Snapshot efímero paginado de PR/CI creado en Actions; no se versiona ni define Done |
