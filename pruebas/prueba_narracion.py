"""La narración de Lucas (docs/guion_narrador.md), sin ventana ni parlantes.

    python pruebas/prueba_narracion.py

1. Qué archivos del narrador están en Audio/Narrador/ (y cuáles faltan).
2. Cada narración se puede medir (juego/voces.duracion_ms) y la escena dura
   al menos lo que la voz (la cinemática y los finales se alargan solos).
3. Los subtítulos van con la voz (Audio/Narrador/cortes.json): cada línea
   aparece cuando Lucas la empieza a decir, en orden y dentro del audio; sin
   esa marca (o sin audio), se reparten parejo, como antes.
4. La cinemática de apertura toca cada narración una sola vez, en orden (la
   escena 1 va al paso de la voz: envía la dirección cuando Lucas lo dice).
5. Solo Esc salta la apertura y la escena de los finales (ni Enter, ni otra
   tecla, ni un clic). Los finales tocan la suya y la frase una vez cada una.
"""

import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

import pygame

pygame.init()
pygame.display.set_mode((1280, 720))

from juego import voces
from screens import cinematica as c
from data.historia import FINALES

NARRADOR = ([f"apertura_{i + 1}" for i in range(len(c.CINEMATICA))] + ["apertura_frase"]
            + [f"final_{k}" for k in FINALES] + ["final_frase", "final_frase_liberados"])

# -- 1 y 2 --------------------------------------------------------------------------------
hay = [n for n in NARRADOR if voces.ruta(n)]
faltan = [n for n in NARRADOR if not voces.ruta(n)]
print(f"narrador: {len(hay)} de {len(NARRADOR)}" + (f" (faltan: {', '.join(faltan)})" if faltan else ""))
for n in hay:
    assert voces.duracion_ms(n) > 1000, (n, voces.duracion_ms(n))
escenas, frase = c.duraciones_apertura()
for i, ms in enumerate(escenas):
    voz = f"apertura_{i + 1}"
    if voces.ruta(voz):
        assert ms >= c.VOZ_ESCENA_DESDE_MS + voces.duracion_ms(voz), (voz, ms)
if voces.ruta("apertura_frase"):
    assert frase >= c.VOZ_FRASE_DESDE_MS + voces.duracion_ms("apertura_frase")
for final in c.TIEMPOS_FINAL:
    a, b, cc = c.tiempos_final(final)
    textos, la_frase = c._voces_final(final)
    if voces.ruta(textos):
        assert b + c.ADELANTO_TEXTOS.get(final, 0) >= c.VOZ_FINAL_DESDE_MS + voces.duracion_ms(textos), final
    if voces.ruta(la_frase):
        assert cc >= c.VOZ_FRASE_DESDE_MS + voces.duracion_ms(la_frase), final
print("cada escena dura al menos lo que su narración")

# -- 3 ------------------------------------------------------------------------------------
def revisar(nombre, textos, total, desde):
    marcas = voces.cortes(nombre, len(textos))
    if voces.ruta(nombre) is None:
        assert marcas is None
        return "sin audio (parejo)"
    assert marcas is not None, f"{nombre}: falta en cortes.json (correr Audio/generar_cortes.py)"
    assert marcas == sorted(marcas) and len(set(marcas)) == len(marcas), (nombre, marcas)
    assert marcas[-1] < voces.duracion_ms(nombre), (nombre, marcas)
    vistas = []
    for t in range(0, int(total), 50):
        linea = c._linea_narrada(textos, t, total, nombre, desde)
        if linea is not None and (not vistas or vistas[-1] != linea[0]):
            vistas.append(linea[0])
            assert abs(t - (desde + marcas[linea[0]])) <= 50, (nombre, linea[0], t)
    assert vistas == list(range(len(textos))), (nombre, vistas)
    return f"{marcas}"


