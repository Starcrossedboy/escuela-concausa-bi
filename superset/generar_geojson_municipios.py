#!/usr/bin/env python3
"""
FARO — Generar el asset GeoJSON de municipios del alcance (US-203).

Descarga (una vez) los GeoJSON municipales por estado del espejo comunitario
del Marco Geoestadístico de INEGI (CONABIO 2020-2023, repo PhantomInsights/
mexico-geojson), filtra las 4 entidades de SCOPE_ENTIDADES (09, 14, 15, 19),
simplifica las geometrías con Douglas-Peucker y redondea coordenadas para que
el asset quede en ~200-400 KB (límite de repo: 5 MB).

El resultado es `superset/assets/geojson/municipios_scope.geojson`, versionado
en el repo para que el coroplético de DB-02 funcione en cualquier clone sin
descargas. Los datos son públicos (INEGI/CONABIO, MIT el espejo); la llave de
cada feature es CVEGEO (5 dígitos = cve_ent + cve_mun_local), igual que
`gold.dim_municipio.cve_mun`.

Uso:
    # 1) descargar los 4 estados a un directorio temporal
    python superset/generar_geojson_municipios.py --descargar <dir_tmp>
    # 2) filtrar + simplificar y escribir el asset
    python superset/generar_geojson_municipios.py --generar <dir_tmp>

Sin dependencias externas (stdlib only): corre en cualquier venv.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import urllib.parse
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ASSET = RAIZ / "superset" / "assets" / "geojson" / "municipios_scope.geojson"

# Espejo comunitario del Marco Geoestadístico INEGI (CONABIO 2020-2023, MIT).
BASE_URL = (
    "https://raw.githubusercontent.com/PhantomInsights/mexico-geojson/"
    "main/2023/states"
)
ESTADOS_SCOPE = {
    "09": "Ciudad de México",
    "14": "Jalisco",
    "15": "México",
    "19": "Nuevo León",
}

# Tolerancia Douglas-Peucker en grados (2e-3 ≈ 200 m; para un coroplético
# municipal es más que suficiente y mantiene el asset bien por debajo de 1 MB).
TOLERANCIA_DP = 0.002
DECIMALES = 4  # ~11 m de precisión tras el redondeo


# --------------------------------------------------------------------------- descarga


def descargar(dir_tmp: Path) -> None:
    dir_tmp.mkdir(parents=True, exist_ok=True)
    for cve_ent, nombre in ESTADOS_SCOPE.items():
        destino = dir_tmp / f"{cve_ent}.json"
        url = f"{BASE_URL}/{urllib.parse.quote(nombre)}.json"
        print(f"↓ {nombre} → {destino.name}")
        with urllib.request.urlopen(url, timeout=120) as resp, destino.open("wb") as fh:
            fh.write(resp.read())
    print("✔ Descarga completa")


# --------------------------------------------------------------------------- simplificación


def _perp_dist(p: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> float:
    """Distancia del punto p al segmento ab (proyección, grados)."""
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    if dx == dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def _douglas_peucker(puntos: list[tuple[float, float]], tol: float) -> list[tuple[float, float]]:
    if len(puntos) < 3:
        return puntos
    a, b = puntos[0], puntos[-1]
    dist_max, idx = 0.0, 0
    for i in range(1, len(puntos) - 1):
        d = _perp_dist(puntos[i], a, b)
        if d > dist_max:
            dist_max, idx = d, i
    if dist_max > tol:
        izq = _douglas_peucker(puntos[: idx + 1], tol)
        der = _douglas_peucker(puntos[idx:], tol)
        return izq[:-1] + der
    return [a, b]


def _simplificar_anillo(anillo: list[list[float]]) -> list[list[float]]:
    pts = [(float(x), float(y)) for x, y in anillo]
    if len(pts) <= 4:
        return [[round(x, DECIMALES), round(y, DECIMALES)] for x, y in pts]
    cerrado = pts[0] == pts[-1]
    simplificado = _douglas_peucker(pts, TOLERANCIA_DP)
    if len(simplificado) < 4:  # un polígono válido necesita ≥ 4 posiciones
        simplificado = pts
    if cerrado and simplificado[0] != simplificado[-1]:
        simplificado.append(simplificado[0])
    return [[round(x, DECIMALES), round(y, DECIMALES)] for x, y in simplificado]


def _simplificar(geom: dict) -> dict:
    tipo = geom["type"]
    if tipo == "Polygon":
        return {"type": tipo, "coordinates": [_simplificar_anillo(a) for a in geom["coordinates"]]}
    if tipo == "MultiPolygon":
        return {
            "type": tipo,
            "coordinates": [
                [_simplificar_anillo(a) for a in poligono] for poligono in geom["coordinates"]
            ],
        }
    raise ValueError(f"Geometría no soportada: {tipo}")


# --------------------------------------------------------------------------- generación


def generar(dir_tmp: Path) -> None:
    features: list[dict] = []
    for cve_ent, nombre in ESTADOS_SCOPE.items():
        ruta = dir_tmp / f"{cve_ent}.json"
        data = json.loads(ruta.read_text(encoding="utf-8"))
        n_antes = len(features)
        for feat in data["features"]:
            props = feat["properties"]
            if str(props.get("CVE_ENT", "")).zfill(2) != cve_ent:
                continue
            features.append({
                "type": "Feature",
                "properties": {
                    "cve_mun": str(props["CVEGEO"]).zfill(5),      # llave contra gold.dim_municipio
                    "nombre_municipio": props.get("NOMGEO", ""),
                    "cve_ent": cve_ent,
                    "nombre_entidad": props.get("NOM_ENT", ""),
                },
                "geometry": _simplificar(feat["geometry"]),
            })
        print(f"✔ {nombre}: {len(features) - n_antes} municipios")

    asset = {"type": "FeatureCollection", "features": features}
    ASSET.parent.mkdir(parents=True, exist_ok=True)
    ASSET.write_text(
        json.dumps(asset, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    peso_kb = ASSET.stat().st_size / 1024
    print(f"✔ Asset escrito: {ASSET} ({len(features)} municipios, {peso_kb:.0f} KB)")
    if peso_kb > 1024:
        print("⚠ El asset superó 1 MB; sube TOLERANCIA_DP o baja DECIMALES")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--descargar", metavar="DIR", help="Descarga los 4 estados a DIR")
    parser.add_argument("--generar", metavar="DIR", help="Genera el asset desde los archivos en DIR")
    args = parser.parse_args()

    if args.descargar:
        descargar(Path(args.descargar))
    if args.generar:
        generar(Path(args.generar))
    if not args.descargar and not args.generar:
        parser.print_help()


if __name__ == "__main__":
    main()
