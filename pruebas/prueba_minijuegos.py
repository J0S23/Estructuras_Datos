"""Minijuegos de las tareas y noticias verdaderas de NEXUS (nov 20).

    python pruebas/prueba_minijuegos.py

1. Cada minijuego (misiones/minijuegos.py) se puede ganar, en normal y en
   fácil, con muchas semillas; los cables y las palancas nunca empiezan
   resueltos.
2. Las tareas (juego/tareas.py) en el juego local: apagar una consola (con la
   tecla de interactuar de verdad y las flechas), encender la caja de
   fusibles en un apagón, reparar la cápsula. Al ganar pasa lo mismo que al
   llenar la barra; con `minijuegos = False` (red) no se abre nada.
3. Noticias verdaderas (redes/nexus.py): las publica un prisionero, ponen el
   candado en un casillero (no se puede esconder ahí), la cuenta para
   volverse viral empieza cuando le llega a un jugador, en el lugar se
   arregla con la ganzúa, y con la foto se confirma (se propaga en verde).
   En red (sin minijuegos) se arregla al llegar.
4. Compartir: la charla de Red y una noticia sin verificar no dan puntos ni
   cambian la confianza; reportar a quien publicó una noticia es injusto.
Capturas en pruebas/capturas/minijuego_*.png.
"""

import os
import sys
import itertools
import random

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

import pygame
pygame.init()
OUT = os.path.join(RAIZ, "pruebas", "capturas")
os.makedirs(OUT, exist_ok=True)

from juego import app as App
from juego import objetos_mapa, tareas
from misiones import minijuegos
from redes import celular as logica
from redes.nexus import VERDE, ROJO, GRIS
from data.nexus import NOTICIAS, PUNTOS_ARREGLAR, PUNTOS_CONFIRMAR
from misiones.mision import PIEZAS_NECESARIAS
objetos_mapa.mapa_activo = lambda: "Nave"
DT = 1000 // 60


class Teclas(dict):
    def __getitem__(self, k):
        return self.get(k, False)


pygame.key.get_pressed = lambda: Teclas()


# -- Cómo gana cada minijuego un jugador perfecto ------------------------------------------

def mover_cursor(mini, tecla, actual, meta):
    """Lleva el cursor (x, y) a `meta` con las flechas."""
    x, y = actual
    while x < meta[0]:
        tecla("derecha"); x += 1
    while x > meta[0]:
        tecla("izquierda"); x -= 1
    while y < meta[1]:
        tecla("abajo"); y += 1
    while y > meta[1]:
        tecla("arriba"); y -= 1


def resolver(mini, tecla, esperar):
    """Juega `mini` hasta ganarlo. `tecla(accion)` y `esperar(ms)`."""
    if isinstance(mini, minijuegos.Cables):
        # El camino armado es el de la rotación 0: deja cada pieza así.
        for c in sorted(mini.base):
            if mini.ganado:
                break
            mover_cursor(mini, tecla, tuple(mini.cursor), c)
            while mini.rot[c] % 4 and not mini.ganado:
                tecla("ok")
    elif isinstance(mini, minijuegos.Interruptores):
        n = mini.n
        for golpes in itertools.product((0, 1), repeat=n):
            prueba = list(mini.arriba)
            for i, g in enumerate(golpes):
                if g:
                    for j in (i - 1, i, i + 1):
                        if 0 <= j < n:
                            prueba[j] = not prueba[j]
            if all(prueba):
                break
        for i, g in enumerate(golpes):
            if g and not mini.ganado:
                while mini.cursor != i:
                    tecla("derecha")
                tecla("ok")
    elif isinstance(mini, minijuegos.Senal):
        while not mini.ganado:
            f, a = mini.objetivo
            while mini.f < f: tecla("derecha")
            while mini.f > f: tecla("izquierda")
            while mini.a < a: tecla("arriba")
            while mini.a > a: tecla("abajo")
            tecla("ok")
    elif isinstance(mini, minijuegos.Abono):
        for _ in range(3000):
            if mini.ganado:
                break
            if mini.caida is None and abs(mini.x_saco()) <= 0.12:
                tecla("ok")
            esperar(DT)
    elif isinstance(mini, minijuegos.Ganzua):
        a, b = mini.ZONA
        for _ in range(3000):
            if mini.ganado:
                break
            altura = mini.altura(mini.puestos)
            if a + 0.03 <= altura <= b - 0.03:
                tecla("ok")
            esperar(DT)
    assert mini.ganado, type(mini).__name__


