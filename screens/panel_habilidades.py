"""Panel del árbol de habilidades, dibujado dentro del viewport de un jugador.

Dibuja el árbol binario completo —incluidas las ramas que el jugador ya perdió,
en gris— porque ver lo que se cerró es la mitad de la gracia: el árbol enseña
que elegir DEBATE fue renunciar a PROPUESTA.

Las posiciones salen del recorrido por niveles (BFS) del árbol: la profundidad
da la fila, y dentro de cada fila los nodos se reparten el ancho por igual.
"""

import os

import pygame

from data.habilidades import ARBOLES_POR_ROL
from fuentes import fuente_de_tamano


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


def _apagar(imagen, alpha=90):
    """Copia en gris y translúcida, para las ramas que el jugador ya perdió."""
    copia = imagen.copy()
    gris = pygame.Surface(copia.get_size(), pygame.SRCALPHA)
    gris.fill((90, 92, 110, 255))
    copia.blit(gris, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
    copia.set_alpha(alpha)
    return copia


# Clave del nodo -> nombre del archivo. Casi todas coinciden con la clave en
# minúscula capitalizada (que es lo que hace el respaldo), pero el arte no
# siempre usa la misma palabra: ACORRALAR se llama Acorralada.png.
#
# Falta CRISIS.png del influencer. Mientras no esté, ese nodo se dibuja como
# una pastilla con la inicial y el juego sigue igual; apenas aparezca el
# archivo se usa solo, sin tocar código.
NOMBRE_ARCHIVO = {
    # Candidato
    "LIDERAZGO": "Liderazgo",
    "DEBATE": "Debate",
    "PROPUESTA": "Propuesta",
    "REPLICA": "Replica",
    "ACORRALAR": "Acorralada",
    "PRIORIDAD": "Prioridad",
    "IMPACTO": "Impacto",
    # Influencer
    "INFLUENCIA": "Influencia",
    "ANTICIPO": "Anticipo",
    "TENDENCIA": "Tendencia",
    "BLINDAJE": "Blindaje",
    "CRISIS": "Crisis",
    "DESAFIO": "Desafio",
    "MOVILIZACION": "Movilizacion",
}


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


def render_panel_habilidades(screen, vista, jugador):
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

    fondo = pygame.Surface(caja.size, pygame.SRCALPHA)
    fondo.fill(COLOR_FONDO)
    screen.blit(fondo, caja.topleft)
    pygame.draw.rect(screen, COLOR_BORDE, caja, 3)

    clip_previo = screen.get_clip()
    screen.set_clip(caja)

    y = caja.y + MARGEN
    titulo = f"Árbol de habilidades · {jugador.rol}"
    screen.blit(f.render(titulo, True, COLOR_TITULO), (caja.x + MARGEN, y))
    puntos = f.render(f"{jugador.puntos} pts", True, COLOR_TITULO)
    screen.blit(puntos, (caja.right - puntos.get_width() - MARGEN, y))
    y += paso + 4

    if arbol.vacio:
        for linea in ["Este rol todavía no tiene árbol de habilidades definido.",
                      "El del candidato y el del influencer ya están."]:
            screen.blit(f.render(linea, True, COLOR_TENUE), (caja.x + MARGEN, y))
            y += paso
        _pie(screen, caja, f, jugador, "cerrar")
        screen.set_clip(clip_previo)
        return

    screen.blit(f.render(f"Nivel {len(arbol.desbloqueadas())} de {arbol.altura()}",
                        True, COLOR_TENUE), (caja.x + MARGEN, y))
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

    for nodo, _ in arbol.por_niveles():
        for hijo in nodo.hijos:
            pygame.draw.line(screen,
                             COLOR_LINEA_MUERTA if hijo.descartada else COLOR_LINEA,
                             centros[id(nodo)], centros[id(hijo)], 2)

    for nodo, _ in arbol.por_niveles():
        cx, cy = centros[id(nodo)]
        if nodo.desbloqueada:
            borde, color_texto = COLOR_DESBLOQUEADA, COLOR_DESBLOQUEADA
        elif nodo.descartada:
            borde, color_texto = COLOR_DESCARTADA, (132, 134, 150)
        elif nodo.clave in claves_opciones:
            borde, color_texto = COLOR_DISPONIBLE, COLOR_DISPONIBLE
        else:
            borde, color_texto = (60, 64, 92), (130, 136, 168)

        icono = icono_habilidad(jugador.rol, nodo.clave, lado)
        marco = pygame.Rect(0, 0, lado + 8, lado + 8)
        marco.center = (cx, cy)

        if icono is not None:
            screen.blit(_apagar(icono) if nodo.descartada else icono,
                        icono.get_rect(center=marco.center))
        else:
            pygame.draw.rect(screen, borde, marco, border_radius=6)
            inicial = f.render(nodo.nombre[:1], True, (18, 19, 32))
            screen.blit(inicial, inicial.get_rect(center=marco.center))
        pygame.draw.rect(screen, borde, marco, 2, border_radius=6)

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
                screen.blit(f.render(linea, True, COLOR_TENUE), (caja.x + MARGEN, y))
                y += paso
    else:
        screen.blit(f.render("Escoge una. La otra se cierra por el resto de la ronda.",
                            True, COLOR_TENUE), (caja.x + MARGEN, y))
        y += paso + 6

        for i, nodo in enumerate(opciones):
            seleccionada = (i == jugador.cursor)
            alcanza = jugador.puntos >= nodo.costo
            descripcion = _partir(nodo.descripcion, f, ancho_texto)[:lineas_desc] if lineas_desc else []
            detalle = _partir(nodo.detalle_puntos, f, ancho_texto)

            alto_fila = paso * (1 + len(descripcion) + len(detalle)) + 8
            fila = pygame.Rect(caja.x + MARGEN - 6, y - 4,
                               caja.width - MARGEN * 2 + 12, alto_fila)
            if seleccionada:
                pygame.draw.rect(screen, COLOR_SELECCION_FONDO, fila)
                pygame.draw.rect(screen, COLOR_SELECCION, fila, 2)

            color = COLOR_TENUE if not alcanza else (
                COLOR_SELECCION if seleccionada else COLOR_TEXTO)
            encabezado = f"{'> ' if seleccionada else '  '}{nodo.nombre}"
            if nodo.costo:
                encabezado += f"  ({nodo.costo} pts)"
                if not alcanza:
                    encabezado += f"  — te faltan {nodo.costo - jugador.puntos}"
            screen.blit(f.render(encabezado, True, color), (caja.x + MARGEN, y))
            y += paso

            for linea in descripcion + detalle:
                screen.blit(f.render("   " + linea, True, COLOR_TENUE),
                            (caja.x + MARGEN, y))
                y += paso
            y += 12

    _pie(screen, caja, f, jugador, "elegir")
    screen.set_clip(clip_previo)


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
        alto += paso * 2
    else:
        alto += paso + 6                  # "Escoge una..."
        for nodo in opciones:
            descripcion = _partir(nodo.descripcion, f, ancho_texto)[:lineas_desc] if lineas_desc else []
            detalle = _partir(nodo.detalle_puntos, f, ancho_texto)
            alto += paso * (1 + len(descripcion) + len(detalle)) + 20
    alto += paso + 6                      # pie
    return alto


def _pie(screen, caja, f, jugador, modo):
    if modo == "elegir":
        texto = (f"[{jugador.pista_mover()}] elegir   "
                 f"[{jugador.nombre_tecla('interactuar')}] desbloquear   "
                 f"[{jugador.nombre_tecla('habilidades')}] cerrar")
    else:
        texto = f"[{jugador.nombre_tecla('habilidades')}] cerrar"
    etiqueta = f.render(texto, True, COLOR_TENUE)
    screen.blit(etiqueta, (caja.x + MARGEN, caja.bottom - MARGEN - etiqueta.get_height()))


def _partir(texto, f, ancho_max):
    palabras = texto.split()
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
