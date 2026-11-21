"""Menos lag con ping alto: la interpolación que se adapta y el eco local.

    python pruebas/prueba_red_eco.py

1. La interpolación (cliente_servidor/interpolacion.py) con ping y jitter
   simulados (reloj falso): con 50 ms fijos, con ~30 ms de jitter los demás se
   quedaban quietos y saltaban en muchos cuadros; ahora el retraso sube lo que
   hace falta y casi nunca se queda sin instantánea. Sin jitter se queda en
   50 ms. Una instantánea más rápida que todas no hace saltar lo dibujado.
2. El eco (cliente_servidor/eco.py), sin sockets como prueba_red_minijuegos:
   en los cables, la flecha y el giro se ven en el cliente en el mismo cuadro;
   las instantáneas que todavía no lo incluyen no lo deshacen; cuando el
   servidor lo usó (ack) queda igual que en el servidor, sin contarlo dos
   veces.
3. Lo que no se adivina espera al servidor: soltar el abono, la ronda nueva
   de la señal.
4. El cursor de los menús también va con eco (no el cambio de pestaña del
   celular, que lo arma el servidor).
"""

import json
import os
import random
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["NEXUS_SIN_EFECTOS"] = "1"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

import pygame

from cliente_servidor import estado as E
from cliente_servidor import interpolacion as I
from cliente_servidor.eco import Eco
from cliente_servidor.servidor import Servidor, Teclas
from cliente_servidor.espejo import Espejo
from cliente_servidor.protocolo import Reconstructor, comprimir


# -- 1. La interpolación ---------------------------------------------------------------------
def simular(ping_ms, jitter_ms, adaptar, segundos=30, semilla=1):
    """(% de cuadros quieto, error de velocidad p99, retraso medio en ms) de
    algo que se mueve parejo a 3 px por cuadro, visto a 60 por segundo."""
    rnd = random.Random(semilla)
    reloj = [0.0]
    it = I.Interpolador(reloj=lambda: reloj[0], adaptar=adaptar)
    llegadas, ultimo = [], 0.0
    for c in range(0, segundos * 60, 2):
        t = 5 + c / 60 + ping_ms / 1000 + (rnd.expovariate(1000 / jitter_ms) if jitter_ms else 0)
        ultimo = max(ultimo, t)          # (TCP: en orden)
        llegadas.append((ultimo, c))
    k, previo, errores, quietos, retrasos = 0, None, [], 0, []
    t = 5.0
    while t < 5 + segundos:
        while k < len(llegadas) and llegadas[k][0] <= t:
            it.agregar(llegadas[k][1], {"j0": {"x": 3.0 * llegadas[k][1], "y": 0.0}}, llegadas[k][0])
            k += 1
        p = it.ahora(t).get("j0")
        if p and t > 8:
            if previo is not None:
                errores.append(abs((p[0] - previo) - 3.0))
                quietos += abs(p[0] - previo) < 0.01
            retrasos.append(it.retraso * 1000)
        if p:
            previo = p[0]
        t += 1 / 60
    errores.sort()
    return 100 * quietos / len(errores), errores[int(len(errores) * 0.99)], sum(retrasos) / len(retrasos)


q_fijo, e_fijo, _ = simular(80, 30, adaptar=False)
q, e, r = simular(80, 30, adaptar=True)
assert q_fijo > 5, f"(la prueba no prueba nada: con 50 ms fijos ya iba bien, {q_fijo:.1f} %)"
assert q < 1 and e < 1, f"con jitter todavía se congela: {q:.1f} % quieto, error p99 {e:.2f} px"
assert 80 < r < I.RETRASO_MAX_MS, f"el retraso no se adaptó: {r:.0f} ms"
q0, e0, r0 = simular(0, 0, adaptar=True)
assert q0 == 0 and e0 < 0.01 and abs(r0 - I.RETRASO_MS) < 1, (q0, e0, r0)
q1, e1, r1 = simular(20, 3, adaptar=True)
assert q1 == 0 and r1 < 70, f"con buen wifi el retraso tiene que quedar chico ({r1:.0f} ms)"
print(f"1. interpolación con 80 ms de ping y ~30 de jitter: quieto {q_fijo:.1f} % -> {q:.1f} % de los "
      f"cuadros (retraso ~{r:.0f} ms); sin jitter queda en {r0:.0f} ms: OK")

