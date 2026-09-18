import json
import os

import pygame


REQUIRED_IDLE_SPRITES = ("idle_down.png", "idle_up.png", "idle_left.png", "idle_right.png")
RUN_SPRITES = ("run_down.png", "run_up.png", "run_left.png", "run_right.png")
WALK_SPRITES = ("walk_down.png", "walk_up.png", "walk_left.png", "walk_right.png")


def cortar_spritesheet_auto(ruta, cantidad_frames):
    """Carga una imagen y la divide en `cantidad_frames` columnas iguales."""
    hoja = pygame.image.load(ruta).convert_alpha()
    ancho_total, alto = hoja.get_size()
    ancho_frame = ancho_total // max(1, cantidad_frames)
    frames = []
    for i in range(cantidad_frames):
        rect = pygame.Rect(i * ancho_frame, 0, ancho_frame, alto)
        frames.append(hoja.subsurface(rect).copy())
    return frames


def _resolve_sprite_pack_path(ruta_pack):
    """Si ruta_pack ya contiene los sprites, la devuelve. Si no, busca en subcarpetas."""
    if not os.path.isdir(ruta_pack):
        return ruta_pack
    for root, _, files in os.walk(ruta_pack):
        lowered = {f.lower() for f in files}
        if "idle_down.png" in lowered:
            return root
    return ruta_pack


def cargar_animaciones(ruta_pack, escala=1.0):
    """Carga walk_<dir>.png (8 frames) e idle_<dir>.png (1 frame) para las 4 direcciones."""
    direcciones = ("down", "up", "left", "right")
    animaciones = {}
    for d in direcciones:
        walk_path = os.path.join(ruta_pack, f"walk_{d}.png")
        idle_path = os.path.join(ruta_pack, f"idle_{d}.png")
        if os.path.exists(walk_path):
            animaciones[d] = cortar_spritesheet_auto(walk_path, 8)
        elif os.path.exists(idle_path):
            animaciones[d] = cortar_spritesheet_auto(idle_path, 1)
        else:
            animaciones[d] = []
        if os.path.exists(idle_path):
            animaciones[f"idle_{d}"] = cortar_spritesheet_auto(idle_path, 1)
        elif d in animaciones:
            animaciones[f"idle_{d}"] = [animaciones[d][0]] if animaciones[d] else []
        else:
            animaciones[f"idle_{d}"] = []
    if escala != 1.0:
        for k, frames in list(animaciones.items()):
            animaciones[k] = [
                pygame.transform.scale(f, (max(1, int(f.get_width() * escala)), max(1, int(f.get_height() * escala))))
                for f in frames
            ]
    return animaciones


class Personaje:
    def __init__(self, x, y, ruta_pack, velocidad=3, fps_animacion=8, escala=1.6, color=None):
        self.x = x
        self.y = y
        self.velocidad = velocidad
        self.sprint_multiplier = 1.8
        self.scale = escala
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config = self._load_config(project_root, ruta_pack)
        self.scale = float(config.get("scale", self.scale))
        ruta_pack_resuelta = _resolve_sprite_pack_path(ruta_pack)
        self.animaciones = cargar_animaciones(ruta_pack_resuelta, escala=self.scale)
        self.direccion = "down"
        self.frame_actual = 0
        self.contador_animacion = 0
        self.fps_animacion = fps_animacion
        base = self.animaciones["idle_down"][0] if self.animaciones.get("idle_down") else pygame.Surface((16, 16))
        self.sprite_w = base.get_width()
        self.sprite_h = base.get_height()

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
        self.moviendose = False

    def _load_config(self, root_dir, ruta_pack=None):
        """Busca primero el config propio de este personaje —
        Hitboxes/<nombre>_config.json, que es lo que genera
        Editores/personaje_editor.py— y si no existe cae al
        personaje_config.json general."""
        candidate_paths = []
        if ruta_pack:
            nombre = os.path.splitext(os.path.basename(os.path.normpath(ruta_pack)))[0]
            if nombre:
                # Acepta tanto 'ciudadano' (carpeta del pack) como
                # 'ciudadano_idle' (nombre del sprite suelto que usa el editor).
                candidate_paths.append(os.path.join(root_dir, "Hitboxes", f"{nombre}_config.json"))
                candidate_paths.append(os.path.join(root_dir, "Hitboxes", f"{nombre}_idle_config.json"))
        candidate_paths += [
            os.path.join(root_dir, "Hitboxes", "personaje_config.json"),
            os.path.join(root_dir, "personaje_config.json"),
        ]
        for config_path in candidate_paths:
            try:
                with open(config_path, "r", encoding="utf-8") as fh:
                    return json.load(fh)
            except (OSError, json.JSONDecodeError):
                continue
        return {}

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

    def actualizar(self):
        teclas = pygame.key.get_pressed()
        self.moviendose = False
        sprint_activo = teclas[pygame.K_LSHIFT] or teclas[pygame.K_RSHIFT]
        velocidad_actual = self.velocidad * self.sprint_multiplier if sprint_activo else self.velocidad

        if teclas[pygame.K_UP] or teclas[pygame.K_w]:
            self.y -= velocidad_actual
            self.direccion = "up"
            self.moviendose = True
        elif teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
            self.y += velocidad_actual
            self.direccion = "down"
            self.moviendose = True
        elif teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            self.x -= velocidad_actual
            self.direccion = "left"
            self.moviendose = True
        elif teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            self.x += velocidad_actual
            self.direccion = "right"
            self.moviendose = True

        if self.moviendose:
            self.contador_animacion += 1
            if self.contador_animacion >= self.fps_animacion:
                self.contador_animacion = 0
                total_frames = len(self.animaciones[self.direccion])
                self.frame_actual = (self.frame_actual + 1) % total_frames
        else:
            self.frame_actual = 0
            self.contador_animacion = 0

        self.sync_hitbox_from_sprite()

    def dibujar(self, pantalla, offset=(0, 0)):
        if self.moviendose:
            imagen_actual = self.animaciones[self.direccion][self.frame_actual]
        else:
            imagen_actual = self.animaciones[f"idle_{self.direccion}"][0]
        pantalla.blit(imagen_actual, (self.x - offset[0], self.y - offset[1]))
