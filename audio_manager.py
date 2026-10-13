"""Gestor de audio: efectos de sonido.

Los efectos están en Audio/SFX/ (los genera Audio/generar_sonidos.py) y se
cargan una sola vez: antes cada `play_sfx` volvía a leer el archivo del disco,
y el latido y los pasos suenan muchas veces por segundo. Si el audio no está
disponible (sin parlantes, o en las pruebas sin ventana), todo falla en
silencio y el juego sigue.

No hay música todavía: cuando la haya, se agrega aquí (pygame.mixer.music).
"""

import os

import pygame


class AudioManager:
    def __init__(self):
        self.sfx_volume = 0.7
        self._sfx_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Audio", "SFX")
        self._sonidos = {}   # nombre -> pygame.mixer.Sound (o None si no hay archivo)

    def _resolve_audio_path(self, folder, nombre):
        for extension in (".ogg", ".wav", ".mp3"):
            full = os.path.join(folder, nombre + extension)
            if os.path.exists(full):
                return full
        return None

    def apply_sfx_volume(self, valor_0_a_100):
        try:
            self.sfx_volume = max(0.0, min(100.0, float(valor_0_a_100))) / 100.0
        except (TypeError, ValueError):
            pass

    def play_sfx(self, nombre, volume_scale=1.0):
        try:
            if pygame.mixer.get_init() is None:
                return
            if nombre not in self._sonidos:
                ruta = self._resolve_audio_path(self._sfx_dir, nombre)
                self._sonidos[nombre] = pygame.mixer.Sound(ruta) if ruta is not None else None
            sonido = self._sonidos[nombre]
            if sonido is not None:
                sonido.set_volume(self.sfx_volume * max(0.0, min(1.0, float(volume_scale))))
                sonido.play()
        except Exception:
            pass


audio_manager = AudioManager()
