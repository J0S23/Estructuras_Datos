"""La predicción del cliente (cliente_servidor/prediccion.py) con una red lenta.

    python pruebas/prueba_red_prediccion.py

Entre el cliente y el servidor va un proxy que retrasa RETRASO_S cada mensaje
en cada sentido (como el wifi entre dos laptops). Comprueba:

1. Con predicción, el jugador se mueve en pantalla en el mismo cuadro en que
   se presiona la tecla; sin ella (F4), recién cuando vuelve la instantánea.
2. Al soltar la tecla, el jugador de la pantalla queda donde lo dejó el
   servidor (a pocos px), y lo mismo después de caminar contra una pared.
3. Si el servidor lo mueve de golpe (lo atraparon, salió de un escondite),
   la predicción salta a donde dice el servidor.
4. El F3 de la red se dibuja y mide la respuesta (~2 x RETRASO_S).

Tarda ~40 s.
"""

import os
import socket
import subprocess
import sys
import threading
import time

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

import pygame

from cliente_servidor import cliente

RETRASO_S = 0.06


class Proxy:
    """Proxy TCP que retrasa cada línea RETRASO_S en los dos sentidos (en orden)."""

    def __init__(self, puerto_servidor):
        self.destino = puerto_servidor
        self.sock = socket.socket()
        self.sock.bind(("127.0.0.1", 0))
        self.sock.listen(8)
        self.puerto = self.sock.getsockname()[1]
        threading.Thread(target=self._aceptar, daemon=True).start()

    def _aceptar(self):
        while True:
            try:
                c, _ = self.sock.accept()
            except OSError:
                return
            s = socket.create_connection(("127.0.0.1", self.destino))
            for a, b in ((c, s), (s, c)):
                threading.Thread(target=self._pasar, args=(a, b), daemon=True).start()

    @staticmethod
    def _pasar(desde, hacia):
        cola = []
        hay = threading.Condition()

        def entregar():
            while True:
                with hay:
                    while not cola:
                        hay.wait()
                    t, datos = cola.pop(0)
                espera = t - time.perf_counter()
                if espera > 0:
                    time.sleep(espera)
                if datos is None:
                    return
                try:
                    hacia.sendall(datos)
                except OSError:
                    return

        threading.Thread(target=entregar, daemon=True).start()
        try:
            while True:
                datos = desde.recv(65536)
                with hay:
                    cola.append((time.perf_counter() + RETRASO_S, datos or None))
                    hay.notify()
                if not datos:
                    return
        except OSError:
            with hay:
                cola.append((time.perf_counter(), None))
                hay.notify()


