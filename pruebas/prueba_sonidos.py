"""Prueba de los sonidos, sin parlantes.

    python pruebas/prueba_sonidos.py

1. Todo sonido que el código pide existe en Audio/SFX/ (antes el juego pedía
   "susto" y no había archivo: esos momentos sonaban mudos).
2. Todo archivo de Audio/SFX/ lo usa alguien.
3. En una partida suenan los nuevos: apagón, luz, pausa, recoger, logro...
4. El zumbido de fondo suena en la partida, se calla en el apagón y se apaga
   al salir.
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
for llamada in re.findall(r"(?:sonar|bucle)\(([^()]*(?:\([^()]*\)[^()]*)*)\)", codigo):
    pedidos |= set(re.findall(r"\"(\w+)\"", llamada))
pedidos.discard("nombre")
hay = {os.path.splitext(os.path.basename(r))[0] for r in glob.glob("Audio/SFX/*")}
faltan = pedidos - hay
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
else:
    print("(sin mezclador de audio: no se prueba el zumbido)")
print("\nTODO OK")
