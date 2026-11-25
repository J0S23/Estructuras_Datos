"""Cuándo empieza cada subtítulo dentro de la narración de Lucas.

    python Audio/generar_cortes.py

Lee cada narración de Audio/Narrador/ (apertura_*, final_*) con ffmpeg, busca
sus pausas y escoge, en orden, las que mejor caen donde termina cada oración
de lo que dice Lucas (el texto del guion, docs/guion_narrador.md: a veces
dice más que los subtítulos, como "Esa misma semana, en otras pantallas.";
se espera que cada oración dure según sus letras). Cada subtítulo empieza
con la oración del guion donde empieza su texto. Guarda en
Audio/Narrador/cortes.json, para cada narración, en qué ms empieza cada
subtítulo (el primero puede empezar después de 0: antes no hay subtítulo). El juego lo lee en juego/voces.py
(`cortes`); si una narración no está ahí, reparte los subtítulos según el
largo de cada texto. Hay que volver a correrlo si cambia un audio o un texto.
"""

import array
import json
import math
import os
import re
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
CARPETA = os.path.join(RAIZ, "Audio", "Narrador")
SR = 8000
VENTANA = 160                   # 20 ms
PAUSA_MIN_S = 0.12
RUIDO_MAX_S = 0.12              # (un golpecito más corto que esto no es voz)


def muestras(ruta):
    crudo = subprocess.run(["ffmpeg", "-v", "error", "-i", ruta, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"],
                           capture_output=True, check=True).stdout
    return array.array("h", crudo)


def tramos_con_voz(x):
    """(inicio, fin) en segundos de lo que suena (umbral: 32 dB bajo lo más fuerte)."""
    rms = []
    for i in range(0, len(x) - VENTANA, VENTANA):
        bloque = x[i:i + VENTANA]
        rms.append(math.sqrt(sum(v * v for v in bloque) / VENTANA) + 1e-6)
    tope = max(rms)
    umbral = tope * 10 ** (-32 / 20)
    tramos, dentro = [], None
    for k, r in enumerate(rms):
        if r >= umbral and dentro is None:
            dentro = k
        elif r < umbral and dentro is not None:
            tramos.append([dentro, k])
            dentro = None
    if dentro is not None:
        tramos.append([dentro, len(rms)])
    s = VENTANA / SR
    tramos = [t for t in tramos if (t[1] - t[0]) * s >= RUIDO_MAX_S]
    # (une los tramos separados por menos de PAUSA_MIN_S)
    unidos = []
    for a, b in tramos:
        if unidos and (a - unidos[-1][1]) * s < PAUSA_MIN_S:
            unidos[-1][1] = b
        else:
            unidos.append([a, b])
    return [(a * s, b * s) for a, b in unidos]


def _palabras(t):
    return re.findall(r"\w+", t.lower())


def oraciones(guion):
    """Las oraciones de lo que dice el narrador (corta en . ? ! : y en "...")."""
    return [p.strip() for p in re.split(r"(?<=[.?!:…])\s+", guion.replace("...", "…")) if _palabras(p)]


def _oracion_de(linea, ors):
    """En qué oración del guion empieza el subtítulo `linea` (por sus primeras palabras)."""
    inicio = _palabras(linea)[:3]
    for k, o in enumerate(ors):
        p = _palabras(o)
        if any(p[i:i + len(inicio)] == inicio for i in range(len(p))):
            return k
    return None


def cortes(ruta, textos, guion=None):
    """El ms en que empieza cada línea de `textos` dentro del audio."""
    tramos = tramos_con_voz(muestras(ruta))
    if not tramos:
        return [0] * len(textos)
    ini, fin = tramos[0][0], tramos[-1][1]
    ors = oraciones(guion or " ".join(textos))
    if len(ors) < 2:
        return [0] * len(textos)
    pausas = [(tramos[i][1], tramos[i + 1][0]) for i in range(len(tramos) - 1)]
    letras = [len(o) for o in ors]
    total = sum(letras)
    esperado, acc = [], 0
    for n in letras[:-1]:
        acc += n
        esperado.append(ini + (fin - ini) * acc / total)
    m, P = len(esperado), len(pausas)
    # Programación dinámica: a cada fin de oración, una pausa distinta y en
    # orden; se premia una pausa larga y se castiga caer lejos de lo esperado.
    INF = float("inf")
    costo = [[INF] * (P + 1) for _ in range(m + 1)]
    desde = [[None] * (P + 1) for _ in range(m + 1)]
    for p in range(P + 1):
        costo[0][p] = 0.0
    for j in range(1, m + 1):
        for p in range(j, P + 1):
            a, b = pausas[p - 1]
            c = abs((a + b) / 2 - esperado[j - 1]) / max(1.0, fin - ini) * 12 - (b - a) * 3
            mejor, de = INF, None
            for q in range(j - 1, p):
                if costo[j - 1][q] < mejor:
                    mejor, de = costo[j - 1][q], q
            costo[j][p] = mejor + c
            desde[j][p] = de
    if m > P:
        empiezan = [ini] + esperado          # (menos pausas que oraciones: según las letras)
    else:
        p = min(range(m, P + 1), key=lambda q: costo[m][q])
        elegidas = []
        for j in range(m, 0, -1):
            elegidas.append(pausas[p - 1][1])
            p = desde[j][p]
        elegidas.reverse()
        empiezan = [ini] + elegidas
    salida = []
    for i, linea in enumerate(textos):
        k = _oracion_de(linea, ors)
        if k is None:
            k = round(i * len(ors) / len(textos))
        salida.append(int(max(0.0, empiezan[k] - 0.12) * 1000))
    for i in range(1, len(salida)):
        salida[i] = max(salida[i], salida[i - 1] + 500)
    return salida


def guiones():
    """Lo que dice el narrador en cada archivo (la tabla de docs/guion_narrador.md)."""
    ruta = os.path.join(RAIZ, "docs", "guion_narrador.md")
    salida = {}
    try:
        for fila in open(ruta, encoding="utf-8"):
            m = re.match(r"\|\s*`(\w+)\.mp3`\s*\|\s*(.+?)\s*\|\s*$", fila)
            if m:
                salida[m.group(1)] = m.group(2)
    except OSError:
        pass
    return salida


def textos_de_narraciones():
    from screens import cinematica
    from data.historia import FINALES
    textos = {f"apertura_{i + 1}": e["textos"] for i, e in enumerate(cinematica.CINEMATICA)}
    textos.update({f"final_{k}": f["escena"] for k, f in FINALES.items()})
    return textos


def main():
    resultado = {}
    dichos = guiones()
    for nombre, textos in textos_de_narraciones().items():
        ruta = os.path.join(CARPETA, nombre + ".mp3")
        if not os.path.exists(ruta) or not textos:
            continue
        resultado[nombre] = cortes(ruta, textos, dichos.get(nombre))
        print(f"{nombre}: {resultado[nombre]}")
    with open(os.path.join(CARPETA, "cortes.json"), "w", encoding="utf-8") as f:
        json.dump(resultado, f, indent=1, ensure_ascii=False)
        f.write("\n")


if __name__ == "__main__":
    main()
