"""La foto al llegar al lugar de un rumor (screens/foto.py, redes/nexus._tomar_foto).

    python pruebas/prueba_foto.py

1. Al llegar al lugar del rumor: `foto_n` sube, suena "foto" (el obturador,
   que existe en Audio/SFX) y no "recoger". En la vista: el flash (blanco), la
   polaroid (papel con la vista adentro) y al final nada. La de otro jugador
   no se mueve.
2. Al arreglar lo de una noticia (que es verdad): también foto.
3. Otra partida: no se anima la foto de la anterior.
4. En red: `foto_n` llega al espejo, el cliente anima la foto y el sonido va
   en las instantáneas.
5. La foto en el celular: la que se tomó sale en lo que publica el equipo (en
   la pestaña Equipo y en la publicación), recortada si se publicó sin
   ubicación; al escoger cómo publicarla se ven las dos versiones. En red, la
   laptop que no vio la foto (la tomó alguien de la otra) muestra el lugar
   sacado del mapa.

Capturas en pruebas/capturas/foto_*.png.
"""

import json
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

from juego import app as App, efectos
from juego.dificultad import Dificultad
from screens import foto
from screens.partida import calcular_viewports

OUT = os.environ.get("NEXUS_CAPTURAS") or os.path.join(RAIZ, "pruebas", "capturas")
os.makedirs(OUT, exist_ok=True)
assert os.path.exists(os.path.join(RAIZ, "Audio", "SFX", "foto.wav")), "falta Audio/SFX/foto.wav"


def partida():
    g = App.Game()
    g.cantidad_jugadores = 2
    g.abrir_seleccion_roles(ir=False)
    for estado, rol in zip(g.seleccion_roles, ("Tecnomante", "Forjador")):
        estado["rol"], estado["listo"] = rol, True
    g.dificultad = Dificultad("normal")
    g._preparar_partida()
    g.current_screen = "partida"
    g.transitions = App.TransitionManager()
    g.saltar_tutorial()
    g.presentacion = None
    g.admin_invencible = True
    g.quitar_cambiaformas()
    for a in g.aliens:
        a.hitbox.topleft = (5, 5)
        a.descanso_ms = 10 ** 9
    g.nexus.reloj_rumor_ms = g.nexus.reloj_normal_ms = 10 ** 9
    sonidos = []
    g.sonar = lambda nombre, volumen=1.0: sonidos.append(nombre)
    return g, sonidos


def poner(j, punto):
    j.personaje.hitbox.center = (int(punto[0]), int(punto[1]))
    j.personaje.sync_sprite_from_hitbox()


def vista_de(g, jugador):
    return calcular_viewports(*g.screen.get_size(), len(g.jugadores))[g.jugadores.index(jugador)]


def dibujar_en(g, jugador, ms):
    """Dibuja el cuadro con la animación de `jugador` justo en `ms` (el reloj
    de screens/foto.py queda quieto mientras se dibuja)."""
    e = foto._estado[foto._clave(jugador)]
    ahora = pygame.time.get_ticks()
    e[1] = ahora - ms
    foto._ahora = lambda: ahora
    try:
        g._dibujar()
    finally:
        foto._ahora = lambda: pygame.time.get_ticks()


def brillo(sup, rect):
    """El promedio de luz de un rectángulo (0-255)."""
    chica = pygame.transform.smoothscale(sup.subsurface(rect), (8, 8))
    return sum(sum(chica.get_at((x, y))[:3]) / 3 for x in range(8) for y in range(8)) / 64


def papel_en(sup, rect):
    """¿Hay papel de la polaroid (casi blanco cálido) en el rectángulo?"""
    claros = 0
    for x in range(rect.left, rect.right, 3):
        for y in range(rect.top, rect.bottom, 3):
            c = sup.get_at((x, y))
            if all(abs(c[i] - foto.COLOR_PAPEL[i]) < 6 for i in range(3)):
                claros += 1
    return claros


