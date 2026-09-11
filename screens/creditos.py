import pygame


def render_creditos(screen, font=None, scroll_y=0, paused=False):
    if font is None:
        font = pygame.font.SysFont("arial", 28)
    screen.fill((15, 15, 25))
    lines = [
        "ALCALDE DIGITAL",
        "Integrante 1",
        "Integrante 2",
        "Integrante 3",
        "Python 3.11",
        "Pygame",
        "Gracias por jugar.",
    ]
    for idx, line in enumerate(lines):
        label = font.render(line, True, (255, 255, 255))
        screen.blit(label, (100, 80 + scroll_y + idx * 45))
    return scroll_y + (0 if paused else 1)
