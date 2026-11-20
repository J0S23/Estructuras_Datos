"""Dibujo de los logros: el aviso cuando se consigue uno y el árbol completo
(Pausa > Logros, Menú > Logros y "Ver logros" en los resultados).

El árbol se dibuja de izquierda a derecha como el de Minecraft: la raíz a la
izquierda, cada columna es un nivel de profundidad y las filas salen del
recorrido en postorden de ArbolLogros.posiciones().

Cada logro es una tarjeta (insignia con el ícono de su rama, nombre y estado)
y las conexiones son pistas de circuito que se prenden del color de la rama
cuando se consigue el hijo. Con 51 logros el árbol no cabe entero con
tarjetas legibles, así que la vista se desplaza: sigue al logro
seleccionado (teclado / mando) y la rueda del mouse la mueve (`rueda`).
Las tarjetas y las insignias se dibujan una vez y se guardan (`_tarjetas`,
`_insignias`); por cuadro solo se pegan las que se ven y se trazan las líneas.
"""

import math
import os
import random

import pygame

from data.logros import COLOR_RAMA
from juego import idioma
from juego.fuentes import fuente, fuente_de_tamano
from juego.idioma import tr

COLOR_FONDO_ARBOL = (12, 12, 26)
COLOR_FONDO_ABAJO = (22, 14, 40)
COLOR_LINEA = (90, 96, 130)
COLOR_OCULTO = (60, 62, 80)
COLOR_TEXTO = (240, 242, 252)
COLOR_TENUE = (150, 156, 190)
COLOR_SELECCION = (255, 214, 64)
COLOR_OK = (120, 230, 150)
COLOR_TARJETA = (24, 26, 46)
COLOR_TARJETA_OCULTA = (17, 18, 30)

NOMBRE_RAMA = {
    "inicio": "Inicio",
    "sigilo": "Sigilo",
    "escape": "Escape",
    "nexus": "NEXUS",
    "equipo": "Equipo",
    "nave": "La nave",
    "aliens": "Aliens",
    "cambiaformas": "Cambiaformas",
    "caso": "El caso",
}

SUPERMUESTREO = 3          # las insignias se dibujan 3 veces más grandes y se achican (bordes suaves)
SUAVIZADO_MS = 90          # qué tan rápido la vista alcanza su objetivo al desplazarse
# Las pruebas (sin ventana) sacan una captura por cuadro: ahí la vista salta
# directo a donde va en vez de deslizarse.
ANIMAR = os.environ.get("SDL_VIDEODRIVER") != "dummy"


def _escala(alto):
    """Cuánto crece el texto en pantallas altas (1 hasta 720 px, 1.4 en 1080)."""
    return max(1.0, min(1.5, 1 + (alto - 720) / 900))


def _color(nodo):
    return COLOR_RAMA.get(nodo.rama, COLOR_TEXTO)


def _oscuro(color, f=0.35):
    return tuple(int(c * f) for c in color)


def _mezclar(a, b, t):
    """a cuando t = 0, b cuando t = 1."""
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# -- Íconos de cada rama -------------------------------------------------------------------

def _puntos_arco(centro, radio, desde, hasta, pasos=18):
    cx, cy = centro
    return [(cx + radio * math.cos(desde + (hasta - desde) * i / pasos),
             cy - radio * math.sin(desde + (hasta - desde) * i / pasos)) for i in range(pasos + 1)]


