"""Pantalla de créditos: un rollo que sube y vuelve a empezar.

Antes el texto se dibujaba en `80 + scroll_y`, o sea que BAJABA, y el
desplazamiento se guardaba en `Game.credit_scroll`. Eso daba dos problemas:
entrar y salir varias veces retomaba donde se había quedado en vez de empezar
de nuevo, y una vez que las líneas se iban por abajo no volvían nunca.

Ahora sube (como cualquier rollo de créditos), arranca desde abajo del todo y
al terminar vuelve a empezar solo. `reiniciar_scroll()` da el valor inicial, y
juego/app.py lo llama cada vez que se entra a la pantalla.
"""

import pygame

from juego.fuentes import fuente_de_tamano


COLOR_FONDO = (15, 15, 25)
COLOR_TITULO = (255, 214, 64)
COLOR_TEXTO = (245, 246, 252)
COLOR_TENUE = (168, 176, 214)

VELOCIDAD = 0.6  # píxeles por frame

# (texto, estilo). "espacio" deja un hueco; "logo" es el logo de NEXUS
# (Imagenes/UI/nexus_logo.png; si no está, el texto como título).
LINEAS = [
    ("NEXUS", "logo"),
    ("En el vacío, nada está realmente solo", "tenue"),
    ("", "espacio"),
    ("Estructura de Datos II", "tenue"),
    ("Universidad del Norte", "tenue"),
    ("", "espacio"),
    ("", "espacio"),
    ("Equipo", "titulo"),
    ("Joseph Arias", "nombre"),
    ("Diego Payares", "nombre"),
    ("Anny Delgado", "nombre"),
    ("Juan David Campo", "nombre"),
    ("", "espacio"),
    ("", "espacio"),
    ("Hecho con Python y Pygame", "tenue"),
    ("Tipografía: Determination Mono", "tenue"),
    # CC-BY 3.0: hay que dar el crédito así (opengameart.org/content/ominous-sci-fi-menu-looping).
    ("Música del menú: \"Ominous Sci-Fi Menu\"", "tenue"),
    ("de Eric Matyas · www.soundimage.org", "tenue"),
    ("", "espacio"),
    ("Música de los finales", "titulo"),
    # (CC BY: hay que dar el crédito así; juego/musica_final.py)
    ("\"Disturbed Soundscape\" y \"Sci-Fi Close\"", "tenue"),
    ("de Eric Matyas · www.soundimage.org", "tenue"),
    ("\"The far side of Proxima Centauri\" de Sascha Ende", "tenue"),
    ("ende.app · CC BY 4.0", "tenue"),
    ("\"Bittersweet Ending\" de Arold Valda · CC BY 4.0", "tenue"),
    ("\"Bittersweet\" de Emma M. Andersson (dominio público)", "tenue"),
    ("", "espacio"),
    ("Narrador", "titulo"),
    ("Lucas Manjarrez", "nombre"),
    # (el plan gratis de ElevenLabs pide dar el crédito: docs/guion_narrador.md)
    ("Voces de los agentes generadas con ElevenLabs", "tenue"),
    ("", "espacio"),
    ("", "espacio"),
    ("Gracias por jugar.", "titulo"),
]


def reiniciar_scroll():
    """Valor inicial del desplazamiento: el rollo empieza fuera de pantalla."""
    return 0.0


def _alto_linea(texto, estilo, paso, alto_logo):
    if estilo == "logo":
        return alto_logo + paso
    if estilo == "titulo":
        return int(paso * 1.6)
    return paso


_fundidos = {}


def _fundido(ancho, alto_banda, arriba):
    """Una banda que oscurece hacia el borde, para que el rollo se desvanezca."""
    clave = (ancho, alto_banda, arriba)
    img = _fundidos.get(clave)
    if img is None:
        img = pygame.Surface((ancho, alto_banda), pygame.SRCALPHA)
        for y in range(alto_banda):
            k = 1 - y / alto_banda if arriba else y / alto_banda
            pygame.draw.line(img, (8, 8, 20, int(235 * k ** 1.5)), (0, y), (ancho, y))
        _fundidos.clear()
        _fundidos[clave] = img
    return img


def render_creditos(screen, font=None, scroll=0.0, pausado=False):
    """Dibuja el rollo y devuelve el desplazamiento siguiente.

    El desplazamiento se mide en píxeles recorridos desde el inicio. Cuando el
    rollo entero ya pasó por arriba, vuelve a cero y empieza de nuevo.
    """
    from screens import estilo as est
    from juego import perfiles
    est.fondo(screen)
    ancho, alto = screen.get_size()

    tam_titulo = max(18, min(34, ancho // 42))
    f_texto = fuente_de_tamano(max(14, min(24, ancho // 60)))
    paso = f_texto.get_linesize() + 10
    alto_logo = max(90, min(240, alto // 4))

    alto_rollo = sum(_alto_linea(t, e, paso, alto_logo) for t, e in LINEAS)
    # El rollo recorre su propio alto más una pantalla, para entrar desde abajo
    # y salir del todo por arriba antes de reiniciarse.
    recorrido = alto_rollo + alto

    y = alto - scroll
    nombre = 0
    for texto, estilo in LINEAS:
        h = _alto_linea(texto, estilo, paso, alto_logo)
        # Solo se dibuja lo que se ve, para no pedirle trabajo de más.
        if texto and -h < y < alto + h:
            if estilo == "logo":
                imagen = perfiles.logo(alto_logo, completo=True)
                if imagen is not None:
                    centro = (ancho // 2, int(y + alto_logo // 2))
                    luz = est._brillo_elipse((int(imagen.get_width() * 1.6), int(alto_logo * 1.2)), (60, 40, 110))
                    screen.blit(luz, luz.get_rect(center=centro), special_flags=pygame.BLEND_RGB_ADD)
                    screen.blit(imagen, imagen.get_rect(center=centro))
                else:
                    est.titulo(screen, texto, (ancho // 2, int(y + alto_logo // 2)), tam_titulo + 12)
            elif estilo == "titulo":
                est.titulo(screen, texto, (ancho // 2, int(y + paso * 0.6)), tam_titulo, est.COLOR_ORO,
                           (255, 170, 60))
            elif estilo == "nombre":
                color = est.COLOR_JUGADOR[nombre % 4]
                rect = est.texto(screen, texto, f_texto, (ancho // 2, int(y + paso // 2)), est.COLOR_TEXTO, "center")
                for lado in (-1, 1):
                    cx = rect.centerx + lado * (rect.w // 2 + 22)
                    cy = rect.centery
                    pygame.draw.polygon(screen, color, [(cx, cy - 5), (cx + 5, cy), (cx, cy + 5), (cx - 5, cy)])
            else:
                color = est.COLOR_TENUE if estilo == "tenue" else est.COLOR_TEXTO
                est.texto(screen, texto, f_texto, (ancho // 2, int(y + paso // 2)), color, "center")
        if estilo == "nombre":
            nombre += 1
        y += h

    # Arriba y abajo el rollo se desvanece.
    banda = max(60, alto // 7)
    screen.blit(_fundido(ancho, banda, True), (0, 0))
    screen.blit(_fundido(ancho, banda, False), (0, alto - banda))
    est.pie(screen, "[ENTER] volver", alto - 32)

    if pausado:
        return scroll
    siguiente = scroll + VELOCIDAD
    return siguiente if siguiente < recorrido else 0.0
