"""Visor de personajes: revisa que los sprites de un personaje carguen bien.

Cómo correrlo, desde la raíz del proyecto:

    python Editores/visor_personajes.py
    python Editores/visor_personajes.py P2

Muestra el personaje animado y permite recorrer las 8 direcciones y las tres
animaciones, para confirmar que no falte ninguna hoja antes de meterlo al
juego.

Controles:
    Flechas / WASD   -> mueven al personaje (cambia de dirección y camina)
    ESPACIO           -> cambia la animación en reposo (idle / breathing)
    TAB                -> siguiente personaje de Imagenes/Personajes/
    H                   -> muestra/oculta los hitboxes
    ESC                  -> salir
"""

import os
import sys

import pygame

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Movimiento.Personaje import (  # noqa: E402
    DIRECCIONES, Personaje, detectar_hojas,
)


CARPETA_PERSONAJES = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Imagenes", "Personajes"
)
ANCHO, ALTO = 900, 620


def listar_personajes():
    if not os.path.isdir(CARPETA_PERSONAJES):
        return []
    return [
        nombre for nombre in sorted(os.listdir(CARPETA_PERSONAJES))
        if os.path.isdir(os.path.join(CARPETA_PERSONAJES, nombre))
        and detectar_hojas(os.path.join(CARPETA_PERSONAJES, nombre))
    ]


def informe(nombre):
    """Texto con qué hojas tiene y cuáles le faltan a un personaje."""
    hojas = detectar_hojas(os.path.join(CARPETA_PERSONAJES, nombre))
    lineas = []
    for animacion in ("idle", "breathing", "walking"):
        presentes = hojas.get(animacion, {})
        faltan = [d for d in DIRECCIONES if d not in presentes]
        estado = "completo" if not faltan else f"faltan {len(faltan)}: {', '.join(faltan)}"
        lineas.append(f"{animacion}: {len(presentes)}/8 ({estado})")
    return lineas


def main():
    personajes = listar_personajes()
    if not personajes:
        print(f"No se encontró ningún personaje con sprites en {CARPETA_PERSONAJES}.")
        print("Cada personaje va en su propia subcarpeta (P1, P2, ...).")
        return

    pedido = sys.argv[1] if len(sys.argv) > 1 else None
    indice = personajes.index(pedido) if pedido in personajes else 0

    pygame.init()
    pygame.display.set_caption("Visor de personajes - Alcalde Digital")
    screen = pygame.display.set_mode((ANCHO, ALTO))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 18)
    font_chico = pygame.font.SysFont("arial", 15)

    def cargar(idx):
        nombre = personajes[idx]
        ruta = os.path.join(CARPETA_PERSONAJES, nombre)
        personaje = Personaje(ANCHO // 2 - 46, ALTO // 2 - 46, ruta, velocidad=4)
        origen = getattr(personaje, "ruta_config", None)
        for linea in [f"--- {nombre} ---"] + informe(nombre):
            print(linea)
        print("config de hitbox:", os.path.basename(origen) if origen else "ninguno (valores por defecto)")
        print(f"escala: {personaje.scale}  hitbox: {personaje.hitbox_w}x{personaje.hitbox_h}")
        return nombre, personaje

    nombre, personaje = cargar(indice)
    mostrar_hitboxes = False
    reposo = "breathing"

    corriendo = True
    while corriendo:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                corriendo = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    corriendo = False
                elif evento.key == pygame.K_TAB:
                    indice = (indice + 1) % len(personajes)
                    nombre, personaje = cargar(indice)
                elif evento.key == pygame.K_h:
                    mostrar_hitboxes = not mostrar_hitboxes
                elif evento.key == pygame.K_SPACE:
                    reposo = "idle" if reposo == "breathing" else "breathing"

        personaje.actualizar()
        if not personaje.moviendose and personaje.estado != reposo:
            personaje.estado = reposo
            personaje.frame_actual = 0

        screen.fill((28, 30, 44))
        for gx in range(0, ANCHO, 46):
            pygame.draw.line(screen, (36, 38, 56), (gx, 0), (gx, ALTO))
        for gy in range(0, ALTO, 46):
            pygame.draw.line(screen, (36, 38, 56), (0, gy), (ANCHO, gy))

        personaje.dibujar(screen)

        if mostrar_hitboxes:
            pygame.draw.rect(screen, (230, 60, 60), personaje.hitbox, 2)
            pygame.draw.rect(screen, (255, 210, 40), personaje.interactable_hitbox, 2)

        barra = pygame.Surface((ANCHO, 96), pygame.SRCALPHA)
        barra.fill((0, 0, 0, 180))
        screen.blit(barra, (0, 0))

        frames = len(personaje.animaciones.get(personaje.estado, {}).get(personaje.direccion, []))
        screen.blit(font.render(
            f"{nombre}   dirección: {personaje.direccion}   animación: {personaje.estado} "
            f"({frames} frames)   escala: {personaje.scale:.2f}",
            True, (255, 255, 255)), (12, 8))
        screen.blit(font_chico.render(
            "   ".join(informe(nombre)), True, (200, 210, 235)), (12, 34))
        screen.blit(font_chico.render(
            "Flechas/WASD mover   ESPACIO reposo   TAB cambiar personaje   H hitboxes   ESC salir",
            True, (180, 190, 215)), (12, 60))

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
