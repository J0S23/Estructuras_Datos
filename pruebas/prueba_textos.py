"""Comprueba que la tipografía del juego pueda dibujar todo el texto que usamos.

    python pruebas/prueba_textos.py

Determination Mono no trae los glifos de flecha (U+2190-2193). Escribir "↑/↓"
en una pista de teclas no da ningún error: la fuente dibuja el cuadrito vacío
de .notdef y el juego sigue como si nada, así que solo se nota jugando y
mirando con atención. Esta prueba lo detecta antes.

Recorre las cadenas de todos los .py del juego y avisa de cualquier carácter
que la fuente no sepa dibujar. Las tildes, la ñ y los signos de apertura sí
están, así que no hay que renunciar a escribir bien en español.

Cómo se detecta: no sirve `Font.metrics()`, que devuelve medidas también para
los glifos que faltan. Lo que sí funciona es dibujar el carácter y compararlo
con el cuadrito que sale al pedir uno del área de uso privado (U+E000), que
ninguna fuente normal define.
"""

import ast
import io
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

import pygame

pygame.init()
pygame.display.set_mode((10, 10))

from fuentes import fuente_de_tamano, ruta_fuente

# Carpetas que no son del juego. Editores/ viene de EmpatiaQuest y usa flechas
# en sus propias pantallas; no se toca aquí.
SALTAR = {".venv", "__pycache__", ".git", "capturas", "Editores", ".vscode"}

CARACTER_INEXISTENTE = ""   # área de uso privado: nadie lo define


def construir_detector(tam=28):
    f = fuente_de_tamano(tam)
    referencia = pygame.image.tostring(
        f.render(CARACTER_INEXISTENTE, True, (255, 255, 255), (0, 0, 0)), "RGB")

    def sin_glifo(caracter):
        dibujo = pygame.image.tostring(
            f.render(caracter, True, (255, 255, 255), (0, 0, 0)), "RGB")
        return dibujo == referencia

    return sin_glifo


# Este mismo archivo se salta: contiene el carácter inexistente a propósito.
ESTE_ARCHIVO = os.path.basename(__file__)


def archivos_del_juego():
    for carpeta, subcarpetas, archivos in os.walk("."):
        subcarpetas[:] = [d for d in subcarpetas if d not in SALTAR]
        for archivo in archivos:
            if archivo.endswith(".py") and archivo != ESTE_ARCHIVO:
                yield os.path.join(carpeta, archivo)


def main():
    sin_glifo = construir_detector()
    problemas = []

    for ruta in sorted(archivos_del_juego()):
        try:
            arbol = ast.parse(io.open(ruta, encoding="utf-8").read())
        except SyntaxError:
            continue
        for nodo in ast.walk(arbol):
            if not (isinstance(nodo, ast.Constant) and isinstance(nodo.value, str)):
                continue
            # Los docstrings no se dibujan nunca.
            if "\n" in nodo.value and len(nodo.value) > 120:
                continue
            for caracter in sorted(set(nodo.value)):
                if ord(caracter) > 127 and sin_glifo(caracter):
                    problemas.append((ruta, nodo.lineno, caracter, nodo.value.strip()[:60]))

    print(f"Fuente: {ruta_fuente()}")
    if not problemas:
        print("OK: la fuente puede dibujar todos los caracteres del texto del juego.")
        return 0

    print(f"\n{len(problemas)} caracteres que la fuente NO puede dibujar "
          f"(saldrían como cuadritos):")
    for ruta, linea, caracter, muestra in problemas:
        print(f"  {ruta}:{linea}  {caracter!r} (U+{ord(caracter):04X})  en: {muestra!r}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
