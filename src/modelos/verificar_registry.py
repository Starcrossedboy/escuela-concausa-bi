"""Verifica versiones publicadas en MLflow Model Registry (US-303)."""

from __future__ import annotations

import argparse
import os

from src.modelos.mlflow_utils import (
    NOMBRES_MODELOS_CANONICOS,
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
    args = parser.parse_args()

    nombres = frozenset(args.modelo) if args.modelo else NOMBRES_MODELOS_CANONICOS
    versiones = verificar_modelos_registrados(args.tracking_uri, nombres)
    for nombre, version in sorted(versiones.items()):
        print(f"{nombre}: versión {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())