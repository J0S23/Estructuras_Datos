"""Prueba de las dificultades (dificultad.py, data/dificultad.py).

    python pruebas/prueba_dificultad.py
"""

import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
import pygame; pygame.init()
OUT = os.path.join(RAIZ, "pruebas", "capturas")
os.makedirs(OUT, exist_ok=True)

from juego import app as App
from juego import objetos_mapa
from juego import dificultad
from juego.dificultad import Dificultad
from data.dificultad import DIFICULTADES, AJUSTES, POR_DEFECTO
from data.npcs import ESPERA_INICIAL_MS
objetos_mapa.mapa_activo = lambda: "Nave"
DT = 1000 // 60


class Teclas(dict):
    def __getitem__(self, k):
        return self.get(k, False)


pygame.key.get_pressed = lambda: Teclas()

# ================= Los números =================
claves = [d["clave"] for d in DIFICULTADES]
assert claves == ["tutorial", "facil", "normal", "dificil", "inteligente"]
for nombre, (facil, normal, dificil) in AJUSTES.items():
    assert facil != dificil, nombre
    # Ir de Fácil a Difícil siempre aprieta en la misma dirección.
    assert (facil <= normal <= dificil) or (facil >= normal >= dificil), nombre
d = Dificultad("dificil")
assert d.valor("vel_aliens") == 1.0 and d.valor("cf_espera_ms") == ESPERA_INICIAL_MS
assert d.vidas == 3 and not d.flecha, "Difícil = como era el juego"
t = Dificultad("tutorial")
assert t.vidas_infinitas and t.flecha and t.valor("vel_aliens") < Dificultad("facil").valor("vel_aliens")
i = Dificultad("inteligente")
i.nivel = 3.0
assert i.valor("vel_aliens") > 1.0 and i.valor("cf_espera_ms") < ESPERA_INICIAL_MS
assert i.nombre_nivel() == "Pesadilla" and not i.flecha
i.nivel = 0.5
assert i.flecha
print("niveles:", ", ".join(f"{d['nombre']}" for d in DIFICULTADES))


# Sin dificultad (las pruebas que arman el juego a mano) = como Difícil.
class SinNada:
    pass


assert dificultad.valor(SinNada(), "vel_aliens", 1.0) == 1.0


# ================= La pantalla =================
def avanzar(g):
    for _ in range(80):
        if g.transitions.is_idle():
            break
        g.transitions.update(g, 33)


g = App.Game()
g._activar_opcion_menu("jugar"); avanzar(g)
assert g.current_screen == "cantidad"
g._manejar_tecla(pygame.K_RETURN); avanzar(g)
assert g.current_screen == "dificultad"
assert DIFICULTADES[g.dificultad_seleccionada]["clave"] == POR_DEFECTO
g._manejar_tecla(pygame.K_DOWN)
g._dibujar()
pygame.image.save(g.screen, os.path.join(OUT, "dificultad_pantalla.png"))
g._manejar_tecla(pygame.K_ESCAPE); avanzar(g)
assert g.current_screen == "cantidad", "Esc vuelve a cuántos juegan"
g._manejar_tecla(pygame.K_RETURN); avanzar(g)
g._manejar_tecla(pygame.K_RETURN); avanzar(g)
assert g.current_screen == "roles" and g.dificultad.clave == POR_DEFECTO
g._manejar_tecla(pygame.K_ESCAPE); avanzar(g)
assert g.current_screen == "dificultad", "Esc en los roles vuelve a la dificultad"
print("pantalla: cantidad -> dificultad -> roles (y Esc para atrás)")

# Con el mouse también.
g = App.Game()
g._activar_opcion_menu("jugar"); avanzar(g)
g._dibujar()
g._manejar_click(g.rects_opciones[1].center)        # 3 jugadores
avanzar(g)
assert g.current_screen == "dificultad" and g.cantidad_jugadores == 3
g._dibujar()
g._manejar_click(g.rects_opciones[1].center)        # Fácil
avanzar(g)
assert g.current_screen == "roles" and g.dificultad.clave == "facil"
print("con el mouse: 3 jugadores, Fácil")


# ================= En la partida =================
def partida(clave):
    g = App.Game()
    g._activar_opcion_menu("jugar"); avanzar(g)
    g._manejar_tecla(pygame.K_RETURN); avanzar(g)
    g.dificultad_seleccionada = claves.index(clave)
    g._manejar_tecla(pygame.K_RETURN); avanzar(g)
    g._manejar_tecla(pygame.K_e); g._manejar_tecla(pygame.K_RETURN)
    avanzar(g); g.current_screen = "partida"
    g.tutorial.activo = False; g._terminar_tutorial()
    return g