# Una más rápida que todas: lo dibujado no salta hacia adelante.
reloj = [0.0]
it = I.Interpolador(reloj=lambda: reloj[0])
for c in range(0, 60, 2):
    it.agregar(c, {"j0": {"x": 3.0 * c, "y": 0}}, 1 + c / 60 + 0.08)
reloj[0] = 1 + 60 / 60 + 0.08
antes = it.ahora()["j0"][0]
it.agregar(60, {"j0": {"x": 180.0, "y": 0}}, 1 + 60 / 60 + 0.02)    # 60 ms antes de lo normal
reloj[0] += 1 / 60
despues = it.ahora()["j0"][0]
assert 0 < despues - antes < 6, f"saltó {despues - antes:.1f} px en un cuadro"
print("   una instantánea más rápida que las demás no hace saltar lo que se dibuja: OK")


# -- 2. El eco de los minijuegos -----------------------------------------------------------
class Red:
    def __init__(self, servidor):
        self.s = servidor
        self.r = Reconstructor()
        self.anterior = None
        self.cuadro = 0

    def mandar(self):
        ahora = self.s.instantanea()
        self.cuadro += 2
        if self.anterior is None:
            m = {"tipo": "estado", "c": self.cuadro, "base": None, "z": comprimir(ahora)}
        else:
            cambios = {}
            for seccion, datos in ahora.items():
                d = E.diferencias(self.anterior.get(seccion, {}), datos)
                if d:
                    cambios[seccion] = d
            m = {"tipo": "estado", "c": self.cuadro, "base": self.cuadro - 2, "s": cambios}
        self.anterior = ahora
        return self.r.aplicar(json.loads(json.dumps(m)))


pygame.init()
s = Servidor(2, avisar=lambda t: None, semilla=5, presentaciones=False, aliens_quietos=True,
             roles=["Tecnomante", "Forjador"])
s.preparar_partida()
s.lista.set()
for p in s.puestos:
    p.ocupado = True
g = s.juego
g.admin_invencible = True
g.quitar_cambiaformas()
if g.eventos is not None:
    g.eventos.reloj_ms = 10 ** 9
g.nexus.reloj_rumor_ms = g.nexus.reloj_normal_ms = 10 ** 9
for a in g.aliens:
    a.hitbox.topleft = (5, 5)
s.teclas = Teclas()

from juego.app import Game
from juego import tareas
from misiones import minijuegos
from redes import celular
from entidades.jugador import WASD, FLECHAS
espejo = Espejo(Game(), s.bienvenida(s.puestos[0]))
espejo.preparar()
espejo.controles({0: WASD, 1: FLECHAS})
canal = Red(s)
m = espejo.g
eco = Eco()
n = [0]
acks = [-1, -1]


def sincronizar():
    """Una instantánea llega al cliente (con los acks que tenía el servidor)."""
    secciones = canal.mandar()
    espejo.aplicar(secciones)
    eco.reaplicar(m, espejo.completos, list(acks))


def presionar(accion):
    """El cliente presiona: manda la intención (todavía no llega) y hace el eco."""
    n[0] += 1
    eco.presionar(m, 0, accion, n[0])
    return n[0], accion


def llega(*intenciones):
    """Las intenciones llegan al servidor (Servidor._aplicar_entradas)."""
    b = s.buzones[0]
    with b.candado:
        for k, accion in intenciones:
            b.pulsar.append(accion)
            b.ultimo_n = k
    acks[:] = s._aplicar_entradas()
    g._actualizar_partida(16)


