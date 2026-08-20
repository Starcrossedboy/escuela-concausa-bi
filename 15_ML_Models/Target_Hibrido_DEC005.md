---
id: DOC-TARGET-HIBRIDO
title: "Target híbrido de dos niveles para ML-01 (DEC-005)"
owner: "Héctor Rafael Morales Marbán"
status: in_review
traces_up: ["10_Risk_Governance/Risk_Register", "10_Risk_Governance/Decision_Log", "03_Architecture/Data_Model"]
traces_down: ["US-311", "US-313"]
tags: [ml, celula-3, ml-01, dec-005, risk-007]
---

# Target híbrido de dos niveles para ML-01 (DEC-005)

> Implementación de la mitigación de **RISK-007**: el Formato 911 sólo se descargó con el ciclo
> 2024-2025 y sin ≥2 ciclos no hay `target_variacion_matricula` que predecir.
> → [[15_ML_Models/ML01_Entrenamiento]] · [[10_Risk_Governance/Risk_Register]] · [[03_Architecture/Data_Model]]

## 1. Qué separa DEC-005

| | Grano | Fuente |
|---|---|---|
| **Objetivo supervisado** | `municipio × nivel × ciclo` | serie agregada SNIEE (SEP), multi-año |
| **Features y driver dominante** | `cct` (escuela) | 911 2024-2025 + los 6 drivers |

El carácter prescriptivo se conserva: **el driver dominante no se agrega**, así que la
recomendación se sigue emitiendo escuela por escuela. Lo que sube de grano es sólo la etiqueta.

## 2. El hueco que había que resolver

`gold.features_escuela` **no expone `cve_mun` ni `nivel`**. El contrato §5.3 trae `cct`, los seis
drivers, sus banderas, `indice_completitud_drivers` y el target — nada más.

Ambas columnas viven en **`gold.dim_escuela`** (US-103), así que la agregación se resuelve con un
**join a la dimensión**. No hace falta cambiar el contrato de la Célula 1 ni pedirle columnas
nuevas; el acoplamiento entre células no crece.

## 3. Cómo se agregan los drivers

**Un driver agregado es el promedio de las escuelas que sí tienen dato, nunca de las que no.** Una
escuela sin medición de aire no arrastra el promedio de su municipio hacia cero: queda fuera del
cálculo y su ausencia se refleja en la cobertura.

La cobertura pasa de enum a **fracción**:

```
d6_cobertura_frac = escuelas con dato / escuelas del grupo
```

A nivel agregado, «OK / SIN_DATO» pierde información: no es lo mismo un municipio donde mide una
estación de cada diez escuelas que uno donde miden todas. Se conserva **además** el enum del
contrato original, para que un consumidor que sólo entienda `OK`/`SIN_DATO` siga funcionando.

## 4. Lo que la agregación reporta

`ResumenAgregacion` devuelve cuántas escuelas entraron, cuántas **no encontraron su fila en la
dimensión** y qué cobertura tuvo el join. Una escuela sin municipio no desaparece en silencio: se
cuenta. Agregar es justo donde es fácil perder filas sin notarlo.

## 5. Estado

El objetivo real todavía no llega: la serie SNIEE es responsabilidad de la Célula 1 y el **gate de
DEC-005 es el 30 de agosto**. Por eso `unir_target()` **lo recibe como argumento en vez de
calcularlo** — el mismo patrón que usamos en US-313 con el driver de ML-02. Cuando la serie
aterrice, es conectarla.

Si nada llega para el gate, el fallback de DEC-005 es un índice compuesto desde los seis drivers
marcado `SIN_DATO_REAL`.

### Ensayo sobre el fixture

```
entrada: 400 filas escuela×ciclo · 80 escuelas
salida : 230 filas municipio×nivel×ciclo · 46 grupos · 5 ciclos
cobertura de dimensión: 100.0%
```

Los cinco ciclos se conservan, que es lo único que hace validable el objetivo con partición
temporal — el propósito entero de DEC-005.

## 6. Pruebas

`tests/test_target_hibrido.py` — 18 casos (`TEST-009`). Las que importan:

- `test_no_cuenta_la_ausencia_como_cero` — dos escuelas, una sin dato: el promedio es el valor de
  la que sí lo tiene, no su mitad. Un `fillna(0)` antes del promedio hace fallar la prueba.
- `test_conserva_todos_los_ciclos` — agregar no puede perder profundidad temporal.
- `test_reporta_las_escuelas_sin_dimension` — una escuela sin municipio se cuenta, no desaparece.
- `test_un_grupo_sin_objetivo_queda_fuera_y_no_se_rellena` — entrenar contra un cero inventado es
  peor que tener menos filas.
- `test_el_agregado_admite_particion_temporal` — el punto de DEC-005, verificado.

## 7. Pendiente

1. **La serie SNIEE** (Célula 1, gate 30 de agosto). Sin ella el objetivo sigue simulado.
2. **Reentrenar ML-01 sobre el grano agregado** y republicar métricas cuando exista el objetivo real.
3. **Decidir qué se publica en `gold.predicciones`**: hoy la tabla tiene grano `cct × ciclo × modelo`.
   Si ML-01 predice por `municipio × nivel`, hay que definir si la predicción se reparte a las
   escuelas del grupo o si la tabla admite ambos granos. **Toca coordinar con Diana y Christian.**