resumen = {}
for clave in claves:
    g = partida(clave)
    d = g.dificultad
    assert d.clave == clave
    assert g.tiempo_restante_ms is None, "con misión no hay límite de tiempo"
    assert all(j.vidas == j.vidas_max == d.vidas for j in g.jugadores)
    assert g.nexus.umbral_planos == d.umbral_planos
    assert g.cambiaformas.calma_ms == int(d.valor("cf_espera_ms"))
    for _ in range(3):
        g._actualizar_partida(DT)
    assert all(a.ajuste_vel == d.valor("vel_aliens") for a in g.aliens)
    g.screen = pygame.Surface((1024, 768))
    g._dibujar()
    resumen[clave] = (d.vidas, d.umbral_planos,
                      round(d.valor("vel_aliens"), 2))
print("vidas, planos, velocidad de aliens:", resumen)

# Tutorial: que te atrapen no quita vidas.
g = partida("tutorial")
j = g.jugadores[0]
g._atrapar(j, g.aliens[0])
assert j.vidas == j.vidas_max and j.veces_atrapado == 1
print("tutorial: atrapado sin perder vida")

# Fuga: en Fácil el encerrado sale solo; que estén todos presos no es derrota.
g = partida("facil")
g.mision.abrir_puerta()
for j in g.jugadores:
    j.invulnerable_ms = 0
    g._atrapar(j, g.aliens[0])
assert all(j.preso for j in g.jugadores)
g._actualizar_partida(DT)
assert g.mision.resultado is None, "pueden fugarse: no es derrota"
assert "reja" in (g.jugadores[0].pista_mision or "")
for _ in range(int(21000 / DT)):
    g._actualizar_partida(DT)
assert not any(j.preso for j in g.jugadores), "se fugaron a los 20 s"
print("fácil: los encerrados se fugan solos a los 20 s")
# En Difícil, todos presos = derrota (como era).
g = partida("dificil")
g.mision.abrir_puerta()
for j in g.jugadores:
    j.invulnerable_ms = 0
    g._atrapar(j, g.aliens[0])
g._actualizar_partida(DT)
assert g.mision.resultado == "derrota"

# Normal: 4 vidas y se pierden.
g = partida("normal")
j = g.jugadores[0]
g._atrapar(j, g.aliens[0])
assert j.vidas == 3

# ================= La flecha =================
g = partida("facil")
j1 = g.jugadores[0]
m = g.mision
objetivo = m.punto_objetivo(j1)
assert objetivo is not None and "nota" in objetivo[1].lower(), objetivo
for n in m.notas:
    n["leida_por"].add(j1)
assert "puerta" in m.punto_objetivo(j1)[1].lower()
m.abrir_puerta()
assert "consola" in m.punto_objetivo(j1)[1].lower()
for c in m.consolas:
    c["progreso"] = 1.0
g._actualizar_partida(DT)
assert m.fase == "capsula"
assert m.punto_objetivo(j1) is not None
m.empezar_huida()
assert m.punto_objetivo(j1)[0] == m.capsula.center
g.screen = pygame.Surface((1024, 768))
g._dibujar()
pygame.image.save(g.screen, os.path.join(OUT, "dificultad_flecha.png"))
print("flecha: notas -> puerta -> consolas -> cápsula")

# ================= Inteligente =================
g = partida("inteligente")
d = g.dificultad
dichas = []
g.decir = lambda evento, rol=None, forzar=False: dichas.append(evento)
# Les va muy bien: misión avanzada temprano y la tripulación con ellos.
g.mision.abrir_puerta()
for c in g.mision.consolas:
    c["progreso"] = 1.0
for nodo in g.nexus._presos():
    g.nexus.grafo.datos[nodo]["color"] = "verde"
inicio = d.nivel
for _ in range(60 * 80):
    d.actualizar(DT, g)
assert d.nivel > inicio + 1, (inicio, d.nivel)
assert "dificultad_sube" in dichas
print(f"inteligente: les va bien -> nivel {inicio:.1f} a {d.nivel:.2f} ({d.nombre_nivel()})")
# Les va mal: los atrapan seguido y la tripulación les cree a los aliens.
for nodo in g.nexus._presos():
    g.nexus.grafo.datos[nodo]["color"] = "rojo"
alto = d.nivel
for k in range(60 * 100):
    if k % 300 == 0:
        d.al_atrapar()
    d.actualizar(DT, g)
assert d.nivel < alto - 1, (alto, d.nivel)
assert "dificultad_baja" in dichas
assert d.nivel_max >= alto
print(f"inteligente: les va mal -> baja a {d.nivel:.2f} ({d.nombre_nivel()}); "
      f"llegó hasta {d.nombre_nivel(d.nivel_max)}")

# Resultados con la dificultad.
g.terminar_ronda() if hasattr(g, "terminar_ronda") else None
g.current_screen = "resultados"
g.screen = pygame.Surface((1024, 768))
g._dibujar()
pygame.image.save(g.screen, os.path.join(OUT, "dificultad_resultados.png"))

print("\nTODO OK")
