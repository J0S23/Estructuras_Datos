"""Las dos pantallas previas a la partida: cuántos juegan y quién es quién.

Antes el rol venía atado al puesto —el primero Ciudadano, el segundo
Candidato—, así que no había nada que elegir. Ahora hay dos pasos:

1. **Cantidad**: 2, 3 o 4. Ese número decide en cuántas partes se corta la
   pantalla, así que se pregunta antes que nada.
2. **Roles**: la pantalla ya se ve partida y cada jugador escoge el suyo desde
   su propia sección, con sus propias teclas. Dos no pueden repetir rol: el que
   ya está tomado se ve tachado y no se puede confirmar.

La sección de cada jugador se dibuja con el mismo `calcular_viewports` de la
partida, así que desde la selección ya se ve qué trozo de pantalla le va a
tocar a cada uno.
"""

import pygame

from data.roles import ROLES, MINIMO_JUGADORES, MAXIMO_JUGADORES
from fuentes import fuente_de_tamano


COLOR_FONDO = (26, 28, 48)
COLOR_TITULO = (255, 214, 64)
COLOR_TEXTO = (245, 246, 252)
COLOR_TENUE = (168, 176, 214)
COLOR_BORDE = (120, 132, 190)
COLOR_SELECCION_FONDO = (52, 57, 92)
COLOR_TOMADO = (104, 108, 132)
COLOR_LISTO = (96, 188, 118)

MARGEN = 18

# Franja de arriba reservada para el aviso de "faltan N por elegir". Las
# secciones que tocan el borde superior empiezan su contenido por debajo, o el
# aviso se monta encima del título del jugador de la derecha.
ALTO_AVISO = 34


# --------------------------------------------------------------------------
# Paso 1: cuántos juegan
# --------------------------------------------------------------------------

