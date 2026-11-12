"""Muestra en vivo qué teclas ve el juego y si cada jugador está en sigilo.

    python pruebas/probar_teclas.py

Para revisar choques de teclas en un computador de verdad (no se puede desde
las pruebas: los atajos de Windows, los remapeos como el de la tecla Copilot
y el "ghosting" del teclado pasan antes de que el juego vea nada):

- "presionadas" son las teclas que pygame dice que están abajo AHORA (lo que
  usa el juego para moverse y el sigilo);
- abajo, los últimos eventos KEYDOWN/KEYUP con su nombre, su scancode y los
  modificadores. Un KEYUP de una tecla que sigues apretando es un remapeo o
  un atajo del sistema que la está "soltando".
- Sigilo J1 / Sigilo J2: lo mismo que calcula `Jugador.actualizar`.

Prueba: mantén el sigilo del J1 y el del J2 a la vez, y caminen. Cierra la
ventana o presiona ESC para salir.
"""

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import pygame
pygame.init()
from entidades.jugador import TECLAS_POR_PUESTO

pantalla = pygame.display.set_mode((900, 560))
pygame.display.set_caption("Probar teclas")
fuente = pygame.font.SysFont("consolas", 17)
reloj = pygame.time.Clock()
eventos = []


def escribir(texto, x, y, color=(230, 232, 240)):
    pantalla.blit(fuente.render(texto, True, color), (x, y))


corriendo = True
while corriendo:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
            corriendo = False
        elif ev.type in (pygame.KEYDOWN, pygame.KEYUP):
            tipo = "abajo " if ev.type == pygame.KEYDOWN else "arriba"
            eventos.append(f"{tipo}  {pygame.key.name(ev.key):<14} scancode {ev.scancode:<4} "
                           f"mods {ev.mod:#06x}")
            del eventos[:-14]
    teclas = pygame.key.get_pressed()
    pantalla.fill((14, 16, 26))
    escribir("Mantén el sigilo de los dos a la vez (ESC sale)", 20, 16, (255, 214, 64))
    abajo = [pygame.key.name(k) for k in range(len(teclas)) if teclas[k]]
    escribir("presionadas: " + (", ".join(abajo) or "-"), 20, 56)
    for i, nombre in enumerate(("J1 (WASD)", "J2 (flechas)")):
        sigilo = any(teclas[k] for k in TECLAS_POR_PUESTO[i]["sigilo"] if k < len(teclas))
        nombres = " o ".join(pygame.key.name(k) for k in TECLAS_POR_PUESTO[i]["sigilo"])
        escribir(f"Sigilo {nombre}: {'SÍ' if sigilo else 'no'}   ({nombres})", 20, 96 + i * 28,
                 (96, 220, 130) if sigilo else (160, 164, 180))
    escribir("últimos eventos:", 20, 170, (255, 214, 64))
    for i, linea in enumerate(eventos):
        escribir(linea, 20, 198 + i * 24)
    pygame.display.flip()
    reloj.tick(60)
pygame.quit()
