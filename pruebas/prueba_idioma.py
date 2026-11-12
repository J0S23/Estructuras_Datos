"""El juego en inglés (juego/idioma.py + data/idioma_en.py).

    python pruebas/prueba_idioma.py

1. `tr`: exactos, plantillas con {} (lo de adentro también se traduce),
   mayúsculas, puntuación alrededor y pedazos; en español no toca nada.
2. Recorre el juego en inglés (menú, ayuda, créditos, logros, selección,
   partida con paneles, celular, terminal NEXUS, árbol de habilidades,
   apagón, alarma, pausa, admin, resultados) y anota cada texto que se dibujó
   y sigue en español. Si hay alguno, los lista y falla: falta su traducción
   en data/idioma_en.py (o la función que lo dibuja lo parte antes de
   traducirlo).
3. Menú > Opciones (nuevo) y Pausa > Opciones cambian el idioma.
Capturas en pruebas/capturas/idioma_*.png.
"""

import os
import re
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

import pygame
pygame.init()
pygame.display.set_mode((1366, 768))
OUT = os.path.join(RAIZ, "pruebas", "capturas")
os.makedirs(OUT, exist_ok=True)

from juego import idioma
from juego.idioma import tr
from juego import fuentes

# -- 1. tr ---------------------------------------------------------------------------------
assert tr("Continuar") == "Continuar", "en español no se toca"
idioma.cambiar("en", guardar=False)
assert tr("Continuar") == "Continue"
assert tr("PAUSA") == "PAUSE"
assert tr("CONTINUAR") == "CONTINUE", "mayúsculas por .upper()"
assert tr("3 aliens fuera de combate 20 s") == "3 aliens out of action for 20 s"
assert tr("[E] Terminal NEXUS") == "[E] NEXUS Terminal", tr("[E] Terminal NEXUS")
assert tr("Bahía") == "Bay" and tr("  Bahía ") == "  Bay "
assert tr("Sección rara que no existe") == "Sección rara que no existe"
assert tr("@kevin_gamer") == "@kevin_gamer"
assert tr("Opciones:") == "Options:"
print("1. tr: exactos, plantillas, mayúsculas, puntuación: OK")

# -- 2. Recorrido ------------------------------------------------------------------------------
ESPANOL = re.compile(r"[áéíóúñ¿¡]|\b(el|la|los|las|del|que|para|con|una|por|sin|está|están|ya|y|en|de|se|su|sus|hay|tu|al|lo|le|es|son|más|cuando)\b",
                     re.I)
# Nombres propios y textos que se quedan igual en los dos idiomas.
IGUALES = re.compile(r"^(@\S+|Don Hernán|Julián|Tomás|Lía.*|.*Determination Mono|Diego Payares|Anny Delgado|"
                     r"Joseph Arias|Juan David Campo|Universidad del Norte)$")
sin_traducir = {}
dibujados = set()
_render = fuentes.Fuente.render


def _anotar(self, texto, *args, **kwargs):
    if isinstance(texto, str) and texto.strip():
        final = tr(texto)
        dibujados.add(final)
        limpio = re.sub(r"Lía|Hernán|Julián|Tomás|Universidad del Norte", "", final)
        if ESPANOL.search(limpio) and not IGUALES.match(final.strip()):
            sin_traducir.setdefault(final, texto)
    return _render(self, texto, *args, **kwargs)


fuentes.Fuente.render = _anotar

from juego import app as App
from juego import admin as A
from juego import historial_logros
from data.dificultad import DIFICULTADES

historial_logros.agregar = lambda claves: None
DT = 1000 // 60


class Teclas(dict):
    def __getitem__(self, k):
        return self.get(k, False)


pygame.key.get_pressed = lambda: Teclas()
g = App.Game()


def avanzar():
    for _ in range(80):
        if g.transitions.is_idle():
            break
        g.transitions.update(g, 33)


def foto(nombre):
    g._dibujar()
    pygame.image.save(g.screen, os.path.join(OUT, f"idioma_{nombre}.png"))


def cuadros(n):
    for _ in range(n):
        g._actualizar_partida(DT)
    g._dibujar()


foto("menu")
for pantalla in ("ayuda", "creditos"):
    g._activar_opcion_menu(pantalla); avanzar(); foto(pantalla)
    g._manejar_tecla(pygame.K_RETURN); avanzar()
g._activar_opcion_menu("logros"); avanzar(); foto("logros")
g._manejar_tecla(pygame.K_ESCAPE); avanzar()

