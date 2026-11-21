"""Lo de la feria: el modo feria, la pantalla de atracción, el ranking y el blindaje.

    python pruebas/prueba_feria.py

1. Modo feria (Menú > Opciones; juego/feria.py), en la dificultad que se
   escoja: un solo código, una consola (la más cercana CAMINANDO), dos piezas,
   con el Guardia, la planta y las puertas para dos (como en el juego normal),
   sin las pruebas del caso,
   el primer rumor pronto, los planos con más confianza (80 %), la
   confianza que sube más rápido (la verdad avanza cada 0.6 s) y un reloj (12 min) en
   el HUD; avisa a los 2 minutos y a 1, y al llegar a 0 termina ("Se acabó el
   tiempo"). Las vidas y los aliens, los de la dificultad. Sin el
   modo feria, nada de esto (ni iniciales ni demo).
2. Ranking (juego/ranking.py): el nombre del equipo (largo: se escribe con el
   teclado, o con el mando, que llega como flechas y Enter), el puntaje, el orden, el archivo, la pantalla
   (Menú > Ranking) y que con el menú de admin no se anota.
3. La pantalla de atracción (juego/demo.py): el menú quieto -> una partida de
   Feria que se juega sola (los jugadores caminan, avanza la misión), con el
   letrero; después el ranking y el menú. Una tecla en la demo -> al menú, con
   lo de antes como estaba. La demo no anota logros.
4. Blindaje: un cuadro que se cae se anota en errores.txt y vuelve al menú (si
   sigue fallando, se deja caer); F12 dos veces vuelve al menú desde la partida.
5. En red: el servidor con --feria arma la partida corta y el espejo igual.
6. Los planos: con desmentidos a tiempo y con foto, cuántos hacen falta (en
   la feria y en Normal sin el modo feria, 3 o más casi siempre).

Capturas en pruebas/capturas/feria_*.png.
"""

import json
import math
import os
import sys
import tempfile

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

import pygame

pygame.init()

from juego import app as App
from juego import demo, feria, ranking, historial_logros
from juego.dificultad import Dificultad
from data.feria import FERIA
from juego.pausa import MenuPausa

OUT = os.environ.get("NEXUS_CAPTURAS") or os.path.join(RAIZ, "pruebas", "capturas")
os.makedirs(OUT, exist_ok=True)
TEMP = tempfile.mkdtemp(prefix="nexus_feria_")
ranking.RUTA = os.path.join(TEMP, "ranking.json")
App.RUTA_ERRORES = os.path.join(TEMP, "errores.txt")


def partida(dificultad="normal", roles=("Tecnomante", "Forjador"), modo_feria=True):
    feria.ACTIVO = modo_feria
    g = App.Game()
    g.cantidad_jugadores = len(roles)
    g.abrir_seleccion_roles(ir=False)
    for estado, rol in zip(g.seleccion_roles, roles):
        estado["rol"], estado["listo"] = rol, True
    g.dificultad = Dificultad(dificultad)
    g._preparar_partida()
    g.current_screen = "partida"
    g.transitions = App.TransitionManager()
    return g


# -- 1. El modo feria ------------------------------------------------------------------------
# Se prende en Menú > Opciones (no es una dificultad).
from data.dificultad import DIFICULTADES
assert "feria" not in [d["clave"] for d in DIFICULTADES]
menu = App.Game()
feria.ACTIVO = False
opciones = MenuPausa(menu, desde_menu=True)
i = [a for _, a in opciones.opciones()].index("feria")
assert opciones.opciones()[i][0] == "Modo feria: No"
opciones.activar(i)
assert feria.ACTIVO and opciones.opciones()[i][0] == "Modo feria: Sí"
opciones.activar(i)
assert not feria.ACTIVO
g = partida()
m = g.mision
normal = partida("normal", modo_feria=False)
assert len(normal.mision.consolas) > 1 and len(normal.mision.puertas) > 1, "(el mapa de la prueba no sirve)"
assert len(m.puertas) == 1, f"en la Feria queda solo la puerta de la salida ({len(m.puertas)})"
assert len(m.consolas) == FERIA["consolas"][2] == 1
# Con 3 jugadores, 2 consolas; con 4, 3 (Diego, nov 21). Ninguna en una sala sellada.
for roles, esperadas in ((("Tecnomante", "Forjador", "Biomante"), 2),
                         (("Tecnomante", "Forjador", "Biomante", "Resonante"), 3)):
    for semilla in range(3):
        _random_consolas = __import__("random")
        _random_consolas.seed(semilla)
        gx = partida(roles=roles)
        assert len(gx.mision.consolas) == esperadas, (len(roles), semilla, len(gx.mision.consolas))
        sellos = getattr(gx.mundo.sellado, "rects", ())
        assert not any(r.colliderect(c["base"]) for r in sellos for c in gx.mision.consolas)
