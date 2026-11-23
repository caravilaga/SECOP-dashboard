"""Pipeline semanal: descarga, limpia, agrega y actualiza las tablas del repo.

Uso desde la terminal (así lo corre GitHub Actions):
    python -m src.pipeline
"""
from datetime import date
from pathlib import Path

import pandas as pd

from src.agregar import (ARCHIVO_CUBO, ARCHIVO_ENTIDADES, actualizar_tabla,
                         agregar_cubo, agregar_entidades, inicio_ventana)
from src.extraer import descargar_contratos
from src.transformar import limpiar

MESES_ATRAS = 1          # la ventana empieza el día 1 del mes anterior
UMBRAL_CAIDA = 0.5       # si un mes queda con menos de la mitad de contratos, algo anda mal


class DatosSospechosos(Exception):
    """Los datos nuevos parecen incompletos: mejor no guardarlos."""


def verificar_caida(nuevo: pd.DataFrame, archivo: Path, umbral: float = UMBRAL_CAIDA) -> None:
    """Compara, mes a mes, el total de contratos nuevo contra el guardado.

    Si algún mes cae por debajo de `umbral` × total guardado, lanza DatosSospechosos.
    Protege contra respuestas incompletas de la API que no generan error.
    """
    if not archivo.exists():
        return
    guardado = pd.read_parquet(archivo).groupby("mes_firma")["contratos"].sum()
    actual = nuevo.groupby("mes_firma")["contratos"].sum()
    for mes, total_nuevo in actual.items():
        total_guardado = guardado.get(mes)
        if total_guardado and total_nuevo < umbral * total_guardado:
            raise DatosSospechosos(
                f"{mes}: {total_nuevo} contratos nuevos frente a {total_guardado} guardados. "
                "No se guardó nada.")


def ejecutar(hoy: date | None = None, departamento: str | None = None,
             archivo_cubo: Path = ARCHIVO_CUBO,
             archivo_entidades: Path = ARCHIVO_ENTIDADES) -> dict:
    hoy = hoy or date.today()
    desde = inicio_ventana(hoy, MESES_ATRAS)
    print(f"Ventana: {desde} → {hoy} ({departamento or 'todo el país'})")

    crudos = descargar_contratos(departamento, dias_atras=(hoy - desde).days, hoy=hoy)
    if crudos.empty:
        raise DatosSospechosos("La API no devolvió contratos para la ventana. No se guardó nada.")

    limpio = limpiar(crudos, hoy=hoy)
    cubo_nuevo = agregar_cubo(limpio)
    entidades_nuevo = agregar_entidades(limpio)

    verificar_caida(cubo_nuevo, archivo_cubo)   # antes de escribir cualquier archivo

    cubo = actualizar_tabla(cubo_nuevo, archivo_cubo)
    entidades = actualizar_tabla(entidades_nuevo, archivo_entidades)

    resumen = {
        "contratos_descargados": len(crudos),
        "contratos_validos": len(limpio),
        "meses_actualizados": sorted(cubo_nuevo["mes_firma"].unique()),
        "filas_cubo": len(cubo),
        "filas_entidades": len(entidades),
    }
    for clave, valor in resumen.items():
        print(f"  {clave}: {valor}")
    return resumen


if __name__ == "__main__":
    ejecutar()
