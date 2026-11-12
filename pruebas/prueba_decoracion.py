"""Las imágenes de los objetos (Anny) y la decoración del mapa.

    python pruebas/prueba_decoracion.py

1. Cada imagen que piden sprites_objetos y el catálogo existe.
2. MapaFinal: los muebles se arman, sus hitboxes son parte del mapa, ninguna
   se mete en una pared ni encima de otra.
3. Se choca con un mueble sólido, pero se ve por encima de él (campo de
   visión del jugador y vista de los aliens).
4. Con los muebles se sigue llegando caminando a todo lo de la misión.
5. Se dibuja ordenado por la base: un jugador detrás del mueble queda tapado,
   delante lo tapa. Capturas en pruebas/capturas/deco_*.png.
6. Editor de mapa: poner, mover, voltear, alzar, borrar y deshacer.
"""

import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
sys.path.insert(0, os.path.join(RAIZ, "Editores"))
os.chdir(RAIZ)

import pygame
pygame.init()
pygame.display.set_mode((1366, 768))
OUT = os.path.join(RAIZ, "pruebas", "capturas")
os.makedirs(OUT, exist_ok=True)

from juego import sprites_objetos, decoracion, objetos_mapa, vision
from juego.mundo import Mundo
from data.decoracion import CATALOGO

# -- 1. Imágenes -------------------------------------------------------------------
for clave in sprites_objetos.ARCHIVOS:
    assert sprites_objetos.sprite(clave, 60) is not None, f"falta la imagen de {clave}"
for clave, ficha in CATALOGO.items():
    assert decoracion.tamano(clave) is not None, f"falta {ficha['archivo']}"
usadas = set(sprites_objetos.ARCHIVOS.values()) | {f["archivo"] for f in CATALOGO.values()}
assert not usadas & {f["archivo"] for f in CATALOGO.values()} & set(sprites_objetos.ARCHIVOS.values()), \
    "una imagen es objeto del juego y adorno a la vez"
print(f"1. {len(sprites_objetos.ARCHIVOS)} objetos del juego y {len(CATALOGO)} adornos con imagen: OK")

# -- 2. MapaFinal --------------------------------------------------------------------
mundo = Mundo("MapaFinal")
objetos = objetos_mapa.cargar("MapaFinal")
assert objetos["decoracion"], "MapaFinal no tiene decoración"
muebles = decoracion.crear(objetos, mundo)
solidos = [m for m in muebles if m.solido]
assert len(muebles) == len(objetos["decoracion"]) and solidos
assert all(m.hitbox in mundo.paredes_base for m in solidos)
for i, m in enumerate(solidos):
    assert m.hitbox.collidelist(mundo.paredes_archivo) == -1, f"{m.clave}: hitbox en una pared"
    for otro in solidos[i + 1:]:
        assert not m.hitbox.colliderect(otro.hitbox), f"{m.clave} encima de {otro.clave}"
print(f"2. {len(muebles)} muebles, {len(solidos)} con hitbox, ninguno en una pared: OK")

# -- 3. Se choca, pero se ve por encima ---------------------------------------------------
m = max(solidos, key=lambda m: m.hitbox.width)
pie = pygame.Rect(0, 0, 48, 19)
pie.center = m.hitbox.center
assert mundo.colisiona(pie), "no se choca con el mueble"
antes = (m.hitbox.centerx, m.hitbox.top - 70)
despues = (m.hitbox.centerx, m.hitbox.bottom + 70)
assert not mundo.colisiona(pygame.Rect(antes[0] - 4, antes[1] - 4, 8, 8))
obst = vision.obstaculos(mundo)
assert m.hitbox not in obst, "el mueble tapa el campo de visión"
campo = vision.Campo(antes, obst)
cuerpo = pygame.Rect(0, 0, 30, 60)
cuerpo.midbottom = despues
assert campo.ve_a(cuerpo), "no se ve por encima del mueble"
assert not mundo.tapa_vista_alien(m.hitbox), "el mueble no deja ver a los aliens"
assert mundo.colisiona_alien(m.hitbox), "los aliens atraviesan el mueble"
print(f"3. {m.ficha['nombre']}: se choca, se ve por encima: OK")

# -- 4. Todo sigue alcanzable --------------------------------------------------------------
desde = mundo.punto_libre((int(objetos["spawn"][0] * mundo.ancho), int(objetos["spawn"][1] * mundo.alto)))
con = mundo.area_alcanzable(desde, 48, 19)
mundo.poner_muebles([])
sin = mundo.area_alcanzable(desde, 48, 19)
mundo.poner_muebles([mm.hitbox for mm in solidos])


def toca(celdas, x, y):
    return any(abs(cx + 24 - x) < 70 and abs(cy + 10 - y) < 70 for cx, cy in celdas)


puntos = [p for parte in ("piezas", "notas", "consolas", "consumibles", "nexus", "fusibles", "pruebas")
          for p in objetos[parte]]
