"""
Configuración global de colores y constantes del juego.
"""

DEFAULT_FPS = 60

# Paleta de colores principal
BG_DARK = (20, 18, 42)
BG_MID = (31, 27, 64)
GRID = (44, 39, 83)
CARD = (224, 233, 213)
CARD_HOVER = (247, 232, 142)
CARD_BORDER = (50, 42, 94)
TEXT_MAIN = (25, 26, 39)
TEXT_SOFT = (58, 61, 90)
PIXEL_CYAN = (91, 227, 255)
PIXEL_PINK = (255, 99, 179)

# Colores de paleta para personalización de personaje
PALETTE_COLORS = [
    (240, 240, 240), (20, 20, 20), (216, 163, 117), (134, 85, 56),
    (87, 52, 35), (52, 103, 178), (38, 160, 87), (196, 55, 55),
    (226, 185, 74), (145, 97, 207), (255, 132, 184), (80, 201, 232),
]

# Partes de personaje y sus estilos
CUSTOM_PARTS = [
    "Cabello",
    "Piel",
    "Ojos",
    "Sueter",
    "Camisa",
    "Pantalones",
    "Zapatos",
]

PART_STYLES = {
    "Cabello": ["Corto", "Largo", "Rizado", "Afro", "Coleta"],
    "Piel": ["Base"],
    "Ojos": ["Normal", "Grandes"],
    "Sueter": ["Sin sueter", "Hoodie", "Chaqueta"],
    "Camisa": ["Camiseta", "Flanelilla", "Polo"],
    "Pantalones": ["Jeans", "Jogger", "Short"],
    "Zapatos": ["Tenis", "Botas", "Casuales"],
}

# Colores por defecto de partes del personaje
DEFAULT_CHARACTER_COLORS = {
    "Cabello": (92, 58, 38),
    "Piel": (216, 163, 117),
    "Ojos": (52, 103, 178),
    "Sueter": (145, 97, 207),
    "Camisa": (240, 240, 240),
    "Pantalones": (52, 103, 178),
    "Zapatos": (20, 20, 20),
}

# Configuraciones por defecto
DEFAULT_SETTINGS = {
    "Pantalla completa": False,
    "Musica": 70,
    "Efectos de sonido": 70,
    "Limite FPS": DEFAULT_FPS,
    "Mostrar FPS": False,
    "Mostrar hitboxes": False,
    "Animaciones": True,
    "Ayuda en pantalla": True,
}

# Controles por defecto (teclas pygame)
DEFAULT_CONTROLS = {
    "mover_arriba": "w",
    "mover_abajo": "s",
    "mover_izquierda": "a",
    "mover_derecha": "d",
    "interactuar": "e",
    "guardar": "f5",
    "continuar": "return",
    "opcion_1": "1",
    "opcion_2": "2",
    "opcion_3": "3",
    "opcion_4": "4",
    "opcion_5": "5",
}

# Versión del schema de guardado; incrementar si cambia la estructura del JSON.
SAVE_VERSION = 1

# Duración de transiciones de pantalla en milisegundos.
TRANSITION_DURATION_MS = 300

# ── Específico de Alcalde Digital (nuevo, no viene de EmpatiaQuest) ─────────
ROLES_JUGABLES = ["Ciudadano", "Periodista", "Influencer", "Candidato"]

INDICADORES_CIUDAD_INICIALES = {
    "informacion_verificada": 50,
    "confianza_ciudadana": 50,
    "convivencia": 50,
    "bienestar_digital": 50,
    "desinformacion": 20,
    "conflictos": 10,
}
