---
id: TEST-003
title: "Partición temporal y fixture de features — ML-01"
owner: "Héctor Rafael Morales Marbán"
status: implemented
traces_up: ["02_Requirements/User_Stories", "02_Requirements/Requirements_Detailed"]
tags: [qa, testing, unit, celula-3, ml]
---

# TEST-003 — Partición temporal y fixture de features (ML-01)

> Valida **AC-003.3** (partición temporal, nunca aleatoria) y el fixture simulado que desbloquea
> [[02_Requirements/User_Stories|US-311]] mientras la Célula 1 publica `gold.features_escuela`.
> → [[06_Quality_Testing/Automated/_index]] · [[15_ML_Models/_index]]

## Qué valida

| Ruta en repo | Comando | Casos | Corre en |
|---|---|---|---|
| `tests/test_particion_temporal.py` | `pytest tests/ -q` | 15 | CI |

Cubre dos cosas distintas:

1. **El fixture cumple el contrato.** Grano CCT × ciclo sin duplicados, las 16 columnas de
   `FeaturesEscuela`, tope de 500 filas, coherencia `SIN_DATO` ⇔ valor nulo, coherencia de
   `indice_completitud_drivers` y pertenencia de los CCT a las 4 entidades del alcance.
2. **La partición no tiene fuga temporal.** Ciclos ordenados cronológicamente, sin traslape entre
   entrenamiento y prueba, entrenamiento estrictamente anterior a la prueba, ventanas de
   backtesting crecientes, y rechazo explícito de particiones inválidas.

### El caso que más importa

`test_particion_aleatoria_es_rechazada` baraja el fixture, lo parte a la mitad y verifica que
`verificar_sin_fuga()` levante `ValueError`. Convierte **AC-003.3 de regla escrita en regla que el
CI hace cumplir**: si alguien —persona o IA— sustituye la partición por un `train_test_split`
aleatorio, la suite falla.

## El fixture

**Datos 100 % sintéticos.** Ningún CCT corresponde a una escuela real y no hay dato personal
alguno. Cumple el §8 del plan de sprint: muestra pequeña, determinista y anonimizada.

| | |
|---|---|
| **Archivo** | `tests/fixtures/features_escuela_mock.csv` (44 KB) |
| **Generador** | `python -m src.modelos.generar_fixture` (semilla fija `20260808`) |
| **Filas** | 400 = 80 escuelas × 5 ciclos (2019-2020 … 2023-2024) |
| **Cobertura media** | `indice_completitud_drivers` ≈ 0.83 · 405 celdas `SIN_DATO` de 2 400 |

El generador es **idempotente**: regenerarlo produce un archivo byte a byte idéntico, así que no
mete diff espurio en los PR.

### Qué reproduce y qué no

**Sí:** el grano, las columnas, el rango [0,1] de los drivers, la ausencia explícita `SIN_DATO` y
su coherencia con el nulo, y una cobertura desigual entre drivers parecida a la real — D5 es
regional y D6 cubre ~80 zonas urbanas, así que fallan más seguido que D1–D4.

**No:** las distribuciones reales de cada driver. Sirve para validar la mecánica de la partición y
del pipeline, **no para sacar conclusiones sustantivas ni métricas comparables con las reales.**

## Dependencia abierta

`src/modelos/contrato.py` es un **espejo temporal** del contrato de
[[03_Architecture/Data_Model|Data_Model §5.3]], que produce la Célula 1. Cuando Diana Alvarez
publique su módulo Pydantic canónico, el espejo se borra y se importa el suyo; si divergen, manda
el contrato. `src/modelos/particion_temporal.py` **no** depende del contrato: sólo usa `id_ciclo`.

## Cómo reproducir

```bash
source .venv/bin/activate
python -m src.modelos.generar_fixture      # regenera el fixture (determinista)
pytest tests/ -q                            # 15 passed
```
