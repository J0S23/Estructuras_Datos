"""Prueba del árbol de logros (Estructuras/arbol_logros.py y logros.py).

    python pruebas/prueba_logros.py
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
import objetos_mapa
from Estructuras.arbol_logros import ArbolLogros
from data.logros import ARBOL_LOGROS, COLOR_RAMA
objetos_mapa.mapa_activo = lambda: "Nave"
DT = 1000 // 60


class Teclas(dict):
    def __getitem__(self, k):
        return self.get(k, False)


TECLAS = Teclas()
pygame.key.get_pressed = lambda: TECLAS

# ---------- La estructura sola ----------
arbol = ArbolLogros(ARBOL_LOGROS)
nodos = arbol.preorden()
assert len(nodos) == arbol.total() == len(arbol.indice)
assert all(n.rama in COLOR_RAMA for n in nodos)
niveles = arbol.por_niveles()
assert niveles[0] == [arbol.raiz] and len(niveles[1]) == 7
assert sum(len(n) for n in niveles) == arbol.total()
print(f"{arbol.total()} logros, {len(niveles)} niveles, ramas: {[n.nombre for n in niveles[1]]}")

# Conseguir uno profundo marca todo el camino hasta la raíz.
nuevos = arbol.conseguir("libertad", "Forjador")
assert [n.clave for n in nuevos] == ["despertar", "codigo_roto", "sin_rumbo", "chatarrero", "libertad"]
assert arbol.buscar("libertad").quien == "Forjador" and not arbol.buscar("libertad").por_camino
assert arbol.buscar("chatarrero").por_camino
assert arbol.conseguir("libertad") == []          # dos veces no cuenta
assert arbol.buscar("todos_a_bordo").visible and not arbol.buscar("a_la_primera").obtenido
assert not arbol.buscar("fantasma").visible       # su padre no está
print("conseguir 'Libertad' marca su camino a la raíz:", [n.nombre for n in nuevos])

# Posiciones (postorden): cada padre a la altura del medio de sus hijos.
pos = arbol.posiciones()
for n in nodos:
    if n.hijos:
        assert pos[n][1] == (pos[n.hijos[0]][1] + pos[n.hijos[-1]][1]) / 2
    if n.padre:
        assert pos[n][0] == pos[n.padre][0] + 1
hojas = [n for n in nodos if not n.hijos]
assert sorted(pos[h][1] for h in hojas) == list(range(len(hojas)))
arbol.reiniciar()
assert arbol.obtenidos() == 0
print(f"posiciones: {len(hojas)} filas x {max(c for c, _ in pos.values()) + 1} columnas")

# ---------- En una partida ----------
def nueva_partida(roles=("Tecnomante", "Forjador")):
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
    return g


def poner(j, punto):
    j.personaje.hitbox.center = punto
    j.personaje.sync_sprite_from_hitbox()


def frames(g, n):
    for _ in range(n):
        g._actualizar_partida(DT)


g = nueva_partida()
L = g.logros
j1, j2 = g.jugadores
assert L is not None and L.arbol.obtenidos() == 0
frames(g, 5)
assert not L.tiene("despertar"), "en el tutorial no hay logros"
for j in g.jugadores:
    while g.en_tutorial:
        g.tutorial.siguiente(j)
        if not g.en_tutorial:
            g._terminar_tutorial()
        if g.tutorial.esta_listo(j):
            break
frames(g, 2)
assert L.tiene("despertar") and L.avisos
cap = lambda nombre: (g._dibujar(), pygame.image.save(g.screen, os.path.join(OUT, nombre)))
cap("logros_a_aviso.png")
print("terminar el tutorial: 'Despertar' y sale el aviso")
for a in g.aliens:
    a.hitbox.topleft = (5, 5)
    a.descanso_ms = 10 ** 9

# Puerta: a la primera.
poner(j1, g.mision.puerta.center)
g.mision._panel_codigo(j1)
j1.cursor = j1.panel["codigos"].index(g.mision.codigo) if isinstance(j1.panel["codigos"], list) \
    else list(j1.panel["codigos"]).index(g.mision.codigo)
g.confirmar(j1)
frames(g, 2)
assert L.tiene("codigo_roto") and L.tiene("a_la_primera")
assert L.arbol.buscar("a_la_primera").quien == "Tecnomante"
print("abrir la puerta sin fallar: 'Código roto' y 'A la primera'")

# NEXUS: entrar a una terminal.
zona = next(z for z in g.zonas if z["clave"].startswith("nexus"))
poner(j2, zona["rect"].center); frames(g, 1)
g._tecla_en_partida(pygame.K_RETURN)
assert j2.panel["accion"] == "ayuda_menu" and L.tiene("conectado")
assert L.arbol.buscar("conectado").quien == "Forjador"
j2.cerrar_panel()
print("NEXUS: 'Conectado'")

# Rescate de alguien en su última vida.
j2.vidas = 2
g._atrapar(j2, g.aliens[0])
assert j2.preso is not None and j2.vidas == 1
celda = next(c for c in g.mision.celdas if c["preso"] is j2)
g.mision.liberar(celda, j1)
assert L.tiene("nadie_atras") and L.tiene("segunda_oportunidad")
print("rescatar al que le queda 1 vida: 'Nadie se queda atrás' y 'Segunda oportunidad'")

# Apagón rápido.
g.eventos.lanzar("apagon")
frames(g, 30)
g.eventos.restaurar_luz(j1)
frames(g, 1)
assert L.tiene("hagase_la_luz") and L.tiene("electricista")
print("devolver la luz rápido: 'Hágase la luz' y 'Electricista'")

# 30 s en sigilo.
poner(j1, g.mision.puerta.center)
L.sigilo_ms[id(j1)] = 29_900
TECLAS[pygame.K_LSHIFT] = True; TECLAS[pygame.K_d] = True
frames(g, 12)
TECLAS.clear()
assert L.tiene("pasos_de_gato")
print("30 s caminando en sigilo: 'Pasos de gato'")

# Infiltrado: recoger y subir.
caso = g.infiltrado
p = caso.pruebas[0]
poner(j1, p["rect"].center); frames(g, 1)
g._tecla_en_partida(pygame.K_e); j1.cerrar_panel()
assert L.tiene("algo_no_cuadra")
caso.subir(j1)
assert L.tiene("evidencia")
caso.acusar(j1, caso.infiltrado)
assert L.tiene("corazonada") and not L.tiene("caso_cerrado")
print("infiltrado: 'Algo no cuadra', 'Evidencia' y 'Corazonada'")

# El árbol en la pausa: navegar con las flechas.
g._manejar_tecla(pygame.K_ESCAPE)
g.pausa.seleccion = 2; g._manejar_tecla(pygame.K_RETURN)
assert g.pausa.vista == "logros"
raiz = L.arbol.raiz
g._manejar_tecla(pygame.K_RIGHT); assert g.pausa.nodo is raiz.hijos[0]
g._manejar_tecla(pygame.K_RIGHT); assert g.pausa.nodo is raiz.hijos[0].hijos[0]
g._manejar_tecla(pygame.K_LEFT); assert g.pausa.nodo is raiz.hijos[0]
g._manejar_tecla(pygame.K_DOWN); assert g.pausa.nodo is L.arbol.preorden()[2]
g.pausa.nodo = L.arbol.buscar("libertad")
cap("logros_b_arbol.png")
g.pausa.nodo = L.arbol.buscar("fantasma")
for tam in ((1280, 720), (1920, 1080)):
    g.screen = pygame.display.set_mode(tam)
    cap(f"logros_c_arbol_{tam[0]}.png")
g.screen = pygame.display.set_mode((1366, 768))
# El mouse también selecciona.
nodo = L.arbol.buscar("medico")
g.pausa.mover_mouse(g.pausa.rects_logros[nodo].center)
assert g.pausa.nodo is nodo
g._manejar_tecla(pygame.K_ESCAPE)
assert g.pausa.vista == "menu"
g._manejar_tecla(pygame.K_ESCAPE)
assert g.pausa is None
print("pausa > Logros: el árbol se recorre con las flechas (izq: padre, der: hijo) y el mouse")

# Escapar: los de la rama escape y los de terminar.
g.mision.piezas_entregadas = 3
frames(g, 1)
assert L.tiene("chatarrero") and L.tiene("sin_rumbo")
g.mision.resultado = "victoria"
L.capturas_total = 0
g.terminar_ronda()
assert L.tiene("libertad") and L.tiene("todos_a_bordo") and L.tiene("nadie_me_vio")
for _ in range(80):
    if g.transitions.is_idle(): break
    g.transitions.update(g, 33)
g.current_screen = "resultados"
cap("logros_d_resultados.png")
print(f"escapar: 'Libertad', 'Todos a bordo' y 'Nadie me vio' -> {L.arbol.obtenidos()}/{L.arbol.total()}")

# Resultados: botón "Ver logros" abre el árbol; se recorre igual que en la pausa.
assert g.resultados_vista == "resumen" and g.resultados_sel == 0
g._manejar_tecla(pygame.K_RETURN)
assert g.resultados_vista == "logros" and g.resultados_nodo is L.arbol.raiz
g._manejar_tecla(pygame.K_RIGHT)
assert g.resultados_nodo is L.arbol.raiz.hijos[0]
g._manejar_tecla(pygame.K_LEFT)
assert g.resultados_nodo is L.arbol.raiz
g._manejar_tecla(pygame.K_DOWN)
assert g.resultados_nodo is L.arbol.preorden()[1]
cap("logros_e_resultados_arbol.png")
g._manejar_tecla(pygame.K_ESCAPE)
assert g.resultados_vista == "resumen" and g.current_screen == "resultados"
# Con el mouse: clic en "Ver logros" y vuelve con Esc; con el mando, A y B.
g._dibujar()
g._manejar_click(g.resultados_rects[0].center)
assert g.resultados_vista == "logros"
g._tecla_mando(2, "volver")
assert g.resultados_vista == "resumen"
g._tecla_mando(2, "derecha")
assert g.resultados_sel == 1
g._manejar_tecla(pygame.K_RETURN)
assert g.transitions.active or g.current_screen == "menu", "Volver al menú"
print("resultados: 'Ver logros' muestra el árbol (teclado, mouse y mando) y 'Volver al menú' sale")

# Otra partida: el árbol empieza de cero.
g2 = nueva_partida()
assert g2.logros.arbol.obtenidos() == 0
print("partida nueva: logros en 0")
print("\nTODO OK")
