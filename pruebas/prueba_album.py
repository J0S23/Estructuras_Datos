"""El álbum de fotos de los resultados (screens/album.py).

    python pruebas/prueba_album.py

1. Sin fotos subidas no sale el botón "Álbum de fotos".
2. Con fotos (un rumor desmentido tal cual, otro recortado y una noticia
   confirmada): sale el botón entre "Ver logros" y "Volver al menú", con las
   flechas se llega a él y abre el álbum: una polaroid por foto, en orden, con
   lo que mostraba, lo que decían y si era falso o verdad; las flechas
   escogen; el mouse también; Esc vuelve al resumen.
3. En red: el cliente ve el botón y el álbum (con la foto que vio tomar, o el
   lugar sacado del mapa).

Capturas en pruebas/capturas/album_*.png.
"""

import json
import os
import random
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

import pygame

pygame.init()

from juego import app as App
from juego.dificultad import Dificultad
from screens import album, foto
from screens import resultados as pantalla_resultados
from data.nexus import NOTICIAS

OUT = os.environ.get("NEXUS_CAPTURAS") or os.path.join(RAIZ, "pruebas", "capturas")
os.makedirs(OUT, exist_ok=True)
K = pygame


def partida(semilla=4):
    random.seed(semilla)
    g = App.Game()
    g.cantidad_jugadores = 2
    g.abrir_seleccion_roles(ir=False)
    for estado, rol in zip(g.seleccion_roles, ("Tecnomante", "Forjador")):
        estado["rol"], estado["listo"] = rol, True
    g.dificultad = Dificultad("normal")
    g._preparar_partida()
    g.current_screen = "partida"
    g.transitions = App.TransitionManager()
    g.saltar_tutorial()
    g.presentacion = None
    g.admin_invencible = True
    g.nexus.rng = random.Random(semilla)
    g.nexus.reloj_rumor_ms = g.nexus.reloj_normal_ms = 10 ** 9
    g.eventos.proximo_ms = 10 ** 9
    return g


def poner(j, punto):
    j.personaje.hitbox.center = (int(punto[0]), int(punto[1]))
    j.personaje.sync_sprite_from_hitbox()


def a_resultados(g):
    g.mision.resultado = "victoria"
    g.terminar_ronda()
    g.current_screen = "resultados"
    g.transitions = App.TransitionManager()
    g._dibujar()
    pantalla_resultados.saltar_intro()
    g.iniciales = None
    g._dibujar()


# -- 1. Sin fotos ---------------------------------------------------------------------------------
g = partida()
a_resultados(g)
acciones = [a for _, a in pantalla_resultados.opciones_resultados(g.logros, g.nexus)]
assert "album" not in acciones, acciones
print("1. sin fotos subidas: no sale el botón: OK")

# -- 2. Con fotos ---------------------------------------------------------------------------------
g = partida()
red = g.nexus
j1, j2 = g.jugadores
g._dibujar()
subidas = []
for k, recortada in enumerate((False, True)):
    pub = red.lanzar_rumor()
    assert pub is not None
    quien = (j1, j2)[k]
    red.investigando[quien] = pub
    poner(quien, pub.lugar)
    g._actualizar_partida(16)
    g._dibujar()                       # (aquí se captura la foto)
    assert pub in red.evidencias[quien]
    red.desmentir(quien, pub, con_ubicacion=not recortada)
    subidas.append(pub)
    red.investigando.pop(quien, None)
noticia = red.lanzar_noticia(next(n for n in NOTICIAS if n["lugar"] == "fusibles"))
if noticia is None:
    noticia = red.lanzar_noticia()
if noticia is not None:
    red.arreglar(j1, noticia)
    g._dibujar()
    red.confirmar(j1, noticia, con_ubicacion=True)
    subidas.append(noticia)
entradas = album.fotos_del_equipo(red)
assert [e["origen"] for e in entradas] == subidas, "el álbum no tiene las fotos en orden"
assert [e["recortada"] for e in entradas][:2] == [False, True]
assert all(not e["verdad"] for e in entradas[:2]) and (len(entradas) < 3 or entradas[2]["verdad"])
assert all(foto._por_pub.get(e["origen"].id) is not None for e in entradas), "falta alguna foto tomada"

