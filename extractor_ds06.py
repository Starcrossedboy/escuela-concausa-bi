import requests
import pandas as pd
from datetime import datetime, timezone

# --- Configuración ---
URL = "https://sisuar.imta.mx/aplicacion/controlador/mapa.php"
SOURCE_NAME = "DS-06_CONAGUA_Presas"
OUTPUT_PATH = "data/bronze/ds06_conagua_presas.parquet"

def extraer_ds06():
    # 1. Armamos el filtro para pedir TODOS los estados (1 al 33) de un jalón
    condiciones = " or ".join([f"id_estado={i}" for i in range(1, 34)])
    query = f"({condiciones})"

    # 2. Armamos el mismo "payload" (los datos del formulario) que capturaste en el navegador
    payload = {
        "query": query,
        "Accion": "Presas"
    }

    # 3. Hacemos la petición POST, igual que hace el navegador al dar clic en "Consultar"
    respuesta = requests.post(URL, data=payload, timeout=30)
    respuesta.raise_for_status()  # avisa si algo salió mal (ej. error 404, 500)

    # 4. Convertimos la respuesta JSON en una tabla de pandas
    datos = respuesta.json()
    df = pd.DataFrame(datos)

    print(f"Registros obtenidos: {df.shape[0]}")
    print(f"Columnas: {df.columns.tolist()}")

    # 5. Agregamos los sellos de metadatos que pide tu historia (US-122a)
    df["_ingested_at"] = datetime.now(timezone.utc).isoformat()
    df["_source"] = SOURCE_NAME
    df["_source_url"] = URL

    # 6. Guardamos como Parquet en la capa Bronze
    df.to_parquet(OUTPUT_PATH, index=False)
    print(f"Guardado en: {OUTPUT_PATH}")

    return df

if __name__ == "__main__":
    extraer_ds06()