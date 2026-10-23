"""Pantalla de ayuda: la historia, cómo se juega y las estructuras de datos.

La sección de estructuras está aquí a propósito: el laboratorio pide poder
explicar por qué se eligió cada estructura, y conviene que la explicación viva
dentro del juego y no solo en los comentarios del código.

Se dibuja en dos columnas para que quepa completa sin recortarse: a la
izquierda la historia y cómo se juega, a la derecha las estructuras.
"""

from fuentes import fuente_de_tamano


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
    ("Grafo de la nave (BFS)", [
        "Para ir a un ruido, el alien busca camino por una",
        "cuadrícula del mapa (cada celda es un nodo) y rodea paredes.",
    ]),
]

COLOR_FONDO = (30, 30, 55)
COLOR_TEXTO = (255, 255, 255)
COLOR_TENUE = (210, 210, 210)
COLOR_TITULO = (240, 220, 140)


def _ancho_maximo(f, lineas):
    return max((f.size(t)[0] for t in lineas if t), default=0)


def render_ayuda(screen, font=None, small_font=None):
    screen.fill(COLOR_FONDO)
    ancho, alto = screen.get_size()

    # -- Texto de cada columna ------------------------------------------------
    izquierda = [
        (COLOR_TITULO, "La historia"),
        (COLOR_TEXTO, "Una nave alienígena secuestró a cuatro personas."),
        (COLOR_TEXTO, "Despiertan en una prisión y tienen que escapar juntas,"),
        (COLOR_TEXTO, "sin armas: solo sigilo y lo que sabe hacer cada una."),
        (None, ""),
        (COLOR_TITULO, "La misión"),
        (COLOR_TEXTO, "1. Encuentren el código en las notas y abran la puerta."),
        (COLOR_TEXTO, "2. Apaguen las consolas de navegación."),
        (COLOR_TEXTO, "3. Lleven 3 piezas a la cápsula y repárenla"),
        (COLOR_TEXTO, "   (hacen falta los planos: ver NEXUS)."),
        (COLOR_TEXTO, "4. ¡Alerta! Todos a la cápsula antes de que se acabe"),
        (COLOR_TEXTO, "   el tiempo."),
        (None, ""),
        (COLOR_TITULO, "Cómo sobrevivir"),
        (COLOR_TEXTO, "Los aliens oyen tu corazón: entre más asustado, más"),
        (COLOR_TEXTO, "ruido. Camina en sigilo, escóndete en los casilleros y"),
        (COLOR_TEXTO, "no te dejes ver. Si te atrapan vas a una celda y un"),
        (COLOR_TEXTO, "compañero te saca. Tienes 3 vidas."),
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
    # bien tanto maximizada como en la ventana chica de F11.
    margen = 40
    disponible_ancho = (ancho - margen * 3) / 2
    disponible_alto = alto - 80
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
    # Se centra verticalmente: si la letra tuvo que encogerse mucho, el texto
    # queda en el medio en vez de amontonado arriba con media pantalla vacía.
    alto_bloque = max(len(izquierda), len(derecha)) * paso
    y_inicial = max(36, (alto - 50 - alto_bloque) // 2)

    columnas = [(margen, izquierda), (margen * 2 + disponible_ancho, derecha)]
    for x, bloque in columnas:
        y = y_inicial
        for color, linea in bloque:
            if linea:
                screen.blit(f.render(linea, True, color), (int(x), int(y)))
            y += paso

    aviso = f.render("[ENTER] Volver", True, (194, 216, 248))
    screen.blit(aviso, aviso.get_rect(center=(ancho // 2, alto - 26)))
