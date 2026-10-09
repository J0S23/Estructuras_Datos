"""Prueba de los cuatro roles y sus habilidades, sin ventana.

    python pruebas/prueba_roles.py

Recorre cada habilidad de la lámina de Anny y comprueba que hace lo que dice
data/habilidades.py: terminales, hackeo y escaneo (Tecnomante); piezas,
reparación y señuelo (Forjador); vínculo, regeneración e impulso (Biomante);
sintonía, interceptación y señal falsa (Resonante). También que el árbol manda:
la rama que no se escogió no funciona.

Guarda capturas en pruebas/capturas/ (roles_*.png).
"""

import os, sys, math
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
import pygame; pygame.init()
OUT = os.path.join(RAIZ, "pruebas", "capturas")
os.makedirs(OUT, exist_ok=True)

import App
import objetos_mapa
# Siempre con los valores de data/, no con lo que haya guardado el editor de mapa.
objetos_mapa.USAR_ARCHIVOS = False
import acciones_rol
from data.habilidades import ARBOLES_POR_ROL
from data.roles import ROLES
from Estructuras.arbol_habilidades import construir_arbol

DT = 1000 // 60

# ---------- 1. Los árboles ----------
assert [r["nombre"] for r in ROLES] == list(ARBOLES_POR_ROL)
for rol, datos in ARBOLES_POR_ROL.items():
    arbol = construir_arbol(rol, datos)
    assert arbol.altura() == 2 and len(arbol.por_niveles()) == 3, rol
    for nodo, _ in arbol.por_niveles():
        assert nodo.uso in ("pasiva", "estacion", "activa"), (rol, nodo.clave)
        if nodo.uso == "activa":
            assert nodo.recarga_s > 0, (rol, nodo.clave)
    print(f"{rol}: {[n.clave for n, _ in arbol.por_niveles()]}")
print("cada rol: una base y dos hijas, todas con su forma de uso")

# ---------- 2. Partida ----------
g = App.Game()
def avanzar():
    for _ in range(80):
        if g.transitions.is_idle(): break
        g.transitions.update(g, 33)
g._activar_opcion_menu("jugar"); avanzar(); g.current_screen = "cantidad"
g._manejar_tecla(pygame.K_RETURN); avanzar(); g.current_screen = "roles"
g.seleccion_roles[0]["cursor"] = 0; g._manejar_tecla(pygame.K_e)
g.seleccion_roles[1]["cursor"] = 1; g._manejar_tecla(pygame.K_RETURN)
avanzar(); g.current_screen = "partida"
j1, j2 = g.jugadores
print("\njugadores:", [j.rol for j in g.jugadores])

def cap(nombre):
    g._dibujar(); pygame.display.flip()
    pygame.image.save(g.screen, os.path.join(OUT, nombre))

def frames(n, hasta=None):
    for _ in range(n):
        g._actualizar_partida(DT)
        if hasta and hasta():
            return True
    return False

def poner(jugador, punto):
    jugador.personaje.hitbox.center = (int(punto[0]), int(punto[1]))
    jugador.personaje.sync_sprite_from_hitbox()

def rol(jugador, nombre, hija=None):
    jugador.asignar_rol(nombre)
    jugador.recarga_ms = 0; jugador.efectos.clear(); jugador.piezas = 0
    if hija:
        ok, _, _ = jugador.arbol.desbloquear(hija, 0)
        assert ok, hija

def aliens_lejos():
    for a in g.aliens:
        a.hitbox.center = (1500, 1500); a.descanso_ms = 0; a.punto_ruido = None
        a.rastro.clear(); a.escondite_objetivo = None; a.busqueda_ms = 0

for j in g.jugadores:
    j.invulnerable_ms = 10 ** 9      # que no los atrapen mientras se prueba

# Estaciones bien puestas.
alcanzable = g.mundo.area_alcanzable(j1.spawn)
ocupado = [z["rect"] for z in g.zonas] + [e["rect"] for e in g.escondites]
cosas = g.terminales + g.paneles + g.piezas
for cosa in cosas:
    r = cosa["rect"]
    assert not g.mundo.colisiona(r), f"{cosa.get('clave', 'pieza')} choca con una pared"
    assert any(pygame.Rect(c[0], c[1], 48, 19).colliderect(r) for c in alcanzable), \
        f"{cosa.get('clave', 'pieza')} no se alcanza"
    assert not any(o.colliderect(r) for o in ocupado), f"{cosa.get('clave', 'pieza')} pisa algo"
