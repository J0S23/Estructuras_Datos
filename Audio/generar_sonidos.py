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
    susto       golpe grave con chirrido: despiertan los aliens
    apagon      la nave se apaga: zumbido que cae y un golpe
    luz         la nave vuelve: zumbido que sube
    compuerta   golpe metálico pesado de una compuerta que baja
    recoger     dos notas cortas al recoger algo
    encajar     clic mecánico al dejar una pieza en la cápsula
    hackeo      descarga eléctrica entrecortada
    sello       campo de energía que se levanta
    senal       ping de radar (Emisión y señuelo)
    curar       campanitas que suben (Biomante)
    impulso     barrido que sube (Impulso energético)
    logro       arpegio corto de logro
    expuesto    glitch y acorde: expusieron al infiltrado
    eliminado   tres notas que bajan: alguien quedó fuera
    victoria    fanfarria corta
    derrota     notas graves que bajan
    pausa       dos notas suaves al abrir la pausa
    menu_mover  tic al moverse por un menú
    menu_ok     clic al confirmar
    ambiente    zumbido de la nave en bucle (se oye durante la partida)
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


def arpegio(frecuencias, dur_nota, vol=0.5, forma="square", caida=0.12):
    salida = []
    for f in frecuencias:
        salida += tono(f, dur_nota, vol, forma, caida=caida)
    return salida


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

    # -- Nuevos ------------------------------------------------------------------
    guardar("susto", mezclar(tono(40, 0.9, 1.0, caida=0.35), ruido(0.5, 0.8, 0.15, 3),
                             tono(1200, 0.5, 0.25, "saw", caida=0.2, f_final=1600)), 0.9)

    guardar("apagon", mezclar(tono(220, 1.1, 0.6, "saw", caida=0.6, f_final=30),
                              silencio(0.9) + mezclar(tono(55, 0.3, 1.0, caida=0.08),
                                                      ruido(0.2, 0.6, 0.05, 8))), 0.8)
    guardar("luz", mezclar(tono(40, 1.0, 0.6, "saw", ataque=0.4, f_final=220),
                           silencio(0.85) + tono(880, 0.15, 0.3, "square", caida=0.08)), 0.6)

    guardar("compuerta", ruido(0.25, 0.5, 0.15, 3) + mezclar(tono(60, 0.45, 1.0, caida=0.12),
                                                             ruido(0.2, 0.9, 0.05, 12),
                                                             tono(140, 0.3, 0.4, "square", caida=0.05)), 0.85)

    guardar("recoger", tono(784, 0.06, 0.5, "square", caida=0.05) +
            tono(1175, 0.09, 0.5, "square", caida=0.07), 0.4)
    guardar("encajar", mezclar(ruido(0.05, 1.0, 0.01, 2), tono(320, 0.12, 0.6, "square", caida=0.03))
            + silencio(0.04) + mezclar(ruido(0.05, 1.0, 0.01, 2), tono(480, 0.15, 0.6, "square", caida=0.04)),
            0.55)

    zap = []
    for _ in range(9):
        zap += mezclar(ruido(0.025, 1.0, 0.02, 1), tono(rng.choice([1400, 1800, 2400]), 0.025, 0.4, "square"))
        zap += silencio(rng.uniform(0.005, 0.02))
    guardar("hackeo", zap + tono(1600, 0.3, 0.4, "saw", caida=0.12, f_final=200), 0.5)

    guardar("sello", mezclar(tono(110, 0.9, 0.6, "saw", ataque=0.3, caida=0.6, f_final=220),
                             tono(330, 0.9, 0.3, "sin", ataque=0.3, caida=0.6, f_final=660),
                             tono(334, 0.9, 0.3, "sin", ataque=0.3, caida=0.6, f_final=668)), 0.6)

    guardar("senal", tono(1320, 0.12, 0.6, caida=0.06) + silencio(0.08) +
            tono(1320, 0.4, 0.4, caida=0.15), 0.5)

    guardar("curar", mezclar(arpegio([784, 988, 1175, 1568], 0.11, 0.4, "sin", caida=0.2),
                             silencio(0.2) + tono(1568, 0.5, 0.2, "sin", caida=0.25)), 0.5)
    guardar("impulso", mezclar(tono(200, 0.6, 0.6, "saw", ataque=0.05, caida=0.4, f_final=1200),
                               ruido(0.6, 0.4, 0.3, 1)), 0.5)

    guardar("logro", arpegio([523, 659, 784], 0.08, 0.5) + tono(1047, 0.35, 0.5, "square", caida=0.15), 0.4)

    glitch = []
    for _ in range(6):
        glitch += tono(rng.choice([300, 450, 900, 1300]), rng.uniform(0.02, 0.05), 0.5, "square")
    acorde_bien = mezclar(tono(392, 0.8, 0.4, "saw", caida=0.4), tono(494, 0.8, 0.4, "saw", caida=0.4),
                          tono(587, 0.8, 0.4, "saw", caida=0.4))
    guardar("expuesto", glitch + acorde_bien, 0.6)

    guardar("eliminado", arpegio([392, 330, 262], 0.22, 0.5, "saw", caida=0.25) +
            tono(196, 0.6, 0.5, "saw", caida=0.3), 0.5)
    guardar("victoria", arpegio([523, 523, 523, 659, 784], 0.1, 0.5, caida=0.1) +
            tono(1047, 0.7, 0.5, "square", caida=0.35), 0.45)
    guardar("derrota", arpegio([330, 311, 294], 0.3, 0.5, "saw", caida=0.3) +
            tono(147, 1.0, 0.6, "saw", caida=0.5), 0.5)

    guardar("pausa", tono(660, 0.07, 0.4, caida=0.05) + tono(440, 0.12, 0.4, caida=0.08), 0.4)
    guardar("menu_mover", tono(1000, 0.025, 0.4, "square", caida=0.015), 0.25)
    guardar("menu_ok", mezclar(tono(700, 0.05, 0.5, "square", caida=0.03),
                               ruido(0.02, 0.5, 0.01, 1)), 0.35)

    # Zumbido de la nave: 8 s que empalman sin corte (cada frecuencia da un
    # número entero de vueltas en 8 s, así el final coincide con el inicio).
    dur = 8.0
    n = int(FRECUENCIA * dur)
    zumbido = []
    for i in range(n):
        t = i / FRECUENCIA
        lfo = 0.75 + 0.25 * math.sin(2 * math.pi * 0.25 * t)
        v = (0.55 * math.sin(2 * math.pi * 55 * t) +
             0.25 * math.sin(2 * math.pi * 110.125 * t) +
             0.12 * math.sin(2 * math.pi * 165 * t) * lfo +
             0.06 * math.sin(2 * math.pi * 330.5 * t) * (1 - lfo))
        zumbido.append(v * lfo)
    guardar("ambiente", zumbido, 0.5)


if __name__ == "__main__":
    generar()
