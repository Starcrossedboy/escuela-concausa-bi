import pandas as pd

from src.ingesta.extractor_cemabe import conformar_cemabe


def test_conformar_cemabe_mapea_contrato_y_retira_turno():
    inmuebles = pd.DataFrame(
        [
            {
                "ID_INM": "000001",
                "P17A": "1",
                "P18A": "5",
                "P21": "9",
                "P22": "2",
            }
        ]
    )
    centros = pd.DataFrame(
        [
            {
                "ID_INM": "000001",
                "CLAVE_CT": "09DPR0001A1",
                "P268": "1",
                "P277": "0",
            }
        ]
    )

    resultado = conformar_cemabe(inmuebles, centros).iloc[0].to_dict()

    assert resultado == {
        "cct": "09DPR0001A",
        "agua_red": "1",
        "drenaje": "0",
        "electricidad": "0",
        "sanitarios": "",
        "internet": "1",
        "computadoras": "0",
    }


def test_conformar_cemabe_consolida_turnos_y_excluye_claves_temporales():
    inmuebles = pd.DataFrame(
        [
            {
                "ID_INM": "000002",
                "P17A": "2",
                "P18A": "1",
                "P21": "1",
                "P22": "1",
            }
        ]
    )
    centros = pd.DataFrame(
        [
            {
                "ID_INM": "000002",
                "CLAVE_CT": "15DST0002B1",
                "P268": "2",
                "P277": "9999",
            },
            {
                "ID_INM": "000002",
                "CLAVE_CT": "15DST0002B2",
                "P268": "1",
                "P277": "4",
            },
            {
                "ID_INM": "000002",
                "CLAVE_CT": "15DJNTEMP31",
                "P268": "1",
                "P277": "4",
            },
        ]
    )

    resultado = conformar_cemabe(inmuebles, centros)

    assert resultado.to_dict("records") == [
        {
            "cct": "15DST0002B",
            "agua_red": "0",
            "drenaje": "1",
            "electricidad": "1",
            "sanitarios": "1",
            "internet": "1",
            "computadoras": "1",
        }
    ]
