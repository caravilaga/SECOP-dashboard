from src.geo import cargar_geojson, codigo_dane, tabla_codigos

# Nombres de departamento tal como aparecen en SECOP II
DEPARTAMENTOS_SECOP = [
    "Amazonas", "Antioquia", "Arauca", "Atlántico", "Bolívar", "Boyacá", "Caldas", "Caquetá",
    "Casanare", "Cauca", "Cesar", "Chocó", "Córdoba", "Cundinamarca", "Distrito Capital de Bogotá",
    "Guainía", "Guaviare", "Huila", "La Guajira", "Magdalena", "Meta", "Nariño",
    "Norte De Santander", "Putumayo", "Quindío", "Risaralda",
    "San Andrés, Providencia y Santa Catalina", "Santander", "Sucre", "Tolima",
    "Valle del Cauca", "Vaupés", "Vichada",
]


def test_todos_los_departamentos_tienen_poligono():
    codigos = tabla_codigos(cargar_geojson())
    sin_poligono = [d for d in DEPARTAMENTOS_SECOP if codigo_dane(d, codigos) is None]
    assert sin_poligono == []


def test_cada_departamento_tiene_un_codigo_distinto():
    codigos = tabla_codigos(cargar_geojson())
    asignados = [codigo_dane(d, codigos) for d in DEPARTAMENTOS_SECOP]
    assert len(set(asignados)) == len(DEPARTAMENTOS_SECOP) == 33
