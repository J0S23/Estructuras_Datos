"""Pantalla de resultados al terminar la ronda.

De arriba hacia abajo:

- el titular (escaparon o no) con POR QUÉ terminó, la dificultad y el tiempo;
- una fila de cifras grandes: puntos del equipo, piezas en la cápsula,
  logros, prisioneros rescatados y veces que los atraparon;
- a la izquierda, la tripulación: una tarjeta por jugador con su personaje,
  sus puntos, sus tareas y las habilidades que escogió (en orden de jugador:
  es un juego en equipo, no una tabla de posiciones; el que más puntos hizo
  lleva una estrella);
- a la derecha, la misión (hasta qué fase llegaron, en pasos) con el caso
  del Cambiaformas, y cómo usaron NEXUS: lo bueno en verde, lo que hay que
  mejorar en rojo, la confianza al final y un consejo;
- abajo, "Ver logros" (el árbol completo, screens/logros.py) y "Volver al
  menú". La lógica de la pantalla está en App._tecla_resultados.

Se usa igual en el modo local y en red (cliente_servidor/espejo.py).

Con los efectos prendidos (juego/efectos.py) la pantalla se arma de a poco
(`_desde`, ms desde que apareció): el titular entra (con un glitch si
perdieron), las cifras y los puntos cuentan hacia arriba, las tarjetas entran
una tras otra, la línea de la misión avanza paso a paso, la barra de NEXUS se
llena y, si hay sitio en la tripulación, las insignias de los logros de la
partida aparecen una por una. Si escaparon, caen papelitos de colores.
"""

import math

import pygame

from juego.fuentes import fuente_de_tamano
from juego.idioma import tr
from juego.mandos import botones_conectados
from juego.ui_components import Button
from juego import efectos

COLOR_FONDO = (18, 19, 36)
COLOR_PANEL = (28, 30, 54)
COLOR_PANEL_BORDE = (58, 62, 104)
COLOR_TITULO = (255, 214, 64)
COLOR_TEXTO = (245, 246, 252)
COLOR_TENUE = (160, 168, 206)
COLOR_APAGADO = (78, 82, 118)
COLOR_BARRA = (96, 200, 120)        # (nombre viejo: lo usan otras pantallas)
COLOR_BIEN = COLOR_BARRA
COLOR_BARRA_MALA = (226, 82, 74)
COLOR_MAL = COLOR_BARRA_MALA
COLOR_ROJO_NEXUS = (230, 70, 80)

MOTIVOS = {
    "escaparon": "Llegaron todos a la cápsula y escaparon de la nave.",
    "atrapados": "Los aliens los encerraron a todos.",
    "eliminados": "Se quedaron sin vidas.",
    "terminaron": "Terminaron la partida antes de escapar.",
    "imposible": "Ya no se podía escapar.",
    "tiempo": "Se acabó el tiempo.",
}
# Los pasos de la misión, en orden (misiones/mision.py).
PASOS = [("prision", "Salir de la prisión"), ("sabotaje", "Apagar consolas"),
         ("piezas", "Piezas a la cápsula"), ("reparar", "Reparar la cápsula"),
         ("huida", "Escapar")]


def opciones_resultados(logros, nexus=None):
    """(texto, acción) de los botones de abajo. "Álbum de fotos" solo si el
    equipo subió alguna (screens/album.py)."""
    from screens import album
    opciones = []
    if logros is not None:
        opciones.append((f"Ver logros  {logros.arbol.obtenidos()}/{logros.arbol.total()}", "logros"))
    fotos = len(album.fotos_del_equipo(nexus))
    if fotos:
        opciones.append((f"Álbum de fotos  {fotos}", "album"))
    opciones.append(("Volver al menú", "menu"))
    return opciones


def _paso_alcanzado(mision):
    """Hasta qué paso de PASOS llegaron (len(PASOS) = todos, escaparon)."""
    from misiones.mision import PIEZAS_NECESARIAS
    if mision.resultado == "victoria":
        return len(PASOS)
    fase = mision.fase
    if fase == "prision":
        return 0
    if fase == "sabotaje":
        return 1
    if fase == "capsula":
        return 3 if mision.piezas_entregadas >= getattr(mision, "piezas_necesarias", PIEZAS_NECESARIAS) else 2
    if fase == "huida":
        return 4
    return 0


def _motivo(mision):
    if mision is None or not mision.activa:
        return ""
    motivo = getattr(mision, "motivo_fin", None)
    if motivo == "imposible" and getattr(mision, "razon_imposible_txt", None):
        return mision.razon_imposible_txt          # (por qué: mision.razon_imposible)
    if motivo in MOTIVOS:
        return MOTIVOS[motivo]
    return MOTIVOS["escaparon"] if mision.resultado == "victoria" else ""


# -- Animación de entrada -------------------------------------------------------------

_entrada = {"clave": None, "t0": 0, "intro": 0}