j1, c1 = g.jugadores[0], m.jugadores[0]
sincronizar()
mini = tareas.empezar(g, j1, "cables", None)
g._actualizar_partida(16)
sincronizar()
otro = tareas.de(c1)
assert isinstance(otro, minijuegos.Cables) and otro.cursor == mini.cursor
cursor0 = list(mini.cursor)
a = presionar("derecha")
assert otro.cursor[0] == cursor0[0] + 1, "la flecha no se vio en el mismo cuadro"
assert mini.cursor == cursor0, "(el servidor todavía no la vio)"
sincronizar()                       # llega una que todavía no la incluye
otro = tareas.de(c1)
assert otro.cursor[0] == cursor0[0] + 1, "la instantánea vieja deshizo la flecha"
b = presionar("interactuar")
celda = tuple(otro.cursor)
rot_esperada = (mini.rot[celda] + 1) % 4
assert otro.rot[celda] == rot_esperada, "el giro no se vio en el mismo cuadro"
sincronizar()
assert tareas.de(c1).rot[celda] == rot_esperada and tareas.de(c1).cursor[0] == cursor0[0] + 1
llega(a)                            # el servidor ya vio la flecha, el giro todavía no
sincronizar()
otro = tareas.de(c1)
assert mini.cursor[0] == cursor0[0] + 1 and otro.cursor == mini.cursor, "la flecha quedó contada dos veces"
assert otro.rot[celda] == rot_esperada, "el giro (todavía sin ack) se perdió"
llega(b)
sincronizar()
otro = tareas.de(c1)
assert otro.rot[celda] == mini.rot[celda] == rot_esperada, "el giro quedó contado dos veces"
assert not eco.anotadas, eco.anotadas
print("2. cables: la flecha y el giro se ven al instante; las instantáneas viejas no los deshacen "
      "y con el ack quedan como en el servidor (sin contarlos dos veces): OK")

# -- 3. Lo que no se adivina ---------------------------------------------------------------------
j1.cerrar_panel()
mini = tareas.empezar(g, j1, "abono", None)
g._actualizar_partida(16)
sincronizar()
otro = tareas.de(c1)
k = presionar("interactuar")
assert otro.caida is None and not eco.anotadas, "soltar el abono se adivinó (lo juzga el servidor)"
llega(k)
sincronizar()
assert tareas.de(c1).caida is not None, "el abono no se soltó al llegar al servidor"
j1.cerrar_panel()
mini = tareas.empezar(g, j1, "senal", None, facil=False)
mini.rondas = 2
mini.f, mini.a = mini.objetivo
g._actualizar_partida(16)
sincronizar()
otro = tareas.de(c1)
k = presionar("interactuar")
assert otro.ronda == 0 and not eco.anotadas, "la ronda nueva de la señal (sale al azar) se adivinó"
llega(k)
sincronizar()
assert tareas.de(c1).ronda == 1 and tareas.de(c1).objetivo == mini.objetivo
k = presionar("izquierda")
assert tareas.de(c1).f == mini.f - 1 or mini.f == 1, "la frecuencia no se movió al instante"
llega(k)
sincronizar()
assert tareas.de(c1).f == mini.f
j1.cerrar_panel()
print("3. soltar el abono y la ronda nueva de la señal esperan al servidor; la frecuencia va con eco: OK")

# -- 4. El cursor de un menú (el celular, la terminal NEXUS, soltar...) --------------------------
j1.abrir_panel({"titulo": "Soltar", "accion": "soltar",
                "opciones": [{"texto": t} for t in ("Uno", "Dos", "Tres", "Cuatro")]})
j1.cursor = 0
g._actualizar_partida(16)
sincronizar()
assert c1.panel is not None and len(c1.panel.get("opciones", [])) == 4 and c1.cursor == 0
k1 = presionar("abajo")
k2 = presionar("abajo")
assert c1.cursor == 2, f"el cursor no bajó al instante ({c1.cursor})"
sincronizar()
assert c1.cursor == 2, "la instantánea vieja subió el cursor"
llega(k1)
sincronizar()
assert j1.cursor == 1 and c1.cursor == 2
llega(k2)
sincronizar()
assert j1.cursor == c1.cursor == 2 and not eco.anotadas
j1.cerrar_panel()
g._actualizar_partida(16)
sincronizar()
# En el celular, izquierda/derecha cambian de pestaña: eso lo arma el servidor.
celular.abrir(g, j1)
g._actualizar_partida(16)
sincronizar()
assert c1.panel is not None and c1.panel.get("tipo") == "celular"
presionar("derecha")
assert not eco.anotadas, "el cambio de pestaña se adivinó"
print("4. el cursor de un menú baja al instante y queda igual que en el servidor; "
      "la pestaña del celular espera al servidor: OK")

print("OK prueba_red_eco")
