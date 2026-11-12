"""Consolas y terminales que se chocan, cajas de fusibles en la pared y el
editor de mapa con las imágenes de todo.

    python pruebas/prueba_estaciones_solidas.py

1. MapaFinal: las patas de cada consola y cada terminal son parte del mapa
   (se chocan); el piso de enfrente queda libre.
2. Una consola se apaga desde enfrente y desde un lado, no desde lejos.
3. Una terminal se usa desde enfrente o pegado a ella, no desde lejos.
4. Se dibujan ordenadas con los personajes: delante de la consola el jugador
   la tapa, detrás ella lo tapa (y se vuelve transparente).
5. Una caja de fusibles colgada en la pared se arregla desde el piso de
   abajo, y sigue contando como alcanzable para el apagón.
6. Editor: dibuja la imagen de los objetos del juego (consolas, terminales,
   paneles, cajas, casilleros, NEXUS, paneles de puertas), una caja en la
   pared no es un problema, una caja metida en medio de un muro sí, y
   MapaFinal no tiene problemas.
7. Los casilleros usan dos modelos; el armario 029 es decoración.
8. Las terminales NEXUS también se chocan, y se usan parado debajo de ellas.
9. Los casilleros se chocan: se entra parado delante (la mitad de abajo de
   su casilla), y al salir el jugador queda libre, no metido en las patas.
Capturas en pruebas/capturas/solidas_*.png.
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

from juego import app as App
from juego import objetos_mapa as om
from juego import sprites_objetos, decoracion
from entidades import acciones_rol
from misiones.mision import consola_cerca
from misiones.eventos import junto_a_caja
from screens import mision_dibujo

om.mapa_activo = lambda: "MapaFinal"
g = App.Game()
g.cantidad_jugadores = 2
g.abrir_seleccion_roles(ir=False)
for estado, rol in zip(g.seleccion_roles, ("Tecnomante", "Forjador")):
    estado["rol"], estado["listo"] = rol, True
g._preparar_partida()
g.current_screen = "partida"
g.saltar_tutorial()
g.presentacion = None
for alien in g.aliens:
    alien.descanso_ms = 10 ** 9
g.oscuridad = False
tec, forj = g.jugadores
m = g.mision
mundo = g.mundo


def poner(j, midbottom):
    hb = j.personaje.hitbox
    hb.midbottom = midbottom
    j.personaje.sync_sprite_from_hitbox()


# -- 1. Las patas se chocan ------------------------------------------------------------------
assert m.consolas and g.terminales
for k in m.consolas:
    assert k["solido"] in mundo.paredes_base, "las patas de la consola no son parte del mapa"
    assert mundo.colisiona(k["solido"].inflate(-4, -4))
    assert not mundo.colisiona(k["rect"]), "el piso de enfrente de la consola choca"
for t in g.terminales:
    assert t["solido"] in mundo.paredes_base, "las patas de la terminal no son parte del mapa"
    assert not mundo.colisiona(sprites_objetos.frente("terminal", t["rect"])), \
        "el piso de enfrente de la terminal choca"
print(f"1. {len(m.consolas)} consolas y {len(g.terminales)} terminales se chocan; su frente queda libre: OK")

# -- 2. Apagar una consola ---------------------------------------------------------------------
m.fase = "sabotaje"
consola = m.consolas[0]
poner(tec, (consola["rect"].centerx, consola["rect"].bottom - 2))   # enfrente
assert not mundo.colisiona(tec.hitbox)
assert consola_cerca(consola, tec)
for _ in range(20):
    m.mantener(tec, 100)
assert consola["progreso"] > 0, "no se apagó desde enfrente"
lado = consola["solido"]
poner(tec, (lado.left - 30, lado.bottom))                             # a la izquierda
assert consola_cerca(consola, tec), "desde un lado no la alcanza"
poner(tec, (consola["rect"].centerx, consola["rect"].bottom + 120))   # lejos
assert not consola_cerca(consola, tec)
print("2. la consola se apaga desde enfrente y desde un lado, no desde lejos: OK")

# -- 3. Terminal ---------------------------------------------------------------------------------
terminal = g.terminales[0]
poner(tec, (terminal["rect"].centerx, terminal["rect"].bottom - 2))
assert acciones_rol.estacion_bajo(g, tec) is terminal
poner(tec, (terminal["rect"].centerx, terminal["rect"].bottom + 90))
assert acciones_rol.estacion_bajo(g, tec) is None
print("3. la terminal se usa desde enfrente, no desde lejos: OK")

# -- 4. Delante y detrás ---------------------------------------------------------------------------
camara = pygame.Rect(0, 0, 4000, 4000)
camara.center = consola["solido"].center
erguidos = mision_dibujo.erguidos(m, camara, 0)
e = next(x for x in erguidos if x.hitbox is consola["solido"])
poner(tec, (consola["rect"].centerx, consola["rect"].bottom - 2))
assert sorted([tec, e], key=lambda c: c.hitbox.bottom)[-1] is tec, "delante, el jugador debía ir encima"
detras = (consola["solido"].centerx, consola["solido"].top - 2)
poner(tec, detras)
assert sorted([tec, e], key=lambda c: c.hitbox.bottom)[-1] is e, "detrás, la consola debía ir encima"
decoracion.marcar_transparentes([e], [tec])
assert e.transparente, "la consola que tapa al jugador no se volvió transparente"
poner(tec, (consola["rect"].centerx, consola["rect"].bottom - 2))
g._dibujar()
pygame.image.save(g.screen, os.path.join(OUT, "solidas_consola.png"))
print("4. delante de la consola el jugador la tapa; detrás, ella (transparente): OK")

# -- 5. Caja de fusibles en la pared -------------------------------------------------------------
ev = g.eventos
en_pared = [c for c in ev.cajas if mundo.colisiona(c["rect"])]
assert en_pared, "MapaFinal debía tener alguna caja colgada en la pared"
caja = en_pared[0]
assert not mundo.colisiona(pygame.Rect(caja["pie"][0] - 17, caja["pie"][1] - 10, 34, 20))
poner(forj, (caja["pie"][0], caja["pie"][1] + 9))
assert not mundo.colisiona(forj.hitbox)
assert junto_a_caja(caja, forj), "desde el piso de abajo no alcanza la caja de la pared"
# (con las puertas abiertas: alguna caja de la pared puede quedar detrás de una)
mundo.paredes = list(mundo.paredes_base)
for doble in g.puertas_dobles:
    doble["abierta"] = True
assert caja in ev._cajas_alcanzables(), "la caja de la pared no cuenta como alcanzable"
ev.apagon, ev.caja = True, caja
for _ in range(40):
    ev.mantener(forj, 100)
assert not ev.apagon, "no volvió la luz arreglando la caja de la pared"
poner(forj, (caja["pie"][0], caja["pie"][1] + 140))
assert not junto_a_caja(caja, forj)
print(f"5. {len(en_pared)} caja(s) en la pared: se arreglan desde el piso de abajo: OK")

# -- 6. Editor -------------------------------------------------------------------------------------
import editor_mapa as E
ed = E.EditorMapa("MapaFinal")
ed.validar()
assert not ed.problemas, ed.problemas
tipos = {herr for herr, *_ in ed.objetos_con_imagen()}
for herr in ("escondites", "terminales", "paneles", "consolas", "fusibles", "nexus", "puertas_dobles"):
    assert herr in tipos, f"el editor no dibuja la imagen de {herr}"
con_patas = [x for x in ed.objetos_con_imagen() if x[4] is not None]
assert len(con_patas) == len(ed.datos["consolas"]) + len(ed.datos["terminales"]) + len(ed.datos["nexus"]) \
    + len(ed.datos["escondites"])
ed.herramienta = [h["clave"] for h in E.HERRAMIENTAS].index("consolas")
W = ed.mundo.ancho
c0 = ed.datos["consolas"][0]
ed.cam = [c0[0] * W * ed.zoom - ed.area_mapa.width / 2, c0[1] * W * ed.zoom - ed.area_mapa.height / 2]
ed.dibujar()
pygame.image.save(ed.screen, os.path.join(OUT, "solidas_editor.png"))
# Una caja metida en medio de un muro grueso, lejos del piso: eso sí es un problema.
grueso = max(ed.mundo.paredes_archivo, key=lambda r: min(r.width, r.height))
ed.datos["fusibles"].append([grueso.centerx / W, grueso.centery / ed.mundo.alto])
ed.validar()
assert any("Fusibles" in p and "pared" in p for p in ed.problemas), ed.problemas
print(f"6. editor: imágenes de {len(tipos)} clases de objetos, caja en la pared sin problema, "
      "en medio del muro sí: OK")

# -- 7. Casilleros y el armario 029 ------------------------------------------------------------------
from data.decoracion import CATALOGO
assert {sprites_objetos.modelo_escondite(f"casillero_{i}") for i in range(30)} == {"escondite_0", "escondite_1"}
assert "OBJ-029_Armario_de_almacenamiento" in CATALOGO
assert "OBJ-029_Armario_de_almacenamiento.png" not in sprites_objetos.ARCHIVOS.values()
print("7. casilleros con dos modelos; el armario 029 es decoración: OK")

# -- 8. Terminales NEXUS -----------------------------------------------------------------------------
nexus = [z for z in g.zonas if str(z.get("clave", "")).startswith("nexus")]
assert nexus, "MapaFinal debía tener terminales NEXUS"
for z in nexus:
    patas = sprites_objetos.hitbox("nexus", z["rect"])
    assert patas in mundo.paredes_base, "las patas de la terminal NEXUS no son parte del mapa"
    poner(tec, (z["rect"].centerx, patas.bottom + 22))             # parado debajo
    assert not mundo.colisiona(tec.hitbox), f"debajo de {z['clave']} choca"
    assert g.zona_bajo(tec) is z, f"no se usa {z['clave']} desde debajo"
    poner(tec, (z["rect"].centerx, z["rect"].bottom + 160))
    assert g.zona_bajo(tec) is not z
z = nexus[0]
poner(tec, (z["rect"].centerx, sprites_objetos.hitbox("nexus", z["rect"]).bottom + 22))
g._dibujar()
pygame.image.save(g.screen, os.path.join(OUT, "solidas_nexus.png"))
print(f"8. {len(nexus)} terminales NEXUS se chocan y se usan desde debajo: OK")

# -- 9. Casilleros -----------------------------------------------------------------------------------
assert g.escondites
for esc in g.escondites:
    assert esc["solido"] in mundo.paredes_base, "las patas del casillero no son parte del mapa"
    assert not mundo.colisiona(sprites_objetos.frente("escondite", esc["rect"])), \
        f"el piso de enfrente de {esc['clave']} choca"
    poner(tec, esc["rect"].midbottom)                                 # delante
    assert not mundo.colisiona(tec.hitbox), f"delante de {esc['clave']} choca"
    assert g.escondite_bajo(tec) is esc, f"no se entra a {esc['clave']} desde delante"
    tec.esconderse(esc)
    tec.salir_del_escondite()
    assert not mundo.colisiona(tec.hitbox), f"al salir de {esc['clave']} queda metido en las patas"
esc = g.escondites[0]
poner(tec, (esc["solido"].centerx, esc["solido"].top - 2))          # detrás
assert not tec.hitbox.colliderect(esc["solido"])
antes = tec.hitbox.copy()
for _ in range(30):                                                    # camina hacia abajo
    tec.personaje.hitbox.y += 3
    if mundo.colisiona(tec.hitbox):
        tec.personaje.hitbox.y -= 3
assert tec.hitbox.bottom <= esc["solido"].top, "se pasó a través del casillero"
camara = pygame.Rect(0, 0, 4000, 4000)
camara.center = esc["rect"].center
from screens import partida as pantalla_partida
ergs = pantalla_partida.erguidos_escondites(g.escondites, camara, tec)
e = next(x for x in ergs if x.hitbox is esc["solido"])
assert sorted([tec, e], key=lambda c: c.hitbox.bottom)[-1] is e, "detrás, el casillero debía ir encima"
decoracion.marcar_transparentes([e], [tec])
assert e.transparente
g._dibujar()
pygame.image.save(g.screen, os.path.join(OUT, "solidas_casillero.png"))
print(f"9. {len(g.escondites)} casilleros se chocan, se entra desde delante y se sale libre: OK")
print("\nTODO OK")
