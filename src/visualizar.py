"""Genera el tablero HTML a partir de la capa gold."""
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

RAIZ = Path(__file__).resolve().parents[1]
DIR_GOLD = RAIZ / "data" / "gold"
DIR_SITIO = RAIZ / "site"

# Paleta: un solo tono (azul) porque cada gráfica muestra una sola serie
AZUL = "#2a78d6"
AZUL_CLARO = "#86b6ef"      # mes en curso: datos todavía incompletos
TINTA = "#0b0b0b"
TINTA_SECUNDARIA = "#52514e"
TINTA_TENUE = "#898781"
GRILLA = "#e1e0d9"
EJE = "#c3c2b7"
FONDO = "#fcfcfb"
FUENTE = 'system-ui, -apple-system, "Segoe UI", sans-serif'

MIL_MILLONES = 1e9
MESES = ["ene", "feb", "mar", "abr", "may", "jun",
         "jul", "ago", "sep", "oct", "nov", "dic"]


# ---------- Formato de números en español (1.234,5) ----------

def numero_es(valor: float, decimales: int = 0) -> str:
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def pesos_es(valor: float) -> str:
    if valor >= 1e12:
        return f"${numero_es(valor / 1e12, 2)} billones"
    return f"${numero_es(valor / MIL_MILLONES, 1)} mil millones"


def etiqueta_mes(mes: str) -> str:
    """'2026-11' -> 'nov<br>26' (dos líneas para que quepan 12 meses)."""
    anio, num = mes.split("-")
    return f"{MESES[int(num) - 1]}<br>{anio[2:]}"


# ---------- Estilo común ----------

def estilo_base(fig: go.Figure, titulo: str, alto: int = 360) -> go.Figure:
    fig.update_layout(
        title=dict(text=titulo, x=0, xanchor="left", font=dict(size=16, color=TINTA)),
        font=dict(family=FUENTE, size=13, color=TINTA_SECUNDARIA),
        paper_bgcolor=FONDO, plot_bgcolor=FONDO,
        height=alto, margin=dict(l=10, r=20, t=50, b=10),
        separators=",.",                     # decimal con coma, miles con punto
        showlegend=False,                    # una sola serie: el título la nombra
        hoverlabel=dict(bgcolor="white", font=dict(family=FUENTE, color=TINTA)),
        bargap=0.35,
    )
    fig.update_xaxes(tickfont=dict(color=TINTA_TENUE), linecolor=EJE, tickangle=0)
    fig.update_yaxes(tickfont=dict(color=TINTA_TENUE), linecolor=EJE)
    return fig


# ---------- Gráficas ----------

def meses_completos(resumen: pd.DataFrame) -> pd.DataFrame:
    """Quita el primer mes: la carga histórica empezó a mitad de mes y siempre estará incompleto."""
    datos = resumen.sort_values("mes_firma").iloc[1:].copy()
    datos["etiqueta"] = datos["mes_firma"].map(etiqueta_mes)
    return datos


def grafica_barras_mensual(resumen: pd.DataFrame, columna: str, titulo: str,
                           hover: str, escala: float = 1) -> go.Figure:
    datos = meses_completos(resumen)
    mes_actual = datetime.now(timezone.utc).strftime("%Y-%m")
    colores = [AZUL_CLARO if m == mes_actual else AZUL for m in datos["mes_firma"]]

    fig = go.Figure(go.Bar(
        x=datos["etiqueta"], y=datos[columna] / escala,
        marker=dict(color=colores),
        hovertemplate=hover + "<extra></extra>",
    ))
    estilo_base(fig, titulo)
    fig.update_xaxes(type="category", showgrid=False)
    fig.update_yaxes(gridcolor=GRILLA, zeroline=False)
    return fig


