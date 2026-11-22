"""El tutorial del principio, dibujado (la lógica está en juego/tutorial.py).

Diego, nov 21: "haz el tutorial del inicio mucho más atractivo e interactivo".

- `render(screen, vista, jugador, tutorial)`: la tarjeta de cada jugador,
  abajo al centro (entre el pulso y el inventario; encima del pulso si no
  cabe). Arriba "ENTRENAMIENTO", la barra de pasos (uno por segmento: los
  hechos en verde, el de ahora late) y cuántos están listos; al medio el
  dibujo del paso, el título y lo que hay que hacer; abajo las teclas
  dibujadas como teclas (las de moverse se prenden al caminar), la barra del
  sigilo y "[tecla] saltar". Las de leer traen tres puntos con su dibujito.
  Al cambiar de paso la tarjeta entra deslizándose; al completar uno
  haciéndolo, "¡Bien!" sube encima y salta un destello verde en el jugador.
  Anota su borde de arriba en `jugador.hud_tutorial` (paneles.tope_abajo:
  la pista "[E] ..." y la barra de progreso van encima).
- `dibujar_objetivo(screen, vista, camara, dueño, tutorial, tiempo_ms)`: el
  casillero o la nota del paso: el camino de puntos, un aro que late en el
  piso, una flecha que rebota encima con el letrero y, si está fuera de la
  pantalla, la flecha alrededor del jugador (screens/flechas.py).

Todo sale del estado del tutorial (`hechos`, `paso`), así en red cada cliente
lo anima igual. Sin "Efectos visuales", la tarjeta no se desliza ni hay
destello (el resto igual).
"""

import math

import pygame

from juego import cache_dibujo, efectos
from juego.fuentes import fuente_de_tamano
from juego.tutorial import PASOS, con_teclas

COLOR = (90, 220, 230)          # el cian del tutorial
COLOR_HECHO = (96, 220, 130)
COLOR_TEXTO = (240, 242, 255)
COLOR_TENUE = (150, 156, 190)
COLOR_TECLA = (46, 50, 86)
COLOR_TECLA_BORDE = (120, 132, 190)
COLOR_ICONO = {"mover": (90, 220, 230), "sigilo": (120, 170, 255), "casillero": (150, 200, 120),
               "nota": (245, 214, 120), "celular": (230, 120, 220), "arbol": (255, 196, 90),
               "peligro": (255, 120, 100), "capsula": (120, 220, 255)}
COLOR_PUNTO = {"cambiaformas": (190, 140, 255), "apagon": (255, 214, 90), "celda": (255, 120, 100),
               "puerta": (90, 220, 230), "prisionero": (150, 220, 140), "capsula": (120, 220, 255)}
DESLIZAR_MS = 280
BIEN_MS = 1100

_vistos = {}            # id(jugador) -> {"paso", "desde", "hechos", "bien"}
_renglones = {}


def olvidar():
    _vistos.clear()


def _ahora():
    return pygame.time.get_ticks()


