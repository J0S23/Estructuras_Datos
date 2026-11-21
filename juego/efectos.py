"""Efectos visuales de la partida: lo que hace que se sienta viva.

Todo sale del ESTADO que ya se dibuja (no de la lógica del juego), así que
vale igual en el modo local y en el cliente de red (cliente_servidor/espejo.py
dibuja con las mismas funciones): si una pieza pasa a "recogida", aquí se ve
el destello, la haya recogido este proceso o el servidor.

- **Sombras** suaves bajo jugadores, prisioneros y aliens (`sombra`).
- **Contorno** del color del rol de cada jugador (`contorno`), para saber
  quién es quién con 3-4 en pantalla dividida.
- **Partículas** en coordenadas del mundo (`Particula`): chispas de los
  paneles rotos, destellos al recoger algo / apagar una consola / reparar,
  polvo cuando cae una compuerta y el que flota en la luz de la linterna en
  un apagón.
- **Huellas** que se borran solas detrás de quien camina normal (en sigilo no
  deja: se ve que la tecla sirve).
- **Puertas que se mueven** (`apertura`): la puerta para dos y la del código
  se abren deslizándose; la compuerta baja (y sube) en vez de aparecer, y al
  golpear el piso levanta polvo y sacude la cámara de quien está cerca
  (`temblor`).

Una vez por cuadro `tick(extras, jugadores)` (lo llama
screens/partida.render_partida) mira qué cambió y mueve todo; cada vista
dibuja lo suyo (`dibujar_piso`, `dibujar_particulas`, `dibujar_polvo`).
Pausa / Menú > Opciones > "Efectos visuales" los apaga (`ACTIVOS`), por si un
PC no da abasto; se guarda en Guardado/opciones.json. Con la variable de
entorno NEXUS_SIN_EFECTOS (las pruebas de red que comparan el cliente con el
modo local píxel a píxel) arrancan apagados.
"""

import json
import math
import os
import random

import pygame

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_OPCIONES = os.path.join(_RAIZ, "Guardado", "opciones.json")

ACTIVOS = not os.environ.get("NEXUS_SIN_EFECTOS")


def cargar_preferencia():
    """Lee "efectos" de Guardado/opciones.json (si no está, prendidos). Las
    pruebas (sin ventana) no la leen."""
    global ACTIVOS
    if os.environ.get("SDL_VIDEODRIVER") == "dummy" or os.environ.get("NEXUS_SIN_EFECTOS"):
        return
    try:
        with open(RUTA_OPCIONES, encoding="utf-8") as f:
            ACTIVOS = bool(json.load(f).get("efectos", True))
    except (OSError, ValueError, AttributeError):
        pass


