"""Construye el tablero: prepara los datos (JSON) y los inserta en la plantilla HTML.

Python solo prepara datos pequeños y agregados. El dibujo de las gráficas y los
filtros los hace JavaScript (Plotly.js) en el navegador, por eso la página puede
filtrar sin necesitar un servidor.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.agregar import ARCHIVO_CUBO, ARCHIVO_ENTIDADES, SIN_DATO
from src.geo import CAMPO_CODIGO, cargar_geojson, codigo_dane, tabla_codigos

RAIZ = Path(__file__).resolve().parents[1]
PLANTILLA = Path(__file__).resolve().parent / "plantilla_tablero.html"
DIR_SITIO = RAIZ / "site"

# Periodo de restricción a la contratación directa (Ley de Garantías, elecciones 2026)
LEY_GARANTIAS = {"inicio": "2026-01-31", "fin": "2026-06-22",
                 "mes_desde": "2026-02", "mes_hasta": "2026-06"}
MIN_CONTRATOS_MAPA = 30     # con menos contratos el porcentaje es muy inestable
TOP_ENTIDADES = 10


def _indices(serie: pd.Series, orden: list) -> pd.Series:
    """Convierte textos en índices de una lista (reduce mucho el tamaño del JSON)."""
    return serie.map({valor: i for i, valor in enumerate(orden)}).astype(int)


def top_entidades_por_filtro(entidades: pd.DataFrame, deptos: list, tipos: list) -> dict:
    """Top de entidades para cada combinación de filtros, incluida 'todos' (-1)."""
    base = (entidades.groupby(["departamento", "tipo_de_contrato", "nombre_entidad"], as_index=False)
                     [["contratos", "valor"]].sum())
    resultado = {}
    for d in [-1] + list(range(len(deptos))):
        por_depto = base if d < 0 else base[base["departamento"] == deptos[d]]
        for t in [-1] + list(range(len(tipos))):
            sub = por_depto if t < 0 else por_depto[por_depto["tipo_de_contrato"] == tipos[t]]
            if sub.empty:
                continue
            top = (sub.groupby("nombre_entidad", as_index=False)[["contratos", "valor"]].sum()
                      .nlargest(TOP_ENTIDADES, "valor"))
            resultado[f"{d}|{t}"] = top[["nombre_entidad", "contratos", "valor"]].values.tolist()
    return resultado


def preparar_datos(cubo: pd.DataFrame, entidades: pd.DataFrame, geo: dict) -> dict:
    # El primer mes siempre está incompleto (la carga histórica empezó a mitad de mes)
    meses = sorted(cubo["mes_firma"].unique())[1:]
    cubo = cubo[cubo["mes_firma"].isin(meses)]
    entidades = entidades[entidades["mes_firma"].isin(meses)]

    # Listas de valores: ordenadas por número de contratos (lo más común primero)
    def por_volumen(col):
        return cubo.groupby(col)["contratos"].sum().sort_values(ascending=False).index.tolist()

    deptos = sorted(cubo["departamento"].unique(), key=lambda d: (d == SIN_DATO, d))
    tipos = por_volumen("tipo_de_contrato")
    modalidades = por_volumen("modalidad_de_contratacion")

    codigos = tabla_codigos(geo)
    codigos_deptos = [codigo_dane(d, codigos) for d in deptos]
    sin_mapa = [d for d, c in zip(deptos, codigos_deptos) if c is None]
    if sin_mapa:
        print("Aviso: departamentos sin polígono en el mapa:", sin_mapa)

    filas = pd.DataFrame({
        "m": _indices(cubo["mes_firma"], meses),
        "d": _indices(cubo["departamento"], deptos),
        "t": _indices(cubo["tipo_de_contrato"], tipos),
        "mo": _indices(cubo["modalidad_de_contratacion"], modalidades),
        "n": cubo["contratos"].astype(int),
        "v": cubo["valor"].round(0),
        "nd": cubo["n_directa"].astype(int),
        "nn": cubo["n_natural"].astype(int),
        "np": cubo["n_pyme"].astype(int),
    })

    return {
        "actualizado": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "mes_en_curso": datetime.now(timezone.utc).strftime("%Y-%m"),
        "meses": meses,
        "deptos": deptos,
        "codigos": codigos_deptos,
        "tipos": tipos,
        "modalidades": modalidades,
        "filas": filas.values.tolist(),     # columnas: m, d, t, mo, n, v, nd, nn, np
        "entidades": top_entidades_por_filtro(entidades, deptos, tipos),
        "ley_garantias": LEY_GARANTIAS,
        "min_contratos_mapa": MIN_CONTRATOS_MAPA,
        "campo_codigo": CAMPO_CODIGO,
    }


def _json_para_html(objeto) -> str:
    """JSON seguro para incrustar dentro de <script> (evita cerrar la etiqueta por accidente)."""
    return json.dumps(objeto, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def construir_pagina(archivo_cubo: Path = ARCHIVO_CUBO,
                     archivo_entidades: Path = ARCHIVO_ENTIDADES,
                     salida: Path = DIR_SITIO) -> Path:
    cubo = pd.read_parquet(archivo_cubo)
    entidades = pd.read_parquet(archivo_entidades)
    geo = cargar_geojson()

    datos = preparar_datos(cubo, entidades, geo)
    html = (PLANTILLA.read_text(encoding="utf-8")
            .replace("__DATOS__", _json_para_html(datos))
            .replace("__GEO__", _json_para_html(geo)))

    salida.mkdir(parents=True, exist_ok=True)
    archivo = salida / "index.html"
    archivo.write_text(html, encoding="utf-8")
    return archivo


if __name__ == "__main__":
    print("Página generada en:", construir_pagina())