def grafica_porcentaje_mensual(resumen: pd.DataFrame, columna: str, titulo: str,
                               texto_hover: str) -> go.Figure:
    """Línea mensual para una proporción entre 0 y 1 (se muestra como %)."""
    datos = meses_completos(resumen)
    fig = go.Figure(go.Scatter(
        x=datos["etiqueta"], y=datos[columna],
        mode="lines+markers",
        line=dict(color=AZUL, width=2),
        marker=dict(size=8, color=AZUL, line=dict(color=FONDO, width=2)),
        hovertemplate="%{x}<br>%{y:.1%} " + texto_hover + "<extra></extra>",
    ))
    estilo_base(fig, titulo)
    fig.update_xaxes(type="category", showgrid=False)
    fig.update_yaxes(gridcolor=GRILLA, zeroline=False, tickformat=".0%", range=[0, 1])
    return fig


def grafica_ranking(tabla: pd.DataFrame, columna: str, titulo: str) -> go.Figure:
    datos = tabla.sort_values("valor_total")          # Plotly dibuja de abajo hacia arriba
    nombres = datos[columna].where(datos[columna].str.len() <= 45,
                                   datos[columna].str.slice(0, 44) + "…")
    fig = go.Figure(go.Bar(
        x=datos["valor_total"] / MIL_MILLONES, y=nombres, orientation="h",
        marker=dict(color=AZUL),
        customdata=datos[[columna, "contratos"]],
        hovertemplate=("<b>%{customdata[0]}</b><br>"
                       "Valor: $%{x:,.1f} mil millones<br>"
                       "Contratos: %{customdata[1]:,}<extra></extra>"),
    ))
    estilo_base(fig, titulo, alto=420)
    fig.update_xaxes(gridcolor=GRILLA, zeroline=False, title_text="Miles de millones de pesos",
                     title_font=dict(size=12, color=TINTA_TENUE))
    fig.update_yaxes(showgrid=False)
    return fig


# ---------- Página ----------

def tarjeta(etiqueta: str, valor: str) -> str:
    return f'<div class="kpi"><span class="kpi-etiqueta">{etiqueta}</span><span class="kpi-valor">{valor}</span></div>'


def construir_pagina(directorio_gold: Path = DIR_GOLD, salida: Path = DIR_SITIO) -> Path:
    kpis = json.loads((directorio_gold / "kpis.json").read_text(encoding="utf-8"))
    resumen = pd.read_csv(directorio_gold / "resumen_mensual.csv")
    entidades = pd.read_csv(directorio_gold / "top_entidades.csv")
    modalidades = pd.read_csv(directorio_gold / "por_modalidad.csv")

    figuras = [
        grafica_barras_mensual(resumen, "contratos", "Contratos firmados por mes",
                               "%{x}<br>%{y:,} contratos").update_yaxes(tickformat=",d"),
        grafica_barras_mensual(resumen, "valor_total", "Valor contratado por mes (miles de millones de pesos)",
                               "%{x}<br>$%{y:,.1f} mil millones", escala=MIL_MILLONES),
        grafica_porcentaje_mensual(resumen, "pct_directa",
                                   "Contratos por contratación directa (% del total del mes)",
                                   "de los contratos"),
        grafica_porcentaje_mensual(resumen, "p_natural",
                                   "Contratos con personas naturales (% del total del mes)",
                                   "de los contratos fueron con personas naturales"),
        grafica_ranking(entidades, "nombre_entidad", "Las 10 entidades con mayor valor contratado"),
        grafica_ranking(modalidades, "modalidad_de_contratacion", "Valor contratado por modalidad"),
    ]
    config = {"displayModeBar": False, "responsive": True}
    bloques = [
        fig.to_html(full_html=False, include_plotlyjs="cdn" if i == 0 else False,
                    config=config, default_width="100%")
        for i, fig in enumerate(figuras)
    ]

    tarjetas = "".join([
        tarjeta("Contratos", numero_es(kpis["contratos"])),
        tarjeta("Valor total", pesos_es(kpis["valor_total"])),
        tarjeta("Contratación directa", f'{numero_es(kpis["pct_contratacion_directa"] * 100, 1)}%'),
        tarjeta("Proveedores pyme", f'{numero_es(kpis["pct_pyme"] * 100, 1)}%'),
    ])

    tabla = meses_completos(resumen)[["etiqueta", "contratos", "valor_total",
                                      "pct_directa", "p_natural"]].copy()
    tabla["etiqueta"] = tabla["etiqueta"].str.replace("<br>", " ")
    tabla["valor_total"] = tabla["valor_total"].map(pesos_es)
    tabla["contratos"] = tabla["contratos"].map(numero_es)
    for col in ["pct_directa", "p_natural"]:
        tabla[col] = (tabla[col] * 100).map(lambda v: f"{numero_es(v, 1)}%")
    tabla.columns = ["Mes", "Contratos", "Valor total", "% contratación directa",
                     "% personas naturales"]
    tabla_html = tabla.to_html(index=False, border=0, classes="tabla")

    actualizado = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Contratación pública en Valle del Cauca · SECOP II</title>
