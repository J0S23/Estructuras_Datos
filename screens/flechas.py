"""Las flechas que guían al jugador: la amarilla (lo que toca hacer en la
misión), la azul (el lugar del rumor que va a verificar en NEXUS) y la roja
(la caja de fusibles que hay que encender en un apagón, eventos.py).

Van alrededor del propio jugador, apuntando hacia el objetivo, y no en el
borde de su vista: en el borde las tapaban el HUD, el celular, el pulso o el
inventario. Cuando el objetivo ya se ve en pantalla, se marca ahí mismo
(mision_dibujo.py y celular.py) y la flecha no sale, salvo que quede en
la franja del borde, donde lo tapa el HUD (`cerca_del_borde`).

Además (nov 12), cada una marca en el piso el CAMINO hasta su objetivo
(`dibujar_camino`): puntos de su color que avanzan hacia allá, rodeando
paredes con el A* de juego/navegacion.py (el de los aliens y prisioneros), y
la flecha apunta hacia el primer tramo de ese camino, no en línea recta a
través de la pared. Sin mundo (o sin camino posible), la flecha de antes.

Pueden salir dos a la vez (la roja con la amarilla o la azul). Para que no
se monten, cada vista llama `empezar()` antes de dibujar las suyas: si una
flecha cae casi en la misma dirección que otra ya dibujada, se corre un poco
de lado (SEPARACION), y si su texto choca con otro, se aleja del jugador.
"""

import math

import pygame

from juego import navegacion
from juego.fuentes import fuente_de_tamano

RADIO = 74           # del centro del cuerpo del jugador a la flecha
ALTO_CUERPO = 26     # el centro del cuerpo queda arriba de la hitbox (los pies)
COLOR_SOMBRA = (12, 11, 23)
SEPARACION = math.radians(30)   # ángulo mínimo entre dos flechas del mismo jugador

# El camino: se busca con el tamaño de los prisioneros (su navegación ya está
# armada desde que carga la partida) y se vuelve a buscar solo si cambia el
# objetivo, si el jugador se sale RECALCULAR_PX del tramo que va siguiendo o
# cada RECALCULAR_MS. Mientras lo sigue, se recortan los puntos ya pasados
# (así caminando por el camino no se busca de nuevo cada paso).
ANCHO_GUIA, ALTO_GUIA = 34, 20
RECALCULAR_PX = 48
RECALCULAR_MS = 4000
CAMBIO_DESTINO_PX = 64   # menos que esto, sigue con el camino que tenía
ENTRE_PUNTOS = 22    # px del mundo entre los puntos del camino
VELOCIDAD_PUNTOS = 0.05   # px por ms que avanzan hacia el objetivo
DESDE_PIES = 28      # los primeros px (debajo del jugador) no se pintan
SEPARAR_CAMINOS = 7  # px de lado entre dos caminos de la misma vista
MIRAR_ADELANTE = 120     # la flecha apunta a este punto del camino (px por el camino)
CUERPO = (56, 96)    # ancho y alto del dibujo del jugador: ahí no se pintan puntos

_angulos = []    # las flechas ya dibujadas en esta vista
_textos = []     # y sus textos (Rect en pantalla)
_mundo = [None]  # el mundo de esta vista (para buscar los caminos)
_caminos = [0]   # cuántos caminos se dibujaron ya en esta vista
_rutas = {}      # (id del jugador, color) -> {"destino", "desde", "ms", "puntos"}


def empezar(mundo=None):
    """Al empezar a dibujar las flechas de una vista (`mundo`: para que
    sigan el camino; sin él, en línea recta como antes)."""
    _angulos.clear()
    _textos.clear()
    _mundo[0] = mundo
    _caminos[0] = 0


def _nav():
    mundo = _mundo[0]
    if mundo is None or not hasattr(mundo, "paredes_base"):
        return None
    return navegacion.de_mundo(mundo, ANCHO_GUIA, ALTO_GUIA)