def _desde(clave):
    """ms desde que apareció esta pantalla de resultados (muy grande sin efectos)."""
    if not efectos.ACTIVOS:
        return 10 ** 9
    ahora = pygame.time.get_ticks()
    if _entrada["clave"] != clave:
        _entrada["clave"], _entrada["t0"], _entrada["intro"] = clave, ahora, 0
    return ahora - _entrada["t0"]


def en_intro():
    """¿Se está viendo la escena del final sola (antes de los resultados)?"""
    return (efectos.ACTIVOS and _entrada["intro"] > 0
            and pygame.time.get_ticks() - _entrada["t0"] < _entrada["intro"])


def saltar_intro():
    """Enter, un botón o un clic durante la escena: pasa a los resultados (la
    escena sigue de fondo). Devuelve True si había escena que saltar."""
    if not en_intro():
        return False
    _entrada["t0"] = pygame.time.get_ticks() - _entrada["intro"]
    return True


def _hay_escena(mision):
    return (efectos.ACTIVOS and mision is not None and mision.activa
            and mision.resultado in ("victoria", "derrota"))


def _intro(screen, victoria, t, jugadores, titular, color, motivo):
    """La escena del final sola, con el titular y la pista para saltarla."""
    from screens import estilo, final
    ancho, alto = screen.get_size()
    final.dibujar(screen, victoria, t, jugadores)
    e = max(0.72, min(1.6, min(ancho / 1280, alto / 720)))
    aparece = _suave(t, 2600 if victoria else 1700, 700)
    if aparece > 0:
        tam = int(54 * e)
        y = int(alto * (0.13 if victoria else 0.1)) - int((1 - aparece) * 30)
        if not victoria and (t // 70) % 4 == 0 and t < 3200:
            y += 3
        rect = estilo.titulo(screen, titular, (ancho // 2, y), tam, color, color)
        if motivo and aparece >= 1:
            estilo.texto(screen, motivo, fuente_de_tamano(max(14, int(19 * e))),
                         (ancho // 2, rect.bottom + int(18 * e)), COLOR_TEXTO, "midtop")
    if t > 700:
        estilo.pie(screen, "[ENTER] ver los resultados", alto - 34)


def _suave(t, inicio, duracion):
    """0 antes de `inicio`, 1 después de inicio + duracion, frenando al final."""
    if t <= inicio:
        return 0.0
    x = min(1.0, (t - inicio) / max(1, duracion))
    return 1 - (1 - x) ** 3


def _contando(valor, k):
    """El texto de una cifra mientras cuenta: "160" -> "96", "3/3" -> "2/3"."""
    if k >= 1:
        return valor
    if "/" in valor:
        a, b = valor.split("/", 1)
        if a.isdigit():
            return f"{int(round(int(a) * k))}/{b}"
        return valor
    return str(int(round(int(valor) * k))) if valor.isdigit() else valor


COLORES_PAPELITOS = ((255, 214, 64), (96, 210, 120), (90, 200, 255), (233, 120, 200), (255, 140, 70),
                     (190, 150, 255))


def _papelitos(screen, t):
    """Papelitos que salen disparados desde abajo y caen (escaparon). Sin
    estado: la posición de cada uno sale de su semilla y del tiempo."""
    if t > 7000:
        return
    ancho, alto = screen.get_size()
    import random
    azar = random.Random(42)
    s = t / 1000
    for i in range(140):
        lado = -1 if i % 2 else 1
        x0 = ancho * (0.5 + lado * azar.uniform(0.3, 0.5))
        vx = -lado * azar.uniform(80, 420)
        vy = -azar.uniform(500, 950)
        retraso = azar.uniform(0, 0.5)
        color = azar.choice(COLORES_PAPELITOS)
        giro = azar.uniform(4, 11)
        tam = azar.randint(5, 9)
        u = s - retraso
        if u <= 0:
            continue
        # Sube con roce y cae despacito, meciéndose.
        x = x0 + vx * (1 - math.exp(-u * 1.6)) / 1.6 + math.sin(u * 2.5 + i) * 14
        y = alto + 10 + vy * (1 - math.exp(-u * 1.8)) / 1.8 + 90 * u * u * 0.5
        if y > alto + 20 or x < -20 or x > ancho + 20:
            continue
        ancho_p = max(1, int(abs(math.cos(u * giro + i)) * tam))
        pygame.draw.rect(screen, color, (int(x), int(y), ancho_p, max(2, tam // 2)))


def _tiempo(ms):
    s = int((ms or 0) // 1000)
    return f"{s // 60}:{s % 60:02d}"


_vidrios = {}


def _caja(screen, rect):
    """El fondo de un recuadro: un poco transparente (detrás está la escena
    del final, screens/final.py)."""
    img = _vidrios.get(rect.size)
    if img is None:
        if len(_vidrios) > 30:
            _vidrios.clear()
        img = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(img, (*COLOR_PANEL, 222), img.get_rect(), border_radius=12)
        _vidrios[rect.size] = img
    screen.blit(img, rect.topleft)


def _panel(screen, rect, titulo=None, f_titulo=None, color=COLOR_TITULO):
    """Un recuadro con su título; devuelve la y donde empieza el contenido."""
    _caja(screen, rect)
    pygame.draw.rect(screen, COLOR_PANEL_BORDE, rect, 2, border_radius=12)
    if not titulo:
        return rect.y + 12
    img = f_titulo.render(titulo, True, color)
    screen.blit(img, (rect.x + 16, rect.y + 10))
    return rect.y + 10 + img.get_height() + 8


def _texto(screen, texto, f, x, y, ancho, color):
    """Una línea que se encoge si no cabe (y si ni así, se corta con "...");
    devuelve su alto."""
    texto = tr(texto)
    if f.size(texto)[0] > ancho:
        minimo = max(10, int(f.get_height() * 0.7))
        for px in range(f.get_height(), minimo - 1, -1):
            f = fuente_de_tamano(px)
            if f.size(texto)[0] <= ancho:
                break
        while len(texto) > 4 and f.size(texto)[0] > ancho:
            texto = texto[:-4].rstrip() + "..."
    img = f.render(texto, True, color)
    screen.blit(img, (x, y))
    return img.get_height()


def _fondo(screen, color_titular, t=0):
    ancho, alto = screen.get_size()
    screen.fill(COLOR_FONDO)
    # Un degradado del color del final (verde o rojo) que baja desde arriba.
    alto_brillo = int(alto * 0.32)
    brillo = pygame.Surface((ancho, alto_brillo), pygame.SRCALPHA)
    for fila in range(0, alto_brillo, 2):
        a = int(46 * (1 - fila / alto_brillo) ** 2)
        pygame.draw.rect(brillo, (*color_titular, a), (0, fila, ancho, 2))
    screen.blit(brillo, (0, 0))
    # Unas estrellas (siempre las mismas; con efectos, pasan lento y titilan).
    mover = efectos.ACTIVOS
    for i in range(70):
        x = (i * 7919) % ancho
        y = (i * 104729) % alto
        color = (44, 48, 80)
        if mover:
            x = (x - int(t * (0.004 + (i % 3) * 0.004))) % ancho
            k = 0.5 + 0.5 * math.sin(t / 700 + i)
            color = (int(44 + 50 * k), int(48 + 50 * k), int(80 + 60 * k))
        pygame.draw.circle(screen, color, (x, y), 1)


def _cifra(screen, rect, valor, etiqueta, color, f_valor, f_etiqueta, aparece=1.0, cuenta=1.0):
    if aparece <= 0:
        return
    rect = rect.move(0, int((1 - aparece) * 24))
    valor = _contando(valor, cuenta)
    _caja(screen, rect)
    pygame.draw.rect(screen, COLOR_PANEL_BORDE, rect, 2, border_radius=12)
    pygame.draw.rect(screen, color, (rect.x + 10, rect.y, rect.width - 20, 4), border_radius=2)
    img = f_valor.render(valor, True, color)
    alto_total = img.get_height() + f_etiqueta.get_linesize()
    y = rect.centery - alto_total // 2
    screen.blit(img, img.get_rect(midtop=(rect.centerx, y)))
    _centrado(screen, etiqueta, f_etiqueta, rect.centerx, y + img.get_height() + 2, rect.width - 12,
              COLOR_TENUE)


def _centrado(screen, texto, f, cx, y, ancho, color):
    if f.size(texto)[0] > ancho:
        for px in range(f.get_height(), 9, -1):
            otra = fuente_de_tamano(px)
            if otra.size(texto)[0] <= ancho:
                f = otra
                break
    img = f.render(texto, True, color)
    screen.blit(img, img.get_rect(midtop=(cx, y)))


def _estrella(screen, centro, radio, color):
    puntos = []
    for i in range(10):
        r = radio if i % 2 == 0 else radio * 0.45
        ang = -math.pi / 2 + i * math.pi / 5
        puntos.append((centro[0] + r * math.cos(ang), centro[1] + r * math.sin(ang)))
    pygame.draw.polygon(screen, color, puntos)


def _tarjeta_jugador(screen, rect, numero, jugador, fuentes, mejor, cuenta=1.0):
    from data.roles import ROLES_POR_NOMBRE
    from screens.seleccion import _retrato
    f_nombre, f, f_chica, f_puntos = fuentes
    color = ROLES_POR_NOMBRE.get(jugador.rol, {}).get("color", COLOR_TEXTO)
    eliminado = getattr(jugador, "eliminado", False)
    pygame.draw.rect(screen, COLOR_PANEL, rect, border_radius=12)
    pygame.draw.rect(screen, color if not eliminado else COLOR_APAGADO, rect, 2, border_radius=12)
    pygame.draw.rect(screen, color, (rect.x, rect.y + 10, 6, rect.height - 20), border_radius=3)
    # El personaje a la izquierda.
    alto_retrato = max(28, rect.height - 16)
    imagen = _retrato(jugador.rol, alto_retrato)
    # Una columna fija para el personaje: así los textos quedan alineados
    # entre tarjetas (cada personaje tiene otro ancho).
    columna = int(alto_retrato * 0.85)
    x = rect.x + 18
    if imagen is not None:
        if imagen.get_height() > alto_retrato or imagen.get_width() > columna:
            escala = min(alto_retrato / imagen.get_height(), columna / imagen.get_width())
            imagen = pygame.transform.scale(imagen, (max(1, int(imagen.get_width() * escala)),
                                                     max(1, int(imagen.get_height() * escala))))
        if eliminado:
            imagen = imagen.copy()
            imagen.fill((90, 90, 110, 255), special_flags=pygame.BLEND_RGBA_MULT)
        screen.blit(imagen, imagen.get_rect(center=(x + columna // 2, rect.centery)))
    x += columna + 14
    # Los puntos a la derecha.
    puntos = f_puntos.render(str(int(round(jugador.puntos * cuenta))), True, COLOR_TITULO)
    etiqueta = f_chica.render("puntos", True, COLOR_TENUE)
    derecha = rect.right - 16
    screen.blit(puntos, puntos.get_rect(topright=(derecha, rect.y + 10)))
    screen.blit(etiqueta, etiqueta.get_rect(topright=(derecha, rect.y + 12 + puntos.get_height())))
    ancho_texto = derecha - max(puntos.get_width(), etiqueta.get_width()) - 16 - x
    # Nombre, número y etiquetas.
    y = rect.y + 10
    nombre = f_nombre.render(jugador.rol, True, color)
    screen.blit(nombre, (x, y))
    extra_x = x + nombre.get_width() + 10
    jtxt = f_chica.render(f"J{numero}", True, COLOR_TENUE)
    screen.blit(jtxt, (extra_x, y + nombre.get_height() - jtxt.get_height() - 1))
    extra_x += jtxt.get_width() + 10
    if mejor:
        _estrella(screen, (extra_x + 8, y + nombre.get_height() // 2), 8, COLOR_TITULO)
        extra_x += 22
    if eliminado:
        tag = f_chica.render("ELIMINADO", True, COLOR_MAL)
        screen.blit(tag, (extra_x, y + nombre.get_height() - tag.get_height() - 1))
    y += nombre.get_height() + 4
    lineas = [(f"Tareas hechas: {jugador.tareas_hechas}", COLOR_TEXTO)]
    if not jugador.arbol.vacio:
        camino = [n.nombre for n in jugador.arbol.desbloqueadas()]
        lineas.append(("Habilidades: " + " > ".join(camino), COLOR_TENUE))
    for texto, c in lineas:
        if y + f.get_linesize() > rect.bottom - 4:
            break
        y += _texto(screen, texto, f, x, y, ancho_texto, c) + 2


def _pasos(screen, rect, alcanzado, resultado, f_chica, radio=11, avance=None):
    """Los pasos de la misión unidos por una línea: hechos en verde, donde
    se quedaron en amarillo (rojo si perdieron ahí), lo que faltó apagado.
    `avance` (de 0 a `alcanzado`, animación): hasta dónde llegó la línea verde."""
    n = len(PASOS)
    margen = rect.width / (n * 2)
    y = rect.y + radio + 3
    xs = [int(rect.x + margen + i * (rect.width - 2 * margen) / (n - 1)) for i in range(n)]
    if avance is None:
        avance = alcanzado
    for i in range(n - 1):
        pygame.draw.line(screen, COLOR_APAGADO, (xs[i], y), (xs[i + 1], y), 4)
        if i < alcanzado and avance > i:
            fin = xs[i] + (xs[i + 1] - xs[i]) * min(1.0, avance - i)
            pygame.draw.line(screen, COLOR_BIEN, (xs[i], y), (int(fin), y), 4)
    for i, (_, nombre) in enumerate(PASOS):
        if avance < i:
            # Todavía no llegó la línea: apagado (el que se alcanzó, sin color).
            pygame.draw.circle(screen, COLOR_PANEL, (xs[i], y), radio)
            pygame.draw.circle(screen, COLOR_APAGADO, (xs[i], y), radio, 3)
            _centrado(screen, nombre, f_chica, xs[i], y + radio + 5,
                      int((rect.width - 2 * margen) / (n - 1)) - 4, COLOR_APAGADO)
            continue
        if i < alcanzado:
            c, lleno = COLOR_BIEN, True
        elif i == alcanzado:
            c, lleno = (COLOR_MAL if resultado == "derrota" else COLOR_TITULO), True
        else:
            c, lleno = COLOR_APAGADO, False
        pygame.draw.circle(screen, COLOR_PANEL, (xs[i], y), radio)
        pygame.draw.circle(screen, c, (xs[i], y), radio, 0 if lleno else 3)
        if i < alcanzado:      # una palomita
            k = radio / 11
            pygame.draw.lines(screen, COLOR_PANEL, False, [(xs[i] - 5 * k, y), (xs[i] - 1 * k, y + 4 * k),
                                                           (xs[i] + 6 * k, y - 4 * k)], 3)
        _centrado(screen, nombre, f_chica, xs[i], y + radio + 5, int((rect.width - 2 * margen) / (n - 1)) - 4,
                  COLOR_TEXTO if i <= alcanzado else COLOR_APAGADO)
    return y + radio + 5 + f_chica.get_linesize() + 6


def _punto(screen, x, y, color, bueno, radio=6):
    pygame.draw.circle(screen, color, (x, y), radio)
    k = radio / 6
    if bueno:
        pygame.draw.lines(screen, COLOR_PANEL, False, [(x - 3 * k, y), (x - 1 * k, y + 2 * k),
                                                       (x + 3 * k, y - 2 * k)], 2)
    else:
        pygame.draw.line(screen, COLOR_PANEL, (x - 2 * k, y - 2 * k), (x + 2 * k, y + 2 * k), 2)
        pygame.draw.line(screen, COLOR_PANEL, (x + 2 * k, y - 2 * k), (x - 2 * k, y + 2 * k), 2)


def _cambiaformas(infiltrado, cambiaformas):
    """El caso del Cambiaformas en una o dos líneas (antes eran dos líneas
    sueltas que decían "Cambiaformas:" cada una, una del infiltrado y otra de
    lo que hizo el alien)."""
    lineas = []
    if infiltrado is not None and getattr(infiltrado, "pruebas", None):
        nombre = infiltrado.infiltrado["nombre"]
        if infiltrado.estado == "expuesto":
            lineas.append((f"Lo desenmascararon: se hacía pasar por {nombre}.", COLOR_BIEN))
        elif infiltrado.estado == "fallido":
            lineas.append((f"Acusaron a {infiltrado.acusado['nombre']}, pero era {nombre}.", COLOR_MAL))
        else:
            lineas.append((f"No lo descubrieron: era {nombre} ({len(infiltrado.subidas)}/3 pruebas).",
                           COLOR_TENUE))
    if cambiaformas is not None:
        if cambiaformas.revelaciones or cambiaformas.capturas or cambiaformas.sabotajes:
            veces = lambda n: "1 vez" if n == 1 else f"{n} veces"
            lineas.append((f"Se reveló {veces(cambiaformas.revelaciones)}, atrapó a "
                           f"{cambiaformas.capturas} y saboteó {veces(cambiaformas.sabotajes)}.", COLOR_TENUE))
        else:
            lineas.append(("No llegó a revelarse ni a atrapar a nadie.", COLOR_TENUE))
    return lineas


def render_resultados(screen, jugadores, font=None, small_font=None,
                      mision=None, equipo=None, infiltrado=None, logros=None, seleccion=0,
                      nexus=None, cambiaformas=None, npcs=None, dificultad=None,
                      tiempo_jugado_ms=None):
    """Dibuja el resumen. Devuelve los rects de los botones (para el mouse)."""
    ancho, alto = screen.get_size()
    e = max(0.72, min(1.6, min(ancho / 1280, alto / 720)))
    px = lambda v: max(10, int(v * e))
    f_titular = fuente_de_tamano(px(48))
    f_sub = fuente_de_tamano(px(19))
    f_seccion = fuente_de_tamano(px(19))
    f = fuente_de_tamano(px(16))
    f_chica = fuente_de_tamano(px(13))
    f_cifra = fuente_de_tamano(px(34))
    margen = int(28 * e)

    victoria = mision is not None and mision.activa and mision.resultado == "victoria"
    if mision is None or not mision.activa:
        titular, color = "SE ACABÓ LA RONDA", COLOR_TEXTO
    elif victoria:
        titular, color = "¡ESCAPARON DE LA NAVE!", COLOR_BIEN
    else:
        titular, color = "NO LOGRARON ESCAPAR", COLOR_MAL
    t = _desde((id(mision), id(logros), len(jugadores)))
    if _hay_escena(mision):
        # Primero la escena del final sola (screens/final.py); después queda de
        # fondo, oscurecida, y los resultados entran encima.
        from screens import final
        _entrada["intro"] = final.INTRO_MS
        if t < final.INTRO_MS:
            _intro(screen, victoria, t, jugadores, titular, color, _motivo(mision))
            return []
        final.dibujar(screen, victoria, t, jugadores)
        final.oscurecer(screen, 140)
        t -= final.INTRO_MS
    else:
        _fondo(screen, color, t)

    # -- Titular -------------------------------------------------------------------
    y = int(18 * e)
    img = f_titular.render(titular, True, color)
    entra = _suave(t, 0, 550)
    destino = img.get_rect(midtop=(ancho // 2, y - int((1 - entra) * 30)))
    if entra < 1:
        img.set_alpha(int(255 * entra))
    if not victoria and mision is not None and mision.activa and 150 < t < 1300 and (t // 70) % 3 != 0:
        # Glitch: copias corridas en rojo y celeste, de a ratos.
        corrido = int(6 * (1 - (t - 150) / 1150))
        for dx, c in ((-corrido, (255, 40, 60)), (corrido, (60, 220, 255))):
            fantasma = f_titular.render(titular, True, c)
            fantasma.set_alpha(110)
            screen.blit(fantasma, destino.move(dx, 0))
    screen.blit(img, destino)
    y += img.get_height() + int(6 * e)
    motivo = _motivo(mision)
    if motivo:
        _centrado(screen, motivo, f_sub, ancho // 2, y, ancho - 2 * margen, COLOR_TEXTO)
        y += f_sub.get_linesize()
    meta = []
    if dificultad is not None:
        texto = f"Dificultad {dificultad.nombre}"
        if dificultad.inteligente:
            texto += (f" (llegó a {dificultad.nombre_nivel(dificultad.nivel_max)}, "
                      f"terminó en {dificultad.nombre_nivel()})")
        meta.append(texto)
    if tiempo_jugado_ms is not None:
        meta.append(f"{_tiempo(tiempo_jugado_ms)} de partida")
    meta.append(f"{len(jugadores)} jugadores")
    _centrado(screen, "   ·   ".join(meta), f_chica, ancho // 2, y + 2, ancho - 2 * margen, COLOR_TENUE)
    y += f_chica.get_linesize() + int(14 * e)

    # -- Las cifras -----------------------------------------------------------------
    cifras = []
    if equipo is not None:
        cifras.append((str(equipo.total), "puntos del equipo", COLOR_TITULO))
    if mision is not None and mision.activa:
        from misiones.mision import PIEZAS_NECESARIAS
        piezas = mision.piezas_entregadas
        necesarias = getattr(mision, "piezas_necesarias", PIEZAS_NECESARIAS)
        cifras.append((f"{piezas}/{necesarias}", "piezas en la cápsula",
                       COLOR_BIEN if piezas >= necesarias else COLOR_TEXTO))
    if logros is not None:
        cifras.append((f"{logros.arbol.obtenidos()}/{logros.arbol.total()}", "logros", COLOR_TITULO))
    if npcs is not None:
        rescatados = len(npcs.rescatados)
        cifras.append((str(rescatados), "prisioneros rescatados", COLOR_BIEN if rescatados else COLOR_TEXTO))
    if logros is not None:
        capturas = logros.capturas_total
        cifras.append((str(capturas), "veces los atraparon", COLOR_MAL if capturas else COLOR_BIEN))
    alto_cifra = int(78 * e)
    if cifras:
        sep = int(14 * e)
        ancho_cifra = min(int(210 * e), (ancho - 2 * margen - sep * (len(cifras) - 1)) // len(cifras))
        x = ancho // 2 - (ancho_cifra * len(cifras) + sep * (len(cifras) - 1)) // 2
        for k, (valor, etiqueta, c) in enumerate(cifras):
            inicio = 300 + 110 * k
            _cifra(screen, pygame.Rect(x, y, ancho_cifra, alto_cifra), valor, etiqueta, c, f_cifra, f_chica,
                   aparece=_suave(t, inicio, 380), cuenta=_suave(t, inicio + 100, 1100))
            x += ancho_cifra + sep
        y += alto_cifra + int(16 * e)

    # -- Botones (abajo: lo de en medio usa lo que quede) ---------------------------------
    alto_boton = 52 if alto >= 600 else 40
    y_botones = alto - alto_boton - int(40 * e)
    abajo = y_botones - int(14 * e)

    # -- La tripulación (izquierda) ------------------------------------------------------
    ancho_izq = int((ancho - 3 * margen) * 0.44)
    x_izq = margen
    caja = pygame.Rect(x_izq, y, ancho_izq, abajo - y)
    y_c = _panel(screen, caja, "La tripulación", f_seccion)
    n = max(1, len(jugadores))
    sep = int(8 * e)
    alto_tarjeta = min(int(112 * e), (caja.bottom - 10 - y_c - sep * (n - 1)) // n)
    mejores = max((j.puntos for j in jugadores), default=0)
    unico = sum(1 for j in jugadores if j.puntos == mejores) == 1
    fuentes = (fuente_de_tamano(px(19)), f, f_chica, fuente_de_tamano(px(26)))
    for i, jugador in enumerate(jugadores):
        rect = pygame.Rect(caja.x + 10, y_c + i * (alto_tarjeta + sep), caja.width - 20, alto_tarjeta)
        entra = _suave(t, 700 + 160 * i, 450)
        if entra <= 0:
            continue
        recorte = screen.get_clip()
        screen.set_clip(caja.inflate(-4, -4).clip(recorte))
        _tarjeta_jugador(screen, rect.move(-int((1 - entra) * (rect.width * 0.6)), 0), i + 1, jugador, fuentes,
                         mejor=unico and mejores > 0 and jugador.puntos == mejores,
                         cuenta=_suave(t, 800 + 160 * i, 1000))
        screen.set_clip(recorte)
    # Si sobra sitio debajo: las insignias de los logros de esta partida.
    debajo = y_c + n * (alto_tarjeta + sep) + int(6 * e)
    if logros is not None and caja.bottom - 12 - debajo >= int(70 * e):
        _insignias_logros(screen, pygame.Rect(caja.x + 14, debajo, caja.width - 28, caja.bottom - 12 - debajo),
                          logros.arbol, f_chica, e, t)

    # -- La misión y NEXUS (derecha) -----------------------------------------------------
    x_der = x_izq + ancho_izq + margen
    ancho_der = ancho - margen - x_der
    texto_x = x_der + 18
    texto_ancho = ancho_der - 36
    paso = f.get_linesize() + 3
    alto_mision = 0
    lineas_cf = _cambiaformas(infiltrado, cambiaformas)
    radio = max(9, int(11 * e))
    if mision is not None and mision.activa:
        alto_mision = (10 + f_seccion.get_height() + 8          # el título
                       + 2 * radio + 8 + f_chica.get_linesize() + 6      # los pasos
                       + ((f_chica.get_height() + 8) if lineas_cf else 0)
                       + (f.get_height() + 3) * len(lineas_cf) + 8)
        caja = pygame.Rect(x_der, y, ancho_der, alto_mision)
        y_c = _panel(screen, caja, "La misión", f_seccion)
        alcanzado = _paso_alcanzado(mision)
        y_c = _pasos(screen, pygame.Rect(caja.x + 10, y_c, caja.width - 20, 40),
                     alcanzado, mision.resultado, f_chica, radio,
                     avance=alcanzado * _suave(t, 900, 300 + 320 * max(1, alcanzado)))
        if lineas_cf:
            img = f_chica.render("El Cambiaformas", True, COLOR_TITULO)
            screen.blit(img, (texto_x, y_c + 2))
            y_c += img.get_height() + 6
        for texto, c in lineas_cf:
            y_c += _texto(screen, texto, f, texto_x, y_c, texto_ancho, c) + 3
        y += alto_mision + int(12 * e)

    if nexus is not None:
        caja = pygame.Rect(x_der, y, ancho_der, abajo - y)
        y_c = _panel(screen, caja, "Su uso de NEXUS", f_seccion)
        r = nexus.resumen()
        verde, rojo = nexus.barras()
        llena = _suave(t, 1300, 900)
        verde, rojo = verde * llena, rojo * llena
        # La confianza al final: verde (en ustedes) contra rojo (en los aliens).
        barra = pygame.Rect(texto_x, y_c + 2, texto_ancho, int(14 * e))
        pygame.draw.rect(screen, (40, 42, 70), barra, border_radius=7)
        if verde > 0:
            pygame.draw.rect(screen, COLOR_BIEN, (barra.x, barra.y, int(barra.width * verde), barra.height),
                             border_radius=7)
        if rojo > 0:
            w = int(barra.width * rojo)
            pygame.draw.rect(screen, COLOR_ROJO_NEXUS, (barra.right - w, barra.y, w, barra.height),
                             border_radius=7)
        y_c = barra.bottom + 4
        izq = f_chica.render(f"Confían en ustedes: {int(verde * 100)}%", True, COLOR_BIEN)
        der = f_chica.render(f"En los aliens: {int(rojo * 100)}%", True, COLOR_ROJO_NEXUS)
        screen.blit(izq, (barra.x, y_c))
        screen.blit(der, der.get_rect(topright=(barra.right, y_c)))
        y_c += izq.get_height() + int(8 * e)
        bien = [("Rumores desmentidos", r.get("desmentidos", 0)),
                ("Bots reportados", r.get("bots_reportados", 0)),
                ("Suplantaciones reportadas", r.get("suplantaciones", 0)),
                ("Fotos recortadas (sin ubicación)", r.get("fotos_recortadas", 0))]
        mal = [("Compartidos sin verificar", r.get("compartidos_falsos", 0)),
               ("Reportes a gente real", r.get("reportes_injustos", 0)),
               ("Fotos con su ubicación", r.get("fotos_ubicacion", 0)),
               ("Rumores que se volvieron virales", r.get("virales", 0)),
               ("Seguidores que ganaron los bots", r.get("seguidores_bots", 0))]
        col = texto_ancho // 2
        for k, (lista, c, bueno, titulo) in enumerate(((bien, COLOR_BIEN, True, "Lo que hicieron bien"),
                                                       (mal, COLOR_MAL, False, "Lo que hay que cuidar"))):
            x0 = texto_x + k * col
            yy = y_c
            screen.blit(f_chica.render(titulo, True, c), (x0, yy))
            yy += f_chica.get_linesize() + 2
            for nombre, valor in lista:
                activo = valor > 0
                _punto(screen, x0 + 6, yy + f.get_linesize() // 2, c if activo else COLOR_APAGADO, bueno,
                       radio=max(5, int(6 * e)))
                num = f.render(str(valor), True, c if activo else COLOR_APAGADO)
                screen.blit(num, (x0 + col - 16 - num.get_width(), yy))
                _texto(screen, nombre, f, x0 + 18, yy, col - 46 - num.get_width(),
                       COLOR_TEXTO if activo else COLOR_TENUE)
                yy += paso
            alto_cols = yy - y_c
        y_c += max(alto_cols, (f_chica.get_linesize() + 2) + paso * len(bien)) + 2
        minutos = r.get("minutos_celular", 0)
        y_c += _texto(screen, f"Tiempo con el celular abierto: {_tiempo(minutos * 60000)}", f_chica,
                      texto_x, y_c, texto_ancho, COLOR_TENUE) + int(8 * e)
        # El consejo, en su propia cajita (verde si les fue bien).
        from screens.paneles import partir_lineas
        consejo = r.get("consejo", "")
        bueno = consejo.startswith("Buen uso")
        c = COLOR_BIEN if bueno else COLOR_TITULO
        renglones = partir_lineas(consejo, f, texto_ancho - 24)
        alto_consejo = len(renglones) * f.get_linesize() + 14
        if y_c + alto_consejo > caja.bottom - 6:
            renglones = partir_lineas(consejo, f_chica, texto_ancho - 24)
            alto_consejo = len(renglones) * f_chica.get_linesize() + 14
            fc = f_chica
        else:
            fc = f
        cajita = pygame.Rect(texto_x, y_c, texto_ancho, alto_consejo)
        pygame.draw.rect(screen, (24, 40, 34) if bueno else (46, 40, 22), cajita, border_radius=8)
        pygame.draw.rect(screen, c, cajita, 2, border_radius=8)
        yy = cajita.y + 7
        for renglon in renglones:
            screen.blit(fc.render(renglon, True, c), (cajita.x + 12, yy))
            yy += fc.get_linesize()

    # -- Botones ------------------------------------------------------------------
    opciones = opciones_resultados(logros, nexus)
    ancho_boton = min(360, (ancho - 80) // len(opciones) - 20)
    separacion = 28
    total = len(opciones) * ancho_boton + (len(opciones) - 1) * separacion
    x = ancho // 2 - total // 2
    mouse = pygame.mouse.get_pos()
    rects = []
    for i, (texto, accion) in enumerate(opciones):
        rect = pygame.Rect(x, y_botones, ancho_boton, alto_boton)
        Button(rect, texto, accion).draw(screen, hover=(i == seleccion or rect.collidepoint(mouse)))
        rects.append(rect)
        x += ancho_boton + separacion
    pista = fuente_de_tamano(px(14)).render(
        f"Flechas + Enter  ·  Mando: cruceta y {botones_conectados('interactuar')}", True, COLOR_TENUE)
    screen.blit(pista, pista.get_rect(midtop=(ancho // 2, y_botones + alto_boton + 10)))
    if victoria and efectos.ACTIVOS:
        _papelitos(screen, t)
    return rects


def _insignias_logros(screen, caja, arbol, f_chica, e, t):
    """Las insignias de los logros conseguidos en la partida, apareciendo una
    por una (las mismas del árbol de logros, screens/logros.py)."""
    from screens.logros import insignia
    obtenidos = [n for n in arbol.preorden() if n.obtenido]
    titulo = f_chica.render(f"Logros de la partida  {len(obtenidos)}", True, COLOR_TITULO)
    screen.blit(titulo, (caja.x, caja.y))
    if not obtenidos:
        screen.blit(f_chica.render("Ninguno esta vez.", True, COLOR_TENUE), (caja.x, caja.y + titulo.get_height() + 6))
        return
    d = max(24, int(38 * e))
    paso = d + int(8 * e)
    y0 = caja.y + titulo.get_height() + int(8 * e)
    por_fila = max(1, caja.width // paso)
    filas = max(1, (caja.bottom - y0) // paso)
    caben = por_fila * filas
    mostrar = obtenidos if len(obtenidos) <= caben else obtenidos[:caben - 1]
    for i, nodo in enumerate(mostrar):
        aparece = _suave(t, 1600 + 90 * i, 260)
        if aparece <= 0:
            break
        # Crece un poco de más y vuelve (un "pop").
        escala = aparece * (1 + 0.25 * math.sin(math.pi * aparece))
        lado = max(4, int(d * escala))
        img = insignia(d, nodo.rama, "obtenido", nodo.clave)
        if lado != d:
            img = pygame.transform.smoothscale(img, (lado, lado))
        cx = caja.x + (i % por_fila) * paso + d // 2
        cy = y0 + (i // por_fila) * paso + d // 2
        screen.blit(img, img.get_rect(center=(cx, cy)))
    if len(mostrar) < len(obtenidos) and _suave(t, 1600 + 90 * len(mostrar), 260) > 0:
        mas = f_chica.render(f"+{len(obtenidos) - len(mostrar)}", True, COLOR_TENUE)
        i = len(mostrar)
        screen.blit(mas, mas.get_rect(center=(caja.x + (i % por_fila) * paso + d // 2,
                                              y0 + (i // por_fila) * paso + d // 2)))
