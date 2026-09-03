"""Verifica versiones publicadas en MLflow Model Registry (US-303).

Comprueba dos cosas **distintas**, y por eso son dos pasos:

1. Que cada modelo canónico tenga al menos una versión registrada.
2. Que esa versión se pueda **cargar de vuelta**. Una fila `READY` en el Registry no prueba que el
   modelo esté ahí: con el servidor sin `--serve-artifacts`, las métricas se guardan pero los
   artefactos nunca salen del contenedor (**BUG-043**). Sin este segundo paso la verificación da
   verde sobre un modelo que nadie puede usar, que es justo lo que pasó con
   `ML01_RegresionMatricula` v1 entre el 18-ago y el 2-sep.

Uso:

    python -m src.modelos.verificar_registry --tracking-uri http://localhost:5001
    python -m src.modelos.verificar_registry --modelo ML01_RegresionMatricula --sin-artefacto
"""

from __future__ import annotations

import argparse
import os

from src.modelos.mlflow_utils import (
    NOMBRES_MODELOS_CANONICOS,
    verificar_artefactos_descargables,
    verificar_modelos_registrados,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifica modelos canónicos en MLflow Registry.")
    parser.add_argument(
        "--tracking-uri",
        default=os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5001"),
    )
    parser.add_argument(
        "--modelo",
        action="append",
        choices=sorted(NOMBRES_MODELOS_CANONICOS),
        help="Modelo a verificar; puede repetirse. Sin esta opción verifica los tres.",
    )
    parser.add_argument(
        "--sin-artefacto",
        action="store_true",
        help="sólo comprueba que exista la versión, sin intentar cargarla (verificación débil)",
    )
    args = parser.parse_args()

    nombres = frozenset(args.modelo) if args.modelo else NOMBRES_MODELOS_CANONICOS
    versiones = verificar_modelos_registrados(args.tracking_uri, nombres)

    if args.sin_artefacto:
        for nombre, version in sorted(versiones.items()):
            print(f"{nombre}: versión {version} (artefacto NO verificado)")
        return 0

    verificar_artefactos_descargables(args.tracking_uri, versiones)
    for nombre, version in sorted(versiones.items()):
        print(f"{nombre}: versión {version} — carga verificada ✅")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
