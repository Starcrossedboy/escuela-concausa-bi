"""Evaluación comparativa de los modelos y análisis de error (US-312).

Cierra AC-003.2: *"cada modelo reporta su métrica, documentadas y **reproducibles**"*. El énfasis
está en lo último — este módulo genera el reporte de
`06_Quality_Testing/Automated/Evaluacion_Modelos.md` desde el código, no a mano, para que las
cifras del vault nunca se desincronicen de las que produce el pipeline.

## Qué evalúa

| Modelo | Métrica principal | Origen |
|---|---|---|
| ML-01 · regresión de matrícula | MAE / RMSE | `entrenar_ml01` (US-311) |
| ML-02 · clasificación de driver | F1 macro / accuracy | `entrenar_ml02` (US-302, Andrés) |
| ML-03 · clustering | Silhouette | **pendiente** — US-321 (Estefany) |

Ambos comparten la misma partición temporal, así que sus ventanas son comparables entre sí.

## Sobre las "curvas"

La historia pide curvas. Se emiten como **tablas de datos por ventana** —la evolución del error a
lo largo del backtesting— y no como imágenes:

- Una tabla es diffable: en un PR se ve exactamente qué métrica cambió y cuánto. Un PNG sólo se ve
  distinto.
- El vault versiona artefactos de texto; meter binarios regenerables contradice su higiene.
- La misma serie alimenta después los tableros de la Célula 2, que es donde la curva *se dibuja*.

`--figuras` renderiza los PNG en local para la demo, sin versionarlos.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from src.modelos.contrato import DRIVERS, entidad_de_cct
from src.modelos.entrenar_ml01 import COLUMNA_TARGET as TARGET_ML01
from src.modelos.entrenar_ml01 import cargar_features
from src.modelos.entrenar_ml01 import entrenar_y_evaluar as entrenar_ml01
from src.modelos.entrenar_ml02 import cargar_features_ml02, columna_target_disponible
from src.modelos.entrenar_ml02 import entrenar_y_evaluar as entrenar_ml02

REPORTE_POR_DEFECTO = Path("06_Quality_Testing/Automated/Evaluacion_Modelos.md")

#: Umbrales provisionales de aceptación de `15_ML_Models/ML_Strategy` §5.
UMBRALES: dict[str, float] = {
    "ML-01_mae": 0.03,
    "ML-01_rmse": 0.05,
    "ML-02_f1_macro": 0.60,
    "ML-03_silhouette": 0.30,
}


@dataclass(frozen=True)
class FilaComparativa:
    """Una línea de la tabla comparativa entre modelos."""

    modelo: str
    tipo: str
    metrica: str
    valor: float
    desviacion: float
    baseline: float
    mejora: float
    ventanas: int

    @property
    def supera_baseline(self) -> bool:
        return self.mejora > 0


def _resumen_ml01(resultado) -> FilaComparativa:
    return FilaComparativa(
        modelo="ML-01",
        tipo="regresión",
        metrica="MAE",
        valor=resultado.mae_promedio,
        desviacion=resultado.mae_desviacion,
        baseline=float(np.mean([v.mae_baseline for v in resultado.ventanas])),
        mejora=float(np.mean([v.mejora_sobre_baseline for v in resultado.ventanas])),
        ventanas=len(resultado.ventanas),
    )


def _resumen_ml02(resultado) -> FilaComparativa:
    return FilaComparativa(
        modelo="ML-02",
        tipo="clasificación",
        metrica="F1 macro",
        valor=resultado.f1_macro_promedio,
        desviacion=resultado.f1_macro_desviacion,
        baseline=float(np.mean([v.f1_macro_baseline for v in resultado.ventanas])),
        mejora=float(np.mean([v.mejora_sobre_baseline for v in resultado.ventanas])),
        ventanas=len(resultado.ventanas),
    )


def tabla_comparativa(resultado_ml01, resultado_ml02) -> pd.DataFrame:
    """Tabla comparativa de los modelos evaluados.

    ML-01 y ML-02 optimizan cosas distintas (error absoluto vs F1), así que **sus métricas no se
    comparan entre sí**. Lo comparable es la columna `mejora`: cuánto aporta cada modelo sobre su
    propio baseline.
    """
    filas = [_resumen_ml01(resultado_ml01), _resumen_ml02(resultado_ml02)]
    return pd.DataFrame([f.__dict__ for f in filas])


def curva_por_ventana(resultado_ml01, resultado_ml02) -> pd.DataFrame:
    """Evolución de la métrica a lo largo de las ventanas de backtesting.

    Es la "curva" de la historia, en forma de datos. Permite ver si el modelo se degrada conforme
    predice ciclos más lejanos del inicio de la serie.
    """
    filas = []
    for i, v in enumerate(resultado_ml01.ventanas, start=1):
        filas.append(
            {
                "ventana": i,
                "modelo": "ML-01",
                "ciclo_prueba": v.particion.ciclos_prueba[0],
                "metrica": "MAE",
                "valor": v.mae,
                "baseline": v.mae_baseline,
                "mejora": v.mejora_sobre_baseline,
                "n_entrena": v.n_entrena,
            }
        )
    for i, v in enumerate(resultado_ml02.ventanas, start=1):
        filas.append(
            {
                "ventana": i,
                "modelo": "ML-02",
                "ciclo_prueba": v.particion.ciclos_prueba[0],
                "metrica": "F1 macro",
                "valor": v.f1_macro,
                "baseline": v.f1_macro_baseline,
                "mejora": v.mejora_sobre_baseline,
                "n_entrena": v.n_entrena,
            }
        )
    return pd.DataFrame(filas)


def error_por_entidad(df: pd.DataFrame, resultado_ml01) -> pd.DataFrame:
    """Error de ML-01 desglosado por entidad federativa, sobre la ventana de producción.

    `features_escuela` no trae `cve_ent`; la entidad se deriva del CCT. Sirve para detectar si el
    modelo funciona peor en alguna entidad, que es distinto de que el error global sea aceptable.
    """
    particion = resultado_ml01.ventana_produccion.particion
    _, prueba = particion.aplicar(df)
    from src.modelos.entrenar_ml01 import _matriz

    # Las columnas deben ser las del entrenamiento: si un driver quedó fuera por falta de datos,
    # pasarlo aquí rompe el predict — y es justo el caso que este reporte tiene que documentar.
    columnas = list(getattr(resultado_ml01.modelo, "feature_names_in_", DRIVERS))
    predicho = resultado_ml01.modelo.predict(_matriz(prueba, columnas))

    detalle = pd.DataFrame(
        {
            "entidad": [entidad_de_cct(c) for c in prueba["cct"]],
            "error_absoluto": np.abs(prueba[TARGET_ML01].to_numpy() - predicho),
        }
    )
    tabla = (
        detalle.groupby("entidad")
        .agg(escuelas=("error_absoluto", "size"), mae=("error_absoluto", "mean"))
        .reset_index()
    )
    mae_global = float(detalle["error_absoluto"].mean())
    tabla["desviacion_vs_global"] = tabla["mae"] / mae_global - 1.0
    return tabla.sort_values("mae", ascending=False, ignore_index=True)


def cobertura_y_error(df: pd.DataFrame, resultado_ml01) -> pd.DataFrame:
    """Relaciona el error con `indice_completitud_drivers`.

    Responde una pregunta que el proyecto se hace explícitamente: **¿predecimos peor donde hay menos
    datos?** Si el error crece al bajar la completitud, el sistema es menos confiable justo en las
    zonas con cobertura parcial, y eso hay que declararlo.
    """
    particion = resultado_ml01.ventana_produccion.particion
    _, prueba = particion.aplicar(df)
    from src.modelos.entrenar_ml01 import _matriz

    # Las columnas deben ser las del entrenamiento: si un driver quedó fuera por falta de datos,
    # pasarlo aquí rompe el predict — y es justo el caso que este reporte tiene que documentar.
    columnas = list(getattr(resultado_ml01.modelo, "feature_names_in_", DRIVERS))
    predicho = resultado_ml01.modelo.predict(_matriz(prueba, columnas))
    detalle = pd.DataFrame(
        {
            "completitud": prueba["indice_completitud_drivers"].to_numpy(),
            "error_absoluto": np.abs(prueba[TARGET_ML01].to_numpy() - predicho),
        }
    )
    detalle["tramo"] = pd.cut(
        detalle["completitud"],
        bins=[-0.01, 0.5, 0.83, 1.01],
        labels=["≤ 3 de 6 drivers", "4-5 de 6", "6 de 6"],
    )
    return (
        detalle.groupby("tramo", observed=False)
        .agg(escuelas=("error_absoluto", "size"), mae=("error_absoluto", "mean"))
        .reset_index()
    )


def drivers_en_el_modelo(resultado_ml01, resultado_ml02) -> pd.DataFrame:
    """Qué drivers entraron a cada modelo y cuáles quedaron fuera por falta de datos.

    Que un driver no aporte **nada** es un hallazgo del proyecto, no un detalle de implementación:
    significa que su fuente no está llegando. Hasta ahora eso sólo existía como un `print` en la
    consola de quien corría el entrenamiento y como un campo del resultado en memoria; aquí queda
    en el artefacto publicado, que es donde se puede citar.

    Args:
        resultado_ml01: `ResultadoEntrenamiento` de ML-01.
        resultado_ml02: `ResultadoML02` de ML-02.

    Returns:
        Una fila por driver, con su estado en cada modelo.
    """
    usados_01, usados_02 = set(resultado_ml01.drivers_usados), set(resultado_ml02.drivers_usados)
    return pd.DataFrame(
        {
            "driver": list(DRIVERS),
            "ML-01": ["entró" if d in usados_01 else "**fuera**" for d in DRIVERS],
            "ML-02": ["entró" if d in usados_02 else "**fuera**" for d in DRIVERS],
        }
    )


def exclusiones_por_ventana(resultado_ml01, resultado_ml02) -> pd.DataFrame:
    """Detalle por ventana: un driver puede faltar sólo en el tramo con el que se entrena.

    Es la distinción que costó dos vueltas descubrir (BUG-015): un driver ausente **siempre** es un
    hueco de fuente, mientras que uno ausente **sólo en las ventanas viejas** se resuelve solo en
    cuanto haya más ciclos cargados. No son el mismo problema ni tienen el mismo dueño.
    """
    filas: list[dict[str, str]] = []
    for modelo, resultado in (("ML-01", resultado_ml01), ("ML-02", resultado_ml02)):
        por_ventana = getattr(resultado, "excluidos_por_ventana", None) or {}
        for ventana, fuera in por_ventana.items():
            filas.append(
                {"modelo": modelo, "ventana": ventana, "sin_datos": ", ".join(fuera)}
            )
    if not filas:
        return pd.DataFrame({"modelo": [], "ventana": [], "sin_datos": []})
    return pd.DataFrame(filas)


def _md(df: pd.DataFrame, decimales: int = 4) -> str:
    """DataFrame → tabla Markdown, con números estables para que el diff sea legible."""
    copia = df.copy()
    for col in copia.select_dtypes(include=[float]).columns:
        copia[col] = copia[col].map(lambda v: f"{v:.{decimales}f}")
    encabezado = "| " + " | ".join(copia.columns) + " |"
    separador = "|" + "|".join(["---"] * len(copia.columns)) + "|"
    filas = ["| " + " | ".join(str(v) for v in fila) + " |" for fila in copia.to_numpy()]
    return "\n".join([encabezado, separador, *filas])


def _parrafo_exclusiones(fuera_ml01: tuple[str, ...], fuera_ml02: tuple[str, ...]) -> str:
    """Redacta el hallazgo en prosa, para que el reporte se lea sin descifrar la tabla."""
    if not fuera_ml01 and not fuera_ml02:
        return "Los seis drivers tienen datos suficientes: **ningún driver quedó fuera**."
    partes = []
    if fuera_ml01:
        partes.append(f"ML-01 entrena con {len(DRIVERS) - len(fuera_ml01)} de {len(DRIVERS)} "
                      f"drivers; queda fuera `{'`, `'.join(fuera_ml01)}`")
    if fuera_ml02:
        partes.append(f"ML-02 con {len(DRIVERS) - len(fuera_ml02)} de {len(DRIVERS)}; "
                      f"queda fuera `{'`, `'.join(fuera_ml02)}`")
    return "**" + ". ".join(partes) + ".**"


def construir_reporte(df: pd.DataFrame, resultado_ml01, resultado_ml02) -> str:
    """Genera el documento Markdown completo, con frontmatter listo para el vault."""
    comparativa = tabla_comparativa(resultado_ml01, resultado_ml02)
    curva = curva_por_ventana(resultado_ml01, resultado_ml02)
    entidades = error_por_entidad(df, resultado_ml01)
    cobertura = cobertura_y_error(df, resultado_ml01)
    drivers = drivers_en_el_modelo(resultado_ml01, resultado_ml02)
    exclusiones = exclusiones_por_ventana(resultado_ml01, resultado_ml02)
    fuera_01 = resultado_ml01.drivers_excluidos
    fuera_02 = resultado_ml02.drivers_excluidos
    target_ml02 = resultado_ml02.columna_target_usada
    peor = entidades.iloc[0]

    return f"""---
