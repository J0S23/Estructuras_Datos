"""Luces de colores, pantallas que titilan, estrellas tras los ventanales y la
alarma (juego/efectos.py tiene el resto de los efectos).

- **Luces** (`dibujar`, encima de la oscuridad de cada vista): manchas de luz
  de color que respiran, pegadas con BLEND_RGB_ADD. Las de las cosas del juego
  salen del estado (consolas prendidas o apagadas, terminales, NEXUS, la
  cápsula, cajas de fusibles, paneles rotos y reparados, sellos, puertas,
  compuertas, señuelos y señales) y las del mapa de data/luces_mapa.py (el
  reactor, la incubadora, el ventanal, las pantallas de General y Control, los
  tubos del laboratorio y cada lámpara de los pasillos, que se encuentran
  solas por su color). Cada luz se multiplica por la luz que hay donde está
  (oscuridad.brillo_en): detrás de una pared, fuera del campo de visión, se
  ve tenue como todo lo demás. En un apagón se apagan las eléctricas.
- **Pantallas**: los píxeles brillantes de pantallas y tubos del mapa (y de
  las consolas y terminales: `pantalla`) titilan, respiran y les pasa una
  línea de barrido; las lámparas que "fallan" se apagan a ratos.
- **Ventanales** (`dibujar_fondo`): estrellas que pasan detrás del vidrio, en
  tres capas (las de lejos más lentas), y de vez en cuando una fugaz.
- **Alarma** (`dibujar_alarma`): la vista se tiñe de rojo que late, una franja
  de luz barre de lado a lado como una baliza que gira y los bordes se
  encienden. El cierre de emergencia (compuerta), lo mismo en ámbar y suave.

Todo se apaga con efectos.ACTIVOS.
"""

import math
import os
import random

import pygame

from juego import efectos
from juego import oscuridad

try:
    from data.luces_mapa import LUCES_MAPA
except ImportError:          # (sin el archivo de datos, solo las luces de las cosas)
    LUCES_MAPA = {}


NIVELES = 6                  # cuántas intensidades se guardan por luz chica
NIVELES_GRANDE = 4           # y por luz grande (ocupan más memoria)