def ruta(dueño, destino, color, tiempo_ms):
    """Los puntos del mundo del camino del jugador a `destino`, empezando
    donde está él; None si no hay mundo o no se encontró camino."""
    nav = _nav()
    if nav is None:
        return None
    pie = dueño.hitbox.center
    destino = (int(destino[0]), int(destino[1]))
    clave = (id(dueño), color)
    r = _rutas.get(clave)
    if r is None or r.get("mundo") is not _mundo[0]:
        r = _rutas[clave] = {"destino": destino, "desde": None, "ms": -10 ** 9, "puntos": None,
                             "mundo": _mundo[0]}
    elif math.dist(r["destino"], destino) > CAMBIO_DESTINO_PX:
        # Otro objetivo (o el mismo que se movió: el Guardia, un prisionero):
        # se busca de nuevo; mientras, si estaba cerca, el camino de antes.
        cerca = math.dist(r["destino"], destino) < 300
        r.update(destino=destino, desde=None, puntos=r["puntos"] if cerca else None)
    destino = r["destino"]
    puntos = r["puntos"]
    viejo = r["desde"] is None or tiempo_ms - r["ms"] > RECALCULAR_MS or tiempo_ms < r["ms"] \
        or (puntos and _distancia_a_tramo(pie, r["previo"], puntos[0]) > RECALCULAR_PX) \
        or (not puntos and math.dist(r["desde"], pie) > RECALCULAR_PX)
    if viejo:
        nuevo = nav.camino(pie, destino, parcial=True, sellos=False, por_partes=True,
                           quien=("guia",) + clave)
        if nuevo is not None:
            r.update(desde=pie, previo=pie, ms=tiempo_ms, puntos=nuevo)
        elif not nav.ocupada:
            r.update(desde=pie, previo=pie, ms=tiempo_ms, puntos=None)    # no se llega
        # (si sigue buscando, mientras tanto el camino de antes)
    puntos = r["puntos"]
    if not puntos:
        return None
    # Lo que ya caminó: fuera los puntos a los que ya llegó o desde donde ya
    # se ve de frente el siguiente.
    while len(puntos) > 1 and math.dist(puntos[0], pie) < 20:
        r["previo"] = puntos.pop(0)
    if len(puntos) > 1 and nav.libre_entre(pie, puntos[1]):    # (una por cuadro)
        puntos.pop(0)
        r["previo"] = pie
    return [pie] + puntos


def punto_a(camino, distancia):
    """El punto que queda a `distancia` px por el camino desde su inicio."""
    for (ax, ay), (bx, by) in zip(camino, camino[1:]):
        largo = math.hypot(bx - ax, by - ay)
        if largo >= distancia and largo > 0:
            t = distancia / largo
            return ax + (bx - ax) * t, ay + (by - ay) * t
        distancia -= largo
    return camino[-1]


