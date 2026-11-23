from datetime import date

import pandas as pd
import pytest

import src.pipeline as pipeline
from src.pipeline import DatosSospechosos, verificar_caida


def _cubo(mes, contratos):
    return pd.DataFrame({"mes_firma": [mes], "contratos": [contratos]})


def test_verificar_caida_detecta_datos_incompletos(tmp_path):
    archivo = tmp_path / "cubo.parquet"
    _cubo("2026-10", 1000).to_parquet(archivo)
    with pytest.raises(DatosSospechosos):
        verificar_caida(_cubo("2026-10", 300), archivo)


def test_verificar_caida_acepta_cambios_normales(tmp_path):
    archivo = tmp_path / "cubo.parquet"
    _cubo("2026-10", 1000).to_parquet(archivo)
    verificar_caida(_cubo("2026-10", 980), archivo)    # pequeña corrección: no falla
    verificar_caida(_cubo("2026-11", 50), archivo)     # mes nuevo: no hay con qué comparar


def test_pipeline_completo_sin_internet(tmp_path, monkeypatch, crudos):
    """Reemplaza la descarga por datos de prueba y corre todo el pipeline."""
    monkeypatch.setattr(pipeline, "descargar_contratos", lambda *a, **k: crudos)
    cubo, entidades = tmp_path / "cubo.parquet", tmp_path / "entidades.parquet"

    resumen = pipeline.ejecutar(hoy=date(2026, 11, 23), archivo_cubo=cubo, archivo_entidades=entidades)

    assert resumen["contratos_validos"] == 3
    assert resumen["meses_actualizados"] == ["2026-10", "2026-11"]
    assert pd.read_parquet(cubo)["contratos"].sum() == 3
    assert entidades.exists()


def test_pipeline_no_guarda_si_la_api_no_devuelve_nada(tmp_path, monkeypatch, crudos):
    monkeypatch.setattr(pipeline, "descargar_contratos", lambda *a, **k: crudos.iloc[0:0])
    cubo = tmp_path / "cubo.parquet"
    with pytest.raises(DatosSospechosos):
        pipeline.ejecutar(hoy=date(2026, 11, 23), archivo_cubo=cubo,
                          archivo_entidades=tmp_path / "entidades.parquet")
    assert not cubo.exists()
