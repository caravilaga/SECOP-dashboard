from datetime import date

import pandas as pd

from src.transformar import limpiar, normalizar_texto

HOY = date(2026, 11, 23)


def test_normalizar_texto():
    entrada = pd.Series(["  terminado ", "Salud y Protección Social", "en   ejecución", None])
    salida = normalizar_texto(entrada).tolist()
    assert salida[:3] == ["Terminado", "Salud y Protección Social", "En ejecución"]
    assert pd.isna(salida[3])


def test_limpiar_descarta_negativos_y_fechas_futuras(crudos):
    limpio = limpiar(crudos, hoy=HOY)
    assert set(limpio["id_contrato"]) == {"C1", "C2", "C3"}   # C4 negativo, C5 en 2099


def test_limpiar_convierte_tipos(crudos):
    limpio = limpiar(crudos, hoy=HOY)
    assert pd.api.types.is_datetime64_any_dtype(limpio["fecha_de_firma"])
    assert pd.api.types.is_numeric_dtype(limpio["valor_del_contrato"])


def test_columnas_derivadas(crudos):
    limpio = limpiar(crudos, hoy=HOY).set_index("id_contrato")
    assert limpio.loc["C1", "es_contratacion_directa"]
    assert limpio.loc["C3", "es_contratacion_directa"]       # "Directa (con ofertas)"
    assert not limpio.loc["C2", "es_contratacion_directa"]
    assert limpio.loc["C1", "es_persona_natural"]             # cédula
    assert not limpio.loc["C2", "es_persona_natural"]         # NIT
    assert limpio.loc["C1", "sector"] == "Sin sector"
    assert limpio.loc["C1", "mes_firma"] == "2026-10"
    assert pd.isna(limpio.loc["C2", "duracion_dias"])         # fin antes de inicio