for i, a in enumerate(cosas):
    for b in cosas[i + 1:]:
        assert not a["rect"].colliderect(b["rect"])
print(f"{len(g.terminales)} terminales, {len(g.paneles)} paneles, {len(g.piezas)} piezas: bien puestos")

terminal = g.terminales[0]
a1, a2 = g.aliens

# ---------- 3. Tecnomante ----------
aliens_lejos()
rol(j1, "Tecnomante")
poner(j1, terminal["rect"].center); g._actualizar_partida(DT)
assert j1.estacion_cerca is terminal
g._tecla_en_partida(pygame.K_e)
assert "mapa" in j1.efectos and "escaneo" not in j1.efectos
print("\nConexión digital: la terminal muestra el mapa de la nave")
cap("roles_a_mapa_terminal.png")

rol(j1, "Tecnomante", "HACKEO"); terminal["recarga_ms"] = 0
a1.hitbox.center = (terminal["rect"].centerx + 200, terminal["rect"].centery)
puntos = j1.puntos
g._tecla_en_partida(pygame.K_e)
assert a1.descanso_ms > 0 and a1.aturdido and j1.puntos == puntos + acciones_rol.PUNTOS_HACKEO
g._actualizar_partida(DT)
assert a1.accion == "DESCANSAR", a1.accion
print("Hackeo básico: apaga al alien cercano ->", [n.texto for n in a1.camino])
cap("roles_b_hackeo.png")
terminal["recarga_ms"] = 0

rol(j1, "Tecnomante", "ESCANEO")
g._tecla_en_partida(pygame.K_f)
assert "escaneo" in j1.efectos and j1.recarga_ms > 0
recarga = j1.recarga_ms
g._tecla_en_partida(pygame.K_f)
assert j1.recarga_ms == recarga, "no debería poder usarla en recarga"
print("Escaneo de sistemas: mapa con conos, y respeta la recarga")
cap("roles_c_escaneo.png")
# El árbol manda: con ESCANEO, la terminal ya no hackea.
terminal["recarga_ms"] = 0; aliens_lejos()
a1.hitbox.center = (terminal["rect"].centerx + 200, terminal["rect"].centery)
poner(j1, terminal["rect"].center); g._actualizar_partida(DT)
g._tecla_en_partida(pygame.K_e)
assert a1.descanso_ms == 0, "HACKEO quedó descartado y aun así hackeó"
print("con ESCANEO escogido, la terminal no hackea (la rama HACKEO quedó cerrada)")

# ---------- 4. Forjador ----------
aliens_lejos()
rol(j2, "Forjador")
pieza = g.piezas[0]
poner(j2, pieza["rect"].center); g._actualizar_partida(DT)
assert pieza["recogida"] and j2.piezas == 1
print("\nIngenio mecánico: recoge la pieza al pasar ->", j2.piezas)
rol(j1, "Tecnomante")
poner(j1, g.piezas[1]["rect"].center); g._actualizar_partida(DT)
assert not g.piezas[1]["recogida"], "solo el Forjador recoge piezas"
cap("roles_d_piezas.png")

panel = g.paneles[0]
poner(j2, panel["rect"].center); g._actualizar_partida(DT)
j2.piezas = 1
g._tecla_en_partida(pygame.K_RETURN)
assert not panel["reparado"], "sin REPARACION no debería reparar"
rol(j2, "Forjador", "REPARACION"); j2.piezas = 1
puntos = j2.puntos
g._actualizar_partida(DT)
g._tecla_en_partida(pygame.K_RETURN)
assert panel["reparado"] and j2.piezas == 0 and j2.puntos == puntos + acciones_rol.PUNTOS_REPARACION
print("Reparación básica: repara el panel con una pieza")
cap("roles_e_panel.png")

rol(j2, "Forjador", "FABRICACION"); j2.piezas = 1
poner(j2, (768, 900)); aliens_lejos()
a2.hitbox.center = (768 + 350, 900 - 300 + 0)
a2.hitbox.center = (1000, 640)
g._tecla_en_partida(pygame.K_RCTRL)
assert len(g.senuelos) == 1 and j2.piezas == 0
g._actualizar_partida(DT)
assert a2.punto_ruido == g.senuelos[0]["pos"], (a2.punto_ruido, a2.accion)
assert a2.accion == "INVESTIGAR"
print("Fabricación improvisada: el señuelo atrae al alien ->", a2.accion)
cap("roles_f_senuelo.png")
g.senuelos.clear()

