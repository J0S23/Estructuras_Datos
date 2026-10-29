"""Prueba de la misión completa en la nave, sin ventana.

    python pruebas/prueba_mision.py

Juega la misión de punta a punta con lo que hay en Hitboxes/Nave_objetos.json:
notas y código de la puerta, alarma por código equivocado, puntos de equipo
para habilidades, consolas (mantener la tecla), piezas y reparación de la
cápsula, celdas y rescate, NEXUS, huida y victoria. Después repite con una
tripulación sin Tecnomante ni Forjador (consumibles) y prueba la derrota.

Guarda capturas en pruebas/capturas/mision_*.png.
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

from juego import app as App
from juego import objetos_mapa
from misiones import mision as M
objetos_mapa.mapa_activo = lambda: "Nave"      # sin tocar el mapa activo real
DT = 1000 // 60


def nueva_partida(roles):
    g = App.Game()
    def avanzar():
        for _ in range(80):
            if g.transitions.is_idle(): break
            g.transitions.update(g, 33)
    g._activar_opcion_menu("jugar"); avanzar(); g.current_screen = "cantidad"
    g._manejar_tecla(pygame.K_RETURN); avanzar(); g.current_screen = "roles"
    nombres = [r["nombre"] for r in App.ROLES]
    g.seleccion_roles[0]["cursor"] = nombres.index(roles[0]); g._manejar_tecla(pygame.K_e)
    g.seleccion_roles[1]["cursor"] = nombres.index(roles[1]); g._manejar_tecla(pygame.K_RETURN)
    avanzar(); g.current_screen = "partida"
    # El tutorial ya no se acaba solo: aquí se da por terminado (con el
    # tutorial abierto la puerta de la prisión no abre).
    if g.tutorial is not None:
        g.tutorial.activo = False; g._terminar_tutorial()
    # NEXUS se prueba aparte (prueba_nexus.py): aquí no mete rumores ni pide planos.
    # Y el Cambiaformas también (prueba_cambiaformas.py).
    g.nexus = None
    g.quitar_cambiaformas()
    return g


def poner(j, punto):
    j.personaje.hitbox.center = (int(punto[0]), int(punto[1]))
    j.personaje.sync_sprite_from_hitbox()


def calmar_aliens(g):
    for a in g.aliens:
        a.descanso_ms = 10 ** 9; a.punto_ruido = None; a.escondite_objetivo = None


def frames(g, n):
    for _ in range(n):
        g._actualizar_partida(DT)


def cap(g, nombre):
    g._dibujar(); pygame.display.flip()
    pygame.image.save(g.screen, os.path.join(OUT, nombre))


def mantener(g, j, segundos):
    for _ in range(int(segundos * 1000 / DT) + 2):
        g.mision.mantener(j, DT)
        g.mision.actualizar(DT)


# ================= Partida 1: Tecnomante + Forjador =================
g = nueva_partida(("Tecnomante", "Forjador"))
tec, forj = g.jugadores
m = g.mision
print("mapa:", g.mundo.nombre_mapa, "| misión activa:", m.activa, "| fase:", m.fase,
      "| código:", m.codigo, "| sin límite de tiempo:", g.tiempo_restante_ms is None)
assert m.activa and m.fase == "prision" and m.puerta in g.mundo.paredes
assert not m.consumibles, "con Tecnomante y Forjador no hay consumibles"
assert len(g.aliens) == 3 and any(z["clave"].startswith("nexus") for z in g.zonas)
cap(g, "mision_a_inicio.png")
calmar_aliens(g)

# Notas: la del código está en la prisión.
con_codigo = [n for n in m.notas if m.codigo in n["texto"]]
assert len(con_codigo) == 1
poner(tec, con_codigo[0]["rect"].center)
assert g.mision.interactuar(tec) and tec.panel["titulo"] == "Nota arrugada"
print("nota del código:", tec.panel["cuerpo"][0])
cap(g, "mision_b_nota.png")
tec.cerrar_panel()

# Puerta: código equivocado suena la alarma; el correcto abre.
poner(tec, (m.puerta.right + 40, m.puerta.centery))
for a in g.aliens:
    a.descanso_ms = 0
g._tecla_en_partida(pygame.K_e)
assert tec.panel and tec.panel.get("accion") == "codigo"
codigos = tec.panel["codigos"]
tec.cursor = next(i for i, c in enumerate(codigos) if c != m.codigo)
g.confirmar(tec)
assert all(a.punto_ruido == m.puerta.center for a in g.aliens), "la alarma debió atraer aliens"
print("código equivocado: los aliens van a la puerta")
calmar_aliens(g)
g._tecla_en_partida(pygame.K_e)
tec.cursor = tec.panel["codigos"].index(m.codigo)
g.confirmar(tec)
assert m.puerta_abierta and m.puerta not in g.mundo.paredes and m.fase == "sabotaje"
print("código correcto: puerta abierta | fase:", m.fase, "| puntos del equipo:", g.equipo.puntos)

# Las habilidades se pagan con puntos del equipo.
antes = g.equipo.puntos
g.alternar_habilidades(tec); tec.cursor = 1; g._confirmar_habilidad(tec)
assert tec.arbol.tiene("ESCANEO") and g.equipo.puntos == antes - 15
tec.cerrar_panel()
print("Tecnomante desbloqueó Escaneo con puntos del equipo:", antes, "->", g.equipo.puntos)

# Consolas: el Forjador no puede; el Tecnomante sí, manteniendo la tecla.
c0, c1 = m.consolas
poner(forj, c0["rect"].center)
mantener(g, forj, 1)
assert c0["progreso"] == 0
for consola in m.consolas:
    poner(tec, consola["rect"].center)
    mantener(g, tec, M.SABOTAJE_ROL_S)
    assert consola["progreso"] >= 1
assert m.fase == "capsula"
print("consolas apagadas | fase:", m.fase)

# Piezas: el Forjador las recoge y las lleva; repara manteniendo la tecla.
for pieza in g.piezas[:3]:
    poner(forj, pieza["rect"].center)
    frames(g, 1)
assert forj.piezas == 3, forj.piezas
poner(forj, m.capsula.center); poner(tec, m.capsula.center)
assert m.interactuar(forj) and m.piezas_entregadas == 3
mantener(g, tec, 1)
assert m.reparacion == 0, "el Tecnomante sin kit no repara"
mantener(g, forj, M.REPARACION_ROL_S)
assert m.fase == "huida" and all(a.alerta for a in g.aliens)
print("cápsula reparada | fase:", m.fase, "| aliens en alerta")

# Celdas: atrapan al Tecnomante y el Forjador lo saca.
poner(tec, (1500, 1300))
g._atrapar(tec, g.aliens[0])
assert tec.preso is not None and not tec.cazable
cap(g, "mision_c_celda.png")
celda = tec.preso
poner(forj, (celda["punto"][0], celda["punto"][1] + 60))
g._tecla_en_partida(pygame.K_RETURN)
assert tec.preso is None and not g.mundo.colisiona(tec.hitbox)
print("rescate: el Forjador sacó al Tecnomante de la celda")

# NEXUS: la terminal es la central de ayuda; desde ahí también se abre el caso.
nexus = [z for z in g.zonas if z["clave"].startswith("nexus")][0]
poner(tec, nexus["rect"].center)
tec.zona_cerca = g.zona_bajo(tec)
g.interactuar(tec)
assert tec.panel["accion"] == "ayuda_menu"
assert any("Confianza" in l for l in tec.panel["cuerpo"]) or g.nexus is None
cap(g, "mision_d_ayuda.png")
tec.cursor = next(i for i, (t, _) in enumerate(tec.panel["acciones"]) if t == "infiltrado")
g.confirmar(tec)
assert tec.panel["accion"] == "infiltrado_menu" and "Sospechosos:" in tec.panel["cuerpo"]
print("NEXUS:", tec.panel["titulo"], "|", len(g.infiltrado.sospechosos), "sospechosos")
cap(g, "mision_d_nexus.png")
tec.cerrar_panel()

# Huida: todos en la cápsula = victoria.
calmar_aliens(g)
poner(tec, m.capsula.center); poner(forj, m.capsula.center)
frames(g, 2)
assert m.resultado == "victoria"
for _ in range(80):
    if g.transitions.is_idle(): break
    g.transitions.update(g, 33)
g.current_screen = "resultados"
cap(g, "mision_e_victoria.png")
print("VICTORIA | puntos del equipo:", g.equipo.total)

# ================= Partida 2: sin Tecnomante ni Forjador =================
g = nueva_partida(("Biomante", "Resonante"))
bio, res = g.jugadores
m = g.mision
calmar_aliens(g)
tipos = sorted(c["tipo"] for c in m.consumibles)
print("\nsin Tecnomante ni Forjador -> consumibles:", tipos, "| piezas para todos:", m.piezas_para_todos)
assert tipos == ["decodificador", "kit"] and m.piezas_para_todos
m.abrir_puerta(bio)
deco = [c for c in m.consumibles if c["tipo"] == "decodificador"][0]
poner(bio, deco["rect"].center)
assert m.interactuar(bio) and "decodificador" in bio.objetos
poner(bio, m.consolas[0]["rect"].center)
mantener(g, bio, M.SABOTAJE_ROL_S)
assert 0 < m.consolas[0]["progreso"] < 1, "con decodificador debe ser más lento"
mantener(g, bio, M.SABOTAJE_OTROS_S)
assert m.consolas[0]["progreso"] >= 1 and "decodificador" in bio.objetos
mantener(g, bio, M.SABOTAJE_OTROS_S)
print("la Biomante apagó una consola con el decodificador (y le sirve para las demás)")
poner(res, g.piezas[0]["rect"].center); frames(g, 1)
assert res.piezas == 1, "sin Forjador cualquiera recoge piezas"
print("la Resonante recogió una pieza")

# Derrota: todos encerrados.
g._atrapar(bio, g.aliens[0]); g._atrapar(res, g.aliens[1])
frames(g, 1)
assert m.resultado == "derrota"
print("todos encerrados -> DERROTA")

print("\nTODO OK")
