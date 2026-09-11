import pygame

from config import INDICADORES_CIUDAD_INICIALES, ROLES_JUGABLES


def render_ayuda(screen, font=None):
    if font is None:
        font = pygame.font.SysFont("arial", 28)
    screen.fill((30, 30, 55))
    lines = [
        "Objetivo del juego: combatir la desinformación.",
        f"Roles disponibles: {', '.join(ROLES_JUGABLES)}",
        "Controles: WASD para moverse, E para interactuar.",
        "Cómo ganar: mejorar la confianza y la información verificada.",
        "Indicadores:",
    ]
    for idx, line in enumerate(lines):
        label = font.render(line, True, (255, 255, 255))
        screen.blit(label, (40, 40 + idx * 35))
    for idx, (k, v) in enumerate(INDICADORES_CIUDAD_INICIALES.items()):
        label = font.render(f"- {k}: {v}", True, (200, 200, 200))
        screen.blit(label, (60, 260 + idx * 28))