id: DOC-EVALUACION-MODELOS
title: "Evaluación comparativa de modelos y análisis de error"
owner: "Héctor Rafael Morales Marbán"
status: in_review
traces_up: ["02_Requirements/Requirements_Detailed", "15_ML_Models/ML_Strategy"]
traces_down: ["US-312"]
tags: [qa, ml, celula-3, metricas]
---

# Evaluación comparativa de modelos y análisis de error

> **Documento generado por `src/modelos/evaluar.py`. No editar a mano.**
> Regenerar con `python -m src.modelos.evaluar`. Así las cifras del vault no se desincronizan de
> las que produce el pipeline, que es lo que exige AC-003.2 al pedir métricas *reproducibles*.
> → [[06_Quality_Testing/Automated/_index]] · [[15_ML_Models/ML01_Entrenamiento]] · [[15_ML_Models/ML_Strategy]]

> [!warning] Métricas sobre datos sintéticos
> Se evalúa contra `tests/fixtures/features_escuela_mock.csv`. Las cifras validan que el pipeline
> de evaluación funciona; **no son resultados de negocio**. Se regeneran cuando la Célula 1
> publique `gold.features_escuela` (US-104).

## 1. Tabla comparativa

{_md(comparativa)}

ML-01 y ML-02 optimizan cosas distintas —error absoluto contra F1—, así que **sus métricas no se
comparan entre sí**. Lo comparable es `mejora`: cuánto aporta cada modelo sobre su propio baseline.
Un modelo que no supera su baseline no aporta nada, sin importar qué tan buena se vea su métrica.

