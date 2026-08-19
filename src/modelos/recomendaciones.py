"""Catálogo canónico de recomendaciones prescriptivas de ML-02 (US-302)."""

from __future__ import annotations

RECOMENDACION_POR_DRIVER: dict[str, str] = {
    "D1": "Priorizar programas de becas y apoyo alimentario en la zona.",
    "D2": "Coordinar con seguridad pública rutas escolares seguras y entornos protegidos.",
    "D3": "Gestionar rehabilitación de infraestructura escolar prioritaria.",
    "D4": "Ampliar conectividad y dotación de equipo de cómputo.",
    "D5": "Asegurar suministro de agua y planes de contingencia hídrica.",
    "D6": "Activar protocolos por contingencia de calidad del aire.",
}

CODIGOS_DRIVER: tuple[str, ...] = tuple(RECOMENDACION_POR_DRIVER)


def recomendacion_para_driver(driver: str) -> str:
    """Devuelve la recomendación prescriptiva asociada al driver dominante."""
    try:
        return RECOMENDACION_POR_DRIVER[driver]
    except KeyError as exc:
        raise ValueError(
            f"Driver desconocido: {driver!r}. Esperado uno de {CODIGOS_DRIVER}."
        ) from exc