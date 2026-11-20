"""Panel del árbol de habilidades, dibujado dentro del viewport de un jugador.

Dibuja el árbol binario completo —incluidas las ramas que el jugador ya perdió,
en gris— porque ver lo que se cerró es la mitad de la gracia: el árbol enseña
que elegir HACKEO fue renunciar a ESCANEO.

Las posiciones salen del recorrido por niveles (BFS) del árbol: la profundidad
da la fila, y dentro de cada fila los nodos se reparten el ancho por igual.
"""

import os

import pygame

from data.habilidades import ARBOLES_POR_ROL
from juego.fuentes import fuente_de_tamano
from juego import idioma
from juego.idioma import tr


CARPETA_ICONOS = os.path.join("Imagenes", "UI", "Habilidades")

# Los .png del equipo vienen con fondo negro sólido, no transparente. Si se
# dibujaran tal cual, cada habilidad sería un cuadro negro sobre el panel.
_CACHE_ICONOS = {}      # (rol, clave, lado) -> Surface lista para dibujar
_CACHE_BASES = {}       # (rol, clave)        -> Surface intermedia, sin fondo

# Un píxel cuenta como fondo si la suma de sus canales no pasa de esto. No sirve
# un colorkey de negro puro: el fondo trae píxeles como (1,0,1) que un colorkey
# dejaría pasar.
UMBRAL_NEGRO = 34

# Tamaño intermedio al que se encoge el icono ANTES de quitarle el fondo.
# Los archivos son de 1254x1254 y se dibujan a 28-56 px: recorrer pixel por
# pixel en Python el millón y medio de píxeles del original tardaba ~1 s por
# icono (7 s la primera vez que se abría el panel, congelando la partida).
# Encogiendo primero, el recorrido baja a ~16 mil píxeles.
LADO_INTERMEDIO = 128

# Tamaños a los que se dibuja un icono. El panel calcula un lado a partir del
# alto disponible, que sale un número cualquiera; si se usara tal cual, el
# caché (rol, clave, lado) nunca acertaría y cada apertura volvería a procesar
# los PNG. Se redondea al más cercano de esta escalera, que es justo la que se
# precarga al empezar la partida.
LADOS_ICONO = (28, 36, 44, 52, 56)


def ajustar_lado(px):
    """Redondea un tamaño al valor más cercano de LADOS_ICONO."""
    return min(LADOS_ICONO, key=lambda lado: abs(lado - px))


COLOR_FONDO = (22, 24, 42, 240)
COLOR_BORDE = (120, 132, 190)
COLOR_TITULO = (255, 214, 64)
COLOR_TEXTO = (240, 242, 252)
COLOR_TENUE = (168, 176, 214)

COLOR_DESBLOQUEADA = (96, 188, 118)
COLOR_DISPONIBLE = (222, 190, 92)
COLOR_DESCARTADA = (78, 82, 104)
COLOR_LINEA = (96, 104, 150)
COLOR_LINEA_MUERTA = (56, 58, 76)

COLOR_SELECCION = (255, 214, 64)
COLOR_SELECCION_FONDO = (52, 57, 92)
COLOR_DETALLE = (150, 210, 235)       # "en una terminal: ..." (lo que hace en el juego)

MARGEN = 18


def _base_icono(rol, clave):
    """Icono cargado, encogido y sin fondo, en el tamaño intermedio.

    Se cachea aparte del tamaño final porque decodificar el PNG y quitarle el
    fondo es lo caro, y no depende de a qué tamaño se vaya a dibujar. Antes se
    hacía una vez por cada tamaño pedido, o sea cinco veces por icono.
    """
    if (rol, clave) in _CACHE_BASES:
        return _CACHE_BASES[(rol, clave)]

    nombre = NOMBRE_ARCHIVO.get(clave, clave.capitalize())
    ruta = os.path.join(CARPETA_ICONOS, rol, nombre + ".png")
    if not os.path.isfile(ruta):
        _CACHE_BASES[(rol, clave)] = None
        return None
    try:
        imagen = pygame.image.load(ruta).convert_alpha()
    except pygame.error:
        _CACHE_BASES[(rol, clave)] = None
        return None

    # Encoger con `scale`, que NO interpola: así el fondo sigue siendo negro
    # plano y no se mezcla con los bordes de la insignia. Recién después se le
    # quita el fondo, ya sobre una imagen chica.
    if imagen.get_width() > LADO_INTERMEDIO:
        imagen = pygame.transform.scale(imagen, (LADO_INTERMEDIO, LADO_INTERMEDIO))
    imagen = _quitar_fondo_negro(imagen)

    _CACHE_BASES[(rol, clave)] = imagen
    return imagen


