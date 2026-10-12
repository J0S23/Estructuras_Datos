"""Prueba de los mandos (jugadores 3 y 4) sin un mando de verdad.

    python pruebas/prueba_mandos.py

Se inyecta un mando falso que dice qué botones están presionados y se
mandan eventos como los que manda pygame. Para probar el control real:
python pruebas/probar_mando.py.
"""

import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
import pygame; pygame.init()
OUT = os.path.join(RAIZ, "pruebas", "capturas")

import App
import objetos_mapa
import mandos as M
objetos_mapa.mapa_activo = lambda: "Nave"
DT = 1000 // 60
NOMBRES = [r["nombre"] for r in App.ROLES]


class MandoFalso:
    def __init__(self, ident):
        self.ident = ident
        self.botones, self.ejes, self.cruceta = set(), [0.0] * 6, (0, 0)
    def init(self): pass
    def get_instance_id(self): return self.ident
    def get_name(self): return "Mando falso"
    def get_button(self, b): return b in self.botones
    def get_axis(self, a): return self.ejes[a]
    def get_numaxes(self): return 6
    def get_numhats(self): return 1
    def get_hat(self, i): return self.cruceta


class Teclas(dict):
    def __getitem__(self, k):
        return self.get(k, False)


pygame.key.get_pressed = lambda: Teclas()
mando = MandoFalso(77)
mando.ejes[M.EJE_LT] = -1.0


def boton(nombre):
    return pygame.event.Event(pygame.JOYBUTTONDOWN, instance_id=77, button=M.BOTONES[nombre], joy=0)


g = App.Game()
g.mandos.por_puesto = {2: mando}

# Menú y cantidad con la cruceta y A.
g.current_screen = "cantidad"
antes = g.cantidad_seleccionada
pygame.event.post(pygame.event.Event(pygame.JOYHATMOTION, instance_id=77, value=(0, -1), hat=0, joy=0))
g._manejar_eventos()
assert g.cantidad_seleccionada != antes, "la cruceta mueve la selección en los menús"
print("menús: la cruceta del mando elige")

# Partida de 3: el jugador 3 tiene mando.
def avanzar():
    for _ in range(80):
        if g.transitions.is_idle(): break
        g.transitions.update(g, 33)


g.cantidad_jugadores = 3
g.abrir_seleccion_roles()
avanzar()
assert g.seleccion_roles[2]["tecla_ok"] == "A" and g.seleccion_roles[2]["tecla_mover"] == "Stick"
for i, e in enumerate(g.seleccion_roles[:2]):
    e["listo"], e["rol"] = True, NOMBRES[i]
g.current_screen = "roles"
g.seleccion_roles[2]["cursor"] = 2
pygame.event.post(boton("A"))
g._manejar_eventos()
assert g.current_screen != "roles" or g.seleccion_roles[2]["listo"], "A confirma el rol"
avanzar()
g.current_screen = "partida"
j3 = g.jugadores[2]
assert j3.con_mando and j3.puede_moverse and j3.nombre_tecla("interactuar") == "A"
assert not g.jugadores[2 - 1].con_mando
g.tutorial.activo = False; g._terminar_tutorial()
for a in g.aliens:
    a.descanso_ms = 10 ** 9
print("selección: el mando escoge rol; el jugador 3 se puede mover")

# Moverse con el stick, y en sigilo con LB.
x0 = j3.hitbox.x
mando.ejes[M.EJE_X] = 1.0
for _ in range(20):
    g._actualizar_partida(DT)
normal = j3.hitbox.x - x0
mando.botones.add(M.BOTONES["LB"])
x0 = j3.hitbox.x
for _ in range(20):
    g._actualizar_partida(DT)
lento = j3.hitbox.x - x0
mando.ejes[M.EJE_X] = 0.0
mando.botones.clear()
assert normal > 0 and 0 < lento < normal, (normal, lento)
print(f"stick: avanza {normal}px; con LB (sigilo) {lento}px")

# Cruceta también mueve.
y0 = j3.hitbox.y
mando.cruceta = (0, 1)
for _ in range(15):
    g._actualizar_partida(DT)
mando.cruceta = (0, 0)
assert j3.hitbox.y < y0
print("cruceta: mueve hacia arriba")

# Y abre el árbol; B lo cierra.
pygame.event.post(boton("Y"))
g._manejar_eventos()
assert j3.panel is not None and j3.panel.get("tipo") == "habilidades"
pygame.event.post(boton("B"))
g._manejar_eventos()
assert j3.panel is None
print("Y abre el árbol de habilidades, B lo cierra")

# Mantener A cuenta como mantener la tecla de interactuar.
mando.botones.add(M.BOTONES["A"])
teclas = g.mandos.envolver(Teclas())
assert any(teclas[k] for k in j3.teclas["interactuar"])
mando.botones.clear()

g._dibujar()
pygame.image.save(g.screen, os.path.join(OUT, "mandos_partida.png"))

# Sin mando, el jugador 4 sigue quieto, y si se desconecta el del 3, también.
g.mandos.por_puesto = {}
g._sincronizar_mandos()
assert not j3.puede_moverse
print("desconectado: el jugador 3 deja de moverse")
print("\nTODO OK")
