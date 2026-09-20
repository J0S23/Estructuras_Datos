"""El mundo de juego: el mapa, sus colisiones y las cámaras de cada jugador.

Carga un fondo de Imagenes/Fondos/ junto con las hitboxes que se hayan
dibujado para él en Hitboxes/<nombre>_hitboxes.json (ver CLAUDE.md).
Las coordenadas del archivo son proporciones de 0 a 1, así que aquí se
desnormalizan contra el tamaño al que se dibuja el mundo.
"""

import json
import os
from collections import deque

import pygame


CARPETA_FONDOS = os.path.join(os.path.dirname(__file__), "Imagenes", "Fondos")
CARPETA_HITBOXES = os.path.join(os.path.dirname(__file__), "Hitboxes")

# El mapa se dibuja más grande que su archivo original para que el personaje
# no ocupe media pantalla. Se escala con nearest neighbor para no emborronar
# el pixel art.
ESCALA_MAPA = 3


class Mundo:
    def __init__(self, nombre_mapa="Colegio", escala=ESCALA_MAPA):
        self.nombre_mapa = nombre_mapa
        self.escala = escala
        self.imagen = self._cargar_mapa()
        self.ancho, self.alto = self.imagen.get_size()
        self.paredes, self.interactuables = self._cargar_hitboxes()

    # -- Carga -------------------------------------------------------------------

    def _cargar_mapa(self):
        for extension in (".png", ".jpg", ".jpeg"):
            ruta = os.path.join(CARPETA_FONDOS, self.nombre_mapa + extension)
            if os.path.isfile(ruta):
                original = pygame.image.load(ruta).convert()
                ancho, alto = original.get_size()
                return pygame.transform.scale(
                    original, (ancho * self.escala, alto * self.escala)
                )
        # Sin mapa: un fondo liso para que el juego siga corriendo.
        respaldo = pygame.Surface((960 * 2, 600 * 2))
        respaldo.fill((46, 62, 54))
        return respaldo

    def _cargar_hitboxes(self):
        """Devuelve (paredes, interactuables) como listas de Rect del mundo."""
        ruta = os.path.join(CARPETA_HITBOXES, f"{self.nombre_mapa}_hitboxes.json")
        paredes, interactuables = [], []
        try:
            with open(ruta, "r", encoding="utf-8") as fh:
                datos = json.load(fh)
        except (OSError, json.JSONDecodeError):
            return paredes, interactuables

        for h in datos.get("hitboxes", []):
            if h.get("type") != "rect":
                continue  # por ahora solo rectángulos
            try:
                rect = pygame.Rect(
                    int(h["rx"] * self.ancho),
                    int(h["ry"] * self.alto),
                    max(1, int(h["rw"] * self.ancho)),
                    max(1, int(h["rh"] * self.alto)),
                )
            except (KeyError, TypeError):
                continue
            if h.get("role") == "interactable":
                interactuables.append(rect)
            else:
                paredes.append(rect)
        return paredes, interactuables

    # -- Consultas ----------------------------------------------------------------

    def colisiona(self, rect):
        """True si el rect choca con una pared o se sale del mapa."""
        if rect.left < 0 or rect.top < 0 or rect.right > self.ancho or rect.bottom > self.alto:
            return True
        return rect.collidelist(self.paredes) != -1

    def interactuable_en(self, rect):
        """Devuelve el rect interactuable que toca, o None."""
        indice = rect.collidelist(self.interactuables)
        return self.interactuables[indice] if indice != -1 else None

    def punto_libre(self, preferido, ancho=40, alto=24):
        """Busca una posición sin paredes cerca de `preferido` (x, y del mundo)."""
        px, py = preferido
        for radio in range(0, max(self.ancho, self.alto), 16):
            for dx, dy in ((0, 0), (radio, 0), (-radio, 0), (0, radio), (0, -radio),
                           (radio, radio), (-radio, -radio), (radio, -radio), (-radio, radio)):
                candidato = pygame.Rect(px + dx, py + dy, ancho, alto)
                if not self.colisiona(candidato):
                    return candidato.x, candidato.y
        return px, py

    def area_alcanzable(self, desde, ancho=48, alto=19, paso=16):
        """Celdas del mapa a las que se puede llegar caminando desde `desde`.

        Un rectángulo puede no chocar con ninguna pared y aun así ser
        inalcanzable, porque está dentro de un cuarto cerrado. La única forma
        de saberlo es recorrer el mapa como lo haría el jugador: se avanza de
        celda en celda en las cuatro direcciones (BFS con una cola) y se
        devuelve todo lo que se pudo tocar.
        """
        inicio = (int(desde[0]) // paso * paso, int(desde[1]) // paso * paso)
        vistos = {inicio}
        cola = deque([inicio])
        while cola:
            cx, cy = cola.popleft()
            for dx, dy in ((paso, 0), (-paso, 0), (0, paso), (0, -paso)):
                vecino = (cx + dx, cy + dy)
                if vecino in vistos:
                    continue
                if not (0 <= vecino[0] <= self.ancho - ancho
                        and 0 <= vecino[1] <= self.alto - alto):
                    continue
                if self.colisiona(pygame.Rect(vecino[0], vecino[1], ancho, alto)):
                    continue
                vistos.add(vecino)
                cola.append(vecino)
        return vistos

    def zonas_inalcanzables(self, zonas, desde, ancho=48, alto=19, paso=16):
        """Zonas que el jugador no podría alcanzar desde `desde`.

        Se llama al empezar la partida. Si devuelve algo, es que alguien puso
        una zona dentro de un cuarto cerrado y hay que mover sus coordenadas en
        data/tareas.py. Vale el costo: encontrar esto jugando es mucho más caro
        que un recorrido al arrancar.
        """
        alcanzable = self.area_alcanzable(desde, ancho, alto, paso)
        malas = []
        for zona in zonas:
            rect = zona["rect"]
            if not any(pygame.Rect(c[0], c[1], ancho, alto).colliderect(rect)
                       for c in alcanzable):
                malas.append(zona)
        return malas

    def camara(self, centro, ancho_vista, alto_vista):
        """Rect de cámara centrado en `centro`, recortado a los bordes del mapa."""
        cx, cy = centro
        x = int(cx - ancho_vista / 2)
        y = int(cy - alto_vista / 2)
        x = max(0, min(x, max(0, self.ancho - ancho_vista)))
        y = max(0, min(y, max(0, self.alto - alto_vista)))
        return pygame.Rect(x, y, ancho_vista, alto_vista)
