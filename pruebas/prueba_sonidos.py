"""Prueba de los sonidos, sin parlantes.

    python pruebas/prueba_sonidos.py

1. Todo sonido que el código pide existe en Audio/SFX/ (antes el juego pedía
   "susto" y no había archivo: esos momentos sonaban mudos).
2. Todo archivo de Audio/SFX/ lo usa alguien.
3. En una partida suenan los nuevos: apagón, luz, pausa, recoger, logro...
4. El zumbido de fondo suena en la partida, se calla en el apagón y se apaga
   al salir.
5. En los resultados suena la música de ese final (Audio/Musica/).
"""

import os, re, sys, glob
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
import pygame; pygame.init()

# ---------- 1 y 2: lo que se pide y lo que hay ----------
codigo = ""
for ruta in (glob.glob("*.py") + glob.glob("screens/*.py")
             + [r for carpeta in ("juego", "entidades", "misiones", "redes")
                for r in glob.glob(f"{carpeta}/*.py")]):
    codigo += open(ruta, encoding="utf-8").read()
# Las palabras entre comillas dentro de cada llamada a sonar(...) / bucle(...)
# (incluye `"acierto" if ok else "fallo"` y `_sonar(juego, "curar", 0.7)`).
pedidos = set()
for llamada in re.findall(r"(?:sonar|bucle|musica)\(([^()]*(?:\([^()]*\)[^()]*)*)\)", codigo):
    pedidos |= set(re.findall(r"\"(\w+)\"", llamada))
pedidos.discard("nombre")
# Los que el ambiente saca de sus tablas (voces de los aliens, pasto, arreglos).
from juego import ambiente as _ambiente
for sonidos, _minimo, _maximo in _ambiente.VOCES.values():
    pedidos |= set(sonidos)
pedidos |= set(_ambiente.PASOS_PASTO) | {t[1] for t in _ambiente.TRABAJOS}
hay = {os.path.splitext(os.path.basename(r))[0] for r in glob.glob("Audio/SFX/*")}
# La música del menú la escoge el equipo (no la genera generar_sonidos.py):
# sin el archivo, el menú va callado.
OPCIONALES = {"musica_menu"}
faltan = pedidos - hay - OPCIONALES
assert not faltan, f"el código pide sonidos que no existen: {sorted(faltan)}"
sobran = hay - pedidos
assert not sobran, f"sonidos que nadie usa: {sorted(sobran)}"
print(f"{len(hay)} sonidos: todos existen y todos se usan")

# ---------- 3: en una partida ----------
from juego import app as App
from juego import objetos_mapa
from juego.audio_manager import audio_manager
objetos_mapa.mapa_activo = lambda: "Nave"
DT = 1000 // 60


class Teclas(dict):
    def __getitem__(self, k):
        return self.get(k, False)


pygame.key.get_pressed = lambda: Teclas()
g = App.Game()


def avanzar():
    for _ in range(80):
        if g.transitions.is_idle(): break
        g.transitions.update(g, 33)


def sonaron():
    return {n for n, _ in g.ambiente.ultimos}


# ---------- 3a: los botones del menú principal (Diego, nov 23) ----------
g.current_screen = "menu"
g.transitions = App.TransitionManager()
g.ambiente.ultimos.clear()
g.menu_selected = 0
g._manejar_tecla(pygame.K_DOWN)
assert g.menu_selected == 1 and sonaron() == {"menu_mover"}, sonaron()
g.ambiente.ultimos.clear()
g._manejar_tecla(pygame.K_LEFT)                     # no mueve nada: no suena
assert not sonaron(), sonaron()
centro = g.menu_buttons[3].rect.center
g._mouse_en_menu(centro)
assert g.menu_selected == 3 and sonaron() == {"menu_mover"}, "pasar el mouse por un botón no sonó"
g.ambiente.ultimos.clear()
g._mouse_en_menu((centro[0] + 3, centro[1]))       # el mismo botón: no vuelve a sonar
assert not sonaron(), sonaron()
g._mouse_en_menu((2, 2))                            # fuera de los botones: nada
assert g.menu_selected == 3 and not sonaron()
i_opciones = next(i for i, b in enumerate(g.menu_buttons) if b.action == "opciones")
g._manejar_click(g.menu_buttons[i_opciones].rect.center)
assert g.opciones_menu is not None and "menu_ok" in sonaron(), "el clic no sonó"
g.ambiente.ultimos.clear()
g._manejar_tecla(pygame.K_ESCAPE)                   # (cierra Opciones: lo de la pausa)
g.opciones_menu = None
g.ambiente.ultimos.clear()
i_ok = next(i for i, b in enumerate(g.menu_buttons) if b.action == "creditos")
g.menu_selected = i_ok
g._manejar_tecla(pygame.K_RETURN)
assert "menu_ok" in sonaron(), sonaron()
avanzar(); g.current_screen = "menu"; g.ambiente.ultimos.clear()
print("menú principal: flechas, mouse encima (solo al cambiar de botón), clic y Enter suenan")

