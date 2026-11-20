"""Pantalla de ayuda: la historia, cómo se juega y las estructuras de datos.

La sección de estructuras está aquí a propósito: el laboratorio pide poder
explicar por qué se eligió cada estructura, y conviene que la explicación viva
dentro del juego y no solo en los comentarios del código.

Se dibuja en dos columnas para que quepa completa sin recortarse: a la
izquierda la historia y cómo se juega, a la derecha las estructuras.
"""

import pygame

from juego.fuentes import fuente_de_tamano


# (nombre, líneas de explicación). Se corresponde con Estructuras/ y navegacion.py.
ARBOLES = [
    ("Árbol de comportamiento de los aliens", [
        "Cada frame el alien baja de la raíz a una hoja respondiendo",
        "preguntas (¿ve a alguien?, ¿oye un ruido?) y la hoja dice",
        "qué hace: patrullar, perseguir, revisar... Se ve en Pausa > Opciones.",
    ]),
    ("Árbol binario de habilidades", [
        "Cada rol escoge una de dos ramas; la otra se cierra para",
        "toda la ronda. Por niveles (BFS) para dibujarlo.",
    ]),
    ("Árbol de comportamiento del Cambiaformas", [
        "Otro árbol binario con sus propias preguntas: ¿lo escoltan?,",
        "¿ya conoce a su presa y está sola y desprevenida?, ¿se aburrió",
        "del grupo? Hojas: estudiar, rondar, revelarse, alejarse...",
    ]),
    ("Árbol N-ario de logros", [
        "Cada logro abre otros, como en Minecraft. Al conseguir uno",
        "se sube por los padres hasta la raíz marcando los que falten.",
        "Se dibuja en postorden: cada padre al medio de sus hijos.",
        "Se ve en Pausa > Logros.",
    ]),
    ("Grafo de NEXUS (la red social)", [
        "Cada cuenta es un nodo; lo que publica llega a sus seguidores",
        "nivel por nivel (BFS). Rastrear un rumor = camino más corto;",
        "reportar un bot = borrar su nodo. Las barras = % de verdes/rojos.",
    ]),
    ("Grafo de la nave (A*)", [
        "Para ir a un ruido, el alien busca camino por una",
        "cuadrícula del mapa (cada celda es un nodo) y rodea paredes.",
        "A* = un BFS que prueba primero las celdas que van hacia la meta.",
    ]),
]

COLOR_FONDO = (30, 30, 55)
COLOR_TEXTO = (240, 242, 252)
COLOR_TENUE = (180, 188, 220)
COLOR_TITULO = (240, 220, 140)


def _ancho_maximo(f, lineas):
    return max((f.size(t)[0] for t in lineas if t), default=0)


_capas = {}


