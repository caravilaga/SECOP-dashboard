from datetime import date

import pandas as pd
import pytest

from src.agregar import actualizar_tabla, agregar_cubo, inicio_ventana
from src.transformar import limpiar


@pytest.mark.parametrize("hoy, esperado", [
    (date(2026, 11, 23), date(2026, 10, 1)),
    (date(2026, 11, 1), date(2026, 10, 1)),
    (date(2026, 1, 15), date(2025, 12, 1)),    # cambio de año
])
def test_inicio_ventana(hoy, esperado):
    assert inicio_ventana(hoy, meses_atras=1) == esperado


def test_cubo_no_pierde_ni_duplica_contratos(crudos):
    limpio = limpiar(crudos, hoy=date(2026, 11, 23))
    cubo = agregar_cubo(limpio)
    assert cubo["contratos"].sum() == len(limpio)
    assert cubo["valor"].sum() == limpio["valor_del_contrato"].sum()
    assert cubo["n_directa"].sum() == limpio["es_contratacion_directa"].sum()


def _tabla(mes, contratos):
    return pd.DataFrame({"mes_firma": [mes], "departamento": ["Antioquia"],
                         "tipo_de_contrato": ["Obra"], "modalidad_de_contratacion": ["Licitación pública"],
                         "contratos": [contratos]})


def test_actualizar_tabla_reemplaza_solo_los_meses_nuevos(tmp_path):
    archivo = tmp_path / "cubo.parquet"
    actualizar_tabla(pd.concat([_tabla("2026-09", 10), _tabla("2026-10", 20)]), archivo)
    tabla = actualizar_tabla(_tabla("2026-10", 25), archivo)
    assert dict(zip(tabla["mes_firma"], tabla["contratos"])) == {"2026-09": 10, "2026-10": 25}


def test_actualizar_tabla_es_idempotente(tmp_path):
    archivo = tmp_path / "cubo.parquet"
    nuevos = pd.concat([_tabla("2026-10", 20), _tabla("2026-11", 5)])
    primera = actualizar_tabla(nuevos, archivo)
    segunda = actualizar_tabla(nuevos, archivo)
    pd.testing.assert_frame_equal(primera, segunda)
