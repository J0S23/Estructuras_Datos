"""Las huellas miran hacia donde se camina (juego/efectos.py).

    python pruebas/prueba_huellas.py

Diego: "creo que las huellas están al revés". Cada huella es un talón chico
atrás y la parte de adelante, más ancha, hacia donde camina (antes era un
óvalo con una bolita adelante, que se leía como un talón). Se revisa caminando en las
cuatro direcciones, que dejan un pie a cada lado y que en sigilo no dejan.
"""

import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

import pygame

pygame.init()

from juego import efectos

efectos.ACTIVOS = True


class Caminante:
    def __init__(self):
        self.hitbox = pygame.Rect(1000, 1000, 48, 19)
        self.sigilo = False


def caminar(dx, dy, pasos=8, sigilo=False):
    efectos.limpiar()
    j = Caminante()
    j.sigilo = sigilo
    efectos._huellas_de([j], 16)
    for _ in range(pasos):
        j.hitbox.x += dx
        j.hitbox.y += dy
        efectos._huellas_de([j], 16)
    return list(efectos._huellas)


def anchos(img, dx, dy):
    """(ancho de la parte de adelante, ancho de la de atrás), medidos de
    costado (perpendicular a donde camina)."""
    frente, atras = set(), set()
    for x in range(img.get_width()):
        for y in range(img.get_height()):
            if img.get_at((x, y))[3] < 40:
                continue
            avance = (x - 7.5) * (1 if dx > 0 else -1 if dx < 0 else 0) + \
                     (y - 7.5) * (1 if dy > 0 else -1 if dy < 0 else 0)
            costado = y if dx else x
            (frente if avance > 0 else atras).add(costado)
    return len(frente), len(atras)


for nombre, (dx, dy) in {"derecha": (31, 0), "izquierda": (-31, 0),
                         "abajo": (0, 31), "arriba": (0, -31)}.items():
    huellas = caminar(dx, dy)
    assert len(huellas) >= 6, (nombre, len(huellas))
    frente, atras = anchos(huellas[-1][4], dx, dy)
    # La parte de adelante (planta y dedos) es más ancha que el talón.
    assert frente > atras, f"caminando a la {nombre} la huella mira al revés (adelante {frente}, atrás {atras})"
    # Un pie a cada lado.
    if dx:
        assert len({round(h[1]) for h in huellas}) == 2, nombre
    else:
        assert len({round(h[0]) for h in huellas}) == 2, nombre
assert not caminar(31, 0, sigilo=True), "en sigilo dejó huellas"

# Una captura grande para verlas.
efectos.limpiar()
lienzo = pygame.Surface((460, 220))
lienzo.fill((150, 150, 170))
for fila, (dx, dy) in enumerate(((-31, 0), (31, 0))):
    huellas = caminar(dx, dy, 10)
    efectos._huellas[:] = huellas
    centro_x = sum(h[0] for h in huellas) / len(huellas)
    efectos.dibujar_piso(lienzo, (centro_x - 230, 1000 - 60 - fila * 100), pygame.Rect(0, 0, 4000, 4000))
salida = os.path.join(os.environ.get("NEXUS_CAPTURAS") or os.path.join(RAIZ, "pruebas", "capturas"),
                      "huellas.png")
os.makedirs(os.path.dirname(salida), exist_ok=True)
pygame.image.save(pygame.transform.scale(lienzo, (920, 440)), salida)
print("huellas: miran hacia donde se camina en las 4 direcciones, un pie a cada lado, sin huellas en sigilo: OK")
print("OK prueba_huellas")
