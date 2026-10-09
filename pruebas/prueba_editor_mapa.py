"""Prueba del editor de mapa y de que el juego use lo que se guarda, sin ventana.

    python pruebas/prueba_editor_mapa.py

Abre el editor sobre el Colegio, pone, mueve y borra cosas con "clics"
simulados, revisa que avise lo que choca con paredes, guarda en un archivo de
prueba y arranca una partida con ese archivo para ver que el juego lo use.
No toca Hitboxes/Colegio_objetos.json ni el mapa activo.

Guarda una captura en pruebas/capturas/editor_mapa.png.
"""

import os, sys, math
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "Editores"))
os.chdir(RAIZ)
import pygame; pygame.init()
pygame.display.set_mode((1366, 768))
OUT = os.path.join(RAIZ, "pruebas", "capturas")
os.makedirs(OUT, exist_ok=True)
TEMP = os.path.join(OUT, "_objetos_prueba.json")
if os.path.exists(TEMP):
    os.remove(TEMP)

import objetos_mapa
from editor_mapa import EditorMapa, HERRAMIENTAS

real = objetos_mapa.ruta_archivo("Colegio")
existia = os.path.exists(real)
activo_antes = objetos_mapa.mapa_activo()

ed = EditorMapa("Colegio", ruta_salida=TEMP)
fabrica = objetos_mapa.normalizar(objetos_mapa.por_defecto())
for parte in ("escondites", "terminales", "paneles", "piezas", "rutas_aliens"):
    assert len(ed.datos[parte]) == len(fabrica[parte]), parte
print("arranca con los valores de data/:",
      {p: len(ed.datos[p]) for p in ("rutas_aliens", "escondites", "terminales", "paneles", "piezas")})
print("problemas con lo de fábrica:", ed.problemas or "ninguno")
assert not ed.problemas, ed.problemas

def usar(nombre):
    ed.herramienta = [h["clave"] for h in HERRAMIENTAS].index(nombre)

def en_pantalla(p):
    return ed.a_pantalla(p)

def clic(p):
    ed.clic_izquierdo(en_pantalla(p)); ed.soltar()

# Poner un escondite en un lugar libre, moverlo y borrarlo.
usar("escondites")
libre = (768, 560)
clic(libre)
assert len(ed.datos["escondites"]) == len(fabrica["escondites"]) + 1
nuevo = ed.datos["escondites"][-1]
assert nuevo["clave"] and nuevo["nombre"] == "Casillero"
print("\nescondite puesto con clic:", nuevo["clave"], "| problemas:", len(ed.problemas))
ed.clic_izquierdo(en_pantalla(libre)); ed.arrastrar(en_pantalla((800, 600))); ed.soltar()
movido = ed.datos["escondites"][-1]
assert abs(movido["rx"] * ed.mundo.ancho - 800) < 4 and abs(movido["ry"] * ed.mundo.alto - 600) < 4
print("arrastrado a", (round(movido["rx"], 3), round(movido["ry"], 3)))

# Uno encima de una pared: el editor lo marca.
pared = ed.mundo.paredes[0].center
clic(pared)
assert any("pared" in p for p in ed.problemas), ed.problemas
print("en una pared ->", [p for p in ed.problemas if "pared" in p])
ed.clic_derecho(en_pantalla(pared))
assert not any("pared" in p for p in ed.problemas)
print("clic derecho lo borra")

# Deshacer y rehacer.
antes = len(ed.datos["escondites"])
ed.deshacer_uno()
assert len(ed.datos["escondites"]) == antes + 1
ed.rehacer_uno()
assert len(ed.datos["escondites"]) == antes
print("deshacer / rehacer funcionan")

# Ruta nueva: tres puntos libres y uno que cruza una pared.
usar("rutas_aliens")
ed.nueva_ruta()
for p in [(600, 640), (930, 640), (930, 900)]:
    clic(p)
ruta = ed.datos["rutas_aliens"][-1]
assert len(ruta) == 3 and ed.ruta_elegida == len(ed.datos["rutas_aliens"]) - 1
print("\nruta nueva con 3 puntos:", ruta)
assert not ed.tramos_malos.get(ed.ruta_elegida), ed.tramos_malos
clic((60, 900))         # al otro lado de un salón
assert ed.tramos_malos.get(ed.ruta_elegida), "debió detectar el tramo que cruza la pared"
print("el tramo que cruza una pared sale marcado:", ed.tramos_malos[ed.ruta_elegida])
ed.clic_derecho(en_pantalla((60, 900)))
assert not ed.tramos_malos.get(ed.ruta_elegida)

# Mover el inicio y una zona.
usar("spawn"); clic((768, 700))
usar("zonas")
plaza = ed.datos["zonas"]["plaza"]
centro = ed.px(plaza["rx"], plaza["ry"])
ed.clic_izquierdo(en_pantalla(centro)); ed.arrastrar(en_pantalla((centro[0] + 40, centro[1]))); ed.soltar()
assert abs(ed.datos["zonas"]["plaza"]["rx"] * ed.mundo.ancho - (centro[0] + 40)) < 4
print("\ninicio y zona movidos")

ed.dibujar(); pygame.image.save(ed.screen, os.path.join(OUT, "editor_mapa.png"))

# Guardar y que el juego lo use.
ed.guardar()
assert os.path.exists(TEMP) and not ed.sucio
leido = objetos_mapa.cargar(ruta=TEMP)
assert leido["rutas_aliens"] == ed.datos["rutas_aliens"]
assert len(leido["escondites"]) == len(ed.datos["escondites"])
print("guardado y leído igual:", os.path.relpath(TEMP, RAIZ))

import App
original = objetos_mapa.cargar
objetos_mapa.cargar = lambda mapa=None, ruta=None: original(ruta=TEMP)
g = App.Game()
def avanzar():
    for _ in range(80):
        if g.transitions.is_idle(): break
        g.transitions.update(g, 33)
g._activar_opcion_menu("jugar"); avanzar(); g.current_screen = "cantidad"
g._manejar_tecla(pygame.K_RETURN); avanzar(); g.current_screen = "roles"
g.seleccion_roles[0]["cursor"] = 0; g._manejar_tecla(pygame.K_e)
g.seleccion_roles[1]["cursor"] = 1; g._manejar_tecla(pygame.K_RETURN)
avanzar()
objetos_mapa.cargar = original
assert len(g.aliens) == len(leido["rutas_aliens"])
assert len(g.escondites) == len(leido["escondites"])
inicio = (0.5 * 0 + leido["spawn"][0] * g.mundo.ancho, leido["spawn"][1] * g.mundo.alto)
cerca = min(math.dist(j.hitbox.center, inicio) for j in g.jugadores)
assert cerca < 200, cerca
plaza_juego = [z for z in g.zonas if z["clave"] == "plaza"][0]
assert abs(plaza_juego["rect"].centerx - leido["zonas"]["plaza"]["rx"] * g.mundo.ancho) < 3
print(f"el juego usa el archivo: {len(g.aliens)} aliens, {len(g.escondites)} escondites, "
      f"jugadores junto al inicio, plaza movida")

os.remove(TEMP)
assert os.path.exists(real) == existia, "no debía tocar el archivo real del Colegio"
assert objetos_mapa.mapa_activo() == activo_antes
print("\nTODO OK")
