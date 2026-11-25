"""Las voces grabadas: el narrador (la cinemática y los finales) y los cuatro
agentes (la sala de los niños). El guion está en docs/guion_narrador.md.

Los archivos van en Audio/Narrador/ con el nombre del guion (`ninos_1.mp3`).
Cada línea de los agentes la graba la voz de un rol (`POR_DEFECTO`); como en
la partida la puede decir otro (si ese rol no está), se puede agregar la
misma línea con la voz de otro agente: `ninos_1_tecnomante.mp3`. Una línea
solo suena si quien la dice tiene su grabación: nunca con la voz de otro
personaje (si no, sale solo el texto, como antes).

Suenan en un canal apartado (audio_manager.play_voz): una voz nueva corta a
la anterior, así nunca se encima una con otra. En red viajan como cualquier
sonido ("voz:<archivo>", juego/ambiente.sonar), y la cinemática y los
finales se oyen en cada laptop (los dibuja cada una).

`duracion_ms` lee el largo del archivo sin el mezclador (el servidor de la
red no tiene parlantes): con eso el cuadro del diálogo dura lo mismo que el
audio. `cortes` dice en qué ms de una narración empieza cada subtítulo
(Audio/Narrador/cortes.json, lo arma Audio/generar_cortes.py).
"""

import json
import os
import struct
import wave

CARPETA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Audio", "Narrador")
EXTENSIONES = (".mp3", ".ogg", ".wav")
PREFIJO = "voz:"            # (en juego.sonar: "voz:ninos_1" suena por el canal de las voces)
MARGEN_MS = 450             # lo que el cuadro se queda después de que termina el audio

# Con qué voz está grabada cada línea de los agentes (docs/guion_narrador.md).
POR_DEFECTO = {
    "ninos_1": "Biomante", "ninos_2": "Tecnomante", "ninos_3": "Resonante",
    "ninos_4_pistas0": "Forjador", "ninos_4_pistas1": "Forjador",
    "ninos_4_pistas2": "Forjador", "ninos_4_pistas3": "Forjador",
    "ninos_5": "Biomante", "ninos_6": "Resonante",
    "regenerar": "Biomante", "voto_quedarse": "Biomante",
    "sala_abierta": "Resonante", "vidrio_sin_martillo": "Resonante",
    "sala_esperar": "Tecnomante", "voto_escapar": "Tecnomante", "liberar_sube": "Tecnomante",
    "vidrio_con_martillo": "Forjador", "voto_liberar": "Forjador",
}

_rutas = {}
_duraciones = {}
_cortes = None


def ruta(nombre):
    """El archivo de `nombre` (sin extensión) en Audio/Narrador, o None."""
    if nombre not in _rutas:
        _rutas[nombre] = next((os.path.join(CARPETA, nombre + e) for e in EXTENSIONES
                               if os.path.isfile(os.path.join(CARPETA, nombre + e))), None)
    return _rutas[nombre]


def de_rol(linea, rol):
    """El nombre del archivo con el que `rol` dice `linea`, o None si no
    hay una grabación con su voz: la suya propia (`linea_rol`) o la de
    siempre, si es la de su rol."""
    rol = (rol or "").strip()
    if rol and ruta(f"{linea}_{rol.lower()}") is not None:
        return f"{linea}_{rol.lower()}"
    if rol and POR_DEFECTO.get(linea) == rol and ruta(linea) is not None:
        return linea
    if linea not in POR_DEFECTO and ruta(linea) is not None:
        return linea        # (el narrador: una sola voz)
    return None


def duracion_ms(nombre):
    """Lo que dura el audio `nombre` (ms), o 0 si no está."""
    if nombre in _duraciones:
        return _duraciones[nombre]
    archivo = ruta(nombre) if nombre else None
    ms = 0
    try:
        if archivo is not None and archivo.endswith(".wav"):
            with wave.open(archivo) as w:
                ms = int(w.getnframes() * 1000 / max(1, w.getframerate()))
        elif archivo is not None and archivo.endswith(".mp3"):
            ms = _duracion_mp3(archivo)
        elif archivo is not None:
            ms = _duracion_mezclador(archivo)
    except Exception:
        ms = 0
    _duraciones[nombre] = ms
    return ms


def ms_en_pantalla(nombre, minimo=0):
    """Cuánto se ve el cuadro de una línea con audio: lo del audio y un poco más."""
    ms = duracion_ms(nombre)
    return max(minimo, ms + MARGEN_MS) if ms else minimo


# -- El largo de un MP3 (cuadro por cuadro, sin decodificarlo) -------------------------------

_KBPS = {  # (versión, capa) -> tabla de bitrates
    (1, 3): (0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320),
    (2, 3): (0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160),
}
_HZ = {1: (44100, 48000, 32000), 2: (22050, 24000, 16000), 25: (11025, 12000, 8000)}


def _duracion_mp3(archivo):
    with open(archivo, "rb") as f:
        datos = f.read()
    i = 0
    if datos[:3] == b"ID3" and len(datos) > 10:
        tam = datos[6:10]
        i = 10 + ((tam[0] & 0x7F) << 21 | (tam[1] & 0x7F) << 14 | (tam[2] & 0x7F) << 7 | (tam[3] & 0x7F))
    muestras, hz = 0, 44100
    while i + 4 <= len(datos):
        cabeza = struct.unpack(">I", datos[i:i + 4])[0]
        if (cabeza >> 21) & 0x7FF != 0x7FF:
            i += 1
            continue
        version = {3: 1, 2: 2, 0: 25}.get((cabeza >> 19) & 3)
        capa = 4 - ((cabeza >> 17) & 3)
        indice_kbps = (cabeza >> 12) & 0xF
        indice_hz = (cabeza >> 10) & 3
        relleno = (cabeza >> 9) & 1
        if version is None or capa != 3 or indice_kbps in (0, 15) or indice_hz == 3:
            i += 1
            continue
        kbps = _KBPS[(1 if version == 1 else 2, 3)][indice_kbps]
        hz = _HZ[version][indice_hz]
        por_cuadro = 1152 if version == 1 else 576
        largo = (144 if version == 1 else 72) * kbps * 1000 // hz + relleno
        if largo <= 0:
            break
        muestras += por_cuadro
        i += largo
    return int(muestras * 1000 / hz)


def _duracion_mezclador(archivo):
    import pygame
    if pygame.mixer.get_init() is None:
        return 0
    return int(pygame.mixer.Sound(archivo).get_length() * 1000)


def cortes(nombre, n):
    """En qué ms de la narración `nombre` empieza cada uno de sus `n`
    subtítulos (Audio/Narrador/cortes.json), o None si no está (o el audio
    no está, o no coinciden: cambiaron los textos)."""
    global _cortes
    if _cortes is None:
        try:
            with open(os.path.join(CARPETA, "cortes.json"), encoding="utf-8") as f:
                _cortes = json.load(f)
        except (OSError, ValueError):
            _cortes = {}
    lista = _cortes.get(nombre)
    if not lista or len(lista) != n or ruta(nombre) is None:
        return None
    return [int(x) for x in lista]
