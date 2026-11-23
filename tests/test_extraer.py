from datetime import date

from src.extraer import construir_filtro

DESDE, HASTA = date(2026, 10, 1), date(2026, 11, 23)


def test_filtro_todo_el_pais_no_empieza_con_and():
    filtro = construir_filtro(None, DESDE, HASTA)
    assert not filtro.strip().upper().startswith("AND")
    assert "departamento" not in filtro


def test_filtro_con_departamento():
    filtro = construir_filtro("Valle del Cauca", DESDE, HASTA)
    assert filtro.startswith("departamento = 'Valle del Cauca' AND ")
    assert filtro.count(" AND ") == 2


def test_filtro_escapa_comillas():
    filtro = construir_filtro("Departamento d'Prueba", DESDE, HASTA)
    assert "d''Prueba" in filtro


def test_filtro_incluye_todo_el_ultimo_dia():
    assert "fecha_de_firma <= '2026-11-23T23:59:59'" in construir_filtro(None, DESDE, HASTA)
