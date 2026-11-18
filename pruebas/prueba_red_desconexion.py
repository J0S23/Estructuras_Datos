"""Alguien pierde la conexión en red (cliente_servidor/ausencias.py).

    python pruebas/prueba_red_desconexion.py

Dos "laptops" (dos sesiones), J1 = Tecnomante y J2 = Forjador:
1. Corte corto (el wifi se va un segundo y el cliente vuelve solo con su
   token): J1 sale "sin conexión", no suelta nada y vuelve a moverse.
2. J1 cierra el juego y no vuelve: en GRACIA_S suelta sus cosas (el
   decodificador del Tecnomante cae al piso), deja de contar, y a J2 le
   llega el aviso ("perdió la conexión", "se desconectó").
3. J1 vuelve (otro cliente, sin token, desde la misma IP): toma su puesto,
   se mueve otra vez y a J2 le avisan que volvió; el decodificador sigue en
   el piso.

Tarda ~40 s.
"""

import os
import subprocess
import sys
import time

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

import pygame

from cliente_servidor import cliente, ausencias
from entidades.jugador import WASD, FLECHAS

proceso = subprocess.Popen(
    [sys.executable, "-u", "-m", "cliente_servidor.servidor", "--puerto", "0", "--mapa", "Nave",
     "--jugadores", "2", "--roles", "Tecnomante,Forjador", "--sin-presentaciones", "--aliens-quietos",
     "--segundos", "120", "--espera", "30"],
    cwd=RAIZ, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
consola = []
try:
    puerto = None
    while puerto is None:
        linea = proceso.stdout.readline()
        assert linea, "el servidor no arrancó"
        if "escuchando en" in linea:
            puerto = int(linea.split("escuchando en ")[1].split()[0].rsplit(":", 1)[1])
    import threading
    threading.Thread(target=lambda: [consola.append(l.strip()) for l in proceso.stdout], daemon=True).start()

    pygame.init()
    from juego.app import Game

    def laptop(esquema, mantener):
        s = cliente.Sesion(Game(), "127.0.0.1", puerto, [esquema], avisar=lambda t: None)
        s.conectar()
        s.entrada.sacar = lambda: [(set(mantener), [])]
        return s

    quieto_a, quieto_b = [], []
    a = laptop(WASD, quieto_a)
    b = laptop(FLECHAS, quieto_b)
    for s in (a, b):
        s.preparar_espejo()
    pantallas = {a: pygame.Surface((960, 540)), b: pygame.Surface((960, 540))}

    def correr(sesiones, segundos, hasta=None):
        fin = time.time() + segundos
        while time.time() < fin:
            for s in sesiones:
                s.paso(pantallas.get(s) or pygame.Surface((960, 540)), eventos=[])
            if hasta is not None and hasta():
                return True
            time.sleep(1 / 60)
        return hasta is None

    correr([a, b], 3)
    gb = b.espejo.g
    j1_en_b = gb.jugadores[0]
    assert j1_en_b.rol == "Tecnomante", j1_en_b.rol
    assert not j1_en_b.sin_conexion and j1_en_b.puede_moverse

    def decodificadores():
        return [c for c in gb.mision.consumibles if c["tipo"] == "decodificador" and not c["tomado"]]

    antes = len(decodificadores())

    # 1. Corte corto: vuelve solo.
    c = a.conexiones[0]
    c.cortar()
    assert correr([a, b], 5, hasta=lambda: c.reconexiones >= 1 and c.situacion == "jugando"), \
        "el cliente vuelve solo"
    correr([a, b], 1.0)
    # (si volvió entre dos cuadros del servidor, ni se nota: no hace falta aviso)
    assert not j1_en_b.sin_conexion and not j1_en_b.desconectado and j1_en_b.puede_moverse, \
        "después de un corte corto sigue igual"
    assert len(decodificadores()) == antes, "un corte corto no suelta nada"
    quieto_a[:] = ["derecha"]
    x0 = j1_en_b.personaje.x
    correr([a, b], 1.0)
    quieto_a[:] = []
    assert j1_en_b.personaje.x > x0 + 20, "después del corte se sigue moviendo"
    print("1. corte corto: vuelve y no suelta nada: OK")

    # 2. Se va del todo.
    a.cerrar()
    assert correr([b], 3, hasta=lambda: j1_en_b.sin_conexion), "J2 ve que J1 perdió la conexión"
    assert not j1_en_b.puede_moverse
    assert "perdió la conexión" in gb.jugadores[1].mensaje, gb.jugadores[1].mensaje
    pygame.image.save(pantallas[b], os.path.join(os.environ.get("NEXUS_CAPTURAS", "/tmp"),
                                                 "red_sin_conexion.png"))
    assert not j1_en_b.desconectado, "todavía está en la gracia"
    assert correr([b], ausencias.GRACIA_S + 4, hasta=lambda: j1_en_b.desconectado), \
        "a los GRACIA_S se da por desconectado"
    correr([b], 0.5)
    tirados = decodificadores()
    assert len(tirados) > antes, "el Tecnomante soltó un decodificador"
    cerca = min(abs(d["rect"].centerx - j1_en_b.hitbox.centerx) + abs(d["rect"].centery - j1_en_b.hitbox.centery)
                for d in tirados)
    assert cerca < 200, f"el decodificador cayó donde estaba ({cerca} px)"
    texto = gb.jugadores[1].mensaje
    assert "dejó caer" in texto or "se desconectó" in texto, texto
    pygame.image.save(pantallas[b], os.path.join(os.environ.get("NEXUS_CAPTURAS", "/tmp"),
                                                 "red_desconectado.png"))
    print(f"2. se fue: soltó {len(tirados) - antes} decodificador(es), aviso \"{texto}\": OK")

    # 3. Vuelve (otro cliente, sin token).
    otra = []
    a2 = laptop(WASD, otra)
    assert a2.conexiones[0].jugador == 0, "vuelve a su puesto"
    a2.preparar_espejo()
    pantallas[a2] = pygame.Surface((960, 540))
    assert correr([a2, b], 6, hasta=lambda: not j1_en_b.desconectado and j1_en_b.puede_moverse), \
        "al volver se puede mover otra vez"
    correr([a2, b], 0.5)
    assert "volvió" in gb.jugadores[1].mensaje, gb.jugadores[1].mensaje
    assert len(decodificadores()) > antes, "lo que soltó sigue en el piso"
    otra[:] = ["abajo"]
    y0 = j1_en_b.personaje.y
    correr([a2, b], 1.0)
    assert abs(j1_en_b.personaje.y - y0) > 20, "se mueve después de volver"
    for s in (a2, b):
        assert s.error_dibujo is None, s.error_dibujo
    print("3. vuelve: se mueve, avisa y lo soltado sigue ahí: OK")
    a2.cerrar()
    b.cerrar()
    print("\nOK prueba_red_desconexion")
finally:
    proceso.terminate()
    try:
        proceso.wait(5)
    except subprocess.TimeoutExpired:
        proceso.kill()
