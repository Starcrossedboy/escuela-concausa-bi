import pandas as pd, pytest
from src.ingesta.cargar_bronze_conagua_real import validar_df

def base():
    return pd.DataFrame({
        "id_presa":["1","2"],"nombre_oficial":["A","B"],"estado":["X","Y"],"cap_namo":[10.0,20.0],
        "_ingested_at":pd.to_datetime(["2026-08-30T00:00:00Z"]*2,utc=True),
        "_source":["DS-06_CONAGUA_SINA"]*2,
        "_source_url":["https://sisuar.imta.mx/aplicacion/controlador/mapa.php"]*2,
    })

def test_ok(): validar_df(base())

def test_dup():
    d=base(); d.loc[1,"id_presa"]="1"
    with pytest.raises(ValueError,match="duplicado"): validar_df(d)

def test_range():
    d=base(); d.loc[0,"cap_namo"]=-1
    with pytest.raises(ValueError,match="cap_namo"): validar_df(d)