def render_cantidad(screen, seleccionado):
    """Menú de 2, 3 o 4 jugadores. `seleccionado` es el índice en OPCIONES."""
    screen.fill(COLOR_FONDO)
    ancho, alto = screen.get_size()

    f_titulo = fuente_de_tamano(max(22, min(40, ancho // 38)))
    f = fuente_de_tamano(max(15, min(24, ancho // 62)))

    titulo = f_titulo.render("¿CUÁNTOS JUEGAN?", True, COLOR_TEXTO)
    screen.blit(titulo, titulo.get_rect(center=(ancho // 2, int(alto * 0.22))))

    aviso = f.render("Todos en el mismo teclado, cada uno con su parte de la pantalla.",
                     True, COLOR_TENUE)
    screen.blit(aviso, aviso.get_rect(center=(ancho // 2, int(alto * 0.22) + 46)))

    # El recuadro cubre las DOS líneas de la opción (el número y el reparto de
    # pantalla). Antes solo envolvía la primera y su borde inferior cruzaba por
    # encima de la segunda, tachándola.
    linea = f.get_linesize()
    alto_opcion = linea * 2 + 16
    separacion = 26
    y = int(alto * 0.42)

    for i, cantidad in enumerate(OPCIONES):
        elegido = (i == seleccionado)
        ancho_caja = min(int(ancho * 0.6), 560)
        caja = pygame.Rect(0, 0, ancho_caja, alto_opcion)
        caja.center = (ancho // 2, y + alto_opcion // 2)

        if elegido:
            pygame.draw.rect(screen, COLOR_SELECCION_FONDO, caja)
            pygame.draw.rect(screen, COLOR_TITULO, caja, 2)

        texto = f.render(f"{cantidad} jugadores", True,
                         COLOR_TITULO if elegido else COLOR_TEXTO)
        screen.blit(texto, texto.get_rect(center=(ancho // 2, caja.y + 8 + linea // 2)))

        reparto = f.render(DESCRIPCION[cantidad], True, COLOR_TENUE)
        screen.blit(reparto, reparto.get_rect(center=(ancho // 2,
                                                      caja.y + 8 + linea + linea // 2)))
        y += alto_opcion + separacion

    pie = f.render("[W/S] o flechas para elegir    [ENTER] continuar    [ESC] volver al menú",
                   True, (194, 216, 248))
    screen.blit(pie, pie.get_rect(center=(ancho // 2, alto - 40)))


OPCIONES = list(range(MINIMO_JUGADORES, MAXIMO_JUGADORES + 1))

DESCRIPCION = {
    2: "pantalla partida en dos, lado a lado",
    3: "dos arriba y uno abajo, a lo ancho",
    4: "pantalla partida en cuatro",
}


# --------------------------------------------------------------------------
# Paso 2: qué rol juega cada uno
# --------------------------------------------------------------------------

def render_roles(screen, viewports, seleccion):
    """Dibuja la selección de rol de cada jugador en su propia sección.

    `seleccion` es una lista con un dict por jugador: cursor (índice del rol
    sobre el que está), listo (si ya confirmó) y rol (el nombre confirmado).
    """
    screen.fill((18, 16, 30))

    tomados = {s["rol"] for s in seleccion if s["listo"]}
    for indice, vista in enumerate(viewports):
        if indice >= len(seleccion):
            break
        # Solo las secciones pegadas al borde superior ceden espacio al aviso.
        tope = ALTO_AVISO if vista.top < ALTO_AVISO else 0
        _seccion_jugador(screen, vista, indice, seleccion[indice], tomados, tope)

    _separadores(screen, viewports)

    f = fuente_de_tamano(max(13, min(20, screen.get_width() // 80)))
    faltan = sum(1 for s in seleccion if not s["listo"])
    if faltan:
        mensaje = f"Faltan {faltan} por elegir" if faltan > 1 else "Falta uno por elegir"
        color = COLOR_TENUE
    else:
        mensaje = "Todos listos. Empezando…"
        color = COLOR_LISTO
    # Arriba y no abajo: con cuatro jugadores el borde inferior lo ocupan las
    # pistas de teclas de los dos de abajo, y el aviso se les montaba encima.
    etiqueta = f.render(mensaje, True, color)
    caja = etiqueta.get_rect(center=(screen.get_width() // 2, ALTO_AVISO // 2))
    fondo = pygame.Surface((etiqueta.get_width() + 28, etiqueta.get_height() + 12),
                           pygame.SRCALPHA)
    fondo.fill((18, 16, 30, 235))
    screen.blit(fondo, (caja.x - 14, caja.y - 6))
    pygame.draw.rect(screen, COLOR_BORDE,
                     (caja.x - 14, caja.y - 6, caja.width + 28, caja.height + 12), 1)
    screen.blit(etiqueta, caja)


def _seccion_jugador(screen, vista, indice, estado, tomados, tope=0):
    f = fuente_de_tamano(max(12, min(20, vista.width // 34)))
    f_titulo = fuente_de_tamano(max(14, min(26, vista.width // 26)))
    paso = f.get_linesize() + 2

    pygame.draw.rect(screen, COLOR_FONDO, vista)
    clip_previo = screen.get_clip()
    screen.set_clip(vista)

    y = vista.y + tope + MARGEN
    titulo = f_titulo.render(f"Jugador {indice + 1}", True,
                             COLOR_LISTO if estado["listo"] else COLOR_TEXTO)
    screen.blit(titulo, (vista.x + MARGEN, y))
    y += f_titulo.get_linesize()

    screen.blit(f.render(estado["controles"], True, COLOR_TENUE), (vista.x + MARGEN, y))
    y += paso + 8

    if estado["listo"]:
        _confirmado(screen, vista, f, y, estado)
        screen.set_clip(clip_previo)
        return

    for i, rol in enumerate(ROLES):
        sobre = (i == estado["cursor"])
        ocupado = rol["nombre"] in tomados

        alto_fila = paso * 2 + 8
        fila = pygame.Rect(vista.x + MARGEN - 6, y - 4, vista.width - MARGEN * 2 + 12, alto_fila)
        if sobre:
            pygame.draw.rect(screen, COLOR_SELECCION_FONDO, fila)
            pygame.draw.rect(screen, COLOR_TITULO if not ocupado else COLOR_TOMADO, fila, 2)

        if ocupado:
            nombre, color = f"{rol['nombre']} — ya lo tomaron", COLOR_TOMADO
        else:
            nombre, color = rol["nombre"], (rol["color"] if sobre else COLOR_TEXTO)
        screen.blit(f.render(("> " if sobre else "  ") + nombre, True, color),
                    (vista.x + MARGEN, y))
        y += paso
        screen.blit(f.render("   " + rol["resumen"], True,
                             COLOR_TOMADO if ocupado else COLOR_TENUE),
                    (vista.x + MARGEN, y))
        y += paso + 12

    pie = f.render(f"[{estado['tecla_mover']}] elegir   [{estado['tecla_ok']}] confirmar",
                   True, (194, 216, 248))
    screen.blit(pie, (vista.x + MARGEN, vista.bottom - MARGEN - pie.get_height()))
    screen.set_clip(clip_previo)


def _confirmado(screen, vista, f, y, estado):
    paso = f.get_linesize() + 2
    rol = next((r for r in ROLES if r["nombre"] == estado["rol"]), None)
    if rol is None:
        return

    caja = pygame.Rect(vista.x + MARGEN, y, vista.width - MARGEN * 2, paso * 4 + 16)
    pygame.draw.rect(screen, (34, 48, 40), caja)
    pygame.draw.rect(screen, COLOR_LISTO, caja, 2)

    y += 10
    screen.blit(f.render(rol["nombre"], True, rol["color"]), (caja.x + 12, y))
    y += paso
    screen.blit(f.render(rol["objetivo"], True, COLOR_TEXTO), (caja.x + 12, y))
    y += paso
    screen.blit(f.render(f"Personaje: {estado['personaje']}", True, COLOR_TENUE),
                (caja.x + 12, y))
    y += paso
    screen.blit(f.render("Listo", True, COLOR_LISTO), (caja.x + 12, y))

    pie = f.render(f"[{estado['tecla_ok']}] cambiar", True, (194, 216, 248))
    screen.blit(pie, (vista.x + MARGEN, vista.bottom - MARGEN - pie.get_height()))


def _separadores(screen, viewports):
    """Mismo criterio que en la partida: el borde de cada sección, no líneas
    de punta a punta, que con tres jugadores partían en dos la de abajo."""
    from screens.partida import _dibujar_separadores
    _dibujar_separadores(screen, viewports, color=(18, 16, 30), grosor=4)
