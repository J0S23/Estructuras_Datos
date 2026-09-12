"""Gestor de audio para Alcalde Digital."""

import os

import pygame


BGM_MAP = {
    "menu": "tema_principal",
    "ciudad": "tema_principal",
    "publicacion": "tema_tension",
    "resultados": "tema_principal",
    "ayuda": "tema_principal",
    "creditos": "tema_principal",
}


class AudioManager:
    def __init__(self):
        self.music_volume = 0.7
        self.sfx_volume = 0.7
        self.current_bgm = None
        self._base_dir = os.path.dirname(os.path.abspath(__file__))
        self._bgm_dir = os.path.join(self._base_dir, "Audio", "BGM")
        self._sfx_dir = os.path.join(self._base_dir, "Audio", "SFX")

    def _resolve_audio_path(self, folder, nombre):
        extensiones = [".ogg", ".wav", ".mp3"]
        for extension in extensiones:
            full = os.path.join(folder, nombre + extension)
            if os.path.exists(full):
                return full
        return None

    def _safe_set_music_volume(self, value):
        try:
            if pygame.mixer.get_init() is not None:
                pygame.mixer.music.set_volume(max(0.0, min(1.0, value)))
        except Exception:
            pass

    def apply_music_volume(self, valor_0_a_100):
        try:
            value = max(0.0, min(100.0, float(valor_0_a_100))) / 100.0
            self.music_volume = value
            self._safe_set_music_volume(value)
        except Exception:
            pass

    def apply_sfx_volume(self, valor_0_a_100):
        try:
            self.sfx_volume = max(0.0, min(100.0, float(valor_0_a_100))) / 100.0
        except Exception:
            pass

    def play_bgm(self, nombre):
        try:
            if pygame.mixer.get_init() is None:
                return
            ruta = self._resolve_audio_path(self._bgm_dir, nombre)
            if ruta is None:
                self.current_bgm = None
                return
            pygame.mixer.music.load(ruta)
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(-1)
            self.current_bgm = nombre
        except Exception:
            pass

    def play_bgm_for_screen(self, screen_name):
        nombre = BGM_MAP.get(str(screen_name), "tema_principal")
        self.play_bgm(nombre)

    def stop_bgm(self, fade_ms=0):
        try:
            if pygame.mixer.get_init() is not None:
                if fade_ms > 0:
                    pygame.mixer.music.fadeout(fade_ms)
                else:
                    pygame.mixer.music.stop()
                self.current_bgm = None
        except Exception:
            pass

    def play_sfx(self, nombre, volume_scale=1.0):
        try:
            if pygame.mixer.get_init() is None:
                return
            ruta = self._resolve_audio_path(self._sfx_dir, nombre)
            if ruta is not None:
                sonido = pygame.mixer.Sound(ruta)
                sonido.set_volume(self.sfx_volume * max(0.0, min(2.0, float(volume_scale))))
                sonido.play()
                return
        except Exception:
            pass

        # Si no hay archivo, no se genera un sonido artificial.
        return

    def sfx_click(self):
        self.play_sfx("click", 1.0)

    def sfx_hover(self):
        self.play_sfx("hover", 0.7)

    def sfx_decision(self):
        self.play_sfx("decision", 1.2)


audio_manager = AudioManager()
