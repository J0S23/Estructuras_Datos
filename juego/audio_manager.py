"""Gestor de audio: efectos de sonido.

Los efectos están en Audio/SFX/ (los genera Audio/generar_sonidos.py) y se
cargan una sola vez: antes cada `play_sfx` volvía a leer el archivo del disco,
y el latido y los pasos suenan muchas veces por segundo. Si el audio no está
disponible (sin parlantes, o en las pruebas sin ventana), todo falla en
silencio y el juego sigue.

No hay música: de fondo suena un zumbido de la nave en bucle (`bucle`), que
se calla en los apagones. Su volumen sigue al de los efectos.
"""

import os

# La raíz del proyecto (este archivo está en una subcarpeta).
_RAIZ_PROYECTO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

import pygame


class AudioManager:
    def __init__(self):
        self.sfx_volume = 0.7
        self._sfx_dir = os.path.join(_RAIZ_PROYECTO, "Audio", "SFX")
        self._sonidos = {}   # nombre -> pygame.mixer.Sound (o None si no hay archivo)
        self._canal_bucle = None
        self._bucle = None         # nombre del sonido en bucle que está sonando
        self._volumen_bucle = 0.0  # 0 a 1, antes de multiplicar por sfx_volume

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
            return
        self.volumen_bucle(self._volumen_bucle)

    def _sonido(self, nombre):
        if nombre not in self._sonidos:
            ruta = self._resolve_audio_path(self._sfx_dir, nombre)
            self._sonidos[nombre] = pygame.mixer.Sound(ruta) if ruta is not None else None
        return self._sonidos[nombre]

    def precargar(self):
        """Carga de una vez todos los efectos de Audio/SFX/ (al empezar la
        partida). Si no, el primer susto o la primera alarma se cargaban del
        disco en ese momento y el juego daba un tirón."""
        try:
            if pygame.mixer.get_init() is None or not os.path.isdir(self._sfx_dir):
                return
            for archivo in os.listdir(self._sfx_dir):
                nombre, extension = os.path.splitext(archivo)
                if extension.lower() in (".ogg", ".wav", ".mp3"):
                    self._sonido(nombre)
        except Exception:
            pass

    # -- Sonido de fondo en bucle -------------------------------------------------

    def bucle(self, nombre, volumen=1.0):
        """Empieza a sonar `nombre` sin parar (si ya suena, solo cambia el volumen)."""
        try:
            if pygame.mixer.get_init() is None:
                return
            if self._bucle != nombre:
                self.parar_bucle()
                sonido = self._sonido(nombre)
                if sonido is None:
                    return
                self._canal_bucle = sonido.play(loops=-1, fade_ms=800)
                self._bucle = nombre
            self.volumen_bucle(volumen)
        except Exception:
            pass

    def volumen_bucle(self, volumen):
        self._volumen_bucle = max(0.0, min(1.0, volumen))
        try:
            if self._canal_bucle is not None:
                self._canal_bucle.set_volume(self._volumen_bucle * self.sfx_volume)
        except Exception:
            pass

    def parar_bucle(self):
        try:
            if self._canal_bucle is not None:
                self._canal_bucle.fadeout(500)
        except Exception:
            pass
        self._canal_bucle, self._bucle = None, None

    @property
    def sonando_bucle(self):
        return self._bucle

    def play_sfx(self, nombre, volume_scale=1.0):
        try:
            if pygame.mixer.get_init() is None:
                return
            sonido = self._sonido(nombre)
            if sonido is not None:
                sonido.set_volume(self.sfx_volume * max(0.0, min(1.0, float(volume_scale))))
                sonido.play()
        except Exception:
            pass


audio_manager = AudioManager()