ML-02 se entrena hoy contra `{target_ml02}`. Si es el proxy determinista, su F1 mide la capacidad
de recuperar una etiqueta derivada de los propios drivers, **no de predecir un driver observado**;
la cifra se vuelve significativa cuando Gold publique la etiqueta real.

## 2. Curva de error por ventana

{_md(curva)}

Es la "curva" de la historia en forma de datos: permite ver si el modelo se degrada conforme
predice ciclos más lejanos del inicio de la serie. Se emite como tabla y no como imagen porque un
diff de PR muestra exactamente qué métrica cambió; un PNG sólo se ve distinto. `--figuras` las
renderiza en local para la demo, sin versionarlas.

## 3. Error por entidad (ML-01, ventana de producción)

{_md(entidades)}

`desviacion_vs_global` es la diferencia relativa contra el MAE global de la ventana. La entidad con
peor desempeño es **{peor["entidad"]}**, con MAE {peor["mae"]:.4f}
({peor["desviacion_vs_global"]:+.1%} respecto al global).

Importa porque un error global aceptable puede esconder una entidad en la que el modelo funciona
mal, y las recomendaciones prescriptivas se emiten escuela por escuela.

## 4. Error contra cobertura de drivers

{_md(cobertura)}

Responde la pregunta que el proyecto se hace explícitamente: **¿predecimos peor donde hay menos
datos?** Si el error crece al bajar la completitud, el sistema es menos confiable justo en las
zonas con cobertura parcial —y eso debe declararse junto a la predicción, no esconderse.