g._activar_opcion_menu("jugar"); avanzar(); g.current_screen = "cantidad"
g._manejar_tecla(pygame.K_DOWN); g._manejar_tecla(pygame.K_UP)
g._manejar_tecla(pygame.K_RETURN); avanzar(); g.current_screen = "roles"
g._manejar_tecla(pygame.K_e); g._manejar_tecla(pygame.K_RETURN)
avanzar(); g.current_screen = "partida"
g.ambiente.ultimos.clear()
for j in g.jugadores:
    while g.en_tutorial and not g.tutorial.esta_listo(j):
        g._tecla_en_partida(j.teclas["habilidad"][0])
assert {"menu_ok", "susto"} <= sonaron(), sonaron()
print("tutorial: cada paso hace clic y al terminar suena el susto")
for a in g.aliens:
    a.descanso_ms = 10 ** 9

g.ambiente.ultimos.clear()
g.eventos.lanzar("apagon")
g.eventos.restaurar_luz(g.jugadores[0])
assert {"apagon", "luz"} <= sonaron(), sonaron()
g._manejar_tecla(pygame.K_ESCAPE)
assert "pausa" in sonaron()
g._manejar_tecla(pygame.K_DOWN)
assert "menu_mover" in sonaron()
g._manejar_tecla(pygame.K_UP); g._manejar_tecla(pygame.K_RETURN)   # continuar
assert g.pausa is None
print("apagón, luz y pausa suenan")

g.ambiente.ultimos.clear()
j1 = g.jugadores[0]
prueba = g.infiltrado.pruebas[0]
j1.personaje.hitbox.center = prueba["rect"].center; j1.personaje.sync_sprite_from_hitbox()
g._actualizar_partida(DT)
g._tecla_en_partida(pygame.K_e)
assert "recoger" in sonaron() and "logro" in sonaron(), sonaron()
print("recoger una prueba: suena al recoger y el logro")

# ---------- 4: el zumbido de fondo ----------
if pygame.mixer.get_init() is not None:
    g.eventos.apagon = False
    g._sonido_de_fondo()
    assert audio_manager.sonando_bucle == "ambiente"
    assert audio_manager._volumen_bucle > 0
    g.eventos.apagon = True
    g._sonido_de_fondo()
    assert audio_manager._volumen_bucle == 0, "en el apagón se calla"
    g.eventos.apagon = False
    g.current_screen = "menu"
    g._sonido_de_fondo()
    assert audio_manager.sonando_bucle is None
    print("zumbido de fondo: suena en la partida, se calla en el apagón y se apaga en el menú")
    # La música del menú (con la de calma haciéndose pasar por ella, si no está el archivo).
    if "musica_menu" not in hay:
        audio_manager._sonidos["musica_menu"] = audio_manager._sonido("musica_calma")
    g._sonido_de_fondo()
    assert audio_manager.sonando_musica == "musica_menu", audio_manager.sonando_musica
    for pantalla in ("cantidad", "roles", "ranking", "creditos", "cargando"):
        g.current_screen = pantalla
        g._sonido_de_fondo()
        assert audio_manager.sonando_musica == "musica_menu", (pantalla, audio_manager.sonando_musica)
    g.current_screen = "resultados"
    g._sonido_de_fondo()
    assert audio_manager.sonando_musica is None, "en los resultados no va la música del menú"
    g.current_screen = "partida"
    g._sonido_de_fondo()
    assert audio_manager.sonando_musica in ("musica_calma", "musica_tension")
    g.current_screen = "menu"
    g._sonido_de_fondo()
    assert audio_manager.sonando_musica == "musica_menu"
    audio_manager._sonidos.pop("musica_menu", None)
    print("música del menú: en el menú y sus pantallas, no en los resultados; en la partida, la de la nave")

    # La música de cada final (juego/musica_final.py), en los resultados.
    from juego import musica_final
    from types import SimpleNamespace
    for final, archivo in (("sin_entrar", "final_sin_entrar"), ("escaparon", "final_escaparon"),
                           ("quedarse", "final_quedarse"), ("nadie", "final_quedarse"),
                           ("liberados", "final_liberados"), (None, "final_derrota")):
        mision = SimpleNamespace(activa=True, resultado="derrota" if final in (None, "quedarse", "nadie")
                                 else "victoria", final=final)
        assert musica_final.ruta(musica_final.clave(mision)), (final, "falta el archivo")
        g.mision = mision
        g.current_screen = "resultados"
        g._sonido_de_fondo()
        assert (audio_manager.sonando_cancion or "").endswith(archivo + ".ogg"), \
            (final, audio_manager.sonando_cancion)
    assert musica_final.clave(SimpleNamespace(activa=True, resultado="victoria", final=None)) == "victoria"
    # Baja mientras habla el narrador, y se va al salir de los resultados.
    audio_manager._agachar(True)
    assert abs(pygame.mixer.music.get_volume() - musica_final.VOLUMEN * audio_manager.sfx_volume * 0.45) < 0.02
    audio_manager._agachar(False)
    g.current_screen = "menu"
    g._sonido_de_fondo()
    assert audio_manager.sonando_cancion is None, "en el menú ya no suena la del final"
    g.current_screen = "resultados"
    g._sonido_de_fondo()
    g.current_screen = "partida"
    g._sonido_de_fondo()
    assert audio_manager.sonando_cancion is None, "ni en la partida siguiente"
    print("música de los finales: cada final la suya en los resultados; baja con el narrador; se va al salir")
else:
    print("(sin mezclador de audio: no se prueba el zumbido)")
print("\nTODO OK")