assert m.piezas_necesarias == FERIA["piezas"] == 2 and normal.mision.piezas_necesarias == 3
# El Guardia, la planta con su fruta y las puertas para dos van como en el juego normal.
assert len(g.puertas_dobles) == len(normal.puertas_dobles) > 0, "faltan las puertas para dos en la Feria"
assert g.guardia_planta.guardia is not None and g.guardia_planta.planta is not None, \
    "falta el Guardia o la planta en la Feria"
assert not g.infiltrado.pruebas and normal.infiltrado.pruebas
assert g.nexus.reloj_rumor_ms == FERIA["primer_rumor_s"] * 1000
# Los planos piden más confianza (al menos el 80 %), la verdad convence menos que
# sin dificultad y corre más rápido que en el juego normal.
assert normal.nexus.umbral_planos == normal.dificultad.umbral_planos
assert g.nexus.umbral_planos == max(g.dificultad.umbral_planos, FERIA["umbral_planos_min"]) >= 0.80
from data.feria import AJUSTES_FERIA
assert g.nexus.factor_convencer() == AJUSTES_FERIA["convencer"] < 1
assert normal.nexus.factor_convencer() == normal.dificultad.valor("convencer") < 1
from data.nexus import TICK_PROPAGACION_MS as _TICK
assert g.nexus.tick_verde_ms == FERIA["tick_verde_ms"] < _TICK and normal.nexus.tick_verde_ms == _TICK
assert AJUSTES_FERIA["convencer"] > normal.dificultad.valor("convencer")
assert g.dificultad.valor("bot_crece_cada") > 50 and normal.dificultad.valor("bot_crece_cada") < 5
# Las vidas y los aliens son los de la dificultad (Normal: 5 vidas; Fácil: infinitas).
assert all(j.vidas == 5 and not j.vidas_infinitas for j in g.jugadores)
assert all(j.vidas_infinitas for j in partida("facil").jugadores)
assert g.tiempo_restante_ms == FERIA["limite_s"] * 1000 and normal.tiempo_restante_ms is None
# La consola que queda es la más cercana CAMINANDO (no en línea recta).
from juego import navegacion
for i in range(len(normal.mision.puertas)):
    normal.mision.abrir_puerta(i=i)          # (para medir los caminos sin las puertas)
nav = navegacion.de_mundo(normal.mundo, 34, 20)
inicio = normal.jugadores[0].hitbox.center


def largo(punto):
    c = nav.camino(inicio, punto, sellos=False)
    return sum(math.dist(a, b) for a, b in zip([inicio] + c, c)) if c else float("inf")


largos = sorted((largo(c["base"].center), c["base"].center) for c in normal.mision.consolas)
assert math.dist(largos[0][1], m.consolas[0]["base"].center) < 4, \
    f"la consola de la Feria no es la más cercana caminando: {m.consolas[0]['base'].center} vs {largos}"