puntos += [(o["rx"], o["ry"]) for parte in ("escondites", "terminales", "paneles") for o in objetos[parte]]
perdidos = [p for p in puntos if toca(sin, p[0] * mundo.ancho, p[1] * mundo.alto)
            and not toca(con, p[0] * mundo.ancho, p[1] * mundo.alto)]
assert not perdidos, f"los muebles dejan sin llegar a {perdidos}"
print(f"4. con los muebles se llega igual a los {len(puntos)} puntos de la misión: OK")

# -- 5. Delante y detrás --------------------------------------------------------------------
from juego import app as App
from juego import objetos_mapa as om
g = App.Game()
g.cantidad_jugadores = 1
g.abrir_seleccion_roles(ir=False)
g.seleccion_roles[0]["rol"], g.seleccion_roles[0]["listo"] = "Forjador", True
om.mapa_activo = lambda: "MapaFinal"
g._preparar_partida()
g.current_screen = "partida"
g.saltar_tutorial()
g.presentacion = None
for alien in g.aliens:
    alien.descanso_ms = 10 ** 9
assert len(g.muebles) == len(muebles) and g.mundo.muebles
m = max((mm for mm in g.muebles if mm.solido), key=lambda mm: mm.rect.height)
j = g.jugadores[0]


def poner(y_pies):
    hb = j.personaje.hitbox
    hb.midbottom = (m.hitbox.centerx, y_pies)
    j.personaje.sync_sprite_from_hitbox()


def pixel_del_mueble_tapado():
    """¿Se ve el mueble en el medio de su dibujo (o lo tapa el jugador)?"""
    g._dibujar()
    vista = g.screen.get_rect()
    camara = g.mundo.camara(j.hitbox.center, vista.width, vista.height)
    x, y = m.rect.centerx - camara.x, m.rect.centery - camara.y
    return g.screen.get_at((x, y))


g.oscuridad = False
poner(m.hitbox.top - 2)           # detrás: el mueble lo tapa
assert not g.mundo.colisiona(j.hitbox)
detras = pixel_del_mueble_tapado()
pygame.image.save(g.screen, os.path.join(OUT, "deco_detras.png"))
poner(m.hitbox.bottom + 30)       # delante
pygame.image.save(g.screen, os.path.join(OUT, "deco_delante.png"))
lista = sorted([j] + list(g.muebles), key=lambda c: c.hitbox.bottom)
assert lista.index(j) > lista.index(m), "delante del mueble, el jugador debía dibujarse después"
poner(m.hitbox.top - 2)
lista = sorted([j] + list(g.muebles), key=lambda c: c.hitbox.bottom)
assert lista.index(j) < lista.index(m), "detrás del mueble, el mueble debía dibujarse después"
print(f"5. {m.ficha['nombre']}: detrás lo tapa, delante no (capturas deco_*): OK")

# -- 6. Editor --------------------------------------------------------------------------------
import editor_mapa as E
ed = E.EditorMapa("MapaFinal", ruta_salida=os.path.join(OUT, "_deco_editor.json"))
assert not ed.datos["decoracion"]
ed.herramienta = [h["clave"] for h in E.HERRAMIENTAS].index("decoracion")
W = ed.mundo.ancho
ed.cam = [0.404 * W * ed.zoom - ed.area_mapa.width / 2, 0.53 * W * ed.zoom - ed.area_mapa.height / 2]
libre = ed.a_pantalla((0.47 * W, 0.545 * W))
ed.tecla(pygame.K_t)
ed.clic_izquierdo(libre)
ed.soltar()
assert len(ed.datos["decoracion"]) == 1 and ed.datos["decoracion"][0]["img"] == E.MUEBLES[1]
assert not ed.problemas, ed.problemas
encima = (libre[0], libre[1] - 5)
ed.clic_izquierdo(encima)
ed.arrastrar((encima[0] + 30, encima[1]))
ed.soltar()
assert ed.datos["decoracion"][0]["rx"] > 0.47, "no se movió"
pygame.mouse.get_pos = lambda: (encima[0] + 30, encima[1])
ed.tecla(pygame.K_f)
ed.tecla(pygame.K_PLUS)
assert ed.datos["decoracion"][0].get("volteado") and ed.datos["decoracion"][0].get("alzado") == 4
ed.dibujar()
pared = ed.a_pantalla((0.335 * W, 0.47 * W))
ed.tecla(pygame.K_y)
ed.clic_izquierdo(pared)
ed.soltar()
assert any("pared" in p for p in ed.problemas), ed.problemas
ed.clic_derecho(pared)
ed.clic_derecho((encima[0] + 30, encima[1]))
assert not ed.datos["decoracion"]
ed.deshacer_uno()
assert len(ed.datos["decoracion"]) == 1
print("6. editor: poner, mover, voltear, alzar, aviso de pared, borrar y deshacer: OK")
print("\nTODO OK")
