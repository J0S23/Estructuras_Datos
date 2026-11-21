"""La foto: al llegar al lugar de un rumor (o al arreglar lo de una noticia),
la cámara del celular hace clic.

Lo que se ve, en la vista de quien la tomó (~1,7 s):
1. El visor: cuatro esquinas que se cierran sobre lo que tiene alrededor.
2. El flash: la vista se pone blanca y se apaga.
3. La foto: una polaroid con lo que se veía en ese momento (la vista misma,
   un poco aclarada por el flash) y el nombre del lugar abajo; aparece
   ladeada, se queda un momento y vuela arriba, al aviso de NEXUS (donde se
   publica).

redes/nexus._tomar_foto sube `jugador.foto_n` (y pone `foto_lugar`) y suena
"foto" (el obturador, Audio/generar_sonidos.generar_foto). Aquí se nota que
`foto_n` subió: como los atributos del jugador viajan en las instantáneas,
en el cliente de red se ve igual. screens/partida.render_partida llama
`capturar` justo después de dibujar el mundo de cada vista (para sacar la
imagen sin el HUD) y `dibujar` encima de casi todo. Sin "Efectos visuales"
(juego/efectos.ACTIVOS) la foto no se ladea (rotar cuesta en un PC lento).
"""

import pygame

from juego import efectos
from juego.fuentes import fuente_de_tamano

DURACION_MS = 1700
VISOR_MS = 320          # las esquinas que se cierran
FLASH_MS = 280          # el blanco que se apaga
APARECE_MS = 120        # cuándo sale la polaroid
QUIETA_HASTA_MS = 1050  # desde ahí vuela al aviso de NEXUS
COLOR_PAPEL = (246, 244, 236)
COLOR_TINTA = (52, 56, 70)

# puesto del jugador -> [foto_n visto, inicio (ms) o None, imagen, lugar, polaroid armada]
_estado = {}
# id del rumor o noticia -> la foto que se tomó ahí (TAM_GUARDADA), para el
# celular (las publicaciones del equipo); y sus copias achicadas.
_por_pub = {}
_achicadas = {}
TAM_GUARDADA = (360, 270)
MUNDO_FOTO = (560, 420)     # lo que entra en la foto sacada del mapa (px del mundo)


def _ahora():
    return pygame.time.get_ticks()      # (las pruebas lo cambian para dibujar un momento exacto)


def olvidar():
    """Al empezar otra partida (juego/app._olvidar_partida_anterior)."""
    _estado.clear()
    _por_pub.clear()
    _achicadas.clear()


def _clave(jugador):
    puesto = getattr(jugador, "puesto", None)
    return puesto if puesto is not None else id(jugador)


def _marco(vista):
    """Lo que entra en la foto: un rectángulo en el centro de la vista (la
    cámara sigue al jugador)."""
    lado = int(min(vista.width, vista.height * 1.25) * 0.5)
    r = pygame.Rect(0, 0, lado, int(lado * 0.75))
    r.center = vista.center
    return r.clip(vista)


def capturar(screen, vista, jugador, ahora=None):
    """Después de dibujar el mundo de la vista: si tomó una foto nueva, se
    guarda lo que se ve."""
    n = getattr(jugador, "foto_n", 0) or 0
    clave = _clave(jugador)
    e = _estado.get(clave)
    if e is None or n < e[0]:
        # Primera vez que se ve a este jugador (o es otra partida): sin animar.
        _estado[clave] = [n, None, None, "", None]
        return
    if n == e[0]:
        return
    ahora = _ahora() if ahora is None else ahora
    marco = _marco(vista)
    imagen = None
    if marco.width > 8 and marco.height > 8:
        try:
            imagen = screen.subsurface(marco).copy()
            imagen.fill((38, 38, 34), special_flags=pygame.BLEND_RGB_ADD)    # (el flash la aclara)
        except (ValueError, pygame.error):
            imagen = None
    _estado[clave] = [n, ahora, imagen, getattr(jugador, "foto_lugar", "") or "", None]
    pub_id = getattr(jugador, "foto_pub", 0)
    if imagen is not None and pub_id:
        _por_pub[pub_id] = pygame.transform.smoothscale(imagen, TAM_GUARDADA)


def activa(jugador, ahora=None):
    e = _estado.get(_clave(jugador))
    if e is None or e[1] is None:
        return False
    ahora = _ahora() if ahora is None else ahora
    return ahora - e[1] < DURACION_MS