def render_ayuda(screen, font=None, small_font=None):
    """El fondo se mueve; los paneles y el texto (quietos) se dibujan una vez
    por tamaño de ventana e idioma y se guardan."""
    from screens import estilo
    from juego import idioma
    estilo.fondo(screen)
    ancho, alto = screen.get_size()
    arriba = max(56, min(96, alto // 10))
    estilo.titulo(screen, "AYUDA", (ancho // 2, arriba // 2 + 4), max(22, min(40, arriba // 2)))
    clave = (ancho, alto, idioma.IDIOMA)
    capa = _capas.get(clave)
    if capa is None:
        _capas.clear()
        capa = pygame.Surface((ancho, alto), pygame.SRCALPHA)
        _dibujar_paneles(capa)
        _capas[clave] = capa
    screen.blit(capa, (0, 0))
    estilo.pie(screen, "[ENTER] Volver", alto - 32)


def _dibujar_paneles(screen):
    ancho, alto = screen.get_size()

    # -- Texto de cada columna ------------------------------------------------
    izquierda = [
        (COLOR_TITULO, "La historia"),
        (COLOR_TEXTO, "Una nave alienígena secuestró a cuatro personas."),
        (COLOR_TEXTO, "Despiertan encerradas y tienen que escapar juntas,"),
        (COLOR_TEXTO, "sin armas: solo sigilo y lo que sabe hacer cada una."),
        (None, ""),
        (COLOR_TITULO, "La misión"),
        (COLOR_TEXTO, "1. Busquen el código en las notas y abran la puerta."),
        (COLOR_TEXTO, "2. Apaguen las consolas de navegación."),
        (COLOR_TEXTO, "3. Lleven 3 piezas a la cápsula y repárenla"),
        (COLOR_TEXTO, "   (hacen falta los planos: ver NEXUS)."),
        (COLOR_TEXTO, "4. ¡Alerta! Todos a la cápsula. No hay límite de"),
        (COLOR_TEXTO, "   tiempo: pierden si los atrapan a todos."),
        (None, ""),
        (COLOR_TITULO, "Cómo sobrevivir"),
        (COLOR_TEXTO, "Los aliens oyen tu corazón: entre más asustado, más"),
        (COLOR_TEXTO, "ruido. Camina en sigilo, escóndete en los casilleros y"),
        (COLOR_TEXTO, "no te dejes ver. Si te atrapan vas a una celda y un"),
        (COLOR_TEXTO, "compañero te saca. Las vidas dependen de la"),
        (COLOR_TEXTO, "dificultad (en Fácil y Normal también sales solo)."),
        (None, ""),
        (COLOR_TITULO, "El Cambiaformas"),
        (COLOR_TEXTO, "Se disfraza de prisionero y estudia a su presa antes de"),
        (COLOR_TEXTO, "atacar. No habla, se te pega y su nombre falla. No te"),
        (COLOR_TEXTO, "quedes solo ni de espaldas. A los prisioneros verdes"),
        (COLOR_TEXTO, "puedes llevarlos a la cápsula (\"¿vienes conmigo?\")."),
        (None, ""),
        (COLOR_TITULO, "Los roles"),
        (COLOR_TENUE, "Tecnomante: terminales, hackeo y consolas."),
        (COLOR_TENUE, "Forjador: piezas, sellos, señuelos y la cápsula."),
        (COLOR_TENUE, "Biomante: siente el pulso, cura y recarga al equipo."),
        (COLOR_TENUE, "Resonante: oye a los aliens y les manda señales falsas."),
        (None, ""),
        (COLOR_TITULO, "NEXUS (en tu celular)"),
        (COLOR_TEXTO, "Los aliens riegan rumores falsos. Vayan al lugar,"),
        (COLOR_TEXTO, "saquen una foto y desmiéntanlos: si la tripulación"),
        (COLOR_TEXTO, "les cree, les pasan los planos de la cápsula."),
        (COLOR_TEXTO, "No compartan sin verificar y cuiden su ubicación."),
    ]

    derecha = [(COLOR_TITULO, "Estructuras de datos que usa el juego"), (None, "")]
    for nombre, lineas in ARBOLES:
        derecha.append((COLOR_TEXTO, nombre))
        derecha.extend((COLOR_TENUE, "  " + linea) for linea in lineas)
        derecha.append((None, ""))
    derecha.append((COLOR_TITULO, "Por qué árboles y no listas"))
    derecha.extend((COLOR_TENUE, "  " + linea) for linea in [
        "La IA de los aliens, las habilidades y los logros se",
        "ramifican: una respuesta o una elección abre otras. En una",
        "lista no se ve de dónde sale cada cosa ni qué se cierra.",
    ])

    # -- Elegir el tamaño de letra que hace que todo quepa --------------------
    # Se busca de grande a chico el primer tamaño en el que las dos columnas
    # caben a lo ancho y la más larga cabe a lo alto. Así la pantalla se ve
    # bien tanto maximizada como en la ventana chica de F11. Cada columna va
    # en un panel de vidrio (screens/estilo.py), con su relleno por dentro.
    from screens import estilo
    margen = max(20, min(40, ancho // 40))
    relleno = 22
    arriba = max(56, min(96, alto // 10))        # el título
    abajo = 64                                    # las teclas
    disponible_ancho = (ancho - margen * 3) / 2 - relleno * 2 - 14
    disponible_alto = alto - arriba - abajo - relleno * 2
    textos_izq = [t for _, t in izquierda]
    textos_der = [t for _, t in derecha]

    f = None
    for px in range(22, 9, -1):
        candidata = fuente_de_tamano(px)
        cabe_ancho = (_ancho_maximo(candidata, textos_izq) <= disponible_ancho
                      and _ancho_maximo(candidata, textos_der) <= disponible_ancho)
        paso = candidata.get_linesize() + 2
        cabe_alto = max(len(izquierda), len(derecha)) * paso <= disponible_alto
        if cabe_ancho and cabe_alto:
            f = candidata
            break
    if f is None:
        f = fuente_de_tamano(10)

    paso = f.get_linesize() + 2
    # Los paneles miden lo que mide su texto y quedan en el medio: si la letra
    # tuvo que encogerse mucho, no queda media pantalla vacía.
    alto_bloque = max(len(izquierda), len(derecha)) * paso
    alto_panel = alto_bloque + relleno * 2
    y_panel = max(arriba, (arriba + alto - abajo - alto_panel) // 2)
    ancho_panel = (ancho - margen * 3) // 2

    colores_seccion = [estilo.COLOR_ORO, estilo.COLOR_NEON, (110, 220, 140), estilo.COLOR_ROSA,
                       (255, 150, 90), (170, 140, 255), (120, 200, 255)]
    columnas = [(margen, izquierda, estilo.COLOR_NEON), (margen * 2 + ancho_panel, derecha, estilo.COLOR_ROSA)]
    for x, bloque, color_panel in columnas:
        estilo.panel(screen, pygame.Rect(x, y_panel, ancho_panel, alto_panel), color_panel)
        y = y_panel + relleno
        x_texto = x + relleno + 14
        seccion = 0
        for color, linea in bloque:
            if not linea:
                y += paso
                continue
            if color == COLOR_TITULO:
                # Título de sección: un rombito y una raya de su color.
                tono = colores_seccion[seccion % len(colores_seccion)]
                seccion += 1
                cy = y + f.get_height() // 2
                k = max(3, f.get_height() // 5)
                pygame.draw.polygon(screen, tono, [(x_texto - 12, cy - k), (x_texto - 12 + k, cy),
                                                   (x_texto - 12, cy + k), (x_texto - 12 - k, cy)])
                rect = estilo.texto(screen, linea, f, (x_texto, y), tono)
                fin = x + ancho_panel - relleno
                if rect.right + 14 < fin:
                    pygame.draw.line(screen, estilo._mezclar(tono, (20, 20, 40), 0.65),
                                     (rect.right + 12, cy), (fin, cy), 1)
            elif bloque is derecha and color == COLOR_TEXTO:
                # El nombre de cada estructura.
                estilo.texto(screen, linea, f, (x_texto, y), (150, 225, 255))
            else:
                estilo.texto(screen, linea, f, (x_texto, y), color, sombra=False)
            y += paso