def icono_habilidad(rol, clave, lado):
    """Icono de una habilidad ya escalado, o None si ese archivo no existe.

    El nombre del archivo se deduce de la clave del nodo. Si el equipo agrega
    arte nueva basta con dejarla en Imagenes/UI/Habilidades/<Rol>/<Nombre>.png.
    """
    cache_id = (rol, clave, lado)
    if cache_id in _CACHE_ICONOS:
        return _CACHE_ICONOS[cache_id]

    base = _base_icono(rol, clave)
    if base is None:
        _CACHE_ICONOS[cache_id] = None
        return None

    # Aquí sí conviene suavizar: como el fondo ya es transparente, lo que se
    # mezcla en los bordes es alfa y no negro.
    imagen = pygame.transform.smoothscale(base, (lado, lado))
    _CACHE_ICONOS[cache_id] = imagen
    return imagen


def _quitar_fondo_negro(imagen):
    """Vuelve transparentes los píxeles casi negros del borde de la insignia."""
    copia = imagen.copy()
    copia.lock()
    ancho, alto = copia.get_size()
    for x in range(ancho):
        for y in range(alto):
            r, g, b, a = copia.get_at((x, y))
            if r + g + b <= UMBRAL_NEGRO:
                copia.set_at((x, y), (r, g, b, 0))
    copia.unlock()
    return copia


_CACHE_APAGADOS = {}


