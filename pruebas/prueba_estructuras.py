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

from Estructuras.arbol_decision import ArbolDecision
from Estructuras.abb_publicaciones import ArbolPublicaciones
from data.publicaciones_ejemplo import PUBLICACIONES_EJEMPLO


if __name__ == "__main__":
    print("Inicializando Alcalde Digital...")

    arbol_publicaciones = ArbolPublicaciones()
    for idx, item in enumerate(PUBLICACIONES_EJEMPLO, start=1):
        arbol_publicaciones.insertar(idx * 10, item["texto"], "rumor")

    root_data = PUBLICACIONES_EJEMPLO[0]
    arbol = ArbolDecision(root_data)
    root_node = arbol.construir_desde_dict(root_data)
    print("Raíz:", root_node.texto)
    print("Recorrido de prueba:", root_node.hijos[0].texto, root_node.hijos[0].hijos[0].texto)

    print("ABB inorden:")
    for pub in arbol_publicaciones.recorrido_inorden():
        print(pub)

    print("Búsqueda por veracidad:")
    for ver in [10, 20, 30]:
        print(ver, arbol_publicaciones.buscar(ver))

    print("Fin de la prueba de lógica de estructuras.")