for i, escena in enumerate(c.CINEMATICA):
    print(f"apertura_{i + 1}:", revisar(f"apertura_{i + 1}", escena["textos"], escenas[i], c.VOZ_ESCENA_DESDE_MS))
for final in c.TIEMPOS_FINAL:
    a, b, cc = c.tiempos_final(final)
    total = b + c.ADELANTO_TEXTOS.get(final, 0)
    print(f"final_{final}:", revisar(f"final_{final}", FINALES[final]["escena"], total, c.VOZ_FINAL_DESDE_MS))
# Sin marca: parejo (como antes).
linea = c._linea_narrada(["a", "b"], 600, 1000, voz=None)
assert linea[0] == 1 and abs(linea[2] - 500) < 1e-6
print("los subtítulos van con la voz")

# -- 4 ------------------------------------------------------------------------------------
tocadas = []
c._voz = lambda nombre: tocadas.append(nombre)
cine = c.Cinematica()
while not cine.terminada:
    cine.actualizar(50)
esperadas = [n for _, n in cine.voces if voces.ruta(n)]
assert [n for n in tocadas if n in esperadas] == esperadas, (tocadas, esperadas)
assert len(tocadas) == len(set(tocadas)), tocadas
print(f"apertura: {len(esperadas)} narraciones, cada una una vez y en orden")
# La escena 1 va al paso de Lucas: la dirección se envía cuando dice "y la envía".
marcas = voces.cortes("apertura_1", len(c.CINEMATICA[0]["textos"]))
if marcas:
    enviada = next(ms for ms, nombre, _ in cine.sonidos if nombre == "menu_ok")
    assert enviada >= c.VOZ_ESCENA_DESDE_MS + marcas[1], (enviada, marcas)
    assert abs(c._interpolar(c._anclas_escena_1(cine.duraciones[0]), enviada) - 8500) < 2
    print(f"escena 1: la envía a los {enviada / 1000:.1f} s, con la narración")
pantalla = pygame.Surface((1280, 720))
for final in c.TIEMPOS_FINAL:
    tocadas.clear()
    c._narrando.update(final=None, t=-1)
    total = c.intro_final_ms(final)
    for t in range(0, total, 100):
        c._narrar_final(final, t)
    textos, la_frase = c._voces_final(final)
    assert tocadas == [textos, la_frase], (final, tocadas)
    for t in (0, total // 3, total // 2, total - 200):
        c.dibujar_final(pantalla, final, t, [])
print("finales: la narración y la frase, una vez cada una")

# -- 5. Solo Esc salta las cinemáticas -------------------------------------------------------
from juego.app import Game
from screens import resultados as pantalla_resultados
g = Game()
g.abrir_intro()
for evento in (pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode="\r", mod=0),
               pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, unicode=" ", mod=0),
               pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(10, 10))):
    pygame.event.post(evento)
    g._manejar_eventos()
    assert not g.intro.terminada, f"{pygame.event.event_name(evento.type)} ya no salta la apertura"
pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, unicode="\x1b", mod=0))
g._manejar_eventos()
assert g.intro.terminada, "Esc salta la apertura"
# La escena del final, en los resultados.
pantalla_resultados._entrada.update(intro=60000, t0=pygame.time.get_ticks())
g._reiniciar_resultados()
for tecla in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_LEFT, pygame.K_a):
    g._tecla_resultados(tecla)
    assert pantalla_resultados.en_intro(), f"{pygame.key.name(tecla)} ya no salta el final"
g._click_resultados((10, 10))
assert pantalla_resultados.en_intro(), "un clic ya no salta el final"
g._tecla_resultados(pygame.K_ESCAPE)
assert not pantalla_resultados.en_intro(), "Esc salta el final"
assert g.resultados_vista == "resumen" and not g.transitions.active, "y no se va al menú de una"
print("las cinemáticas solo se saltan con Esc (la apertura y los finales)")
print("\nOK prueba_narracion")
