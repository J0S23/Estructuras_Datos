"""Ensayo de la feria: muchas partidas seguidas sin cerrar el juego.

    python pruebas/ensayo_feria.py            (10 partidas de 60 s)
    python pruebas/ensayo_feria.py 20 90      (20 partidas de 90 s)

No es una prueba de la suite: es para ver, antes de la feria, que el juego no
se pone lento ni se come la memoria con el tiempo (cachés que crecen sin tope,
cosas de una partida que quedan vivas en la siguiente). Usa la pantalla de
atracción (juego/demo.py): el juego se juega solo, partida tras partida en
modo feria, pasando por el menú y el ranking como en la feria. Por cada
partida imprime la memoria del proceso, los objetos de Python vivos y cuánto
tardan los cuadros. Al final dice si algo fue creciendo.

En el PC de la feria se puede correr con ventana (sin SDL_VIDEODRIVER=dummy):
    NEXUS_VENTANA=1 python pruebas/ensayo_feria.py 5
"""

import gc
import os
import statistics
import sys
import time

if not os.environ.get("NEXUS_VENTANA"):
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

import pygame

pygame.init()

from juego import app as App
from juego import demo, feria

args = [a for a in sys.argv[1:] if not a.startswith("-")]
PARTIDAS = int(args[0]) if args else 10
SEGUNDOS = float(args[1]) if len(args) > 1 else 60
demo.ESPERA_MENU_S, demo.PARTIDA_S, demo.RANKING_S = 0.5, SEGUNDOS, 1


def memoria_mb():
    """La memoria que usa el proceso ahora (MB)."""
    try:
        with open("/proc/self/statm") as fh:
            return int(fh.read().split()[1]) * os.sysconf("SC_PAGE_SIZE") / 2 ** 20
    except (OSError, ValueError, AttributeError):
        pass
    try:
        import psutil
        return psutil.Process().memory_info().rss / 2 ** 20
    except ImportError:
        return float("nan")


g = App.Game()
feria.ACTIVO = True          # (la pantalla de atracción solo sale con el modo feria; no se guarda)
g.demo_permitida = True
filas = []
partida, cuadros, en_partida = 0, [], False
reloj = pygame.time.Clock()
inicio = time.time()
while partida < PARTIDAS:
    a = time.perf_counter()
    g._cuadro_seguro(16)
    ms = (time.perf_counter() - a) * 1000
    if os.environ.get("NEXUS_VENTANA"):
        reloj.tick(60)
    jugando = g.demo is not None and g.current_screen == "partida"
    if jugando:
        cuadros.append(ms)
    if en_partida and not jugando and g.current_screen in ("ranking", "menu"):
        partida += 1
        gc.collect()
        c = sorted(cuadros) or [0]
        fila = (partida, memoria_mb(), len(gc.get_objects()), statistics.mean(c), c[int(len(c) * 0.99) - 1],
                c[-1], len(c), getattr(g.mision, "fase", None))
        filas.append(fila)
        print(f"partida {fila[0]:2d}: memoria {fila[1]:7.1f} MB · objetos {fila[2]:7d} · cuadro medio "
              f"{fila[3]:5.2f} ms, p99 {fila[4]:5.2f}, peor {fila[5]:6.1f} ({fila[6]} cuadros) · llegó a {fila[7]}",
              flush=True)
        cuadros = []
    en_partida = jugando

print(f"\n{PARTIDAS} partidas en {time.time() - inicio:.0f} s")
if len(filas) >= 4:
    # Desde la segunda (la primera carga todo por primera vez).
    m0, m1 = filas[1][1], filas[-1][1]
    o0, o1 = filas[1][2], filas[-1][2]
    t0, t1 = statistics.mean(f[3] for f in filas[1:3]), statistics.mean(f[3] for f in filas[-2:])
    print(f"memoria: {m0:.0f} -> {m1:.0f} MB ({(m1 - m0) / max(1, len(filas) - 2):+.1f} MB por partida)")
    print(f"objetos: {o0} -> {o1} ({(o1 - o0) / max(1, len(filas) - 2):+.0f} por partida)")
    print(f"cuadro medio: {t0:.2f} -> {t1:.2f} ms")
    crece = (m1 - m0) / max(1, len(filas) - 2) > 15 or t1 > t0 * 1.3
    print("ALGO CRECE: revisar" if crece else "OK: ni la memoria ni los cuadros crecen partida tras partida")
