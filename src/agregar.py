"""Tablas agregadas que se guardan en el repo (reemplazan a data/raw).

En vez de un contrato por fila, se guarda una fila por combinación de
mes × departamento × tipo de contrato × modalidad. Son tablas pequeñas, sin datos
personales, y sus sumas se pueden recombinar para cualquier filtro del tablero.
"""
from datetime import date
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
DIR_AGREGADOS = RAIZ / "data" / "agregados"
ARCHIVO_CUBO = DIR_AGREGADOS / "cubo.parquet"
ARCHIVO_ENTIDADES = DIR_AGREGADOS / "entidades.parquet"

DIMENSIONES_CUBO = ["mes_firma", "departamento", "tipo_de_contrato", "modalidad_de_contratacion"]
DIMENSIONES_ENTIDADES = ["mes_firma", "departamento", "tipo_de_contrato", "nombre_entidad"]
SIN_DATO = "Sin dato"


def inicio_ventana(hoy: date, meses_atras: int = 1) -> date:
    """Primer día del mes que está `meses_atras` meses antes del mes de `hoy`.

    La ventana siempre empieza el día 1 para que cada mes descargado quede completo:
    así se puede reemplazar el mes entero en las tablas agregadas.
    Ejemplo: hoy=2026-11-20, meses_atras=1 -> 2026-10-01.
    """
    anio, mes = hoy.year, hoy.month - meses_atras
    while mes <= 0:
        mes += 12
        anio -= 1
    return date(anio, mes, 1)


def _rellenar_vacios(df: pd.DataFrame, columnas: list) -> pd.DataFrame:
    """groupby descarta las filas con dimensiones vacías; las marcamos como 'Sin dato'."""
    return df.assign(**{c: df[c].fillna(SIN_DATO) for c in columnas})


def agregar_cubo(limpio: pd.DataFrame) -> pd.DataFrame:
    df = _rellenar_vacios(limpio, DIMENSIONES_CUBO[1:])
    return (df.groupby(DIMENSIONES_CUBO, as_index=False)
              .agg(contratos=("id_contrato", "count"),
                   valor=("valor_del_contrato", "sum"),
                   n_directa=("es_contratacion_directa", "sum"),
                   n_natural=("es_persona_natural", "sum"),
                   n_pyme=("es_pyme", "sum")))


def agregar_entidades(limpio: pd.DataFrame) -> pd.DataFrame:
    df = _rellenar_vacios(limpio, DIMENSIONES_ENTIDADES[1:])
    return (df.groupby(DIMENSIONES_ENTIDADES, as_index=False)
              .agg(contratos=("id_contrato", "count"),
                   valor=("valor_del_contrato", "sum")))


def actualizar_tabla(nuevos: pd.DataFrame, archivo: Path) -> pd.DataFrame:
    """Reemplaza por completo los meses que vienen en `nuevos` y conserva los demás.

    Es idempotente: correrlo dos veces con los mismos datos deja la misma tabla.
    """
    archivo.parent.mkdir(parents=True, exist_ok=True)
    if archivo.exists():
        existentes = pd.read_parquet(archivo)
        meses_nuevos = nuevos["mes_firma"].unique()
        existentes = existentes[~existentes["mes_firma"].isin(meses_nuevos)]
        tabla = pd.concat([existentes, nuevos], ignore_index=True)
    else:
        tabla = nuevos.copy()

    tabla = tabla.sort_values(list(tabla.columns[:4])).reset_index(drop=True)
    tabla.to_parquet(archivo, index=False)
    return tabla