m.abrir_puerta(i=0)
assert m.fase == "sabotaje"
g._actualizar_partida(16)
print(f"1. modo feria (Menú > Opciones): 1 código, 1 consola con 2 jugadores, 2 con 3 y 3 con 4 (la de 2, a {largos[0][0]:.0f} px caminando; la más "
      f"cercana en línea recta queda más lejos), 2 piezas, con Guardia/planta/puerta para dos, sin caso, rumor a los "
      f"{FERIA['primer_rumor_s']} s, planos y vidas de la dificultad: OK")

# El reloj: en el HUD, los avisos y el final.
pantalla = pygame.Surface((1280, 720))
g.saltar_tutorial()
g.tiempo_restante_ms = 121 * 1000
g._actualizar_partida(1000)
assert any("2 minutos" in (j.mensaje or "") for j in g.jugadores), [j.mensaje for j in g.jugadores]
g.tiempo_restante_ms = 61 * 1000
g._actualizar_partida(1000)
assert any("1 minuto" in (j.mensaje or "") for j in g.jugadores)
g._dibujar_partida_en(pantalla, g.jugadores, g._extras_dibujo())
pygame.image.save(pantalla, os.path.join(OUT, "feria_reloj.png"))
g.tiempo_restante_ms = 500
g._actualizar_partida(1000)
assert m.resultado == "derrota" and m.motivo_fin == "tiempo", (m.resultado, m.motivo_fin)
assert g.current_screen == "resultados" or g.transitions.active
from screens.resultados import MOTIVOS
assert MOTIVOS["tiempo"]
print("   el reloj: avisa a los 2 minutos y a 1, y al llegar a 0 termina por tiempo: OK")

# -- 2. El ranking ------------------------------------------------------------------------------
assert isinstance(g.iniciales, ranking.Iniciales), "no salieron las iniciales en los resultados"
g.current_screen = "resultados"
g.transitions = App.TransitionManager()
from screens import resultados as pantalla_resultados
g._dibujar()                                 # (empieza la escena del final...)
pantalla_resultados.saltar_intro()           # (... y se salta, como con el primer Enter)
g._dibujar()
assert not pantalla_resultados.en_intro()
K = pygame


def escribir(juego, texto):
    """Teclas del teclado que escriben `texto` (como las manda pygame: el
    unicode en el evento, que app pasa en `texto_tecla`)."""
    for letra in texto:
        juego.texto_tecla = letra
        juego._manejar_tecla(ord(letra.lower()) if letra.isascii() else K.K_a)
        juego.texto_tecla = ""


# Enter sin nombre no anota.
g._manejar_tecla(K.K_RETURN)
assert not g.iniciales.hecho
# Con el teclado se escribe un nombre largo (las W/A/S/D, la E y el espacio
# escriben: ya no mueven) y Borrar borra.
escribir(g, "Los Pumas 23")
g._manejar_tecla(K.K_BACKSPACE)
assert g.iniciales.nombre == "Los Pumas 2" and not g.iniciales.hecho, g.iniciales.nombre
# Con el mando (flechas): arriba al final pone una letra nueva y la cambia.
for tecla in (K.K_UP, K.K_UP, K.K_LEFT, K.K_UP):
    g._manejar_tecla(tecla)
assert g.iniciales.nombre == "Los Pumas 3B", g.iniciales.nombre
g._dibujar()
pygame.image.save(g.screen, os.path.join(OUT, "feria_iniciales.png"))
g._manejar_tecla(K.K_RETURN)
assert g.iniciales.hecho and g.iniciales.puesto == 1, (g.iniciales.hecho, g.iniciales.puesto)
guardado = json.load(open(ranking.RUTA, encoding="utf-8"))["equipos"]
assert guardado[0]["nombre"] == "Los Pumas 3B" and guardado[0]["dificultad"] == "normal" \
    and guardado[0]["feria"] and not guardado[0]["escaparon"]
# Hasta MAX_LETRAS, sin espacios al principio ni dos seguidos.
largo_ = ranking.Iniciales(g)
for letra in "  Los   Guardianes de la Galaxia":
    largo_.escribir(letra)
assert largo_.nombre == "Los Guardianes d"[:ranking.MAX_LETRAS] and len(largo_.letras) == ranking.MAX_LETRAS, \
    largo_.nombre
