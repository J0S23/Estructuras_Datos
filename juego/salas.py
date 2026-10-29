"""Las salas del mapa (Control, Laboratorio, Pasillo...): rectángulos con
nombre que se dibujan con el editor de mapa (herramienta "Salas") y se
guardan en Hitboxes/<mapa>_objetos.json, junto con todo lo demás.

Una sala puede tener varios rectángulos con el mismo nombre (una sala en L,
o todos los pasillos llamados "Pasillo"). El HUD de cada jugador dice en
cuál está parado.
"""

import pygame


def preparar(objetos, mundo):
    """[(nombre, Rect en píxeles del mundo)] a partir de lo del archivo."""
    salas = []
    for s in objetos.get("salas") or []:
        rect = pygame.Rect(0, 0, max(1, int(s["ancho"] * mundo.ancho)),
                           max(1, int(s["alto"] * mundo.alto)))
        rect.center = (int(s["rx"] * mundo.ancho), int(s["ry"] * mundo.alto))
        salas.append((s["nombre"], rect))
    return salas


def sala_en(salas, punto):
    """El nombre de la sala donde está `punto`, o None. Si dos se tocan (en
    una puerta), gana la más chica: así una sala dentro de otra funciona."""
    mejor, area = None, None
    for nombre, rect in salas:
        if rect.collidepoint(punto) and (area is None or rect.width * rect.height < area):
            mejor, area = nombre, rect.width * rect.height
    return mejor
