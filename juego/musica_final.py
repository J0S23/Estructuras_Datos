"""La música de cada final (Audio/Musica/): suena en la pantalla de
resultados, desde la escena del final, y baja mientras habla el narrador.

| Final                                   | Canción                                          |
|-----------------------------------------|--------------------------------------------------|
| Derrota (los atraparon)                 | "Disturbed Soundscape", Eric Matyas (CC BY)      |
| Escapan sin entrar (o sin sala oculta)  | "Sci-Fi Close", Eric Matyas (CC BY)              |
| Escapan sabiendo lo de los niños        | "The far side of Proxima Centauri", Sascha Ende (CC BY 4.0) |
| Se quedan con los niños / nadie votó    | "Bittersweet", Emma M. Andersson (CC0)           |
| Los liberan (y se quedan delante)       | "Bittersweet Ending", Arold Valda (CC BY 4.0)    |

Los créditos están en screens/creditos.py. Los archivos van normalizados al
mismo volumen (ffmpeg loudnorm, -20 LUFS), así que todas suenan parejo.
Sirve igual en el modo normal, la feria y en red (el cliente lo llama desde
su pantalla de resultados).
"""

import os

from juego.audio_manager import audio_manager

CARPETA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "Audio", "Musica")
ARCHIVOS = {
    "derrota": "final_derrota",
    "victoria": "final_sin_entrar",
    "sin_entrar": "final_sin_entrar",
    "escaparon": "final_escaparon",
    "quedarse": "final_quedarse",
    "nadie": "final_quedarse",
    "liberados": "final_liberados",
}
VOLUMEN = 0.6


def clave(mision):
    """Qué final fue ("derrota", "victoria" o el de la sala oculta), o None."""
    if mision is None or not getattr(mision, "activa", False):
        return None
    resultado = getattr(mision, "resultado", None)
    if resultado is None:
        return None
    final = getattr(mision, "final", None)
    if final in ARCHIVOS:
        return final
    return "victoria" if resultado == "victoria" else "derrota"


def ruta(clave_final):
    nombre = ARCHIVOS.get(clave_final)
    if nombre is None:
        return None
    for extension in (".ogg", ".mp3", ".wav"):
        r = os.path.join(CARPETA, nombre + extension)
        if os.path.exists(r):
            return r
    return None


def actualizar(mision):
    """En los resultados: la canción de ese final (sin archivo, silencio)."""
    actualizar_clave(clave(mision))


def actualizar_clave(clave_final):
    r = ruta(clave_final)
    if r is None:
        parar()
        return
    audio_manager.cancion(r, VOLUMEN)


def parar():
    if audio_manager.sonando_cancion:
        audio_manager.parar_cancion()
