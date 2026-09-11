import pygame


def render_ciudad(screen, font=None):
    if font is None:
        font = pygame.font.SysFont("arial", 30)
    screen.fill((40, 90, 80))
    label = font.render("CIUDAD", True, (255, 255, 255))
    screen.blit(label, (50, 50))