def cambiar(activos):
    """Prende o apaga los efectos y lo guarda (Opciones)."""
    global ACTIVOS
    ACTIVOS = bool(activos)
    limpiar()
    if os.environ.get("SDL_VIDEODRIVER") == "dummy":
        return
    try:
        datos = {}
        if os.path.exists(RUTA_OPCIONES):
            with open(RUTA_OPCIONES, encoding="utf-8") as f:
                datos = json.load(f)
        datos["efectos"] = ACTIVOS
        os.makedirs(os.path.dirname(RUTA_OPCIONES), exist_ok=True)
        with open(RUTA_OPCIONES, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    except (OSError, ValueError):
        pass


def _mezclar(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# -- Sombras -----------------------------------------------------------------------------

_sombras = {}


def _sombra_img(ancho, alto, alfa):
    clave = (ancho, alto, alfa)
    img = _sombras.get(clave)
    if img is None:
        # Elipses del borde (tenue) al centro (más oscuro): borde difuso.
        img = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        pasos = 7
        for k in range(pasos):
            t = k / (pasos - 1)
            r = pygame.Rect(0, 0, max(2, int(ancho * (1 - 0.55 * t))), max(2, int(alto * (1 - 0.55 * t))))
            r.center = (ancho // 2, alto // 2)
            pygame.draw.ellipse(img, (6, 6, 14, int(alfa * (0.25 + 0.75 * t))), r)
        _sombras[clave] = img
    return img


def sombra(screen, pies, ancho, alfa=120):
    """Sombra suave en el piso, centrada en `pies` (coordenadas de pantalla).
    Sin efectos, la elipse oscura de siempre."""
    ancho = max(12, int(ancho))
    alto = max(6, int(ancho * 0.34))
    if not ACTIVOS:
        r = pygame.Rect(0, 0, int(ancho * 0.8), max(6, int(alto * 0.75)))
        r.center = pies
        pygame.draw.ellipse(screen, (10, 12, 20), r)
        return
    screen.blit(_sombra_img(ancho, alto, alfa), (int(pies[0] - ancho / 2), int(pies[1] - alto / 2)))


# -- Contorno del color del jugador ------------------------------------------------------

_contornos = {}
GROSOR_CONTORNO = 2


def contorno(screen, img, pos, color):
    """Pega el contorno de `img` (un cuadro del personaje) del color dado, para
    dibujar el personaje encima. Guardado por cuadro y color."""
    if not ACTIVOS or img is None:
        return
    datos = _contornos.get((img, color), False)
    if datos is False:
        datos = _armar_contorno(img, color)
    if datos is not None:
        screen.blit(datos[0], (pos[0] + datos[1][0], pos[1] + datos[1][1]))


def _armar_contorno(img, color):
    clave = (img, color)
    if len(_contornos) > 5000:
        _contornos.clear()
    caja = img.get_bounding_rect(min_alpha=90)
    if caja.w == 0 or caja.h == 0:
        _contornos[clave] = None
        return None
    g = GROSOR_CONTORNO
    recorte = img.subsurface(caja)
    mascara = pygame.mask.from_surface(recorte, 90)
    silueta = mascara.to_surface(setcolor=(*color, 255), unsetcolor=(0, 0, 0, 0))
    borde = pygame.Surface((caja.w + 2 * g, caja.h + 2 * g), pygame.SRCALPHA)
    for dx in range(-g, g + 1):
        for dy in range(-g, g + 1):
            if dx * dx + dy * dy <= g * g + 1:
                borde.blit(silueta, (g + dx, g + dy))
    # Un poco transparente: marca, no tapa el dibujo.
    borde.fill((255, 255, 255, 215), special_flags=pygame.BLEND_RGBA_MULT)
    datos = _contornos[clave] = (borde, (caja.x - g, caja.y - g))
    return datos


def precalentar_contornos(jugadores):
    """Arma el contorno de cada cuadro de cada jugador (todas sus animaciones y
    direcciones) en la carga: si no, cada cuadro nuevo que salía (al girar, al
    empezar a caminar) costaba ~0.5 ms la primera vez (~1.5 en el PC de Diego)."""
    if not ACTIVOS:
        return
    for j in jugadores or ():
        personaje = getattr(j, "personaje", None)
        color = getattr(j, "color", None)
        if personaje is None or color is None:
            continue
        for direcciones in getattr(personaje, "animaciones", {}).values():
            for cuadros in direcciones.values():
                for img in cuadros:
                    if (img, color) not in _contornos:
                        _armar_contorno(img, color)


# -- Partículas ---------------------------------------------------------------------------

class Particula:
    __slots__ = ("x", "y", "vx", "vy", "vida", "total", "color", "tam", "gravedad", "roce", "estela", "brilla")

    def __init__(self, x, y, vx, vy, vida, color, tam=2.0, gravedad=0.0, roce=0.0, estela=False, brilla=True):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.vida = self.total = vida
        self.color, self.tam, self.gravedad, self.roce, self.estela = color, tam, gravedad, roce, estela
        self.brilla = brilla          # False: polvo (se mezcla, no se suma)


class Anillo:
    __slots__ = ("x", "y", "vida", "total", "color", "radio")

    def __init__(self, x, y, color, radio=60, vida=500):
        self.x, self.y, self.color, self.radio = x, y, color, radio
        self.vida = self.total = vida


MAX_PARTICULAS = 500

_particulas = []
_anillos = []
_huellas = []            # [x, y, angulo, ms de vida, lado]
_impactos = []           # [x, y, ms de vida, fuerza]
_azar = random.Random()

# Estado visto el cuadro anterior: (clase, x, y) -> valor.
_antes = {}
_aperturas = {}          # (clase, x, y) -> 0 (cerrada) .. 1 (abierta)
_pasos = {}              # id del jugador -> (x, y, lado) de la última huella
_ultimo_ms = None
cuadro = 0               # cuántas veces corrió tick (lo que se arma una vez por cuadro lo usa de clave)
_chispas_ms = {}         # (x, y) del panel -> ms para la próxima chispa
_polvo = {}              # id del dueño -> [motas]


def limpiar():
    """Borra todo lo que está en el aire (otra partida, efectos apagados)."""
    global _ultimo_ms
    _particulas.clear()
    _anillos.clear()
    _huellas.clear()
    _impactos.clear()
    _antes.clear()
    _aperturas.clear()
    _pasos.clear()
    _chispas_ms.clear()
    _polvo.clear()
    _ultimo_ms = None


def _agregar(p):
    if len(_particulas) < MAX_PARTICULAS:
        _particulas.append(p)


def destello(x, y, color, cantidad=22, fuerza=1.0, anillo=True):
    """Chispitas que salen hacia afuera y un anillo que se agranda (recoger algo,
    apagar una consola, reparar)."""
    if not ACTIVOS:
        return
    claro = _mezclar(color, (255, 255, 255), 0.45)
    for _ in range(cantidad):
        a = _azar.uniform(0, 2 * math.pi)
        v = _azar.uniform(0.05, 0.22) * fuerza
        _agregar(Particula(x, y, math.cos(a) * v, math.sin(a) * v - 0.05 * fuerza,
                           _azar.uniform(380, 800), claro if _azar.random() < 0.5 else color,
                           _azar.uniform(1.5, 3.2), gravedad=0.00012, roce=0.0025))
    if anillo:
        _anillos.append(Anillo(x, y, color, radio=int(70 * fuerza), vida=520))


def chispas(x, y, cantidad=7):
    """Chispas de un panel roto: saltan, caen y dejan estela."""
    if not ACTIVOS:
        return
    for _ in range(cantidad):
        a = _azar.uniform(-math.pi * 0.95, -math.pi * 0.05)        # hacia arriba
        v = _azar.uniform(0.12, 0.34)
        color = _azar.choice(((255, 236, 150), (255, 200, 90), (255, 255, 220), (255, 170, 60)))
        _agregar(Particula(x + _azar.uniform(-6, 6), y, math.cos(a) * v, math.sin(a) * v,
                           _azar.uniform(260, 620), color, _azar.uniform(1.2, 2.2),
                           gravedad=0.0011, roce=0.0008, estela=True))


def polvareda(rect, cantidad=26, color=(160, 156, 170)):
    """Polvo que levanta algo pesado al golpear el piso (la compuerta)."""
    if not ACTIVOS:
        return
    for _ in range(cantidad):
        x = _azar.uniform(rect.left, rect.right)
        y = rect.bottom - _azar.uniform(0, 6)
        a = _azar.uniform(-math.pi, 0)
        v = _azar.uniform(0.03, 0.12)
        _agregar(Particula(x, y, math.cos(a) * v * 1.6, math.sin(a) * v * 0.6,
                           _azar.uniform(500, 1100), color, _azar.uniform(2.5, 5.0),
                           gravedad=-0.00002, roce=0.002, brilla=False))


def golpe(x, y, fuerza=7.0):
    """Algo pesado cayó en (x, y): sacude la cámara de quien está cerca."""
    if ACTIVOS:
        _impactos.append([x, y, 380, fuerza])


DISTANCIA_TEMBLOR = 700


def temblor(dueño):
    """(dx, dy) para la cámara de `dueño` por los golpes recientes cerca suyo."""
    if not _impactos or dueño is None:
        return (0, 0)
    cx, cy = dueño.hitbox.center
    amp = 0.0
    fase = 0.0
    for x, y, vida, fuerza in _impactos:
        d = math.hypot(x - cx, y - cy)
        if d >= DISTANCIA_TEMBLOR:
            continue
        a = fuerza * (vida / 380) * (1 - d / DISTANCIA_TEMBLOR)
        if a > amp:
            amp, fase = a, vida
    if amp < 0.5:
        return (0, 0)
    return (int(round(math.sin(fase / 23) * amp)), int(round(math.cos(fase / 17) * amp * 0.7)))


# -- Lo que cambió desde el cuadro anterior -------------------------------------------------

def _cambio(clase, rect, valor):
    """True la primera vez que (clase, rect) pasa a `valor` (y no la primera
    vez que se ve: al empezar no salta nada)."""
    clave = (clase, rect.x, rect.y)
    previo = _antes.get(clave)
    _antes[clave] = valor
    return previo is not None and previo != valor and valor


def _abrir_suave(clase, rect, abierta, dt, ms_abrir=650, ms_cerrar=650):
    """Lleva la apertura de (clase, rect) hacia 1 (abierta) o 0 (cerrada)."""
    clave = (clase, rect.x, rect.y)
    actual = _aperturas.get(clave)
    objetivo = 1.0 if abierta else 0.0
    if actual is None:
        actual = objetivo                         # la primera vez, como está
    elif actual < objetivo:
        actual = min(objetivo, actual + dt / ms_abrir)
    elif actual > objetivo:
        actual = max(objetivo, actual - dt / ms_cerrar)
    _aperturas[clave] = actual
    return actual


def apertura(clase, rect, abierta):
    """0 = cerrada, 1 = abierta, en medio = moviéndose (lo lleva `tick`).
    Sin efectos (o si `tick` no la vio), lo que diga el estado."""
    if not ACTIVOS:
        return 1.0 if abierta else 0.0
    return _aperturas.get((clase, rect.x, rect.y), 1.0 if abierta else 0.0)


def tick(extras, jugadores):
    """Una vez por cuadro: ve qué cambió en el estado y mueve partículas,
    huellas, puertas y golpes."""
    global _ultimo_ms, cuadro
    if not ACTIVOS:
        return
    cuadro += 1
    ahora = pygame.time.get_ticks()
    dt = 0 if _ultimo_ms is None else min(60, max(0, ahora - _ultimo_ms))
    _ultimo_ms = ahora
    extras = extras or {}
    _mover(dt)
    if dt <= 0:
        return
    _revisar_estado(extras, dt)
    _huellas_de(jugadores, dt)
    _chispas_de_paneles(extras, jugadores, dt)
    _motas(jugadores, extras, dt)


def _mover(dt):
    if dt <= 0:
        return
    vivas = []
    for p in _particulas:
        p.vida -= dt
        if p.vida <= 0:
            continue
        p.vy += p.gravedad * dt
        if p.roce:
            f = max(0.0, 1 - p.roce * dt)
            p.vx *= f
            p.vy *= f
        p.x += p.vx * dt
        p.y += p.vy * dt
        vivas.append(p)
    _particulas[:] = vivas
    _anillos[:] = [a for a in _anillos if _restar(a, dt) > 0]
    vivas = []
    for h in _huellas:
        h[3] -= dt
        if h[3] > 0:
            # (la imagen que le toca, ya escogida: dibujar_piso solo pega)
            nivel = max(1, min(6, int(6 * h[3] / VIDA_HUELLA_MS) + 1))
            h[4] = _imagen_huella(int(round(h[2] / (math.pi / 8))) % 16, nivel)
            vivas.append(h)
    _huellas[:] = vivas
    for i in _impactos:
        i[2] -= dt
    _impactos[:] = [i for i in _impactos if i[2] > 0]


def _restar(cosa, dt):
    cosa.vida -= dt
    return cosa.vida


COLOR_PIEZA = (255, 170, 50)
COLOR_CONSUMIBLES = {"decodificador": (90, 160, 255), "kit": (110, 210, 140), "fruta": (255, 150, 60),
                     "abono": (150, 220, 90)}
COLOR_PRUEBA = (240, 110, 200)
COLOR_CONSOLA = (180, 110, 255)
COLOR_LISTO = (96, 210, 120)
COLOR_SELLO = (90, 200, 255)


def _revisar_estado(extras, dt):
    for pieza in extras.get("piezas", ()) or ():
        if _cambio("pieza", pieza["rect"], bool(pieza.get("recogida"))):
            destello(*pieza["rect"].center, COLOR_PIEZA)
    mision = extras.get("mision")
    if mision is not None:
        for cons in getattr(mision, "consumibles", ()):
            if _cambio("consumible", cons["rect"], bool(cons.get("tomado"))):
                destello(*cons["rect"].center, COLOR_CONSUMIBLES.get(cons.get("tipo"), (240, 240, 255)))
        for consola in getattr(mision, "consolas", ()):
            base = consola.get("base", consola["rect"])
            if _cambio("consola", base, consola.get("progreso", 0) >= 1):
                destello(base.centerx, base.top - 30, COLOR_LISTO, cantidad=30, fuerza=1.3)
        capsula = getattr(mision, "capsula", None)
        if capsula is not None:
            entregadas = getattr(mision, "piezas_entregadas", 0)
            clave = ("entregadas", capsula.x, capsula.y)
            previo = _antes.get(clave)
            _antes[clave] = entregadas
            if previo is not None and entregadas > previo:
                destello(*capsula.center, COLOR_PIEZA, cantidad=34, fuerza=1.5)
            if _cambio("huida", capsula, getattr(mision, "fase", "") == "huida"):
                destello(*capsula.center, (90, 220, 230), cantidad=60, fuerza=2.2)
        for puerta in getattr(mision, "puertas", ()):
            _abrir_suave("puerta_codigo", puerta["rect"], bool(puerta.get("abierta")), dt, 700)
            if _cambio("puerta_codigo", puerta["rect"], bool(puerta.get("abierta"))):
                polvareda(puerta["rect"], 16)
    caso = extras.get("infiltrado")
    for prueba in getattr(caso, "pruebas", ()) if caso is not None else ():
        if _cambio("prueba", prueba["rect"], bool(prueba.get("tomada"))):
            destello(*prueba["rect"].center, COLOR_PRUEBA)
    for panel in extras.get("paneles", ()) or ():
        if _cambio("panel", panel["rect"], bool(panel.get("reparado"))):
            destello(panel["rect"].centerx, panel["rect"].centery - 20, COLOR_SELLO, cantidad=26)
    for puerta in extras.get("puertas_dobles", ()) or ():
        _abrir_suave("puerta_doble", puerta["rect"], bool(puerta.get("abierta")), dt, 900)
        if _cambio("puerta_doble", puerta["rect"], bool(puerta.get("abierta"))):
            polvareda(puerta["rect"], 20)
            golpe(*puerta["rect"].center, 3.0)
    for compuerta in extras.get("compuertas", ()) or ():
        cerrada = bool(compuerta.get("cerrada"))
        previo = _aperturas.get(("compuerta", compuerta["rect"].x, compuerta["rect"].y))
        # La compuerta "abierta" = arriba. Baja rápido (cae) y sube lento.
        valor = _abrir_suave("compuerta", compuerta["rect"], not cerrada, dt, ms_abrir=900, ms_cerrar=260)
        if cerrada and previo is not None and previo > 0 and valor <= 0:
            # Acaba de golpear el piso.
            polvareda(compuerta["rect"], 34)
            golpe(*compuerta["rect"].center, 8.0)


DISTANCIA_HUELLA = 30         # px caminados entre huella y huella
VIDA_HUELLA_MS = 2600


def _huellas_de(jugadores, dt):
    for j in jugadores or ():
        if (getattr(j, "escondido", False) or getattr(j, "eliminado", False)
                or getattr(j, "desconectado", False) or getattr(j, "preso", None) is not None):
            _pasos.pop(id(j), None)
            continue
        x, y = j.hitbox.centerx, j.hitbox.bottom - 4
        previo = _pasos.get(id(j))
        if previo is None:
            _pasos[id(j)] = (x, y, 1)
            continue
        dx, dy = x - previo[0], y - previo[1]
        d = math.hypot(dx, dy)
        if d > 160:                       # lo movieron (celda, rescate): sin huellas
            _pasos[id(j)] = (x, y, 1)
            continue
        if d < DISTANCIA_HUELLA:
            continue
        lado = -previo[2]
        _pasos[id(j)] = (x, y, lado)
        if getattr(j, "sigilo", False):
            continue                      # en sigilo no deja huellas
        angulo = math.atan2(dy, dx)
        # Un pie a cada lado de la línea por donde camina.
        px, py = -math.sin(angulo) * 7 * lado, math.cos(angulo) * 7 * lado
        _huellas.append([x + px, y + py, angulo, VIDA_HUELLA_MS,
                         _imagen_huella(int(round(angulo / (math.pi / 8))) % 16, 6)])
    if len(_huellas) > 300:
        del _huellas[:len(_huellas) - 300]


def _chispas_de_paneles(extras, jugadores, dt):
    """Los paneles rotos (los repara el Forjador) echan chispas de vez en cuando,
    solo si hay alguien que los pueda ver."""
    if extras.get("sin_luz"):
        return
    centros = [j.hitbox.center for j in jugadores or ()]
    for panel in extras.get("paneles", ()) or ():
        if panel.get("reparado"):
            continue
        r = panel["rect"]
        if not any(abs(r.centerx - c[0]) < 1100 and abs(r.centery - c[1]) < 800 for c in centros):
            continue
        clave = (r.x, r.y)
        falta = _chispas_ms.get(clave)
        if falta is None:
            falta = _azar.uniform(0, 900)
        falta -= dt
        if falta <= 0:
            chispas(r.centerx + _azar.uniform(-12, 12), r.centery - 26, _azar.randint(4, 9))
            falta = _azar.uniform(500, 1500)
        _chispas_ms[clave] = falta


# -- Polvo en la luz de la linterna ---------------------------------------------------------

MOTAS = 32
RADIO_MOTAS = 470


def _motas(jugadores, extras, dt):
    """Motas de polvo alrededor de cada jugador (solo se ven donde hay luz:
    `dibujar_polvo` las pinta según el mapa de luz de la vista)."""
    if not extras.get("oscuridad"):
        _polvo.clear()
        return
    for j in jugadores or ():
        cx, cy = j.hitbox.center
        motas = _polvo.get(id(j))
        if motas is None:
            motas = _polvo[id(j)] = []
        while len(motas) < MOTAS:
            a, r = _azar.uniform(0, 2 * math.pi), RADIO_MOTAS * math.sqrt(_azar.random())
            motas.append([cx + math.cos(a) * r, cy + math.sin(a) * r - 40,
                          _azar.uniform(-0.012, 0.012), _azar.uniform(-0.01, 0.006),
                          _azar.uniform(0, 6.28), 1])
        for m in motas:
            m[4] += dt * 0.002
            m[0] += (m[2] + math.sin(m[4]) * 0.008) * dt
            m[1] += (m[3] + math.cos(m[4] * 0.7) * 0.006) * dt
            if abs(m[0] - cx) > RADIO_MOTAS or abs(m[1] - cy) > RADIO_MOTAS:
                # Se salió: vuelve por el otro lado.
                a, r = _azar.uniform(0, 2 * math.pi), RADIO_MOTAS * math.sqrt(_azar.random())
                m[0], m[1] = cx + math.cos(a) * r, cy + math.sin(a) * r


# -- Dibujo ---------------------------------------------------------------------------------

_puntos = {}


def _punto(color, tam, nivel):
    """Un puntito brillante (difuso) para pegar con BLEND_RGB_ADD."""
    clave = (color, tam, nivel)
    img = _puntos.get(clave)
    if img is None:
        if len(_puntos) > 2000:
            _puntos.clear()
        r = max(2, int(tam * 2.2))
        img = pygame.Surface((r * 2, r * 2))
        img.fill((0, 0, 0))
        f = nivel / 8
        for k in range(r, 0, -1):
            t = k / r
            v = (1 - t) ** 1.6 * f
            pygame.draw.circle(img, tuple(min(255, int(c * v)) for c in color), (r, r), k)
        pygame.draw.circle(img, tuple(min(255, int(c * f)) for c in _mezclar(color, (255, 255, 255), 0.6)),
                           (r, r), max(1, int(tam * 0.6)))
        _puntos[clave] = img
    return img


_nubes = {}


def _nube(color, radio, nivel):
    """Una bolita de polvo semitransparente (se agranda y se desvanece)."""
    clave = (color, radio, nivel)
    img = _nubes.get(clave)
    if img is None:
        if len(_nubes) > 600:
            _nubes.clear()
        r = max(2, radio)
        img = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        for k in range(r, 0, -1):
            t = k / r
            pygame.draw.circle(img, (*color, int(14 * nivel * (1 - t) ** 0.8)), (r, r), k)
        _nubes[clave] = img
    return img


_huella_img = {}


def _imagen_huella(angulo_idx, nivel):
    clave = (angulo_idx, nivel)
    img = _huella_img.get(clave)
    if img is None:
        base = pygame.Surface((16, 16), pygame.SRCALPHA)
        alfa = int(150 * nivel / 6)
        # Mirando a +x (hacia donde camina): el talón chico atrás y la parte
        # de adelante más ancha, separados (antes era un óvalo con una bolita
        # adelante y se leía al revés, como si la bolita fuera el talón).
        pygame.draw.ellipse(base, (14, 14, 26, alfa), (1, 5, 5, 6))         # talón
        pygame.draw.ellipse(base, (14, 14, 26, alfa), (7, 4, 8, 8))         # planta y dedos
        img = pygame.transform.rotate(base, -angulo_idx * 22.5)
        # Del mismo tamaño siempre (16x16 centrada), así dibujar_piso no mide nada.
        centrada = pygame.Surface((16, 16), pygame.SRCALPHA)
        centrada.blit(img, img.get_rect(center=(8, 8)))
        img = _huella_img[clave] = centrada
    return img


def dibujar_piso(screen, offset, camara):
    """Las huellas (en el piso, debajo de los personajes)."""
    if not ACTIVOS or not _huellas:
        return
    x0, y0, x1, y1 = camara.x, camara.y, camara.right, camara.bottom
    ox, oy = offset[0] + 8, offset[1] + 8
    for x, y, _, _, img in _huellas:
        if x0 <= x < x1 and y0 <= y < y1:
            screen.blit(img, (int(x - ox), int(y - oy)))


def dibujar_particulas(screen, offset, camara):
    """Chispas, destellos, polvo y anillos (encima de la oscuridad: brillan)."""
    if not ACTIVOS or not (_particulas or _anillos):
        return
    zona = camara.inflate(40, 40)
    for a in _anillos:
        if not zona.collidepoint(a.x, a.y) and not camara.inflate(a.radio * 2, a.radio * 2).collidepoint(a.x, a.y):
            continue
        t = 1 - a.vida / a.total
        r = int(8 + a.radio * (1 - (1 - t) ** 2))
        v = (1 - t) ** 1.5
        pygame.draw.circle(screen, tuple(int(c * v) for c in a.color),
                           (int(a.x - offset[0]), int(a.y - offset[1])), r, max(1, int(3 * (1 - t)) + 1))
    for p in _particulas:
        if not zona.collidepoint(p.x, p.y):
            continue
        vida = p.vida / p.total
        x, y = p.x - offset[0], p.y - offset[1]
        if p.estela:
            fin = (x - p.vx * 18, y - p.vy * 18)
            pygame.draw.line(screen, tuple(int(c * vida) for c in p.color), (x, y), fin, 1)
        if not p.brilla:
            img = _nube(p.color, int(p.tam + (1 - vida) * 6), max(1, min(6, int(6 * vida) + 1)))
            screen.blit(img, (int(x - img.get_width() / 2), int(y - img.get_height() / 2)))
            continue
        nivel = max(1, min(8, int(8 * vida ** 0.7) + 1))
        img = _punto(p.color, round(p.tam), nivel)
        screen.blit(img, (int(x - img.get_width() / 2), int(y - img.get_height() / 2)),
                    special_flags=pygame.BLEND_RGB_ADD)


def dibujar_polvo(screen, vista, offset, camara, dueño, mapa_luz):
    """En un apagón, motas de polvo que se ven solo donde hay luz (el cono de
    la linterna). `mapa_luz` = (mapa de luz chico de la vista, x e y de su
    esquina en el mundo, escala) de oscuridad.mapa_de_luz, o None."""
    if not ACTIVOS or mapa_luz is None:
        return
    motas = _polvo.get(id(dueño))
    if not motas:
        return
    luz_chica, zx, zy, e = mapa_luz
    ancho, alto = luz_chica.get_size()
    leer = luz_chica.get_at
    for x, y, _, _, fase, tam in motas:
        if not camara.collidepoint(x, y):
            continue
        px, py = int((x - zx) / e), int((y - zy) / e)
        if not (0 <= px < ancho and 0 <= py < alto):
            continue
        luz = leer((px, py))[0] / 255
        if luz < 0.3:
            continue
        nivel = max(1, min(5, int(6 * (luz - 0.25) * (0.5 + 0.5 * math.sin(fase * 3)))))
        img = _punto((200, 185, 150), tam, nivel)
        screen.blit(img, (int(x - offset[0] - img.get_width() / 2), int(y - offset[1] - img.get_height() / 2)),
                    special_flags=pygame.BLEND_RGB_ADD)
