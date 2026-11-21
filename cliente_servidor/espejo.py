"""El "espejo": un Game de verdad en el cliente que solo sirve para dibujar.

En vez de reescribir el dibujo para el modo en red, el cliente arma la misma
partida que el servidor (mismo mapa, roles, dificultad y semilla) con el
`Game` de juego/app.py, NUNCA la actualiza (no corre `_actualizar_partida`:
el que manda es el servidor) y en cada cuadro le copia encima lo que dice la
instantánea: posiciones, vidas, paneles, misión, eventos, linterna... Después
llama las MISMAS funciones de dibujo del modo local (`_dibujar_partida_en`,
que usa screens/partida.py, paneles.py, celular.py, oscuridad.py...). Así se
ve igual que el local: vistas divididas, HUD, oscuridad y visión, sustos,
paneles, celular.

Lo que no viaja (referencias entre objetos, imágenes, árboles de
comportamiento) se queda como lo armó el espejo; ver cliente_servidor/estado.py.
"""

import random

import pygame

from cliente_servidor import estado as E
from cliente_servidor.protocolo import lista as a_lista


# Listas de dicts de datos (no de objetos) que pueden empezar vacías en el
# espejo y llenarse en el servidor: ver Espejo.aplicar.
LISTAS_DE_DATOS = {"mision": ("consumibles",), "infiltrado": ("pruebas",)}


class _Preso(dict):
    """En el servidor `jugador.preso` es la celda (un dict); en el espejo
    basta con algo que diga "sí" y aguante un .get()."""

    def __bool__(self):
        return True


