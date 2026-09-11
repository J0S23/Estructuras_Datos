"""Gestor de audio para Alcalde Digital."""

import math
import os
from typing import Optional

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

    def _resolve_audio_path(self, folder: str, nombre: str) -> Optional[str]:
        for ext in (".ogg", ".wav", ".mp3"):
            full = os.path.join(folder, f"{nombre}{ext}")
            if os.path.exists(full):
                return full
        return None

    def _safe_set_music_volume(self, value: float):
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

        try:
            if not pygame.mixer.get_init():
                return
            sample_rate = 22050
            duration = 0.12
            total_samples = int(sample_rate * duration)
            audio = []
            for i in range(total_samples):
                t = i / sample_rate
                value = int(32767 * math.sin(2 * math.pi * (440 if "click" in nombre.lower() else 220) * t) * 0.3)
                audio.append(value)
            sound_data = pygame.mixer.Sound(buffer=bytearray(audio))
            sound_data.set_volume(self.sfx_volume * max(0.0, min(2.0, float(volume_scale))))
            sound_data.play()
        except Exception:
            pass

    def sfx_click(self):
        self.play_sfx("click", 1.0)

    def sfx_hover(self):
        self.play_sfx("hover", 0.7)

    def sfx_decision(self):
        self.play_sfx("decision", 1.2)


audio_manager = AudioManager()
