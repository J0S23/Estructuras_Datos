"""Dibujo de la misión del infiltrado (infiltrado.py): las pruebas en el mapa y
sus iconos (también los usa el inventario, screens/paneles.py).

Figuras provisionales hasta que llegue el arte: cuando Anny haga los sprites
se cambian aquí sin tocar la lógica.
"""

import math

import pygame

COLOR_PRUEBA = (233, 120, 200)
COLOR_OSCURO = (40, 20, 40)


def icono_prueba(screen, tipo, centro, tam, color=COLOR_PRUEBA):
    """Audio (ondas), expediente (carpeta) o captura (camarita)."""
    cx, cy = centro
    if tipo == "prueba_audio":
        alturas = (0.3, 0.7, 1.0, 0.55, 0.85, 0.4)
        ancho_barra = max(2, tam // 9)
        x0 = cx - (len(alturas) * (ancho_barra + 1)) // 2
        for i, h in enumerate(alturas):
            alto = max(3, int(tam * 0.8 * h))
            pygame.draw.rect(screen, color, (x0 + i * (ancho_barra + 1), cy - alto // 2,
                                             ancho_barra, alto))
    elif tipo == "prueba_expediente":
        cuerpo = pygame.Rect(0, 0, int(tam * 0.9), int(tam * 0.66))
        cuerpo.center = (cx, cy + tam // 10)
        pestana = pygame.Rect(cuerpo.x, cuerpo.y - tam // 7, tam // 3, tam // 7 + 1)
        pygame.draw.rect(screen, color, pestana)
        pygame.draw.rect(screen, color, cuerpo)
        for i in (1, 2):
            y = cuerpo.y + cuerpo.height * i // 3
            pygame.draw.line(screen, COLOR_OSCURO, (cuerpo.x + 4, y), (cuerpo.right - 4, y), 1)
    else:   # captura de cámara
        cuerpo = pygame.Rect(0, 0, int(tam * 0.9), int(tam * 0.62))
        cuerpo.center = (cx, cy + tam // 12)
        pygame.draw.rect(screen, color, cuerpo, border_radius=3)
        pygame.draw.rect(screen, color, (cuerpo.x + tam // 6, cuerpo.y - tam // 8,
                                         tam // 3, tam // 8 + 1))
        pygame.draw.circle(screen, COLOR_OSCURO, cuerpo.center, max(3, tam // 5))
        pygame.draw.circle(screen, color, cuerpo.center, max(1, tam // 10))


def dibujar_pruebas(screen, offset, camara, caso, tiempo_ms):
    """Las pruebas sin recoger: un icono rosado que late, para que se note
    que es algo distinto de las piezas y las notas."""
    if caso is None or not caso.activo:
        return
    brillo = 0.55 + 0.45 * math.sin(tiempo_ms / 260)
    for prueba in caso.pruebas:
        if prueba["tomada"] or not prueba["rect"].colliderect(camara):
            continue
        r = prueba["rect"].move(-offset[0], -offset[1])
        halo = pygame.Surface((r.width + 24, r.height + 24), pygame.SRCALPHA)
        pygame.draw.ellipse(halo, (*COLOR_PRUEBA, int(40 + 50 * brillo)), halo.get_rect())
        screen.blit(halo, (r.x - 12, r.y - 12))
        pygame.draw.rect(screen, (30, 18, 34), r, border_radius=5)
        pygame.draw.rect(screen, COLOR_PRUEBA, r, 2, border_radius=5)
        icono_prueba(screen, prueba["tipo"], r.center, r.width - 8)
