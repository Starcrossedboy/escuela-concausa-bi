"""Completa el paso de carga a Postgres que `extractor_formato911_historico.py` deja
pendiente: ese script descarga y parsea cada ciclo real, pero solo escribe Parquet en
`data/bronze/formato911_historico/` -- nunca inserta en `bronze.formato911_historico`.

Motivo de este script: verificado en vivo contra Postgres (2026-09-03) que
`bronze.formato911_historico` solo tenia 30-32 filas por ciclo en los 6 ciclos -- tamano de
fixture de prueba (BUG-026), no de carga real (los CSV reales traen entre 228 mil y 232 mil
filas cct x turno por ciclo, ver DS-01_Formato_911.md SS9). Los 2 ciclos que ademas nunca se
habian intentado cargar aqui son 2019-2020 y 2020-2021.

Reutiliza extraer_formato911_historico() (descarga + parseo, ya probado) y cargar_fixture()
(esquema "formato911_historico", ya registrado en ESQUEMAS de cargar_bronze_fixture.py) -- no
duplica ninguna de las dos logicas, solo conecta la salida de la primera con la entrada de la
segunda (Parquet -> CSV temporal -> Postgres), que es el paso que faltaba.

OJO -- revisar antes de correr en produccion: la UNIQUE de bronze.formato911_historico es
(_source, _ingested_at, cct, ciclo, turno). Como _ingested_at cambia en cada corrida, las 30-32
filas viejas (el fixture de BUG-026) NO se sobreescriben ni se detectan como conflicto -- van a
CONVIVIR con las filas reales nuevas para el mismo ciclo. Si no se quiere esa mezcla, hay que
limpiar las filas viejas a mano antes de correr esto (ver nota en el DevLog de esta sesion) --
este script no borra nada por diseno (CLAUDE.md: nunca DELETE/UPDATE/DROP desde el agente).

Uso:
    python -m src.ingesta.cargar_bronze_formato911_historico_real --ciclos 2019-2020 2020-2021
    python -m src.ingesta.cargar_bronze_formato911_historico_real   # los 6 ciclos completos
"""
import argparse
import logging
import tempfile
from pathlib import Path

import pandas as pd

from src.ingesta.cargar_bronze_fixture import cargar_fixture
from src.ingesta.extractor_formato911_historico import extraer_formato911_historico

logger = logging.getLogger(__name__)


def cargar(ciclos: list = None, tabla: str = "formato911_historico") -> dict:
    """Descarga (via red real), parsea y carga a Postgres los ciclos indicados de la
    distribucion historica de DS-01. Devuelve {ciclo: filas_insertadas}."""
    rutas_parquet = extraer_formato911_historico(ciclos)
    resultado = {}
    for ruta in rutas_parquet:
        df = pd.read_parquet(ruta)
        ciclo = df["ciclo"].iloc[0]
        logger.info("%s: %d filas parseadas desde %s", ciclo, len(df), ruta)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as tmp:
            df.to_csv(tmp.name, index=False)
            tmp_path = tmp.name

        try:
            insertadas = cargar_fixture(tmp_path, tabla, esquema="formato911_historico")
        finally:
            Path(tmp_path).unlink(missing_ok=True)

        logger.info("%s: %d filas nuevas insertadas en bronze.%s", ciclo, insertadas, tabla)
        resultado[ciclo] = insertadas

    return resultado


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--ciclos", nargs="*", default=None,
        help="Ciclos a cargar (ej. 2019-2020 2020-2021). Por default, los 6.",
    )
    parser.add_argument("--tabla", default="formato911_historico")
    args = parser.parse_args()

    resultado = cargar(args.ciclos, args.tabla)
    print("OK:")
    for ciclo, n in resultado.items():
        print(f"  {ciclo}: {n} filas nuevas en bronze.{args.tabla}")