assert g.resultados_sel == 0, "las teclas de las iniciales movieron los botones de los resultados"
g._dibujar()
pygame.image.save(g.screen, os.path.join(OUT, "feria_resultados_puesto.png"))

# Otro equipo que escapó con tiempo de sobra queda primero.
g2 = partida()
g2.equipo.sumar(30)
g2.tiempo_restante_ms = 200 * 1000
g2.mision.resultado = "victoria"
total, detalle = ranking.puntaje(g2)
assert total == 30 + ranking.BONO_ESCAPE + 200 // ranking.SEGUNDOS_POR_PUNTO and detalle["escaparon"], total
ini = ranking.Iniciales(g2)
for accion in ("arriba", "arriba", "derecha", "arriba", "ok"):     # (solo con el mando)
    ini.tecla(accion, g2)
assert ini.puesto == 1 and ini.total == 2 and ini.nombre == "BA", ini.nombre
assert [e["nombre"] for e in ranking.ordenar(ranking.cargar())] == ["BA", "Los Pumas 3B"]
# Esc: no se anota.
g3 = partida()
g3.mision.resultado = "derrota"
ini = ranking.Iniciales(g3)
ini.tecla("saltar", g3)
assert ini.hecho and ini.saltado and len(ranking.cargar()) == 2
# Sin el modo feria no hay iniciales (ni reloj).
sin = partida(modo_feria=False)
sin.mision.resultado = "derrota"
sin.terminar_ronda()
assert sin.iniciales is None and sin.tiempo_restante_ms is None
# Con el menú de admin, tampoco.
g3.admin_usado = True
g3.current_screen = "partida"
g3.terminar_ronda()
assert g3.iniciales is None, "con el menú de admin se anotaba en el ranking"
# La pantalla: Menú > Ranking.
g3.current_screen = "menu"
g3.transitions = App.TransitionManager()
g3._activar_opcion_menu("ranking")
for _ in range(80):
    g3.transitions.update(g3, 33)
assert g3.current_screen == "ranking" and len(g3.ranking_entradas) == 2
# Un nombre largo en la tabla: cabe (o se corta con "...").
ranking.agregar(dict(ranking.entrada_de(g3, "WWWWWWWWWWWWWWWW"), puntaje=1))
g3.ranking_entradas = ranking.cargar()
g3._dibujar()
pygame.image.save(g3.screen, os.path.join(OUT, "feria_ranking.png"))
g3._manejar_tecla(K.K_ESCAPE)
print("2. ranking: nombre largo con el teclado y el mando, puntaje (+100 por escapar y lo que sobró del reloj), orden, "
      "archivo, Esc no anota, sin admin, Menú > Ranking: OK")

# -- 3. La pantalla de atracción -------------------------------------------------------------------
demo.ESPERA_MENU_S, demo.PARTIDA_S, demo.RANKING_S = 0.2, 25, 1
historial_antes = historial_logros.cargar()
# Sin el modo feria, el menú quieto no hace nada.
feria.ACTIVO = False
d = App.Game()
d.demo_permitida = True
for _ in range(40):
    d._cuadro_seguro(16)
assert d.demo is None and d.current_screen == "menu", "sin el modo feria salió la demo"
feria.ACTIVO = True
cantidad_antes, dificultad_antes = d.cantidad_jugadores, d.dificultad
vistos, recorrido, fases = set(), 0.0, set()
previas = None
letrero = False
for _ in range(60 * 40):
    d._cuadro_seguro(16)
    vistos.add((d.demo is not None, d.current_screen))
    if d.demo is not None and d.current_screen == "partida" and d.transitions.is_idle():
        pos = [j.hitbox.center for j in d.jugadores]
        if previas is not None:
            recorrido += sum(math.dist(a, b) for a, b in zip(pos, previas))
        previas = pos
        fases.add(d.mision.fase)
        if not letrero and d.demo.ms > 6000:
            pygame.image.save(d.screen, os.path.join(OUT, "feria_demo.png"))
            letrero = True
    if (True, "ranking") in vistos and d.demo is None and d.current_screen == "menu":
        break
