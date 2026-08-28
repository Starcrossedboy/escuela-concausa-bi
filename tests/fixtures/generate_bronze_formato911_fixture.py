"""Genera tests/fixtures/bronze_formato911_sample.csv — muestra sintética y anonimizada
de bronze.formato911 (DS-01) para poder correr y probar dbt/models/silver/matricula.sql
localmente mientras la URL real de Formato 911 sigue bloqueada para descarga automática.

No sustituye la ingesta real (src/ingesta/extractor_formato911.py): es solo fixture de
prueba, <=500 filas, sin datos personales (grano escuela, nunca alumno), por
_Meta/Vault_Rules.md / CLAUDE.md §3 "Nunca subas datos reales pesados".

A propósito incluye "suciedad" real que Silver debe resolver (Data_Model.md §3):
- CCT en minúsculas y con menos de 10 caracteres (homologación: lpad + upper)
- `entidad`/`municipio` como enteros sin ceros a la izquierda (homologación INEGI 5 dígitos)
- Un mismo (cct, ciclo) ingestado dos veces con distinto _ingested_at (dedupe: se queda el más
  reciente) — simula un re-run idempotente del extractor
- Entidades fuera de SCOPE_ENTIDADES (Bronze/Silver son nacionales; el filtro va en Gold)
"""
import random
from datetime import datetime, timedelta, timezone

import pandas as pd

random.seed(7)

SOURCE_NAME = "DS-01_FORMATO911"
SOURCE_URL = "https://repodatos.atdt.gob.mx/api_update/secretaria_educacion/registro_alumnado_personal_docente_educacion_basica_media_superior_formato_911/educacion_basica_2024_2025.csv"

# entidad -> lista de claves de municipio (INEGI, sin homologar todavía) usadas en el fixture
MUNICIPIOS_POR_ENTIDAD = {
    "09": [2, 3, 5],     # CDMX (SCOPE)
    "15": [33, 106, 20], # Edomex (SCOPE)
    "19": [39, 6],       # Nuevo León (SCOPE)
    "14": [39, 98],      # Jalisco (SCOPE)
    "20": [67],          # Oaxaca (fuera de SCOPE_ENTIDADES; Silver es nacional igual)
    "1":  [1],           # Aguascalientes — entidad de 1 dígito a propósito (homologar a "01")
}
NIVELES = ["PREESCOLAR", "PRIMARIA", "SECUNDARIA"]
# Códigos de 2 letras (el CCT oficial son siempre 10 caracteres exactos: EE T LL NNNN X).
TIPO_POR_NIVEL = {"PREESCOLAR": "JN", "PRIMARIA": "PR", "SECUNDARIA": "SN"}
CICLOS = ["2023-2024", "2024-2025"]

base_ingest = datetime(2026, 8, 18, 12, 0, 0, tzinfo=timezone.utc)

rows = []
folio = 0
for ciclo in CICLOS:
    for entidad, municipios in MUNICIPIOS_POR_ENTIDAD.items():
        for municipio in municipios:
            for nivel in NIVELES:
                folio += 1
                tipo = TIPO_POR_NIVEL[nivel]
                cct = f"{int(entidad):02d}D{tipo}{folio:04d}A"
                alumnos = random.randint(40, 420)
                docentes = max(1, round(alumnos / random.randint(18, 28)))
                grupos = max(1, round(alumnos / random.randint(20, 35)))

                row = {
                    "cct": cct,
                    "ciclo": ciclo,
                    "entidad": entidad,       # a propósito sin lpad (p.ej. "1" en vez de "01")
                    "municipio": municipio,   # a propósito sin lpad (int, no str de 3 dígitos)
                    "nivel": nivel,
                    "alumnos_total": alumnos,
                    "docentes_total": docentes,
                    "grupos_total": grupos,
                    "_ingested_at": base_ingest.isoformat(),
                    "_source": SOURCE_NAME,
                    "_source_url": SOURCE_URL,
                }
                rows.append(row)

# Caso 1: CCT "sucio" (minúsculas, sin cero a la izquierda) para una fila ya generada arriba
rows[3]["cct"] = rows[3]["cct"].lower().lstrip("0")

# Caso 2: reingesta del mismo (cct, ciclo) con _ingested_at más reciente y matrícula corregida
# — Silver debe quedarse con esta versión, no con la primera
reingesta = dict(rows[0])
reingesta["alumnos_total"] = reingesta["alumnos_total"] + 5
reingesta["_ingested_at"] = (base_ingest + timedelta(days=1)).isoformat()
rows.append(reingesta)

df = pd.DataFrame(rows)
output_path = "tests/fixtures/bronze_formato911_sample.csv"
df.to_csv(output_path, index=False)
print(f"Fixture generado: {output_path} ({len(df)} filas, {df['cct'].nunique()} CCT únicos, "
      f"{df['ciclo'].nunique()} ciclos)")