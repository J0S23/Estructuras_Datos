"""La sala oculta de los niños (misiones/sala_secreta.py), sin ventana.

    python pruebas/prueba_sala_secreta.py

En MapaFinal: la pared está cerrada (y la navegación no pasa) hasta que la
cápsula queda lista; se abre; las pistas del Acto 2 se revisan; al entrar
hablan, suena la alarma y votan; los aliens vienen pero llegan justo al
acabar el contador (ni antes ni después); y cada final sale bien:

- "quedarse" (más votos o empate), "escaparon" (más votos por la cápsula),
  "nadie" (nadie votó) y "sin_entrar" (escaparon sin entrar a la sala);
- el reloj de la Feria no corre durante la votación;
- en la ronda siguiente la pared vuelve a estar cerrada.

Las capturas quedan en la carpeta temporal (o en NEXUS_CAPTURAS).
"""

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
CARPETA = os.environ.get("NEXUS_CAPTURAS") or os.path.join(tempfile.gettempdir(), "nexus_capturas")
os.makedirs(CARPETA, exist_ok=True)


class Teclas(dict):
    def __getitem__(self, k):
        return self.get(k, False)


pygame.key.get_pressed = lambda: Teclas()

from juego import app as App, objetos_mapa, navegacion
from data.historia import VOTACION, DESENLACE_MS, ABRIR_PARED_MS
from misiones.sala_secreta import geometria

objetos_mapa.mapa_activo = lambda: "MapaFinal"
DT = 16


def partida(g, n=2, feria=False):
    def avanzar():
        for _ in range(80):
            if g.transitions.is_idle():
                break
            g.transitions.update(g, 33)
    g.modo_feria_forzado = feria
    avanzar()                    # (la transición a los resultados de la ronda anterior)
    g.current_screen = "menu"
    g._activar_opcion_menu("jugar")
    avanzar()
    g.cantidad_seleccionada = n - 2
    for _ in range(12):
        # Las pantallas de antes de jugar, como las recorre un jugador (la de
        # dificultad sale desde la segunda partida).
        if g.current_screen == "roles":
            # (cada uno escoge un rol distinto; con 3 o 4, el tercero va con mando)
            from data.roles import ROLES
            for i, estado in enumerate(g.seleccion_roles):
                if not estado["listo"]:
                    usados = {e["rol"] for e in g.seleccion_roles if e["listo"]}
                    estado["cursor"] = next(k for k, r in enumerate(ROLES) if r["nombre"] not in usados)
                    g._confirmar_rol(i, estado)
        elif g.current_screen in ("cantidad", "dificultad", "controles"):
            g._manejar_tecla(pygame.K_RETURN)
        else:
            break
        avanzar()
    for _ in range(400):
        if g.current_screen == "partida" or g.carga is None:
            break
        g._actualizar_carga(DT)
        avanzar()
    g.current_screen = "partida"
    if g.tutorial is not None:
        g.saltar_tutorial()
    g.presentacion = None
    for j in g.jugadores:
        j.invulnerable_ms = 10 ** 9
    return g.sala_secreta