def _dibujar_icono(sup, rama, centro, s, color, fondo):
    """El ícono de la rama, dentro de un cuadrado de lado `s` centrado en
    `centro`. `fondo` es el color de lo que queda "hueco" (ojos, ventanas)."""
    cx, cy = centro
    g = max(2, int(s * 0.09))          # grosor de las líneas
    if rama == "oculto":
        # Candado.
        cuerpo = pygame.Rect(0, 0, int(s * 0.56), int(s * 0.42))
        cuerpo.midtop = (cx, int(cy - s * 0.02))
        pygame.draw.lines(sup, color, False, _puntos_arco((cx, cuerpo.top), s * 0.19, 0, math.pi), g)
        pygame.draw.rect(sup, color, cuerpo, border_radius=max(2, int(s * 0.07)))
        pygame.draw.circle(sup, fondo, (cx, int(cuerpo.centery - s * 0.03)), max(2, int(s * 0.07)))
        pygame.draw.rect(sup, fondo, (cx - max(1, int(s * 0.03)), int(cuerpo.centery - s * 0.02),
                                      max(2, int(s * 0.06)), int(s * 0.14)))
    elif rama == "sigilo":
        # Un ojo entrecerrado.
        n = 20
        arriba = [(cx - s * 0.46 + s * 0.92 * i / n, cy - s * 0.26 * math.sin(math.pi * i / n)) for i in range(n + 1)]
        abajo = [(cx + s * 0.46 - s * 0.92 * i / n, cy + s * 0.26 * math.sin(math.pi * i / n)) for i in range(n + 1)]
        pygame.draw.polygon(sup, color, arriba + abajo)
        pygame.draw.circle(sup, fondo, (cx, cy), int(s * 0.17))
        pygame.draw.circle(sup, color, (cx, cy), int(s * 0.08))
        pygame.draw.lines(sup, color, False, [(cx - s * 0.5, cy - s * 0.36), (cx - s * 0.36, cy - s * 0.26)], g)
        pygame.draw.lines(sup, color, False, [(cx + s * 0.5, cy - s * 0.36), (cx + s * 0.36, cy - s * 0.26)], g)
    elif rama == "escape":
        # Un cohete.
        cuerpo = [(cx, cy - s * 0.47), (cx + s * 0.16, cy - s * 0.18), (cx + s * 0.16, cy + s * 0.24),
                  (cx - s * 0.16, cy + s * 0.24), (cx - s * 0.16, cy - s * 0.18)]
        pygame.draw.polygon(sup, color, [(cx - s * 0.16, cy + s * 0.0), (cx - s * 0.34, cy + s * 0.32),
                                         (cx - s * 0.16, cy + s * 0.24)])
        pygame.draw.polygon(sup, color, [(cx + s * 0.16, cy + s * 0.0), (cx + s * 0.34, cy + s * 0.32),
                                         (cx + s * 0.16, cy + s * 0.24)])
        pygame.draw.polygon(sup, color, cuerpo)
        pygame.draw.circle(sup, fondo, (cx, int(cy - s * 0.08)), max(2, int(s * 0.08)))
        pygame.draw.polygon(sup, color, [(cx - s * 0.1, cy + s * 0.3), (cx + s * 0.1, cy + s * 0.3),
                                         (cx, cy + s * 0.48)])
    elif rama == "nexus":
        # Señal: un punto y tres ondas.
        base = (cx, cy + s * 0.3)
        pygame.draw.circle(sup, color, (int(base[0]), int(base[1])), max(2, int(s * 0.08)))
        for r in (0.25, 0.43, 0.61):
            pygame.draw.lines(sup, color, False, _puntos_arco(base, s * r, math.pi * 0.25, math.pi * 0.75), g)
    elif rama == "equipo":
        # Dos personas.
        recorte = sup.get_clip()
        sup.set_clip(pygame.Rect(int(cx - s * 0.5), int(cy - s * 0.5), int(s), int(s * 0.9)))
        atras = _mezclar(color, fondo, 0.35)
        pygame.draw.circle(sup, atras, (int(cx + s * 0.15), int(cy - s * 0.17)), int(s * 0.13))
        pygame.draw.ellipse(sup, atras, (cx + s * 0.15 - s * 0.24, cy + s * 0.02, s * 0.48, s * 0.5))
        pygame.draw.circle(sup, fondo, (int(cx - s * 0.12), int(cy - s * 0.08)), int(s * 0.18))
        pygame.draw.ellipse(sup, fondo, (cx - s * 0.12 - s * 0.3, cy + s * 0.05, s * 0.6, s * 0.56))
        pygame.draw.circle(sup, color, (int(cx - s * 0.12), int(cy - s * 0.08)), int(s * 0.14))
        pygame.draw.ellipse(sup, color, (cx - s * 0.12 - s * 0.26, cy + s * 0.1, s * 0.52, s * 0.5))
        sup.set_clip(recorte)
    elif rama == "nave":
        # Un rayo.
        pygame.draw.polygon(sup, color, [(cx + s * 0.1, cy - s * 0.47), (cx - s * 0.24, cy + s * 0.06),
                                         (cx - s * 0.02, cy + s * 0.06), (cx - s * 0.12, cy + s * 0.47),
                                         (cx + s * 0.24, cy - s * 0.08), (cx + s * 0.02, cy - s * 0.08)])
    elif rama == "aliens":
        # Cabeza de alien con ojos rasgados.
        pygame.draw.ellipse(sup, color, (cx - s * 0.34, cy - s * 0.44, s * 0.68, s * 0.6))
        pygame.draw.polygon(sup, color, [(cx - s * 0.3, cy - s * 0.04), (cx + s * 0.3, cy - s * 0.04),
                                         (cx, cy + s * 0.46)])
        for lado in (-1, 1):
            pygame.draw.polygon(sup, fondo, [(cx + lado * s * 0.27, cy - s * 0.16), (cx + lado * s * 0.05, cy - s * 0.02),
                                             (cx + lado * s * 0.07, cy + s * 0.1), (cx + lado * s * 0.24, cy + s * 0.02)])
    elif rama == "cambiaformas":
        # Una cara partida: mitad de un color, mitad de otro.
        r = int(s * 0.42)
        pygame.draw.circle(sup, color, (cx, cy), r)
        pygame.draw.circle(sup, fondo, (cx, cy), r - g, draw_top_right=True, draw_bottom_right=True)
        pygame.draw.circle(sup, fondo, (int(cx - s * 0.17), int(cy - s * 0.06)), max(2, int(s * 0.07)))
        pygame.draw.circle(sup, color, (int(cx + s * 0.17), int(cy - s * 0.06)), max(2, int(s * 0.07)))
        pygame.draw.line(sup, fondo, (cx - s * 0.28, cy + s * 0.17), (cx - s * 0.06, cy + s * 0.2), g)
        pygame.draw.line(sup, color, (cx + s * 0.06, cy + s * 0.2), (cx + s * 0.28, cy + s * 0.14), g)
    elif rama == "caso":
        # Una lupa.
        pygame.draw.circle(sup, color, (int(cx - s * 0.08), int(cy - s * 0.08)), int(s * 0.28), g + 1)
        pygame.draw.line(sup, color, (cx + s * 0.12, cy + s * 0.12), (cx + s * 0.4, cy + s * 0.4), int(g * 1.8))
    else:
        # La raíz: una estrella.
        puntos = []
        for i in range(10):
            r = s * (0.47 if i % 2 == 0 else 0.2)
            a = -math.pi / 2 + i * math.pi / 5
            puntos.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        pygame.draw.polygon(sup, color, puntos)


_insignias = {}