# -- 1. Cada minijuego, solo ------------------------------------------------------------------
for tipo, clase in minijuegos.TIPOS.items():
    for facil in (False, True):
        for semilla in range(40):
            mini = minijuegos.crear(tipo, facil, random.Random(semilla))
            if tipo == "cables":
                assert not mini._conectado(), "los cables empezaron conectados"
            if tipo == "interruptores":
                assert not all(mini.arriba), "las palancas empezaron arriba"
            resolver(mini, mini.tecla, mini.actualizar)
            assert not mini.listo
            mini.actualizar(minijuegos.FIN_MS)
            assert mini.listo
    # Un error se ve (y en la ganzúa, se cae el pin anterior).
print(f"1. los {len(minijuegos.TIPOS)} minijuegos se ganan (normal y fácil, 40 semillas): OK")

mini = minijuegos.Ganzua(rng=random.Random(3))
mini.fases[0] = -1.57                          # abajo del todo: fuera de la línea
assert mini.tecla("ok") == "fallo" and mini.error_ms > 0 and mini.puestos == 0
mini = minijuegos.Senal(rng=random.Random(3))
assert mini.tecla("ok") == "fallo"


# -- La partida ---------------------------------------------------------------------------
def nueva_partida():
    juego = App.Game()

    def avanzar():
        for _ in range(80):
            if juego.transitions.is_idle():
                break
            juego.transitions.update(juego, 33)
    juego._activar_opcion_menu("jugar"); avanzar(); juego.current_screen = "cantidad"
    juego._manejar_tecla(pygame.K_RETURN); avanzar(); juego.current_screen = "roles"
    juego._manejar_tecla(pygame.K_e); juego._manejar_tecla(pygame.K_RETURN)
    avanzar(); juego.current_screen = "partida"
    juego.saltar_tutorial()
    juego.presentacion = None
    juego.quitar_cambiaformas()
    for a in juego.aliens:
        a.hitbox.topleft = (5, 5)
        a.descanso_ms = 10 ** 9
    if juego.eventos is not None:
        juego.eventos.reloj_ms = 10 ** 9
    juego.admin_invencible = True                # (que ningún alien interrumpa)
    red = juego.nexus
    red.reloj_rumor_ms = red.reloj_normal_ms = 10 ** 9
    return juego


def frames(juego, n):
    for _ in range(n):
        juego._actualizar_partida(DT)