proceso = subprocess.Popen(
    [sys.executable, "-u", "-m", "cliente_servidor.servidor", "--puerto", "0", "--mapa", "Nave",
     "--jugadores", "2", "--sin-presentaciones", "--aliens-quietos", "--segundos", "60", "--espera", "5"],
    cwd=RAIZ, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
try:
    puerto = None
    while puerto is None:
        linea = proceso.stdout.readline()
        assert linea, "el servidor no arrancó"
        if "escuchando en" in linea:
            puerto = int(linea.split("escuchando en ")[1].split()[0].rsplit(":", 1)[1])
    threading.Thread(target=lambda: [None for _ in proceso.stdout], daemon=True).start()
    proxy = Proxy(puerto)

    pygame.init()
    from juego.app import Game
    mantener = [set(), set()]
    s = cliente.Sesion(Game(), "127.0.0.1", proxy.puerto, cliente.esquemas_para(2), avisar=lambda t: None)
    s.conectar()
    s.entrada.sacar = lambda: [(set(m), []) for m in mantener]
    s.preparar_espejo()
    pantalla = pygame.Surface((1280, 720))

    def cuadro():
        s.paso(pantalla, eventos=[])
        time.sleep(1 / 60)

    def correr(segundos):
        fin = time.time() + segundos
        while time.time() < fin:
            cuadro()

    correr(3)
    assert s.espejo is not None and s.espejo.listo and s.error_dibujo is None, s.error_dibujo
    g = s.espejo.g
    j1 = g.jugadores[0]

    def servidor_x():
        return s.conexiones[0].ultimo_estado()["j0"]["x"]

    def servidor_y():
        return s.conexiones[0].ultimo_estado()["j0"]["y"]

    def tarda_en_moverse(direccion, con_prediccion):
        """Cuadros (y ms) desde presionar hasta que el J1 de la pantalla se mueve."""
        s.prediccion = con_prediccion
        mantener[0].clear()
        correr(0.8)
        x0, y0 = j1.personaje.x, j1.personaje.y
        mantener[0].add(direccion)
        inicio = time.perf_counter()
        for n in range(1, 120):
            cuadro()
            if abs(j1.personaje.x - x0) + abs(j1.personaje.y - y0) > 0.5:
                mantener[0].clear()
                return n, (time.perf_counter() - inicio) * 1000
        mantener[0].clear()
        return None, None

    # 1. La tecla mueve al instante con predicción, y tarde sin ella.
    n_sin, ms_sin = tarda_en_moverse("derecha", False)
    n_con, ms_con = tarda_en_moverse("izquierda", True)
    print(f"sin predicción se movió en el cuadro {n_sin} ({ms_sin:.0f} ms); "
          f"con predicción en el {n_con} ({ms_con:.0f} ms)")
    assert n_con == 1, "con predicción tiene que moverse en el mismo cuadro"
    assert n_sin is not None and ms_sin > 2 * RETRASO_S * 1000 * 0.8, "sin predicción espera la red"

    # 2. Caminar, soltar y ver que queda donde dice el servidor.
    def caminar_y_comparar(acciones, segundos, nombre):
        mantener[0].clear()
        mantener[0].update(acciones)
        peor = 0.0
        fin = time.time() + segundos
        while time.time() < fin:
            cuadro()
            pred = s.predicciones.get(0)
            if pred is not None and pred.activa:
                peor = max(peor, pred.ultimo_error)
        mantener[0].clear()
        correr(0.8)
        d = abs(j1.personaje.x - servidor_x()) + abs(j1.personaje.y - servidor_y())
        print(f"  {nombre}: al soltar queda a {d:.1f} px del servidor (peor diferencia caminando "
              f"{peor:.1f} px)")
        assert d < 4, f"{nombre}: quedó a {d:.1f} px de donde dice el servidor"
        return peor

    s.prediccion = True
    caminar_y_comparar({"derecha"}, 1.5, "derecha")
    caminar_y_comparar({"abajo", "izquierda"}, 1.5, "diagonal")
    caminar_y_comparar({"arriba", "sigilo"}, 1.5, "sigilo")
    caminar_y_comparar({"arriba"}, 4.0, "contra la pared")
    caminar_y_comparar({"izquierda"}, 4.0, "contra otra pared")

    # 3. El servidor lo mueve de golpe: la predicción salta.
    pred = s.predicciones[0]
    saltos = pred.saltos
    # (como si el cliente lo creyera 500 px corrido de donde lo tiene el servidor)
    pred.pos = (pred.pos[0] + 500, pred.pos[1])
    pred.historia.clear()
    pred.historia.append([time.perf_counter() - 1, pred.pos[0], pred.pos[1]])
    correr(0.5)
    assert pred.saltos > saltos, "una diferencia grande con el servidor tiene que saltar"
    d = abs(j1.personaje.x - servidor_x())
    assert d < 4, f"después del salto quedó a {d:.1f} px del servidor"
    print(f"  salto: {pred.saltos - saltos} (vuelve a donde dice el servidor)")

    # 4. F3.
    s.f3 = True
    correr(1.5)
    c = s.conexiones[0]
    inst, hz = s.medidas.ritmo(c)
    print(f"F3: respuesta {c.respuesta_ms:.0f} ms, {inst:.0f} instantáneas/s, servidor {hz:.0f} cuadros/s, "
          f"{s.medidas.fps():.0f} FPS")
    assert c.respuesta_ms > 2 * RETRASO_S * 1000 * 0.8, "la respuesta tiene que incluir el retraso"
    assert 20 <= inst <= 40 and 45 <= hz <= 70, (inst, hz)
    pygame.image.save(pantalla, os.path.join(os.environ.get("NEXUS_CAPTURAS", "/tmp"), "red_f3.png"))
    assert s.error_dibujo is None, s.error_dibujo
    s.cerrar()
    print("\nOK prueba_red_prediccion")
finally:
    proceso.terminate()
