"""Métricas agregadas para el tablero (capa gold)."""
import json
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
DIR_GOLD = RAIZ / "data" / "gold"


def resumen_mensual(df: pd.DataFrame) -> pd.DataFrame:
    tabla = df.groupby("mes_firma").agg(contratos=("id_contrato", "count"),
        valor_total=("valor_del_contrato", "sum"),
        valor_mediano=("valor_del_contrato", "median"),
        pct_directa=("es_contratacion_directa", "mean"),
        pct_pyme = ("es_pyme", "mean")).reset_index().sort_values("mes_firma")
    tabla['p_natural'] = 1 - tabla['pct_pyme']
    return (tabla)



def ranking(df: pd.DataFrame, columna: str, n: int | None = 10) -> pd.DataFrame:
    tabla = (df.groupby(columna)
               .agg(contratos=("id_contrato", "count"),
                    valor_total=("valor_del_contrato", "sum"))
               .reset_index()
               .sort_values("valor_total", ascending=False))
    return tabla if n is None else tabla.head(n)


def por_modalidad(df: pd.DataFrame) -> pd.DataFrame:
    tabla = ranking(df, "modalidad_de_contratacion", n=None)
    tabla["pct_valor"] = tabla["valor_total"] / tabla["valor_total"].sum()
    return tabla


def kpis(df: pd.DataFrame) -> dict:
    return {
        "contratos": int(len(df)),
        "valor_total": float(df["valor_del_contrato"].sum()),
        "pct_contratacion_directa": round(float(df["es_contratacion_directa"].mean()), 4),
        "pct_pyme": round(float(df["es_pyme"].mean()), 4),
        "fecha_min": df["fecha_de_firma"].min().strftime("%Y-%m-%d"),
        "fecha_max": df["fecha_de_firma"].max().strftime("%Y-%m-%d"),
    }


def generar_gold(df: pd.DataFrame, directorio: Path = DIR_GOLD) -> dict:
    """Calcula todas las métricas y las guarda como CSV + JSON."""
    directorio.mkdir(parents=True, exist_ok=True)
    tablas = {
        "resumen_mensual": resumen_mensual(df),
        "top_entidades": ranking(df, "nombre_entidad"),
        "top_proveedores": ranking(df, "proveedor_adjudicado"),
        "por_modalidad": por_modalidad(df),
    }
    for nombre, tabla in tablas.items():
        tabla.to_csv(directorio / f"{nombre}.csv", index=False)

    (directorio / "kpis.json").write_text(
        json.dumps(kpis(df), indent=2, ensure_ascii=False), encoding="utf-8")
    return tablas