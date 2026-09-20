"""Árbol de diálogo: conversaciones ramificadas con los habitantes de Ciudad Nova.

Las cinco preguntas que plantea el laboratorio:

1) ¿Qué problema resuelve?
   Que hablar con un vecino no sea un texto fijo sino una conversación con
   consecuencias. El jugador escoge qué responder y según eso el NPC le da
   información verificada, le suelta un rumor, o desconfía de él. Cada camino
   de la conversación afecta los indicadores de la ciudad de forma distinta.

2) ¿Por qué esta estructura?
   Porque una conversación ramificada es un árbol por naturaleza: una
   intervención abre varias respuestas posibles, cada respuesta lleva a otra
   intervención, y así hasta cerrar. Guardarlo como árbol permite escribir el
   contenido como datos (data/dialogos_ejemplo.py) sin tocar el código, y hace
   que agregar una rama nueva sea agregar un diccionario más.

3) ¿Qué variante se utiliza?
   Un árbol N-ario, igual que el árbol de decisión, porque un NPC puede
   ofrecer dos o tres respuestas según el momento. La diferencia con el árbol
   de decisión es la profundidad: aquel tiene tres niveles fijos
   (publicación - opción - consecuencia) mientras que un diálogo puede seguir
   bajando mientras la conversación siga.

4) ¿Cómo se insertan y eliminan elementos?
   Se construye recursivamente con construir_desde_dict, que baja por el
   diccionario anidado colgando cada respuesta con NodoDialogo.agregar_hijo.
   No se eliminan nodos en partida: el diálogo es contenido fijo. Lo que sí
   cambia es la posición del jugador dentro del árbol.

5) ¿Cómo se realiza su recorrido?
   Igual que el árbol de decisión, lo recorre el jugador: se arranca en la
   raíz y cada respuesta que elige baja un nivel, aplicando los efectos del
   nodo al que llega. La conversación termina al caer en un nodo sin hijos.
   `profundidad` y `contar_finales` sí recorren el árbol completo de forma
   automática (en postorden) para poder describirlo.
"""

from Estructuras.nodo_dialogo import NodoDialogo


class ArbolDialogo:
    def __init__(self, nombre_npc="Vecino"):
        self.nombre_npc = nombre_npc
        self.raiz = None

    def construir_desde_dict(self, data):
        """Construye el árbol desde un diccionario anidado y lo deja como raíz."""
        if not isinstance(data, dict):
            raise TypeError("El diálogo debe ser un diccionario con estructura de árbol.")

        self.nombre_npc = data.get("npc", self.nombre_npc)
        self.raiz = self._construir_nodo(data)
        return self.raiz

    def _construir_nodo(self, data):
        nodo = NodoDialogo(
            texto=data.get("texto", ""),
            respuesta=data.get("respuesta"),
            efectos=data.get("efectos", {}),
        )
        for hijo in data.get("hijos", []):
            nodo.agregar_hijo(self._construir_nodo(hijo))
        return nodo

    def aplicar_efectos(self, nodo, estado_ciudad):
        """Suma los efectos del nodo a los indicadores, acotados entre 0 y 100."""
        if nodo is None:
            return
        for clave, valor in (nodo.efectos or {}).items():
            if clave in estado_ciudad:
                estado_ciudad[clave] = max(0, min(100, int(estado_ciudad[clave]) + int(valor)))

    def responder(self, nodo_actual, indice):
        """Baja al hijo `indice` (la respuesta que eligió el jugador).

        Devuelve el nodo nuevo, o None si el índice no existe.
        """
        if nodo_actual is None or indice < 0 or indice >= len(nodo_actual.hijos):
            return None
        return nodo_actual.hijos[indice]
