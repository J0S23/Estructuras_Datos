"""Dibuja los paneles a varias resoluciones para revisar que el texto quepa.

    python pruebas/prueba_paneles.py

Los paneles se dimensionan según su contenido y el viewport, así que un cambio
en un texto puede romper el encaje solo en algunas resoluciones. Esta prueba
los dibuja en las combinaciones que aprietan —sobre todo un viewport de cuatro
jugadores en pantalla chica— y deja las imágenes en pruebas/capturas/paneles/
para revisarlas a ojo.
"""

import os, sys
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)
import pygame; pygame.init(); pygame.display.set_mode((100,100))
OUT = os.path.join(RAIZ, "pruebas", "capturas", "paneles")
os.makedirs(OUT, exist_ok=True)

from entidades.jugador import Jugador
from Movimiento.Personaje import Personaje, CONTROLES_FLECHAS
from screens.panel_habilidades import render_panel_habilidades, precargar_iconos
from screens.paneles import render_panel
from screens.partida import calcular_viewports

precargar_iconos(["Forjador"])
p = Personaje(0, 0, os.path.join("Imagenes","Personajes","Forjador"), controles=CONTROLES_FLECHAS)

# El panel más cargado del juego: la Terminal NEXUS con el caso del infiltrado.
CASO = {"tipo": "opciones", "titulo": "NEXUS · El infiltrado",
        "cuerpo": ["Alguien en NEXUS es un alien cambiaformas haciéndose pasar por "
                   "un prisionero. Busquen las 3 pruebas por la nave y súbanlas aquí.",
                   "Pruebas subidas: 1/3", "", "Sospechosos:",
                   "  - Lía, la piloto: Laboratorio, de día, con lentes",
                   "  x Dra. Vega: descartado",
                   "  - Mecánico Ruiz: Laboratorio, de noche, sin lentes",
                   "  x Cabo Duarte: descartado",
                   "  - Nadia (cocina): Laboratorio, de noche, con lentes"],
        "opciones": [{"texto": "Subir pruebas (2)"}, {"texto": "Acusar a alguien"},
                     {"texto": "Salir"}],
        "pie": "[Flechas] elegir   [ENTER] confirmar"}

RESOLUCIONES = [(1920,1080), (1366,768), (1280,720)]
JUGADORES = [2, 4]

for ancho, alto in RESOLUCIONES:
    for n in JUGADORES:
        vista = calcular_viewports(ancho, alto, n)[1]
        sup = pygame.Surface((ancho, alto)); sup.fill((40,44,60))

        # --- panel de habilidades con la rama mas larga ---
        j = Jugador(p, "Forjador", puesto=1); j.puntos = 200
        j.arbol.desbloquear("REPARACION", 200)
        j.abrir_panel({"tipo":"habilidades"})
        render_panel_habilidades(sup, vista, j)
        pygame.image.save(sup.subsurface(vista).copy(), f"{OUT}/hab_{ancho}x{alto}_{n}j.png")

        # --- panel de opciones mas cargado: el caso del infiltrado ---
        j2 = Jugador(p, "Forjador", puesto=1)
        j2.abrir_panel(dict(CASO))
        sup2 = pygame.Surface((ancho, alto)); sup2.fill((40,44,60))
        render_panel(sup2, vista, j2)
        pygame.image.save(sup2.subsurface(vista).copy(), f"{OUT}/op_{ancho}x{alto}_{n}j.png")
        print(f"  {ancho}x{alto} {n} jugadores -> viewport {vista.width}x{vista.height}")
print("listo")
