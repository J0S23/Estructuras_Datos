from .Personaje import cortar_spritesheet_auto


class Animacion:
    def __init__(self, ruta, cantidad_frames, fps_animacion=8, x=0, y=0):
        self.frames = cortar_spritesheet_auto(ruta, cantidad_frames)
        self.frame_actual = 0
        self.contador = 0
        self.fps_animacion = fps_animacion
        self.x = x
        self.y = y
        self.velocidad = 2
        self.direccion_x = 1
        self.limite_izquierdo = 0
        self.limite_derecho = 0

    def actualizar(self):
        self.contador += 1
        if self.contador >= self.fps_animacion:
            self.contador = 0
            self.frame_actual = (self.frame_actual + 1) % len(self.frames)

    def mover_lateral(self, x_min, x_max):
        self.limite_izquierdo = x_min
        self.limite_derecho = x_max

        if self.x <= self.limite_izquierdo:
            self.direccion_x = 1
        elif self.x >= self.limite_derecho:
            self.direccion_x = -1

        self.x += self.velocidad * self.direccion_x

    def dibujar(self, pantalla, offset=(0, 0)):
        pantalla.blit(self.frames[self.frame_actual], (self.x - offset[0], self.y - offset[1]))