## 5. Drivers que entraron al modelo

{_md(drivers)}

{_parrafo_exclusiones(fuera_01, fuera_02)}

Un driver excluido **no es un ajuste técnico**: es una fuente que no está llegando. Aparece aquí, y
no sólo en la consola de quien entrena, porque es una cifra que el proyecto tiene que poder citar —
decir "el modelo entrena con 5 de 6 drivers" obliga a decir también cuál falta y por qué.

Los `SIN_DATO` de un driver que sí entró no se imputan: llegan al modelo como ausencia real
(`HistGradientBoosting` los maneja de forma nativa). Lo que se excluye es únicamente el driver que
no tiene **ningún** valor con el que aprender.

### 5.1 Exclusiones por ventana

{_md(exclusiones)}

La cobertura se evalúa dentro de cada ventana de entrenamiento, no sobre el conjunto completo. La
distinción importa y tiene dueños distintos: un driver ausente en **todas** las ventanas es un hueco
de fuente que alguien debe ir a buscar; uno ausente sólo en las **más viejas** —porque su serie
apenas empieza— se resuelve solo conforme se carguen más ciclos.

## 6. Umbrales de aceptación

`15_ML_Models/ML_Strategy` §5 fija: ML-01 MAE < {UMBRALES["ML-01_mae"]} (3 puntos porcentuales) y
RMSE < {UMBRALES["ML-01_rmse"]} (5 puntos porcentuales); ML-02 F1 macro ≥
{UMBRALES["ML-02_f1_macro"]}; ML-03 Silhouette ≥ {UMBRALES["ML-03_silhouette"]}.

