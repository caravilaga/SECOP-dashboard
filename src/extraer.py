"""Extracción de contratos de SECOP II desde datos.gov.co (API Socrata)."""
import os
import time
from datetime import date, timedelta

import pandas as pd
import requests

URL = "https://www.datos.gov.co/resource/jbjy-vk9h.json"
TAMANO_PAGINA = 10_000

COLUMNAS = [
    "id_contrato", "nombre_entidad", "nit_entidad", "departamento", "ciudad",
    "orden", "sector", "estado_contrato", "tipo_de_contrato",
    "modalidad_de_contratacion", "tipodocproveedor", "proveedor_adjudicado", "es_pyme",
    "valor_del_contrato", "valor_pagado", "origen_de_los_recursos",
    "fecha_de_firma", "fecha_de_inicio_del_contrato", "fecha_de_fin_del_contrato",
    "objeto_del_contrato", "urlproceso",
]


def construir_filtro(departamento: str | None, desde: date, hasta: date) -> str:
    """Arma la cláusula $where de SoQL. Si departamento es None, trae todo el país."""
    condiciones = [
        f"fecha_de_firma >= '{desde.isoformat()}T00:00:00'",
        f"fecha_de_firma <= '{hasta.isoformat()}T23:59:59'",
    ]
    if departamento:
        departamento = departamento.replace("'", "''")   # escapa comillas simples
        condiciones.insert(0, f"departamento = '{departamento}'")
    return " AND ".join(condiciones)


def _pedir_pagina(params: dict, intentos: int = 3) -> list:
    """Hace una petición a la API con reintentos si falla la red."""
    headers = {}
    token = os.getenv("SOCRATA_APP_TOKEN")
    if token:
        headers["X-App-Token"] = token

    for intento in range(1, intentos + 1):
        try:
            resp = requests.get(URL, params=params, headers=headers, timeout=(10, 60))
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as error:
            if intento == intentos:
                raise
            espera = 5 * intento
            print(f"Intento {intento} falló ({error}). Reintento en {espera}s...")
            time.sleep(espera)


def descargar_contratos(departamento: str | None = None, dias_atras: int = 30,
                        hoy: date | None = None) -> pd.DataFrame:
    """Descarga los contratos firmados en los últimos `dias_atras` días."""
    hoy = hoy or date.today()
    desde = hoy - timedelta(days=dias_atras)
    filtro = construir_filtro(departamento, desde, hoy)

    paginas, offset = [], 0
    while True:
        params = {
            "$select": ",".join(COLUMNAS),
            "$where": filtro,
            "$order": ":id",
            "$limit": TAMANO_PAGINA,
            "$offset": offset,
        }
        filas = _pedir_pagina(params)
        if not filas:
            break
        paginas.append(pd.DataFrame(filas))
        print(f"  Página: {len(filas)} filas (offset {offset})")
        if len(filas) < TAMANO_PAGINA:
            break
        offset += TAMANO_PAGINA

    if not paginas:
        return pd.DataFrame(columns=COLUMNAS)

    df = pd.concat(paginas, ignore_index=True)
    df = df.reindex(columns=COLUMNAS)
    return df.drop_duplicates(subset="id_contrato", keep="last")
