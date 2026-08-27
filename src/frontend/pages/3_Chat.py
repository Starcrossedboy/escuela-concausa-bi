"""Widget de chat del agente. Historia: US-305.

Entrada de lenguaje natural -> API del agente RAG (US-304/US-323) -> respuesta citada.
"""
import os

import streamlit as st
from agente_client import consultar_agente

API_BASE_URL = os.environ.get("FARO_API_BASE_URL", "http://localhost:8000")

st.title("Agente FARO")
st.caption("Pregunta en lenguaje natural sobre los datos del proyecto.")

access_token = st.session_state.get("access_token")
mensajes = st.session_state.setdefault("mensajes_agente", [])
for mensaje in mensajes:
	with st.chat_message(mensaje["rol"]):
		st.markdown(mensaje["contenido"])
		if mensaje.get("sql"):
			with st.expander("SQL generado"):
				st.code(mensaje["sql"], language="sql")

pregunta = st.chat_input("Escribe tu pregunta sobre escuelas, riesgo o drivers")
if pregunta:
	mensajes.append({"rol": "user", "contenido": pregunta})
	with st.chat_message("user"):
		st.markdown(pregunta)

	with st.chat_message("assistant"):
		try:
			with st.spinner("Consultando FARO..."):
				respuesta = consultar_agente(
					API_BASE_URL,
					pregunta,
					access_token=access_token,
				)
		except (ValueError, OSError) as exc:
			st.error(f"No se pudo consultar el agente: {exc}")
		else:
			estilo = st.warning if respuesta.fuera_de_alcance else st.markdown
			estilo(respuesta.respuesta)
			if respuesta.sql_generado:
				with st.expander("SQL generado"):
					st.code(respuesta.sql_generado, language="sql")
			mensajes.append(
				{
					"rol": "assistant",
					"contenido": respuesta.respuesta,
					"sql": respuesta.sql_generado,
				}
			)