# -- 1. Un rumor: llegar al lugar --------------------------------------------------------------------
efectos.ACTIVOS = True
random.seed(5)
g, sonidos = partida()
red = g.nexus
red.rng = random.Random(5)
j1, j2 = g.jugadores
pub = red.lanzar_rumor()
assert pub is not None and pub.lugar is not None
red.investigando[j1] = pub
g._dibujar()                                    # (la primera vez solo se anota foto_n = 0)
v1, v2 = vista_de(g, j1), vista_de(g, j2)
antes = g.screen.copy()
poner(j1, pub.lugar)
g._actualizar_partida(16)
assert pub in red.evidencias[j1], "no tomó la foto al llegar"
assert j1.foto_n == 1 and j2.foto_n == 0, (j1.foto_n, j2.foto_n)
assert j1.foto_lugar, "la foto no sabe de dónde es"
assert "foto" in sonidos and "recoger" not in sonidos, sonidos
# Quedarse ahí no saca otra.
for _ in range(20):
    g._actualizar_partida(16)
assert j1.foto_n == 1

g._dibujar()                                    # aquí se captura la vista
e = foto._estado[foto._clave(j1)]
assert e[1] is not None and e[2] is not None, "no se guardó la imagen de la foto"
assert foto.activa(j1) and not foto.activa(j2)

