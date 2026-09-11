import pygame


class Fondo:
    def __init__(self, ruta_imagen, x, y):
        self.ruta_imagen = ruta_imagen
        self.imagen = pygame.image.load(ruta_imagen).convert()
        self.x = x
        self.y = y

    def dibujar(self, pantalla):
        pantalla.blit(self.imagen, (self.x, self.y))