assert (True, "partida") in vistos, f"no empezó la demo: {vistos}"
assert (True, "ranking") in vistos, "la demo no pasó al ranking"
assert d.demo is None and d.current_screen == "menu", (d.demo, d.current_screen)
assert recorrido > 3000, f"los jugadores de la demo casi no se movieron ({recorrido:.0f} px)"
assert "sabotaje" in fases, f"la misión de la demo no avanzó: {fases}"
assert d.cantidad_jugadores == cantidad_antes and d.dificultad is dificultad_antes, "la demo no dejó todo como estaba"
assert historial_logros.cargar() == historial_antes
assert not d.minijuegos is False, "la demo dejó los minijuegos apagados"
# Una tecla en medio de la demo: al menú.
d._menu_quieto_ms = demo.ESPERA_MENU_S * 1000
for _ in range(60 * 8):
    d._cuadro_seguro(16)
    if d.demo is not None and d.current_screen == "partida" and d.transitions.is_idle() and d.demo.ms > 2000:
        break
assert d.demo is not None and d.current_screen == "partida", "no volvió a empezar la demo"
pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, mod=0, unicode=" ", scancode=0))
d._cuadro_seguro(16)
assert d.demo is None and d.current_screen == "menu", "una tecla en la demo no volvió al menú"
for _ in range(5):                          # (menos que ESPERA_MENU_S de esta prueba)
    d._cuadro_seguro(16)
assert d.demo is None and d.current_screen == "menu", "volvió a la demo enseguida"
print(f"3. atracción (solo en modo feria): menú quieto -> partida sola (caminaron {recorrido:.0f} px, fases {sorted(fases)}) "
      "-> ranking -> menú; una tecla vuelve al menú y deja todo como estaba: OK")

# -- 4. Blindaje -------------------------------------------------------------------------------------
b = partida()
b.saltar_tutorial()
original = App.Game._actualizar_partida


def falla(self, dt=0):
    raise RuntimeError("falla de prueba")


App.Game._actualizar_partida = falla
try:
    b._cuadro_seguro(16)
finally:
    App.Game._actualizar_partida = original
assert b.current_screen == "menu" and b.aviso_menu is not None, "un error en la partida no volvió al menú"
assert "falla de prueba" in open(App.RUTA_ERRORES, encoding="utf-8").read()
b._dibujar()
pygame.image.save(b.screen, os.path.join(OUT, "feria_error_menu.png"))
# Si falla siempre (también en el menú), se deja caer.
original_dibujar = App.Game._dibujar
App.Game._dibujar = lambda self: (_ for _ in ()).throw(ValueError("siempre"))
try:
    cayo = False
    for _ in range(App.Game.MAX_FALLOS + 1):
        try:
            b._cuadro_seguro(16)
        except ValueError:
            cayo = True
            break
finally:
    App.Game._dibujar = original_dibujar
assert cayo, "un error que se repite sin parar no cerró el juego (bucle de errores)"
# F12 dos veces: de la partida al menú.
f = partida()
f._manejar_tecla(pygame.K_F12)
assert f.current_screen == "partida"
f._manejar_tecla(pygame.K_F12)
assert f.current_screen == "menu" and f.iniciales is None
print("4. blindaje: un error vuelve al menú y queda anotado; si no para, se cierra; F12 F12 al menú: OK")

# -- 5. En red ------------------------------------------------------------------------------------------
# Sin sockets, como prueba_red_minijuegos: el servidor arma la partida y sus
# instantáneas pasan por JSON al espejo del cliente.
import json as _json
from cliente_servidor import estado as E
from cliente_servidor.servidor import Servidor, Teclas
from cliente_servidor.espejo import Espejo
from cliente_servidor.protocolo import Reconstructor, comprimir
from cliente_servidor import cliente as C
from entidades.jugador import WASD, FLECHAS


