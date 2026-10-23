"""Grafo dirigido de NEXUS: quién le llega a quién en la red social.

Las cinco preguntas que plantea el laboratorio:

1) ¿Qué problema resuelve?
   Modelar cómo viaja una publicación por NEXUS. Un rumor de los aliens no le
   llega a todos de una: le llega a quienes siguen al que lo publicó, después a
   los que siguen a esos, y así. Con el grafo se sabe a quién alcanza cada
   publicación, en qué orden, por dónde pasó (para rastrear al que empezó un
   rumor) y qué pasa con la red cuando se reporta una cuenta falsa.

2) ¿Por qué esta estructura?
   Porque una red social ES un grafo: las cuentas son nodos y "lo que publica
   A le aparece a B" es una arista. No es un árbol: una cuenta tiene muchos
   seguidores y sigue a muchas, hay ciclos (A sigue a B y B a A) y a una
   cuenta le puede llegar lo mismo por dos caminos distintos. Ni una lista ni
   un árbol pueden representar eso.

3) ¿Qué variante se utiliza?
   Un grafo **dirigido y sin pesos**, guardado como **lista de adyacencia**: un
   diccionario `nodo -> conjunto de nodos a los que les llega lo que publica`.
   Dirigido porque seguir no es recíproco (que tú sigas a alguien no hace que
   él vea lo tuyo). Lista de adyacencia y no matriz porque la red es dispersa:
   cada cuenta tiene unas pocas conexiones, no todas con todas. Cada nodo
   guarda además sus datos (nombre, usuario, color...) en `datos`.

4) ¿Cómo se insertan y eliminan elementos?
   `agregar_nodo` y `agregar_arista` en O(1). `eliminar_nodo` borra la cuenta y
   todas las aristas que entran y salen de ella (O(V), hay que quitarla del
   conjunto de cada vecino). Es lo que pasa al **reportar un bot**: desaparece
   de la red y lo que se propagaba a través de él deja de pasar por ahí.

5) ¿Cómo se realiza su recorrido?
   - **BFS por niveles** (`expandir` / `bfs_niveles`): una publicación avanza un
     nivel por "tick": primero les llega a los seguidores directos, después a
     los seguidores de ellos... Es el recorrido por niveles de los árboles,
     pero con un conjunto de visitados para no dar vueltas en los ciclos.
     `puede_pasar` deja frenar la propagación en ciertos nodos (una cuenta que
     ya confía en los humanos no reenvía el rumor).
   - **Camino más corto** (`camino_mas_corto`, BFS guardando el padre de cada
     nodo): por dónde te llegó un rumor, desde la cuenta que lo empezó. En un
     grafo sin pesos el BFS ya da el camino con menos saltos.
   - **Componentes conexas** (`componentes`): grupos de cuentas que solo se
     hablan entre ellas (burbujas), mirando las aristas sin dirección.
"""

from collections import deque


class Grafo:
    def __init__(self):
        self.ady = {}      # nodo -> set(nodos a los que les llega lo que publica)
        self.datos = {}    # nodo -> dict con lo que se quiera guardar del nodo

    # -- Insertar y eliminar ----------------------------------------------------------

    def agregar_nodo(self, nodo, **datos):
        if nodo not in self.ady:
            self.ady[nodo] = set()
            self.datos[nodo] = {}
        self.datos[nodo].update(datos)

    def agregar_arista(self, desde, hasta):
        """Lo que publica `desde` le llega a `hasta`."""
        if desde == hasta:
            return
        self.agregar_nodo(desde)
        self.agregar_nodo(hasta)
        self.ady[desde].add(hasta)

    def eliminar_nodo(self, nodo):
        """Borra la cuenta y todas sus aristas (las que salen y las que entran)."""
        if nodo not in self.ady:
            return False
        del self.ady[nodo]
        del self.datos[nodo]
        for vecinos in self.ady.values():
            vecinos.discard(nodo)
        return True

    # -- Consultas ---------------------------------------------------------------------

    def __contains__(self, nodo):
        return nodo in self.ady

    def __len__(self):
        return len(self.ady)

    def nodos(self):
        return list(self.ady)

    def vecinos(self, nodo):
        """A quiénes les llega lo que publica `nodo` (sus seguidores)."""
        return self.ady.get(nodo, set())

    def seguidos_por(self, nodo):
        """De quiénes le llega algo a `nodo` (aristas que entran)."""
        return [n for n, vecinos in self.ady.items() if nodo in vecinos]

    def grado_salida(self, nodo):
        return len(self.ady.get(nodo, ()))

    def aristas(self):
        return sum(len(v) for v in self.ady.values())

    # -- Recorridos ----------------------------------------------------------------------

    def expandir(self, frontera, visitados, puede_pasar=None):
        """Un paso del BFS: el siguiente nivel a partir de `frontera`.

        Los nodos de `frontera` que no `puede_pasar` no reenvían. Marca los
        nuevos en `visitados` y devuelve el nivel nuevo como lista de
        (nodo, de_quien_le_llego).
        """
        nivel = []
        for nodo in frontera:
            if puede_pasar is not None and not puede_pasar(nodo):
                continue
            for vecino in sorted(self.vecinos(nodo), key=str):
                if vecino not in visitados:
                    visitados.add(vecino)
                    nivel.append((vecino, nodo))
        return nivel

    def bfs_niveles(self, origen, puede_pasar=None, max_niveles=None):
        """[[origen], [seguidores], [seguidores de seguidores], ...]."""
        if origen not in self.ady:
            return []
        niveles = [[origen]]
        visitados = {origen}
        while max_niveles is None or len(niveles) <= max_niveles:
            nivel = self.expandir(niveles[-1], visitados, puede_pasar)
            if not nivel:
                break
            niveles.append([n for n, _ in nivel])
        return niveles

    def camino_mas_corto(self, origen, destino):
        """Lista de nodos de `origen` a `destino` con menos saltos, o None."""
        if origen not in self.ady or destino not in self.ady:
            return None
        padre = {origen: None}
        cola = deque([origen])
        while cola:
            nodo = cola.popleft()
            if nodo == destino:
                camino = []
                while nodo is not None:
                    camino.append(nodo)
                    nodo = padre[nodo]
                return list(reversed(camino))
            for vecino in sorted(self.vecinos(nodo), key=str):
                if vecino not in padre:
                    padre[vecino] = nodo
                    cola.append(vecino)
        return None

    def componentes(self):
        """Grupos de nodos conectados, ignorando la dirección de las aristas."""
        sin_direccion = {n: set(v) for n, v in self.ady.items()}
        for n, vecinos in self.ady.items():
            for v in vecinos:
                sin_direccion[v].add(n)
        vistos, grupos = set(), []
        for inicio in self.ady:
            if inicio in vistos:
                continue
            grupo, cola = [], deque([inicio])
            vistos.add(inicio)
            while cola:
                nodo = cola.popleft()
                grupo.append(nodo)
                for v in sin_direccion[nodo]:
                    if v not in vistos:
                        vistos.add(v)
                        cola.append(v)
            grupos.append(grupo)
        return grupos
