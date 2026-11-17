"""Guarda contratos crudos en Parquet, particionados por mes de firma."""
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]   # carpeta raíz del repo
DIR_RAW = RAIZ / "data" / "raw"


def agregar_fecha_descarga(df: pd.DataFrame, momento: datetime | None = None) -> pd.DataFrame:
    """Agrega una columna con el momento de la descarga (útil para auditoría)."""
    momento = momento or datetime.now(timezone.utc)
    df = df.copy()
    df["fecha_descarga"] = momento.isoformat(timespec="seconds")
    return df


def mes_de_firma(df: pd.DataFrame) -> pd.Series:
    """'2026-11-03T10:22:00' -> '2026-11'."""
    return df["fecha_de_firma"].str[:7]


def guardar_particionado(df: pd.DataFrame, directorio: Path = DIR_RAW) -> dict:
    """Combina los datos nuevos con los existentes, mes por mes, sin duplicados."""
    directorio.mkdir(parents=True, exist_ok=True)
    resumen = {}

    for mes, nuevos in df.groupby(mes_de_firma(df)):
        archivo = directorio / f"contratos_{mes}.parquet"

        if archivo.exists():
            existentes = pd.read_parquet(archivo)
            combinado = pd.concat([existentes, nuevos], ignore_index=True)
        else:
            existentes = pd.DataFrame()
            combinado = nuevos

        # keep="last": si un contrato ya existía, gana la versión recién descargada
        combinado = (combinado
                     .drop_duplicates(subset="id_contrato", keep="last")
                     .sort_values("id_contrato"))
        combinado.to_parquet(archivo, index=False)

        resumen[mes] = {"antes": len(existentes), "despues": len(combinado)}

    return resumen