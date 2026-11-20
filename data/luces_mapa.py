"""Luces y detalles de cada mapa (juego/luces.py). Editable sin tocar código.

Coordenadas en píxeles de la IMAGEN ORIGINAL del mapa (la de
Imagenes/Fondos/, sin agrandar): el juego las multiplica por lo que se agranda
el mapa. Los radios ya van en píxeles del juego.

- "luces": manchas de luz de color que respiran. `intensidad` 0-1, `pulso` =
  cuánto sube y baja (0 = fija), `vel` = qué tan rápido, `falla` = probabilidad
  de que parpadee (como un tubo que falla), `electrica` = se apaga en un
  apagón (las que no, siguen tenues: el reactor, la incubadora).
- "lamparas": color exacto del centro de las lámparas de los pasillos; cada
  una que se encuentre en la imagen alumbra un poco (y algunas fallan).
- "ventanas": rectángulos de vidrio con el espacio detrás: estrellas que pasan.
- "pantallas": rectángulos del dibujo cuyos píxeles brillantes (pantallas,
  tubos, barras del reactor) titilan o respiran (`modo`: "titila" o "respira").
"""

LUCES_MAPA = {
    "MapaFinal": {
        "luces": [
            # Motores: el reactor (rejilla naranja y blanca) y su reflejo en el piso.
            {"x": 1782, "y": 392, "radio": 290, "color": (255, 130, 50), "intensidad": 0.55,
             "pulso": 0.22, "vel": 0.9, "electrica": False},
            {"x": 1782, "y": 455, "radio": 200, "color": (255, 170, 90), "intensidad": 0.35,
             "pulso": 0.15, "vel": 0.9, "electrica": False},
            # Gestación: la incubadora rosada.
            {"x": 994, "y": 1785, "radio": 230, "color": (240, 80, 200), "intensidad": 0.5,
             "pulso": 0.3, "vel": 0.5, "electrica": False},
            # Bahía: la luz amarilla bajo el portón y la ventanita de arriba.
            {"x": 1205, "y": 165, "radio": 220, "color": (255, 200, 90), "intensidad": 0.36,
             "pulso": 0.1, "vel": 0.4},
            {"x": 1204, "y": 82, "radio": 130, "color": (120, 150, 255), "intensidad": 0.22, "pulso": 0.15,
             "vel": 0.3, "electrica": False},
            # Comando: el ventanal (luz fría del espacio).
            {"x": 1823, "y": 1050, "radio": 300, "color": (100, 140, 255), "intensidad": 0.32,
             "pulso": 0.12, "vel": 0.25, "electrica": False},
            # General: las cuatro pantallas de arriba.
            {"x": 723, "y": 913, "radio": 120, "color": (80, 230, 230), "intensidad": 0.26, "pulso": 0.2, "vel": 1.3},
            {"x": 793, "y": 913, "radio": 120, "color": (80, 230, 230), "intensidad": 0.26, "pulso": 0.2, "vel": 1.1},
            {"x": 863, "y": 913, "radio": 120, "color": (80, 230, 230), "intensidad": 0.26, "pulso": 0.2, "vel": 1.25},
            {"x": 933, "y": 913, "radio": 120, "color": (80, 230, 230), "intensidad": 0.26, "pulso": 0.2,
             "vel": 1.05, "falla": 0.25},
            # Control: los paneles morados y azules de la pared.
            {"x": 1466, "y": 1004, "radio": 95, "color": (170, 90, 240), "intensidad": 0.3, "pulso": 0.25, "vel": 1.4},
            {"x": 1466, "y": 1039, "radio": 95, "color": (70, 130, 240), "intensidad": 0.3, "pulso": 0.25, "vel": 1.0},
            {"x": 1466, "y": 1077, "radio": 95, "color": (170, 90, 240), "intensidad": 0.3, "pulso": 0.25, "vel": 1.2},
            {"x": 1466, "y": 1135, "radio": 95, "color": (70, 130, 240), "intensidad": 0.3, "pulso": 0.25, "vel": 0.9},
            {"x": 1466, "y": 1173, "radio": 95, "color": (170, 90, 240), "intensidad": 0.3, "pulso": 0.25, "vel": 1.3},
            # Laboratorio: los tres tubos.
            {"x": 254, "y": 505, "radio": 150, "color": (150, 225, 255), "intensidad": 0.24, "pulso": 0.2, "vel": 0.6},
            {"x": 380, "y": 505, "radio": 150, "color": (150, 225, 255), "intensidad": 0.24, "pulso": 0.2,
             "vel": 0.7, "falla": 0.2},
            {"x": 504, "y": 505, "radio": 150, "color": (150, 225, 255), "intensidad": 0.24, "pulso": 0.2, "vel": 0.65},
            # Biosfera: la luz que entra por los ventanales del jardín.
            {"x": 1760, "y": 1530, "radio": 280, "color": (210, 255, 170), "intensidad": 0.26, "pulso": 0.08,
             "vel": 0.2, "electrica": False},
        ],
        "lamparas": {"color": (181, 251, 243), "luz": (90, 235, 220), "radio": 75, "intensidad": 0.2,
                     "falla": 0.08},
        "ventanas": [
            (1676, 985, 80, 44), (1769, 985, 102, 44), (1884, 985, 87, 44),     # Comando
            (1152, 74, 105, 10),                                                  # Bahía
        ],
        "pantallas": [
            {"rect": (700, 890, 260, 50), "modo": "titila"},       # General: pantallas
            {"rect": (1448, 990, 40, 200), "modo": "titila"},      # Control: paneles
            {"rect": (1710, 353, 143, 68), "modo": "respira"},     # Motores: reactor
            {"rect": (960, 1730, 70, 110), "modo": "respira"},     # Gestación: incubadora
        ],
    },
}
