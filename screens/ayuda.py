"""Pantalla de ayuda: objetivo, controles, indicadores y las estructuras de datos.

La sección de estructuras está aquí a propósito: el laboratorio pide poder
explicar por qué se eligió cada estructura, y conviene que la explicación viva
dentro del juego y no solo en los comentarios del código.

Se dibuja en dos columnas para que quepa completa sin recortarse: a la
izquierda cómo se juega y qué significan los indicadores, a la derecha los tres
árboles.
"""

import pygame

from config import INDICADORES_CIUDAD_INICIALES, INDICADOR_LABELS, ROLES_JUGABLES
from fuentes import fuente_de_tamano


DESCRIPCION_INDICADORES = {
    "informacion_verificada": "qué tanto de lo que circula está comprobado",
    "confianza_ciudadana": "cuánto confían los ciudadanos entre sí",
    "convivencia": "qué tan sano es el ambiente de la ciudad",
    "bienestar_digital": "qué tan sana es la relación con la red social",
    "desinformacion": "cuánta mentira circula (mientras más baja, mejor)",
    "conflictos": "cuántas peleas genera la campaña (mejor baja)",
}

# (nombre, líneas de explicación). Se corresponde con Estructuras/.
ARBOLES = [
    ("ABB de publicaciones", [
        "Ordena las publicaciones por su veracidad, de 0 a 100.",
        "El juego siempre saca la más dudosa, que es la primera del",
        "recorrido inorden. Se eliminan del árbol al atenderlas.",
        "Con [TAB] se ve dibujado y cambiando en vivo.",
    ]),
    ("Árbol N-ario de decisión", [
        "Uno por publicación. La raíz es la publicación, los hijos son",
        "tus cuatro opciones (verificar, compartir, ignorar, reportar)",
        "y los nietos las consecuencias posibles. Las hojas son las",
        "que mueven los indicadores de la ciudad.",
    ]),
    ("Árbol N-ario de diálogo", [
        "Cada conversación es un árbol. Lo que respondes elige la rama",
        "por la que bajas y no se puede volver a subir, así que las",
        "respuestas distintas llevan a finales distintos.",
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
        (COLOR_TITULO, "Objetivo"),
        (COLOR_TEXTO, "Que Ciudad Nova llegue a las elecciones con la mejor"),
        (COLOR_TEXTO, "información y la menor desinformación posible."),
        (None, ""),
        (COLOR_TITULO, "Cómo se juega"),
        (COLOR_TEXTO, "En la ciudad presionas [E] para ver una publicación"),
        (COLOR_TEXTO, "pendiente y eliges qué hacer con ella con [1] a [4]:"),
        (COLOR_TEXTO, "verificar, compartir, ignorar o reportar. Cada decisión"),
        (COLOR_TEXTO, "mueve los indicadores y te da puntaje."),
        (None, ""),
        (COLOR_TEXTO, "Con [D] hablas con un habitante. Lo que le respondas"),
        (COLOR_TEXTO, "también cuenta: ayudarlo a dudar de un rumor mejora la"),
        (COLOR_TEXTO, "información verificada; animarlo a regarlo la empeora."),
        (None, ""),
        (COLOR_TITULO, "Cómo ganar"),
        (COLOR_TEXTO, "Terminar con la confianza ciudadana y la información"),
        (COLOR_TEXTO, "verificada altas, y la desinformación y los conflictos"),
        (COLOR_TEXTO, "bajos."),
        (None, ""),
        (COLOR_TENUE, f"Roles: {', '.join(ROLES_JUGABLES)}"),
        (None, ""),
        (COLOR_TITULO, "Indicadores"),
    ]
    for clave in INDICADORES_CIUDAD_INICIALES:
        nombre = INDICADOR_LABELS.get(clave, clave)
        descripcion = DESCRIPCION_INDICADORES.get(clave, "")
        izquierda.append((COLOR_TENUE,
                          f"- {nombre}: {descripcion}" if descripcion else f"- {nombre}"))

    derecha = [(COLOR_TITULO, "Estructuras de datos que usa el juego"), (None, "")]
    for nombre, lineas in ARBOLES:
        derecha.append((COLOR_TEXTO, nombre))
        derecha.extend((COLOR_TENUE, "  " + linea) for linea in lineas)
        derecha.append((None, ""))
    derecha.append((COLOR_TITULO, "Por qué árboles y no listas"))
    derecha.extend((COLOR_TENUE, "  " + linea) for linea in [
        "Porque las tres cosas que el juego necesita —mantener las",
        "publicaciones ordenadas, buscar por nivel de veracidad y",
        "retirar las ya atendidas— son O(log n) en un ABB, y en una",
        "lista habría que recorrerla o reordenarla en cada turno.",
        "Y porque las decisiones y los diálogos son ramificados por",
        "naturaleza: una opción abre otras, y eso es un árbol.",
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