class Red:
    def __init__(self, servidor):
        self.s, self.r, self.anterior, self.cuadro = servidor, Reconstructor(), None, 0

    def mandar(self):
        ahora = self.s.instantanea()
        self.cuadro += 2
        if self.anterior is None:
            m = {"tipo": "estado", "c": self.cuadro, "base": None, "z": comprimir(ahora)}
        else:
            cambios = {k: d for k, d in ((k, E.diferencias(self.anterior.get(k, {}), v)) for k, v in ahora.items())
                       if d}
            m = {"tipo": "estado", "c": self.cuadro, "base": self.cuadro - 2, "s": cambios}
        self.anterior = ahora
        return self.r.aplicar(_json.loads(_json.dumps(m)))


def en_red(con_feria, feria_cliente):
    """(servidor, espejo, canal) de una partida en red con o sin modo feria;
    `feria_cliente`: lo que dice Menú > Opciones en la laptop del cliente."""
    feria.ACTIVO = False                       # (el servidor no lee las opciones)
    srv = Servidor(2, avisar=lambda t: None, semilla=7, presentaciones=False, aliens_quietos=True,
                   roles=["Tecnomante", "Forjador"], feria=con_feria)
    srv.preparar_partida()
    srv.lista.set()
    for p in srv.puestos:
        p.ocupado = True
    srv.teclas = Teclas()
    feria.ACTIVO = feria_cliente
    menu = App.Game()
    esp = Espejo(menu, srv.bienvenida(srv.puestos[0]))
    esp.preparar()
    esp.controles({0: WASD, 1: FLECHAS})
    return srv, esp, Red(srv)


srv, esp, canal = en_red(True, feria_cliente=False)
gs, gc = srv.juego, esp.g
assert srv.bienvenida(srv.puestos[0])["feria"] is True
assert gs.modo_feria and gc.modo_feria, "el espejo no armó la partida en modo feria"
assert len(gs.mision.consolas) == len(gc.mision.consolas) == 1
assert len(gs.mision.puertas) == len(gc.mision.puertas) == 1
assert gs.mision.consolas[0]["base"].center == gc.mision.consolas[0]["base"].center
assert len(gc.puertas_dobles) == len(gs.puertas_dobles) > 0
assert gc.guardia_planta.guardia is not None and gs.guardia_planta.guardia is not None
assert gs.mision.piezas_necesarias == 2
gs.saltar_tutorial()
for _ in range(30):
    gs._actualizar_partida(16)
esp.aplicar(canal.mandar())
assert gc.tiempo_restante_ms is not None and abs(gc.tiempo_restante_ms - gs.tiempo_restante_ms) < 1, \
    "el reloj no llegó al cliente"
assert getattr(gc, "modo_feria_forzado", None) is None, "el Game del menú quedó con el modo feria de la red"
# Se acaba el tiempo en el servidor: termina igual en el cliente.
gs.tiempo_restante_ms = 10
gs._actualizar_partida(16)
gs.equipo.sumar(12)
esp.aplicar(canal.mandar())
assert gc.mision.resultado == "derrota" and gc.mision.motivo_fin == "tiempo", (gs.mision.resultado, gs.mision.motivo_fin, gc.mision.resultado, gc.mision.motivo_fin, gs.tiempo_restante_ms)
# Las iniciales: en la laptop anfitriona (la del servidor), con el puntaje del equipo.
pantalla = pygame.Surface((1280, 720))
for anfitrion, salen in ((False, False), (True, True)):
    ses = C.Sesion(gc, "127.0.0.1", 1, [0, 1], avisar=lambda t: None)
    ses.espejo, ses.anfitrion, ses._fin_visto = esp, anfitrion, True
    gc._reiniciar_resultados()
    ses._resultado(pantalla, "derrota")
    pantalla_resultados.saltar_intro()
    ses._resultado(pantalla, "derrota")
    assert (ses.iniciales is not None) == salen, (anfitrion, ses.iniciales)
