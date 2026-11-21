"""El álbum de fotos (Diego, nov 21: "al final de la partida, junto a logros y
volver al menú, un botón 'Álbum de fotos' donde aparezcan todas las fotos que
subió el equipo con sus respectivas noticias").

Una polaroid por cada foto que el equipo publicó en NEXUS (desmentidos de
rumores y confirmaciones de noticias verdaderas), en el orden en que se
subieron: la foto (screens/foto.py: la que se tomó en el lugar; recortada si se
publicó sin ubicación; en red, si la tomó alguien de la otra laptop, el lugar
sacado del mapa), lo que mostraba, lo que decía la publicación que
verificaron, si era falso o verdad y quién la subió.

- `fotos_del_equipo(red)`: lo que va en el álbum (vacío = no sale el botón:
  screens/resultados.opciones_resultados).
- `render_album(screen, red, seleccion)`: la pantalla; devuelve los rects de
  las polaroids que se ven (el mouse las escoge).
- `mover(seleccion, tecla, total, columnas)`: las flechas.

Lo abren "Álbum de fotos" de los resultados (Game._activar_resultados, y en
red cliente.Sesion._activar_resultado); Esc, Enter o Borrar vuelven al resumen.
"""

import pygame

from juego.fuentes import fuente_de_tamano
from screens import estilo, foto
from screens.paneles import partir_lineas

COLOR_FALSO = (245, 130, 120)
COLOR_VERDAD = (96, 210, 130)
COLOR_PAPEL = foto.COLOR_PAPEL
COLOR_TINTA = foto.COLOR_TINTA
COLOR_TINTA_TENUE = (110, 112, 128)
MAX_RENGLONES = 2


def _es_del_equipo(nodo):
    return str(nodo).startswith("jugador_")


def fotos_del_equipo(red):
    """[{pub, origen, quien, verdad, recortada}] de lo que el equipo subió con
    foto, del primero al último."""
    if red is None:
        return []
    salida = []
    for pub in getattr(red, "publicaciones", ()):
        if pub.tipo not in ("desmentido", "confirmacion") or not _es_del_equipo(pub.autor):
            continue
        origen = getattr(pub, "desmiente", None)
        if origen is None:
            continue
        salida.append({"pub": pub, "origen": origen, "quien": red.usuario(pub.autor),
                       "verdad": pub.tipo == "confirmacion",
                       "recortada": not getattr(pub, "con_ubicacion", True)})
    return salida


