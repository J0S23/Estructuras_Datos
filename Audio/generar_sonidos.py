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
    susurro     el Cambiaformas disfrazado anda cerca
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
    cf_revela   el Cambiaformas se transforma: chillido que sube, glitch y golpe
    cf_captura  te atrapó el Cambiaformas: el mismo chillido, pero cayendo, y un
                golpe más grave (parecidos a propósito: es el mismo alien)
    captura_ciego    te atrapó el Ciego: pings de sonar que se cierran, un
                     gruñido sordo y el golpe
    captura_cazador  te atrapó el Cazador: un zumbido de velocidad que pasa,
                     chillido y zarpazo
    captura_vigia    te atrapó el Vigía: pitidos de "fijando blanco" cada vez
                     más seguidos y un acorde eléctrico
    captura_sombra   te alcanzó la Sombra: un susurro que crece, silencio y un
                     chasquido de dientes con un golpe grave
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
    generar_susurro()
    generar_cambiaformas()
    generar_sustos_aliens()


def generar_susurro():
    """Un susurro (el Cambiaformas disfrazado está cerca): siseos que suben y
    bajan, como sílabas que no se entienden."""
    dur = 1.6
    siseo = ruido(dur, 1.0, 99, 1)          # agudo: "ssss"
    aliento = ruido(dur, 0.6, 99, 5)        # más sordo: "hhhh"
    salida = []
    for i in range(len(siseo)):
        t = i / FRECUENCIA
        silabas = max(0.0, math.sin(math.pi * t * 4.2)) ** 2
        entrada = min(1.0, t / 0.25) * min(1.0, (dur - t) / 0.4)
        salida.append((siseo[i] * 0.6 + aliento[i]) * silabas * entrada)
    guardar("susurro", salida, 0.45)


def generar_cambiaformas():
    """Los sustos del Cambiaformas, distintos del "captura" de los demás
    aliens. Usan su propio azar para no cambiar los otros sonidos.

        python -c "import sys; sys.path.insert(0, 'Audio'); import generar_sonidos as g; g.generar_cambiaformas()"
    """
    azar = random.Random(23)

    def chasquidos(dur, vol):
        """Glitch: ruido cortado en pedacitos, como una señal que falla."""
        n = int(FRECUENCIA * dur)
        salida = []
        while len(salida) < n:
            largo = azar.randint(80, 900)
            suena = azar.random() < 0.6
            salida += [azar.uniform(-1, 1) * vol if suena else 0.0 for _ in range(largo)]
        return [v * math.exp(-i / FRECUENCIA / (dur * 0.6)) for i, v in enumerate(salida[:n])]

    revela = mezclar(tono(220, 1.0, 0.5, "saw", caida=0.6, f_final=880),
                     tono(233, 1.0, 0.4, "saw", caida=0.6, f_final=940),
                     chasquidos(0.9, 0.5),
                     silencio(0.35) + tono(42, 0.6, 1.0, caida=0.25))
    guardar("cf_revela", revela, 0.95)
    captura = mezclar(tono(900, 0.8, 0.5, "saw", caida=0.4, f_final=180),
                      tono(950, 0.8, 0.4, "saw", caida=0.4, f_final=170),
                      chasquidos(0.5, 0.6), tono(35, 0.9, 1.0, caida=0.35))
    guardar("cf_captura", captura, 0.95)



