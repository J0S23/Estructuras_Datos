"""Pantalla de la ciudad: muestra el estado actual (indicadores) alimentado por GameState."""

import pygame

from assets import cargar_imagen, dibujar_fondo_o_color


INDICADOR_LABELS = {
    "informacion_verificada": "Información verificada",
    "confianza_ciudadana": "Confianza ciudadana",
    "convivencia": "Convivencia",
    "bienestar_digital": "Bienestar digital",
    "desinformacion": "Desinformación",
    "conflictos": "Conflictos",
}

# Icono opcional por indicador (Imagenes/UI/...). Si no existe todavía, se omite sin romper nada.
INDICADOR_ICONOS = {
    "informacion_verificada": "Imagenes/UI/icono_verificacion.png",
    "confianza_ciudadana": "Imagenes/UI/icono_confianza.png",
    "desinformacion": "Imagenes/UI/icono_desinformacion.png",
    "convivencia": "Imagenes/UI/icono_convivencia.png",
}


def render_ciudad(screen, font=None, state=None, small_font=None):
    if font is None:
        font = pygame.font.SysFont("arial", 30)
    if small_font is None:
        small_font = pygame.font.SysFont("arial", 20)

    # Fondo: usa Imagenes/Fondos/fondo_ciudad.png si ya existe, si no rellena de color.
    dibujar_fondo_o_color(screen, "Imagenes/Fondos/fondo_ciudad.png", (40, 90, 80))

    label = font.render("CIUDAD NOVA", True, (255, 255, 255))
    screen.blit(label, (40, 30))

    if state is not None:
        rol = small_font.render(f"Rol: {state.rol_actual}", True, (230, 230, 230))
        screen.blit(rol, (40, 85))
        puntaje = small_font.render(f"Puntaje: {state.puntaje}", True, (230, 230, 230))
        screen.blit(puntaje, (40, 110))

    y = 155
    titulo = small_font.render("Indicadores de la ciudad:", True, (240, 220, 140))
    screen.blit(titulo, (40, y))
    y += 36

    if state is not None:
        for clave, valor in state.indicadores.items():
            nombre = INDICADOR_LABELS.get(clave, clave)

            x_texto = 60
            ruta_icono = INDICADOR_ICONOS.get(clave)
            if ruta_icono:
                icono = cargar_imagen(ruta_icono, (22, 22))
                if icono is not None:
                    screen.blit(icono, (60, y - 2))
                    x_texto = 90

            texto = f"{nombre}: {valor}"
            label = small_font.render(texto, True, (255, 255, 255))
            screen.blit(label, (x_texto, y))

            barra_fondo = pygame.Rect(360, y + 2, 200, 14)
            pygame.draw.rect(screen, (20, 20, 20), barra_fondo, 1)
            ancho = int(196 * max(0, min(100, valor)) / 100)
            pygame.draw.rect(screen, (120, 220, 140), (barra_fondo.x + 2, barra_fondo.y + 2, ancho, 10))
            y += 32

    ayuda = small_font.render("[E] Publicaciones   [D] Hablar con alguien   [H] Ayuda   [C] Créditos", True, (200, 200, 200))
    screen.blit(ayuda, (40, screen.get_height() - 45))
