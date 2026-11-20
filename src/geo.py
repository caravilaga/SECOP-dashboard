"""Geometría de los departamentos y equivalencia de nombres SECOP -> código DANE."""
import json
import re
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
ARCHIVO_GEO = RAIZ / "data" / "geo" / "departamentos.geo.json"
CAMPO_CODIGO = "DPTO_CCDGO"     # código DANE del departamento en el GeoJSON
CAMPO_NOMBRE = "DPTO_CNMBR"


def normalizar_nombre(nombre: str) -> str:
    """'Bogotá, D.C.' -> 'BOGOTA D C'. Quita tildes, signos y espacios de más."""
    sin_tildes = unicodedata.normalize("NFKD", str(nombre)).encode("ascii", "ignore").decode()
    solo_letras = re.sub(r"[^A-Za-z ]", " ", sin_tildes)
    return re.sub(r"\s+", " ", solo_letras).strip().upper()


def _redondear(coordenadas, decimales: int):
    """Redondea coordenadas anidadas (reduce el peso del archivo sin cambiar el dibujo)."""
    if isinstance(coordenadas[0], (int, float)):
        return [round(c, decimales) for c in coordenadas]
    return [_redondear(c, decimales) for c in coordenadas]


def cargar_geojson(archivo: Path = ARCHIVO_GEO, decimales: int = 3) -> dict:
    geo = json.loads(archivo.read_text(encoding="utf-8"))
    for f in geo["features"]:
        f["geometry"]["coordinates"] = _redondear(f["geometry"]["coordinates"], decimales)
        f["properties"] = {CAMPO_CODIGO: f["properties"][CAMPO_CODIGO],
                           CAMPO_NOMBRE: f["properties"][CAMPO_NOMBRE]}
    return geo


def tabla_codigos(geo: dict) -> dict:
    """Nombre normalizado del GeoJSON -> código DANE."""
    return {normalizar_nombre(f["properties"][CAMPO_NOMBRE]): f["properties"][CAMPO_CODIGO]
            for f in geo["features"]}


def codigo_dane(nombre_secop: str, codigos: dict) -> str | None:
    """Busca el código DANE de un departamento escrito como en SECOP."""
    n = normalizar_nombre(nombre_secop)
    if "BOGOTA" in n:                 # SECOP: 'Distrito Capital de Bogotá'
        return "11"
    if "SAN ANDRES" in n:             # SECOP: 'San Andrés, Providencia y Santa Catalina'
        return "88"
    return codigos.get(n)