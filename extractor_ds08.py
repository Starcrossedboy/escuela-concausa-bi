import pandas as pd
from datetime import datetime, timezone

# --- Configuración ---
SOURCE_FILE = "data/raw/pobproy_quinq1.csv"
SOURCE_NAME = "DS-08_CONAPO_Proyecciones"
SOURCE_URL = "https://www.datos.gob.mx/dataset/proyecciones-de-poblacion/resource/3c3092be-583e-4490-8c23-67ef9a64b198"
OUTPUT_PATH = "data/bronze/ds08_conapo.parquet"

def extraer_ds08():
    # 1. Leemos el archivo ya descargado (CONAPO no tiene link de descarga fijo,
    #    usa sesiones temporales, ver ficha DS-08 sección 10 "Riesgos conocidos")
    df = pd.read_csv(SOURCE_FILE)

    # 2. Limpiamos la clave de municipio (mismo fix que hicimos al explorar)
    df["cve_mun"] = df["CLAVE"].astype(str).str.zfill(5)

    # 3. Agregamos los sellos de metadatos que pide la historia
    df["_ingested_at"] = datetime.now(timezone.utc).isoformat()
    df["_source"] = SOURCE_NAME
    df["_source_url"] = SOURCE_URL

    print(f"Registros procesados: {df.shape[0]}")

    # 4. Guardamos como Parquet en la capa Bronze
    df.to_parquet(OUTPUT_PATH, index=False)
    print(f"Guardado en: {OUTPUT_PATH}")

    return df

if __name__ == "__main__":
    extraer_ds08()