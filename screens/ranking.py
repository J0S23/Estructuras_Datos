"""El ranking de la feria (juego/ranking.py): la tabla y las iniciales.

- `render_ranking(screen, entradas, resaltar)`: Menú > Ranking y la pantalla
  de atracción. Los 10 mejores; el último que se anotó, resaltado.
- `render_iniciales(screen, estado)`: encima de los resultados, el nombre del
  equipo (hasta MAX_LETRAS, se escribe o se arma con el mando) y su puntaje
  (o, ya anotado, en qué puesto quedó). Los nombres largos se cortan con
  "..." en la tabla.
"""

import math

import pygame

from juego.fuentes import fuente_de_tamano
from juego import ranking as datos_ranking
from screens import estilo

COLOR_ORO = (255, 214, 64)
COLOR_PLATA = (205, 215, 235)
COLOR_BRONCE = (225, 150, 90)
COLOR_BIEN = (96, 210, 130)
COLOR_MAL = (245, 130, 120)
NOMBRE_DIFICULTAD = {"facil": "Fácil", "normal": "Normal", "dificil": "Difícil",
                     "inteligente": "Inteligente"}


def _tiempo(segundos):
    segundos = max(0, int(segundos or 0))
    return f"{segundos // 60}:{segundos % 60:02d}"


def _cortar(texto, fuente, ancho):
    """El nombre de un equipo cortado con "..." si no cabe en `ancho`."""
    if fuente.size(texto)[0] <= ancho:
        return texto
    while texto and fuente.size(texto + "...")[0] > ancho:
        texto = texto[:-1]
    return texto.rstrip() + "..."


