"""Las transiciones del modo local también en red (cliente.Sesion).

    python pruebas/prueba_red_transiciones.py

Con "Efectos visuales: Sí", como en el juego local (juego/transition_manager.py):
1. Al llegar la primera instantánea, la pantalla de espera se va con el
   GLITCH (franjas corridas, cian y magenta) y entra la partida. Antes se
   pasaba de golpe.
2. Al terminar, el DESTELLO (escaparon) sobre la partida y entran los
   resultados (o el iris si perdieron). Mientras sale, Enter no hace nada.
3. Sin efectos, nada de esto (las pruebas que comparan píxeles los apagan).

Dos servidores de verdad (otros procesos); una laptop con los dos jugadores.
Tarda ~20 s. Capturas en pruebas/capturas/red_transicion_*.png.
"""

import os
import subprocess
import sys
import time

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ.pop("NEXUS_SIN_EFECTOS", None)
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

import pygame

from cliente_servidor import cliente
from entidades.jugador import WASD, FLECHAS
from juego import efectos

OUT = os.environ.get("NEXUS_CAPTURAS") or os.path.join(RAIZ, "pruebas", "capturas")
os.makedirs(OUT, exist_ok=True)


def servidor(*extra):
    proceso = subprocess.Popen(
        [sys.executable, "-u", "-m", "cliente_servidor.servidor", "--puerto", "0", "--mapa", "Nave",
         "--jugadores", "2", "--roles", "Tecnomante,Forjador", "--sin-presentaciones", "--aliens-quietos",
         "--segundos", "60", "--espera", "20", *extra],
        cwd=RAIZ, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    while True:
        linea = proceso.stdout.readline()
        assert linea, "el servidor no arrancó"
        if "escuchando en" in linea:
            puerto = int(linea.split("escuchando en ")[1].split()[0].rsplit(":", 1)[1])
            break
    import threading
    threading.Thread(target=lambda: [None for _ in proceso.stdout], daemon=True).start()
    return proceso, puerto


pygame.init()
from juego.app import Game


def sesion(puerto):
    s = cliente.Sesion(Game(), "127.0.0.1", puerto, [WASD, FLECHAS], avisar=lambda t: None)
    s.conectar()
    s.entrada.sacar = lambda: [(set(), []), (set(), [])]
    s.preparar_espejo()
    return s


def jugar(s, pantalla, segundos, cada=None, hasta=None, eventos=()):
    fin = time.time() + segundos
    while time.time() < fin:
        s.paso(pantalla, eventos=list(eventos))
        if cada is not None:
            cada()
        if hasta is not None and hasta():
            return True
        time.sleep(1 / 60)
    return hasta is None


procesos = []
try:
    # -- 1. El glitch al entrar ------------------------------------------------------------
    efectos.ACTIVOS = True
    proceso, puerto = servidor()
    procesos.append(proceso)
    s = sesion(puerto)
    pantalla = pygame.Surface((1280, 720))
    vistos = []

    def anotar():
        t = s.transicion
        vistos.append(None if t is None else (t._estilo, t._phase))
        # (a la mitad de la entrada: al principio está negra del todo)
        if (t is not None and t._phase == "fade_in" and t._elapsed > 200
                and not os.path.exists(captura)):
            pygame.image.save(pantalla, captura)

    captura = os.path.join(OUT, "red_transicion_glitch.png")
    if os.path.exists(captura):
        os.remove(captura)
    assert jugar(s, pantalla, 15, anotar, hasta=lambda: s._entro and s.transicion is None
                 and len(vistos) > 5), "la partida no empezó"
    assert ("glitch", "fade_out") in vistos, f"no salió la espera con el glitch: {set(vistos)}"
    assert ("glitch", "fade_in") in vistos, "la partida no entró con el glitch"
    assert vistos.index(("glitch", "fade_out")) < vistos.index(("glitch", "fade_in"))
    assert s.error_dibujo is None, s.error_dibujo
    print(f"1. al entrar a la partida en red, el glitch ({vistos.count(('glitch', 'fade_out'))} cuadros "
          f"saliendo, {vistos.count(('glitch', 'fade_in'))} entrando): OK")
    s.cerrar()
    proceso.terminate()

    # -- 2. El destello al escapar --------------------------------------------------------------
    proceso, puerto = servidor("--fase-final")
    procesos.append(proceso)
    s = sesion(puerto)
    vistos.clear()
    captura = os.path.join(OUT, "red_transicion_destello.png")
    if os.path.exists(captura):
        os.remove(captura)
    enter = [pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, mod=0, unicode="\r", scancode=0)]

    def cuando_sale():
        t = s.transicion
        return t is not None and t._estilo == "destello" and t._phase == "fade_out"
    assert jugar(s, pantalla, 20, anotar, hasta=cuando_sale), f"no salió el destello: {set(vistos)}"
    # Mientras la partida se va, Enter no saca de los resultados.
    s.paso(pantalla, eventos=enter)
    assert s.motivo is None, "Enter durante el destello terminó la sesión"
    assert jugar(s, pantalla, 5, anotar, hasta=lambda: s.transicion is None)
    assert ("destello", "fade_in") in vistos, "los resultados no entraron con el destello"
    pygame.image.save(pantalla, os.path.join(OUT, "red_transicion_resultados.png"))
    print("2. al escapar en red, el destello y después los resultados: OK")
    s.cerrar()
    proceso.terminate()

    # -- 3. Sin efectos, nada -----------------------------------------------------------------------
    efectos.ACTIVOS = False
    proceso, puerto = servidor()
    procesos.append(proceso)
    s = sesion(puerto)
    vistos.clear()
    assert jugar(s, pantalla, 15, anotar, hasta=lambda: s._entro and len(vistos) > 30)
    assert all(v is None for v in vistos), set(vistos)
    print("3. sin efectos visuales, sin transiciones (como antes): OK")
    s.cerrar()
finally:
    for p in procesos:
        p.terminate()

print("OK prueba_red_transiciones")
