"""Carga y control de personajes con sprites de 8 direcciones (formato PixelLab).

Cada personaje vive en su propia carpeta dentro de Imagenes/Personajes/
(por ejemplo P1, P2) con hojas de sprites así:

    <prefijo>Idle_<direccion>.png        1 frame
    <prefijo>Breathing_<direccion>.png   varios frames (idle animado)
    <prefijo>Walking_<direccion>.png     varios frames (caminata)

donde <direccion> es una de las 8: north, north-east, east, south-east,
south, south-west, west, north-west.

El `<prefijo>` es opcional y las mayúsculas no importan: tanto
`Walking_south.png` como `Joseph_walking_south.png` o
`walking_south-west.png` se reconocen igual. Eso es a propósito, porque los
sprites vienen exportados con nombres inconsistentes.

La cantidad de frames de cada hoja no está fija en el código: se deduce del
tamaño de la imagen asumiendo frames cuadrados (una hoja de 736x92 tiene
736/92 = 8 frames).
"""

import json
import os

import pygame


# Las 8 direcciones, con el mismo nombre que usan los archivos de sprites.
DIRECCIONES = (
    "north", "north-east", "east", "south-east",
    "south", "south-west", "west", "north-west",
)

# De más larga a más corta: al reconocer el nombre de un archivo hay que
# probar "north-east" antes que "north", o "north" se comería el prefijo.
_DIRECCIONES_POR_LONGITUD = tuple(sorted(DIRECCIONES, key=len, reverse=True))

ANIMACIONES = ("idle", "breathing", "walking")

# Los sprites vienen casi tan anchos como altos (el contenido de P1 mide 63x64),
# y una figura humana se ve natural más cerca de 0.5. Este factor los estrecha
# horizontalmente sin tocar la altura. Se puede ajustar por personaje con
# "ancho_ratio" en su Hitboxes/<personaje>_config.json.
ANCHO_RATIO_DEFECTO = 0.7

# Si falta una animación para una dirección, se usa la siguiente disponible.
_RESPALDOS = {
    "walking": ("walking", "breathing", "idle"),
    "breathing": ("breathing", "idle", "walking"),
    "idle": ("idle", "breathing", "walking"),
}


def cortar_spritesheet_auto(ruta, cantidad_frames=None):
    """Divide una hoja de sprites en frames de igual ancho.

    Si no se indica `cantidad_frames`, se deduce asumiendo frames cuadrados:
    una hoja de 736x92 son 8 frames de 92x92.
    """
    hoja = pygame.image.load(ruta).convert_alpha()
    ancho_total, alto = hoja.get_size()
    if cantidad_frames is None:
        cantidad_frames = max(1, round(ancho_total / alto)) if alto else 1
    ancho_frame = ancho_total // max(1, cantidad_frames)
    return [
        hoja.subsurface(pygame.Rect(i * ancho_frame, 0, ancho_frame, alto)).copy()
        for i in range(cantidad_frames)
    ]


def _resolver_carpeta_pack(ruta_pack):
    """Si `ruta_pack` no tiene sprites directamente, busca en sus subcarpetas."""
    if not os.path.isdir(ruta_pack):
        return ruta_pack
    if detectar_hojas(ruta_pack):
        return ruta_pack
    for raiz, _, _ in os.walk(ruta_pack):
        if raiz != ruta_pack and detectar_hojas(raiz):
            return raiz
    return ruta_pack


def detectar_hojas(carpeta):
    """Mapea las hojas de sprites de una carpeta: {animacion: {direccion: ruta}}.

    Reconoce el nombre sin importar mayúsculas ni prefijos del personaje.
    """
    hojas = {}
    if not os.path.isdir(carpeta):
        return hojas

    for archivo in sorted(os.listdir(carpeta)):
        if not archivo.lower().endswith(".png"):
            continue
        nombre = os.path.splitext(archivo)[0].lower()

        direccion = next(
            (d for d in _DIRECCIONES_POR_LONGITUD if nombre.endswith(d)), None
        )
        if direccion is None:
            continue

        animacion = next((a for a in ANIMACIONES if a in nombre), None)
        if animacion is None:
            continue

        hojas.setdefault(animacion, {})[direccion] = os.path.join(carpeta, archivo)

    return hojas


