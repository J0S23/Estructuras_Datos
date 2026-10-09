"""Terminales, paneles dañados y piezas sueltas del mapa.

Son los puntos donde se usan las habilidades de estación (ver `uso` en
data/habilidades.py). Coordenadas de 0 a 1 sobre el mapa, como todo lo demás.
Están en el Colegio mientras llega el mapa de la nave; pruebas/prueba_roles.py
revisa que no choquen con paredes, que se alcancen caminando y que no se monten
sobre zonas ni escondites.

- terminales: las usa el Tecnomante.
- paneles: los repara el Forjador con una pieza.
- piezas: solo el Forjador las ve y las recoge (pasando por encima).
"""

TERMINALES = [
    {"clave": "terminal_oeste", "nombre": "Terminal", "rx": 0.30, "ry": 0.42},
    {"clave": "terminal_este", "nombre": "Terminal", "rx": 0.70, "ry": 0.42},
]

PANELES = [
    {"clave": "panel_suroeste", "nombre": "Panel dañado", "rx": 0.40, "ry": 0.58},
    {"clave": "panel_sureste", "nombre": "Panel dañado", "rx": 0.60, "ry": 0.58},
    {"clave": "panel_norte", "nombre": "Panel dañado", "rx": 0.50, "ry": 0.26},
]

PIEZAS = [
    (0.25, 0.27), (0.75, 0.27), (0.45, 0.36), (0.94, 0.58),
    (0.50, 0.42), (0.33, 0.48), (0.67, 0.48),
]

TAMANO_ESTACION = (60, 40)
TAMANO_PIEZA = (34, 34)