def cuadros(g, ms):
    for _ in range(int(ms // DT)):
        g._actualizar_partida(DT)
        if g.mision.resultado is not None:
            return


def poner(j, punto):
    j.personaje.hitbox.center = punto
    j.personaje.sync_sprite_from_hitbox()


def foto(g, nombre):
    g._dibujar()
    pygame.image.save(g.screen, os.path.join(CARPETA, f"sala_{nombre}.png"))


def abrir(g, sala):
    g.mision.abrir_puerta()
    g.mision.empezar_huida()
    cuadros(g, ABRIR_PARED_MS + 400)
    assert sala.estado == "abierta", sala.estado


def entrar(g, sala):
    poner(g.jugadores[0], (sala.sala.left + 120, sala.pasillo.centery))
    if len(g.jugadores) > 1:
        poner(g.jugadores[1], (sala.sala.left + 60, sala.pasillo.centery + 40))
    cuadros(g, 50)
    assert sala.estado == "dialogo", sala.estado
    dicho = set()
    while sala.estado == "dialogo":
        cuadros(g, DT)
        dicho.update(j.mensaje for j in g.jugadores if j.mensaje)
    return dicho


def votar(g, j, clave):
    """Con las teclas del jugador, como en el juego."""
    quiere = [o["clave"] for o in VOTACION["opciones"]].index(clave)
    while j.cursor % 2 != quiere:
        g._tecla_en_partida(j.teclas["derecha"][0])
    g._tecla_en_partida(j.teclas["interactuar"][0])


def terminar(g, sala):
    while sala.estado == "votacion":
        cuadros(g, DT)
    cuadros(g, DESENLACE_MS + 200)
    return g.mision.final, g.mision.resultado


g = App.Game()

# == 1. Cerrada hasta reparar la cápsula; se abre; pistas; votación ========================
sala = partida(g)
assert sala is not None and sala.activa, "MapaFinal tiene sala oculta"
assert sala.puerta in g.mundo.paredes, "la losa tapa el pasillo"
nav = navegacion.de_mundo(g.mundo, 34, 20)
desde = (sala.puerta.centerx, sala.puerta.bottom + 90)       # en la Bahía, frente a la puerta
assert not nav.conectados(desde, sala.sala.center), "cerrada: nadie llega a la sala"
assert len(sala.pistas) == 3, sala.pistas
from juego.salas import sala_en
print("pistas en:", [(p["tipo"], sala_en(g.salas, p["punto"])) for p in sala.pistas])
cuadros(g, 1000)
assert sala.estado == "cerrada", "no se abre sola"

# Las pistas: J2 revisa dos (con la tecla de interactuar).
for pista in sala.pistas[:2]:
    poner(g.jugadores[1], (pista["punto"][0] - 30, pista["punto"][1]))
    cuadros(g, 50)
    assert g.jugadores[1].pista_mision, "abajo dice qué revisar"
    g._tecla_en_partida(g.jugadores[1].teclas["interactuar"][0])
    assert pista["encontrada"] and g.jugadores[1].mensaje, pista
assert sala.encontradas == 2
foto(g, "a_pista")

abrir(g, sala)
assert sala.puerta not in g.mundo.paredes, "abierta: la losa ya no tapa"
assert nav.conectados(desde, sala.sala.center), "abierta: se llega a la sala caminando"
poner(g.jugadores[0], (sala.puerta.centerx + 40, sala.puerta.bottom + 140))
cuadros(g, 50)
foto(g, "b_abierta")

dicho = entrar(g, sala)
assert sala.estado == "votacion"
for j in g.jugadores:
    assert (j.panel or {}).get("tipo") == "votacion", "a cada uno le sale el menú"
# Hablan de los niños y de lo que encontraron por el camino (2 pistas).
from data.historia import PISTAS_EN_DIALOGO
assert any("niños" in m for m in dicho), dicho
assert any(PISTAS_EN_DIALOGO[2] in m for m in dicho), dicho
distancias = {a.nombre: math.dist(a.centro, sala.pasillo.center) for a in g.aliens if sala.conduce(a)}
assert distancias, "hay aliens que vienen"
votar(g, g.jugadores[0], "quedarse")
cuadros(g, 6000)
foto(g, "c_votacion")
# A mitad del contador ninguno ha llegado a la puerta de la sala.
mitad = [math.dist(a.centro, (sala.sala.left, sala.pasillo.centery)) for a in g.aliens if sala.conduce(a)]
assert min(mitad) > 60, f"llegaron antes de tiempo: {min(mitad):.0f} px"
assert any(mitad[i] < list(distancias.values())[i] - 50 for i in range(len(mitad))), "vienen acercándose"
while sala.estado == "votacion":
    cuadros(g, DT)
al_final = [math.dist(a.centro, (sala.sala.left, sala.pasillo.centery)) for a in g.aliens if sala.conduce(a)]
print(f"al acabar el contador, el más cercano está a {min(al_final):.0f} px de la sala")
assert min(al_final) < 80, "al acabar el contador llegan a la puerta de la sala"
cuadros(g, 600)
foto(g, "d_desenlace")
final, resultado = terminar(g, sala)
assert (final, resultado) == ("quedarse", "derrota"), (final, resultado)
print("final con 1 voto por quedarse:", final)

# == 2. Escapan (más votos por la cápsula): 3 jugadores ======================================
sala = partida(g, 3)
assert sala.estado == "cerrada" and sala.puerta in g.mundo.paredes, "la ronda siguiente empieza cerrada"
# (el tercer puesto juega con mando: sin él no se mueve ni vota)
g.jugadores[2].con_mando = g.jugadores[2].puede_moverse = True
abrir(g, sala)
entrar(g, sala)
votar(g, g.jugadores[0], "escapar")
votar(g, g.jugadores[1], "escapar")
votar(g, g.jugadores[2], "quedarse")
cuadros(g, 50)
assert sala.acortado and sala.quedan_ms <= max(VOTACION["segundos_si_votaron_todos"] * 1000,
                                                sala.quedan_ms), "votaron todos: se acorta"
final, resultado = terminar(g, sala)
assert (final, resultado) == ("escaparon", "victoria"), (final, resultado)
print("final con 2 contra 1 por escapar:", final)

# == 3. Nadie vota ===========================================================================
sala = partida(g)
abrir(g, sala)
entrar(g, sala)
final, resultado = terminar(g, sala)
assert (final, resultado) == ("nadie", "derrota"), (final, resultado)
print("final sin votos:", final)

# == 4. Empate: se quedan =====================================================================
sala = partida(g)
abrir(g, sala)
entrar(g, sala)
votar(g, g.jugadores[0], "escapar")
votar(g, g.jugadores[1], "quedarse")
final, resultado = terminar(g, sala)
assert final == "quedarse", final
print("final con empate:", final)

# == 5. Escapan sin entrar ====================================================================
sala = partida(g)
abrir(g, sala)
for j in g.jugadores:
    poner(j, g.mision.capsula.center)
cuadros(g, 200)
assert (g.mision.final, g.mision.resultado) == ("sin_entrar", "victoria"), (g.mision.final, g.mision.resultado)
print("final sin entrar:", g.mision.final)

# == 6. Feria: el reloj no corre mientras votan ===============================================
sala = partida(g, feria=True)
assert g.modo_feria and g.tiempo_restante_ms is not None, "la Feria tiene reloj"
abrir(g, sala)
entrar(g, sala)
antes = g.tiempo_restante_ms
cuadros(g, 3000)
assert g.tiempo_restante_ms == antes, "con los niños el reloj de la Feria se detiene"
final, _ = terminar(g, sala)
assert final == "nadie", final
print("feria: el reloj se detuvo y terminó con", final)

# == 7. La escena de cada final se dibuja ======================================================
from screens import final as escenas
pantalla = pygame.Surface((1280, 720))
for clave in ("sin_entrar", "escaparon", "quedarse", "nadie"):
    total = escenas.intro_ms(clave)
    for t in range(0, total + 2000, 900):
        escenas.dibujar(pantalla, clave in ("sin_entrar", "escaparon"), t, g.jugadores, clave)
    escenas.dibujar(pantalla, False, 500, g.jugadores, clave, de_fondo=True)
    pygame.image.save(pantalla, os.path.join(CARPETA, f"final_{clave}.png"))
print("escenas de los finales: OK")

# == 8. Un mapa sin sala oculta: nada cambia ======================================================
objetos_mapa.mapa_activo = lambda: "Nave"
sala = partida(g)
assert geometria(g.mundo) is None
assert not sala.activa, "Nave no tiene sala oculta"
g.mision.abrir_puerta()
g.mision.empezar_huida()
cuadros(g, 500)
assert sala.estado == "cerrada"

print(f"capturas en {CARPETA}")
print("OK prueba_sala_secreta")
