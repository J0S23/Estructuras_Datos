"""Genera los efectos de sonido del juego con matemáticas (sin archivos ajenos).

    python Audio/generar_sonidos.py

Escribe WAV en Audio/SFX/. Son provisionales pero no tienen problemas de
licencia: cuando el equipo consiga sonidos mejores, basta con dejar un archivo
con el mismo nombre (.ogg, .wav o .mp3) y el juego lo usa (audio_manager.py).

    latido      el "pum-pum" del corazón; el juego lo repite al ritmo del pulso
    paso_alien  pisada blanda y pesada
    captura     golpe disonante para el susto cuando te atrapan
    alarma      sirena de dos tonos
    puerta      siseo hidráulico y golpe metálico
    consola     barrido hacia abajo, algo que se apaga
    nota        papel que se arruga
    acierto     pitido corto que sube
    fallo       zumbido corto que baja
    ia_voz      chirridos robóticos de la IA de la nave
"""

import math
import os
import random
import struct
import wave

FRECUENCIA = 22050
CARPETA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "SFX")
rng = random.Random(7)


def tono(f, dur, vol=1.0, forma="sin", ataque=0.005, caida=None, f_final=None):
    n = int(FRECUENCIA * dur)
    salida, fase = [], 0.0
    for i in range(n):
        t = i / FRECUENCIA
        fi = f if f_final is None else f + (f_final - f) * (i / n)
        fase += 2 * math.pi * fi / FRECUENCIA
        if forma == "sin":
            v = math.sin(fase)
        elif forma == "square":
            v = 1.0 if math.sin(fase) >= 0 else -1.0
        else:  # sierra
            v = 2 * ((fase / (2 * math.pi)) % 1) - 1
        env = min(1.0, t / ataque) if ataque else 1.0
        if caida:
            env *= math.exp(-t / caida)
        salida.append(v * env * vol)
    return salida


def ruido(dur, vol=1.0, caida=0.05, suave=6):
    n = int(FRECUENCIA * dur)
    crudo = [rng.uniform(-1, 1) for _ in range(n)]
    # Un promedio móvil le quita los agudos: queda un ruido sordo.
    salida, acum, ventana = [], 0.0, []
    for i, v in enumerate(crudo):
        ventana.append(v)
        acum += v
        if len(ventana) > suave:
            acum -= ventana.pop(0)
        t = i / FRECUENCIA
        salida.append(acum / len(ventana) * vol * math.exp(-t / caida))
    return salida


def silencio(dur):
    return [0.0] * int(FRECUENCIA * dur)


def mezclar(*pistas):
    largo = max(len(p) for p in pistas)
    return [sum(p[i] for p in pistas if i < len(p)) for i in range(largo)]


def guardar(nombre, muestras, volumen=0.9):
    pico = max(1e-6, max(abs(m) for m in muestras))
    os.makedirs(CARPETA, exist_ok=True)
    with wave.open(os.path.join(CARPETA, nombre + ".wav"), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(FRECUENCIA)
        w.writeframes(b"".join(struct.pack("<h", int(m / pico * volumen * 32767)) for m in muestras))
    print("  ", nombre)


def generar():
    print("Generando en", CARPETA)
    golpe1 = mezclar(tono(58, 0.16, 1.0, caida=0.045), ruido(0.05, 0.3, 0.01, 20))
    golpe2 = mezclar(tono(50, 0.18, 0.8, caida=0.05), ruido(0.05, 0.2, 0.01, 20))
    guardar("latido", golpe1 + silencio(0.07) + golpe2)

    guardar("paso_alien", mezclar(ruido(0.18, 1.0, 0.04, 30), tono(70, 0.15, 0.6, caida=0.04, f_final=45)), 0.8)

    acorde = mezclar(tono(311, 0.9, 0.5, "saw", caida=0.35), tono(330, 0.9, 0.5, "saw", caida=0.35),
                     tono(466, 0.9, 0.4, "saw", caida=0.3, f_final=520),
                     ruido(0.4, 1.2, 0.12, 2), tono(45, 0.6, 1.0, caida=0.2))
    guardar("captura", acorde, 0.95)

    sirena = []
    for _ in range(2):
        sirena += tono(880, 0.2, 0.6, "square") + tono(660, 0.2, 0.6, "square")
    guardar("alarma", sirena, 0.6)

    guardar("puerta", ruido(0.35, 0.7, 0.2, 2) + mezclar(tono(90, 0.25, 1.0, caida=0.06),
                                                        ruido(0.1, 0.6, 0.02, 10)), 0.8)
    guardar("consola", tono(900, 0.6, 0.6, "square", caida=0.3, f_final=120), 0.5)
    guardar("nota", ruido(0.12, 1.0, 0.04, 1) + ruido(0.1, 0.7, 0.03, 1), 0.5)
    guardar("acierto", tono(660, 0.07, 0.6, "square") + tono(990, 0.1, 0.6, "square", caida=0.08), 0.45)
    guardar("fallo", tono(220, 0.25, 0.6, "saw", caida=0.15, f_final=110), 0.5)

    voz = []
    for _ in range(7):
        voz += tono(rng.choice([520, 610, 740, 880, 990]), rng.uniform(0.03, 0.07), 0.5, "square")
        voz += silencio(rng.uniform(0.01, 0.03))
    guardar("ia_voz", voz, 0.35)


if __name__ == "__main__":
    generar()