pygame.image.save(pantalla, os.path.join(OUT, "feria_red_iniciales.png"))
antes = len(ranking.cargar())
for letra in "Equipo Rojo":
    ses._tecla_resultado(ord(letra.lower()), letra)
ses._tecla_resultado(K.K_RETURN)
assert ses.iniciales.hecho and len(ranking.cargar()) == antes + 1
assert any(e["nombre"] == "Equipo Rojo" and e["puntos"] >= 12 for e in ranking.cargar())
assert ses.motivo is None, "las teclas de las iniciales sacaron de la sesión"
# Sin modo feria en la partida (aunque esta laptop lo tenga prendido): nada recortado.
srv2, esp2, canal2 = en_red(False, feria_cliente=True)
assert not srv2.juego.modo_feria and not esp2.g.modo_feria
assert len(esp2.g.mision.consolas) == len(srv2.juego.mision.consolas) > 1
assert srv2.juego.tiempo_restante_ms is None
feria.ACTIVO = False
print("5. en red: el servidor con --feria arma la partida corta y el espejo igual (aunque esta laptop no "
      "tenga el modo feria), el reloj y el final llegan, las iniciales solo en la anfitriona; sin --feria "
      "nada se recorta: OK")

# -- 6. Cuántos desmentidos piden los planos -----------------------------------------------------
# Un rumor, la foto, el desmentido a los 15 s y 25 s para que corra; hasta que
# lleguen los planos (o 8 desmentidos).
import random as _random
from data.nexus import TICK_PROPAGACION_MS


def desmentidos_para_planos(con_feria, semilla):
    _random.seed(semilla)
    g = partida(modo_feria=con_feria)
    red = g.nexus
    red.rng = _random.Random(semilla)
    red.reloj_rumor_ms = red.reloj_normal_ms = 10 ** 9      # los rumores los pone la prueba
    j = g.jugadores[0]
    for k in range(1, 9):
        pub = red.lanzar_rumor()
        if pub is None:
            return None
        for _ in range(15000 // TICK_PROPAGACION_MS):
            red.actualizar(TICK_PROPAGACION_MS)
        red.evidencias[j].append(pub)
        red.desmentir(j, pub, con_ubicacion=True)
        for paso in range(25000 // 200):
            red.actualizar(200)
            if k == 1 and paso == 10000 // 200 - 1:
                a_los_10_s[con_feria].append(red.barras()[0])
        if red.planos:
            return k
    return 9


a_los_10_s = {True: [], False: []}     # la confianza 10 s después del primer desmentido


con = [desmentidos_para_planos(True, s) for s in range(8)]
sin = [desmentidos_para_planos(False, s) for s in range(8)]
feria.ACTIVO = False
con_ok, sin_ok = sorted(x for x in con if x), sorted(x for x in sin if x)
assert len(con_ok) >= 6 and len(sin_ok) >= 6, (con, sin)
assert con_ok[len(con_ok) // 2] >= 3, f"en la feria los planos salen con muy pocos desmentidos: {con}"
assert min(con_ok) >= 2, f"en la feria un solo desmentido dio los planos: {con}"
# Sin el modo feria también hacen falta varios (antes bastaba uno: Diego llegó
# al 85 % con una foto sin recortar).
assert sin_ok[len(sin_ok) // 2] >= 3, f"en Normal los planos salen con muy pocos desmentidos: {sin}"
# Diego: "en modo feria la confianza sube muy lento". Ahora sube más rápido.
media = {k: sum(v) / len(v) for k, v in a_los_10_s.items()}
assert media[True] > 1.5 * media[False], f"en la feria la confianza no sube más rápido: {media}"
print(f"   confianza 10 s después del primer desmentido: feria {media[True]:.0%}, Normal {media[False]:.0%}")
print(f"6. planos: en la feria con {con} desmentidos (mediana {con_ok[len(con_ok) // 2]}); "
      f"en Normal sin el modo feria con {sin} (mediana {sin_ok[len(sin_ok) // 2]}): OK")

print("OK prueba_feria")
