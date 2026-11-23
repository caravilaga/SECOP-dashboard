"""Datos de prueba compartidos por todas las pruebas."""
import pandas as pd
import pytest


@pytest.fixture
def crudos():
    """Contratos tal como llegan de la API: todo como texto."""
    return pd.DataFrame({
        "id_contrato": ["C1", "C2", "C3", "C4", "C5"],
        "nombre_entidad": ["Alcaldía A", "Alcaldía A", "Gobernación B", "Hospital C", "Alcaldía A"],
        "nit_entidad": ["1", "1", "2", "3", "1"],
        "departamento": ["Antioquia", "Antioquia", "Valle del Cauca", "Antioquia", "Antioquia"],
        "ciudad": ["Medellín"] * 5,
        "orden": ["Territorial"] * 5,
        "sector": ["No aplica/No pertenece", "Salud", "deportes", "Salud", "Salud"],
        "estado_contrato": [" terminado", "En ejecución", "En ejecución", "Aprobado", "En ejecución"],
        "tipo_de_contrato": ["Prestación de servicios", "Obra", "Prestación de servicios",
                             "Suministros", "Obra"],
        "modalidad_de_contratacion": ["Contratación directa", "Licitación pública",
                                      "Contratación Directa (con ofertas)", "Mínima cuantía",
                                      "Licitación pública"],
        "tipodocproveedor": ["Cédula de Ciudadanía", "NIT", "Cédula de Ciudadanía", "NIT", None],
        "proveedor_adjudicado": ["P1", "P2", "P3", "P4", "P5"],
        "es_pyme": ["No", "Si", "No", "Sí", "No"],
        "valor_del_contrato": ["1000000", "50000000", "2000000", "-5", "3000000"],
        "valor_pagado": ["0"] * 5,
        "origen_de_los_recursos": ["Recursos propios"] * 5,
        "fecha_de_firma": ["2026-10-05T10:00:00", "2026-10-20T09:00:00", "2026-11-03T08:00:00",
                           "2026-11-04T08:00:00", "2099-01-01T00:00:00"],
        "fecha_de_inicio_del_contrato": ["2026-10-06T00:00:00"] * 5,
        "fecha_de_fin_del_contrato": ["2026-12-31T00:00:00", "2026-10-01T00:00:00",
                                      "2026-12-31T00:00:00", "2026-12-31T00:00:00",
                                      "2026-12-31T00:00:00"],
        "objeto_del_contrato": ["x"] * 5,
        "urlproceso": ["u"] * 5,
    })