def generar_sustos_aliens():
    """Un susto por tipo de alien (ambiente.py), distinto del "captura" de
    siempre, que queda de respaldo. Con su propio azar, para no
    cambiar los otros sonidos.

        python -c "import sys; sys.path.insert(0, 'Audio'); import generar_sonidos as g; g.generar_sustos_aliens()"
    """
    azar = random.Random(31)

    def soplo(dur, vol, suave, subida=True):
        """Ruido que crece (o se apaga): aire, velocidad."""
        n = int(FRECUENCIA * dur)
        salida, acum, ventana = [], 0.0, []
        for i in range(n):
            v = azar.uniform(-1, 1)
            ventana.append(v)
            acum += v
            if len(ventana) > suave:
                acum -= ventana.pop(0)
            k = i / n
            salida.append(acum / len(ventana) * vol * ((k ** 2) if subida else (1 - k) ** 2))
        return salida

    # Ciego: tres pings de sonar cada vez más cerca (más fuertes y seguidos),
    # un gruñido sordo y el golpe.
    pings = []
    for espera, vol in ((0.0, 0.25), (0.16, 0.45), (0.26, 0.8)):
        pings.append(silencio(espera) + tono(1250, 0.12, vol, caida=0.05))
    grunido = silencio(0.36) + [v * (0.5 + 0.5 * math.sin(i / FRECUENCIA * 2 * math.pi * 23))
                                for i, v in enumerate(soplo(0.55, 1.0, 40, subida=False))]
    golpe = silencio(0.36) + tono(40, 0.6, 1.0, caida=0.22)
    guardar("captura_ciego", mezclar(*pings, grunido, golpe,
                                     silencio(0.36) + tono(180, 0.5, 0.35, "saw", caida=0.2, f_final=120)), 0.95)

    # Cazador: algo que pasa rapidísimo (soplo que sube), chillido y zarpazo.
    paso = soplo(0.24, 1.0, 3)
    chillido = silencio(0.2) + mezclar(tono(620, 0.5, 0.5, "saw", caida=0.25, f_final=1500),
                                       tono(660, 0.5, 0.4, "saw", caida=0.25, f_final=1580))
    zarpazo = silencio(0.26) + mezclar(soplo(0.12, 1.0, 1, subida=False), tono(48, 0.4, 0.9, caida=0.15))
    guardar("captura_cazador", mezclar(paso, chillido, zarpazo), 0.95)

    # Vigía: pitidos de "fijando blanco" cada vez más seguidos y un acorde
    # eléctrico al fijarlo.
    pitidos, t = [], 0.0
    for espera in (0.13, 0.1, 0.075, 0.055, 0.045):
        pitidos.append(silencio(t) + tono(1760, 0.04, 0.4, "square", caida=0.03))
        t += espera
    acorde = silencio(t) + mezclar(tono(440, 0.55, 0.45, "square", caida=0.3),
                                   tono(466, 0.55, 0.4, "square", caida=0.3),
                                   tono(932, 0.55, 0.25, "saw", caida=0.25, f_final=700),
                                   tono(44, 0.55, 0.9, caida=0.25))
    guardar("captura_vigia", mezclar(*pitidos, acorde), 0.95)

    # Sombra: un susurro que crece (sílabas que no se entienden), un instante
    # de silencio y el chasquido de dientes con un golpe grave.
    susurro = []
    for i, v in enumerate(soplo(0.55, 1.0, 2)):
        t = i / FRECUENCIA
        silabas = max(0.0, math.sin(math.pi * t * 9)) ** 2
        susurro.append(v * (0.3 + 0.7 * silabas) * (t / 0.55 + 0.2))
    chasquido = silencio(0.62) + mezclar(soplo(0.05, 1.0, 1, subida=False),
                                          tono(2400, 0.05, 0.4, "square", caida=0.02))
    golpe = silencio(0.62) + mezclar(tono(38, 0.6, 1.0, caida=0.25),
                                     tono(150, 0.45, 0.4, "saw", caida=0.18, f_final=70))
    guardar("captura_sombra", mezclar(susurro, chasquido, golpe), 0.95)