def jugar_tarea(juego, jugador, por_teclas=False):
    """Resuelve el minijuego abierto del jugador (con las teclas del juego o
    con `tareas.tecla`) y espera a que se cierre."""
    mini = tareas.de(jugador)
    assert mini is not None, "no se abrió el minijuego"

    def tecla(accion):
        if por_teclas:
            juego._manejar_tecla(jugador.teclas[accion if accion != "ok" else "interactuar"][0])
        else:
            tareas.tecla(juego, jugador, accion)
    resolver(mini, tecla, lambda ms: frames(juego, max(1, ms // DT)))
    frames(juego, minijuegos.FIN_MS // DT + 3)
    assert tareas.de(jugador) is None, "el minijuego no se cerró al ganar"
    return mini


def foto(juego, nombre):
    juego._dibujar()
    pygame.image.save(juego.screen, os.path.join(OUT, f"minijuego_{nombre}.png"))


def parar_en(jugador, punto):
    jugador.personaje.hitbox.center = (int(punto[0]), int(punto[1]))
    jugador.personaje.sync_sprite_from_hitbox()


# -- 2. Tareas con minijuego --------------------------------------------------------------
juego = nueva_partida()
assert juego.minijuegos
red = juego.nexus
mision = juego.mision
j1, j2 = juego.jugadores
mision.abrir_puerta()
frames(juego, 2)
assert mision.fase == "sabotaje", mision.fase
for j in (j1, j2):
    j.objetos.add("decodificador")

# Consola, con la tecla de interactuar de verdad y las flechas.
consola = mision.consolas[0]
parar_en(j1, consola["rect"].center)
juego._manejar_tecla(j1.teclas["interactuar"][0])
mini = tareas.de(j1)
assert isinstance(mini, minijuegos.Senal), mini
assert j1.panel and j1.panel["tipo"] == "tarea"
x0 = j1.hitbox.x
juego._manejar_tecla(j1.teclas["izquierda"][0])
frames(juego, 3)
assert j1.hitbox.x == x0, "se movió jugando el minijuego"
foto(juego, "a_consola")
puntos = j1.puntos
jugar_tarea(juego, j1, por_teclas=True)
assert consola["progreso"] >= 1 and j1.puntos > puntos, (consola["progreso"], j1.puntos, puntos)

# Cerrar sin ganar: la tecla del árbol de habilidades lo cierra y no pasa nada.
otra = mision.consolas[1]
parar_en(j2, otra["rect"].center)
assert tareas.intentar(juego, j2)
juego._manejar_tecla(j2.teclas["habilidades"][0])
assert tareas.de(j2) is None and otra["progreso"] < 1
assert tareas.intentar(juego, j2)
jugar_tarea(juego, j2)
assert otra["progreso"] >= 1
print("2a. consolas: se abren con la tecla, no se camina, flechas y Enter juegan, ganar las apaga: OK")

# Apagón: la caja de fusibles buena.
eventos = juego.eventos
eventos.lanzar("apagon")
frames(juego, 2)
assert juego.sin_luz
caja = eventos.caja
parar_en(j1, caja.get("pie") or caja["rect"].center)
assert eventos.caja_cerca(j1) is not None
assert tareas.intentar(juego, j1)
assert isinstance(tareas.de(j1), minijuegos.Interruptores)
foto(juego, "b_fusibles")
jugar_tarea(juego, j1)
frames(juego, 2)
assert not juego.sin_luz, "no volvió la luz"
print("2b. apagón: la caja de fusibles se enciende con las palancas: OK")

# La cápsula (con planos y piezas).
for c in mision.consolas:
    c["progreso"] = 1.0
frames(juego, 3)
mision.fase = "capsula"
mision.piezas_entregadas = PIEZAS_NECESARIAS
red.planos = True
j2.objetos.add("kit")
parar_en(j2, mision.capsula.center)
lista, aviso = mision.capsula_para(j2)
assert lista, aviso
assert tareas.intentar(juego, j2)
assert isinstance(tareas.de(j2), minijuegos.Cables)
foto(juego, "c_capsula")
jugar_tarea(juego, j2)
assert mision.reparacion >= 1 and mision.fase == "huida", (mision.reparacion, mision.fase)
print("2c. cápsula: se repara conectando los cables y empieza la huida: OK")

# Sin minijuegos (en red): no se abre nada.
juego = nueva_partida()
juego.minijuegos = False
juego.mision.abrir_puerta()
frames(juego, 2)
j1 = juego.jugadores[0]
j1.objetos.add("decodificador")
parar_en(j1, juego.mision.consolas[0]["rect"].center)
assert not tareas.intentar(juego, j1) and tareas.de(j1) is None
print("2d. sin minijuegos (red), las tareas siguen siendo mantener la tecla: OK")


# -- 3. Noticias verdaderas ---------------------------------------------------------------
def noticia(lugar):
    return next(n for n in NOTICIAS if n["lugar"] == lugar)


juego = nueva_partida()
red = juego.nexus
j1, j2 = juego.jugadores
assert red.con_noticias
pub = red.lanzar_noticia(noticia("escondite"))
assert pub is not None and pub.tipo == "noticia" and not pub.falsa
assert not red.es_bot(pub.autor), "la publicó un bot"
escondite = pub.efecto["escondite"]
assert escondite["candado"] and escondite["rect"].center == pub.lugar
# No se puede esconder ahí.
parar_en(j1, (escondite["rect"].centerx, escondite["rect"].bottom + 40))
frames(juego, 2)
foto(juego, "g_candado")
parar_en(j1, escondite["rect"].center)
juego.minijuegos = False
juego._manejar_tecla(j1.teclas["interactuar"][0])
assert not j1.escondido if hasattr(j1, "escondido") else escondite["ocupante"] is None
assert escondite["ocupante"] is None, "se escondió en un casillero con candado"
juego.minijuegos = True
parar_en(j1, (5000, 5000))
# La cuenta para volverse viral no corre mientras no le llegue a nadie.
red.propagaciones = [p for p in red.propagaciones if p.pub is not pub]
frames(juego, 120)
assert pub.viral_ms == 0, pub.viral_ms
assert red.progreso_viral(pub) == 0
red.reloj_rumor_ms = 10 ** 9
pub.alcanzados.add(red.nodo_de(j2))
frames(juego, 60)
assert pub.viral_ms > 0, "le llegó a un jugador y no empezó la cuenta"
# En el celular se ve como un rumor: misión "Por verificar", con el lugar.
assert pub in logica.misiones(red, j2)
assert logica.estado_mision(red, j2, pub) == "pendiente"
j2.abrir_panel(logica._post(juego, j2, pub))
acciones = [a for _, a in j2.panel["opciones"]]
assert acciones[0] == "investigar" and "rastrear" in acciones, acciones
foto(juego, "d_noticia_post")
j2.cursor = 0
logica.confirmar(juego, j2)                      # "Ir a verificarlo"
assert red.investigando.get(j2) is pub
j2.cerrar_panel()
# En el lugar: se sabe que es verdad, la pista dice qué hacer.
parar_en(j2, escondite["rect"].center)
frames(juego, 2)
assert red.noticia_para(j2) is pub and not pub.arreglada
assert pub not in red.evidencias[j2], "con minijuegos no se arregla solo"
assert "verdad" in j2.mensaje, j2.mensaje
assert red.pista(j2) == noticia("escondite")["pista"]
puntos = j2.puntos
assert tareas.intentar(juego, j2)
assert isinstance(tareas.de(j2), minijuegos.Ganzua)
foto(juego, "e_ganzua")
jugar_tarea(juego, j2)
assert pub.arreglada and not escondite["candado"] and pub in red.evidencias[j2]
assert j2.puntos == puntos + PUNTOS_ARREGLAR, (j2.puntos, puntos)
assert red.investigando.get(j2) is None
assert logica.estado_mision(red, j2, pub) == "foto"
# Para el otro, ya está arreglada: no tiene nada que hacer.
pub.alcanzados.add(red.nodo_de(j1))
assert logica.estado_mision(red, j1, pub) == "arreglada"
assert not logica.es_mision_activa(red, pub, j1) and logica.es_mision_activa(red, pub, j2)
assert pub not in red.por_verificar_de(j1) and pub in red.por_verificar_de(j2)
# Confirmarla con la foto (recortada).
j2.abrir_panel(logica._post(juego, j2, pub))
assert j2.panel["opciones"][0][1] == "confirmar", j2.panel["opciones"]
j2.cursor = 0
logica.confirmar(juego, j2)
assert j2.panel["vista"] == "ubicacion"
foto(juego, "f_confirmar")
j2.cursor = 1
puntos = j2.puntos
logica.confirmar(juego, j2)
assert pub.desmentida and j2.panel["vista"] == "mensaje"
assert j2.puntos == puntos + PUNTOS_CONFIRMAR
assert red.stats[j2]["confirmados"] == 1
prop = [p for p in red.propagaciones if p.pub.desmiente is pub]
assert prop and prop[0].color == VERDE
assert logica.estado_mision(red, j2, pub) == "hecha"
assert any(p.tipo == "confirmacion" for p in logica.equipo(red, j2))
frames(juego, 400)
print("3a. noticia del candado: un prisionero, candado, cuenta viral desde que llega, "
      "ganzúa, confirmación en verde: OK")

# Viral: una noticia no pinta a nadie de rojo.
pub2 = red.lanzar_noticia(noticia("fusibles"))
assert pub2 is not None and pub2.lugar is not None
pub2.alcanzados.add(red.nodo_de(j1))
rojos = sum(red.color(n) == ROJO for n in red._presos())
pub2.viral_ms = red.limite_viral() - 5
frames(juego, 2)
assert pub2.viral and red.virales == 0
assert sum(red.color(n) == ROJO for n in red._presos()) <= rojos
assert "viral" in j1.mensaje, j1.mensaje

# Reportar a quien la publicó: es un prisionero de verdad.
texto, puntos = red.reportar(j1, pub2.autor, pub2)
assert puntos < 0 and "era cierto" in texto, texto
print("3b. noticia viral: solo se riega (sin rojos); reportar a su autor no ayuda: OK")

# En red (sin minijuegos): se arregla al llegar.
juego = nueva_partida()
juego.minijuegos = False
red = juego.nexus
j1 = juego.jugadores[0]
pub = red.lanzar_noticia(noticia("terminal"))
assert pub is not None
pub.alcanzados.add(red.nodo_de(j1))
parar_en(j1, pub.lugar)
frames(juego, 2)
assert pub.arreglada and pub in red.evidencias[j1]
print("3c. en red (sin minijuegos) la noticia se arregla al llegar: OK")

# El timer de rumores también lanza noticias.
juego = nueva_partida()
red = juego.nexus
red.rng = random.Random(1)
for _ in range(12):
    red.reloj_rumor_ms = 0
    frames(juego, 1)
    for p in red.rumores_activos():
        p.desmentida = True
    for p in red.noticias_activas():
        p.desmentida = True
tipos = [p.tipo for p in red.publicaciones if p.tipo in ("rumor", "noticia")]
assert "noticia" in tipos and "rumor" in tipos, tipos
print(f"3d. a Misiones llegan rumores y noticias ({tipos.count('rumor')} y {tipos.count('noticia')} "
      f"de {len(tipos)}): OK")


# -- 4. Compartir -------------------------------------------------------------------------
juego = nueva_partida()
red = juego.nexus
j1 = juego.jugadores[0]
normal = red.publicar_normal()
assert normal is not None
verdes = sum(red.color(n) == VERDE for n in red._presos())
texto, puntos = red.compartir(j1, normal)
assert puntos == 0, (texto, puntos)
frames(juego, 400)
assert sum(red.color(n) == VERDE for n in red._presos()) == verdes, "compartir charla cambió la confianza"
copia = red.publicaciones[-1]
texto, puntos = red.compartir(juego.jugadores[1], copia)
assert puntos == 0, "volver a compartir charla dio puntos"
pub = red.lanzar_noticia(noticia("panel"))
grises = sum(red.color(n) == GRIS for n in red._presos())
texto, puntos = red.compartir(j1, pub)
assert puntos == 0 and "verdad" in texto, texto
print("4. compartir charla o una noticia sin verificar: 0 puntos y la confianza no cambia: OK")

print("\nTODO OK")
