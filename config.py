"""Configuración global: colores, constantes y datos de la ciudad.

Este archivo venía de EmpatiaQuest y traía un montón de constantes de aquel
juego (paletas de personalización de personaje, partes del cuerpo, controles
por defecto, versión de guardado). Nada de eso se usa en Alcalde Digital, así
que se sacó. Lo que queda es lo que alguien importa de verdad.
"""

DEFAULT_FPS = 60

# Colores de los botones del menú (ui_components.Button).
CARD = (224, 233, 213)
CARD_HOVER = (247, 232, 142)
CARD_BORDER = (50, 42, 94)
TEXT_MAIN = (25, 26, 39)

# Duración de los fundidos entre pantallas, en milisegundos.
TRANSITION_DURATION_MS = 300


# -- Ciudad Nova ------------------------------------------------------------

ROLES_JUGABLES = ["Ciudadano", "Periodista", "Influencer", "Candidato"]

INDICADORES_CIUDAD_INICIALES = {
    "informacion_verificada": 50,
    "confianza_ciudadana": 50,
    "convivencia": 50,
    "bienestar_digital": 50,
    "desinformacion": 20,
    "conflictos": 10,
}

# Nombre bonito de cada indicador, para la interfaz.
INDICADOR_LABELS = {
    "informacion_verificada": "Información verificada",
    "confianza_ciudadana": "Confianza ciudadana",
    "convivencia": "Convivencia",
    "bienestar_digital": "Bienestar digital",
    "desinformacion": "Desinformación",
    "conflictos": "Conflictos",
}

# Indicadores donde subir es MALO: la interfaz los pinta al revés.
INDICADORES_INVERSOS = {"desinformacion", "conflictos"}