def _fuentes(alto):
    return (fuente_de_tamano(max(11, min(16, alto // 52))),      # fc: "Decían...", quién
            fuente_de_tamano(max(12, min(18, alto // 46))),      # fm: lo que mostraba la foto
            fuente_de_tamano(max(13, min(20, alto // 40))))      # f: el subtítulo


def _zona(ancho, alto):
    """(arriba, abajo) de donde van las polaroids."""
    tam = max(28, min(60, alto // 13))
    arriba = int(alto * 0.08) + tam // 2 + 22 + _fuentes(alto)[2].get_linesize() + 14
    abajo = alto - max(22, alto // 24) - 30
    return arriba, abajo


def distribucion(ancho, alto):
    """(columnas, ancho de cada polaroid): que quepan dos filas a la vista."""
    fc, fm, _ = _fuentes(alto)
    columnas = 3 if ancho >= 1100 else 2 if ancho >= 640 else 1
    hueco = max(16, ancho // 50)
    arriba, abajo = _zona(ancho, alto)
    ancho_p = min(340, (ancho - 60 - (columnas - 1) * hueco) // columnas)
    while ancho_p > 160 and 2 * alto_polaroid(ancho_p, fc, fm) + hueco > abajo - arriba:
        ancho_p -= 8
    # Más chicas: a lo mejor cabe otra columna.
    while columnas < 4 and (columnas + 1) * ancho_p + columnas * hueco <= ancho - 60:
        columnas += 1
    return columnas, ancho_p


def columnas_para(tam):
    """Cuántas columnas tiene el álbum en una pantalla de `tam` (ancho, alto)."""
    return distribucion(*tam)[0]


def mover(seleccion, tecla, total, columnas):
    """La foto escogida después de una flecha (W/A/S/D también)."""
    if total <= 0:
        return 0
    if tecla in (pygame.K_LEFT, pygame.K_a):
        return max(0, seleccion - 1)
    if tecla in (pygame.K_RIGHT, pygame.K_d):
        return min(total - 1, seleccion + 1)
    if tecla in (pygame.K_UP, pygame.K_w):
        return seleccion - columnas if seleccion - columnas >= 0 else seleccion
    if tecla in (pygame.K_DOWN, pygame.K_s):
        if seleccion + columnas < total:
            return seleccion + columnas
        if seleccion // columnas < (total - 1) // columnas:
            return total - 1            # (la última fila está incompleta)
        return seleccion
    return seleccion


def _renglones(texto, f, ancho, maximo=MAX_RENGLONES):
    lineas = partir_lineas(texto, f, ancho)
    if len(lineas) > maximo:
        lineas = lineas[:maximo]
        while lineas[-1] and f.size(lineas[-1] + "...")[0] > ancho:
            lineas[-1] = lineas[-1][:-1]
        lineas[-1] = lineas[-1].rstrip() + "..."
    return lineas


def _polaroid(screen, rect, entrada, red, fc, fm, elegida):
    """Una foto del álbum en `rect` (el papel con la foto y lo de abajo)."""
    sombra = pygame.Surface(rect.size, pygame.SRCALPHA)
    sombra.fill((0, 0, 0, 90))
    screen.blit(sombra, rect.move(5, 7))
    pygame.draw.rect(screen, COLOR_PAPEL, rect, border_radius=4)
    borde = max(8, rect.w // 26)
    ancho_foto = rect.w - 2 * borde
    tam = (ancho_foto, ancho_foto * 3 // 4)
    img = foto.de_publicacion(entrada["pub"], red, tam)
    hueco = pygame.Rect(rect.x + borde, rect.y + borde, *tam)
    if img is not None:
        screen.blit(img, hueco)
    else:
        pygame.draw.rect(screen, (200, 205, 215), hueco)
    pygame.draw.rect(screen, (190, 186, 175), hueco, 1)
    # Sello: falso o verdad, en una esquina de la foto.
    verdad = entrada["verdad"]
    sello = "ERA VERDAD" if verdad else "ERA FALSO"
    color = COLOR_VERDAD if verdad else COLOR_FALSO
    img_sello = fm.render(sello, True, (255, 255, 255))
    caja = img_sello.get_rect().inflate(14, 6)
    caja.topright = (hueco.right - 6, hueco.y + 6)
    pygame.draw.rect(screen, color, caja, border_radius=caja.h // 2)
    screen.blit(img_sello, img_sello.get_rect(center=caja.center))
    if entrada["recortada"]:
        img_r = fc.render("recortada", True, (255, 255, 255))
        caja_r = img_r.get_rect().inflate(12, 4)
        caja_r.bottomleft = (hueco.x + 6, hueco.bottom - 6)
        pygame.draw.rect(screen, (60, 70, 100), caja_r, border_radius=caja_r.h // 2)
        screen.blit(img_r, img_r.get_rect(center=caja_r.center))
    # Debajo: lo que mostraba la foto, lo que decían y quién la subió.
    x, y, ancho = hueco.x, hueco.bottom + 6, hueco.w
    origen = entrada["origen"]
    mostraba = getattr(entrada["pub"], "foto", None) or (origen.rumor or {}).get("foto", "")
    for renglon in _renglones(mostraba, fm, ancho):
        screen.blit(fm.render(renglon, True, COLOR_TINTA), (x, y))
        y += fm.get_linesize()
    y += 2
    decian = f"Decían: \"{origen.texto}\""
    for renglon in _renglones(decian, fc, ancho):
        screen.blit(fc.render(renglon, True, COLOR_TINTA_TENUE), (x, y))
        y += fc.get_linesize()
    y += 2
    accion = "Lo confirmó" if verdad else "Lo desmintió"
    linea = fc.render(f"{accion} {entrada['quien']}", True, color)
    screen.blit(linea, (x, y))
    if elegida:
        pygame.draw.rect(screen, (255, 214, 64), rect.inflate(6, 6), 3, border_radius=6)


def alto_polaroid(ancho, fc, fm):
    borde = max(8, ancho // 26)
    alto_foto = (ancho - 2 * borde) * 3 // 4
    return (borde + alto_foto + 6 + MAX_RENGLONES * fm.get_linesize() + 2
            + MAX_RENGLONES * fc.get_linesize() + 2 + fc.get_linesize() + borde)


def render_album(screen, red, seleccion=0):
    """El álbum. Devuelve [(índice, rect)] de las polaroids que se ven."""
    ancho, alto = screen.get_size()
    estilo.fondo(screen)
    tam = max(28, min(60, alto // 13))
    rect_titulo = estilo.titulo(screen, "ÁLBUM DE FOTOS", (ancho // 2, int(alto * 0.08)), tam)
    entradas = fotos_del_equipo(red)
    fc, fm, f = _fuentes(alto)
    n = len(entradas)
    falsos = sum(1 for e in entradas if not e["verdad"])
    sub = (f"{n} {'foto' if n == 1 else 'fotos'} que subió el equipo · "
           f"{falsos} {'rumor desmentido' if falsos == 1 else 'rumores desmentidos'} · "
           f"{n - falsos} {'noticia confirmada' if n - falsos == 1 else 'noticias confirmadas'}")
    estilo.texto(screen, sub, f, (ancho // 2, rect_titulo.bottom + 16), estilo.COLOR_TENUE, "midtop")
    y0, abajo = _zona(ancho, alto)
    y0 = max(y0, rect_titulo.bottom + 16 + f.get_linesize() + 14)
    rects = []
    pie_y = alto - max(22, alto // 24)
    if not entradas:
        estilo.texto(screen, "El equipo no subió fotos en esta partida.", f, (ancho // 2, alto // 2),
                     estilo.COLOR_TEXTO, "center")
    else:
        columnas, ancho_p = distribucion(ancho, alto)
        hueco = max(16, ancho // 50)
        alto_p = alto_polaroid(ancho_p, fc, fm)
        filas_visibles = max(1, (abajo - y0 + hueco) // (alto_p + hueco))
        seleccion = max(0, min(n - 1, seleccion))
        fila_sel = seleccion // columnas
        primera = max(0, fila_sel - filas_visibles + 1)
        filas = (n + columnas - 1) // columnas
        alto_usado = min(filas - primera, filas_visibles) * (alto_p + hueco) - hueco
        y_inicio = y0 + max(0, (abajo - y0 - alto_usado) // 2)
        x0 = ancho // 2 - (columnas * ancho_p + (columnas - 1) * hueco) // 2
        for i, entrada in enumerate(entradas):
            fila, col = divmod(i, columnas)
            if fila < primera or fila >= primera + filas_visibles:
                continue
            rect = pygame.Rect(x0 + col * (ancho_p + hueco),
                               y_inicio + (fila - primera) * (alto_p + hueco), ancho_p, alto_p)
            _polaroid(screen, rect, entrada, red, fc, fm, i == seleccion)
            rects.append((i, rect))
        if primera > 0:
            estilo.texto(screen, f"{primera * columnas} más arriba", fc, (ancho // 2, y0 - fc.get_linesize() - 2),
                         estilo.COLOR_TENUE, "midtop")
        if primera + filas_visibles < filas:
            estilo.texto(screen, f"{n - (primera + filas_visibles) * columnas} más abajo", fc,
                         (ancho // 2, abajo + 6), estilo.COLOR_TENUE, "midtop")
    estilo.pie(screen, "[FLECHAS] mover  [ESC] volver a los resultados", pie_y)
    return rects