g._activar_opcion_menu("jugar"); avanzar(); foto("cantidad")
g._manejar_tecla(pygame.K_RETURN); avanzar(); foto("dificultad")
g.dificultad_seleccionada = [d["clave"] for d in DIFICULTADES].index("facil")
g._manejar_tecla(pygame.K_RETURN); avanzar(); foto("roles")
g.seleccion_roles[0]["cursor"] = 0; g._manejar_tecla(pygame.K_e)
g.seleccion_roles[1]["cursor"] = 1; g._manejar_tecla(pygame.K_RETURN); avanzar()
foto("tutorial")
g.saltar_tutorial()
g.presentacion = None
assert g.current_screen == "partida"
j1, j2 = g.jugadores
cuadros(30); foto("partida")

# Celular, árbol de habilidades y pausa.
j1.puntos = 100
g.equipo.sumar(100)
g._tecla_en_partida(pygame.K_TAB); cuadros(2)
g._tecla_en_partida(pygame.K_d); cuadros(1)
g._tecla_en_partida(pygame.K_d); cuadros(1)
g._tecla_en_partida(pygame.K_RSHIFT); cuadros(2); foto("celular_y_arbol")
g._tecla_en_partida(pygame.K_TAB); g._tecla_en_partida(pygame.K_RSHIFT)

# Terminal NEXUS (central de ayuda) y el caso.
from redes import celular
j1.panel = celular.panel_ayuda(g, j1); cuadros(2); foto("terminal")
j1.cerrar_panel()

# Eventos: rumor, apagón, alarma, Sombra, aturdir (con el menú de admin).
g._manejar_tecla(pygame.K_F1); foto("admin")
g._manejar_tecla(pygame.K_ESCAPE)
for i, opcion in enumerate(A.OPCIONES):
    g.admin = A.MenuAdmin(g)
    g.admin.cursor = i
    g._manejar_tecla(pygame.K_RETURN)
    cuadros(20)
    if i == 0:
        foto("apagon")
g.decir("inicio", forzar=True); cuadros(40); foto("ia")

# Pausa y sus opciones.
g._manejar_tecla(pygame.K_ESCAPE); foto("pausa")
g._manejar_tecla(pygame.K_DOWN); g._manejar_tecla(pygame.K_RETURN); foto("opciones")
g._manejar_tecla(pygame.K_ESCAPE); g._manejar_tecla(pygame.K_ESCAPE)

# Resultados.
g.terminar_ronda(); avanzar(); foto("resultados")

if sin_traducir:
    print(f"\n{len(sin_traducir)} textos dibujados en español:")
    for final, original in sorted(sin_traducir.items()):
        print("   ", repr(final), "" if final == original else f"   (de {original!r})")
    raise SystemExit("FALTAN TRADUCCIONES")
print(f"2. recorrido en inglés: {len(dibujados)} textos distintos dibujados, ninguno en español: OK")

# -- 3. Cambiar el idioma ----------------------------------------------------------------------
g.transitions.request(g, "menu"); avanzar()
idioma.cambiar("es", guardar=False)
assert "opciones" in [b.action for b in g.menu_buttons]
g._activar_opcion_menu("opciones")
assert g.opciones_menu is not None
acciones = [a for _, a in g.opciones_menu.opciones()]
assert acciones == ["efectos", "pantalla_completa", "oscuridad", "idioma", "volver"], acciones
foto("menu_opciones")
for _ in range(acciones.index("idioma")):
    g._manejar_tecla(pygame.K_DOWN)
g._manejar_tecla(pygame.K_RETURN)
assert idioma.IDIOMA == "en" and g.opciones_menu.opciones()[3][0] == "Language: English"
foto("menu_opciones_en")
g._manejar_tecla(pygame.K_LEFT)
assert idioma.IDIOMA == "es"
g._manejar_tecla(pygame.K_ESCAPE)
assert g.opciones_menu is None and g.running, "Esc cierra las opciones, no el juego"
g._activar_opcion_menu("opciones")
g._manejar_tecla(pygame.K_UP); g._manejar_tecla(pygame.K_RETURN)
assert g.opciones_menu is None, "Volver cierra"
from juego.pausa import MenuPausa
p = MenuPausa(g)
p._ir_a("opciones")
k = [a for _, a in p.opciones()].index("idioma")
p.seleccion = k
assert p.tecla(pygame.K_RIGHT) == "idioma"
g._accion_pausa("idioma")
assert idioma.IDIOMA == "en" and p.opciones()[k][0] == "Language: English"
g._accion_pausa("idioma")
assert idioma.IDIOMA == "es"
print("3. Menú > Opciones (sonido, pantalla, oscuridad, idioma) y Pausa > Opciones: OK")
print("\nTODO OK")
