"""La partida se da por perdida cuando ya no se puede ganar (Mision.razon_imposible).

    python pruebas/prueba_imposible.py

En MapaFinal las dos entradas a la Bahía (donde está la cápsula) son puertas
para dos. Con 2 jugadores:
1. Los dos en pie: se puede.
2. Eliminan a uno con las puertas cerradas: ya no se llega a la cápsula. Se
   avisa a todos por qué y unos segundos después termina en derrota con
   motivo "imposible" (los resultados dicen por qué).
3. Con una de las dos puertas abierta, uno solo sí puede: no termina.
4. Sin piezas suficientes (se gastaron) también es imposible.
5. Si alguien perdió el mando (o la conexión en red) se espera mucho más
   antes de terminar, por si vuelve; y si vuelve a ser posible, se avisa.
"""

import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
import pygame; pygame.init()

from juego import app as App
from juego import objetos_mapa
from misiones import mision as M
from screens import resultados
objetos_mapa.mapa_activo = lambda: "MapaFinal"
DT = 1000 // 60


class Teclas(dict):
    def __getitem__(self, k):
        return self.get(k, False)


pygame.key.get_pressed = lambda: Teclas()


def partida():
    g = App.Game()
    g.screen = pygame.display.set_mode((1280, 720))

    def avanzar():
        for _ in range(80):
            if g.transitions.is_idle():
                break
            g.transitions.update(g, 33)
    g._activar_opcion_menu("jugar"); avanzar(); g._manejar_tecla(pygame.K_RETURN); avanzar()
    g._manejar_tecla(pygame.K_RETURN); avanzar()
    g.seleccion_roles[0]["cursor"] = 0; g._manejar_tecla(pygame.K_e)
    g.seleccion_roles[1]["cursor"] = 1; g._manejar_tecla(pygame.K_RETURN); avanzar()
    g.current_screen = "partida"
    g.saltar_tutorial()
    g.quitar_cambiaformas()
    for alien in g.aliens:
        alien.descanso_ms = 10 ** 9          # (que nadie atrape a nadie mientras tanto)
    for j in g.jugadores:
        j.invulnerable_ms = 10 ** 9
    return g


def segundos(g, s):
    for _ in range(int(s * 1000 / DT)):
        g._actualizar_partida(DT)
        if g.mision.resultado is not None:
            return


g = partida()
m = g.mision
assert len(g.puertas_dobles) >= 2 and not any(p["abierta"] for p in g.puertas_dobles)

# 1.
assert m.razon_imposible() is None
segundos(g, 2)
assert m.resultado is None
print("1. con los dos en pie se puede: OK")

# 2.
g.jugadores[1].eliminar()
razon = m.razon_imposible()
assert razon and "cápsula" in razon and "puerta para dos" in razon, razon
segundos(g, (M.ESPERA_IMPOSIBLE_MS + 500) / 1000)
assert m.resultado is None, "primero avisa"
assert "La partida termina" in g.jugadores[0].mensaje, g.jugadores[0].mensaje
segundos(g, (M.AVISO_IMPOSIBLE_MS + 1000) / 1000)
assert m.resultado == "derrota" and m.motivo_fin == "imposible", (m.resultado, m.motivo_fin)
assert resultados._motivo(m) == razon, resultados._motivo(m)
print(f"2. solo uno y las puertas cerradas: \"{razon}\" -> derrota: OK")

# 3.
g = partida()
m = g.mision
puerta = g.puertas_dobles[0]
puerta["abierta"] = True
if puerta["rect"] in g.mundo.puertas_alien:
    g.mundo.puertas_alien.remove(puerta["rect"])
g.jugadores[1].eliminar()
assert m.razon_imposible() is None, m.razon_imposible()
segundos(g, 12)
assert m.resultado is None
print("3. con una entrada abierta, uno solo sí puede: OK")

# 4.
for p in g.piezas:
    p["recogida"] = True
razon = m.razon_imposible()
assert razon and "piezas" in razon, razon
print(f"4. sin piezas: \"{razon}\": OK")

# 5.
g = partida()
m = g.mision
g.jugadores[1].eliminar()
g.jugadores[0].sin_conexion = True       # (como en red, mientras se espera que vuelva)
g.jugadores[0].puede_moverse = False
segundos(g, 1.5)
assert "Si nadie vuelve" in g.jugadores[0].mensaje, g.jugadores[0].mensaje
segundos(g, (M.ESPERA_IMPOSIBLE_MS + M.AVISO_IMPOSIBLE_MS + 2000) / 1000)
assert m.resultado is None, "con alguien sin conexión se espera más"
g.jugadores[0].sin_conexion = False
g.jugadores[0].puede_moverse = True
for p in g.puertas_dobles:
    p["abierta"] = True
g.mundo.puertas_alien[:] = []
segundos(g, 2)
assert m.razon_imposible_txt is None and m.resultado is None
print("5. con alguien sin conexión espera, y si vuelve a ser posible sigue: OK")

print("\nTODO OK")
