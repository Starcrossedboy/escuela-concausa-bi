"""TEST-014 — El gate de propiedad reprueba lo que tiene que reprobar.

Cubre las tres reglas de `vault/_Meta/scripts/check_ownership.py`: identidad reconocida,
rama fija correcta y alcance respetado. La regla de la rama es la que cierra el error H-09
—ramas gemelas con el apellido materno o el segundo nombre—, así que tiene su propio caso.
"""

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "vault" / "_Meta" / "scripts"))

from check_ownership import coincide, leer_ownership

OWNERSHIP = RAIZ / "vault" / "_Meta" / "ownership.yml"


@pytest.fixture(scope="module")
def datos():
    return leer_ownership(str(OWNERSHIP))


# ── El padrón está completo y es coherente ───────────────────────────────────


def test_estan_las_21_personas(datos):
    assert len(datos["personas"]) == 21


def test_cada_identidad_tiene_su_rama_fija(datos):
    for identidad, persona in datos["personas"].items():
        assert persona["rama"] == f"dev/{identidad}"


def test_no_hay_handles_de_github_repetidos(datos):
    handles = [p["github"].lower() for p in datos["personas"].values()]
    assert len(handles) == len(set(handles))


def test_cada_plan_de_sprint_existe(datos):
    for identidad, persona in datos["personas"].items():
        assert (RAIZ / persona["plan"]).exists(), f"{identidad}: falta {persona['plan']}"


def test_cada_persona_tiene_su_agent_context(datos):
    for identidad in datos["personas"]:
        ruta = RAIZ / "vault/09_AI_Governance/Agent_Contexts" / f"{identidad}-agent-context.md"
        assert ruta.exists(), f"falta el Agent Context de {identidad}"


def test_los_duenos_de_rutas_criticas_son_personas_del_padron(datos):
    for patron, dueno in datos["criticos"].items():
        assert dueno in datos["personas"], f"{patron} apunta a `{dueno}`, que no existe"


# ── Un solo dueño por ruta crítica: es la corrección de C10 ──────────────────


def test_src_frontend_tiene_un_solo_dueno_en_verde(datos):
    en_verde = [
        i for i, p in datos["personas"].items() if "src/frontend/**" in p.get("verde", [])
    ]
    assert en_verde == ["manuel-serrania"]


def test_quien_no_es_dueno_de_src_frontend_lo_tiene_en_amarillo(datos):
    for identidad in ("andres-gonzalez", "christian-ruiz", "marina-garcia"):
        assert "src/frontend/**" in datos["personas"][identidad]["amarillo"]


# ── El emparejado de rutas ───────────────────────────────────────────────────


@pytest.mark.parametrize(
    "ruta,patrones,esperado",
    [
        ("src/ingesta/extractor_cemabe.py", ["src/ingesta/**"], True),
        ("src/ingesta/sub/dir/x.py", ["src/ingesta/**"], True),
        ("src/api/app.py", ["src/ingesta/**"], False),
        ("docker-compose.yml", ["docker-compose.yml"], True),
        ("vault/03_Architecture/Data_Model.md", ["vault/03_Architecture/Data_Model.md"], True),
        ("vault/03_Architecture/ADR-001.md", ["vault/03_Architecture/Data_Model.md"], False),
        # `src/ingesta` no debe cubrir a `src/ingesta_vieja`
        ("src/ingesta_vieja/x.py", ["src/ingesta/**"], False),
    ],
)
def test_coincide(ruta, patrones, esperado):
    assert coincide(ruta, patrones) is esperado


def test_el_devlog_propio_es_comun_pero_el_ajeno_no(datos):
    comunes_diana = [p.replace("{id}", "diana-alvarez") for p in datos["comunes"]]
    assert coincide("vault/_DevLog/2026-09-01-diana-alvarez-us113.md", comunes_diana)
    assert not coincide("vault/_DevLog/2026-09-01-luis-tellez-us502.md", comunes_diana)


# ── Los alias que producían ramas gemelas quedan fuera del padrón ────────────


@pytest.mark.parametrize(
    "alias",
    ["hector-marban", "diana-varela", "edgar-navarrete", "imanol", "eloisa",
     "karla-benitez", "juan-mayen", "oscar-lazaro", "monserrat-olivas"],
)
def test_ningun_alias_historico_resuelve_a_una_rama(datos, alias):
    ramas = {p["rama"] for p in datos["personas"].values()}
    assert f"dev/{alias}" not in ramas
    assert alias not in datos["personas"]