def generar_extras():
    """Voces de los aliens, pasos en el pasto, golpes en el casillero, arreglos,
    el cohete de la cápsula y la música de fondo (calma y tensión). Con su
    propio azar, para no cambiar los otros sonidos.

        python -c "import sys; sys.path.insert(0, 'Audio'); import generar_sonidos as g; g.generar_extras()"

    Son provisionales: un archivo con el mismo nombre (.ogg o .wav) los
    reemplaza. Ojo: un .mp3 no le gana al .wav que ya está (audio_manager.py
    busca .ogg, .wav y .mp3, en ese orden): hay que borrar el .wav.

        voz_ciego_1/2         chasquidos de garganta (como un "clicker")
        voz_vigia_1/2         ronroneo grave entrecortado, de alien que acecha
        voz_cazador_1/2       siseo y chillido corto
        guardia_esfuerzo_1/2  gruñido de esfuerzo, pesado
        sombra_desvanece      soplo que se deshace cuando vuelve la luz
        paso_pasto_1/2        pisada en el pasto de la Biosfera
        casillero_golpe       golpe metálico en la puerta del casillero
        reparar               carraca y golpe de herramienta
        tecleo                teclas de consola
        cohete                la cápsula despega
        musica_calma          bucle tranquilo (16 s)
        musica_tension        bucle de persecución (8 s)
    """
    azar = random.Random(47)
    F = FRECUENCIA
    dos_pi = 2 * math.pi

    def blanco(n):
        return [azar.uniform(-1, 1) for _ in range(n)]

    def pasa_bajos(muestras, corte):
        """Filtro de un polo: deja lo que está por debajo de `corte` Hz."""
        a = 1 - math.exp(-dos_pi * corte / F)
        salida, y = [], 0.0
        for v in muestras:
            y += a * (v - y)
            salida.append(y)
        return salida

    def pasa_altos(muestras, corte):
        bajos = pasa_bajos(muestras, corte)
        return [v - b for v, b in zip(muestras, bajos)]

    def banda(muestras, bajo, alto):
        return pasa_altos(pasa_bajos(muestras, alto), bajo)

    def envolver(muestras, ataque, salida_s):
        n = len(muestras)
        a, s = max(1, int(ataque * F)), max(1, int(salida_s * F))
        return [v * min(1.0, i / a, (n - i) / s) for i, v in enumerate(muestras)]

    def poner(base, pista, en_s, vol=1.0):
        """Suma `pista` dentro de `base` empezando en `en_s` segundos."""
        inicio = int(en_s * F)
        if inicio + len(pista) > len(base):
            base.extend([0.0] * (inicio + len(pista) - len(base)))
        for i, v in enumerate(pista):
            base[inicio + i] += v * vol
        return base

    # -- Ciego: chasquidos de garganta ---------------------------------------------
    def chasquido(f):
        """Un clic seco: golpe de ruido muy corto con una resonancia hueca."""
        n = int(0.022 * F)
        clic = banda(blanco(n), 500, 4200)
        return [clic[i] * math.exp(-i / F / 0.0035) * 1.3 +
                math.sin(dos_pi * f * i / F) * math.exp(-i / F / 0.006) * 0.8 for i in range(n)]

    def voz_ciego(esperas, tono_base):
        pista, t = [], 0.0
        for k, espera in enumerate(esperas):
            poner(pista, chasquido(tono_base + azar.randint(-140, 180)), t, 0.6 + 0.4 * azar.random())
            t += espera
        # El graznido del final: una garganta que raspa.
        n = int(0.42 * F)
        raspa = pasa_bajos(blanco(n), 900)
        graznido = [(raspa[i] * 0.9 + (2 * ((95 * i / F) % 1) - 1) * 0.5)
                    * (0.5 + 0.5 * math.sin(dos_pi * 31 * i / F)) for i in range(n)]
        poner(pista, envolver(graznido, 0.05, 0.25), t + 0.03, 0.55)
        return pista

    guardar("voz_ciego_1", voz_ciego([0.11, 0.09, 0.07, 0.055, 0.05, 0.05, 0.06, 0.08, 0.12], 1150), 0.8)
    guardar("voz_ciego_2", voz_ciego([0.05, 0.05, 0.06, 0.2, 0.06, 0.05, 0.05, 0.05], 900), 0.8)

    # -- Vigía: ronroneo grave entrecortado ------------------------------------------
    def voz_vigia(dur, pulsos_ini, pulsos_fin, f):
        n = int(dur * F)
        aire = pasa_bajos(blanco(n), 700)
        pista, fase, fase_p = [], 0.0, 0.0
        for i in range(n):
            k = i / n
            fase += dos_pi * (f * (1 - 0.18 * k)) / F
            fase_p += (pulsos_ini + (pulsos_fin - pulsos_ini) * k) / F
            pulso = math.exp(-(fase_p % 1) * 7)             # cada pulso: un golpe de garganta
            sierra = 2 * ((fase / dos_pi) % 1) - 1
            pista.append((sierra * 0.7 + aire[i] * 1.6) * pulso)
        return envolver(pasa_bajos(pista, 1500), 0.08, 0.3)

    guardar("voz_vigia_1", voz_vigia(1.3, 26, 14, 72), 0.75)
    guardar("voz_vigia_2", voz_vigia(0.9, 14, 30, 64), 0.75)

    # -- Cazador: siseo y chillido ---------------------------------------------------
    def voz_cazador(dur, f_ini, f_fin, siseo_s):
        n = int(dur * F)
        siseo = envolver(pasa_altos(blanco(int(siseo_s * F)), 2500), 0.12, 0.08)
        pista = [v * 0.5 for v in siseo]
        m = n - len(siseo)
        ruido_m = banda(blanco(m), 900, 5000)
        grito, fase = [], 0.0
        for i in range(m):
            k = i / m
            f = f_ini + (f_fin - f_ini) * (k ** 0.6)
            fase += dos_pi * f * (1 + 0.04 * math.sin(dos_pi * 38 * i / F)) / F
            sierra = 2 * ((fase / dos_pi) % 1) - 1
            cuadrada = 1.0 if math.sin(fase * 1.5) >= 0 else -1.0
            grito.append(sierra * 0.55 + cuadrada * 0.2 + ruido_m[i] * 0.7)
        return pista + envolver(grito, 0.02, 0.22)

    guardar("voz_cazador_1", voz_cazador(0.95, 520, 1350, 0.3), 0.7)
    guardar("voz_cazador_2", voz_cazador(0.7, 900, 480, 0.18), 0.7)

    # -- Guardia: gruñido de esfuerzo -------------------------------------------------
    def esfuerzo(dur, f, empuje):
        n = int(dur * F)
        aire = pasa_bajos(blanco(n), 1100)
        pista, fase = [], 0.0
        for i in range(n):
            k = i / n
            fase += dos_pi * f * (1 + empuje * math.sin(math.pi * k)) / F
            sierra = 2 * ((fase / dos_pi) % 1) - 1
            ronco = 0.65 + 0.35 * math.sin(dos_pi * 27 * i / F)
            pista.append((sierra * 0.8 + aire[i] * 1.4) * ronco * math.sin(math.pi * k) ** 0.6)
        resoplido = envolver(pasa_bajos(blanco(int(0.3 * F)), 1800), 0.03, 0.26)
        return pasa_bajos(pista, 650) + [v * 0.35 for v in resoplido]

    guardar("guardia_esfuerzo_1", esfuerzo(0.55, 68, 0.25), 0.85)
    guardar("guardia_esfuerzo_2", esfuerzo(0.8, 58, -0.15), 0.85)

    # -- Sombra: se deshace ------------------------------------------------------------
    dur = 1.7
    n = int(dur * F)
    aire = blanco(n)
    corte_y, pista = 0.0, []
    for i in range(n):
        k = i / n
        a = 1 - math.exp(-dos_pi * (3800 * (1 - k) ** 2 + 180) / F)   # el filtro se cierra
        corte_y += a * (aire[i] - corte_y)
        brillo = (math.sin(dos_pi * (1480 - 900 * k) * i / F) * 0.12 +
                  math.sin(dos_pi * (1493 - 880 * k) * i / F) * 0.12)
        tiembla = 0.75 + 0.25 * math.sin(dos_pi * (11 - 7 * k) * i / F)
        pista.append((corte_y * 1.2 + brillo) * tiembla * (1 - k) ** 1.6 * min(1.0, i / (0.05 * F)))
    guardar("sombra_desvanece", pista, 0.6)

    # -- Pasos en el pasto -------------------------------------------------------------
    def pasto(crujidos):
        pista = []
        for en_s, largo, vol in crujidos:
            hoja = pasa_altos(pasa_bajos(blanco(int(largo * F)), 5200), 1300)
            poner(pista, [v * math.exp(-i / F / (largo * 0.35)) for i, v in enumerate(hoja)], en_s, vol)
        return pista

    guardar("paso_pasto_1", pasto([(0.0, 0.09, 1.0), (0.05, 0.07, 0.6), (0.11, 0.08, 0.45)]), 0.45)
    guardar("paso_pasto_2", pasto([(0.0, 0.07, 0.8), (0.035, 0.1, 1.0), (0.12, 0.06, 0.4)]), 0.45)

    # -- Golpes en el casillero --------------------------------------------------------
    def golpe_metal(vol):
        n = int(0.45 * F)
        lata = banda(blanco(n), 300, 3000)
        pista = []
        for i in range(n):
            t = i / F
            v = math.sin(dos_pi * 62 * t) * math.exp(-t / 0.06) * 1.0        # el puño
            for f, caida, peso in ((233, 0.16, 0.5), (377, 0.12, 0.4), (611, 0.09, 0.3),
                                   (989, 0.07, 0.22), (1597, 0.05, 0.15)):   # la lata que vibra
                v += math.sin(dos_pi * f * t) * math.exp(-t / caida) * peso
            pista.append((v + lata[i] * math.exp(-t / 0.03) * 0.9) * vol)
        return pista

    casillero = []
    poner(casillero, golpe_metal(1.0), 0.0)
    poner(casillero, golpe_metal(0.7), 0.21)
    guardar("casillero_golpe", casillero, 0.9)

    # -- Arreglos: carraca y golpe de herramienta ----------------------------------------
    reparar = []
    for k in range(6):
        n = int(0.03 * F)
        diente = banda(blanco(n), 1800, 6000)
        poner(reparar, [diente[i] * math.exp(-i / F / 0.006) +
                        math.sin(dos_pi * 2100 * i / F) * math.exp(-i / F / 0.008) * 0.5 for i in range(n)],
              k * 0.055, 0.7)
    n = int(0.3 * F)
    poner(reparar, [(math.sin(dos_pi * 780 * i / F) * 0.5 + math.sin(dos_pi * 1243 * i / F) * 0.35 +
                     math.sin(dos_pi * 1990 * i / F) * 0.2) * math.exp(-i / F / 0.07) for i in range(n)], 0.38, 0.9)
    guardar("reparar", reparar, 0.5)

    tecleo = []
    t = 0.0
    for _ in range(5):
        n = int(0.03 * F)
        tecla = pasa_bajos(blanco(n), 3000)
        poner(tecleo, [tecla[i] * math.exp(-i / F / 0.005) +
                       math.sin(dos_pi * azar.choice([1320, 1480, 1760]) * i / F)
                       * math.exp(-i / F / 0.012) * 0.25 for i in range(n)], t, 0.8)
        t += azar.uniform(0.05, 0.1)
    guardar("tecleo", tecleo, 0.35)

    # -- El cohete de la cápsula ---------------------------------------------------------
    dur = 4.2
    n = int(dur * F)
    trueno = pasa_bajos(blanco(n), 420)
    chispas = pasa_altos(blanco(n), 3000)
    pista = []
    for i in range(n):
        t = i / F
        k = t / dur
        sube = min(1.0, t / 1.1) ** 2                       # el motor arranca
        se_va = 1.0 if t < 2.6 else max(0.0, 1 - (t - 2.6) / 1.6) ** 1.5
        motor = math.sin(dos_pi * (38 + 60 * k) * t) * 0.5
        tiembla = 0.7 + 0.3 * math.sin(dos_pi * 13 * t)
        pista.append((trueno[i] * 3.2 * tiembla + motor + chispas[i] * 0.18 * sube) * sube * se_va)
    guardar("cohete", pista, 0.95)

    # -- Música de fondo -----------------------------------------------------------------
    def bucle_vacio(dur):
        return [0.0] * int(dur * F)

    def nota(pista, f, en_s, dur, vol, ataque, salida_s, forma="sin", vibrato=0.0):
        """Una nota dentro de un bucle: lo que se pasa del final vuelve al
        principio, así el bucle empalma sin corte."""
        total = len(pista)
        n = int(dur * F)
        inicio = int(en_s * F)
        a, s = max(1, int(ataque * F)), max(1, int(salida_s * F))
        fase = 0.0
        for i in range(n):
            fase += dos_pi * f * (1 + vibrato * math.sin(dos_pi * 5 * i / F)) / F
            if forma == "sin":
                v = math.sin(fase) + 0.25 * math.sin(2 * fase)
            elif forma == "tri":
                v = 2 * abs(2 * ((fase / dos_pi) % 1) - 1) - 1
            else:
                v = 2 * ((fase / dos_pi) % 1) - 1
            pista[(inicio + i) % total] += v * vol * min(1.0, i / a, (n - i) / s)

    # Calma: cuatro acordes lentos (La menor, Fa, Do, Sol) y unas notas sueltas.
    calma = bucle_vacio(16.0)
    acordes = [(110.0, 220.0, 261.63, 329.63), (87.31, 174.61, 261.63, 349.23),
               (130.81, 196.0, 261.63, 329.63), (98.0, 196.0, 246.94, 293.66)]
    melodia = [(659.25, 1.0), (523.25, 2.5), (698.46, 5.0), (523.25, 6.5),
               (783.99, 9.0), (659.25, 10.5), (587.33, 13.0), (493.88, 14.5)]
    for k, acorde in enumerate(acordes):
        for j, f in enumerate(acorde):
            nota(calma, f, k * 4.0 - 0.6, 5.2, 0.16 if j else 0.22, 1.4, 1.8)
            nota(calma, f * 1.004, k * 4.0 - 0.6, 5.2, 0.07, 1.4, 1.8)      # un poco desafinada: más cálida
    for f, en_s in melodia:
        nota(calma, f, en_s, 1.8, 0.09, 0.03, 1.6, "tri")
    guardar("musica_calma", calma, 0.6)

    # Tensión: un bajo que late, dos notas pegadas que rozan y un golpe sordo.
    tension = bucle_vacio(8.0)
    pulso = 8.0 / 32                                        # 32 corcheas en el bucle
    for k in range(32):
        f = 73.42 if k % 16 < 12 else 69.3                   # Re, y baja medio tono al final
        nota(tension, f, k * pulso, pulso * 0.85, 0.5 if k % 4 == 0 else 0.3, 0.008, 0.09, "saw")
    # (filtrado dos veces seguidas y se queda la segunda vuelta: así el filtro
    # ya viene "caliente" y el bucle sigue empalmando)
    tension = pasa_bajos(tension + tension, 520)[len(tension):]
    for en_s, f in ((0.0, 293.66), (4.0, 277.18)):
        nota(tension, f, en_s - 0.4, 4.6, 0.11, 1.2, 1.4, "saw", 0.004)
        nota(tension, f * 1.0595, en_s - 0.4, 4.6, 0.09, 1.2, 1.4, "saw", 0.004)   # medio tono arriba: roza
    for k in (0, 3, 8, 11, 16, 19, 24, 27, 30):
        n = int(0.22 * F)
        inicio = int(k * pulso * F)
        for i in range(n):
            t = i / F
            tension[(inicio + i) % len(tension)] += math.sin(dos_pi * (62 - 60 * t) * t) * math.exp(-t / 0.07) * 0.75
    for en_s in (1.75, 3.75, 5.75, 7.75):                    # un tic agudo, como un reloj
        nota(tension, 1760.0, en_s, 0.08, 0.05, 0.002, 0.07, "tri")
    guardar("musica_tension", tension, 0.6)


if __name__ == "__main__":
    generar()
    generar_extras()