def render_ranking(screen, entradas, resaltar=None, pie=True):
    """La tabla (con `resaltar` = el id de una entrada, que se ilumina)."""
    ancho, alto = screen.get_size()
    estilo.fondo(screen)
    tam = max(28, min(64, alto // 13))
    rect_titulo = estilo.titulo(screen, "RANKING DE LA FERIA", (ancho // 2, int(alto * 0.1)), tam)
    lista = datos_ranking.ordenar(entradas)[:datos_ranking.MOSTRAR]
    caja = pygame.Rect(0, 0, min(ancho - 40, 1000), int(alto * 0.68))
    caja.midtop = (ancho // 2, rect_titulo.bottom + max(10, alto // 40))
    estilo.panel(screen, caja)
    f = fuente_de_tamano(max(14, min(26, alto // 36)))
    fc = fuente_de_tamano(max(12, min(18, alto // 54)))
    if not lista:
        estilo.texto(screen, "Todavía no se anota ningún equipo.", f, caja.center, estilo.COLOR_TEXTO, "center")
        estilo.texto(screen, "¡Sean los primeros en escapar!", fc,
                     (caja.centerx, caja.centery + f.get_linesize() + 6), estilo.COLOR_TENUE, "center")
    else:
        columnas = [("#", 0.05, "midleft"), ("Equipo", 0.13, "midleft"), ("Puntaje", 0.42, "midright"),
                    ("Resultado", 0.47, "midleft"), ("Tiempo", 0.74, "midright"),
                    ("Dificultad", 0.78, "midleft")]
        y = caja.y + 16
        for nombre, fx, ancla in columnas:
            estilo.texto(screen, nombre, fc, (caja.x + int(caja.w * fx), y + fc.get_height() // 2),
                         estilo.COLOR_TENUE, ancla)
        y += fc.get_linesize() + 6
        pygame.draw.line(screen, (60, 70, 110), (caja.x + 14, y), (caja.right - 14, y), 1)
        fila = max(f.get_linesize() + 6, (caja.bottom - y - 14) // max(1, datos_ranking.MOSTRAR))
        t = pygame.time.get_ticks() / 1000
        for k, e in enumerate(lista):
            centro_y = y + 4 + fila * k + fila // 2
            marcada = resaltar is not None and e.get("id") == resaltar
            if marcada:
                brillo = 0.6 + 0.4 * math.sin(t * 5)
                r = pygame.Rect(caja.x + 8, centro_y - fila // 2 + 1, caja.w - 16, fila - 2)
                capa = pygame.Surface(r.size, pygame.SRCALPHA)
                capa.fill((255, 214, 64, int(40 + 40 * brillo)))
                screen.blit(capa, r.topleft)
                pygame.draw.rect(screen, COLOR_ORO, r, 1, border_radius=6)
            color = (COLOR_ORO, COLOR_PLATA, COLOR_BRONCE)[k] if k < 3 else estilo.COLOR_TEXTO
            nombre = _cortar(str(e.get("nombre", "???")), f,
                             int(caja.w * (0.42 - 0.13)) - f.size(str(e.get("puntaje", 0)))[0] - 16)
            valores = [f"{k + 1}", nombre, str(e.get("puntaje", 0)),
                       "Escaparon" if e.get("escaparon") else "No escaparon",
                       _tiempo(e.get("tiempo_s")),
                       NOMBRE_DIFICULTAD.get(e.get("dificultad"), "-")]
            colores = [color, color, color, COLOR_BIEN if e.get("escaparon") else COLOR_MAL,
                       estilo.COLOR_TEXTO, estilo.COLOR_TENUE]
            for (nombre, fx, ancla), valor, c in zip(columnas, valores, colores):
                estilo.texto(screen, valor, f, (caja.x + int(caja.w * fx), centro_y), c, ancla)
    estilo.texto(screen, f"Puntaje = puntos del equipo + {datos_ranking.BONO_ESCAPE} si escapan "
                         f"(+1 por cada {datos_ranking.SEGUNDOS_POR_PUNTO} s que les sobren del reloj)",
                 fc, (ancho // 2, caja.bottom + 10), estilo.COLOR_TENUE, "midtop")
    if pie:
        estilo.pie(screen, "[ENTER] volver", alto - max(24, alto // 22))


def render_iniciales(screen, estado):
    """Las iniciales del equipo encima de los resultados (`estado` es un
    juego/ranking.Iniciales). Ya anotadas, una pastilla con el puesto."""
    ancho, alto = screen.get_size()
    f = fuente_de_tamano(max(16, min(28, alto // 34)))
    fc = fuente_de_tamano(max(12, min(18, alto // 54)))
    if estado.hecho:
        if estado.saltado or estado.puesto is None:
            return
        texto = f"¡{estado.nombre} quedó #{estado.puesto} de {estado.total} en el ranking!"
        img = f.render(texto, True, COLOR_ORO)
        caja = pygame.Rect(0, 0, img.get_width() + 36, img.get_height() + 16)
        caja.midtop = (ancho // 2, 10)
        estilo.tarjeta(screen, caja, True, COLOR_ORO, franja=False)
        screen.blit(img, img.get_rect(center=caja.center))
        return
    # Se oscurece todo y va el recuadro en el medio.
    velo = pygame.Surface((ancho, alto), pygame.SRCALPHA)
    velo.fill((4, 6, 16, 170))
    screen.blit(velo, (0, 0))
    caja = pygame.Rect(0, 0, min(ancho - 40, max(560, int(ancho * 0.62))), 0)
    # La letra del nombre: la más grande en la que caben MAX_LETRAS anchas.
    tam = max(20, min(72, alto // 10))
    while tam > 20 and fuente_de_tamano(tam).size("W" * datos_ranking.MAX_LETRAS)[0] > caja.w - 60:
        tam -= 2
    fl = fuente_de_tamano(tam)
    lado = fl.get_height() + 16
    caja.h = lado + f.get_linesize() * 2 + fc.get_linesize() * 3 + 70
    caja.center = (ancho // 2, alto // 2)
    estilo.panel(screen, caja, COLOR_ORO)
    y = caja.y + 14
    estilo.texto(screen, "¡Anoten a su equipo en el ranking!", f, (caja.centerx, y), COLOR_ORO, "midtop")
    y += f.get_linesize()
    detalle = estado.detalle
    if detalle["escaparon"] and detalle["sobro"]:
        resumen = (f"Puntaje: {estado.puntaje}  ({detalle['puntos']} del equipo + "
                   f"{datos_ranking.BONO_ESCAPE} por escapar + {detalle['sobro']} del reloj)")
    elif detalle["escaparon"]:
        resumen = (f"Puntaje: {estado.puntaje}  ({detalle['puntos']} del equipo + "
                   f"{datos_ranking.BONO_ESCAPE} por escapar)")
    else:
        resumen = f"Puntaje: {estado.puntaje}  ({detalle['puntos']} del equipo)"
    estilo.texto(screen, resumen, fc, (caja.centerx, y), estilo.COLOR_TEXTO, "midtop")
    y += fc.get_linesize() + 14
    # El campo del nombre.
    campo = pygame.Rect(caja.x + 24, y + 10, caja.w - 48, lado)
    estilo.tarjeta(screen, campo, True, COLOR_ORO, franja=False)
    t = pygame.time.get_ticks() / 1000
    letras = estado.letras
    texto = "".join(letras)
    ancho_texto = fl.size(texto)[0] if texto else 0
    x0 = campo.centerx - ancho_texto // 2
    cy = campo.centery
    if texto:
        img = fl.render(texto, True, estilo.COLOR_TEXTO)
        screen.blit(img, img.get_rect(midleft=(x0, cy)))
    else:
        img = fc.render("Escriban el nombre del equipo", True, estilo.COLOR_TENUE)
        screen.blit(img, img.get_rect(center=(campo.centerx, cy)))
    # Dónde está el cursor: la letra escogida (se cambia con arriba/abajo) o
    # el hueco de una nueva al final.
    x_cursor = x0 + (fl.size(texto[:estado.pos])[0] if estado.pos else 0)
    if estado.pos < len(letras):
        ancho_letra = fl.size(letras[estado.pos])[0] or fl.size("A")[0]
        marca = pygame.Rect(x_cursor - 2, campo.y + 6, ancho_letra + 4, campo.h - 12)
        pygame.draw.rect(screen, COLOR_ORO, marca, 2, border_radius=4)
        centro_x = marca.centerx
    else:
        if int(t * 2.5) % 2 == 0 or not texto:
            pygame.draw.line(screen, COLOR_ORO, (x_cursor + 2, campo.y + 10), (x_cursor + 2, campo.bottom - 10), 3)
        centro_x = x_cursor + 2 + (fl.size("A")[0] // 2 if texto else 0)
    salto = int(3 * math.sin(t * 6))
    for signo in (-1, 1):
        punta = (centro_x, (campo.top - 4 + salto) if signo < 0 else (campo.bottom + 4 - salto))
        pygame.draw.polygon(screen, COLOR_ORO, [(punta[0], punta[1]),
                                                (punta[0] - 7, punta[1] - 7 * signo),
                                                (punta[0] + 7, punta[1] - 7 * signo)])
    cuenta = fc.render(f"{len(letras)}/{datos_ranking.MAX_LETRAS}", True, estilo.COLOR_TENUE)
    screen.blit(cuenta, cuenta.get_rect(topright=(campo.right, campo.bottom + 6)))
    y = campo.bottom + 6 + fc.get_linesize() + 4
    estilo.pie(screen, "[ENTER] listo  [BORRAR] borrar  [ESC] no anotarse", y + fc.get_height() // 2, fc)
    estilo.pie(screen, "Con el mando: [ARRIBA/ABAJO] letra  [IZQ/DER] mover  [A] listo",
               y + fc.get_linesize() + 6 + fc.get_height() // 2, fc)