def _mezclar(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def _partir(texto, f, ancho):
    from juego.idioma import tr
    clave = (texto, f.get_height(), ancho)
    lineas = _renglones.get(clave)
    if lineas is None:
        if len(_renglones) > 400:
            _renglones.clear()
        lineas, actual = [], ""
        for palabra in tr(texto).split():
            prueba = f"{actual} {palabra}".strip()
            if f.size(prueba)[0] <= ancho or not actual:
                actual = prueba
            else:
                lineas.append(actual)
                actual = palabra
        if actual:
            lineas.append(actual)
        _renglones[clave] = lineas
    return lineas


def _fuentes(vista):
    chica = vista.height < 500
    return (fuente_de_tamano(18 if chica else 21),     # título
            fuente_de_tamano(14 if chica else 16),     # texto
            fuente_de_tamano(12 if chica else 13))     # lo chico


# -- Dibujitos ----------------------------------------------------------------------------------

def _flecha(screen, c, angulo, largo, color, grosor=3):
    x, y = c
    ux, uy = math.cos(angulo), math.sin(angulo)
    punta = (x + ux * largo, y + uy * largo)
    pygame.draw.line(screen, color, (x, y), punta, grosor)
    for d in (2.5, -2.5):
        pygame.draw.line(screen, color, punta,
                         (punta[0] + math.cos(angulo + d) * largo * 0.45,
                          punta[1] + math.sin(angulo + d) * largo * 0.45), grosor)


def icono(screen, clave, centro, r, color, t=0):
    """El dibujo de un paso o de un punto, en un círculo de radio `r`."""
    cx, cy = centro
    oscuro = _mezclar(color, (10, 10, 20), 0.75)
    pygame.draw.circle(screen, oscuro, centro, r)
    pygame.draw.circle(screen, color, centro, r, 2)
    k = r / 26
    if clave == "mover":
        for i in range(4):
            a = i * math.pi / 2 + (math.sin(t / 300) * 0.0)
            ex = 4 * k * math.sin(t / 260 + i)
            _flecha(screen, (cx + math.cos(a) * 3 * k, cy + math.sin(a) * 3 * k), a, 13 * k + ex, color,
                    max(2, int(3 * k)))
    elif clave == "sigilo":
        # El anillo de ruido que se achica y el jugador en el medio.
        f = (t / 1400) % 1
        rr = int(r * (0.85 - 0.45 * f))
        pygame.draw.circle(screen, _mezclar(color, oscuro, f), centro, max(4, rr), 2)
        pygame.draw.circle(screen, color, centro, max(3, int(5 * k)))
    elif clave in ("casillero",):
        cuerpo = pygame.Rect(0, 0, int(22 * k), int(34 * k))
        cuerpo.center = centro
        pygame.draw.rect(screen, color, cuerpo, max(2, int(2 * k)), border_radius=3)
        for j in range(3):
            y = cuerpo.y + int((6 + j * 4) * k)
            pygame.draw.line(screen, color, (cuerpo.x + 5 * k, y), (cuerpo.right - 5 * k, y), 1)
        pygame.draw.rect(screen, color, (cuerpo.right - 7 * k, cuerpo.centery, 3 * k, 6 * k))
    elif clave == "nota":
        hoja = pygame.Rect(0, 0, int(26 * k), int(32 * k))
        hoja.center = centro
        pts = [hoja.topleft, (hoja.right - 8 * k, hoja.y), (hoja.right, hoja.y + 8 * k), hoja.bottomright,
               hoja.bottomleft]
        pygame.draw.polygon(screen, color, pts, max(2, int(2 * k)))
        for j in range(4):
            y = hoja.y + int((10 + j * 5) * k)
            pygame.draw.line(screen, color, (hoja.x + 5 * k, y), (hoja.right - (5 + (j % 2) * 6) * k, y), 2)
    elif clave == "celular":
        tel = pygame.Rect(0, 0, int(22 * k), int(36 * k))
        tel.center = centro
        pygame.draw.rect(screen, color, tel, max(2, int(2 * k)), border_radius=int(5 * k))
        pantalla = tel.inflate(-int(8 * k), -int(14 * k))
        brillo = 0.5 + 0.5 * math.sin(t / 300)
        pygame.draw.rect(screen, _mezclar(oscuro, color, 0.3 + 0.4 * brillo), pantalla, border_radius=2)
        pygame.draw.circle(screen, color, (tel.centerx, tel.bottom - int(4 * k)), max(1, int(2 * k)))
    elif clave == "arbol":
        a = (cx, cy - 11 * k)
        b, c = (cx - 11 * k, cy + 10 * k), (cx + 11 * k, cy + 10 * k)
        for p in (b, c):
            pygame.draw.line(screen, color, a, p, 2)
        for i, p in enumerate((a, b, c)):
            lleno = (int(t / 500) % 3) == i
            pygame.draw.circle(screen, color, (int(p[0]), int(p[1])), int(6 * k), 0 if lleno else 2)
    elif clave == "peligro":
        pts = [(cx, cy - 15 * k), (cx + 16 * k, cy + 12 * k), (cx - 16 * k, cy + 12 * k)]
        pygame.draw.polygon(screen, color, pts, max(2, int(3 * k)))
        pygame.draw.line(screen, color, (cx, cy - 5 * k), (cx, cy + 3 * k), max(2, int(3 * k)))
        pygame.draw.circle(screen, color, (cx, int(cy + 8 * k)), max(1, int(2 * k)))
    elif clave == "capsula":
        cuerpo = pygame.Rect(0, 0, int(16 * k), int(28 * k))
        cuerpo.center = (cx, cy - 2 * k)
        pygame.draw.ellipse(screen, color, cuerpo, max(2, int(2 * k)))
        pygame.draw.circle(screen, color, (cx, int(cy - 6 * k)), max(2, int(4 * k)), 2)
        fuego = 5 * k + 3 * k * math.sin(t / 90)
        pygame.draw.polygon(screen, (255, 170, 80), [(cx - 5 * k, cuerpo.bottom - 2), (cx + 5 * k, cuerpo.bottom - 2),
                                                      (cx, cuerpo.bottom + fuego)])
    elif clave == "cambiaformas":
        pygame.draw.circle(screen, color, centro, int(12 * k), 2)
        pygame.draw.circle(screen, color, (int(cx - 5 * k), int(cy - 2 * k)), max(1, int(2 * k)))
        corrido = int(3 * k * math.sin(t / 120))
        pygame.draw.circle(screen, color, (int(cx + 5 * k + corrido), int(cy - 2 * k)), max(1, int(2 * k)))
        pygame.draw.line(screen, color, (cx - 14 * k, cy + 3 * k), (cx + 14 * k, cy + 1 * k), 2)
    elif clave == "apagon":
        pygame.draw.circle(screen, color, (cx, int(cy - 3 * k)), int(10 * k), 2)
        pygame.draw.rect(screen, color, (cx - 5 * k, cy + 7 * k, 10 * k, 6 * k), 2)
    elif clave == "celda":
        marco = pygame.Rect(0, 0, int(26 * k), int(26 * k))
        marco.center = centro
        pygame.draw.rect(screen, color, marco, 2)
        for j in range(1, 4):
            x = marco.x + marco.w * j // 4
            pygame.draw.line(screen, color, (x, marco.y), (x, marco.bottom), 2)
    elif clave == "puerta":
        marco = pygame.Rect(0, 0, int(20 * k), int(30 * k))
        marco.center = centro
        pygame.draw.rect(screen, color, marco, 2, border_radius=2)
        for i in range(3):
            for j in range(2):
                pygame.draw.circle(screen, color, (int(marco.x + (6 + j * 8) * k), int(marco.y + (8 + i * 6) * k)), 1)
    elif clave == "prisionero":
        pygame.draw.circle(screen, color, (cx, int(cy - 7 * k)), int(6 * k), 2)
        pygame.draw.arc(screen, color, (cx - 11 * k, cy, 22 * k, 22 * k), 0, math.pi, 2)


def _tecla(screen, texto, x, centro_y, f, encendida=False, pulso=0.0):
    """Una tecla con `texto`; devuelve su ancho."""
    img = cache_dibujo.texto(f, texto, COLOR_TEXTO)
    w = max(img.get_width() + 14, f.get_height() + 8)
    alto = f.get_height() + 6
    caja = pygame.Rect(x, centro_y - alto // 2, w, alto)
    abajo = 2 if encendida else 0
    pygame.draw.rect(screen, (14, 14, 30), caja.move(0, 2), border_radius=6)
    caja.move_ip(0, abajo)
    fondo = _mezclar(COLOR_TECLA, COLOR, 0.45 if encendida else 0.18 * pulso)
    borde = COLOR if encendida or pulso > 0.5 else COLOR_TECLA_BORDE
    pygame.draw.rect(screen, fondo, caja, border_radius=6)
    pygame.draw.rect(screen, borde, caja, 1 + (encendida or pulso > 0.5), border_radius=6)
    screen.blit(img, img.get_rect(center=caja.center))
    return w


def _triangulo(screen, c, angulo, tam, color):
    x, y = c
    pts = [(x + math.cos(angulo) * tam, y + math.sin(angulo) * tam),
           (x + math.cos(angulo + 2.4) * tam, y + math.sin(angulo + 2.4) * tam),
           (x + math.cos(angulo - 2.4) * tam, y + math.sin(angulo - 2.4) * tam)]
    pygame.draw.polygon(screen, color, pts)


def _cruceta(screen, x, centro_y, f, jugador, t):
    """Las de moverse: W/A/S/D o las flechas en cruz (se prenden las que
    camina), o el stick del mando. Devuelve el ancho."""
    p = jugador.personaje
    direc = p.direccion if p.moviendose else ""
    prendidas = {"arriba": "north" in direc, "abajo": "south" in direc,
                 "izq": "west" in direc, "der": "east" in direc}
    lado = f.get_height() + 6
    esquema = getattr(jugador, "esquema", jugador.puesto)
    if esquema not in (0, 1):
        # El stick: un círculo con la palanca que se va hacia donde camina.
        r = lado - 2
        c = (x + r, centro_y)
        pygame.draw.circle(screen, COLOR_TECLA, c, r)
        pygame.draw.circle(screen, COLOR if p.moviendose else COLOR_TECLA_BORDE, c, r, 2)
        dx = (1 if prendidas["der"] else -1 if prendidas["izq"] else 0)
        dy = (1 if prendidas["abajo"] else -1 if prendidas["arriba"] else 0)
        if not p.moviendose:
            a = t / 400
            dx, dy = math.cos(a) * 0.5, math.sin(a) * 0.5
        pygame.draw.circle(screen, COLOR if p.moviendose else COLOR_TECLA_BORDE,
                           (int(c[0] + dx * r * 0.5), int(c[1] + dy * r * 0.5)), max(4, r // 2))
        return 2 * r
    letras = {"arriba": "W", "izq": "A", "abajo": "S", "der": "D"} if esquema == 0 else None
    chica = lado - 2
    pasos = [("izq", 0, 1), ("abajo", 1, 1), ("der", 2, 1), ("arriba", 1, 0)]
    arriba_y = centro_y - chica - 1
    for clave, col, fila in pasos:
        caja = pygame.Rect(x + col * (chica + 3), arriba_y + fila * (chica + 2), chica, chica)
        on = prendidas[clave]
        # Sin caminar, la que toca late (para que se note que son teclas).
        demo = not p.moviendose and int(t / 380) % 4 == pasos.index((clave, col, fila))
        caja_dibujo = caja.move(0, 1 if on else 0)
        pygame.draw.rect(screen, (14, 14, 30), caja.move(0, 2), border_radius=4)
        pygame.draw.rect(screen, _mezclar(COLOR_TECLA, COLOR, 0.5 if on else 0.25 if demo else 0),
                         caja_dibujo, border_radius=4)
        pygame.draw.rect(screen, COLOR if on or demo else COLOR_TECLA_BORDE, caja_dibujo, 1, border_radius=4)
        if letras:
            img = cache_dibujo.texto(fuente_de_tamano(max(10, chica - 8)), letras[clave], COLOR_TEXTO)
            screen.blit(img, img.get_rect(center=caja_dibujo.center))
        else:
            angulo = {"arriba": -math.pi / 2, "abajo": math.pi / 2, "izq": math.pi, "der": 0}[clave]
            _triangulo(screen, caja_dibujo.center, angulo, chica * 0.28, COLOR_TEXTO)
    return 3 * chica + 6


# -- La tarjeta ---------------------------------------------------------------------------------

def _animacion(jugador, e, ahora):
    """(ms desde que cambió de paso, ms desde el último "¡Bien!" o None)."""
    clave = id(jugador)
    v = _vistos.get(clave)
    if v is None:
        v = _vistos[clave] = {"paso": e.get("paso"), "desde": -10 ** 6, "hechos": e.get("hechos", 0),
                              "bien": None, "listo": e.get("listo")}
    if v["paso"] != e.get("paso") or v["listo"] != e.get("listo"):
        v["paso"], v["listo"], v["desde"] = e.get("paso"), e.get("listo"), ahora
    if e.get("hechos", 0) > v["hechos"]:
        v["hechos"] = e.get("hechos", 0)
        v["bien"] = ahora
        hb = jugador.hitbox
        efectos.destello(hb.centerx, hb.centery - 40, COLOR_HECHO, cantidad=26, fuerza=1.1)
    bien = None if v["bien"] is None or ahora - v["bien"] > BIEN_MS else ahora - v["bien"]
    return ahora - v["desde"], bien


def _lugar(screen, vista, jugador, ancho_deseado, alto):
    """Dónde va la tarjeta: entre el pulso y el inventario, o encima del pulso."""
    from screens.paneles import rect_pulso, ancho_inventario
    pulso = rect_pulso(screen, vista, jugador)
    inventario = ancho_inventario(vista, jugador)
    libre = vista.right - 12 - (inventario + 12 if inventario else 0) - (pulso.right + 16)
    ancho = min(ancho_deseado, libre)
    if ancho < 300:
        ancho = min(ancho_deseado, vista.width - 32)
        caja = pygame.Rect(0, 0, ancho, alto)
        caja.midbottom = (vista.centerx, pulso.top - 8)
    else:
        caja = pygame.Rect(0, 0, ancho, alto)
        caja.bottomleft = (pulso.right + 16 + max(0, (libre - ancho) // 2), vista.bottom - 12)
    return caja


def render(screen, vista, jugador, tutorial):
    jugador.hud_tutorial = None
    if tutorial is None or not tutorial.activo or not getattr(jugador, "puede_moverse", True):
        return   # los puestos sin mando todavía no se mueven: no hay qué enseñarles
    e = tutorial._de(jugador)
    ahora = _ahora()
    desde, bien = _animacion(jugador, e, ahora)
    ft, f, fc = _fuentes(vista)
    hechos, necesarios = tutorial.listos()
    total = len(PASOS)
    paso_i = min(e["paso"], total - 1)
    listo = e["listo"]
    paso = PASOS[paso_i]
    ancho_deseado = 560 if vista.height >= 500 else 470
    # Medidas (con un ancho tentativo; si cambia, se vuelve a partir).
    from screens.paneles import rect_pulso, ancho_inventario
    pulso = rect_pulso(screen, vista, jugador)
    inventario = ancho_inventario(vista, jugador)
    libre = vista.right - 12 - (inventario + 12 if inventario else 0) - (pulso.right + 16)
    ancho = min(ancho_deseado, libre) if libre >= 300 else min(ancho_deseado, vista.width - 32)
    pad = 14
    d_icono = 50 if vista.height >= 500 else 40
    x_texto = pad + d_icono + 14
    ancho_texto = ancho - x_texto - pad
    lineas, puntos = [], []
    fp = fc if vista.height < 420 else f        # (los puntos de las de leer; con 4 jugadores, más chicos)
    if listo:
        titulo = "¡Listo!"
        lineas = _partir(f"Esperando a los demás ({hechos}/{necesarios} listos)... Mientras, "
                         "puedes caminar por aquí.", f, ancho_texto)
    else:
        titulo = paso["titulo"]
        if paso.get("puntos"):
            for clave, texto in paso["puntos"]:
                puntos.append((clave, _partir(con_teclas(texto, jugador), fp, ancho_texto - 30)))
        else:
            lineas = _partir(con_teclas(paso["texto"], jugador), f, ancho_texto)
    alto_cab = fc.get_linesize() + 12
    alto_cuerpo = ft.get_linesize() + 2
    alto_cuerpo += len(lineas) * f.get_linesize()
    for _, ls in puntos:
        alto_cuerpo += max(24, len(ls) * fp.get_linesize()) + 3
    alto_cuerpo = max(alto_cuerpo, d_icono)
    alto_pie = 0 if listo else f.get_height() + 18
    if not listo and "mover" in paso.get("teclas", ()):
        alto_pie = max(alto_pie, 2 * (f.get_height() + 4) + 14)      # (las teclas en cruz)
    alto = alto_cab + alto_cuerpo + alto_pie + pad + 4
    caja = _lugar(screen, vista, jugador, ancho_deseado, alto)
    # Entra deslizándose desde abajo al cambiar de paso.
    corrimiento = 0
    if efectos.ACTIVOS and desde < DESLIZAR_MS:
        k = desde / DESLIZAR_MS
        corrimiento = int((1 - (1 - (1 - k) ** 3)) * 26)
    caja = caja.move(0, corrimiento)

    color_borde = COLOR
    if bien is not None and bien < 450:
        color_borde = _mezclar(COLOR_HECHO, COLOR, bien / 450)
    if efectos.ACTIVOS:
        from screens import vidrio
        vidrio.caja(screen, caja, color_borde, 225, 10)
    else:
        screen.blit(cache_dibujo.capa(caja.size, (12, 14, 30, 225)), caja.topleft)
        pygame.draw.rect(screen, color_borde, caja, 2, border_radius=8)

    # Cabecera: ENTRENAMIENTO, la barra de pasos y cuántos están listos.
    y = caja.y + 8
    cab = cache_dibujo.texto(fc, "ENTRENAMIENTO", COLOR)
    screen.blit(cab, (caja.x + pad, y))
    listos_txt = cache_dibujo.texto(fc, f"listos {hechos}/{necesarios}",
                                    COLOR_HECHO if hechos else COLOR_TENUE)
    screen.blit(listos_txt, (caja.right - pad - listos_txt.get_width(), y))
    barra = pygame.Rect(caja.x + pad + cab.get_width() + 12, y + fc.get_height() // 2 - 3,
                        caja.w - 2 * pad - cab.get_width() - listos_txt.get_width() - 24, 6)
    if barra.w > total * 6:
        hueco = 3
        seg = (barra.w - hueco * (total - 1)) / total
        for i in range(total):
            r = pygame.Rect(int(barra.x + i * (seg + hueco)), barra.y, max(2, int(seg)), barra.h)
            if listo or i < paso_i:
                c = COLOR_HECHO
            elif i == paso_i:
                c = _mezclar(COLOR, (255, 255, 255), 0.25 + 0.25 * math.sin(ahora / 180))
            else:
                c = (52, 56, 90)
            pygame.draw.rect(screen, c, r, border_radius=3)
    y = caja.y + alto_cab

    # El dibujo del paso.
    centro_icono = (caja.x + pad + d_icono // 2, y + d_icono // 2)
    clave_icono = "capsula" if listo else paso["icono"]
    color_icono = COLOR_HECHO if listo else COLOR_ICONO.get(clave_icono, COLOR)
    if efectos.ACTIVOS:
        from screens import vidrio
        vidrio.brillo(screen, centro_icono, d_icono // 2 + 10, _mezclar(color_icono, (0, 0, 0), 0.55))
    icono(screen, clave_icono, centro_icono, d_icono // 2, color_icono, ahora)
    if bien is not None:
        # Una palomita grande que salta sobre el dibujo.
        k = min(1.0, bien / 180)
        escala = 1.0 + 0.4 * (1 - k) if bien < 180 else 1.0
        alfa = 1.0 if bien < BIEN_MS - 300 else max(0.0, (BIEN_MS - bien) / 300)
        if alfa > 0:
            r = int(d_icono * 0.26 * escala)
            c = (centro_icono[0] + int(d_icono * 0.3), centro_icono[1] + int(d_icono * 0.3))
            pygame.draw.circle(screen, COLOR_HECHO, c, r)
            pygame.draw.lines(screen, (14, 40, 20), False,
                              [(c[0] - r * 0.5, c[1]), (c[0] - r * 0.1, c[1] + r * 0.4),
                               (c[0] + r * 0.55, c[1] - r * 0.4)], max(2, r // 4))

    # Título y texto (o los puntos).
    x = caja.x + x_texto
    screen.blit(cache_dibujo.texto(ft, titulo, COLOR_HECHO if listo else COLOR_TEXTO), (x, y - 2))
    y += ft.get_linesize() + 2
    for linea in lineas:
        screen.blit(cache_dibujo.texto(f, linea, (214, 218, 240)), (x, y))
        y += f.get_linesize()
    for clave, ls in puntos:
        alto_p = max(24, len(ls) * fp.get_linesize())
        icono(screen, clave, (x + 11, y + 12), 11, COLOR_PUNTO.get(clave, COLOR), ahora)
        yy = y + (alto_p - len(ls) * fp.get_linesize()) // 2
        for linea in ls:
            screen.blit(cache_dibujo.texto(fp, linea, (214, 218, 240)), (x + 30, yy))
            yy += fp.get_linesize()
        y += alto_p + 3

    # Abajo: las teclas, la barra del sigilo y saltar/siguiente.
    if not listo:
        _pie(screen, caja, pad, f, fc, jugador, e, paso, paso_i == total - 1, ahora)

    # "¡Bien!" que sube encima de la tarjeta.
    if bien is not None:
        k = bien / BIEN_MS
        alfa = 255 if k < 0.7 else int(255 * (1 - (k - 0.7) / 0.3))
        img = cache_dibujo.texto(ft, "¡Bien!", COLOR_HECHO)
        fondo = pygame.Rect(0, 0, img.get_width() + 26, img.get_height() + 8)
        fondo.midbottom = (caja.centerx, caja.y - 6 - int(18 * min(1.0, k * 2)))
        capa = pygame.Surface(fondo.size, pygame.SRCALPHA)
        pygame.draw.rect(capa, (14, 40, 24, 220), capa.get_rect(), border_radius=fondo.h // 2)
        pygame.draw.rect(capa, (*COLOR_HECHO, 255), capa.get_rect(), 2, border_radius=fondo.h // 2)
        capa.blit(img, img.get_rect(center=capa.get_rect().center))
        if alfa < 255:
            capa.set_alpha(max(1, alfa))
        screen.blit(capa, fondo.topleft)

    jugador.hud_tutorial = (tuple(vista), caja.top - (40 if bien is not None else 0))


def _pie(screen, caja, pad, f, fc, jugador, e, paso, ultimo, ahora):
    y = caja.bottom - pad - (f.get_height() + 6) // 2 - 2
    if "mover" in paso.get("teclas", ()):
        y = caja.bottom - pad // 2 - (f.get_height() + 4) - 3      # (el centro entre las dos filas)
    x = caja.x + pad
    accion = paso["accion"]
    pulso = 0.5 + 0.5 * math.sin(ahora / 200)
    tecla_hab = jugador.nombre_tecla("habilidad")
    if accion == "leer":
        texto = "¡A jugar!" if ultimo else "siguiente"
        w = _tecla(screen, tecla_hab, x, y, f, pulso=pulso)
        img = cache_dibujo.texto(f, texto, COLOR)
        screen.blit(img, img.get_rect(midleft=(x + w + 8, y)))
        return
    # Lo que hay que presionar.
    for i, cual in enumerate(paso.get("teclas", ())):
        if i:
            mas = cache_dibujo.texto(f, "+", COLOR_TENUE)
            screen.blit(mas, mas.get_rect(midleft=(x + 2, y)))
            x += mas.get_width() + 6
        if cual == "mover":
            x += _cruceta(screen, x, y, f, jugador, ahora) + 8
        else:
            nombre = jugador.nombre_tecla(cual)
            if accion == "nota" and jugador.escondido:
                nombre = jugador.nombre_tecla("interactuar")
            encendida = (cual == "sigilo" and jugador.sigilo)
            x += _tecla(screen, nombre, x, y, f, encendida=encendida, pulso=pulso) + 8
    if accion == "sigilo":
        valor = min(1.0, e.get("sigilo_ms", 0) / 900)
        barra = pygame.Rect(x + 4, y - 4, max(40, min(140, caja.right - pad - x - 120)), 8)
        pygame.draw.rect(screen, (40, 44, 76), barra, border_radius=4)
        if valor > 0:
            pygame.draw.rect(screen, COLOR, (barra.x, barra.y, int(barra.w * valor), barra.h), border_radius=4)
        x = barra.right + 8
    else:
        img = cache_dibujo.texto(fc, "¡Hazlo!", COLOR)
        screen.blit(img, img.get_rect(midleft=(x + 2, y)))
    # Saltar (por si alguien se traba): chiquito a la derecha.
    img = cache_dibujo.texto(fc, f"[{tecla_hab}] saltar", COLOR_TENUE)
    screen.blit(img, img.get_rect(midright=(caja.right - pad, y)))


# -- En el mapa -------------------------------------------------------------------------------

_aros = {}


def _aro(rx, alfa):
    """Una elipse hueca del cian (el aro del piso), guardada."""
    clave = (rx, alfa)
    img = _aros.get(clave)
    if img is None:
        if len(_aros) > 200:
            _aros.clear()
        img = pygame.Surface((2 * rx + 4, rx + 4), pygame.SRCALPHA)
        pygame.draw.ellipse(img, (*COLOR, alfa), img.get_rect().inflate(-2, -2), 3)
        _aros[clave] = img
    return img


def dibujar_objetivo(screen, vista, camara, dueño, tutorial, tiempo_ms):
    """El casillero o la nota que toca (camino, aro, flecha y letrero).
    Devuelve True si dibujó algo (entonces no va la flecha amarilla)."""
    if tutorial is None or not tutorial.activo or getattr(dueño, "eliminado", False):
        return False
    if tutorial.esta_listo(dueño):
        return False
    objetivo = tutorial.objetivo(dueño)
    if objetivo is None:
        # Hasta terminar sus pasos, la flecha amarilla (el código, la puerta)
        # no sale: guía el tutorial.
        return True
    from screens.flechas import dibujar_camino, flecha_alrededor, cerca_del_borde
    (x, y), letrero, rect = objetivo
    dibujar_camino(screen, vista, camara, dueño, (x, y), COLOR, tiempo_ms)
    if camara.colliderect(rect.inflate(40, 40)):
        centro = (int(x - camara.x + vista.x), int(rect.bottom - camara.y + vista.y))
        # Aros en el piso que se abren.
        for k in range(2):
            fase = ((tiempo_ms / 900) + k * 0.5) % 1
            rx = int(30 + 34 * fase) // 2 * 2
            alfa = int(220 * (1 - fase)) // 16 * 16
            if alfa > 0:
                capa = _aro(rx, alfa)
                screen.blit(capa, capa.get_rect(center=centro))
        # La flecha que rebota encima, con el letrero.
        arriba = int(rect.top - camara.y + vista.y) - 70 - int(8 * abs(math.sin(tiempo_ms / 220)))
        punta = (centro[0], arriba + 22)
        pygame.draw.polygon(screen, (14, 15, 28), [(punta[0] - 15, punta[1] - 20), (punta[0] + 15, punta[1] - 20),
                                                   (punta[0], punta[1] + 2)])
        pygame.draw.polygon(screen, COLOR, [(punta[0] - 12, punta[1] - 18), (punta[0] + 12, punta[1] - 18),
                                            (punta[0], punta[1] - 1)])
        img = cache_dibujo.texto(fuente_de_tamano(15), letrero, COLOR)
        fondo = pygame.Rect(0, 0, img.get_width() + 16, img.get_height() + 6)
        fondo.midbottom = (punta[0], punta[1] - 22)
        fondo.clamp_ip(vista.inflate(-8, -8))
        screen.blit(cache_dibujo.capa(fondo.size, (14, 15, 28, 200)), fondo.topleft)
        pygame.draw.rect(screen, COLOR, fondo, 1, border_radius=6)
        screen.blit(img, img.get_rect(center=fondo.center))
        if not cerca_del_borde(vista, centro):
            return True
        # En el borde (ahí lo tapan el HUD o el cartel de Neila): la flecha
        # alrededor del jugador, con el letrero.
        flecha_alrededor(screen, vista, camara, dueño, (x, y), COLOR, letrero, tiempo_ms)
    else:
        flecha_alrededor(screen, vista, camara, dueño, (x, y), COLOR, letrero, tiempo_ms)
    return True