def insignia(diametro, rama, est, logro=None):
    """El círculo con el dibujo del logro (`logro` = su clave, ver
    screens/iconos_logros.py; si no tiene, el de la rama; "oculto": un
    candado). Guardada."""
    diametro = max(8, int(diametro))
    clave = (diametro, rama, est, logro if est != "oculto" else None)
    img = _insignias.get(clave)
    if img is not None:
        return img
    color = COLOR_RAMA.get(rama, COLOR_TEXTO)
    d = diametro * SUPERMUESTREO
    sup = pygame.Surface((d, d), pygame.SRCALPHA)
    c = (d // 2, d // 2)
    if est == "obtenido":
        fondo, aro, icono = _oscuro(color, 0.32), color, _mezclar(color, (255, 255, 255), 0.55)
    elif est == "visible":
        fondo, aro, icono = (30, 32, 54), _mezclar(color, COLOR_TARJETA, 0.45), _mezclar(color, COLOR_TARJETA, 0.3)
    else:
        fondo, aro, icono = (24, 25, 38), COLOR_OCULTO, (88, 92, 116)
    pygame.draw.circle(sup, fondo, c, d // 2)
    pygame.draw.circle(sup, aro, c, d // 2, max(2, d // 16))
    if est == "obtenido":
        # Brillo arriba, como una ficha.
        pygame.draw.circle(sup, _mezclar(color, (255, 255, 255), 0.35), c, d // 2 - d // 9,
                           max(1, d // 40), draw_top_left=True, draw_top_right=True)
    from screens import iconos_logros
    if est == "oculto" or not iconos_logros.dibujar(sup, logro, c, d * 0.56, icono, fondo):
        _dibujar_icono(sup, "oculto" if est == "oculto" else rama, c, d * 0.56, icono, fondo)
    img = pygame.transform.smoothscale(sup, (diametro, diametro))
    _insignias[clave] = img
    return img


def _palomita(sup, centro, r):
    """Círculo dorado con visto bueno (logro conseguido)."""
    d = r * 2 * SUPERMUESTREO
    s = pygame.Surface((d, d), pygame.SRCALPHA)
    pygame.draw.circle(s, (40, 30, 6), (d // 2, d // 2), d // 2)
    pygame.draw.circle(s, COLOR_SELECCION, (d // 2, d // 2), d // 2 - d // 12)
    pygame.draw.lines(s, (40, 30, 6), False, [(d * 0.28, d * 0.52), (d * 0.44, d * 0.68), (d * 0.73, d * 0.34)],
                      max(2, d // 7))
    img = pygame.transform.smoothscale(s, (r * 2, r * 2))
    sup.blit(img, (centro[0] - r, centro[1] - r))


def _resplandor(tamano, color, radio_borde):
    """Un halo difuso del tamaño dado (achicar y agrandar hace de desenfoque)."""
    w, h = tamano
    chico = pygame.Surface((max(2, w // 6), max(2, h // 6)), pygame.SRCALPHA)
    borde = max(2, min(chico.get_width(), chico.get_height()) // 5)
    pygame.draw.rect(chico, (*color, 160), chico.get_rect().inflate(-borde * 2, -borde * 2),
                     border_radius=max(1, radio_borde // 6))
    return pygame.transform.smoothscale(chico, (w, h))


_resplandores = {}


def _resplandor_guardado(tamano, color, radio_borde):
    clave = (tamano, color, radio_borde)
    if clave not in _resplandores:
        _resplandores[clave] = _resplandor(tamano, color, radio_borde)
    return _resplandores[clave]


# -- Aviso al conseguir uno ---------------------------------------------------------------

_fondos_aviso = {}


def _fondo_aviso(tamano, alfa):
    clave = (tamano, alfa // 16)
    img = _fondos_aviso.get(clave)
    if img is None:
        if len(_fondos_aviso) > 64:
            _fondos_aviso.clear()
        img = pygame.Surface(tamano, pygame.SRCALPHA)
        pygame.draw.rect(img, (16, 16, 30, alfa // 16 * 16), img.get_rect(), border_radius=8)
        _fondos_aviso[clave] = img
    return img


def render_aviso_logro(screen, gestor):
    """Cartel abajo al centro: insignia, "¡LOGRO!", nombre y descripción."""
    if gestor is None or not gestor.avisos:
        return
    nodo, ms = gestor.avisos[0]
    ancho, alto = screen.get_size()
    color = _color(nodo)
    f_titulo = fuente_de_tamano(22 if ancho >= 1200 else 18)
    f_desc = fuente_de_tamano(15 if ancho >= 1200 else 13)
    from juego import cache_dibujo
    titulo = cache_dibujo.texto(f_titulo, nodo.nombre, COLOR_TEXTO)
    etiqueta = cache_dibujo.texto(f_desc, "¡LOGRO!", COLOR_SELECCION)
    desc = cache_dibujo.texto(f_desc, nodo.descripcion, COLOR_TENUE)
    tam_icono = 48 if ancho >= 1200 else 40
    caja = pygame.Rect(0, 0, max(titulo.get_width() + etiqueta.get_width() + 12,
                                 desc.get_width()) + tam_icono + 46,
                       max(tam_icono, titulo.get_height() + desc.get_height()) + 22)
    caja.midbottom = (ancho // 2, alto - 130)
    # Entra deslizándose y se va apagando al final.
    entrada = min(1.0, (3500 - ms) / 250) if ms <= 3500 else 1.0
    caja.y += int((1 - max(0.0, entrada)) * 40)
    alfa = 240 if ms > 400 else int(240 * ms / 400)
    screen.blit(_fondo_aviso(caja.size, alfa), caja.topleft)
    # Franja del color de la rama a la izquierda y borde.
    franja = pygame.Rect(caja.x, caja.y, 6, caja.h)
    pygame.draw.rect(screen, color, franja, border_top_left_radius=8, border_bottom_left_radius=8)
    pygame.draw.rect(screen, color, caja, 2, border_radius=8)
    icono = insignia(tam_icono, nodo.rama, "obtenido", nodo.clave)
    screen.blit(icono, (caja.x + 14, caja.centery - tam_icono // 2))
    x = caja.x + 14 + tam_icono + 12
    y = caja.y + 11
    screen.blit(etiqueta, (x, y + (titulo.get_height() - etiqueta.get_height()) // 2))
    screen.blit(titulo, (x + etiqueta.get_width() + 12, y))
    screen.blit(desc, (x, y + titulo.get_height() + 2))


# -- Árbol completo ------------------------------------------------------------------------

def estado(nodo, catalogo=False):
    """En el catálogo del menú se ven todos (los que faltan, sin palomita)."""
    if nodo.obtenido:
        return "obtenido"
    return "visible" if nodo.visible or catalogo else "oculto"


def _subtitulo(nodo, est, catalogo):
    if est == "oculto":
        return "Bloqueado"
    if est != "obtenido":
        return "Pendiente"
    if catalogo is not None:
        veces = catalogo.get(nodo.clave, 0)
        return f"Conseguido x{veces}" if veces > 1 else "Conseguido"
    return nodo.quien or "Conseguido"


def _partir(texto, f, maximo):
    """El texto (ya traducido) en una o dos líneas que quepan en `maximo`, o
    None si ni en dos caben."""
    if f.size(texto)[0] <= maximo:
        return [texto]
    cortes = []                 # después de un espacio (se quita) o de un guion (se deja)
    for i, letra in enumerate(texto):
        if letra == " ":
            cortes.append((texto[:i], texto[i + 1:]))
        elif letra == "-" and 0 < i < len(texto) - 1:
            cortes.append((texto[:i + 1], texto[i + 1:]))
    mejor = None
    for a, b in cortes:
        ancho = max(f.size(a)[0], f.size(b)[0])
        if mejor is None or ancho < mejor[0]:
            mejor = (ancho, a, b)
    if mejor is None or mejor[0] > maximo:
        return None
    return [mejor[1], mejor[2]]


def _renglones(texto, f, maximo, color):
    """El nombre en una línea, o en dos si no cabe (partido por una palabra)."""
    texto = tr(texto)
    lineas = _partir(texto, f, maximo) or [texto]
    return [f.render(l, True, color) for l in lineas]


def _envolver(texto, f, maximo, max_lineas=3):
    """Un párrafo (traducido) en renglones de `maximo` px como mucho."""
    palabras, lineas, actual = tr(texto).split(), [], ""
    for p in palabras:
        prueba = f"{actual} {p}".strip()
        if f.size(prueba)[0] <= maximo or not actual:
            actual = prueba
        else:
            lineas.append(actual)
            actual = p
    if actual:
        lineas.append(actual)
    if len(lineas) > max_lineas:
        lineas = lineas[:max_lineas]
        while lineas[-1] and f.size(lineas[-1] + "...")[0] > maximo:
            lineas[-1] = lineas[-1][:-1]
        lineas[-1] += "..."
    return lineas


_tarjetas = {}


def _medidas_tarjeta(w, h):
    """(margen, diámetro de la insignia, x del texto, radio de la palomita)."""
    margen = max(5, h // 8)
    d = min(h - margen * 2, int(w * 0.27))       # en tarjetas angostas, insignia más chica
    return margen, d, margen * 2 + d, max(6, min(h // 7, d // 4))


def _letra_tarjetas(nodos, w, h):
    """El tamaño de letra más grande con el que TODOS los nombres caben (en
    una o dos líneas): así todas las tarjetas van con la misma letra."""
    margen, _, x, _ = _medidas_tarjeta(w, h)
    maximo = w - x - margen
    tam = max(11, min(22, int(h * 0.27)))
    while tam > 10:
        f = fuente_de_tamano(tam)
        if all(_partir(tr(n.nombre), f, maximo) is not None for n in nodos):
            break
        tam -= 1
    return tam


def _tarjeta(nodo, est, w, h, sub, tam):
    """La tarjeta de un logro, guardada por estado, tamaño e idioma."""
    clave = (nodo.clave, nodo.rama, nodo.nombre, est, w, h, sub, tam, idioma.IDIOMA)
    img = _tarjetas.get(clave)
    if img is not None:
        return img
    if len(_tarjetas) > 600:
        _tarjetas.clear()
    color = _color(nodo)
    radio = max(6, h // 6)
    sup = pygame.Surface((w, h), pygame.SRCALPHA)
    fondo = pygame.Surface((w, h), pygame.SRCALPHA)
    if est == "obtenido":
        arriba = _mezclar(COLOR_TARJETA, color, 0.42)
        abajo = _mezclar(COLOR_TARJETA, color, 0.16)
        for y in range(h):
            pygame.draw.line(fondo, _mezclar(arriba, abajo, y / max(1, h - 1)), (0, y), (w, y))
        borde = color
    elif est == "visible":
        fondo.fill(COLOR_TARJETA)
        borde = _mezclar(color, COLOR_TARJETA, 0.5)
    else:
        fondo.fill(COLOR_TARJETA_OCULTA)
        borde = (46, 48, 66)
    mascara = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(mascara, (255, 255, 255, 255), (0, 0, w, h), border_radius=radio)
    fondo.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    sup.blit(fondo, (0, 0))
    if est == "obtenido":
        # Reflejo arriba (como vidrio) y franja de la rama a la izquierda.
        brillo = pygame.Surface((w - 8, max(1, h // 3)), pygame.SRCALPHA)
        brillo.fill((255, 255, 255, 18))
        sup.blit(brillo, (4, 3))
    pygame.draw.rect(sup, borde, (0, 0, w, h), 2, border_radius=radio)

    margen, d, x, r_palomita = _medidas_tarjeta(w, h)
    y_insignia = (h - d) // 2
    sup.blit(insignia(d, nodo.rama, est, nodo.clave), (margen, y_insignia))
    maximo = w - x - margen
    if est == "obtenido":
        # La palomita va encima de la insignia, abajo a la derecha.
        _palomita(sup, (margen + d - r_palomita + 3, y_insignia + d - r_palomita + 3), r_palomita)

    nombre = tr(nodo.nombre) if est != "oculto" else "???"
    color_nombre = COLOR_TEXTO if est == "obtenido" else (_mezclar(COLOR_TEXTO, COLOR_TENUE, 0.5)
                                                          if est == "visible" else COLOR_OCULTO)
    color_sub = (_mezclar(color, COLOR_TEXTO, 0.35) if est == "obtenido"
                 else (COLOR_TENUE if est == "visible" else (80, 82, 102)))
    lineas = None
    while tam >= 10:
        f = fuente_de_tamano(tam)
        lineas = _partir(nombre, f, maximo)
        if lineas is not None:
            break
        tam -= 1
    if lineas is None:
        lineas = [nombre]
    f = fuente_de_tamano(tam)
    f_sub = fuente_de_tamano(max(10, tam - 4))
    alto_nombre = f.get_linesize() * len(lineas)
    con_sub = alto_nombre + f_sub.get_linesize() <= h - 6
    alto_total = alto_nombre + (f_sub.get_linesize() if con_sub else 0)
    y = (h - alto_total) // 2
    for l in lineas:
        sup.blit(f.render(l, True, color_nombre), (x, y))
        y += f.get_linesize()
    if con_sub:
        sup.blit(f_sub.render(sub, True, color_sub), (x, y))
    _tarjetas[clave] = sup
    return sup


# -- Disposición y desplazamiento ------------------------------------------------------------

_disposiciones = {}


def _disposicion(arbol, ancho, alto, area):
    """Rect de cada tarjeta en coordenadas del contenido (antes de desplazar),
    tamaño de tarjeta, paso entre filas y alto total."""
    clave = (id(arbol), arbol.total(), ancho, alto, area.w)
    guardada = _disposiciones.get(clave)
    if guardada is not None:
        return guardada
    pos = arbol.posiciones()
    columnas = max(c for c, _ in pos.values()) + 1
    filas = max(f for _, f in pos.values()) + 1
    paso_x = (area.w - 8) / columnas
    hueco = max(20, min(40, int(paso_x * 0.14)))
    w = int(paso_x - hueco)
    h = max(48, min(84, int(alto * 0.084)))
    h = min(h, max(44, int(w * 0.42)))
    paso_y = h + max(10, int(h * 0.24))
    arriba = 14
    rects = {}
    for nodo, (c, f) in pos.items():
        rects[nodo] = pygame.Rect(int(4 + c * paso_x), int(arriba + f * paso_y), w, h)
    alto_contenido = int(arriba * 2 + (filas - 1) * paso_y + h)
    guardada = {"rects": rects, "w": w, "h": h, "paso_y": paso_y, "alto": alto_contenido,
                "letra": _letra_tarjetas(list(rects), w, h)}
    if len(_disposiciones) > 20:
        _disposiciones.clear()
    _disposiciones[clave] = guardada
    return guardada


# Estado de la vista: dónde está y a dónde va. Es del último árbol dibujado.
_vista = {"clave": None, "y": 0.0, "objetivo": 0.0, "sel": None, "t": 0, "paso": 60}


def rueda(dy):
    """La rueda del mouse sobre el árbol: desplaza la vista (`dy` > 0 sube)."""
    _vista["objetivo"] -= dy * _vista["paso"] * 1.5


def _mover_vista(disp, area, seleccionado, clave):
    """Lleva la vista hasta el logro seleccionado cuando cambia y la desliza."""
    maximo = max(0, disp["alto"] - area.h)
    ahora = pygame.time.get_ticks()
    _vista["paso"] = disp["paso_y"]
    rect = disp["rects"].get(seleccionado)
    if _vista["clave"] != clave:
        # Árbol o tamaño nuevo: centrada en lo seleccionado, sin deslizarse.
        _vista["clave"] = clave
        _vista["sel"] = seleccionado
        y = rect.centery - area.h / 2 if rect is not None else 0
        _vista["objetivo"] = _vista["y"] = max(0, min(maximo, y))
    elif seleccionado is not _vista["sel"]:
        # Cambió la selección: que se vea entera, con un poco de aire alrededor.
        _vista["sel"] = seleccionado
        if rect is not None:
            aire = min(disp["paso_y"] * 1.2, area.h / 3)
            if rect.top - aire < _vista["objetivo"]:
                _vista["objetivo"] = rect.top - aire
            elif rect.bottom + aire > _vista["objetivo"] + area.h:
                _vista["objetivo"] = rect.bottom + aire - area.h
    _vista["objetivo"] = max(0, min(maximo, _vista["objetivo"]))
    if not ANIMAR:
        _vista["y"] = _vista["objetivo"]
    else:
        dt = min(60, max(0, ahora - _vista["t"]))
        _vista["y"] += (_vista["objetivo"] - _vista["y"]) * (1 - math.exp(-dt / SUAVIZADO_MS))
        if abs(_vista["objetivo"] - _vista["y"]) < 0.5:
            _vista["y"] = _vista["objetivo"]
    _vista["t"] = ahora
    return _vista["y"]


# -- Fondo -----------------------------------------------------------------------------------

_fondos = {}


def _fondo(tamano):
    """Degradado oscuro con estrellas (siempre las mismas). Guardado por tamaño."""
    img = _fondos.get(tamano)
    if img is not None:
        return img
    ancho, alto = tamano
    img = pygame.Surface(tamano)
    for y in range(alto):
        pygame.draw.line(img, _mezclar(COLOR_FONDO_ARBOL, COLOR_FONDO_ABAJO, y / max(1, alto - 1)),
                         (0, y), (ancho, y))
    azar = random.Random(7)
    # Nebulosas muy tenues.
    nubes = pygame.Surface((max(2, ancho // 8), max(2, alto // 8)), pygame.SRCALPHA)
    for color in ((70, 40, 120), (30, 70, 120), (110, 40, 90)):
        cx, cy = azar.random() * nubes.get_width(), azar.random() * nubes.get_height()
        r = azar.uniform(0.18, 0.32) * nubes.get_width()
        for k in range(6, 0, -1):
            pygame.draw.circle(nubes, (*color, 7), (int(cx), int(cy)), int(r * k / 6))
    img.blit(pygame.transform.smoothscale(nubes, tamano), (0, 0))
    for _ in range(ancho * alto // 5000):
        x, y = azar.randrange(ancho), azar.randrange(alto)
        brillo = azar.choice((70, 90, 110, 140, 190))
        img.set_at((x, y), (brillo, brillo, min(255, brillo + 30)))
        if brillo >= 190:
            pygame.draw.circle(img, (brillo // 3, brillo // 3, brillo // 2), (x, y), 2)
            img.set_at((x, y), (230, 232, 255))
    if len(_fondos) > 4:
        _fondos.clear()
    _fondos[tamano] = img
    return img


# -- Dibujo del árbol ------------------------------------------------------------------------

def _contar(nodo):
    """(obtenidos, total) de la rama que empieza en `nodo`."""
    obtenidos, total, pila = 0, 0, [nodo]
    while pila:
        n = pila.pop()
        total += 1
        obtenidos += 1 if n.obtenido else 0
        pila.extend(n.hijos)
    return obtenidos, total


def _rama_de(nodo):
    """El hijo de la raíz del que cuelga `nodo` (o la raíz)."""
    while nodo is not None and nodo.padre is not None and nodo.padre.padre is not None:
        nodo = nodo.padre
    return nodo


def _encabezado(screen, arbol, seleccionado, es_catalogo):
    """Título, cuenta, barra de progreso y una ficha por rama. Devuelve dónde termina."""
    ancho, alto = screen.get_size()
    k = _escala(alto)
    f_titulo = fuente_de_tamano(int(28 * k)) if k > 1 else fuente("subtitle")
    titulo = f_titulo.render("Todos los logros" if es_catalogo else "Logros de esta partida",
                             True, COLOR_SELECCION)
    screen.blit(titulo, (32, 16))
    obtenidos, total = arbol.obtenidos(), arbol.total()
    cuenta = f_titulo.render(f"{obtenidos}/{total}", True, COLOR_TEXTO)
    f_por = fuente_de_tamano(int(16 * k))
    por = f_por.render(f"{round(100 * obtenidos / max(1, total))}%", True, COLOR_TENUE)
    screen.blit(cuenta, (ancho - 32 - cuenta.get_width(), 16))
    screen.blit(por, (ancho - 32 - cuenta.get_width() - 10 - por.get_width(),
                      16 + titulo.get_height() - por.get_height() - 3))

    y = 16 + titulo.get_height() + 8
    barra = pygame.Rect(32, y, ancho - 64, int(8 * k))
    pygame.draw.rect(screen, (34, 36, 60), barra, border_radius=4)
    if obtenidos:
        lleno = barra.copy()
        lleno.w = max(8, int(barra.w * obtenidos / max(1, total)))
        pygame.draw.rect(screen, COLOR_SELECCION, lleno, border_radius=4)
        pygame.draw.rect(screen, (255, 240, 170), (lleno.x + 3, lleno.y + 1, max(1, lleno.w - 6), 2),
                         border_radius=1)
    y = barra.bottom + 10

    # Fichas de las ramas: ícono, nombre y cuántos van.
    raiz = arbol.raiz
    ramas = list(raiz.hijos) if raiz is not None else []
    if not ramas:
        return y
    actual = _rama_de(seleccionado) if seleccionado is not None else None
    f = fuente_de_tamano(int(15 * k))
    alto_ficha = int(28 * k)
    d = alto_ficha - 8
    fichas = []
    for con_nombre in (True, False):
        fichas = []
        for nodo in ramas:
            o, t = _contar(nodo)
            texto = f"{tr(NOMBRE_RAMA.get(nodo.rama, nodo.rama))}  {o}/{t}" if con_nombre else f"{o}/{t}"
            fichas.append((nodo, texto, o == t, 4 + d + 6 + f.size(texto)[0] + 10))
        if sum(w for *_, w in fichas) + 8 * (len(fichas) - 1) <= ancho - 64:
            break
    else:
        return y
    x = 32
    for nodo, texto, completa, w in fichas:
        color = _color(nodo)
        caja = pygame.Rect(x, y, w, alto_ficha)
        sel = nodo is actual
        pygame.draw.rect(screen, _mezclar(COLOR_TARJETA, color, 0.28 if sel else 0.1), caja,
                         border_radius=alto_ficha // 2)
        pygame.draw.rect(screen, color if sel else _mezclar(color, COLOR_TARJETA, 0.55), caja,
                         2, border_radius=alto_ficha // 2)
        screen.blit(insignia(d, nodo.rama, "obtenido" if completa or sel else "visible", nodo.clave), (x + 4, y + 4))
        screen.blit(f.render(texto, True, COLOR_TEXTO if sel or completa else COLOR_TENUE),
                    (x + 4 + d + 6, caja.centery - f.get_height() // 2))
        x += w + 8
    return y + alto_ficha


def _lineas(screen, rects, arbol, seleccionado):
    """Las conexiones como pistas de circuito: apagadas, y del color de la rama
    hasta cada hijo conseguido. El camino hasta lo seleccionado, dorado."""
    apagado = (58, 62, 92)
    camino = set()
    n = seleccionado
    while n is not None:
        camino.add(n)
        n = n.padre
    for nodo in arbol.preorden():
        if not nodo.hijos or nodo not in rects:
            continue
        p = rects[nodo]
        hijos = [h for h in nodo.hijos if h in rects]
        if not hijos:
            continue
        bus = p.right + (rects[hijos[0]].left - p.right) // 2
        ys = [rects[h].centery for h in hijos] + [p.centery]
        # Apagado: todo.
        pygame.draw.line(screen, apagado, (p.right, p.centery), (bus, p.centery), 2)
        pygame.draw.line(screen, apagado, (bus, min(ys)), (bus, max(ys)), 2)
        for h in hijos:
            pygame.draw.line(screen, apagado, (bus, rects[h].centery), (rects[h].left, rects[h].centery), 2)
        # Prendido: de la salida del padre a cada hijo conseguido.
        for h in hijos:
            if not h.obtenido:
                continue
            color = _color(h)
            r = rects[h]
            trazo = [(p.right, p.centery), (bus, p.centery), (bus, r.centery), (r.left, r.centery)]
            pygame.draw.lines(screen, _oscuro(color, 0.35), False, trazo, 7)
            pygame.draw.lines(screen, color, False, trazo, 3)
        # Dorado: hacia lo seleccionado.
        for h in hijos:
            if h in camino and nodo in camino:
                r = rects[h]
                trazo = [(p.right, p.centery), (bus, p.centery), (bus, r.centery), (r.left, r.centery)]
                pygame.draw.lines(screen, _oscuro(COLOR_SELECCION, 0.4), False, trazo, 7)
                pygame.draw.lines(screen, COLOR_SELECCION, False, trazo, 3)
        # Uniones.
        alguno = any(h.obtenido for h in hijos)
        pygame.draw.circle(screen, _color(nodo) if alguno else apagado, (bus, p.centery), 4)
        for h in hijos:
            color = _color(h) if h.obtenido else apagado
            pygame.draw.circle(screen, color, (bus, rects[h].centery), 3)


def render_arbol_logros(screen, arbol, seleccionado=None, catalogo=None):
    """Dibuja el árbol entero. Devuelve {nodo: rect} (lo que se ve) para el mouse.

    `catalogo` ({clave: veces}): el de "Logros" en el menú principal. Se ven
    todos, con nombre y descripción, y los obtenidos son los que salieron
    alguna vez en este computador (juego/historial_logros.py)."""
    ancho, alto = screen.get_size()
    screen.blit(_fondo((ancho, alto)), (0, 0))
    es_catalogo = catalogo is not None
    if arbol is None or arbol.raiz is None:
        return {}

    abajo_encabezado = _encabezado(screen, arbol, seleccionado, es_catalogo)
    alto_info = max(104, min(170, int(alto * 0.16)))
    f_pista = fuente_de_tamano(int(15 * _escala(alto)))
    caja_info = pygame.Rect(32, alto - alto_info - f_pista.get_linesize() - 18, ancho - 64, alto_info)
    area = pygame.Rect(24, abajo_encabezado + 10, ancho - 48, caja_info.top - 10 - (abajo_encabezado + 10))
    if area.h < 60:
        return {}

    disp = _disposicion(arbol, ancho, alto, area)
    desfase_y = 0
    if disp["alto"] < area.h:
        desfase_y = (area.h - disp["alto"]) // 2          # cabe entero: centrado
    y_vista = _mover_vista(disp, area, seleccionado, (id(arbol), ancho, alto))
    dx, dy = area.x, area.y - int(round(y_vista)) + desfase_y
    rects = {n: r.move(dx, dy) for n, r in disp["rects"].items()}

    recorte = screen.get_clip()
    screen.set_clip(area)
    _lineas(screen, rects, arbol, seleccionado)
    visibles = {}
    for nodo, rect in rects.items():
        if rect.bottom < area.top or rect.top > area.bottom:
            continue
        est = estado(nodo, es_catalogo)
        if nodo is seleccionado:
            pulso = 0.5 + 0.5 * math.sin(pygame.time.get_ticks() / 260)
            halo = _resplandor_guardado((rect.w + 36, rect.h + 36), COLOR_SELECCION, max(6, rect.h // 6))
            halo = halo.copy()
            halo.set_alpha(int(110 + 100 * pulso))
            screen.blit(halo, (rect.x - 18, rect.y - 18))
        screen.blit(_tarjeta(nodo, est, rect.w, rect.h, _subtitulo(nodo, est, catalogo), disp["letra"]), rect.topleft)
        if nodo is seleccionado:
            pygame.draw.rect(screen, COLOR_SELECCION, rect.inflate(6, 6), 2, border_radius=max(8, rect.h // 6 + 3))
        visible = rect.clip(area)
        if visible.w and visible.h:
            visibles[nodo] = visible
    # Bordes que se desvanecen arriba y abajo (hay más árbol por ahí).
    maximo = max(0, disp["alto"] - area.h)
    _desvanecer(screen, area, arriba=y_vista > 1, abajo=y_vista < maximo - 1)
    screen.set_clip(recorte)
    if maximo > 0:
        _barra_desplazamiento(screen, area, y_vista, disp["alto"])

    _info(screen, caja_info, seleccionado, catalogo)
    texto = ("Flechas: moverse por el árbol (izq: padre, der: hijo)  ·  Rueda: desplazar  ·  Esc: volver"
             if maximo > 0 else "Flechas: moverse por el árbol (izq: padre, der: hijo)  ·  Esc: volver")
    pista = f_pista.render(texto, True, COLOR_TENUE)
    if pista.get_width() > ancho - 32:
        pista = f_pista.render("Flechas: moverse por el árbol (izq: padre, der: hijo)  ·  Esc: volver",
                               True, COLOR_TENUE)
    screen.blit(pista, pista.get_rect(midbottom=(ancho // 2, alto - 8)))
    return visibles


_velos = {}


def _desvanecer(screen, area, arriba, abajo):
    alto = min(36, area.h // 6)
    for lado, hay in (("arriba", arriba), ("abajo", abajo)):
        if not hay:
            continue
        clave = (area.w, alto, lado)
        velo = _velos.get(clave)
        if velo is None:
            velo = pygame.Surface((area.w, alto), pygame.SRCALPHA)
            for i in range(alto):
                t = (1 - i / alto) if lado == "arriba" else (i / alto)
                pygame.draw.line(velo, (*COLOR_FONDO_ARBOL, int(220 * t * t)), (0, i), (area.w, i))
            _velos[clave] = velo
        screen.blit(velo, (area.x, area.y if lado == "arriba" else area.bottom - alto))


def _barra_desplazamiento(screen, area, y, alto_contenido):
    carril = pygame.Rect(area.right + 8, area.y + 4, 5, area.h - 8)
    if carril.right > screen.get_width():
        carril.x = area.right - 7
    pygame.draw.rect(screen, (34, 36, 60), carril, border_radius=3)
    largo = max(24, int(carril.h * area.h / alto_contenido))
    maximo = max(1, alto_contenido - area.h)
    pulgar = pygame.Rect(carril.x, carril.y + int((carril.h - largo) * y / maximo), carril.w, largo)
    pygame.draw.rect(screen, (130, 136, 180), pulgar, border_radius=3)


def _info(screen, caja, nodo, catalogo=None):
    """El recuadro de abajo: insignia grande, nombre, rama, descripción,
    estado y a qué logros lleva."""
    fondo = pygame.Surface(caja.size, pygame.SRCALPHA)
    pygame.draw.rect(fondo, (20, 21, 40, 235), fondo.get_rect(), border_radius=10)
    screen.blit(fondo, caja.topleft)
    if nodo is None:
        pygame.draw.rect(screen, (60, 64, 96), caja, 2, border_radius=10)
        return
    color = _color(nodo)
    est = estado(nodo, catalogo is not None)
    pygame.draw.rect(screen, color if est != "oculto" else COLOR_OCULTO, caja, 2, border_radius=10)
    pygame.draw.rect(screen, color if est != "oculto" else COLOR_OCULTO,
                     (caja.x, caja.y, 6, caja.h), border_top_left_radius=10, border_bottom_left_radius=10)

    d = min(96, caja.h - 28)
    screen.blit(insignia(d, nodo.rama, est, nodo.clave), (caja.x + 20, caja.centery - d // 2))
    x = caja.x + 20 + d + 18

    if est == "oculto":
        nombre = "???"
        desc = (f"Consigue primero «{nodo.padre.nombre}»." if nodo.padre and nodo.padre.visible
                else "Sigue jugando para descubrirlo.")
        abajo = ""
    else:
        nombre, desc = nodo.nombre, nodo.descripcion
        if catalogo is not None:
            veces = catalogo.get(nodo.clave, 0)
            abajo = (f"Conseguido en {veces} partida{'s' if veces != 1 else ''}" if veces
                     else "Todavía no lo consiguen en este computador")
        elif est == "obtenido":
            quien = f"el {nodo.quien}" if nodo.quien else "el equipo"
            abajo = (f"Conseguido por {quien} (al conseguir uno que sale de este)"
                     if nodo.por_camino else f"Conseguido por {quien}")
        else:
            abajo = "Pendiente"

    # A la derecha, a qué lleva (si hay espacio).
    derecha = 0
    if caja.w >= 900:
        derecha = int(caja.w * 0.28)
        _lleva_a(screen, pygame.Rect(caja.right - derecha, caja.y + 12, derecha - 18, caja.h - 24),
                 nodo, catalogo)
    ancho_texto = caja.right - derecha - 18 - x

    k = _escala(screen.get_height())
    f1 = fuente_de_tamano(int((24 if caja.h >= 120 else 21) * k))
    f2 = fuente_de_tamano(int((17 if caja.h >= 120 else 15) * k))
    f3 = fuente_de_tamano(int((16 if caja.h >= 120 else 14) * k))
    color_nombre = color if est != "oculto" else COLOR_TENUE
    texto_nombre = f1.render(nombre, True, color_nombre)
    lineas_desc = _envolver(desc, f2, ancho_texto, 2)
    alto_bloque = f1.get_linesize() + 4 + f2.get_linesize() * len(lineas_desc) + (f3.get_linesize() + 2 if abajo else 0)
    y = caja.centery - alto_bloque // 2
    screen.blit(texto_nombre, (x, y))
    # Ficha con el nombre de la rama, al lado del nombre.
    if est != "oculto":
        f_rama = fuente_de_tamano(int(14 * k))
        texto_rama = f_rama.render(NOMBRE_RAMA.get(nodo.rama, nodo.rama), True, color)
        alto_ficha = f_rama.get_height() + 6
        ficha = pygame.Rect(x + texto_nombre.get_width() + 12, y + (f1.get_height() - alto_ficha) // 2,
                            texto_rama.get_width() + 18, alto_ficha)
        if ficha.right <= caja.right - derecha - 10:
            pygame.draw.rect(screen, _mezclar(COLOR_TARJETA, color, 0.18), ficha, border_radius=alto_ficha // 2)
            pygame.draw.rect(screen, _mezclar(color, COLOR_TARJETA, 0.3), ficha, 1, border_radius=alto_ficha // 2)
            screen.blit(texto_rama, texto_rama.get_rect(center=ficha.center))
    y += f1.get_linesize() + 4
    for linea in lineas_desc:
        screen.blit(f2.render(linea, True, COLOR_TEXTO), (x, y))
        y += f2.get_linesize()
    if abajo:
        screen.blit(f3.render(abajo, True, COLOR_OK if est == "obtenido" else COLOR_TENUE), (x, y + 2))


def _lleva_a(screen, caja, nodo, catalogo):
    """Columna "Lleva a:" con los hijos del logro (los ocultos como ???)."""
    pygame.draw.line(screen, (52, 56, 86), (caja.x - 12, caja.y + 4), (caja.x - 12, caja.bottom - 4), 1)
    k = _escala(screen.get_height())
    f = fuente_de_tamano(int(15 * k))
    f_titulo = fuente_de_tamano(int(14 * k))
    y = caja.y
    if not nodo.hijos:
        screen.blit(f_titulo.render("Es el último de su rama.", True, COLOR_TENUE), (caja.x, y))
        return
    screen.blit(f_titulo.render("Lleva a:", True, COLOR_TENUE), (caja.x, y))
    y += f_titulo.get_linesize() + 2
    caben = max(1, (caja.bottom - y) // (f.get_linesize() + 2))
    hijos = nodo.hijos
    mostrar = hijos if len(hijos) <= caben else hijos[:caben - 1]
    d = f.get_height() - 2
    for h in mostrar:
        est = estado(h, catalogo is not None)
        screen.blit(insignia(d, h.rama, est, h.clave), (caja.x, y + 1))
        nombre = tr(h.nombre) if est != "oculto" else "???"
        while nombre and f.size(nombre)[0] > caja.w - d - 8:
            nombre = nombre[:-4] + "..." if len(nombre) > 4 else ""
        color = COLOR_TEXTO if est == "obtenido" else (COLOR_TENUE if est == "visible" else COLOR_OCULTO)
        screen.blit(f.render(nombre, True, color), (caja.x + d + 8, y))
        y += f.get_linesize() + 2
    if len(mostrar) < len(hijos):
        screen.blit(f.render(f"y {len(hijos) - len(mostrar)} más", True, COLOR_TENUE), (caja.x + d + 8, y))


idioma.al_cambiar(lambda: (_tarjetas.clear(), _disposiciones.clear()))
