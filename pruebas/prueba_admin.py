"""Menú de admin (F1): lanzar eventos sin esperarlos.

    python pruebas/prueba_admin.py

1. F1 lo abre y lo cierra (también Esc); abierto, el juego queda congelado.
2. Cada opción hace lo suyo: apagón, volver la luz, la Sombra ya, alarma,
   cierre de emergencia, terminar el evento, evento al azar, rumor de NEXUS,
   trampa del Cambiaformas, aturdir a los aliens, modo invencible, abrir las
   puertas y sacar a los presos. Al escoger se cierra y avisa a todos.
3. Con el mouse: pasar por encima mueve el cursor y el clic la hace.
4. Una partida en que se usó no anota sus logros en el historial.
Captura en pruebas/capturas/admin_menu.png.
"""

import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

import pygame
pygame.init()
pygame.display.set_mode((1366, 768))
OUT = os.path.join(RAIZ, "pruebas", "capturas")
os.makedirs(OUT, exist_ok=True)

from juego import app as App
from juego import admin as A
from juego import historial_logros
from data.dificultad import DIFICULTADES

DT = 1000 // 60


class Teclas(dict):
    def __getitem__(self, k):
        return self.get(k, False)


pygame.key.get_pressed = lambda: Teclas()

g = App.Game()


def avanzar():
    for _ in range(80):
        if g.transitions.is_idle():
            break
        g.transitions.update(g, 33)


g._activar_opcion_menu("jugar"); avanzar(); g._manejar_tecla(pygame.K_RETURN); avanzar()
g.dificultad_seleccionada = [d["clave"] for d in DIFICULTADES].index("normal")
g._manejar_tecla(pygame.K_RETURN); avanzar()
g.seleccion_roles[0]["cursor"] = 0; g._manejar_tecla(pygame.K_e)
g.seleccion_roles[1]["cursor"] = 1; g._manejar_tecla(pygame.K_RETURN); avanzar()
g.saltar_tutorial()
g.presentacion = None
assert g.current_screen == "partida"
j1, j2 = g.jugadores


def indice(texto):
    return next(i for i, o in enumerate(A.OPCIONES) if o["texto"].startswith(texto))


def escoger(texto):
    """Abre el menú, lleva el cursor a la opción con el teclado y Enter."""
    g._manejar_tecla(pygame.K_F1)
    assert g.admin is not None
    for _ in range(indice(texto)):
        g._manejar_tecla(pygame.K_DOWN)
    assert g.admin.cursor == indice(texto)
    g._manejar_tecla(pygame.K_RETURN)
    assert g.admin is None, "al escoger se cierra"
    for _ in range(3):
        g._actualizar_partida(DT)
    return j1.mensaje if hasattr(j1, "mensaje") else None


# -- 1. Abrir, cerrar, congelado ----------------------------------------------------------------
g._manejar_tecla(pygame.K_F1)
assert g.admin is not None
g._dibujar()
pygame.image.save(g.screen, os.path.join(OUT, "admin_menu.png"))
reloj = g.tiempo_jugado_ms
for _ in range(30):                        # como el run(): con el menú abierto no se actualiza
    if g.admin is None:
        g._actualizar_partida(DT)
assert g.tiempo_jugado_ms == reloj
g._manejar_tecla(pygame.K_F1)
assert g.admin is None
g._manejar_tecla(pygame.K_F1); g._manejar_tecla(pygame.K_ESCAPE)
assert g.admin is None and g.pausa is None, "Esc cierra el admin (no abre la pausa)"
print("1. F1 abre y cierra el menú (y Esc); abierto, el juego queda congelado: OK")

# -- 2. Cada opción ------------------------------------------------------------------------------
ev = g.eventos
escoger("Que se vaya la luz")
assert ev.apagon and ev.caja is not None
escoger("Que aparezca la Sombra")
assert g.sombra in g.aliens, "la Sombra no apareció"
escoger("Que vuelva la luz")
assert not ev.apagon
for _ in range(3):
    g._actualizar_partida(DT)
assert g.sombra not in g.aliens, "con luz la Sombra se va"
escoger("Que aparezca la Sombra")                # sin apagón: corta la luz primero
assert ev.apagon and g.sombra in g.aliens
escoger("Que vuelva la luz")
escoger("Alarma")
assert ev.activo == "alarma" and any(a.alerta for a in g.aliens)
escoger("Cierre de emergencia")
assert ev.activo == "compuerta" and ev.compuerta["cerrada"]
escoger("Terminar la alarma")
assert ev.activo is None and not any(c["cerrada"] for c in g.compuertas)
escoger("Un evento al azar")
assert ev.activo is not None or ev.apagon
escoger("Terminar la alarma");
if ev.apagon:
    escoger("Que vuelva la luz")
antes = len(g.nexus.rumores_activos())
escoger("Rumor de un bot")
assert len(g.nexus.rumores_activos()) == antes + 1
if g.cambiaformas is not None:
    g.cambiaformas.siguiendo = g.cambiaformas.presa = None
    escoger("Trampa del Cambiaformas")
    assert g.nexus.trampa_activa() is not None, "no publicó la trampa"
escoger("Aturdir a todos")
assert all(a.descanso_ms > 0 for a in g.aliens
           if not getattr(a, "oculta", False) and a.tipo != "guardia")   # (el Guardia es inmune)
escoger("Modo invencible")
assert g.admin_invencible and all(not j.cazable for j in g.jugadores)
celda = g.mision.celdas[0]
celda["preso"], j2.preso = j2, celda
escoger("Sacar a todos")
assert celda["preso"] is None and j2.preso is None
for _ in range(5):
    g._actualizar_partida(DT)
assert not j2.cazable, "invencible también al salir de la celda"
escoger("Modo invencible")
assert not g.admin_invencible
escoger("Abrir todas las puertas")
assert all(p["abierta"] for p in g.mision.puertas) and all(p["abierta"] for p in g.puertas_dobles)
print("2. las 13 opciones hacen lo suyo y avisan: OK")

# -- 3. Mouse ---------------------------------------------------------------------------------------
g._manejar_tecla(pygame.K_F1)
g._dibujar()
fila = g.admin.rects[indice("Que se vaya la luz")]
pygame.event.post(pygame.event.Event(pygame.MOUSEMOTION, pos=fila.center, rel=(0, 0), buttons=(0, 0, 0)))
g._manejar_eventos()
assert g.admin.cursor == indice("Que se vaya la luz")
g._manejar_click(fila.center)
assert g.admin is None and ev.apagon
print("3. con el mouse: el cursor sigue al mouse y el clic la hace: OK")

# -- 4. Historial de logros ----------------------------------------------------------------------------
anotados = []
historial_logros.agregar = lambda claves: anotados.append(list(claves))
g.terminar_ronda()
assert g.admin_usado and not anotados, "una partida con admin no debe anotar logros"
print("4. la partida en que se usó no anota sus logros en el historial: OK")
print("\nTODO OK")
