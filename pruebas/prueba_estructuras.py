"""Prueba por consola de las estructuras, sin abrir ventana.

    python pruebas/prueba_estructuras.py

Al vivir en pruebas/ hay que meter la raíz del proyecto en sys.path, o los
import de Estructuras/ y data/ no la encuentran.
"""

import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

from data.comportamiento_alien import ARBOL_ALIEN
from data.logros import ARBOL_LOGROS
from Estructuras.arbol_comportamiento import ArbolComportamiento
from Estructuras.arbol_logros import ArbolLogros


if __name__ == "__main__":
    print("Inicializando NEXUS...")

    alien = ArbolComportamiento(ARBOL_ALIEN)
    accion, camino = alien.decidir({"ve_jugador": True, "jugador_al_alcance": False})
    print("Árbol del alien: si ve a alguien ->", accion)

    logros = ArbolLogros(ARBOL_LOGROS)
    print("Árbol de logros:", logros.total(), "logros en", len(logros.por_niveles()), "niveles")
    nuevos = logros.conseguir("libertad")
    print("Conseguir 'Libertad' marca:", [n.nombre for n in nuevos])
    assert nuevos[0] is logros.raiz and logros.buscar("chatarrero").obtenido

    print("Fin de la prueba de lógica de estructuras.")
