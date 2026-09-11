import pygame


def render_menu(screen, font=None):
    if font is None:
        font = pygame.font.SysFont("arial", 30)
    screen.fill((35, 40, 60))
    label = font.render("MENU", True, (255, 255, 255))
    screen.blit(label, (50, 50))
