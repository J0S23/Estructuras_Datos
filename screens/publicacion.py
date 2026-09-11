import pygame


def render_publicacion(screen, font=None):
    if font is None:
        font = pygame.font.SysFont("arial", 30)
    screen.fill((90, 60, 80))
    label = font.render("PUBLICACION", True, (255, 255, 255))
    screen.blit(label, (50, 50))
