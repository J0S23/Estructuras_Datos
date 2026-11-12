"""Gestor de audio: efectos de sonido.

Los efectos están en Audio/SFX/ (los genera Audio/generar_sonidos.py) y se
cargan una sola vez: antes cada `play_sfx` volvía a leer el archivo del disco,
y el latido y los pasos suenan muchas veces por segundo. Si el audio no está
disponible (sin parlantes, o en las pruebas sin ventana), todo falla en
silencio y el juego sigue.

De fondo suena un zumbido de la nave en bucle (`bucle`), que se calla en los
apagones, y encima la música (`musica`): tranquila, o de tensión cuando un
alien persigue a alguien. El volumen de los dos sigue al de los efectos.
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
        self._canal_musica = None
        self._musica = None        # nombre de la música que está sonando
        self._volumen_musica = 0.0
        self._turno_musica = 1     # cuál de los dos canales de música toca (0 o 1)

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
        try:
            if self._canal_musica is not None:
                self._canal_musica.set_volume(self._volumen_musica * self.sfx_volume)
        except Exception:
            pass

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
            # Zumbido + música + voces, pasos y latido a la vez: con los 8
            # canales de siempre, alguno se quedaba sin sonar.
            if pygame.mixer.get_num_channels() < 16:
                pygame.mixer.set_num_channels(16)
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
                # Canal apartado (el 2; el 0 y el 1 son de la música): los
                # efectos no lo usan y la música no lo pisa.
                pygame.mixer.set_reserved(3)
                self._canal_bucle = pygame.mixer.Channel(2)
                self._canal_bucle.play(sonido, loops=-1, fade_ms=800)
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

    # -- Música de fondo (otro bucle, encima del zumbido) ----------------------------

    def musica(self, nombre, volumen=1.0):
        """Suena `nombre` en bucle como música (musica_calma, musica_tension).
        Al cambiar de una a otra, la anterior se apaga de a poco mientras
        entra la nueva."""
        try:
            if pygame.mixer.get_init() is None:
                return
            if self._musica != nombre:
                self.parar_musica()
                sonido = self._sonido(nombre)
                if sonido is None:
                    return
                # Dos canales apartados solo para la música (los efectos no los
                # usan): así nunca se queda sin canal, y al cambiar de música
                # la nueva entra por el otro mientras la anterior se apaga.
                pygame.mixer.set_reserved(3)
                self._turno_musica = 1 - self._turno_musica
                canal = pygame.mixer.Channel(self._turno_musica)
                canal.play(sonido, loops=-1, fade_ms=1500)
                self._canal_musica, self._musica = canal, nombre
            self._volumen_musica = max(0.0, min(1.0, volumen))
            if self._canal_musica is not None:
                self._canal_musica.set_volume(self._volumen_musica * self.sfx_volume)
        except Exception:
            pass

    def parar_musica(self):
        try:
            if self._canal_musica is not None:
                self._canal_musica.fadeout(1200)
        except Exception:
            pass
        self._canal_musica, self._musica = None, None

    @property
    def sonando_musica(self):
        return self._musica

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