def cargar_animaciones(ruta_pack, escala=1.0, ancho_ratio=ANCHO_RATIO_DEFECTO):
    """Carga todas las hojas de un personaje: {animacion: {direccion: [frames]}}.

    `escala` agranda o achica el sprite completo; `ancho_ratio` lo estrecha
    solo a lo ancho (1.0 = sin cambio), para corregir lo anchos que vienen.

    Las animaciones o direcciones que falten se rellenan con la alternativa
    más cercana, para que el personaje nunca quede sin nada que dibujar.
    """
    carpeta = _resolver_carpeta_pack(ruta_pack)
    hojas = detectar_hojas(carpeta)

    cargadas = {}
    for animacion, por_direccion in hojas.items():
        cargadas[animacion] = {}
        for direccion, ruta in por_direccion.items():
            try:
                cargadas[animacion][direccion] = cortar_spritesheet_auto(ruta)
            except (pygame.error, OSError):
                continue

    # Rellena huecos con la animación de respaldo más cercana.
    animaciones = {}
    for animacion in ANIMACIONES:
        animaciones[animacion] = {}
        for direccion in DIRECCIONES:
            frames = None
            for alternativa in _RESPALDOS[animacion]:
                frames = cargadas.get(alternativa, {}).get(direccion)
                if frames:
                    break
            if not frames:
                # Última opción: cualquier frame de cualquier dirección.
                for alternativa in _RESPALDOS[animacion]:
                    por_direccion = cargadas.get(alternativa, {})
                    if por_direccion:
                        frames = next(iter(por_direccion.values()))
                        break
            animaciones[animacion][direccion] = frames or []

    escala_x = escala * ancho_ratio
    if escala_x != 1.0 or escala != 1.0:
        for animacion, por_direccion in animaciones.items():
            for direccion, frames in por_direccion.items():
                # scale (nearest neighbor) y no smoothscale: mantiene el pixel
                # art nítido en vez de emborronarlo.
                por_direccion[direccion] = [
                    pygame.transform.scale(
                        f,
                        (max(1, int(f.get_width() * escala_x)),
                         max(1, int(f.get_height() * escala))),
                    )
                    for f in frames
                ]

    return animaciones


def direccion_desde_vector(dx, dy, por_defecto="south"):
    """Traduce un vector de movimiento a uno de los 8 nombres de dirección."""
    if dx == 0 and dy == 0:
        return por_defecto
    vertical = "north" if dy < 0 else ("south" if dy > 0 else "")
    horizontal = "east" if dx > 0 else ("west" if dx < 0 else "")
    if vertical and horizontal:
        return f"{vertical}-{horizontal}"
    return vertical or horizontal


