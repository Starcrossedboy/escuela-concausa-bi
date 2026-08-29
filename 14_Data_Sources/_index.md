---
id: MOC-DATASOURCES
title: "Data Sources — Índice"
owner: "Diana Aracely Alvarez Varela"
status: active
source_of_truth: true
tags: [index, moc, data-sources]
---

# 14_Data_Sources — Fuentes de datos

> Una nota por fuente. Ninguna fuente entra al pipeline sin su nota documentada y su
> **prueba de descarga real** aprobada.

## Las 8 fuentes del proyecto

| ID | Fuente | Frecuencia | Cobertura | Driver | Dueño | Estado |
|---|---|---|---|---|---|---|
| [[14_Data_Sources/DS-01_Formato_911\|DS-01]] | SEP · Formato 911 | Anual | Nacional | (hecho central) | Diana Aracely Alvarez Varela | draft · prueba pendiente |
| [[14_Data_Sources/DS-02_Catalogo_CCT\|DS-02]] | SEP · Catálogo CCT | Continua | Nacional | (llave primaria) | Diana Aracely Alvarez Varela | draft · prueba pendiente |
| [[14_Data_Sources/DS-03_CEMABE\|DS-03]] | SEP · CEMABE | Censo 2013 | Nacional · escuela | D3 · D4 | Deni Garrido Fragoso | draft · prueba pendiente |
| [[14_Data_Sources/DS-04_SESNSP_Incidencia_Delictiva\|DS-04]] | SESNSP · Incidencia delictiva | **Mensual** | Nacional | D2 | Luis Enrique García Vázquez | draft · prueba pendiente |
| [[14_Data_Sources/DS-05_SINAICA_Calidad_Aire\|DS-05]] | SINAICA · Calidad del aire | **Horaria** | ~80 zonas urbanas | D6 | Luis Enrique García Vázquez | draft · prueba pendiente |
| [[14_Data_Sources/DS-06_CONAGUA_SINA\|DS-06]] | CONAGUA · SINA | **Diaria** | Regional | D5 | Emilio Galnares Ruiz | en revisión (PR abierto) |
| [[14_Data_Sources/DS-07_CONEVAL_Rezago_Social\|DS-07]] | CONEVAL · Rezago social | Bienal | Nacional | D1 | Deni Garrido Fragoso | draft · prueba pendiente |
| [[14_Data_Sources/DS-08_CONAPO_Proyecciones\|DS-08]] | CONAPO · Proyecciones | Anual | Nacional | (denominador) | Emilio Galnares Ruiz | en revisión (PR abierto) |

> **Nota de asignación:** las 8 fuentes se reparten entre la Célula 1 (Data Engineering & Quality)
> como asignación inicial (2 por integrante); la prueba de descarga real de Semana 1 corresponde al
> dueño indicado (ver US-121/US-122 en [[12_Roadmap_Sprints/PLAN_MAESTRO]]).

## Prueba de descarga real — obligatoria (Semana 1)

Una fuente NO está aprobada hasta que alguien:

1. **Descargó físicamente** el archivo o llamó a la API (no basta leer la página del portal)
2. **Lo abrió** y verificó que tiene datos utilizables
3. **Contó los registros** y documentó el número
4. **Verificó el esquema**: columnas, tipos, llave de unión
5. **Confirmó la llave de cruce**: CCT para escuelas, clave INEGI de 5 dígitos para municipios

Si una fuente falla la prueba, se sustituye **en la Semana 1**, no en la 5.
