"""Las voces de los aliens, el pasto, el casillero, los arreglos, el cohete y
la música de fondo, sin ventana.

    python pruebas/prueba_sonidos_nuevos.py

Como en prueba_ambiente.py: no se puede oír, así que se revisa QUÉ sonaría
(Ambiente.ultimos) y que los archivos existen y no están en silencio.
"""

import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
import struct, wave
import pygame; pygame.init()

from juego import app as App
from juego import ambiente as Amb
from juego import objetos_mapa
from juego.audio_manager import audio_manager
objetos_mapa.mapa_activo = lambda: "Nave"
DT = 1000 // 60

# 1. Los archivos están y suenan (no son puro silencio).
NUEVOS = ["voz_ciego_1", "voz_ciego_2", "voz_vigia_1", "voz_vigia_2", "voz_cazador_1",
          "voz_cazador_2", "guardia_esfuerzo_1", "guardia_esfuerzo_2", "sombra_desvanece",
          "paso_pasto_1", "paso_pasto_2", "casillero_golpe", "reparar", "tecleo", "cohete",
          "musica_calma", "musica_tension"]
for nombre in NUEVOS:
    ruta = os.path.join("Audio", "SFX", nombre + ".wav")
    assert os.path.exists(ruta), f"falta {nombre}.wav"
    with wave.open(ruta) as w:
        cuadros = w.readframes(w.getnframes())
    muestras = struct.unpack("<%dh" % (len(cuadros) // 2), cuadros)
    pico = max(abs(m) for m in muestras)
    fuerza = (sum(m * m for m in muestras) / len(muestras)) ** 0.5
    assert pico > 8000 and fuerza > 300, f"{nombre} casi no suena (pico {pico}, rms {fuerza:.0f})"
# Los bucles de música empalman: el final y el principio casi se tocan.
for nombre in ("musica_calma", "musica_tension"):
    with wave.open(os.path.join("Audio", "SFX", nombre + ".wav")) as w:
        cuadros = w.readframes(w.getnframes())
    muestras = struct.unpack("<%dh" % (len(cuadros) // 2), cuadros)
    salto_normal = max(abs(muestras[i + 1] - muestras[i]) for i in range(0, 4000))
    assert abs(muestras[0] - muestras[-1]) <= salto_normal * 2 + 200, f"{nombre} da un salto al repetirse"
print(f"los {len(NUEVOS)} sonidos nuevos están en Audio/SFX, suenan y la música empalma")

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
amb = g.ambiente


class AlienFalso:
    """Lo que Ambiente mira de un alien."""
    def __init__(self, tipo, centro, accion="PATRULLAR"):
        self.tipo, self.centro, self.accion = tipo, centro, accion
        self.alerta = self.aturdido = self.comiendo = False
        self.moviendose = True


def oir(segundos, aliens, antes_de_cada_cuadro=None):
    amb.ultimos.clear()
    nombres = []
    for _ in range(int(segundos * 1000 / DT)):
        if antes_de_cada_cuadro:
            antes_de_cada_cuadro()
        amb.actualizar(DT, g.jugadores, aliens)
        nombres += [n for n, _ in amb.ultimos]
        amb.ultimos.clear()
    return nombres


for j in g.jugadores:
    j.pulso = 20
j2.personaje.hitbox.center = (5000, 5000)
cerca = (j1.hitbox.centerx + 150, j1.hitbox.centery)
lejos = (j1.hitbox.centerx + 3000, j1.hitbox.centery)

# 2. Cada alien tiene su voz, solo cuando anda cerca.
for tipo, prefijo in (("ciego", "voz_ciego"), ("vigia", "voz_vigia"), ("cazador", "voz_cazador"),
                      ("guardia", "guardia_esfuerzo")):
    oido = [n for n in oir(25, [AlienFalso(tipo, cerca)]) if n.startswith(prefijo)]
    nada = [n for n in oir(25, [AlienFalso(tipo, lejos)]) if n.startswith(prefijo)]
    assert oido and not nada, (tipo, oido, nada)
    print(f"{tipo}: {len(oido)} veces en 25 s cerca ({sorted(set(oido))}), 0 lejos")
# El Ciego chasquea más seguido que el Vigía; persiguiendo, todos más seguido.
def veces(tipo, accion="PATRULLAR"):
    amb.voz_ms.clear()
    return len([n for n in oir(60, [AlienFalso(tipo, cerca, accion)]) if n.startswith("voz_")])
assert veces("ciego") > veces("vigia")
assert veces("cazador", "PERSEGUIR") > veces("cazador")
# El Guardia quieto o comiendo no se esfuerza.
quieto = AlienFalso("guardia", cerca); quieto.moviendose = False
assert not [n for n in oir(15, [quieto]) if n.startswith("guardia")]
print("el Ciego chasquea más que el Vigía, persiguiendo se oyen más y el Guardia quieto calla")

# 3. La Sombra se deshace cuando deja de estar.
sombra = AlienFalso("sombra", cerca); sombra.oculta = False
oir(1, [sombra])
assert "sombra_desvanece" in oir(0.2, [])
assert "sombra_desvanece" not in oir(1, [])                 # una sola vez
print("la Sombra se oye deshacerse (una vez) cuando se va")

# 4. Pasto: solo caminando por la Biosfera.
def caminar():
    j1.personaje.hitbox.x += 2
j1.sala = "Biosfera"
pasto = [n for n in oir(3, [], caminar) if n.startswith("paso_pasto")]
quieto_en_pasto = [n for n in oir(3, []) if n.startswith("paso_pasto")]
j1.sala = "Pasillo"
en_pasillo = [n for n in oir(3, [], caminar) if n.startswith("paso_pasto")]
assert len(pasto) >= 6 and not quieto_en_pasto and not en_pasillo
print(f"pasto: {len(pasto)} pisadas en 3 s caminando por la Biosfera, 0 quieto, 0 en el Pasillo")

# 5. Escondido y con el alien encima: golpes en el casillero.
j1.escondite = {"rect": pygame.Rect(0, 0, 10, 10)}
assert j1.escondido
revisando = AlienFalso("vigia", (j1.hitbox.centerx + 60, j1.hitbox.centery), "REVISAR_ESCONDITE")
paseando = AlienFalso("vigia", (j1.hitbox.centerx + 60, j1.hitbox.centery), "PATRULLAR")
golpes = oir(4, [revisando]).count("casillero_golpe")
assert golpes >= 3 and "casillero_golpe" not in oir(4, [paseando])
j1.escondite = None
assert "casillero_golpe" not in oir(2, [revisando])
print(f"casillero: {golpes} golpes en 4 s con el alien revisando, 0 si solo pasa o si no estás escondido")

# 6. Los arreglos se oyen mientras avanza la barra.
def con_progreso(texto):
    def poner():
        j1.progreso = (texto, 0.5)
    oido = oir(3, [], poner)
    j1.progreso = None
    return oido
assert con_progreso("Reparando la cápsula").count("reparar") >= 3
assert con_progreso("Apagando consola").count("tecleo") >= 4
assert not {"reparar", "tecleo"} & set(oir(2, []))
print("arreglos: carraca al reparar y tecleo en las consolas, solo mientras se mantiene la tecla")

# 7. Música: tranquila, y de tensión cuando persiguen a alguien.
g.pausa = None
if g.tutorial is not None:
    g.tutorial.activo = False
for a in g.aliens:
    a.accion = "PATRULLAR"
g._tension_hasta = 0
g._sonido_de_fondo()
assert audio_manager.sonando_musica == "musica_calma", audio_manager.sonando_musica
g.aliens[0].accion = "PERSEGUIR"
g._sonido_de_fondo()
assert audio_manager.sonando_musica == "musica_tension"
g.aliens[0].accion = "PATRULLAR"
g._sonido_de_fondo()
assert audio_manager.sonando_musica == "musica_tension"    # se queda unos segundos
g._tension_hasta = 0
g._sonido_de_fondo()
assert audio_manager.sonando_musica == "musica_calma"
g.current_screen = "menu"
g._sonido_de_fondo()
assert audio_manager.sonando_musica is None and audio_manager.sonando_bucle is None
print("música: calma, tensión al perseguir (dura unos segundos más) y silencio en el menú")

print("\nTODO OK")
