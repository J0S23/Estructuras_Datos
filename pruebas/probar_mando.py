"""Muestra en vivo qué botón, eje o cruceta manda el mando conectado.

    python pruebas/probar_mando.py

Sirve para revisar que los números de mandos.py (BOTONES, EJE_X, EJE_Y,
EJE_LT) coincidan con tu control. Presiona cada botón y mira qué número sale.
Cierra la ventana o presiona ESC para salir.
"""

import os, sys
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
import pygame
import mandos

pygame.init()
pantalla = pygame.display.set_mode((720, 420))
pygame.display.set_caption("Probar mando")
fuente = pygame.font.SysFont("consolas", 18)
reloj = pygame.time.Clock()
m = mandos.Mandos()
log = []

while True:
    for ev in pygame.event.get():
        if ev.type == pygame.QUIT or (ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE):
            pygame.quit(); sys.exit()
        acciones = m.evento(ev)
        if ev.type == pygame.JOYBUTTONDOWN:
            log.append(f"botón {ev.button}  ->  {acciones}")
        elif ev.type == pygame.JOYHATMOTION:
            log.append(f"cruceta {ev.value}  ->  {acciones}")
        elif ev.type == pygame.JOYAXISMOTION and abs(ev.value) > 0.6:
            log.append(f"eje {ev.axis} = {ev.value:+.2f}  ->  {acciones}")
        elif ev.type in (pygame.JOYDEVICEADDED, pygame.JOYDEVICEREMOVED):
            log.append(f"mandos conectados: {sorted(p + 1 for p in m.por_puesto)} (jugadores)")
        log = log[-14:]
    pantalla.fill((18, 19, 30))
    y = 12
    if not m.por_puesto:
        pantalla.blit(fuente.render("No hay mandos conectados.", True, (245, 130, 120)), (12, y))
        y += 26
    for puesto, joy in m.por_puesto.items():
        estado = {a: m.presionada(mandos.tecla_virtual(puesto, a)) for a in mandos.ACCIONES}
        activos = [a for a, v in estado.items() if v]
        pantalla.blit(fuente.render(f"Jugador {puesto + 1}: {joy.get_name()}", True, (255, 214, 64)), (12, y))
        y += 22
        pantalla.blit(fuente.render(f"  ahora: {', '.join(activos) or '-'}", True, (235, 238, 250)), (12, y))
        y += 30
    for linea in log:
        pantalla.blit(fuente.render(linea, True, (150, 156, 190)), (12, y))
        y += 20
    pygame.display.flip()
    reloj.tick(60)
