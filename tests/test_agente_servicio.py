"""Pruebas del flujo seguro de integración del agente FARO."""

from __future__ import annotations

from src.agente import servicio
from src.agente.recuperacion import ErrorRecuperacion
from src.agente.servicio import procesar_consulta, procesar_consulta_con_rag


def test_orquesta_consulta_segura_con_dependencias_inyectadas() -> None:
    llamadas: list[tuple[str, str]] = []

    def recuperar(pregunta: str) -> str:
        llamadas.append(("recuperar", pregunta))
        return "Tabla disponible: gold.features_escuela(cct, indice_riesgo)"

    def generar(prompt: str, pregunta: str) -> str:
        assert "gold.features_escuela" in prompt
        llamadas.append(("generar", pregunta))
        return "SELECT cct FROM gold.features_escuela"

    def ejecutar(sql: str) -> list[dict[str, str]]:
        llamadas.append(("ejecutar", sql))
        return [{"cct": "09ABC0001X"}]

    resultado = procesar_consulta(
        "Que escuelas tienen mayor riesgo?",
        recuperar_contexto=recuperar,
        generar_sql=generar,
        ejecutar_sql=ejecutar,
        redactar_respuesta=lambda pregunta, filas: f"{len(filas)} escuela encontrada.",
    )

    assert resultado.respuesta == "1 escuela encontrada."
    assert resultado.sql_generado == "SELECT cct FROM gold.features_escuela LIMIT 1000;"
    assert not resultado.fuera_de_alcance
    assert [nombre for nombre, _ in llamadas] == ["recuperar", "generar", "ejecutar"]


def test_pregunta_fuera_de_alcance_no_invoca_dependencias() -> None:
    def no_debe_llamarse(*args):
        raise AssertionError("No se deben invocar dependencias para preguntas fuera de alcance")

    resultado = procesar_consulta(
        "Cual es la mejor receta de pasta?",
        recuperar_contexto=no_debe_llamarse,
        generar_sql=no_debe_llamarse,
        ejecutar_sql=no_debe_llamarse,
        redactar_respuesta=no_debe_llamarse,
    )

    assert resultado.fuera_de_alcance
    assert resultado.sql_generado is None


def test_sql_inseguro_nunca_llega_al_ejecutor() -> None:
    ejecutado = False

    def ejecutar(sql: str):
        nonlocal ejecutado
        ejecutado = True
        return []

    resultado = procesar_consulta(
        "Borra el riesgo de una escuela",
        recuperar_contexto=lambda pregunta: "gold.predicciones",
        generar_sql=lambda prompt, pregunta: "DELETE FROM gold.predicciones",
        ejecutar_sql=ejecutar,
        redactar_respuesta=lambda pregunta, filas: "No debe ejecutarse",
    )

    assert resultado.fuera_de_alcance
    assert resultado.sql_generado is None
    assert not ejecutado


def test_fallo_de_recuperacion_no_genera_ni_ejecuta_sql() -> None:
    def recuperar(pregunta: str) -> str:
        raise ErrorRecuperacion("ChromaDB no disponible")

    def no_debe_llamarse(*args):
        raise AssertionError("No debe continuar sin contexto RAG")

    resultado = procesar_consulta(
        "Que escuelas tienen mayor riesgo?",
        recuperar_contexto=recuperar,
        generar_sql=no_debe_llamarse,
        ejecutar_sql=no_debe_llamarse,
        redactar_respuesta=no_debe_llamarse,
    )

    assert resultado.respuesta == "El contexto de FARO no está disponible temporalmente."
    assert resultado.sql_generado is None
    assert not resultado.fuera_de_alcance


def test_entrada_compuesta_usa_recuperacion_rag_real(monkeypatch) -> None:
    monkeypatch.setattr(
        servicio,
        "recuperar_contexto",
        lambda pregunta: "Tabla gold.features_escuela(cct)",
    )

    resultado = procesar_consulta_con_rag(
        "Que escuelas tienen mayor riesgo?",
        generar_sql=lambda prompt, pregunta: "SELECT cct FROM gold.features_escuela",
        ejecutar_sql=lambda sql: [{"cct": "09ABC0001X"}],
        redactar_respuesta=lambda pregunta, filas: "Una escuela.",
    )

    assert resultado.respuesta == "Una escuela."
    assert resultado.sql_generado == "SELECT cct FROM gold.features_escuela LIMIT 1000;"