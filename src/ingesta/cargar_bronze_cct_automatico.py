"""Automatiza DS-02 de punta a punta: descarga los 2 ZIP reales del catalogo CCT (via la API
real de SIGED, ver extractor_cct.py -- antes esto era un paso manual, ver
cargar_bronze_cct_real.py), los extrae, y los carga a bronze.cct_siged_202608. Reutiliza
cargar() de cargar_bronze_cct_real.py -- no duplica esa logica de parseo/validacion, solo la
conecta con el extractor automatico.

Uso:
    python -m src.ingesta.cargar_bronze_cct_automatico
    python -m src.ingesta.cargar_bronze_cct_automatico --tabla cct_siged_202608
"""
import argparse
import logging

from src.ingesta.cargar_bronze_cct_real import cargar
from src.ingesta.extractor_cct import extraer_cct

logger = logging.getLogger(__name__)


def cargar_automatico(tabla: str = "cct_siged_202608") -> int:
    ruta_01_16, ruta_17_32 = extraer_cct()
    return cargar(ruta_01_16, ruta_17_32, tabla)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tabla", default="cct_siged_202608")
    args = parser.parse_args()

    n = cargar_automatico(args.tabla)
    print(f"OK: {n} filas nuevas cargadas en bronze.{args.tabla}")