def _apagar(imagen, alpha=90):
    """Copia en gris y translúcida, para las ramas que el jugador ya perdió.

    Se guarda por imagen: antes se hacía una copia nueva en cada frame.
    """
    clave = (id(imagen), alpha)
    if clave in _CACHE_APAGADOS:
        return _CACHE_APAGADOS[clave]
    copia = imagen.copy()
    gris = pygame.Surface(copia.get_size(), pygame.SRCALPHA)
    gris.fill((90, 92, 110, 255))
    copia.blit(gris, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
    copia.set_alpha(alpha)
    _CACHE_APAGADOS[clave] = copia
    return copia


# Clave del nodo -> nombre del archivo, para cuando el arte no use la misma
# palabra que la clave. Si no está aquí se usa la clave capitalizada
# (HACKEO -> Hackeo.png), que hoy sirve para todas.
# Clave del nodo -> nombre del icono, cuando no coinciden.
NOMBRE_ARCHIVO = {}


def precargar_iconos(roles, lados=LADOS_ICONO):
    """Deja los iconos listos en el caché antes de que empiece la partida.

    Aun con la carga optimizada, abrir el panel por primera vez costaba medio
    segundo (leer y decodificar siete PNG de 1254x1254). Medio segundo a mitad
    de una ronda de cinco minutos se siente; hacerlo mientras carga el mapa, no.
    Se precargan los tamaños que el panel puede pedir según el viewport.
    """
    for rol in roles:
        datos = ARBOLES_POR_ROL.get(rol)
        if datos is None:
            continue
        for clave in _claves(datos):
            for lado in lados:
                icono_habilidad(rol, clave, lado)


def _claves(datos):
    """Todas las claves de un árbol de habilidades, sin construirlo."""
    yield datos["clave"]
    for hijo in datos.get("hijos", []) or []:
        yield from _claves(hijo)


# Panel ya dibujado de cada jugador: {id(jugador): (estado, superficie)}.
_CACHE_PANELES = {}
idioma.al_cambiar(_CACHE_PANELES.clear)


def _puntos(jugador):
    """Con qué se pagan las habilidades: los puntos del equipo, si hay equipo."""
    return getattr(jugador, "puntos_para_habilidades", jugador.puntos)


def _estado_panel(vista, jugador):
    """Todo lo que cambia lo que se ve en el panel. Si no cambió, no se redibuja."""
    arbol = jugador.arbol
    nodos = tuple((n.clave, n.desbloqueada, n.descartada) for n, _ in arbol.por_niveles())
    return (vista.size, jugador.rol, jugador.cursor, _puntos(jugador),
            jugador.controles_nombre, nodos)


def render_panel_habilidades(screen, vista, jugador):
    """Dibuja el panel del árbol de habilidades en el viewport del jugador.

    El panel casi nunca cambia mientras está abierto: solo cuando el jugador
    mueve el cursor, desbloquea algo o le cambian los puntos. Pero armarlo es
    caro (medir texto para escoger la letra, partir descripciones, dibujar
    iconos y una capa translúcida del tamaño del panel), y antes se armaba
    entero en cada frame. Con dos jugadores con el panel abierto eso duplicaba
    el tiempo de dibujo y el juego se ponía lento. Ahora se dibuja una vez en
    una superficie aparte y en los frames siguientes solo se pega.
    """
    estado = _estado_panel(vista, jugador)
    guardado = _CACHE_PANELES.get(id(jugador))
    if guardado is None or guardado[0] != estado:
        superficie = pygame.Surface(vista.size, pygame.SRCALPHA)
        _dibujar_panel_habilidades(superficie, pygame.Rect((0, 0), vista.size), jugador)
        # Se guarda solo el recuadro del panel, no el viewport entero: pegar
        # una capa translúcida cuesta según su tamaño.
        recuadro = superficie.get_bounding_rect()
        guardado = (estado, superficie.subsurface(recuadro).convert_alpha(), recuadro.topleft)
        _CACHE_PANELES[id(jugador)] = guardado
    _, imagen, esquina = guardado
    screen.blit(imagen, (vista.x + esquina[0], vista.y + esquina[1]))


def _dibujar_panel_habilidades(screen, vista, jugador):
    """Dibuja el árbol de habilidades y las opciones que puede desbloquear.

    El panel se dimensiona a partir de su contenido en vez de tener un alto
    fijo. Antes era `min(alto*0.86, 560)` y a 1080p el texto de las dos
    opciones no cabía en esos 560 px: las descripciones se montaban unas sobre
    otras y encima del pie. Ahora se mide cuánto ocupa todo con la letra más
    grande y, si no cabe, se baja de tamaño hasta que quepa.
    """
    arbol = jugador.arbol

    ancho = min(int(vista.width * 0.9), 760)
    alto_max = int(vista.height * 0.92)
    ancho_texto = ancho - MARGEN * 2 - 20

    opciones = arbol.opciones()
    f, paso, alto_total, lineas_desc, fraccion = _elegir_letra(
        arbol, opciones, ancho_texto, alto_max)

    caja = pygame.Rect(0, 0, ancho, min(alto_total, alto_max))
    caja.center = vista.center
    from data.roles import ROLES_POR_NOMBRE
    from screens import vidrio
    color_rol = ROLES_POR_NOMBRE.get(jugador.rol, {}).get("color", COLOR_BORDE)

    # Vidrio con el borde del color del rol y un resplandor suave arriba.
    vidrio.caja(screen, caja, color_rol, 238, 14)
    vidrio.brillo(screen, (caja.centerx, caja.y), caja.width * 0.45, tuple(int(c * 0.12) for c in color_rol))

    clip_previo = screen.get_clip()
    screen.set_clip(caja)

    # -- Encabezado: "ÁRBOL DE HABILIDADES" y los puntos; debajo el rol y el nivel.
    y = caja.y + MARGEN
    f_chica = fuente_de_tamano(max(10, f.get_height() - 4))
    rotulo = f_chica.render(tr("Árbol de habilidades").upper(), True, COLOR_TENUE)
    screen.blit(rotulo, (caja.x + MARGEN, y + (f.get_height() - rotulo.get_height()) // 2))
    texto_puntos = (f"{_puntos(jugador)} pts del equipo" if getattr(jugador, "equipo", None)
                    else f"{_puntos(jugador)} pts")
    _pastilla(screen, f, texto_puntos, COLOR_TITULO, (caja.right - MARGEN, y), "topright")
    y += paso + 4

    screen.blit(f.render(jugador.rol or "", True, color_rol), (caja.x + MARGEN, y))
    if arbol.vacio:
        y += paso
        for linea in ["Este rol todavía no tiene árbol de habilidades definido."]:
            screen.blit(f.render(linea, True, COLOR_TENUE), (caja.x + MARGEN, y))
            y += paso
        _pie(screen, caja, f, jugador, "cerrar")
        screen.set_clip(clip_previo)
        return
    nivel = f.render(tr("Nivel {} de {}").format(len(arbol.desbloqueadas()), arbol.altura()), True, COLOR_TENUE)
    screen.blit(nivel, (caja.right - MARGEN - nivel.get_width(), y))
    y += paso

    # -- El árbol ---------------------------------------------------------------
    niveles = {}
    for nodo, profundidad in arbol.por_niveles():
        niveles.setdefault(profundidad, []).append(nodo)
    claves_opciones = {n.clave for n in opciones}

    alto_arbol, lado = _medidas_arbol(len(niveles), alto_max, fraccion)
    tope = y
    paso_y = alto_arbol / max(1, len(niveles) - 1) if len(niveles) > 1 else 0

    centros = {}
    for profundidad, nodos in niveles.items():
        ancho_celda = (caja.width - MARGEN * 2) / len(nodos)
        for i, nodo in enumerate(nodos):
            cx = caja.x + MARGEN + ancho_celda * (i + 0.5)
            cy = tope + profundidad * paso_y + 10
            centros[id(nodo)] = (int(cx), int(cy))

    def color_de(nodo):
        if nodo.desbloqueada:
            return COLOR_DESBLOQUEADA, COLOR_DESBLOQUEADA
        if nodo.descartada:
            return COLOR_DESCARTADA, (132, 134, 150)
        if nodo.clave in claves_opciones:
            return COLOR_DISPONIBLE, COLOR_DISPONIBLE
        return (60, 64, 92), (130, 136, 168)

    # Las conexiones como pistas de circuito: baja del padre, va de lado y
    # baja al hijo. Encendidas hasta lo desbloqueado, doradas hacia lo que se
    # puede escoger, apagadas hacia lo que se cerró.
    medio_lado = lado // 2 + 4
    for nodo, _ in arbol.por_niveles():
        for hijo in nodo.hijos:
            (x0, y0), (x1, y1) = centros[id(nodo)], centros[id(hijo)]
            y0 += medio_lado
            y1 -= medio_lado
            ym = (y0 + y1) // 2
            if hijo.desbloqueada:
                color = COLOR_DESBLOQUEADA
            elif hijo.descartada:
                color = COLOR_LINEA_MUERTA
            elif hijo.clave in claves_opciones:
                color = COLOR_DISPONIBLE
            else:
                color = COLOR_LINEA
            puntos = [(x0, y0), (x0, ym), (x1, ym), (x1, y1)]
            if hijo.desbloqueada or hijo.clave in claves_opciones:
                pygame.draw.lines(screen, tuple(c // 3 for c in color), False, puntos, 6)
            pygame.draw.lines(screen, color, False, puntos, 2)
            pygame.draw.circle(screen, color, (x0, ym), 4)
            pygame.draw.circle(screen, color, (x1, y1), 3)

    for nodo, _ in arbol.por_niveles():
        cx, cy = centros[id(nodo)]
        borde, color_texto = color_de(nodo)
        marco = pygame.Rect(0, 0, lado + 10, lado + 10)
        marco.center = (cx, cy)
        if nodo.desbloqueada or nodo.clave in claves_opciones:
            vidrio.brillo(screen, marco.center, lado * 0.95, tuple(int(c * 0.3) for c in borde))
        pygame.draw.rect(screen, (14, 14, 28), marco, border_radius=10)
        icono = icono_habilidad(jugador.rol, nodo.clave, lado)
        if icono is not None:
            apagado = nodo.descartada or not (nodo.desbloqueada or nodo.clave in claves_opciones)
            screen.blit(_apagar(icono, 120 if not nodo.descartada else 90) if apagado else icono,
                        icono.get_rect(center=marco.center))
        else:
            inicial = f.render(nodo.nombre[:1], True, borde)
            screen.blit(inicial, inicial.get_rect(center=marco.center))
        pygame.draw.rect(screen, borde, marco, 2, border_radius=10)
        if nodo.desbloqueada:
            # Una palomita verde en la esquina.
            r = max(6, lado // 6)
            esquina = (marco.right - 2, marco.y + 2)
            pygame.draw.circle(screen, (16, 40, 24), esquina, r + 2)
            pygame.draw.circle(screen, COLOR_DESBLOQUEADA, esquina, r)
            pygame.draw.lines(screen, (16, 40, 24), False, [(esquina[0] - r * 0.5, esquina[1]),
                                                            (esquina[0] - r * 0.1, esquina[1] + r * 0.45),
                                                            (esquina[0] + r * 0.55, esquina[1] - r * 0.4)], 2)
        etiqueta = f.render(nodo.nombre, True, color_texto)
        screen.blit(etiqueta, etiqueta.get_rect(midtop=(cx, marco.bottom + 2)))

    y = tope + alto_arbol + lado // 2 + 8 + paso + 14

    # -- Opciones ----------------------------------------------------------------
    if not opciones:
        screen.blit(f.render("Llegaste al final de tu rama.", True, COLOR_TEXTO),
                    (caja.x + MARGEN, y))
        y += paso
        if arbol.actual is not None and arbol.actual.detalle_puntos:
            for linea in _partir(arbol.actual.detalle_puntos, f, ancho_texto):
                screen.blit(f.render(linea, True, COLOR_DETALLE), (caja.x + MARGEN, y))
                y += paso
    else:
        aviso = "Escoge una. La otra se cierra por el resto de la ronda."
        # (en una vista angosta no cabía y se cortaba: con letra más chica)
        f_aviso = f
        for px in range(f.get_height(), 8, -1):
            f_aviso = fuente_de_tamano(px)
            if f_aviso.size(tr(aviso))[0] <= caja.width - MARGEN * 2:
                break
        screen.blit(f_aviso.render(aviso, True, COLOR_TENUE), (caja.x + MARGEN, y))
        y += paso + 6

        for i, nodo in enumerate(opciones):
            seleccionada = (i == jugador.cursor)
            alcanza = _puntos(jugador) >= nodo.costo
            descripcion = _partir(nodo.descripcion, f, ancho_texto)[:lineas_desc] if lineas_desc else []
            detalle = _partir(nodo.detalle_puntos, f, ancho_texto)

            alto_fila = paso * (1 + len(descripcion) + len(detalle)) + 8
            fila = pygame.Rect(caja.x + MARGEN - 6, y - 4,
                               caja.width - MARGEN * 2 + 12, alto_fila)
            # Una tarjeta por opción: franja del color del rol; la escogida, dorada.
            vidrio.caja(screen, fila, COLOR_SELECCION if seleccionada else (70, 76, 110),
                        235 if seleccionada else 170, 8)
            if seleccionada:
                vidrio.brillo(screen, (fila.x + 30, fila.centery), fila.h, (40, 34, 10))
            pygame.draw.rect(screen, color_rol if alcanza else COLOR_DESCARTADA,
                             (fila.x + 1, fila.y + 6, 4, fila.h - 12), border_radius=2)

            color = COLOR_TENUE if not alcanza else (
                COLOR_SELECCION if seleccionada else COLOR_TEXTO)
            screen.blit(f.render(nodo.nombre, True, color), (caja.x + MARGEN + 4, y))
            if nodo.costo:
                if alcanza:
                    _pastilla(screen, f, f"{nodo.costo} pts", COLOR_TITULO, (fila.right - 8, y - 1), "topright")
                else:
                    _pastilla(screen, f, tr("  — faltan {}").format(nodo.costo - _puntos(jugador)).strip(" —"),
                              (236, 100, 90), (fila.right - 8, y - 1), "topright")
            y += paso

            for linea in descripcion:
                screen.blit(f.render("   " + linea, True, COLOR_TENUE), (caja.x + MARGEN, y))
                y += paso
            for linea in detalle:
                screen.blit(f.render("   " + linea, True, COLOR_DETALLE), (caja.x + MARGEN, y))
                y += paso
            y += 12

    _pie(screen, caja, f, jugador, "elegir")
    screen.set_clip(clip_previo)


def _pastilla(screen, f, texto, color, punto, ancla="topleft"):
    """Un texto en una pastilla con borde (los puntos, el costo)."""
    img = f.render(texto, True, color)
    caja = img.get_rect(**{ancla: punto}).inflate(16, 2)
    caja = caja.move(-8 if ancla.endswith("right") else 8, 0)
    pygame.draw.rect(screen, (16, 16, 30), caja, border_radius=caja.h // 2)
    pygame.draw.rect(screen, tuple(c * 2 // 3 for c in color), caja, 1, border_radius=caja.h // 2)
    screen.blit(img, img.get_rect(center=caja.center))


def _medidas_arbol(cantidad_niveles, alto_max, fraccion):
    """Alto que ocupa el dibujo del árbol y tamaño de icono que le corresponde.

    `fraccion` es qué parte del panel se le permite ocupar. Se reduce cuando el
    texto de las opciones necesita el espacio: en un viewport de cuatro
    jugadores el árbol con iconos grandes se comía el panel entero y las
    descripciones terminaban debajo del pie.
    """
    alto_arbol = min(int(alto_max * fraccion), cantidad_niveles * 86)
    paso_y = alto_arbol / max(1, cantidad_niveles - 1) if cantidad_niveles > 1 else 0
    return alto_arbol, ajustar_lado(int(paso_y * 0.62) if paso_y else 44)


def _elegir_letra(arbol, opciones, ancho_texto, alto_max):
    """Busca la combinación más generosa con la que TODO el panel cabe.

    Prueba, de mejor a peor: letra grande, árbol grande y descripciones
    completas; luego letra más chica; luego un árbol más bajo; y en último caso
    sin la descripción larga, dejando solo el nombre, el costo y los puntos que
    da, que es lo que el jugador necesita para decidir.

    Devuelve (fuente, alto de línea, alto del contenido, líneas de descripción,
    fracción del panel para el árbol).
    """
    for lineas_desc in (3, 2, 1, 0):
        for fraccion in (0.40, 0.32, 0.25):
            for px in range(19, 11, -1):
                f = fuente_de_tamano(px)
                paso = f.get_linesize() + 2
                alto = _alto_necesario(arbol, opciones, f, paso, ancho_texto,
                                       alto_max, lineas_desc, fraccion)
                if alto <= alto_max:
                    return f, paso, alto, lineas_desc, fraccion
    f = fuente_de_tamano(12)
    return f, f.get_linesize() + 2, alto_max, 0, 0.25


def _alto_necesario(arbol, opciones, f, paso, ancho_texto, alto_max,
                    lineas_desc, fraccion):
    """Cuánto alto pide el panel con esa letra, sumando bloque por bloque."""
    alto = MARGEN * 2
    alto += paso + 4                      # título
    if arbol.vacio:
        return alto + paso * 2 + paso + 6  # aviso + pie

    alto += paso                          # "Nivel X de Y"
    niveles = len({p for _, p in arbol.por_niveles()})
    alto_arbol, lado = _medidas_arbol(niveles, alto_max, fraccion)
    alto += alto_arbol + lado // 2 + 8 + paso + 14

    if not opciones:
        alto += paso                      # "Llegaste al final de tu rama."
        if arbol.actual is not None and arbol.actual.detalle_puntos:
            alto += paso * len(_partir(arbol.actual.detalle_puntos, f, ancho_texto))
        alto += 8
    else:
        alto += paso + 6                  # "Escoge una..."
        for nodo in opciones:
            descripcion = _partir(nodo.descripcion, f, ancho_texto)[:lineas_desc] if lineas_desc else []
            detalle = _partir(nodo.detalle_puntos, f, ancho_texto)
            alto += paso * (1 + len(descripcion) + len(detalle)) + 20
    alto += paso + 6                      # pie
    return alto


def _pie(screen, caja, f, jugador, modo):
    from screens import estilo
    if modo == "elegir":
        texto = (f"[{jugador.pista_mover()}] elegir   "
                 f"[{jugador.nombre_tecla('interactuar')}] desbloquear   "
                 f"[{jugador.nombre_tecla('habilidades')}] cerrar")
    else:
        texto = f"[{jugador.nombre_tecla('habilidades')}] cerrar"
    # Que quepa en el panel (con los nombres largos de teclas en inglés no cabía).
    import re
    traducido = tr(texto)
    teclas = len(re.findall(r"\[[^\]]+\]", traducido))
    limpio = traducido.replace("[", "").replace("]", "")
    letra = f
    for px in range(f.get_height(), 8, -1):
        letra = fuente_de_tamano(px)
        if letra.size(limpio)[0] + teclas * 16 + 36 <= caja.width - 12:
            break
    estilo.pie(screen, texto, caja.bottom - MARGEN - f.get_height() // 2, letra, COLOR_TENUE, x=caja.centerx)


def _partir(texto, f, ancho_max):
    palabras = tr(texto).split()
    if not palabras:
        return [""]
    lineas, actual = [], palabras[0]
    for palabra in palabras[1:]:
        prueba = actual + " " + palabra
        if f.size(prueba)[0] <= ancho_max:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    lineas.append(actual)
    return lineas