# ---------- 5. Biomante ----------
aliens_lejos()
rol(j1, "Biomante", "REGENERACION")
poner(j1, (768, 640)); poner(j2, (820, 640))
j2.pulso = 90
g._tecla_en_partida(pygame.K_f)
assert j2.pulso <= 90 - acciones_rol.CALMA_REGENERACION + 1, j2.pulso
print("\nRegeneración dirigida: el pulso del compañero baja a", round(j2.pulso))
cap("roles_g_vinculo.png")

rol(j1, "Biomante", "IMPULSO")
j2.recarga_ms = 12000
g._tecla_en_partida(pygame.K_f)
assert j2.recarga_ms == 0
print("Impulso energético: la habilidad del compañero queda lista")

# Regeneración ayudando a alguien escondido que está en el minijuego.
from minijuego_latidos import MinijuegoLatidos
rol(j1, "Biomante", "REGENERACION")
escondite = g.escondites[0]
poner(j2, escondite["rect"].center); j2.esconderse(escondite)
j2.minijuego = MinijuegoLatidos(80, a1, escondite)
a1.escondite_objetivo = escondite; escondite["revisado_por"] = a1
j2.minijuego.amenaza = 70
poner(j1, (escondite["rect"].centerx + 90, escondite["rect"].centery))
g._tecla_en_partida(pygame.K_f)
assert j2.minijuego.amenaza <= 70 - acciones_rol.AMENAZA_REGENERACION + 0.01
print("Regeneración también le baja la amenaza a quien está escondido:", round(j2.minijuego.amenaza))

# Hackear al alien que revisa el escondite termina el minijuego sin captura.
rol(j1, "Tecnomante", "HACKEO"); terminal["recarga_ms"] = 0
a1.hitbox.center = (escondite["rect"].centerx + 60, escondite["rect"].centery)
poner(j1, terminal["rect"].center)
assert math.hypot(a1.centro[0] - terminal["rect"].centerx,
                  a1.centro[1] - terminal["rect"].centery) <= acciones_rol.RADIO_HACKEO
g._actualizar_partida(DT)
g._tecla_en_partida(pygame.K_e)
g._actualizar_partida(DT)
assert j2.minijuego is None and j2.escondido and j2.veces_atrapado == 0
print("hackear al alien que revisa un escondite salva al de adentro")
j2.salir_del_escondite()

# ---------- 6. Resonante ----------
aliens_lejos()
rol(j2, "Resonante")
poner(j2, (768, 640))
a1.hitbox.center = (300, 420)          # fuera de su pantalla
cap("roles_h_sintonia.png")
print("\nSintonía de señales: flechas hacia los aliens fuera de pantalla (ver captura)")

rol(j2, "Resonante", "INTERCEPCION")
g._tecla_en_partida(pygame.K_RCTRL)
assert "intercepcion" in j2.efectos
a1.hitbox.center = (700, 560)
cap("roles_i_intercepcion.png")
print("Interceptación básica: rutas y decisiones de los aliens")

rol(j2, "Resonante", "EMISION")
aliens_lejos()
a1.hitbox.center = (1000, 640); a1.angulo = 0
j2.personaje.direccion = "west"
g._tecla_en_partida(pygame.K_RCTRL)
assert g.senales and a1.punto_ruido == g.senales[0]["pos"]
distancia = math.hypot(g.senales[0]["pos"][0] - j2.hitbox.centerx,
                       g.senales[0]["pos"][1] - j2.hitbox.centery)
assert distancia > 150, "la señal debería caer lejos del jugador"
g._actualizar_partida(DT)
assert a1.accion == "INVESTIGAR"
print(f"Emisión modulada: la señal cae a {int(distancia)} px y el alien va a revisarla")
cap("roles_j_emision.png")

# ---------- 7. El HUD dice qué tecla usar ----------
print("\nHUD:", acciones_rol.linea_de_estado(j1), "|", acciones_rol.linea_de_estado(j2))
rol(j1, "Forjador")
assert "escoge" in acciones_rol.linea_de_estado(j1)

print("\nTODO OK")
