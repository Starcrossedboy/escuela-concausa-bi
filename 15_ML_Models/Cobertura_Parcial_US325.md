---
id: DOC-COBERTURA-PARCIAL-US325
title: "US-325 — Sesgo por cobertura parcial en features"
owner: "Estefany Lucero Hernández Loredo"
status: in_review
traces_up: ["US-325", "REQ-003", "03_Architecture/ADRs/ADR-003-ml-estrategia-modelado"]
traces_down: ["US-321"]
tags: [ml, cobertura, sesgo, celula-3]
---

# US-325 — Sesgo por cobertura parcial en features

> Implementación reproducible: `src/modelos/analizar_features.py`.

## Qué se mide

El análisis entrega, por driver, el número y porcentaje de observaciones `SIN_DATO`, más las escuelas
afectadas. También desglosa cobertura y `indice_completitud_drivers` por entidad, derivada de los dos
primeros caracteres del CCT.

## Regla de interpretación

Una menor cobertura no equivale a un valor cero ni a menor riesgo. Cualquier diferencia sistemática
entre entidades debe reportarse antes de interpretar clusters como perfiles de intervención.

## Bloqueo explícito para análisis municipal

El contrato actual de `gold.features_escuela` no incluye `cve_mun`. Por ello, el módulo falla de forma
explícita cuando se solicita un análisis municipal: no infiere municipio desde el CCT ni sustituye el
resultado municipal por uno estatal. Célula 1 debe confirmar esa llave antes de cerrar este criterio y
antes de aplicar la mediana municipal definida por ADR-003.

## Criterio de salida

Con `cve_mun` disponible, se agregará el desglose municipal y se evaluará si `SIN_DATO` se concentra
en municipios específicos. Hasta entonces, el estado de US-325 es parcial y se limita al diagnóstico
por entidad sobre datos sintéticos.