def _polaroid(e, ancho_foto):
    """La polaroid armada una vez: papel, la foto y el lugar abajo."""
    if e[4] is not None:
        return e[4]
    imagen = e[2]
    alto_foto = int(ancho_foto * 0.75)
    borde = max(6, ancho_foto // 22)
    f = fuente_de_tamano(max(12, min(22, ancho_foto // 12)))
    pie = f.get_linesize() + borde
    papel = pygame.Surface((ancho_foto + 2 * borde, alto_foto + borde + pie), pygame.SRCALPHA)
    papel.fill(COLOR_PAPEL)
    hueco = pygame.Rect(borde, borde, ancho_foto, alto_foto)
    if imagen is not None:
        papel.blit(pygame.transform.smoothscale(imagen, hueco.size), hueco)
    else:
        papel.fill((200, 205, 215), hueco)
    pygame.draw.rect(papel, (190, 186, 175), hueco, 1)
    # Una camarita y el lugar.
    texto = f.render(e[3] or "NEXUS", True, COLOR_TINTA)
    cam = pygame.Rect(0, 0, int(f.get_height() * 0.9), int(f.get_height() * 0.62))
    total = cam.width + 8 + texto.get_width()
    x = (papel.get_width() - total) // 2
    cy = hueco.bottom + pie // 2 + 1
    cam.midleft = (x, cy)
    pygame.draw.rect(papel, COLOR_TINTA, cam, border_radius=3)
    pygame.draw.rect(papel, COLOR_TINTA, (cam.x + cam.width // 4, cam.y - 3, cam.width // 3, 4))
    pygame.draw.circle(papel, COLOR_PAPEL, cam.center, max(2, cam.height // 3))
    papel.blit(texto, texto.get_rect(midleft=(cam.right + 8, cy)))
    pygame.draw.rect(papel, (205, 200, 188), papel.get_rect(), 1)
    e[4] = papel
    return papel


def _esquinas(screen, rect, color, largo, grueso):
    x0, y0, x1, y1 = rect.left, rect.top, rect.right - 1, rect.bottom - 1
    for (x, y, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
        pygame.draw.line(screen, color, (x, y), (x + dx * largo, y), grueso)
        pygame.draw.line(screen, color, (x, y), (x, y + dy * largo), grueso)


def _suave(t):
    """0..1 que arranca rápido y frena al final."""
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def dibujar(screen, vista, jugador, ahora=None):
    e = _estado.get(_clave(jugador))
    if e is None or e[1] is None:
        return
    ahora = _ahora() if ahora is None else ahora
    t = ahora - e[1]
    if t >= DURACION_MS or t < 0:
        e[1], e[2], e[4] = None, None, None      # (se suelta la imagen)
        return
    anterior = screen.get_clip()
    screen.set_clip(vista.clip(anterior) if anterior else vista)
    marco = _marco(vista)

    # 1. El visor: las esquinas se cierran sobre el marco.
    if t < VISOR_MS:
        k = _suave(t / VISOR_MS)
        r = marco.inflate(int(marco.width * 0.35 * (1 - k)), int(marco.height * 0.35 * (1 - k)))
        _esquinas(screen, r, (255, 255, 255), max(12, marco.width // 9), 3)
        punto = max(3, marco.width // 70)
        pygame.draw.circle(screen, (255, 70, 70), (r.right - 3 * punto, r.top + 3 * punto), punto)

    # 2. El flash.
    if t < FLASH_MS:
        blanco = pygame.Surface(vista.size)
        blanco.fill((255, 255, 250))
        blanco.set_alpha(int(210 * (1 - t / FLASH_MS) ** 2))
        screen.blit(blanco, vista.topleft)

    # 3. La polaroid: aparece, se queda y vuela al aviso de NEXUS.
    if t >= APARECE_MS:
        ancho_foto = max(60, int(marco.width * 0.62))
        papel = _polaroid(e, ancho_foto)
        if t < QUIETA_HASTA_MS:
            k = _suave((t - APARECE_MS) / 220)
            escala, angulo = 0.55 + 0.45 * k, -14 + 8 * k
            centro = (vista.centerx, vista.centery + int(vista.height * 0.04))
            alfa = 255
        else:
            k = (t - QUIETA_HASTA_MS) / (DURACION_MS - QUIETA_HASTA_MS)
            k = k * k * (3 - 2 * k)             # (arranca y llega despacio)
            escala, angulo = 1.0 - 0.85 * k, -6 + 6 * k
            desde = (vista.centerx, vista.centery + int(vista.height * 0.04))
            hasta = (vista.centerx, vista.y + max(14, vista.height // 30))
            centro = (int(desde[0] + (hasta[0] - desde[0]) * k), int(desde[1] + (hasta[1] - desde[1]) * k))
            alfa = int(255 * (1 - max(0.0, k - 0.6) / 0.4))
        if efectos.ACTIVOS:
            img = pygame.transform.rotozoom(papel, angulo, escala)
        else:
            tam = (max(1, int(papel.get_width() * escala)), max(1, int(papel.get_height() * escala)))
            img = pygame.transform.scale(papel, tam)
        if alfa < 255:
            img.set_alpha(alfa)
        rect = img.get_rect(center=centro)
        if efectos.ACTIVOS:
            # Una sombra debajo (la misma forma, en negro transparente).
            sombra = img.copy()
            sombra.fill((0, 0, 0, alfa // 3), special_flags=pygame.BLEND_RGBA_MULT)
            screen.blit(sombra, rect.move(5, 7))
        screen.blit(img, rect)
    screen.set_clip(anterior)


# -- La foto en el celular (screens/celular.py) ----------------------------------------------

def _del_mapa(origen, red):
    """Si esta laptop no vio la foto (en red, la tomó alguien de la otra):
    el lugar sacado del mapa."""
    lugar = getattr(origen, "lugar", None)
    mundo = getattr(getattr(red, "juego", None), "mundo", None)
    imagen = getattr(mundo, "imagen", None)
    if lugar is None or imagen is None:
        return None
    r = pygame.Rect(0, 0, *MUNDO_FOTO)
    r.center = (int(lugar[0]), int(lugar[1]))
    r = r.clamp(imagen.get_rect()).clip(imagen.get_rect())
    if r.width < 8 or r.height < 8:
        return None
    foto = pygame.transform.smoothscale(imagen.subsurface(r), TAM_GUARDADA)
    foto.fill((38, 38, 34), special_flags=pygame.BLEND_RGB_ADD)    # (con flash, como las otras)
    return foto


def de_lugar(origen, red):
    """La foto del rumor o la noticia `origen` (la que se tomó ahí, o el lugar
    sacado del mapa), o None."""
    if origen is None:
        return None
    clave = getattr(origen, "id", None)
    foto = _por_pub.get(clave)
    if foto is None:
        foto = _del_mapa(origen, red)
        if foto is not None and clave is not None:
            _por_pub[clave] = foto
    return foto


def recortar(foto):
    """La foto recortada (sin ubicación): solo el centro, agrandado."""
    w, h = foto.get_size()
    r = pygame.Rect(0, 0, w // 2, h // 2)
    r.center = (w // 2, h // 2)
    return pygame.transform.smoothscale(foto.subsurface(r), (w, h))


def de_publicacion(pub, red, tam):
    """La foto de una publicación del equipo (un desmentido, una confirmación o
    lo compartido de eso), achicada a `tam`; None si no lleva foto. Recortada
    si se publicó sin ubicación."""
    origen = getattr(pub, "desmiente", None)
    if origen is None or getattr(pub, "tipo", None) not in ("desmentido", "confirmacion", "compartido"):
        return None
    recortada = pub.tipo != "compartido" and not getattr(pub, "con_ubicacion", True)
    return achicada(origen, red, tam, recortada)


def achicada(origen, red, tam, recortada=False):
    tam = (max(1, int(tam[0])), max(1, int(tam[1])))
    clave = (getattr(origen, "id", id(origen)), tam, recortada)
    if clave in _achicadas:
        return _achicadas[clave]
    foto = de_lugar(origen, red)
    if foto is None:
        return None
    if recortada:
        foto = recortar(foto)
    img = pygame.transform.smoothscale(foto, tam)
    if len(_achicadas) > 60:
        _achicadas.clear()
    _achicadas[clave] = img
    return img


def dibujar_en_celular(screen, img, pos, borde=(214, 218, 230)):
    """La foto en una tarjeta del celular, con un marco fino."""
    rect = img.get_rect(topleft=pos)
    screen.blit(img, rect)
    pygame.draw.rect(screen, borde, rect.inflate(2, 2), 1, border_radius=3)
    return rect
