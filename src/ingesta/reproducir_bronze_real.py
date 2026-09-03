"""Camino A completo (BLOCK-004, ver Blocker_Register.md y DS-01_Formato_911.md SS11): reproduce
la carga real de Bronze en un solo comando -- DS-02 (catalogo CCT, automatizado 2026-09-03, ver
extractor_cct.py) + DS-01 historico (ya automatizado, ver
cargar_bronze_formato911_historico_real.py).

NO incluye bronze.formato911_2024_2025 (DS-01, ciclo unico 2024-2025, PR #105): esa descarga
sigue siendo manual (--csv) porque no se automatizo en esta sesion -- viene de
repodatos.atdt.gob.mx via el boton de datos.gob.mx, un mecanismo distinto al de SIGED, no
verificado hoy. Ver cargar_bronze_formato911_real.py si hace falta cargarla tambien.

Idempotente de punta a punta (ON CONFLICT DO NOTHING en ambas cargas, igual que sus scripts por
separado) -- correrlo dos veces no duplica filas. No corre `dbt run` al final: lo imprime como
siguiente paso, para no asumir que dbt esta configurado en el ambiente de quien lo corre.

Uso:
    python -m src.ingesta.reproducir_bronze_real
"""
import logging

from src.ingesta.cargar_bronze_cct_automatico import cargar_automatico as cargar_cct
from src.ingesta.cargar_bronze_formato911_historico_real import cargar as cargar_historico

logger = logging.getLogger(__name__)


def reproducir() -> None:
    logger.info("=== DS-02: catalogo CCT ===")
    n_cct = cargar_cct()
    logger.info("DS-02: %d fila(s) nueva(s) en bronze.cct_siged_202608", n_cct)

    logger.info("=== DS-01: historico (6 ciclos) ===")
    resultado_historico = cargar_historico()
    for ciclo, n in resultado_historico.items():
        logger.info("DS-01 historico %s: %d fila(s) nueva(s)", ciclo, n)

    print()
    print("Bronze real cargado (DS-02 + DS-01 historico). Siguiente paso:")
    print("  dbt run && dbt test")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    reproducir()