ML-01 usa la misma unidad proporcional de `target_variacion_matricula`: `0.0141` equivale a un
error medio de 1.41 puntos porcentuales. No se convierte a alumnos porque el contrato de features
no incluye la matrícula base necesaria para hacerlo de forma reproducible. Los umbrales son
provisionales hasta ejecutar la evaluación contra los datos reales de US-104.

## 7. Cobertura de la evaluación

| Modelo | Estado |
|---|---|
| ML-01 · regresión | ✅ evaluado |
| ML-02 · clasificación | ✅ evaluado (target `{target_ml02}`) |
| ML-03 · clustering | ⬜ **pendiente** — US-321 (Estefany Hernández), aún sin implementar |

AC-003.2 no queda cerrado hasta que ML-03 reporte su Silhouette.
"""


def main() -> int:
    """Entrena, evalúa y escribe el reporte."""
    parser = argparse.ArgumentParser(description="Evalúa los modelos y documenta métricas (US-312).")
    parser.add_argument("--features", type=Path, default=None)
    parser.add_argument("--ventanas", type=int, default=3)
    parser.add_argument("--salida", type=Path, default=REPORTE_POR_DEFECTO)
    parser.add_argument("--figuras", type=Path, default=None, help="directorio para PNG (no se versionan)")
    args = parser.parse_args()

    df01 = cargar_features(args.features) if args.features else cargar_features()
    df02 = cargar_features_ml02(args.features) if args.features else cargar_features_ml02()

    resultado_ml01 = entrenar_ml01(df01, n_ventanas=args.ventanas)
    resultado_ml02 = entrenar_ml02(df02, n_ventanas=args.ventanas)
    print(f"ML-01 MAE {resultado_ml01.mae_promedio:.4f} ± {resultado_ml01.mae_desviacion:.4f}")
    print(
        f"ML-02 F1 {resultado_ml02.f1_macro_promedio:.4f} ± {resultado_ml02.f1_macro_desviacion:.4f}"
        f" (target: {columna_target_disponible(df02)})"
    )

    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.write_text(construir_reporte(df01, resultado_ml01, resultado_ml02), encoding="utf-8")
    print(f"Reporte escrito en {args.salida}")

    if args.figuras:
        _renderizar_figuras(resultado_ml01, resultado_ml02, args.figuras)
    return 0


def _renderizar_figuras(resultado_ml01, resultado_ml02, destino: Path) -> None:
    """Renderiza las curvas como PNG. Sólo para la demo: no se versionan."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    destino.mkdir(parents=True, exist_ok=True)
    curva = curva_por_ventana(resultado_ml01, resultado_ml02)
    for modelo, grupo in curva.groupby("modelo"):
        figura, eje = plt.subplots(figsize=(7, 4))
        eje.plot(grupo["ciclo_prueba"], grupo["valor"], marker="o", label=grupo["metrica"].iloc[0])
        eje.plot(grupo["ciclo_prueba"], grupo["baseline"], marker="s", linestyle="--", label="baseline")
        eje.set_title(f"{modelo} — error por ventana de backtesting")
        eje.set_xlabel("ciclo evaluado")
        eje.legend()
        figura.tight_layout()
        figura.savefig(destino / f"{modelo.lower().replace('-', '')}_curva.png", dpi=120)
        plt.close(figura)
    print(f"Figuras escritas en {destino} (no se versionan)")


if __name__ == "__main__":
    raise SystemExit(main())