class Personaje:
    """Personaje con movimiento en 8 direcciones y animaciones de PixelLab.

    Estados: "walking" mientras se mueve, y en reposo "breathing" (el idle
    animado) o "idle" si no hay animación de respiración.
    """

    def __init__(self, x, y, ruta_pack, velocidad=3, fps_animacion=8, escala=1.0,
                 controles=None):
        self.x = x
        self.y = y
        self.velocidad = velocidad
        self.sprint_multiplier = 1.8
        self.scale = escala

        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config = self._load_config(project_root, ruta_pack)
        self.scale = float(config.get("scale", self.scale))

        self.ancho_ratio = float(config.get("ancho_ratio", ANCHO_RATIO_DEFECTO))
        self.animaciones = cargar_animaciones(
            ruta_pack, escala=self.scale, ancho_ratio=self.ancho_ratio
        )
        self.direccion = "south"
        self.estado = "breathing"
        self.frame_actual = 0
        self.contador_animacion = 0
        self.fps_animacion = fps_animacion
        self.moviendose = False

        # Controles: por defecto WASD + flechas. Para el segundo jugador se
        # pasa un diccionario distinto (ver CONTROLES_WASD / CONTROLES_FLECHAS).
        self.controles = controles if controles is not None else CONTROLES_AMBOS

        base = self._frame_actual_surface()
        self.sprite_w = base.get_width() if base else 32
        self.sprite_h = base.get_height() if base else 32

        default_width_ratio = 0.20
        default_height_ratio = 0.12
        default_offset_x_ratio = (1.0 - default_width_ratio) / 2.0
        default_offset_y_ratio = 1.0 - default_height_ratio - 0.025

        self.hitbox_w_ratio = float(config.get("hitbox_w_ratio", default_width_ratio))
        self.hitbox_h_ratio = float(config.get("hitbox_h_ratio", default_height_ratio))
        self.hitbox_offset_x_ratio = float(config.get("hitbox_offset_x_ratio", default_offset_x_ratio))
        self.hitbox_offset_y_ratio = float(config.get("hitbox_offset_y_ratio", default_offset_y_ratio))
        self.interactable_hitbox_w_ratio = float(config.get("interactable_hitbox_w_ratio", self.hitbox_w_ratio))
        self.interactable_hitbox_h_ratio = float(config.get("interactable_hitbox_h_ratio", self.hitbox_h_ratio))
        self.interactable_hitbox_offset_x_ratio = float(config.get("interactable_hitbox_offset_x_ratio", self.hitbox_offset_x_ratio))
        self.interactable_hitbox_offset_y_ratio = float(config.get("interactable_hitbox_offset_y_ratio", self.hitbox_offset_y_ratio))

        self.hitbox_w = max(14, int(self.sprite_w * self.hitbox_w_ratio))
        self.hitbox_h = max(8, int(self.sprite_h * self.hitbox_h_ratio))
        self.hitbox_offset_x = int(self.sprite_w * self.hitbox_offset_x_ratio)
        self.hitbox_offset_y = int(self.sprite_h * self.hitbox_offset_y_ratio)
        self.interactable_hitbox_w = max(14, int(self.sprite_w * self.interactable_hitbox_w_ratio))
        self.interactable_hitbox_h = max(8, int(self.sprite_h * self.interactable_hitbox_h_ratio))
        self.interactable_hitbox_offset_x = int(self.sprite_w * self.interactable_hitbox_offset_x_ratio)
        self.interactable_hitbox_offset_y = int(self.sprite_h * self.interactable_hitbox_offset_y_ratio)

        self.hitbox = pygame.Rect(
            self.x + self.hitbox_offset_x, self.y + self.hitbox_offset_y,
            self.hitbox_w, self.hitbox_h,
        )
        self.interactable_hitbox = pygame.Rect(
            self.x + self.interactable_hitbox_offset_x, self.y + self.interactable_hitbox_offset_y,
            self.interactable_hitbox_w, self.interactable_hitbox_h,
        )

    # -- Configuración -----------------------------------------------------------

    def _load_config(self, root_dir, ruta_pack=None):
        """Busca el config de hitbox de este personaje.

        Editores/personaje_editor.py guarda el archivo con el nombre del
        SPRITE que estaba abierto (por ejemplo Idle_east_config.json, o
        Joseph_Idle_east_config.json), no con el nombre de la carpeta del
        personaje. Por eso se buscan, en orden:

        1. Hitboxes/<carpeta>_config.json          (P1_config.json)
        2. Hitboxes/<sprite>_config.json           para cualquier sprite que
           esté dentro de la carpeta del personaje
        3. Hitboxes/personaje_config.json          config compartido
        4. personaje_config.json en la raíz
        """
        carpeta_hitboxes = os.path.join(root_dir, "Hitboxes")
        candidatos = []

        if ruta_pack:
            carpeta = _resolver_carpeta_pack(ruta_pack)
            nombre_carpeta = os.path.basename(os.path.normpath(carpeta))
            if nombre_carpeta:
                candidatos.append(os.path.join(carpeta_hitboxes, f"{nombre_carpeta}_config.json"))

            # Cualquier config nombrado como uno de los sprites del personaje.
            if os.path.isdir(carpeta):
                for archivo in sorted(os.listdir(carpeta)):
                    if not archivo.lower().endswith(".png"):
                        continue
                    base = os.path.splitext(archivo)[0]
                    candidatos.append(os.path.join(carpeta_hitboxes, f"{base}_config.json"))

        candidatos += [
            os.path.join(carpeta_hitboxes, "personaje_config.json"),
            os.path.join(root_dir, "personaje_config.json"),
        ]

        for ruta in candidatos:
            try:
                with open(ruta, "r", encoding="utf-8") as fh:
                    datos = json.load(fh)
                self.ruta_config = ruta
                return datos
            except (OSError, json.JSONDecodeError):
                continue
        self.ruta_config = None
        return {}

    # -- Hitboxes ----------------------------------------------------------------

    def sync_hitbox_from_sprite(self):
        self.hitbox.x = self.x + self.hitbox_offset_x
        self.hitbox.y = self.y + self.hitbox_offset_y
        self.interactable_hitbox.x = self.x + self.interactable_hitbox_offset_x
        self.interactable_hitbox.y = self.y + self.interactable_hitbox_offset_y

    def sync_sprite_from_hitbox(self):
        self.x = self.hitbox.x - self.hitbox_offset_x
        self.y = self.hitbox.y - self.hitbox_offset_y
        self.interactable_hitbox.x = self.x + self.interactable_hitbox_offset_x
        self.interactable_hitbox.y = self.y + self.interactable_hitbox_offset_y

    # -- Animación ---------------------------------------------------------------

    def _frames_actuales(self):
        return self.animaciones.get(self.estado, {}).get(self.direccion, [])

    def _frame_actual_surface(self):
        frames = self._frames_actuales()
        if not frames:
            return None
        return frames[self.frame_actual % len(frames)]

    def _avanzar_animacion(self):
        frames = self._frames_actuales()
        if len(frames) <= 1:
            self.frame_actual = 0
            self.contador_animacion = 0
            return
        self.contador_animacion += 1
        if self.contador_animacion >= self.fps_animacion:
            self.contador_animacion = 0
            self.frame_actual = (self.frame_actual + 1) % len(frames)

    # -- Movimiento --------------------------------------------------------------

    def leer_movimiento(self, teclas):
        """Devuelve (dx, dy) en -1/0/1 según las teclas de este personaje."""
        dx = int(any(teclas[k] for k in self.controles["derecha"])) - \
             int(any(teclas[k] for k in self.controles["izquierda"]))
        dy = int(any(teclas[k] for k in self.controles["abajo"])) - \
             int(any(teclas[k] for k in self.controles["arriba"]))
        return dx, dy

    def actualizar(self, teclas=None, colisiona=None):
        if teclas is None:
            teclas = pygame.key.get_pressed()

        dx, dy = self.leer_movimiento(teclas)
        self.moviendose = dx != 0 or dy != 0

        sprint = any(teclas[k] for k in self.controles.get("sprint", ()))
        velocidad = self.velocidad * (self.sprint_multiplier if sprint else 1)

        if self.moviendose:
            # En diagonal se normaliza para que no sea más rápido que en recto.
            factor = 0.7071 if dx and dy else 1.0
            # Se mueve un eje a la vez: así, al chocar contra una pared en
            # diagonal, el personaje se desliza a lo largo de ella en vez de
            # quedarse trabado.
            self._mover_eje(dx * velocidad * factor, 0, colisiona)
            self._mover_eje(0, dy * velocidad * factor, colisiona)
            self.direccion = direccion_desde_vector(dx, dy, self.direccion)
            nuevo_estado = "walking"
        else:
            nuevo_estado = "breathing" if self.animaciones.get("breathing", {}).get(self.direccion) else "idle"

        if nuevo_estado != self.estado:
            self.estado = nuevo_estado
            self.frame_actual = 0
            self.contador_animacion = 0

        self._avanzar_animacion()
        self.sync_hitbox_from_sprite()

    def _mover_eje(self, paso_x, paso_y, colisiona=None):
        """Aplica el paso en un eje y lo revierte si el hitbox choca."""
        if paso_x == 0 and paso_y == 0:
            return
        x_previo, y_previo = self.x, self.y

        # Si ya venía atrapado dentro de una pared, se le deja moverse para
        # que pueda salir; si no, quedaría trabado para siempre.
        atrapado = colisiona is not None and colisiona(self.hitbox)

        self.x += paso_x
        self.y += paso_y
        self.sync_hitbox_from_sprite()
        if not atrapado and colisiona is not None and colisiona(self.hitbox):
            self.x, self.y = x_previo, y_previo
            self.sync_hitbox_from_sprite()

    def dibujar(self, pantalla, offset=(0, 0)):
        imagen = self._frame_actual_surface()
        if imagen is None:
            return
        pantalla.blit(imagen, (self.x - offset[0], self.y - offset[1]))


# Esquemas de control listos para usar (ver CLAUDE.md: jugador 1 WASD,
# jugador 2 flechas).
CONTROLES_WASD = {
    "arriba": (pygame.K_w,),
    "abajo": (pygame.K_s,),
    "izquierda": (pygame.K_a,),
    "derecha": (pygame.K_d,),
    "sprint": (pygame.K_LSHIFT,),
}

CONTROLES_FLECHAS = {
    "arriba": (pygame.K_UP,),
    "abajo": (pygame.K_DOWN,),
    "izquierda": (pygame.K_LEFT,),
    "derecha": (pygame.K_RIGHT,),
    "sprint": (pygame.K_RSHIFT,),
}

# Ambos a la vez: útil para probar con un solo personaje en pantalla.
CONTROLES_AMBOS = {
    "arriba": (pygame.K_w, pygame.K_UP),
    "abajo": (pygame.K_s, pygame.K_DOWN),
    "izquierda": (pygame.K_a, pygame.K_LEFT),
    "derecha": (pygame.K_d, pygame.K_RIGHT),
    "sprint": (pygame.K_LSHIFT, pygame.K_RSHIFT),
}