a_resultados(g)
opciones = pantalla_resultados.opciones_resultados(g.logros, g.nexus)
acciones = [a for _, a in opciones]
assert acciones == ["logros", "album", "menu"], acciones
assert opciones[1][0].endswith(str(len(entradas)))
pygame.image.save(g.screen, os.path.join(OUT, "album_a_resultados.png"))
# Con las flechas: al botón del álbum y Enter.
g._manejar_tecla(K.K_RIGHT)
assert g.resultados_sel == 1
g._manejar_tecla(K.K_RETURN)
assert g.resultados_vista == "album" and g.album_sel == 0
g._dibujar()
pygame.image.save(g.screen, os.path.join(OUT, "album_b_album.png"))
assert len(g.album_rects) == len(entradas), (len(g.album_rects), len(entradas))
# Las polaroids son de papel y llevan su foto.
primera = g.album_rects[0][1]
assert g.screen.get_at((primera.x + 3, primera.y + 3))[:3] == foto.COLOR_PAPEL
g._manejar_tecla(K.K_RIGHT)
assert g.album_sel == 1
g._manejar_tecla(K.K_LEFT)
g._manejar_tecla(K.K_LEFT)
assert g.album_sel == 0
# El mouse escoge.
g._manejar_click(g.album_rects[-1][1].center)
assert g.album_sel == len(entradas) - 1
g._dibujar()
g._manejar_tecla(K.K_ESCAPE)
assert g.resultados_vista == "resumen" and g.current_screen == "resultados"
# Con muchas fotos (más de las que caben), se ve la escogida.
red.publicaciones += [p for p in list(red.publicaciones) if p.tipo == "desmentido"] * 4
total = len(album.fotos_del_equipo(red))
g._activar_resultados("album")
for _ in range(total + 3):
    g._manejar_tecla(K.K_DOWN)
    g._manejar_tecla(K.K_RIGHT)
g._dibujar()
pygame.image.save(g.screen, os.path.join(OUT, "album_c_muchas.png"))
assert g.album_sel == total - 1 and any(i == total - 1 for i, _ in g.album_rects), \
    "la foto escogida no se ve"
print(f"2. con {len(entradas)} fotos: botón entre logros y menú, álbum en orden (falso/verdad, recortada), "
      f"flechas, mouse, Esc; con {total} se ve la escogida: OK")

# -- 3. En red ------------------------------------------------------------------------------------
from cliente_servidor import estado as E
from cliente_servidor.servidor import Servidor, Teclas
from cliente_servidor.espejo import Espejo
from cliente_servidor.protocolo import Reconstructor, comprimir
from cliente_servidor import cliente as C
from entidades.jugador import WASD, FLECHAS

srv = Servidor(2, avisar=lambda t: None, semilla=7, presentaciones=False, aliens_quietos=True,
               roles=["Tecnomante", "Forjador"])
srv.preparar_partida()
srv.lista.set()
for p in srv.puestos:
    p.ocupado = True
srv.teclas = Teclas()
esp = Espejo(App.Game(), srv.bienvenida(srv.puestos[0]))
esp.preparar()
esp.controles({0: WASD, 1: FLECHAS})
gs, gc = srv.juego, esp.g
gs.saltar_tutorial()
r, anterior, cuadro = Reconstructor(), None, 0


def mandar():
    global anterior, cuadro
    ahora = srv.instantanea()
    cuadro += 2
    if anterior is None:
        m = {"tipo": "estado", "c": cuadro, "base": None, "z": comprimir(ahora)}
    else:
        cambios = {k: d for k, d in ((k, E.diferencias(anterior.get(k, {}), v)) for k, v in ahora.items()) if d}
        m = {"tipo": "estado", "c": cuadro, "base": cuadro - 2, "s": cambios}
    anterior = ahora
    esp.aplicar(r.aplicar(json.loads(json.dumps(m))))


gs.nexus.reloj_rumor_ms = gs.nexus.reloj_normal_ms = 10 ** 9
gs._actualizar_partida(16)
mandar()
pantalla = pygame.Surface((1280, 720))
esp.dibujar(pantalla, [0])
for quien in gs.jugadores:            # J1 (esta laptop) y J2 (la otra)
    pub = gs.nexus.lanzar_rumor()
    gs.nexus.investigando[quien] = pub
    poner(quien, pub.lugar)
    gs._actualizar_partida(16)
    mandar()
    esp.dibujar(pantalla, [0])
    gs.nexus.desmentir(quien, pub, con_ubicacion=True)
    gs.nexus.investigando.pop(quien, None)
gs.mision.resultado = "victoria"
gs._actualizar_partida(16)
mandar()
assert len(album.fotos_del_equipo(gc.nexus)) == 2, "el álbum del cliente no tiene las dos fotos"
ses = C.Sesion(gc, "127.0.0.1", 1, [0, 1], avisar=lambda t: None)
ses.espejo, ses._fin_visto = esp, True
gc._reiniciar_resultados()
ses._resultado(pantalla, "victoria")
pantalla_resultados.saltar_intro()
ses._resultado(pantalla, "victoria")
acciones = [a for _, a in pantalla_resultados.opciones_resultados(gc.logros, gc.nexus)]
assert "album" in acciones, acciones
ses._tecla_resultado(K.K_RIGHT)
ses._tecla_resultado(K.K_RETURN)
assert gc.resultados_vista == "album", gc.resultados_vista
esp.dibujar_resultados(pantalla)
pygame.image.save(pantalla, os.path.join(OUT, "album_d_red.png"))
assert len(gc.album_rects) == 2
ses._tecla_resultado(K.K_ESCAPE)
assert gc.resultados_vista == "resumen" and ses.motivo is None
print("3. en red: el cliente ve el botón y el álbum (2 fotos), Esc vuelve: OK")

print("OK prueba_album")