class Espejo:
    def __init__(self, juego, bienvenida):
        self.g = juego
        self.b = bienvenida
        self.aliens = {}           # nombre -> objeto Alien del espejo
        self.pubs = {}             # id -> Publicacion del espejo (ver _publicaciones)
        self._pasos_npc = {}       # id del NPC -> (posición, cuándo cambió, último paso)
        self._tareas = {}          # id del jugador -> (su minijuego, ms desde la última instantánea)
        self._agujas = {}          # id del jugador -> ((aguja, sentido) del servidor, cuándo llegó)
        self._reloj_ms = None      # para avanzar las animaciones con el tiempo real
        self._dt_ms = 0
        # Lo último que se copió de cada sección de la instantánea: una
        # sección que no cambió llega como EL MISMO dict (protocolo.Reconstructor
        # solo rehace las que cambian) y no se vuelve a copiar (ver `aplicar`).
        self._aplicadas = {}
        self.listo = False
        self.error = None

    def preparar(self):
        """Arma la partida igual que el servidor (tarda unos segundos: se
        puede llamar desde otro hilo, como la pantalla de carga del juego)."""
        from juego import app as App
        from juego.dificultad import Dificultad
        g, b = self.g, self.b
        if b.get("dificultad"):
            g.dificultad = Dificultad(b["dificultad"])
        g.cantidad_jugadores = b["jugadores"]
        # El modo feria es el de la partida (lo escogió quien la creó), no el
        # de Menú > Opciones de esta laptop: si no, el espejo recortaba otra nave.
        g.modo_feria_forzado = bool(b.get("feria"))
        g.abrir_seleccion_roles(ir=False)
        for estado, rol in zip(g.seleccion_roles, b["roles"]):
            estado["rol"], estado["listo"] = rol, True
        from juego import objetos_mapa
        mapa_activo = objetos_mapa.mapa_activo
        objetos_mapa.mapa_activo = lambda: b["mapa"]
        from cliente_servidor.servidor import todos_se_mueven
        try:
            random.seed(b.get("semilla"))
            with todos_se_mueven():          # (como el servidor: ver servidor.todos_se_mueven)
                g._preparar_partida()
        finally:
            objetos_mapa.mapa_activo = mapa_activo
            g.modo_feria_forzado = None      # (el Game es el del menú: las partidas locales, con lo suyo)
            # El random es el de todo el juego (el espejo usa el Game del
            # menú): sin esto, después de una partida en red el random seguía
            # "sembrado" con la semilla del servidor y la siguiente partida
            # local salía siempre igual.
            random.seed()
        # (El tutorial NO se salta aquí: lo dice la instantánea. Saltarlo
        # además despertaba a los aliens del espejo con su sonido de susto.)
        if not b.get("presentaciones", True):
            g.presentacion = None
        for alien in list(g.aliens) + [getattr(g, "sombra", None), getattr(g, "cambiaformas", None)]:
            if alien is not None and hasattr(alien, "nombre"):
                self.aliens[alien.nombre] = alien
        self.listo = True

    def controles(self, esquemas):
        """{número de jugador: esquema} de los que juegan en ESTA laptop. Las
        pistas en pantalla ("presiona E", "Botón A", "Flechas") salen del
        esquema del jugador; el espejo lo armaba con el del puesto en el
        servidor (J2 = flechas, J3 = mando 1), que no es con lo que juega
        aquí: en la otra laptop J3 con WASD veía "presiona ?". Se llama en
        cada cuadro (un mando se puede conectar a mitad de partida)."""
        from entidades.jugador import TECLAS_POR_PUESTO, NOMBRE_CONTROLES
        from entidades import acciones_rol
        from juego.app import CONTROLES_POR_PUESTO
        mandos = getattr(self.g, "mandos", None)
        for numero, esquema in esquemas.items():
            if not 0 <= numero < len(self.g.jugadores):
                continue
            j = self.g.jugadores[numero]
            # La línea del HUD ("[Q] escoge tu habilidad") la arma el servidor
            # con las teclas del PUESTO: aquí se rehace con las de esta laptop
            # (J1 con flechas veía [Q], que es de WASD).
            try:
                j.info = acciones_rol.linea_de_estado(j)
            except Exception:
                pass
            con_mando = bool(mandos is not None and mandos.hay_mando(esquema))
            if getattr(j, "esquema", None) == esquema and j.con_mando == con_mando:
                continue
            j.esquema, j.con_mando = esquema, con_mando
            j.teclas = TECLAS_POR_PUESTO[esquema]
            j.controles_nombre = f"Mando {esquema - 1}" if con_mando else NOMBRE_CONTROLES[esquema]
            j.personaje.controles = CONTROLES_POR_PUESTO[esquema]
            j.personaje.controles_nombre = j.controles_nombre

    # -- Copiar la instantánea encima ----------------------------------------------

    def aplicar(self, secciones, interpolado=None):
        g = self.g
        interpolado = interpolado or {}
        ahora = pygame.time.get_ticks()
        self._dt_ms = 0 if self._reloj_ms is None else max(0, min(100, ahora - self._reloj_ms))
        self._reloj_ms = ahora
        # Las referencias ({"P": id}, {"J": 1}, {"A": "Vigía 3"}) se cambian por
        # los objetos de ESTE espejo (con dos sesiones en un proceso, como en las
        # pruebas, cada una pone el suyo antes de aplicar).
        E.RESOLVER = self._resolver
        E.nueva_pasada()
        # Antes se copiaba TODA la instantánea encima en cada cuadro (~1.7 ms
        # aquí, varios en el PC de Diego, solo en esto). Pero el cliente dibuja
        # a 60 y las instantáneas llegan a 30, y de las que llegan la mayoría
        # de las secciones no cambió (la misión, los casilleros, las
        # terminales, las publicaciones...): esas llegan como el mismo dict
        # de antes y se saltan. Las posiciones (interpoladas) y las
        # animaciones sí van en cada cuadro.
        aplicadas = self._aplicadas

        def cambio(clave):
            datos = secciones.get(clave)
            return datos is not None and datos is not aplicadas.get(clave)

        if cambio("pubs"):
            self._publicaciones(secciones.get("pubs"))
            aplicadas["pubs"] = secciones.get("pubs")
        glob = secciones.get("g", {})
        if cambio("g"):
            for clave, v in glob.items():
                if clave.startswith("G."):
                    try:
                        setattr(g, clave[2:], E.a_python(v))
                    except (AttributeError, TypeError):
                        pass
            aplicadas["g"] = glob
        # De qué jugadores se copió la sección entera en este cuadro (su panel,
        # su cursor, su minijuego vuelven a ser los del servidor): ahí el
        # cliente vuelve a poner encima lo que ya presionó y el servidor todavía
        # no vio (cliente.Sesion._eco).
        self.completos = set()
        for i, jugador in enumerate(g.jugadores):
            datos = secciones.get(f"j{i}")
            if datos is not None:
                completo = datos is not aplicadas.get(f"j{i}")
                self._jugador(jugador, datos, interpolado.get(f"j{i}"), completo=completo)
                aplicadas[f"j{i}"] = datos
                if completo:
                    self.completos.add(i)
        self._aliens(secciones.get("al", {}), interpolado)
        from cliente_servidor.servidor import OBJETOS, LISTAS
        for clave, nombre in OBJETOS.items():
            datos = secciones.get(clave)
            objeto = getattr(g, nombre, None)
            if datos is None or datos is aplicadas.get(clave):
                continue
            if not datos.get("ok"):
                # En el servidor ya no está. Por delta llega como {"ok": None,
                # lo demás: None} (las claves que se borraron), no como {}:
                # antes eso le ponía None a TODOS los atributos del objeto del
                # espejo (y la presentación o el tutorial no se quitaban).
                setattr(g, nombre, None)
                continue
            if objeto is not None:
                cuerpo = {k: v for k, v in datos.items() if k != "ok"}
                if nombre == "cambiaformas" and objeto in g.aliens:
                    # Su lugar ya lo puso `_aliens` (interpolado, como los
                    # demás): con el de esta sección (el último que llegó) se
                    # iba y volvía en cada cuadro en que esta cambiaba.
                    cuerpo.pop("hitbox", None)
                if nombre == "npcs" and isinstance(cuerpo.get("npcs"), list):
                    self._npcs(objeto, cuerpo.pop("npcs"))
                if nombre == "logros" and "obtenidos" in cuerpo:
                    self._logros(objeto, cuerpo.pop("obtenidos"))
                E.aplicar(objeto, cuerpo)
                for atributo in LISTAS_DE_DATOS.get(nombre, ()):
                    # Una lista de dicts que en el espejo estaba VACÍA no se
                    # llenaba nunca (estado._mezclar no sabe si son datos o
                    # objetos y deja la del espejo): el decodificador que suelta
                    # el Tecnomante eliminado o desconectado, o lo que alguien
                    # suelta con la tecla, no aparecía en las otras laptops.
                    nuevos = cuerpo.get(atributo)
                    if (isinstance(nuevos, list) and nuevos and getattr(objeto, atributo, None) == []
                            and all(isinstance(d, dict) for d in nuevos)):
                        setattr(objeto, atributo, E.a_python(nuevos))
            aplicadas[clave] = datos
        for clave, nombre in LISTAS.items():
            datos = secciones.get(clave)
            lista = getattr(g, nombre, None)
            if datos is None or not isinstance(lista, list) or datos is aplicadas.get(clave):
                continue
            nuevos = a_lista(datos)
            for k, d in enumerate(nuevos):
                if d is None:
                    continue
                if k < len(lista):
                    if hasattr(lista[k], "__dict__"):
                        E.aplicar(lista[k], d)
                    else:
                        lista[k] = E._mezclar(lista[k], d)
                elif isinstance(d, dict) and (not lista or isinstance(lista[0], dict)):
                    lista.append(E.a_python(d))
            if len(lista) > len(nuevos):
                del lista[len(nuevos):]
            aplicadas[clave] = datos
        self._presentacion(glob.get("presentacion"))
        self._tutorial(glob.get("tut_estado"))
        self._identidades()
        self._npcs_interpolados(interpolado)
        self._animar_npcs()
        orden = (secciones.get("pubs") or {}).get("orden")
        red = getattr(g, "nexus", None)
        if red is not None and orden is not None:
            red.publicaciones = [self._pub(i) for i in orden]

    def _logros(self, gestor, obtenidos):
        """Los logros que ya salieron, en el árbol del espejo (los resultados
        cuentan con él: antes el cliente decía 0 logros)."""
        if not isinstance(obtenidos, dict) or getattr(gestor, "arbol", None) is None:
            return
        for nodo in gestor.arbol.preorden():
            datos = obtenidos.get(nodo.clave)
            nodo.obtenido = datos is not None
            nodo.quien, nodo.por_camino = (datos[0], bool(datos[1])) if datos else (None, False)

    def _identidades(self):
        """Lo que en el servidor es el MISMO objeto que está en una lista y el
        dibujo lo compara con `is`. Por la red llega una copia, y la copia
        nunca es "esa": la caja de fusibles buena no parpadeaba en rojo ni
        mostraba su barra (eventos.dibujar_cajas: `caja is eventos.caja`).
        Aquí se cambia la copia por el de la lista del espejo (mismo rect)."""
        g = self.g
        ev = getattr(g, "eventos", None)
        if ev is not None:
            for atributo, lista in (("caja", getattr(ev, "cajas", ())),
                                    ("compuerta", getattr(g, "compuertas", ()))):
                actual = getattr(ev, atributo, None)
                if isinstance(actual, dict) and not any(actual is c for c in lista):
                    igual = next((c for c in lista if c.get("rect") == actual.get("rect")), None)
                    if igual is not None:
                        setattr(ev, atributo, igual)
        # Las puertas con código que se abrieron: en el servidor su pared se
        # quita de mundo.paredes (mision.abrir_puerta) y el espejo nunca la
        # quitaba: la vista del cliente seguía tapada por una puerta abierta
        # (el campo de visión, vision.obstaculos, usa mundo.paredes).
        mision = getattr(g, "mision", None)
        paredes = getattr(getattr(g, "mundo", None), "paredes", None)
        if mision is not None and paredes is not None:
            for puerta in getattr(mision, "puertas", ()):
                if puerta.get("abierta") and puerta.get("rect") in paredes:
                    paredes[:] = [p for p in paredes if p != puerta["rect"]]

    def _npcs(self, gestor, lista):
        """Los prisioneros que caminan, por su cuenta (`nodo`): así uno que se
        fue (rescatado) no se queda parado en el espejo y uno nuevo aparece.
        Antes se copiaban por posición en la lista y, si cambiaba el largo, se
        dejaba la lista vieja."""
        from entidades.npcs import NPC
        actuales = {getattr(n, "nodo", None): n for n in gestor.npcs}
        nuevos = []
        for datos in lista:
            if not isinstance(datos, dict):
                continue
            npc = actuales.get(datos.get("nodo"))
            if npc is None:
                npc = NPC.__new__(NPC)
                npc.__dict__.update({"hitbox": pygame.Rect(0, 0, 24, 20), "ruta": [], "burbuja": None,
                                     "burbuja_ms": 0, "siguiendo": None, "juego": self.g,
                                     "apariencia": None, "nodo": None, "usuario": ""})
            E.aplicar(npc, datos)
            if getattr(npc, "apariencia", None) is not None:
                nuevos.append(npc)
        gestor.npcs = nuevos

    def _npcs_interpolados(self, interpolado):
        """Los prisioneros donde los pone la interpolación (como los aliens),
        en cada cuadro: su sección solo trae dónde estaban en la última
        instantánea."""
        gestor = getattr(self.g, "npcs", None)
        for npc in getattr(gestor, "npcs", None) or ():
            q = interpolado.get(f"n{getattr(npc, 'nodo', None)}")
            if q is not None and hasattr(npc, "hitbox"):
                npc.hitbox.center = (round(q[0]), round(q[1]))

    def _animar_npcs(self):
        """Los prisioneros caminan con la animación del cliente: en el modo
        local la avanza su `actualizar`, que el espejo no corre. Se mira cuánto
        se movió cada uno (las posiciones llegan 30 veces por segundo, así que
        "se está moviendo" dura un poco después de cada cambio)."""
        import time
        ahora = time.perf_counter()
        quienes = list(getattr(getattr(self.g, "npcs", None), "npcs", None) or [])
        cf = getattr(self.g, "cambiaformas", None)
        if cf is not None and getattr(cf, "apariencia", None) is not None and hasattr(cf, "hitbox"):
            quienes.append(cf)
        vistos = set()
        for quien in quienes:
            ap = getattr(quien, "apariencia", None)
            if ap is None or not hasattr(ap, "animar"):
                continue
            clave = id(quien)
            vistos.add(clave)
            centro = quien.hitbox.center
            antes = self._pasos_npc.get(clave)
            if antes is None or antes[0] != centro:
                d = (centro[0] - antes[0][0], centro[1] - antes[0][1]) if antes else (0, 0)
                antes = (centro, ahora, d if d != (0, 0) else (antes[2] if antes else (0, 0)))
                self._pasos_npc[clave] = antes
            camina = ahora - antes[1] < 0.15 and antes[2] != (0, 0)
            try:
                ap.animar(*(antes[2] if camina else (0, 0)), self._dt_ms)
            except Exception:
                pass
        for clave in [c for c in self._pasos_npc if c not in vistos]:
            del self._pasos_npc[clave]

    def _tutorial(self, pasos):
        """En qué paso va cada jugador (en el Tutorial va por id() del jugador,
        que en el espejo es otro)."""
        tut = getattr(self.g, "tutorial", None)
        if tut is None:
            return
        if not pasos:
            tut.activo = False
            return
        tut.estado = {id(j): dict(e) for j, e in zip(self.g.jugadores, pasos) if isinstance(e, dict)}
        tut.jugadores = list(self.g.jugadores)

    def _resolver(self, marca, identidad):
        if marca == "P":
            return self._pub(identidad)
        if marca == "J":
            jugadores = self.g.jugadores
            return jugadores[identidad] if isinstance(identidad, int) and 0 <= identidad < len(jugadores) else None
        if marca == "A":
            return self.aliens.get(identidad)
        if marca == "L":
            logros = getattr(self.g, "logros", None)
            arbol = getattr(logros, "arbol", None)
            return arbol.buscar(identidad) if arbol is not None else None
        return None

    def _pub(self, identidad):
        """La publicación `identidad` del espejo (se crea vacía si no estaba)."""
        pub = self.pubs.get(identidad)
        if pub is None:
            from redes.nexus import Publicacion
            pub = Publicacion.__new__(Publicacion)
            pub.__dict__.update({"autor": None, "tipo": "normal", "texto": "", "falsa": False,
                                 "rumor": None, "lugar": None, "desmentida": False, "foto": None,
                                 "con_ubicacion": False, "desmiente": None, "suplantada": False,
                                 "reportada": False, "via": {}, "alcanzados": set(), "edad_ms": 0})
            pub.id = identidad
            self.pubs[identidad] = pub
        return pub

    def _publicaciones(self, datos):
        if not datos:
            return
        for clave, d in datos.items():
            if clave == "orden" or not isinstance(d, dict):
                continue
            identidad = int(clave) if clave.lstrip("-").isdigit() else clave
            E.aplicar(self._pub(identidad), d)

    def _presentacion(self, datos):
        """La ventana que presenta un alien. En el servidor `actual` tiene al
        jugador y al alien (objetos), que no viajan: el dict llegaba sin ellos
        y el dibujo se caía con KeyError 'jugador'. Aquí se arma con los del
        espejo."""
        p = getattr(self.g, "presentacion", None)
        if p is None:
            return
        if not datos:
            p.actual = None
            return
        indice = datos.get("jugador", 0)
        jugador = self.g.jugadores[indice] if 0 <= indice < len(self.g.jugadores) else None
        alien = self.aliens.get(datos.get("alien"))
        if alien is None:       # (no está entre los vistos: uno del mismo tipo, o uno de mentira)
            alien = next((a for a in self.aliens.values() if a.tipo == datos.get("tipo")), None)
        if jugador is None or alien is None or not datos.get("tipo"):
            p.actual = None
            return
        if datos.get("x") is not None and alien not in self.g.aliens:
            alien.hitbox.center = (round(datos["x"]), round(datos["y"]))
        p.actual = {"tipo": datos["tipo"], "alien": alien, "jugador": jugador, "ms": datos.get("ms", 0)}

    def _jugador(self, j, datos, pos, completo=True):
        """Copia el jugador. Sin `completo` (su sección no cambió desde la
        última vez) solo la posición, la animación, la linterna y la aguja."""
        p = j.personaje
        x, y = (pos[0], pos[1]) if pos else (datos["x"], datos["y"])
        p.x, p.y = x, y
        p.sync_hitbox_from_sprite()
        p.direccion = datos["dir"]
        p.moviendose = datos["mov"]
        # La animación es del cliente (no vale la pena mandar el cuadro).
        nuevo = "walking" if datos["mov"] else (
            "breathing" if p.animaciones.get("breathing", {}).get(p.direccion) else "idle")
        if nuevo != p.estado:
            p.estado, p.frame_actual, p.contador_animacion = nuevo, 0, 0
        # En el modo local la animación avanza en Personaje.actualizar, que el
        # espejo nunca llama: sin esto caminaban "deslizándose" en el cuadro 0.
        # (Personaje cuenta cuadros de 60 por segundo: se avanza según el
        # tiempo real, para que vaya igual aunque el cliente dibuje a 30.)
        self._avance_j = getattr(self, "_avance_j", {})
        pendiente = self._avance_j.get(id(p), 0.0) + self._dt_ms * 60 / 1000
        while pendiente >= 1:
            p._avanzar_animacion()
            pendiente -= 1
        self._avance_j[id(p)] = pendiente
        if not completo:
            j.linterna.angulo = pos[2] if pos else datos.get("lin", j.linterna.angulo)
            self._aguja(j)
            self._tarea(j, nuevo=False)
            return
        atributos = {k[2:]: v for k, v in datos.items() if k.startswith("a.")}
        panel = atributos.pop("panel", None)
        objetos = atributos.pop("objetos", None)
        # El escondite va por índice (abajo): mezclar su dict aquí cambiaba EN
        # SU LUGAR el escondite en el que estaba antes (otro).
        atributos.pop("escondite", None)
        E.aplicar(j, atributos)
        # El panel: si cambió de tipo se arma de nuevo; si no, se mezcla (así
        # no se pierden los objetos que el espejo le había puesto).
        if panel is None:
            j.panel = None
        elif not isinstance(j.panel, dict) or j.panel.get("tipo") != panel.get("tipo"):
            j.panel = E.a_python(panel)
        else:
            j.panel = E._mezclar(j.panel, panel)
            for clave in [k for k in j.panel if k not in panel and not hasattr(j.panel[k], "__dict__")]:
                del j.panel[clave]
        if objetos is not None:
            j.objetos.clear()
            j.objetos.update(objetos)
        j.preso = _Preso(fuga_ms=datos.get("fuga")) if datos.get("preso") else None
        g = self.g
        j.escondite = _de(g.escondites, datos.get("escondite"))
        # Lo que tiene cerca, como el objeto del espejo (el dibujo pregunta
        # `jugador.zona_cerca is zona`): ver JUGADOR_NO en servidor.py.
        j.zona_cerca = _de(getattr(g, "zonas", ()), datos.get("zc"))
        j.escondite_cerca = _de(g.escondites, datos.get("ecc"))
        estacion = datos.get("stc")
        j.estacion_cerca = (_de(g.terminales if estacion[0] == "t" else g.paneles, estacion[1])
                            if isinstance(estacion, list) and len(estacion) == 2 else None)
        j.linterna.angulo = pos[2] if pos else datos.get("lin", j.linterna.angulo)
        self._aguja(j)
        self._tarea(j, nuevo=True)
        arbol = getattr(j, "arbol", None)
        if arbol is not None:
            E.aplicar(arbol, {k[2:]: v for k, v in datos.items() if k.startswith("h.")})
            self._habilidades(arbol, datos.get("hab"))

    @staticmethod
    def _habilidades(arbol, hab):
        """Lo que escogió en su árbol (ver "hab" en servidor._jugador)."""
        if not isinstance(hab, list) or len(hab) != 2 or not hasattr(arbol, "por_niveles"):
            return
        camino, descartadas = set(hab[0] or ()), set(hab[1] or ())
        actual = None
        for nodo, _ in arbol.por_niveles():
            nodo.desbloqueada = nodo.clave in camino
            nodo.descartada = nodo.clave in descartadas
            if hab[0] and nodo.clave == hab[0][-1]:
                actual = nodo
        if actual is not None:
            arbol.actual = actual

    def _aguja(self, j):
        """La aguja del minijuego del escondite: llega 30 veces por segundo y
        va rápido, así que entre instantánea e instantánea el cliente la sigue
        moviendo él (rebotando igual que en minijuego_latidos.py). Lo que ve el
        jugador es lo que se manda al servidor cuando presiona (cliente.py)."""
        import time
        mj = getattr(j, "minijuego", None)
        if mj is None or not hasattr(mj, "aguja") or getattr(mj, "resultado", None) is not None:
            self._agujas.pop(id(j), None)
            return
        servidor = (mj.aguja, mj.sentido)
        visto = self._agujas.get(id(j))
        ahora = time.perf_counter()
        if visto is None or visto[0] != servidor:
            visto = self._agujas[id(j)] = (servidor, ahora)
        aguja = mj.aguja + mj.sentido * getattr(mj, "velocidad", 0.0) * min(0.12, ahora - visto[1])
        if aguja >= 1:
            mj.aguja, mj.sentido = 2 - aguja, -1
        elif aguja <= 0:
            mj.aguja, mj.sentido = -aguja, 1
        else:
            mj.aguja = aguja

    def _tarea(self, j, nuevo):
        """El minijuego de una tarea (juego/tareas.py; lo juega el servidor):
        llega 30 veces por segundo y se dibuja a 60, así que entre instantánea
        e instantánea el cliente lo sigue moviendo él (`Minijuego.animar`: el
        reloj de las animaciones, el saco que se mece, el pin que sube). Con
        cada instantánea vuelve a lo del servidor. Lo que ve el jugador al
        presionar se manda con la tecla (cliente.Sesion._extra)."""
        from juego import tareas
        mini = tareas.de(j)
        if mini is None or not hasattr(mini, "animar"):
            self._tareas.pop(id(j), None)
            return
        visto = self._tareas.get(id(j))
        if nuevo or visto is None or visto[0] is not mini:
            self._tareas[id(j)] = (mini, 0.0)
            return
        acumulado = visto[1] + self._dt_ms
        self._tareas[id(j)] = (mini, acumulado)
        if acumulado <= 150:          # (sin instantáneas un rato: se queda quieto)
            mini.animar(self._dt_ms)

    def _aliens(self, datos, interpolado):
        vistos = []
        for i in range(datos.get("n", 0)):
            pos, resto = datos.get(str(i)), datos.get(f"{i}d")
            if pos is None or resto is None:
                continue
            nombre, _alcance, _medio, otros = resto
            alien = self.aliens.get(nombre)
            if alien is None:
                continue
            x, y, ang = interpolado.get(f"a{i}", pos)
            antes = alien.hitbox.center
            alien.hitbox.center = (round(x), round(y))
            # Su animación va con su reloj propio (tiempo_ms) y `moviendose`,
            # que en el modo local pone alien.actualizar: aquí los pone el espejo.
            alien.tiempo_ms = getattr(alien, "tiempo_ms", 0) + self._dt_ms
            alien.moviendose = alien.hitbox.center != antes
            alien.angulo = ang
            for clave, v in otros.items():
                if clave != "tipo":
                    try:
                        setattr(alien, clave, v)
                    except AttributeError:
                        pass
            vistos.append(alien)
        self.g.aliens = vistos

    def sonar(self, sonidos):
        for nombre, volumen in sonidos or ():
            try:
                self.g.ambiente.sonar(nombre, volumen)
            except Exception:
                pass

    # -- Dibujar ---------------------------------------------------------------------

    def dibujar(self, pantalla, locales):
        """Las vistas de los jugadores `locales` (números de jugador) con el
        dibujo del modo local."""
        g = self.g
        # El cuadro del dibujo: en el modo local lo sube _actualizar_partida,
        # que el espejo nunca corre. Sin esto, en red el contador se quedaba
        # quieto y (1) las vistas que se turnan para recalcular su campo de
        # visión (screens/partida.py) no se turnaban: la del J2 solo lo
        # recalculaba cada 24 px que caminaba (la sombra iba a saltos), y (2)
        # el tope de tiempo por cuadro de los caminos de las flechas no se
        # reiniciaba nunca (navegacion._gastado).
        from juego import navegacion
        navegacion.siguiente_cuadro()
        dueños = [g.jugadores[i] for i in locales if i < len(g.jugadores)]
        extras = g._extras_dibujo()
        pantalla_original = g.screen
        g.screen = pantalla
        try:
            g._dibujar_partida_en(pantalla, dueños, extras)
            if g.presentacion is None or not g.presentacion.abierta:
                from screens.logros import render_aviso_logro
                try:
                    render_aviso_logro(pantalla, g.logros)
                except (AttributeError, TypeError, KeyError):
                    pass        # (el aviso de logro es un adorno: que no tumbe el dibujo)
        finally:
            g.screen = pantalla_original

    def dibujar_resultados(self, pantalla):
        """La pantalla de resultados del modo local, con los datos del espejo:
        el resumen con sus botones, el árbol de logros ("Ver logros") o el
        álbum de fotos (screens/album.py). Lo que
        está escogido lo lleva el Game del espejo, como en local
        (`resultados_vista`, `resultados_sel`, `resultados_nodo`; las teclas,
        cliente.Sesion._tecla_resultado)."""
        from screens.resultados import render_resultados
        from screens.logros import render_arbol_logros
        g = self.g
        if not hasattr(g, "resultados_vista"):
            g._reiniciar_resultados()
        if g.resultados_vista == "logros" and g.logros is not None:
            g.resultados_rects_logros = render_arbol_logros(pantalla, g.logros.arbol, g.resultados_nodo)
            return
        if g.resultados_vista == "album":
            from screens.album import render_album
            g.album_rects = render_album(pantalla, g.nexus, getattr(g, "album_sel", 0))
            return
        g.resultados_rects = render_resultados(
            pantalla, g.jugadores, g.font, g.small_font, g.mision, g.equipo,
            g.infiltrado, g.logros, g.resultados_sel, g.nexus, g.cambiaformas, g.npcs,
            g.dificultad, g.tiempo_jugado_ms)


def _de(lista, indice):
    """El elemento `indice` de `lista`, o None."""
    if isinstance(indice, int) and 0 <= indice < len(lista or ()):
        return lista[indice]
    return None


def captura_local(juego, locales):
    """Lo que dibuja el modo local para `locales`, sin pasar por la red (para
    comparar en pruebas/prueba_red_capturas.py)."""
    pantalla = pygame.Surface(juego.screen.get_size())
    dueños = [juego.jugadores[i] for i in locales]
    juego._dibujar_partida_en(pantalla, dueños, juego._extras_dibujo())
    return pantalla