def _ruido(n, semilla):
    """Un número "al azar" de 0 a 1 fijo para (n, semilla): parpadeos que no
    dependen de random (iguales en todas las vistas del mismo cuadro)."""
    x = (n * 374761393 + semilla * 668265263) & 0xFFFFFFFF
    x = ((x ^ (x >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((x ^ (x >> 16)) & 0xFFFF) / 65535


def factor_falla(t, semilla, falla):
    """1 casi siempre; si a la luz le toca fallar (rachas de ~1.3 s con
    probabilidad `falla`), parpadea entre apagada y a medias."""
    if falla <= 0:
        return 1.0
    if _ruido(int(t // 1300), semilla) >= falla:
        return 1.0
    r = _ruido(int(t // 55), semilla + 7)
    return 0.05 if r < 0.45 else (0.5 if r < 0.7 else 1.0)


def _respira(t, vel, fase, pulso):
    return 1 + pulso * math.sin(t / 1000 * vel * 2 * math.pi + fase)


# -- Manchas de luz -----------------------------------------------------------------------

_manchas = {}


def _mancha(radio, color, nivel, niveles):
    """Degradado radial de `color` (a nivel/niveles de fuerza) para BLEND_RGB_ADD."""
    clave = (radio, color, nivel, niveles)
    img = _manchas.get(clave)
    if img is None:
        if len(_manchas) > 700:
            _manchas.clear()
        chico = 48
        base = pygame.Surface((chico, chico))
        base.fill((0, 0, 0))
        f = nivel / niveles
        c = chico // 2
        for k in range(c, 0, -1):
            t = k / c
            v = (1 - t) ** 2.0 * f
            pygame.draw.circle(base, tuple(min(255, int(x * v)) for x in color), (c, c), k)
        img = pygame.transform.smoothscale(base, (radio * 2, radio * 2))
        _manchas[clave] = img
    return img


class Luz:
    __slots__ = ("x", "y", "radio", "color", "intensidad", "pulso", "vel", "fase", "falla",
                 "electrica", "semilla", "emergencia")

    def __init__(self, x, y, radio, color, intensidad=0.3, pulso=0.15, vel=0.6, falla=0.0,
                 electrica=True, semilla=0, emergencia=False):
        self.x, self.y = x, y
        self.radio = max(10, int(radio) // 10 * 10)
        self.color = tuple(color)
        self.intensidad, self.pulso, self.vel, self.falla = intensidad, pulso, vel, falla
        self.electrica, self.semilla, self.emergencia = electrica, semilla, emergencia
        self.fase = (semilla * 1.618) % (2 * math.pi)


def _pegar_luz(screen, luz, offset, t, brillo):
    k = luz.intensidad * _respira(t, luz.vel, luz.fase, luz.pulso) * brillo
    if luz.falla:
        k *= factor_falla(t, luz.semilla, luz.falla)
    niveles = NIVELES_GRANDE if luz.radio >= 200 else NIVELES
    nivel = int(round(k * niveles))
    if nivel <= 0:
        return
    nivel = min(niveles, nivel)
    img = _mancha(luz.radio, luz.color, nivel, niveles)
    screen.blit(img, (int(luz.x - offset[0] - luz.radio), int(luz.y - offset[1] - luz.radio)),
                special_flags=pygame.BLEND_RGB_ADD)


# -- Lo del mapa (data/luces_mapa.py) ---------------------------------------------------------

class Ventana:
    def __init__(self, rect, semilla):
        self.rect = rect
        azar = random.Random(semilla)
        cantidad = max(6, rect.w * rect.h // 900)
        # (x de 0 a 1, y en px, capa 0 lejos .. 2 cerca, fase)
        self.estrellas = [(azar.random(), azar.uniform(1, max(2, rect.h - 2)), azar.choice((0, 0, 0, 1, 1, 2)),
                           azar.uniform(0, 6.28)) for _ in range(cantidad)]
        self.semilla = semilla


class Brillo:
    """Los píxeles brillantes de un pedazo del mapa, listos para sumarlos o
    restarlos (titilar, respirar, apagarse)."""

    def __init__(self, rect, capa, modo, semilla, falla=0.0, electrica=True):
        self.rect, self.capa, self.modo = rect, capa, modo
        self.semilla, self.falla, self.electrica = semilla, falla, electrica
        self._niveles = {}
        for k in range(1, 7):        # todos ya: armarlos en medio del juego daba tirones de ~1 ms
            self.nivel(k / 6)

    def nivel(self, k):
        """La capa a `k` (de 0 a 1, en pasos de 1/6)."""
        k = max(1, min(6, int(round(k * 6))))
        img = self._niveles.get(k)
        if img is None:
            img = self.capa.copy()
            v = int(255 * k / 6)
            img.fill((v, v, v), special_flags=pygame.BLEND_RGB_MULT)
            self._niveles[k] = img
        return img


def _es_brillante(r, g, b):
    alto, bajo = max(r, g, b), min(r, g, b)
    return (alto >= 165 and alto - bajo >= 45) or alto >= 232


def _capa_brillante(original, rect_original, factor):
    """Los píxeles brillantes de `rect_original` (en la imagen original), negro
    lo demás, agrandados como el mapa (sin suavizar). None si no hay."""
    r = rect_original.clip(original.get_rect())
    if r.w <= 0 or r.h <= 0:
        return None
    capa = pygame.Surface(r.size)
    capa.fill((0, 0, 0))
    hay = False
    for y in range(r.h):
        for x in range(r.w):
            c = original.get_at((r.x + x, r.y + y))
            if c[3] > 200 and _es_brillante(c[0], c[1], c[2]):
                capa.set_at((x, y), c[:3])
                hay = True
    if not hay:
        return None
    return pygame.transform.scale(capa, (int(r.w * factor), int(r.h * factor)))


class LucesDelMapa:
    def __init__(self, mundo):
        self.luces, self.ventanas, self.brillos = [], [], []
        datos = LUCES_MAPA.get(getattr(mundo, "nombre_mapa", ""), {})
        original = _imagen_original(mundo)
        if original is None:
            return
        factor = mundo.ancho / max(1, original.get_width())

        def a_mundo(x, y):
            return x * factor, y * factor

        for i, l in enumerate(datos.get("luces", ())):
            x, y = a_mundo(l["x"], l["y"])
            self.luces.append(Luz(x, y, l["radio"], l["color"], l.get("intensidad", 0.3), l.get("pulso", 0.15),
                                  l.get("vel", 0.6), l.get("falla", 0.0), l.get("electrica", True), semilla=i + 1))
        lamparas = datos.get("lamparas")
        if lamparas:
            mascara = pygame.mask.from_threshold(original, (*lamparas["color"], 255), (2, 2, 2, 255))
            for i, comp in enumerate(mascara.connected_components(minimum=4)):
                cajas = comp.get_bounding_rects()
                if not cajas:
                    continue
                caja = cajas[0]
                semilla = 101 + i
                falla = lamparas.get("falla", 0.0) if _ruido(i, 3) < 0.35 else 0.0
                x, y = a_mundo(caja.centerx, caja.centery)
                self.luces.append(Luz(x, y, lamparas.get("radio", 70), lamparas.get("luz", lamparas["color"]),
                                      lamparas.get("intensidad", 0.2), 0.08, 0.5, falla, True, semilla=semilla))
                if falla:
                    capa = _capa_brillante(original, caja.inflate(4, 4), factor)
                    if capa is not None:
                        rx, ry = a_mundo(caja.x - 2, caja.y - 2)
                        self.brillos.append(Brillo(pygame.Rect(int(rx), int(ry), *capa.get_size()), capa,
                                                   "lampara", semilla, falla=falla))
        for i, (x, y, w, h) in enumerate(datos.get("ventanas", ())):
            rx, ry = a_mundo(x + 1, y + 1)
            self.ventanas.append(Ventana(pygame.Rect(int(rx), int(ry), int((w - 2) * factor), int((h - 2) * factor)),
                                         semilla=500 + i))
        self._rejilla = None
        for i, p in enumerate(datos.get("pantallas", ())):
            caja = pygame.Rect(p["rect"])
            capa = _capa_brillante(original, caja, factor)
            if capa is None:
                continue
            rx, ry = a_mundo(caja.x, caja.y)
            self.brillos.append(Brillo(pygame.Rect(int(rx), int(ry), *capa.get_size()), capa, p.get("modo", "titila"),
                                       900 + i, electrica=p.get("modo") != "respira"))


def _imagen_original(mundo):
    """La imagen del mapa sin agrandar (para buscar lámparas y brillos)."""
    try:
        from juego.mundo import CARPETA_FONDOS
    except ImportError:
        return None
    nombre = getattr(mundo, "nombre_mapa", None)
    if not nombre:
        return None
    for extension in (".png", ".jpg", ".jpeg"):
        ruta = os.path.join(CARPETA_FONDOS, nombre + extension)
        if os.path.isfile(ruta):
            try:
                return pygame.image.load(ruta)
            except pygame.error:
                return None
    return None


_mapas = {}


CELDA = 700


def _rejilla(luces):
    """{(cx, cy): [luces]} para buscar solo las que caen cerca de la cámara."""
    rejilla = {}
    for luz in luces:
        rejilla.setdefault((int(luz.x // CELDA), int(luz.y // CELDA)), []).append(luz)
    return rejilla


def _cerca(rejilla, camara, margen):
    x0, x1 = int((camara.x - margen) // CELDA), int((camara.right + margen) // CELDA)
    y0, y1 = int((camara.y - margen) // CELDA), int((camara.bottom + margen) // CELDA)
    for cx in range(x0, x1 + 1):
        for cy in range(y0, y1 + 1):
            lista = rejilla.get((cx, cy))
            if lista:
                yield from lista


_filtrados = {}


def _del_mapa(mapa, mundo):
    """(luces, brillos, ventanas) del mapa sin lo que cae en una sala sellada
    (salas_selladas.py: ahí no se juega y se ve oscuro)."""
    sellado = getattr(mundo, "sellado", None)
    sombras = [r for r in (getattr(sellado, "sombras", None) or ()) if hasattr(r, "collidepoint")]
    clave = (id(mapa), id(sellado), len(sombras))
    guardado = _filtrados.get(clave)
    if guardado is None:
        def libre(x, y):
            return not any(r.collidepoint(x, y) for r in sombras)
        if len(_filtrados) > 8:
            _filtrados.clear()
        luces = [l for l in mapa.luces if libre(l.x, l.y)]
        sin_cable = [l for l in luces if not l.electrica]      # las que siguen en un apagón
        guardado = _filtrados[clave] = (_rejilla(luces), [b for b in mapa.brillos if libre(*b.rect.center)],
                                        [v for v in mapa.ventanas if libre(*v.rect.center)],
                                        _rejilla(sin_cable))
    return guardado


def preparar(mundo):
    """Busca las luces del mapa (una vez por mapa; ~0.1-0.2 s). Lo llama la
    carga de la partida; si no, la primera vez que se dibuja."""
    if mundo is None:
        return None
    clave = (getattr(mundo, "nombre_mapa", None), mundo.ancho, mundo.alto)
    if clave not in _mapas:
        _mapas[clave] = LucesDelMapa(mundo)
        preparar_pantallas()
    return _mapas[clave]


# -- Fuentes de luz de las cosas del juego -------------------------------------------------

COLOR_CONSOLA = (120, 150, 255)
COLOR_LISTO = (96, 210, 120)
COLOR_CAPSULA = (90, 220, 230)
COLOR_TERMINAL = (150, 120, 255)
COLOR_NEXUS = (233, 120, 200)
COLOR_ROJO = (255, 60, 50)
COLOR_SELLO = (90, 200, 255)


def _semilla(rect):
    return (rect.x * 31 + rect.y * 17) & 0xFFFF


_del_cuadro = {"clave": None, "luces": []}


def fuentes_del_juego(extras, zonas):
    """Las luces de las cosas del juego, según cómo están ahora (una vez por
    cuadro: todas las vistas usan la misma lista)."""
    # (por cuadro, no por ms: entre la primera vista y la segunda pasan unos ms)
    clave = (efectos.cuadro, id(extras.get("mision")), id(zonas), bool(extras.get("sin_luz")))
    if _del_cuadro["clave"] == clave:
        return _del_cuadro["luces"]
    luces = _armar_fuentes(extras, zonas)
    _del_cuadro["clave"], _del_cuadro["luces"] = clave, luces
    return luces


def _armar_fuentes(extras, zonas):
    luces = []
    sin_luz = bool(extras.get("sin_luz"))
    mision = extras.get("mision")
    if mision is not None and getattr(mision, "activa", True):
        for consola in getattr(mision, "consolas", ()):
            base = consola.get("base", consola["rect"])
            if consola.get("progreso", 0) >= 1:
                luces.append(Luz(base.centerx, base.top - 20, 90, COLOR_LISTO, 0.22, 0.2, 0.5,
                                 semilla=_semilla(base)))
            else:
                luces.append(Luz(base.centerx, base.top - 30, 190, COLOR_CONSOLA, 0.34, 0.18, 0.9,
                                 semilla=_semilla(base)))
        capsula = getattr(mision, "capsula", None)
        if capsula is not None:
            huida = getattr(mision, "fase", "") == "huida"
            luces.append(Luz(capsula.centerx, capsula.centery - 30, 260, COLOR_CAPSULA,
                             0.42 if huida else 0.22 + 0.2 * getattr(mision, "reparacion", 0),
                             0.35 if huida else 0.12, 1.6 if huida else 0.4, electrica=False,
                             semilla=_semilla(capsula)))
        for puerta in getattr(mision, "puertas", ()):
            if not puerta.get("abierta"):
                r = puerta["rect"]
                luces.append(Luz(r.centerx, r.top - 10, 80, puerta.get("color", (220, 80, 80)), 0.35, 0.3, 1.0,
                                 semilla=_semilla(r)))
    for t in extras.get("terminales", ()) or ():
        r = t["rect"]
        recarga = t.get("recarga_ms", 0) > 0
        luces.append(Luz(r.centerx, r.top - 10, 110, (255, 170, 60) if recarga else COLOR_TERMINAL,
                         0.16 if recarga else 0.26, 0.2, 0.8, semilla=_semilla(r)))
    for zona in zonas or ():
        if str(zona.get("clave", "")).startswith("nexus") and not zona.get("desconectada"):
            r = zona["rect"]
            luces.append(Luz(r.centerx, r.centery - 30, 150, COLOR_NEXUS, 0.26, 0.2, 0.7, semilla=_semilla(r)))
    eventos = extras.get("eventos")
    for caja in getattr(eventos, "cajas", ()) if eventos is not None else ():
        r = caja["rect"]
        if eventos.apagon and caja is eventos.caja:
            luces.append(Luz(r.centerx, r.centery, 170, COLOR_ROJO, 0.55, 0.0, 0, electrica=False,
                             semilla=_semilla(r), emergencia=True))
        elif not eventos.apagon:
            luces.append(Luz(r.centerx, r.centery, 50, COLOR_LISTO, 0.18, 0.1, 0.5, semilla=_semilla(r)))
    for p in extras.get("paneles", ()) or ():
        r = p["rect"]
        if p.get("reparado"):
            luces.append(Luz(r.centerx, r.centery - 10, 80, COLOR_SELLO, 0.2, 0.2, 0.7, semilla=_semilla(r)))
        else:
            luces.append(Luz(r.centerx, r.centery - 20, 90, (255, 160, 60), 0.3, 0.1, 1.0, falla=0.6,
                             semilla=_semilla(r)))
        sello = p.get("sello_rect")
        if sello is not None and p.get("sello_on"):
            largo = max(sello.w, sello.h)
            for k in (0.25, 0.75):
                x = sello.x + sello.w * (k if sello.w >= sello.h else 0.5)
                y = sello.y + sello.h * (k if sello.h > sello.w else 0.5)
                luces.append(Luz(x, y, max(60, largo * 0.6), COLOR_SELLO, 0.32, 0.25, 2.0, electrica=False,
                                 semilla=_semilla(sello) + int(k * 10)))
    for puerta in extras.get("puertas_dobles", ()) or ():
        if puerta.get("abierta"):
            continue
        for i, panel in enumerate(puerta.get("paneles", ())):
            ocupado = puerta.get("en_panel", [None, None])[i] is not None
            luces.append(Luz(panel.centerx, panel.centery, 70, (255, 214, 64) if ocupado else COLOR_ROJO,
                             0.3, 0.45 if not ocupado else 0.1, 1.0, semilla=_semilla(panel)))
    for compuerta in extras.get("compuertas", ()) or ():
        if compuerta.get("cerrada"):
            r = compuerta["rect"]
            luces.append(Luz(r.centerx, r.centery, 160, COLOR_ROJO, 0.4, 0.5, 1.7, electrica=False,
                             semilla=_semilla(r), emergencia=True))
    for senuelo in extras.get("senuelos", ()) or ():
        x, y = senuelo["pos"]
        luces.append(Luz(x, y, 130, (255, 170, 50), 0.35, 0.4, 2.5, electrica=False, semilla=int(x + y),
                         emergencia=True))
    for senal in extras.get("senales", ()) or ():
        x, y = senal["pos"]
        luces.append(Luz(x, y, 150, (255, 90, 170), 0.35, 0.4, 2.0, electrica=False, semilla=int(x * 3 + y),
                         emergencia=True))
    planta = getattr(extras.get("guardia_planta"), "planta", None)
    if planta is not None and planta.get("crecida") and planta.get("fruta"):
        r = planta["rect"]
        luces.append(Luz(r.centerx, r.centery - 30, 110, (255, 150, 60), 0.3, 0.3, 1.0, electrica=False,
                         semilla=_semilla(r)))
    if sin_luz:
        luces = [l for l in luces if not l.electrica]
    return luces


def _niveles_de(radio, color, maximo=1.0):
    """Arma los degradados de (radio, color) hasta la intensidad `maximo` (la
    más alta a la que llega esa luz: intensidad x (1 + pulso); ninguna pasa de
    ahí, así que los niveles de arriba no se usan nunca)."""
    radio = max(10, int(radio) // 10 * 10)
    niveles = NIVELES_GRANDE if radio >= 200 else NIVELES
    for nivel in range(1, max(1, min(niveles, int(round(maximo * niveles)))) + 1):
        _mancha(radio, tuple(color), nivel, niveles)


# Luces de las cosas del juego que dependen de cómo están (una consola ya
# apagada, una compuerta bajada, la caja buena en un apagón, un señuelo...):
# no salen al empezar, pero se preparan igual. (radio, color) como en
# `_armar_fuentes`.
LUCES_QUE_PUEDEN_SALIR = [      # (radio, color, la intensidad más alta: intensidad x (1 + pulso))
    (90, COLOR_LISTO, 0.27), (190, COLOR_CONSOLA, 0.41), (110, (255, 170, 60), 0.2),
    (110, COLOR_TERMINAL, 0.32), (150, COLOR_NEXUS, 0.32), (170, COLOR_ROJO, 0.55), (50, COLOR_LISTO, 0.2),
    (80, COLOR_SELLO, 0.24), (90, (255, 160, 60), 0.33), (70, (255, 214, 64), 0.33), (70, COLOR_ROJO, 0.44),
    (160, COLOR_ROJO, 0.6), (130, (255, 170, 50), 0.49), (150, (255, 90, 170), 0.49),
    (110, (255, 150, 60), 0.39), (80, (220, 80, 80), 0.46),
]


def precalentar(extras, zonas, mundo=None):
    """Arma ya los degradados de todas las luces que pueden salir en esta
    partida (del mapa y de las cosas, en todos sus niveles). Lo llama la carga
    de la partida: si no, el cuadro en que aparece una luz nueva (al sonar la
    alarma, al bajar una compuerta, en un apagón) tardaba unos ms de más."""
    if not efectos.ACTIVOS:
        return
    maximos = {}

    def anotar(radio, color, maximo):
        clave = (max(10, int(radio) // 10 * 10), tuple(color))
        maximos[clave] = max(maximos.get(clave, 0.0), maximo)

    mapa = preparar(mundo) if mundo is not None else None
    for luz in (mapa.luces if mapa is not None else []) + _armar_fuentes(extras, zonas):
        anotar(luz.radio, luz.color, luz.intensidad * (1 + luz.pulso))
    for p in extras.get("paneles", ()) or ():
        sello = p.get("sello_rect")
        if sello is not None:
            anotar(max(60, max(sello.w, sello.h) * 0.6), COLOR_SELLO, 0.32 * 1.25)
    mision = extras.get("mision")
    for puerta in getattr(mision, "puertas", ()) if mision is not None else ():
        anotar(80, puerta.get("color", (220, 80, 80)), 0.35 * 1.3)
    if mision is not None and getattr(mision, "capsula", None) is not None:
        anotar(260, COLOR_CAPSULA, 0.42 * 1.35)                 # (la huida)
    for radio, color, maximo in LUCES_QUE_PUEDEN_SALIR:
        anotar(radio, color, maximo)
    for (radio, color), maximo in maximos.items():
        _niveles_de(radio, color, maximo)
    for nivel in range(1, 5):                     # la baliza de la alarma
        _franja(ALTO_FRANJA, ANCHO_FRANJA, (14 * nivel, 2 * nivel, nivel))


# -- Dibujo ---------------------------------------------------------------------------------

def dibujar(screen, vista, camara, offset, dueño, extras, zonas, mundo, tiempo_ms):
    """Las manchas de luz de color de esta vista (encima de la oscuridad)."""
    if not efectos.ACTIVOS:
        return
    mapa = preparar(mundo)
    apagon = bool(extras.get("oscuridad"))
    sin_luz = bool(extras.get("sin_luz")) or apagon
    luces = fuentes_del_juego(extras, zonas)
    if mapa is not None:
        filtrado = _del_mapa(mapa, mundo)
        rejilla = filtrado[3] if sin_luz else filtrado[0]
        luces = list(_cerca(rejilla, camara, 340)) + luces
    for luz in luces:
        r = luz.radio
        if not (camara.x - r < luz.x < camara.right + r and camara.y - r < luz.y < camara.bottom + r):
            continue
        brillo = oscuridad.brillo_en(vista, dueño, (luz.x, luz.y))
        if brillo is None:
            brillo = 1.0
        if apagon:
            # A oscuras las luces que siguen prendidas se ven igual (son lo único
            # que alumbra); las que no son de emergencia, tenues.
            brillo = 1.0 if luz.emergencia else max(brillo, 0.35)
        _pegar_luz(screen, luz, offset, tiempo_ms, brillo)


def dibujar_brillos(screen, offset, camara, mundo, extras, tiempo_ms):
    """Pantallas y tubos del mapa que titilan; lámparas que fallan (antes de la
    oscuridad: son parte del mapa)."""
    if not efectos.ACTIVOS or extras.get("oscuridad"):
        return          # (en un apagón la oscuridad los tapa igual: no se gasta en ellos)
    mapa = preparar(mundo)
    if mapa is None or not mapa.brillos:
        return
    sin_luz = bool(extras.get("sin_luz")) or bool(extras.get("oscuridad"))
    for b in _del_mapa(mapa, mundo)[1]:
        if not b.rect.colliderect(camara):
            continue
        pos = (b.rect.x - offset[0], b.rect.y - offset[1])
        if sin_luz and b.electrica:
            screen.blit(b.nivel(1.0), pos, special_flags=pygame.BLEND_RGB_SUB)     # apagadas
            continue
        if b.modo == "lampara":
            f = factor_falla(tiempo_ms, b.semilla, b.falla)
            if f < 0.3:
                screen.blit(b.nivel(0.85), pos, special_flags=pygame.BLEND_RGB_SUB)
            elif f < 0.8:
                screen.blit(b.nivel(0.4), pos, special_flags=pygame.BLEND_RGB_SUB)
            continue
        if b.modo == "respira":
            k = 0.3 + 0.3 * math.sin(tiempo_ms / 1000 * 2 * math.pi * 0.5 + b.semilla)
            screen.blit(b.nivel(k), pos, special_flags=pygame.BLEND_RGB_ADD)
            continue
        # "titila": respira rápido, a veces un golpe más brillante, y una
        # línea de barrido que baja.
        k = 0.12 + 0.1 * math.sin(tiempo_ms / 140 + b.semilla)
        if _ruido(int(tiempo_ms // 90), b.semilla) < 0.06:
            k += 0.3
        screen.blit(b.nivel(k), pos, special_flags=pygame.BLEND_RGB_ADD)
        _barrido(screen, b.nivel(0.6), pos, tiempo_ms, b.semilla)


def _barrido(screen, capa, pos, tiempo_ms, semilla, alto_linea=6, periodo=2200):
    """Una franja brillante que baja por los píxeles de `capa`."""
    h = capa.get_height()
    y = int(((tiempo_ms + semilla * 97) % periodo) / periodo * (h + alto_linea)) - alto_linea
    franja = pygame.Rect(0, max(0, y), capa.get_width(), alto_linea)
    franja = franja.clip(capa.get_rect())
    if franja.h > 0:
        screen.blit(capa, (pos[0], pos[1] + franja.y), franja, special_flags=pygame.BLEND_RGB_ADD)


def dibujar_fondo(screen, offset, camara, mundo, tiempo_ms):
    """Estrellas que pasan detrás de los ventanales (encima del mapa, debajo
    de todo lo demás)."""
    if not efectos.ACTIVOS:
        return
    mapa = preparar(mundo)
    if mapa is None:
        return
    for v in _del_mapa(mapa, mundo)[2]:
        if not v.rect.colliderect(camara):
            continue
        r = v.rect.move(-offset[0], -offset[1])
        recorte = screen.get_clip()
        screen.set_clip(r.clip(recorte))
        velocidades = (0.004, 0.010, 0.022)        # px por ms de cada capa
        for fx, y, capa, fase in v.estrellas:
            x = r.x + ((fx * r.w - tiempo_ms * velocidades[capa]) % r.w)
            brillo = (0.45, 0.7, 1.0)[capa] * (0.65 + 0.35 * math.sin(tiempo_ms / 300 + fase))
            c = int(235 * brillo)
            color = (c, c, min(255, c + 20))
            if capa == 2:
                pygame.draw.line(screen, color, (x, r.y + y), (x + 3, r.y + y), 2)
            else:
                screen.set_at((int(x), int(r.y + y)), color)
                if capa == 1:
                    screen.set_at((int(x) + 1, int(r.y + y)), color)
        # Una estrella fugaz cada tanto (~cada 7 s por ventanal).
        ciclo = 7000
        n, dentro = divmod(tiempo_ms + v.semilla * 911, ciclo)
        if dentro < 650 and _ruido(int(n), v.semilla) < 0.7:
            t = dentro / 650
            x0 = r.x + r.w * (0.15 + 0.7 * _ruido(int(n), v.semilla + 1))
            y0 = r.y + r.h * 0.2
            x = x0 - t * r.w * 0.5
            y = y0 + t * r.h * 0.6
            pygame.draw.line(screen, (255, 255, 255), (x, y), (x + 18, y - 8), 2)
            pygame.draw.line(screen, (140, 160, 220), (x + 18, y - 8), (x + 34, y - 15), 1)
        screen.set_clip(recorte)


# -- Pantallas de los sprites (consolas, terminales) ------------------------------------------

_pantallas = {}


def _datos_pantalla(img):
    """Los píxeles de pantalla (claros y azulados) de `img`, una vez por imagen."""
    if img in _pantallas:
        return _pantallas[img]
    if len(_pantallas) > 200:
        _pantallas.clear()
    capa = pygame.Surface(img.get_size())
    capa.fill((0, 0, 0))
    hay = False
    for y in range(img.get_height()):
        for x in range(img.get_width()):
            c = img.get_at((x, y))
            if c[3] > 200 and _es_brillante(c[0], c[1], c[2]) and c[2] >= c[0]:
                capa.set_at((x, y), c[:3])
                hay = True
    datos = _pantallas[img] = (Brillo(capa.get_rect(), capa, "titila", 0) if hay else None)
    return datos


def preparar_pantallas():
    """Las de las consolas y terminales, antes de empezar (si no, la primera
    vez que se ve una el cuadro tarda ~20-30 ms)."""
    try:
        from juego import sprites_objetos
        for clave in ("consola", "terminal", "nexus"):
            img = sprites_objetos.sprite(clave, sprites_objetos.ALTOS[clave])
            if img is not None:
                _datos_pantalla(img)
    except (KeyError, AttributeError, pygame.error):
        pass


def pantalla(screen, img, pos, tiempo_ms, semilla=0):
    """Hace titilar los píxeles brillantes de `img` (la consola o la terminal
    que se acaba de dibujar en `pos`) y les pasa una línea de barrido."""
    if not efectos.ACTIVOS or img is None:
        return
    datos = _datos_pantalla(img)
    if datos is None:
        return
    k = 0.1 + 0.08 * math.sin(tiempo_ms / 120 + semilla)
    if _ruido(int(tiempo_ms // 80), semilla) < 0.05:
        k += 0.25
    screen.blit(datos.nivel(k), pos, special_flags=pygame.BLEND_RGB_ADD)
    _barrido(screen, datos.nivel(0.5), pos, tiempo_ms, semilla, alto_linea=4, periodo=1800)


# -- Alarma ---------------------------------------------------------------------------------

_franjas = {}
_solidos = {}


def _solido(tamano, color):
    clave = (tamano, color)
    img = _solidos.get(clave)
    if img is None:
        if len(_solidos) > 30:
            _solidos.clear()
        img = pygame.Surface(tamano)
        img.fill(color)
        _solidos[clave] = img
    return img


ANCHO_FRANJA = 220
ALTO_FRANJA = 64


def _franja(alto, ancho, color):
    clave = (alto, ancho, color)
    img = _franjas.get(clave)
    if img is None:
        if len(_franjas) > 12:
            _franjas.clear()
        chico = pygame.Surface((32, 4))
        chico.fill((0, 0, 0))
        for x in range(32):
            v = math.sin(math.pi * x / 31) ** 2
            pygame.draw.line(chico, tuple(int(c * v) for c in color), (x, 0), (x, 3))
        img = pygame.transform.smoothscale(chico, (ancho, alto))
        _franjas[clave] = img
    return img


TINTE_ALARMA = (255, 192, 186)
TINTE_CIERRE = (255, 236, 205)


def tinte_alarma(eventos):
    """El color con que se tiñe la vista durante la alarma (rojo) o el cierre
    de emergencia (ámbar), o None. Lo multiplica la oscuridad en su mapa de
    luz (oscuridad.dibujar(..., tinte=)): no cuesta nada por cuadro."""
    if not efectos.ACTIVOS or eventos is None:
        return None
    if eventos.activo == "alarma":
        return TINTE_ALARMA
    if eventos.activo == "compuerta":
        return TINTE_CIERRE
    return None


def dibujar_alarma(screen, vista, eventos, tiempo_ms, tenido=False):
    """Luces de emergencia mientras dura la alarma: el tinte rojo (si la
    oscuridad no lo puso ya: `tenido`) y la baliza que gira, una franja de luz
    que barre de lado a lado y late. El cierre de emergencia, solo el tinte.

    (Antes además se pegaba el tinte y unos bordes encendidos del tamaño de la
    vista en cada cuadro: ~0.5 ms por vista aquí, unas 3 veces eso en el PC de
    Diego, y se notaba al sonar la alarma.)"""
    tinte = tinte_alarma(eventos)
    if tinte is None:
        return
    if not tenido:
        screen.blit(_solido(vista.size, tinte), vista.topleft, special_flags=pygame.BLEND_RGB_MULT)
    if eventos.activo != "alarma":
        return
    latido = 0.5 + 0.5 * math.sin(tiempo_ms / 1000 * 2 * math.pi * 1.4)
    nivel = 1 + round(latido * 3)                       # 1..4: brillo de la franja
    ancho = ANCHO_FRANJA
    periodo = 1600
    t = (tiempo_ms % periodo) / periodo
    x = vista.x - ancho + int((vista.width + ancho) * t)
    # (un pedazo de tamaño fijo, pegado hacia abajo: se prepara en la carga y
    # no depende del tamaño de la vista)
    franja = _franja(ALTO_FRANJA, ancho, (14 * nivel, 2 * nivel, nivel))
    for y in range(vista.y, vista.bottom, ALTO_FRANJA):
        screen.blit(franja, (x, y), special_flags=pygame.BLEND_RGB_ADD)
