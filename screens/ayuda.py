"""Pantalla de ayuda: objetivo, controles y significado de los indicadores."""

import pygame

from config import INDICADORES_CIUDAD_INICIALES, ROLES_JUGABLES
from screens.ciudad import INDICADOR_LABELS


DESCRIPCION_INDICADORES = {
    "informacion_verificada": "qué tanto de lo que circula está comprobado",
    "confianza_ciudadana": "cuánto confían los ciudadanos entre sí",
    "convivencia": "qué tan sano es el ambiente de la ciudad",
    "bienestar_digital": "qué tan sana es la relación con la red social",
    "desinformacion": "cuánta mentira está circulando (mientras más baja, mejor)",
    "conflictos": "cuántas peleas está generando la campaña (mejor baja)",
}


def render_ayuda(screen, font=None, small_font=None):
    if font is None:
        font = pygame.font.SysFont("arial", 28)
    if small_font is None:
        small_font = font

    screen.fill((30, 30, 55))

    lineas = [
        "Objetivo: que Ciudad Nova llegue a las elecciones con la mejor",
        "información y la menor desinformación posible.",
        "",
        "Cómo se juega: en la ciudad presionas [E] para ver una publicación",
        "pendiente y eliges qué hacer con ella con las teclas [1] a [4]",
        "(verificar, compartir, ignorar o reportar). Cada decisión mueve los",
        "indicadores de la ciudad y te da puntaje.",
        "",
        "Cómo ganar: terminar con la confianza ciudadana y la información",
        "verificada altas, y la desinformación y los conflictos bajos.",
        "",
        f"Roles: {', '.join(ROLES_JUGABLES)}",
    ]

    y = 36
    for linea in lineas:
        if linea:
            screen.blit(small_font.render(linea, True, (255, 255, 255)), (40, y))
        y += 26

    y += 10
    screen.blit(small_font.render("Indicadores:", True, (240, 220, 140)), (40, y))
    y += 30

    for clave in INDICADORES_CIUDAD_INICIALES:
        nombre = INDICADOR_LABELS.get(clave, clave)
        descripcion = DESCRIPCION_INDICADORES.get(clave, "")
        texto = f"- {nombre}: {descripcion}" if descripcion else f"- {nombre}"
        screen.blit(small_font.render(texto, True, (210, 210, 210)), (60, y))
        y += 24

    aviso = small_font.render("[ENTER] Volver", True, (194, 216, 248))
    screen.blit(aviso, aviso.get_rect(center=(screen.get_width() // 2, screen.get_height() - 26)))