dibujar_en(g, j1, 30)
pygame.image.save(g.screen, os.path.join(OUT, "foto_a_flash.png"))
centro = pygame.Rect(0, 0, v1.width // 3, v1.height // 3)
centro.center = v1.center
otro = pygame.Rect(0, 0, v2.width // 3, v2.height // 3)
otro.center = v2.center
flash, sin_flash = brillo(g.screen, centro), brillo(antes, centro)
assert flash > sin_flash + 80, f"no se ve el flash ({sin_flash:.0f} -> {flash:.0f})"
assert brillo(g.screen, otro) < 200, "el flash se metió en la vista del otro jugador"

dibujar_en(g, j1, 650)
pygame.image.save(g.screen, os.path.join(OUT, "foto_b_polaroid.png"))
assert papel_en(g.screen, v1) > 40, "no se ve la polaroid"
assert papel_en(g.screen, v2) < 5, "la polaroid salió en la vista del otro"
dibujar_en(g, j1, 1300)
pygame.image.save(g.screen, os.path.join(OUT, "foto_c_vuela.png"))
volando = g.screen.copy()
dibujar_en(g, j1, foto.DURACION_MS + 50)
assert not foto.activa(j1) and e[2] is None, "la foto no terminó (o no soltó la imagen)"
assert papel_en(g.screen, v1) < 5
# Volando, va por arriba de la vista (hacia el aviso de NEXUS): ahí cambia la
# imagen; abajo, no.
arriba = pygame.Rect(v1.centerx - v1.width // 8, v1.y, v1.width // 4, v1.height // 2)
abajo = pygame.Rect(arriba.x, v1.y + int(v1.height * 0.7), arriba.width, int(v1.height * 0.3))
assert brillo(volando, arriba) > brillo(g.screen, arriba) + 8, "la polaroid no vuela hacia arriba"
assert abs(brillo(volando, abajo) - brillo(g.screen, abajo)) < 10, "la polaroid se fue para abajo"

# Sin "Efectos visuales" también (sin ladear).
efectos.ACTIVOS = False
red.evidencias[j1].clear()
pub2 = red.lanzar_rumor()
red.investigando[j1] = pub2
poner(j1, pub2.lugar)
g._actualizar_partida(16)
assert j1.foto_n == 2
g._dibujar()
dibujar_en(g, j1, 650)
assert papel_en(g.screen, v1) > 40, "sin efectos no se ve la polaroid"
efectos.ACTIVOS = True
print(f"1. rumor: foto_n sube, suena 'foto', flash ({sin_flash:.0f} -> {flash:.0f} de luz), polaroid, "
      "vuela y se va; solo en su vista; también sin efectos: OK")

# -- 2. Una noticia (verdad): al arreglarla ----------------------------------------------------------
noticia = red.lanzar_noticia()
if noticia is not None:
    del sonidos[:]
    antes_n = j2.foto_n
    red.arreglar(j2, noticia)
    assert j2.foto_n == antes_n + 1 and "foto" in sonidos and "reparar" in sonidos, (j2.foto_n, sonidos)
    print("2. noticia: al arreglarla, foto (y su sonido, después del de reparar): OK")
else:
    print("2. noticia: (no hubo lugar para una noticia en este mapa; se salta)")

# -- 3. Otra partida -------------------------------------------------------------------------------------
g2, _ = partida()
g2._dibujar()
assert not any(foto.activa(j) for j in g2.jugadores), "se animó la foto de la partida anterior"
assert all(foto._estado[foto._clave(j)][0] == 0 for j in g2.jugadores)
print("3. otra partida: empieza sin foto: OK")

# -- 4. En red -------------------------------------------------------------------------------------------
from cliente_servidor import estado as E
from cliente_servidor.servidor import Servidor, Teclas
from cliente_servidor.espejo import Espejo
from cliente_servidor.protocolo import Reconstructor, comprimir
from entidades.jugador import WASD, FLECHAS

srv = Servidor(2, avisar=lambda t: None, semilla=7, presentaciones=False, aliens_quietos=True,
               roles=["Tecnomante", "Forjador"])
srv.preparar_partida()
srv.lista.set()
for p in srv.puestos:
    p.ocupado = True
srv.teclas = Teclas()
esp = Espejo(App.Game(), srv.bienvenida(srv.puestos[0]))
esp.preparar()
esp.controles({0: WASD, 1: FLECHAS})
gs, gc = srv.juego, esp.g
gs.saltar_tutorial()
r, anterior, cuadro = Reconstructor(), None, 0


def mandar():
    global anterior, cuadro
    ahora = srv.instantanea()
    cuadro += 2
    if anterior is None:
        m = {"tipo": "estado", "c": cuadro, "base": None, "z": comprimir(ahora)}
    else:
        cambios = {k: d for k, d in ((k, E.diferencias(anterior.get(k, {}), v)) for k, v in ahora.items()) if d}
        m = {"tipo": "estado", "c": cuadro, "base": cuadro - 2, "s": cambios}
    anterior = ahora
    sonidos_red = list(srv.sonidos)
    esp.aplicar(r.aplicar(json.loads(json.dumps(m))))
    return sonidos_red


gs.nexus.reloj_rumor_ms = gs.nexus.reloj_normal_ms = 10 ** 9
gs._actualizar_partida(16)
mandar()
pantalla = pygame.Surface((1024, 768))
esp.dibujar(pantalla, [0])
pub = gs.nexus.lanzar_rumor()
js = gs.jugadores[0]
gs.nexus.investigando[js] = pub
poner(js, pub.lugar)
srv.sonidos = []
gs._actualizar_partida(16)
sonaron = mandar()
assert js.foto_n == 1
jc = gc.jugadores[0]
assert jc.foto_n == 1 and jc.foto_lugar == js.foto_lugar, "foto_n no llegó al cliente"
assert any(s[0] == "foto" for s in sonaron), f"el sonido de la foto no va a los clientes: {sonaron}"
esp.dibujar(pantalla, [0])
assert foto.activa(jc), "el cliente no animó la foto"
foto._estado[foto._clave(jc)][1] = pygame.time.get_ticks() - 650
esp.dibujar(pantalla, [0])
pygame.image.save(pantalla, os.path.join(OUT, "foto_d_red.png"))
assert papel_en(pantalla, pantalla.get_rect()) > 40, "en el cliente no se ve la polaroid"
print("4. en red: foto_n y el lugar llegan al espejo, el cliente anima la foto, el sonido va: OK")

# -- 5. La foto en el celular ---------------------------------------------------------------------------
from redes import celular as logica
# En red: la de esta laptop (J1, la vio tomar) y la de la otra (J2: del mapa).
assert pub.id in foto._por_pub, "el cliente no guardó la foto que vio tomar"
vista_cliente = foto._por_pub[pub.id].copy()
js2 = gs.jugadores[1]
pub_b = gs.nexus.lanzar_rumor()
gs.nexus.investigando[js2] = pub_b
poner(js2, pub_b.lugar)
gs._actualizar_partida(16)
gs.nexus.desmentir(js, pub, con_ubicacion=False)
gs.nexus.desmentir(js2, pub_b, con_ubicacion=True)
mandar()
esp.dibujar(pantalla, [0])
desm_c = {p.desmiente.id: p for p in gc.nexus.publicaciones if p.tipo == "desmentido"}
assert set(desm_c) == {pub.id, pub_b.id}, "los desmentidos no llegaron al cliente"
propia = foto.de_publicacion(desm_c[pub.id], gc.nexus, (360, 270))
esperada = foto.recortar(vista_cliente)
assert propia is not None and propia.get_at((180, 135)) == esperada.get_at((180, 135)), \
    "la foto propia (recortada) no es la que se tomó"
ajena = foto.de_publicacion(desm_c[pub_b.id], gc.nexus, (120, 90))
assert ajena is not None, "en la otra laptop no hay foto (debería salir el lugar del mapa)"
print("5a. en red: la foto propia (recortada: sin ubicación) y la de la otra laptop (el lugar del mapa): OK")

# Local.
random.seed(9)
g, sonidos = partida()
red = g.nexus
red.rng = random.Random(9)
j1, j2 = g.jugadores
g._dibujar()
pub = red.lanzar_rumor()
red.investigando[j1] = pub
poner(j1, pub.lugar)
g._actualizar_partida(16)
g._dibujar()
tomada = foto._por_pub.get(pub.id)
assert tomada is not None, "no se guardó la foto para el celular"
# Al escoger cómo publicarla: las dos versiones.
dibujadas = []
original = foto.dibujar_en_celular


def anotar(screen, img, pos, borde=(214, 218, 230)):
    dibujadas.append(img)
    return original(screen, img, pos, borde)


foto.dibujar_en_celular = anotar
j1.abrir_panel({"tipo": "celular", "vista": "ubicacion", "rumor": pub,
                "opciones": [("Publicar la foto tal cual", "tal_cual"),
                             ("Recortar el fondo y publicar", "recortada"), ("Volver", "volver")]})
j1.cursor = 0
g._dibujar()
pygame.image.save(g.screen, os.path.join(OUT, "foto_e_ubicacion.png"))
assert len(dibujadas) == 2, f"al publicar no se ven las dos versiones ({len(dibujadas)})"
w, h = dibujadas[0].get_size()
assert dibujadas[0].get_at((w // 2, h // 2)) != dibujadas[1].get_at((2, 2)) or \
    dibujadas[0].get_at((2, 2)) != dibujadas[1].get_at((2, 2)), "la recortada es igual a la tal cual"
j1.cerrar_panel()
red.desmentir(j1, pub, con_ubicacion=True)
desm = next(p for p in red.publicaciones if p.tipo == "desmentido")
# Equipo (en el celular de quien la publicó; a los demás les llega por la red).
del dibujadas[:]
red.pestanas[j1] = "equipo"
logica.abrir(g, j1)
assert ("post", desm) in j1.panel["opciones"]
g._dibujar()
pygame.image.save(g.screen, os.path.join(OUT, "foto_f_equipo.png"))
assert dibujadas, "la foto no sale en la pestaña Equipo"
chica = dibujadas[0]
igual = pygame.transform.smoothscale(tomada, chica.get_size())
cw, ch = chica.get_size()
assert all(chica.get_at((x, y)) == igual.get_at((x, y)) for x, y in ((cw // 2, ch // 2), (3, 3), (cw - 4, ch - 4))), \
    "la foto de Equipo no es la que se tomó"
# La publicación.
del dibujadas[:]
j1.abrir_panel(logica._post(g, j1, desm))
g._dibujar()
pygame.image.save(g.screen, os.path.join(OUT, "foto_g_publicacion.png"))
assert dibujadas and dibujadas[0].get_width() > cw, "en la publicación la foto no sale (o no es más grande)"
# En Misiones (los rumores) no.
del dibujadas[:]
red.pestanas[j1] = "misiones"
logica.abrir(g, j1)
g._dibujar()
assert not dibujadas, "salió una foto en Misiones"
foto.dibujar_en_celular = original
print(f"5b. local: al publicar, tal cual y recortada; en Equipo la foto que se tomó ({cw}x{ch}) y en la "
      f"publicación más grande ({dibujadas and 0 or 'ok'}); en Misiones no: OK")

print("OK prueba_foto")
