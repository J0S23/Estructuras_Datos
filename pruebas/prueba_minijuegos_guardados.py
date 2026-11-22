"""Los minijuegos a medias se guardan, y los mensajes que dicen qué hacer
duran más (Diego, nov 21).

    python pruebas/prueba_minijuegos_guardados.py

1. Una consola: se abre, se juega un poco, se cierra (con la tecla del árbol)
   y al volver es EL MISMO minijuego, igual que como quedó. Mientras J1 lo
   tiene abierto, J2 no puede entrar. Al ganarlo se borra: la siguiente vez,
   uno nuevo. Igual la cápsula (cables) y la planta (abono, con lo que lleva).
2. Los mensajes: uno largo dura más que uno corto; uno que dice qué hacer
   ("[E] ...", "tengo que...") dura al menos INSTRUCCION_MIN_MS; otro aviso
   que llega mientras tanto espera a que se lea y sale después.
"""

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
from juego import objetos_mapa, tareas
from misiones import minijuegos
from entidades import jugador as J

objetos_mapa.mapa_activo = lambda: "Nave"
DT = 1000 // 60


def nueva_partida():
    random.seed(5)
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
    juego.admin_invencible = True
    red = juego.nexus
    red.reloj_rumor_ms = red.reloj_normal_ms = 10 ** 9
    return juego


def frames(juego, n):
    for _ in range(n):
        juego._actualizar_partida(DT)


def parar_en(jugador, punto):
    jugador.personaje.hitbox.center = (int(punto[0]), int(punto[1]))
    jugador.personaje.sync_sprite_from_hitbox()


def estado(mini):
    datos = dict(mini.a_red())
    for clave in ("t", "error_ms", "fin_ms", "_giros", "_golpes", "_movidas", "fases", "retomado"):
        datos.pop(clave, None)      # (lo que corre solo con el reloj)
    return datos


# -- 1. Minijuegos guardados ------------------------------------------------------------------
juego = nueva_partida()
mision = juego.mision
j1, j2 = juego.jugadores
mision.abrir_puerta()
frames(juego, 2)
for j in (j1, j2):
    j.objetos.add("decodificador")

consola = mision.consolas[0]
parar_en(j1, consola["rect"].center)
assert tareas.intentar(juego, j1)
mini = tareas.de(j1)
assert isinstance(mini, minijuegos.Senal)
for accion in ("derecha", "derecha", "arriba", "derecha"):
    tareas.tecla(juego, j1, accion)
frames(juego, 3)
antes = estado(mini)
juego._manejar_tecla(j1.teclas["habilidades"][0])       # se sale
assert tareas.de(j1) is None
if j1.panel is not None:
    j1.cerrar_panel()
frames(juego, 30)
# J2 al lado de la misma consola: con J1 adentro no puede (después, sí).
parar_en(j2, consola["rect"].center)
assert tareas.intentar(juego, j1) and tareas.de(j1) is mini, "al volver no es el mismo minijuego"
assert estado(mini) == antes, "al volver cambió el minijuego"
assert tareas.intentar(juego, j2) and tareas.de(j2) is None, "J2 entró al minijuego que J1 tenía abierto"
assert "Alguien ya está" in j2.mensaje, j2.mensaje
print("1a. consola: salir y volver deja el mismo minijuego como estaba; otro no entra mientras: OK")

# Ganarlo lo borra: la próxima vez es uno nuevo (en otra consola, por si esta ya se apagó).
mini._ganar()
frames(juego, minijuegos.FIN_MS // DT + 3)
assert tareas.de(j1) is None and consola["progreso"] >= 1
assert all(m is not mini for m in juego.minis_guardados.values()), "el minijuego ganado sigue guardado"
otra = mision.consolas[1]
parar_en(j1, otra["rect"].center)
assert tareas.intentar(juego, j1)
assert tareas.de(j1) is not mini
j1.cerrar_panel()
print("1b. ganarlo lo borra; otra consola, otro minijuego: OK")

# La planta: el abono sigue con sus aciertos.
gp = juego.guardia_planta
if gp is not None and gp.planta is not None:
    from misiones.guardia import es_biomante
    p = gp.planta
    jb = next((j for j in juego.jugadores if es_biomante(j)), j2)
    parar_en(jb, p["rect"].center)
    if gp.puede_cultivar(jb) and tareas.intentar(juego, jb) and isinstance(tareas.de(jb), minijuegos.Abono):
        abono = tareas.de(jb)
        abono.aciertos = 1
        jb.cerrar_panel()
        frames(juego, 10)
        assert tareas.intentar(juego, jb) and tareas.de(jb) is abono and abono.aciertos == 1
        jb.cerrar_panel()
        print("1c. abono: al volver sigue con sus aciertos: OK")

# Otra partida empieza sin minijuegos guardados.
juego2 = nueva_partida()
assert juego2.minis_guardados == {}

# -- 2. Mensajes ------------------------------------------------------------------------------
corto = J.duracion_mensaje("Recogí una pieza")
largo = J.duracion_mensaje("Veo en NEXUS que @kevin desmintió un rumor sobre la caja de fusibles del pasillo")
instruccion = J.duracion_mensaje("¡Lo de la caja de fusibles es verdad! Tengo que arreglarlo: [E] Subir los breakers.")
assert corto < largo <= J.MENSAJE_MAX_MS, (corto, largo)
assert instruccion >= J.INSTRUCCION_MIN_MS > J.DURACION_MENSAJE_MS * 2, instruccion
assert J.es_instruccion("Necesito Reparación básica ([Q])") and not J.es_instruccion("Recogí una pieza")

j = juego2.jugadores[0]
j.avisar("¡Lo de la caja de fusibles es verdad! Tengo que arreglarlo: [E] Subir los breakers.")
texto = j.mensaje
j.actualizar_mensaje(1000)
j.avisar("Recogí una pieza")                 # llega en medio: espera
assert j.mensaje == texto and j.mensajes_pendientes, "un aviso cualquiera tapó la instrucción"
j.actualizar_mensaje(J.INSTRUCCION_PROTEGIDA_MS)
assert j.mensaje == "Recogí una pieza", "lo que esperaba no salió después"
j.avisar("Tengo que mantener la tecla para cambiar los fusibles.")
j.avisar("Necesito al Tecnomante o un decodificador")    # otra instrucción sí la reemplaza
assert j.mensaje == "Necesito al Tecnomante o un decodificador"
# Sin nada más, la instrucción dura lo suyo.
for _ in range(int(J.INSTRUCCION_MIN_MS // DT) - 2):
    j.actualizar_mensaje(DT)
assert j.mensaje, "la instrucción se fue antes de INSTRUCCION_MIN_MS"
print(f"2. mensajes: corto {corto} ms, largo {largo} ms, instrucción {instruccion} ms; "
      "un aviso no tapa una instrucción recién salida: OK")
print("OK prueba_minijuegos_guardados")
