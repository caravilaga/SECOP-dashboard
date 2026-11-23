"""Limpieza de contratos crudos (capa silver)."""
from datetime import date

import pandas as pd

COLUMNAS_FECHA = ["fecha_de_firma", "fecha_de_inicio_del_contrato", "fecha_de_fin_del_contrato"]
COLUMNAS_VALOR = ["valor_del_contrato", "valor_pagado"]
COLUMNAS_TEXTO = [
    "nombre_entidad", "departamento", "ciudad", "orden", "sector", "estado_contrato",
    "tipo_de_contrato", "modalidad_de_contratacion", "proveedor_adjudicado",
    "origen_de_los_recursos",
]
REEMPLAZOS_SECTOR = {"No aplica/No pertenece": "Sin sector"}


def normalizar_texto(serie: pd.Series) -> pd.Series:
    """Quita espacios sobrantes y pone mayúscula inicial sin alterar el resto."""
    s = serie.astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
    return s.str[:1].str.upper() + s.str[1:]


def limpiar(df: pd.DataFrame, hoy: date | None = None) -> pd.DataFrame:
    """Convierte tipos, normaliza categorías y descarta filas inválidas."""
    hoy = pd.Timestamp(hoy or date.today())
    df = df.copy()

    # 1. Tipos de datos
    for col in COLUMNAS_FECHA:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in COLUMNAS_VALOR:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 2. Texto y categorías
    for col in COLUMNAS_TEXTO:
        df[col] = normalizar_texto(df[col])
    df["sector"] = df["sector"].replace(REEMPLAZOS_SECTOR)
    df["es_pyme"] = df["es_pyme"].astype("string").str.strip().str.lower().isin(["si", "sí"])

    # 3. Columnas derivadas
    df["es_contratacion_directa"] = df["modalidad_de_contratacion"].str.contains(
        "directa", case=False, na=False)
    df["es_persona_natural"] = ~df["tipodocproveedor"].astype("string").str.upper().str.contains(
        "NIT", na=True)
    df["mes_firma"] = df["fecha_de_firma"].dt.to_period("M").astype(str)
    df["duracion_dias"] = (
        df["fecha_de_fin_del_contrato"] - df["fecha_de_inicio_del_contrato"]
    ).dt.days
    df.loc[df["duracion_dias"] < 0, "duracion_dias"] = pd.NA

    # 4. Reglas de validez
    valido = (
        df["fecha_de_firma"].notna()
        & (df["fecha_de_firma"] < hoy + pd.Timedelta(days=1))
        & df["valor_del_contrato"].notna()
        & (df["valor_del_contrato"] >= 0)
    )
    descartados = int((~valido).sum())
    if descartados:
        print(f"Se descartaron {descartados} filas inválidas")

    return df[valido].reset_index(drop=True)