<style>
  body {{ margin: 0; background: #f9f9f7; color: {TINTA}; font-family: {FUENTE}; }}
  main {{ max-width: 1100px; margin: 0 auto; padding: 32px 20px 48px; }}
  h1 {{ font-size: 28px; margin: 0 0 6px; }}
  .sub {{ color: {TINTA_SECUNDARIA}; margin: 0 0 24px; }}
  .kpis {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 12px; margin-bottom: 24px; }}
  .kpi, .panel {{ background: {FONDO}; border: 1px solid rgba(11,11,11,0.10); border-radius: 12px; }}
  .kpi {{ padding: 16px 18px; display: flex; flex-direction: column; gap: 6px; }}
  .kpi-etiqueta {{ color: {TINTA_SECUNDARIA}; font-size: 14px; }}
  .kpi-valor {{ font-size: 28px; font-weight: 600; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(460px, 1fr)); gap: 16px; }}
  .panel {{ padding: 12px; min-width: 0; overflow: hidden; }}
  .nota {{ color: {TINTA_SECUNDARIA}; font-size: 14px; line-height: 1.5; margin-top: 24px; }}
  details {{ margin-top: 16px; }}
  .tabla {{ border-collapse: collapse; width: 100%; font-size: 14px; margin-top: 8px; }}
  .tabla th, .tabla td {{ text-align: right; padding: 6px 10px; border-bottom: 1px solid {GRILLA}; }}
  .tabla th:first-child, .tabla td:first-child {{ text-align: left; }}
  @media (max-width: 520px) {{ .grid {{ grid-template-columns: 1fr; }} }}
</style>
</head>
<body>
<main>
  <h1>Contratación pública en Valle del Cauca</h1>
  <p class="sub">Contratos firmados en SECOP II entre {kpis["fecha_min"]} y {kpis["fecha_max"]} · Actualizado: {actualizado}</p>

  <section class="kpis">{tarjetas}</section>

  <section class="grid">
    {"".join(f'<div class="panel">{b}</div>' for b in bloques)}
  </section>

  <details>
    <summary>Ver datos mensuales en tabla</summary>
    {tabla_html}
  </details>

  <p class="nota">
    Fuente: <a href="https://www.datos.gov.co/Gastos-Gubernamentales/SECOP-II-Contratos-Electr-nicos/jbjy-vk9h">SECOP II – Contratos Electrónicos</a>, datos.gov.co.
    La barra más clara corresponde al mes en curso, que todavía está incompleto. Los contratos se publican con días o semanas de retraso,
    así que las cifras de las últimas semanas pueden aumentar en próximas actualizaciones.
  </p>
</main>
<script>
  // Ajusta cada gráfica al ancho real de su panel una vez cargada la página
  window.addEventListener("load", () =>
    document.querySelectorAll(".js-plotly-plot").forEach(el => Plotly.Plots.resize(el)));
</script>
</body>
</html>"""

    salida.mkdir(parents=True, exist_ok=True)
    archivo = salida / "index.html"
    archivo.write_text(html, encoding="utf-8")
    return archivo

if __name__ == "__main__":
    print("Página generada en:", construir_pagina())