def _distancia_a_tramo(p, a, b):
    """Distancia del punto `p` al segmento a-b."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    largo = dx * dx + dy * dy
    t = 0 if largo == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / largo))
    return math.dist(p, (a[0] + dx * t, a[1] + dy * t))


def dibujar_camino(screen, vista, camara, dueño, destino, color, tiempo_ms):
    """Puntos de `color` en el piso, del jugador a `destino` por donde se
    puede caminar, avanzando hacia allá. Devuelve el camino (o None)."""
    puntos = ruta(dueño, destino, color, tiempo_ms)
    if puntos is None or len(puntos) < 2:
        return puntos
    # Encima del dibujo del jugador no van puntos (si el camino sale hacia
    # arriba, lo cruzaban por el cuerpo).
    hb = dueño.hitbox
    cuerpo = pygame.Rect(0, 0, *CUERPO)
    cuerpo.midbottom = (hb.centerx - camara.x + vista.x, hb.bottom + 4 - camara.y + vista.y)
    lado = SEPARAR_CAMINOS * _caminos[0]
    _caminos[0] += 1
    ox, oy = vista.x - camara.x, vista.y - camara.y
    visible = vista.inflate(20, 20)
    fase = (tiempo_ms * VELOCIDAD_PUNTOS) % ENTRE_PUNTOS
    recorrido = 0.0               # px desde el jugador hasta el inicio del tramo
    siguiente = DESDE_PIES + fase  # dónde va el próximo punto
    total = sum(math.dist(a, b) for a, b in zip(puntos, puntos[1:]))
    for (ax, ay), (bx, by) in zip(puntos, puntos[1:]):
        largo = math.hypot(bx - ax, by - ay)
        if largo < 1:
            continue
        ux, uy = (bx - ax) / largo, (by - ay) / largo
        nx, ny = -uy * lado, ux * lado
        while siguiente <= recorrido + largo:
            t = siguiente - recorrido
            px, py = int(ax + ux * t + nx + ox), int(ay + uy * t + ny + oy)
            if visible.collidepoint(px, py) and not cuerpo.collidepoint(px, py):
                # Más grande cerca del objetivo: se ve hacia dónde va.
                radio = 3 if total - siguiente > 60 else 5
                pygame.draw.circle(screen, COLOR_SOMBRA, (px, py), radio + 2)
                pygame.draw.circle(screen, color, (px, py), radio)
            siguiente += ENTRE_PUNTOS
        recorrido += largo
    return puntos


def _apartar(angulo):
    """Corre `angulo` lo justo para que no quede encima de otra flecha."""
    for _ in range(4):
        cerca = None
        for otro in _angulos:
            d = (angulo - otro + math.pi) % (2 * math.pi) - math.pi
            if abs(d) < SEPARACION:
                cerca = (otro, d)
                break
        if cerca is None:
            break
        otro, d = cerca
        angulo = otro + (SEPARACION if d >= 0 else -SEPARACION)
    return angulo


def cerca_del_borde(vista, punto):
    """¿`punto` (en pantalla) cae en la franja del borde de la vista? Ahí van
    el HUD, la barra de confianza, el pulso y el inventario, y un objetivo que
    está en pantalla pero ahí se pierde: también lleva flecha."""
    adentro = pygame.Rect(vista.x + 110, vista.y + 110, vista.width - 220, vista.height - 220)
    return not adentro.collidepoint(punto)


def flecha_alrededor(screen, vista, camara, dueño, destino, color, texto=None, tiempo_ms=0):
    """Flecha de `color` a RADIO px del jugador, apuntando a `destino` (x, y
    del mundo), con `texto` un poco más afuera."""
    x, y = dueño.hitbox.centerx, dueño.hitbox.centery - ALTO_CUERPO
    cx, cy = x - camara.x + vista.x, y - camara.y + vista.y
    # Hacia donde va el camino (si lo hay), no derecho por la pared: un punto
    # MIRAR_ADELANTE px más allá por el camino (el primer tramo puede ser de
    # unos pocos px y apuntar a cualquier lado).
    camino = ruta(dueño, destino, color, tiempo_ms)
    if camino and len(camino) > 1:
        hacia = punto_a(camino, MIRAR_ADELANTE)
        dx, dy = hacia[0] - camino[0][0], hacia[1] - camino[0][1]
    else:
        dx, dy = destino[0] - x, destino[1] - y
    distancia = math.hypot(dx, dy) or 1
    angulo = _apartar(math.atan2(dy / distancia, dx / distancia))
    _angulos.append(angulo)
    ux, uy = math.cos(angulo), math.sin(angulo)
    radio = RADIO + 3 * math.sin(tiempo_ms / 220)          # late un poquito: se nota más
    px, py = cx + ux * radio, cy + uy * radio
    tam = 15
    punta = (px + math.cos(angulo) * tam, py + math.sin(angulo) * tam)
    izq = (px + math.cos(angulo + 2.5) * tam, py + math.sin(angulo + 2.5) * tam)
    der = (px + math.cos(angulo - 2.5) * tam, py + math.sin(angulo - 2.5) * tam)
    pygame.draw.polygon(screen, color, [punta, izq, der])
    pygame.draw.polygon(screen, COLOR_SOMBRA, [punta, izq, der], 2)
    if not texto:
        return
    img = fuente_de_tamano(14).render(texto, True, color)
    fondo = pygame.Surface((img.get_width() + 10, img.get_height() + 4), pygame.SRCALPHA)
    fondo.fill((14, 15, 28, 180))
    # Más afuera que la flecha, del mismo lado; si apunta de lado, el texto se
    # corre hacia afuera para no quedar encima del jugador.
    r = fondo.get_rect(center=(px + ux * (32 + fondo.get_width() / 2 * abs(ux)),
                               py + uy * (22 + fondo.get_height() / 2 * abs(uy))))
    r.clamp_ip(vista.inflate(-8, -8))
    for _ in range(5):                       # que no tape el texto de otra flecha
        if r.collidelist(_textos) < 0:
            break
        r.move_ip(round(ux * 22), round(uy * 22) or 22)
        r.clamp_ip(vista.inflate(-8, -8))
    _textos.append(r)
    screen.blit(fondo, r)
    screen.blit(img, img.get_rect(center=r.center))
