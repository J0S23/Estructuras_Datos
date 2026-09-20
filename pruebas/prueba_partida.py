"""Prueba de humo de una partida completa, sin abrir ventana.

    python pruebas/prueba_partida.py

Recorre las cinco zonas con los dos jugadores, desbloquea las dos ramas del
árbol de habilidades del candidato, baja por un árbol de diálogo y termina la
ronda. Guarda capturas en pruebas/capturas/ para poder revisar a ojo que los
paneles se ven bien.

Usa el driver "dummy" de SDL, así que corre sin monitor y sirve para
comprobar cambios rápido antes de abrir el juego de verdad.
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

import App
from data.roles import ROLES

g = App.Game()

# La partida ya no arranca sola: hay que pasar por cantidad y selección de rol.
# Se hace con las mismas teclas que usaría un jugador, para que la prueba
# recorra el flujo de verdad y no un atajo interno.
g._activar_opcion_menu("jugar")
for _ in range(80):
    if g.transitions.is_idle(): break
    g.transitions.update(g, 33)
g.current_screen = "cantidad"
g._manejar_tecla(pygame.K_RETURN)          # 2 jugadores, la primera opción
for _ in range(80):
    if g.transitions.is_idle(): break
    g.transitions.update(g, 33)
g.current_screen = "roles"
g.seleccion_roles[0]["cursor"] = 0         # Ciudadano
g._manejar_tecla(pygame.K_e)
g.seleccion_roles[1]["cursor"] = 1         # Candidato
g._manejar_tecla(pygame.K_RETURN)
def avanzar():
    for _ in range(80):
        if g.transitions.is_idle(): break
        g.transitions.update(g, 33)
avanzar()
g.current_screen = "partida"

ciu, can = g.jugadores
print("jugadores:", [(j.rol, j.controles_nombre) for j in g.jugadores])
print("zonas:", [(z["clave"], z["tipo"], z["roles"]) for z in g.zonas])
print("ABB nodos:", g.arbol_publicaciones.contar(), "| dudosas:", len(g.publicaciones_dudosas()))

def ir_a(jugador, clave):
    z = [x for x in g.zonas if x["clave"] == clave][0]
    jugador.personaje.hitbox.center = z["rect"].center
    jugador.personaje.sync_sprite_from_hitbox()
    jugador.zona_cerca = g.zona_bajo(jugador)
    assert jugador.zona_cerca is not None, f"{jugador.rol} no detecta la zona {clave}"
    return z

def cap(nombre):
    g._dibujar(); pygame.display.flip()
    pygame.image.save(g.screen, os.path.join(OUT, nombre))

# ---------- 1. Ciudadano: verificar en el tablon ----------
ir_a(ciu, "tablon")
g._tecla_en_partida(pygame.K_e)
assert ciu.ocupado, "no abrio el panel de verificacion"
print("\nTABLON abierto:", ciu.panel["titulo"], "| opciones:", [o["texto"] for o in ciu.panel["opciones"]])
cap("a_tablon.png")
antes = ciu.puntos
g._tecla_en_partida(pygame.K_s)   # baja el cursor
g._tecla_en_partida(pygame.K_e)   # confirma
print("  resultado:", ciu.panel["titulo"], "| puntos", antes, "->", ciu.puntos)
cap("b_resultado.png")
g._tecla_en_partida(pygame.K_e)   # cierra
assert not ciu.ocupado

# ---------- 2. Candidato: acusacion sin habilidades ----------
ir_a(can, "plaza")
g._tecla_en_partida(pygame.K_RETURN)
print("\nPLAZA sin habilidades:", [o["texto"] for o in can.panel["opciones"]])
g._tecla_en_partida(pygame.K_RETURN)  # elige la primera
g._tecla_en_partida(pygame.K_RETURN)  # cierra resultado

# ---------- 3. Candidato: arbol de habilidades ----------
can.puntos = 120
g._tecla_en_partida(pygame.K_RSHIFT)
assert can.panel["tipo"] == "habilidades"
print("\nHABILIDADES opciones:", [n.clave for n in can.arbol.opciones()])
cap("c_habilidades.png")
g._tecla_en_partida(pygame.K_RETURN)  # desbloquea DEBATE
print("  tras desbloquear:", [n.clave for n in can.arbol.desbloqueadas()], "| puntos:", can.puntos)
print("  nuevas opciones:", [n.clave for n in can.arbol.opciones()])
cap("d_habilidades_2.png")
g._tecla_en_partida(pygame.K_DOWN)
g._tecla_en_partida(pygame.K_RETURN)  # desbloquea ACORRALAR
print("  camino final:", [n.clave for n in can.arbol.desbloqueadas()], "| puntos:", can.puntos)
g._tecla_en_partida(pygame.K_RSHIFT)  # cierra
assert not can.ocupado

# ---------- 4. Candidato: acusacion CON habilidades ----------
ir_a(can, "plaza")
g._tecla_en_partida(pygame.K_RETURN)
print("\nPLAZA con DEBATE+ACORRALAR:", [o["texto"] for o in can.panel["opciones"]])
cap("e_acusacion.png")
g._tecla_en_partida(pygame.K_RETURN); g._tecla_en_partida(pygame.K_RETURN)

# ---------- 5. Candidato: emisora (rama cerrada) ----------
ir_a(can, "emisora")
g._tecla_en_partida(pygame.K_RETURN)
print("\nEMISORA (rama PROPUESTA cerrada):", [o["texto"] for o in can.panel["opciones"]])
g._tecla_en_partida(pygame.K_RETURN); g._tecla_en_partida(pygame.K_RETURN)

# ---------- 6. Ciudadano: reportar ----------
ir_a(ciu, "junta")
g._tecla_en_partida(pygame.K_e)
print("\nJUNTA opciones:", len(ciu.panel["opciones"]))
cap("f_reporte.png")
antes = ciu.puntos; nodos_antes = g.arbol_publicaciones.contar()
g._tecla_en_partida(pygame.K_e)
print("  ->", ciu.panel["titulo"], "| puntos", antes, "->", ciu.puntos,
      "| ABB", nodos_antes, "->", g.arbol_publicaciones.contar())
g._tecla_en_partida(pygame.K_e)

# ---------- 7. Dialogo ----------
ir_a(ciu, "casa")
g._tecla_en_partida(pygame.K_e)
print("\nDIALOGO:", ciu.panel["titulo"])
cap("g_dialogo.png")
for paso in range(5):
    if not ciu.ocupado: break
    if not ciu.panel.get("opciones"): 
        g._tecla_en_partida(pygame.K_e); break
    g._tecla_en_partida(pygame.K_e)
print("  recorrido sin romperse, ocupado:", ciu.ocupado)
if ciu.ocupado: g._tecla_en_partida(pygame.K_e)

# ---------- 8. El otro sigue caminando mientras uno lee ----------
ir_a(ciu, "tablon")
g._tecla_en_partida(pygame.K_e)
pos_antes = (can.personaje.x, can.personaje.y)
import collections
teclas = collections.defaultdict(bool); teclas[pygame.K_RIGHT] = True
for _ in range(20):
    can.actualizar(teclas, g.mundo.colisiona)
    ciu.actualizar(teclas, g.mundo.colisiona)
print("\ncandidato se movio mientras el ciudadano lee:", (can.personaje.x, can.personaje.y) != pos_antes)
print("ciudadano quieto con panel abierto:", ciu.ocupado)
cap("h_split.png")
g._tecla_en_partida(pygame.K_e); g._tecla_en_partida(pygame.K_e)

# ---------- 9. Reloj y resultados ----------
g.tiempo_restante_ms = 500
g._actualizar_partida(1000)
avanzar(); g.current_screen = "resultados"
cap("i_resultados.png")
print("\nronda termino, pantalla:", g.current_screen)

# ---------- 10. Panel del ABB ----------
g.current_screen = "arbol"; cap("j_abb.png")

# ---------- 11. Arbol del influencer ----------
# El rol todavia no es jugable, pero su arbol ya existe: se comprueba que se
# construya bien y que el panel lo dibuje sin romperse, incluido el nodo al
# que le falta el arte (CRISIS).
from jugador import Jugador
inf = Jugador(can.personaje, "Influencer", puesto=2)
inf.puntos = 200
assert not inf.arbol.vacio, "el arbol del influencer no se construyo"
print("\nINFLUENCER niveles:", [n.clave for n, _ in inf.arbol.por_niveles()])
inf.arbol.desbloquear("TENDENCIA", inf.puntos)
inf.abrir_panel({"tipo": "habilidades"})
g.jugadores = [ciu, inf]
g.current_screen = "partida"
cap("k_influencer.png")
print("  camino:", [n.clave for n in inf.arbol.desbloqueadas()])
print("  panel dibujado sin romperse")

# Ninguna zona debe quedar encerrada
g.jugadores = [ciu, can]
malas = g.mundo.zonas_inalcanzables(g.zonas, ciu.hitbox.topleft)
assert not malas, f"zonas inalcanzables: {[z['clave'] for z in malas]}"
print("\nzonas inalcanzables: ninguna")

print("TODO OK")
