"""NEXUS: la red social de la nave, en el celular de cada jugador.

Por debajo es un grafo (Estructuras/grafo.py): cada cuenta es un nodo y lo
que publica una cuenta les llega a sus seguidores. Hay tres tipos de cuenta:

- **prisioneros** (data/nexus.py: CUENTAS): son los que cuentan para las
  barras. Cada uno está gris (no decide), verde (confía en los jugadores) o
  rojo (le cree a los aliens).
- **bots** del Cambiaformas: parecen prisioneros, pero publican rumores falsos.
- **los jugadores**: reciben en su feed lo que les llega por el grafo.

Las barras de confianza no son números sueltos: son el % de prisioneros
verdes y rojos.

Cómo se juega:
- Un bot publica un rumor (que habla de un lugar de la nave) y se propaga por
  BFS, un nivel por tick. A cada gris que le llega se lo cree o no (al azar,
  PROB_CREER_RUMOR); el que se lo cree se pone rojo y lo reenvía. Los verdes
  no se lo creen: la confianza hace de cortafuegos.
- El jugador lo ve en el feed y puede **investigar** (una flecha lo lleva al
  lugar), **compartir**, **reportar** o **rastrear de dónde vino** (camino
  más corto desde el bot hasta él).
- En el lugar saca una foto sola. Con la foto **desmiente** desde el celular:
  el desmentido se propaga en verde (lo reenvía quien queda convencido).
  Puede publicarla tal cual (se ve dónde está: convence a más gente, pero el
  alien más cercano va por él) o recortarla.
- Compartir un rumor sin verificar lo riega más y tus seguidores dejan de
  confiar en ti. Reportar un bot lo borra del grafo; reportar a un prisionero
  que solo se creyó el rumor no ayuda.
- **Un rumor que nadie desmiente se vuelve viral** (VIRAL_S): les llega a
  todos los grises y la gente de la nave actúa como si fuera verdad (el
  "viral" de cada rumor: los prisioneros dejan de seguirte, ocupan casilleros,
  desconectan una terminal NEXUS, o el que cae preso tarda más en salir).
  Desmentirlo lo deshace. Y **llegar tarde convence menos**: desde
  TARDE_DESDE de la barra, el desmentido convence cada vez a menos gente
  ("Llegaste tarde: N personas ya se lo habían creído").
- **Noticias verdaderas** (data/nexus.py: NOTICIAS, nov 20): las publica un
  prisionero de verdad y lo que cuentan es cierto ("le pusieron candado a un
  casillero"). En Misiones se ven igual que los rumores: hay que ir a ver.
  Allá se ARREGLA con un minijuego (juego/tareas.py; en red, solo con llegar)
  y con la foto se **confirma** (se propaga en verde, como un desmentido).
  Compartirla sin verificar no castiga ni da nada (era cierta, pero no lo
  sabías); reportar a quien la publicó es reportar a un prisionero de verdad.
- La cuenta para volverse viral empieza cuando le llega a algún jugador (antes
  corría desde que se publicaba y había rumores virales que nadie había visto).
- Compartir la charla de la pestaña Red no da puntos ni cambia la confianza.
- Con UMBRAL_PLANOS de verdes se desbloquean los planos de la cápsula (sin
  ellos no se puede reparar, mision.py). Si el rojo le va ganando al verde,
  los aliens se vuelven más rápidos y ven más. (Antes, con mucho rojo los
  aliens tomaban NEXUS y se perdía; se quitó: perder es solo por vidas o por
  quedar todos encerrados.)

El celular se dibuja en screens/celular.py; juego/app.py lo abre con la tecla de
celular de cada jugador y le pasa las teclas.
"""

from juego import dificultad
import math
import random

from Estructuras.grafo import Grafo
from misiones.logros import logro
from data.nexus import (
    CUENTAS, BOTS, RUMORES, NORMALES,
    SEGUIDORES_PRISIONERO, SEGUIDORES_BOT, SEGUIDORES_JUGADOR, SIGUE_CADA_JUGADOR,
    BOTS_AL_EMPEZAR, TICK_PROPAGACION_MS, PRIMER_RUMOR_S, RUMOR_CADA_S, NORMAL_CADA_S,
    NUEVO_BOT_CADA_S, MAX_POR_VERIFICAR, NIVELES_DESMENTIDO, NOMBRE_LUGAR, PROB_CONVENCER_UBICACION,
    NIVELES_COMPARTIR_CIERTO, UMBRAL_PLANOS, DIFERENCIA_POTENCIA_MAX,
    RADIO_FOTO, PUNTOS_DESMENTIR, PROB_RECAPACITAR, OLVIDO_CADA_S, PROB_OLVIDAR,
    PUNTOS_REPORTAR_BOT, PUNTOS_PLANOS, PROB_CREER_RUMOR, PROB_CONVENCER,
    PUNTOS_SUPLANTACION, VIRAL_S, PROB_CREER_VIRAL, VIRAL_GENERICO, ESCONDITES_VIRAL, PROB_DESCONFIAR,
    TARDE_DESDE, CONVENCE_TARDE, SEGUIDORES_PARA_CONSEJO, BOT_GANA_SEGUIDOR_S, BOT_MAX_SEGUIDORES, AVISOS_SEGUIDORES,
    NOTICIAS, PROB_NOTICIA, PUNTOS_ARREGLAR, PUNTOS_CONFIRMAR,
)

GRIS, VERDE, ROJO = "gris", "verde", "rojo"
COLOR_BIEN = (120, 230, 150)
COLOR_MAL = (245, 130, 120)
COLOR_NEXUS = (120, 190, 255)
MAX_FEED = 25


class Publicacion:
    _siguiente = 0

    def __init__(self, autor, tipo, texto, falsa=False, rumor=None):
        Publicacion._siguiente += 1
        self.id = Publicacion._siguiente
        self.autor = autor          # nodo que la publicó
        self.tipo = tipo            # "rumor", "noticia" (verdadera), "normal", "desmentido",
                                    # "confirmacion", "compartido", "trampa" (suplantación)
                                    # o "testimonio" (rescatado)
        self.texto = texto
        self.falsa = falsa
        self.rumor = rumor          # dict de RUMORES o de NOTICIAS (rumores y noticias)
        self.lugar = None           # (x, y) donde se verifica (rumores y noticias)
        self.desmentida = False     # (una noticia: ya la confirmaron con foto)
        self.arreglada = False      # (una noticia: ya lo arreglaron en el lugar)
        self.avisados = set()       # (una noticia: a quién ya se le dijo que es verdad)
        self.foto = None            # texto de la foto (desmentidos)
        self.con_ubicacion = False
        self.desmiente = None       # la Publicacion que desmiente
        self.suplantada = False     # la escribió el Cambiaformas haciéndose pasar por `autor`
        self.reportada = False
        self.viral_ms = 0           # cuánto lleva sin desmentir (rumores)
        self.viral = False          # se volvió viral: la nave actúa como si fuera verdad
        self.creyentes = set()      # prisioneros que se lo creyeron (se pusieron rojos por él)
        self.efecto = {}            # lo que cambió en la nave al volverse viral (para deshacerlo)
        self.via = {}               # nodo -> de quién le llegó
        self.alcanzados = set()     # nodos a los que les llegó
        self.edad_ms = 0


class Propagacion:
    """Una publicación avanzando por el grafo, un nivel (BFS) por tick."""

    def __init__(self, pub, origen, color, max_niveles=None, prob=1.0):
        self.pub = pub
        self.prob = prob            # a cuántos convence (las verdes)
        self.color = color          # ROJO pinta a los grises; VERDE a todos
        self.frontera = [origen]
        self.visitados = {origen}
        self.niveles = 0
        self.max_niveles = max_niveles
        self.reloj_ms = 0

    @property
    def terminada(self):
        return not self.frontera or (self.max_niveles is not None
                                     and self.niveles >= self.max_niveles)


class RedNexus:
    def __init__(self, juego, rng=None):
        self.juego = juego
        self.rng = rng or random.Random()
        self.grafo = Grafo()
        self.publicaciones = []
        self.propagaciones = []
        self.planos = False
        self.evidencias = {}        # jugador -> [rumores (Publicacion) con foto]
        self.investigando = {}      # jugador -> rumor (Publicacion) que está investigando
        self.vistas = {}            # jugador -> ids de publicaciones ya vistas
        self.stats = {}             # jugador -> contadores para los resultados
        self.tiempo_celular_ms = {}
        self.reloj_rumor_ms = PRIMER_RUMOR_S * 1000
        self.umbral_planos = UMBRAL_PLANOS     # la dificultad lo cambia (App.iniciar_partida)
        self.convencer = None       # cuánto convence la verdad (None: lo de la dificultad, "convencer")
        self.tick_verde_ms = TICK_PROPAGACION_MS    # cada cuánto avanza un nivel la verdad (la feria, más rápido)
        self.reloj_normal_ms = self.rng.uniform(*NORMAL_CADA_S) * 1000
        self.reloj_bot_ms = NUEVO_BOT_CADA_S * 1000
        self.reloj_olvido_ms = OLVIDO_CADA_S * 1000
        self._bots_usados = 0
        # Para la vista del grafo (screens/grafo_vista.py, Pausa > Opciones).
        self.tiempo_ms = 0
        self.ultimo_rastreo = None   # (camino, tiempo_ms) del último "¿De dónde salió esto?"
        self.borrados = []           # (nodo, usuario, tiempo_ms) de los bots reportados
        self.pestanas = {}           # jugador -> pestaña del celular que dejó abierta
        self.virales = 0             # rumores que se volvieron virales (resultados)
        self.creyeron_tarde = 0      # gente que se lo creyó antes de que llegara el desmentido
        self.empeoradas = 0          # noticias verdaderas que nadie arregló a tiempo (`_empeorar`)
        self.desconfiaron = 0        # verdes que dejaron de confiar por eso
        self.seguidores_ganados = 0  # seguidores que ganaron los bots mientras nadie los reportaba
        self.con_noticias = True     # noticias verdaderas (False: solo rumores)
        self._armar_red()

    # -- La red ---------------------------------------------------------------------

    def nodo_de(self, jugador):
        return f"jugador_{jugador.puesto}"

    def _armar_red(self):
        g = self.grafo
        presos = []
        for i, cuenta in enumerate(CUENTAS):
            nodo = f"preso_{i}"
            g.agregar_nodo(nodo, tipo="preso", color=GRIS, **cuenta)
            presos.append(nodo)
        for nodo in presos:
            for otro in self.rng.sample([p for p in presos if p != nodo],
                                        min(SEGUIDORES_PRISIONERO, len(presos) - 1)):
                g.agregar_arista(nodo, otro)
        for jugador in self.juego.jugadores:
            nodo = self.nodo_de(jugador)
            g.agregar_nodo(nodo, tipo="jugador", color=VERDE, nombre=jugador.rol,
                           usuario="@" + jugador.rol.lower())
            for otro in self.rng.sample(presos, min(SEGUIDORES_JUGADOR, len(presos))):
                g.agregar_arista(nodo, otro)
            for otro in self.rng.sample(presos, min(SIGUE_CADA_JUGADOR, len(presos))):
                g.agregar_arista(otro, nodo)
            self.evidencias[jugador] = []
            self.vistas[jugador] = set()
            self.stats[jugador] = {"desmentidos": 0, "compartidos_falsos": 0,
                                   "compartidos_ciertos": 0, "bots_reportados": 0,
                                   "reportes_injustos": 0, "fotos_ubicacion": 0,
                                   "fotos_recortadas": 0, "rastreos": 0, "suplantaciones": 0,
                                   "confirmados": 0, "compartidos_sin_verificar": 0}
            self.tiempo_celular_ms[jugador] = 0
        for _ in range(min(BOTS_AL_EMPEZAR, len(BOTS))):
            self._nuevo_bot()

    def _nuevo_bot(self):
        if self._bots_usados >= len(BOTS):
            return None
        cuenta = BOTS[self._bots_usados]
        nodo = f"bot_{self._bots_usados}"
        self._bots_usados += 1
        self.grafo.agregar_nodo(nodo, tipo="bot", color=ROJO, **cuenta)
        presos = self._presos()
        for otro in self.rng.sample(presos, min(SEGUIDORES_BOT, len(presos))):
            self.grafo.agregar_arista(nodo, otro)
        datos = self.grafo.datos[nodo]
        datos["seguidores_al_abrir"] = self.grafo.grado_salida(nodo)
        datos["crece_ms"] = self.cada_cuanto_crece()
        # Para parecer real, el bot también sigue a unos prisioneros.
        for otro in self.rng.sample(presos, min(2, len(presos))):
            self.grafo.agregar_arista(otro, nodo)
        return nodo

    def _presos(self):
        return [n for n in self.grafo.nodos() if self.grafo.datos[n]["tipo"] == "preso"]

    def bots(self):
        return [n for n in self.grafo.nodos() if self.grafo.datos[n]["tipo"] == "bot"]

    def color(self, nodo):
        return self.grafo.datos[nodo]["color"]

    def usuario(self, nodo):
        datos = self.grafo.datos.get(nodo)
        return datos["usuario"] if datos else "@cuenta_borrada"

    def es_bot(self, nodo):
        datos = self.grafo.datos.get(nodo)
        return datos is not None and datos["tipo"] == "bot"

    # -- Barras --------------------------------------------------------------------------

    def barras(self):
        """(fracción de prisioneros verdes, fracción de rojos)."""
        presos = self._presos()
        if not presos:
            return 0.0, 0.0
        verdes = sum(self.color(n) == VERDE for n in presos)
        rojos = sum(self.color(n) == ROJO for n in presos)
        return verdes / len(presos), rojos / len(presos)

    def potencia_aliens(self):
        """0 a 1: qué tanto le va ganando el rojo al verde."""
        verde, rojo = self.barras()
        return max(0.0, min(1.0, (rojo - verde) / DIFERENCIA_POTENCIA_MAX))

    # -- Frame -----------------------------------------------------------------------------

    def actualizar(self, dt):
        juego = self.juego
        self.tiempo_ms += dt
        en_tutorial = getattr(juego, "en_tutorial", False)
        for jugador in juego.jugadores:
            panel = jugador.panel or {}
            if panel.get("tipo") == "celular":
                self.tiempo_celular_ms[jugador] = self.tiempo_celular_ms.get(jugador, 0) + dt

        if not en_tutorial:
            self.reloj_rumor_ms -= dt
            if self.reloj_rumor_ms <= 0:
                self.reloj_rumor_ms = (self.rng.uniform(*RUMOR_CADA_S) * 1000
                                       * dificultad.valor(self.juego, "rumor_cada", 1.0))
                # A veces es verdad: una noticia de un prisionero (si no se
                # puede, va un rumor como siempre).
                if not (self.con_noticias and self.rng.random() < PROB_NOTICIA and self.lanzar_noticia()):
                    self.lanzar_rumor()
            self.reloj_normal_ms -= dt
            if self.reloj_normal_ms <= 0:
                self.reloj_normal_ms = self.rng.uniform(*NORMAL_CADA_S) * 1000
                self.publicar_normal()
            if len(self.bots()) < BOTS_AL_EMPEZAR:
                self.reloj_bot_ms -= dt
                if self.reloj_bot_ms <= 0:
                    self.reloj_bot_ms = NUEVO_BOT_CADA_S * 1000
                    self._nuevo_bot()
            # Con el tiempo, algunos de los que se creyeron algo empiezan a dudar.
            self.reloj_olvido_ms -= dt
            if self.reloj_olvido_ms <= 0:
                self.reloj_olvido_ms = OLVIDO_CADA_S * 1000
                for n in self._presos():
                    if self.color(n) == ROJO and self.rng.random() < PROB_OLVIDAR:
                        self.grafo.datos[n]["color"] = GRIS
            for bot in self.bots():
                datos = self.grafo.datos[bot]
                datos["crece_ms"] = datos.get("crece_ms", self.cada_cuanto_crece()) - dt
                if datos["crece_ms"] <= 0:
                    datos["crece_ms"] = self.cada_cuanto_crece()
                    self._ganar_seguidor(bot)

        for pub in self.publicaciones:
            pub.edad_ms += dt
        for pub in self.rumores_activos() + self.noticias_activas():
            # La cuenta empieza cuando le llega a algún jugador: antes corría
            # desde que se publicaba y había rumores virales que nadie había visto.
            if not pub.viral and self._le_llego_a_alguien(pub):
                pub.viral_ms += dt
                if pub.viral_ms >= self.limite_viral():
                    self._volverse_viral(pub)
        for prop in list(self.propagaciones):
            prop.reloj_ms += dt
            tick = self.tick_verde_ms if prop.color == VERDE else TICK_PROPAGACION_MS
            while prop.reloj_ms >= tick and not prop.terminada:
                prop.reloj_ms -= tick
                self._avanzar(prop)
            if prop.terminada:
                self.propagaciones.remove(prop)

        self._fotos()
        self._revisar_umbrales()
        potencia = self.potencia_aliens()
        for alien in getattr(juego, "aliens", ()):
            alien.potencia_nexus = potencia

    def factor_convencer(self):
        """Qué tanto convence la verdad: multiplica la prob. de cada
        prisionero al que le llega (data/dificultad.AJUSTES "convencer"; en
        la feria, data/feria.AJUSTES_FERIA). Sin dificultad (pruebas), 1."""
        if self.convencer is not None:
            return self.convencer
        return dificultad.valor(self.juego, "convencer", 1.0)

    def _avanzar(self, prop):
        """Un tick: la publicación llega al siguiente nivel del BFS."""
        g = self.grafo
        if prop.color == ROJO:
            # Solo reenvía el rumor quien se lo cree (el bot que lo empezó y los
            # rojos). Los verdes y los grises que no se lo creyeron lo dejan ahí.
            def puede_pasar(n):
                return n in g and self.color(n) == ROJO
        elif prop.color == VERDE:
            # Igual con la verdad: la reenvía quien quedó convencido (verde).
            def puede_pasar(n):
                return n in g and self.color(n) == VERDE and g.datos[n]["tipo"] != "bot"
        else:
            # Lo que no cambia opiniones (charla, la trampa del Cambiaformas)
            # lo reenvía cualquier prisionero.
            def puede_pasar(n):
                return n in g and g.datos[n]["tipo"] == "preso"
        frontera = [n for n in prop.frontera if n in g]
        nivel = g.expandir(frontera, prop.visitados, puede_pasar)
        prop.niveles += 1
        prop.frontera = [n for n, _ in nivel]
        for nodo, de_quien in nivel:
            if (prop.pub.tipo in ("rumor", "trampa", "noticia") and g.datos[nodo]["tipo"] == "jugador"
                    and self._lleno(nodo)):
                continue        # ya tiene MAX_POR_VERIFICAR: a ese jugador no le llega
            prop.pub.alcanzados.add(nodo)
            prop.pub.via.setdefault(nodo, de_quien)
            tipo = g.datos[nodo]["tipo"]
            if tipo == "preso":
                # No todos se creen lo que les llega: cada uno decide (al azar).
                if (prop.color == ROJO and self.color(nodo) == GRIS
                        and self.rng.random() < dificultad.valor(self.juego, "prob_creer", PROB_CREER_RUMOR)):
                    g.datos[nodo]["color"] = ROJO
                    if prop.pub.tipo == "rumor":
                        prop.pub.creyentes.add(nodo)
                elif prop.color == VERDE and self.rng.random() < prop.prob * self.factor_convencer():
                    g.datos[nodo]["color"] = VERDE
            elif tipo == "jugador":
                self._llego_a_jugador(nodo, prop.pub)

    def _le_llego_a_alguien(self, pub):
        return any(self.nodo_de(j) in pub.alcanzados or self.investigando.get(j) is pub
                   for j in self.juego.jugadores)

    def _lleno(self, nodo):
        jugador = self._jugador_de(nodo)
        return jugador is not None and len(self.por_verificar_de(jugador)) >= MAX_POR_VERIFICAR

    def _llego_a_jugador(self, nodo, pub):
        jugador = self._jugador_de(nodo)
        if jugador is None or pub.tipo == "normal":
            return
        tecla = jugador.nombre_tecla("celular")
        if pub.tipo in ("rumor", "noticia"):
            # (lo mismo para los dos: no se sabe cuál es verdad hasta ir a ver)
            lugar = NOMBRE_LUGAR.get(pub.rumor.get("lugar"), "la nave")
            jugador.avisar(f"Me llegó algo a NEXUS [{tecla}]: dicen algo de {lugar}", COLOR_NEXUS)
            self._sonar("senal", 0.25)
        elif pub.tipo == "trampa":
            lugar = getattr(pub, "nombre_lugar", None) or "la nave"
            jugador.avisar(f"Me llegó a NEXUS [{tecla}]: {self.usuario(pub.autor)} pide ayuda en {lugar}",
                           COLOR_NEXUS)
            self._sonar("senal", 0.25)
        elif pub.tipo == "desmentido":
            jugador.avisar(f"Veo en NEXUS que {self.usuario(pub.autor)} desmintió un rumor", COLOR_BIEN)
        elif pub.tipo == "confirmacion":
            jugador.avisar(f"Veo en NEXUS que {self.usuario(pub.autor)} confirmó algo y lo arregló", COLOR_BIEN)
        elif pub.tipo == "testimonio":
            jugador.avisar(f"Veo en NEXUS que rescataron a {self.usuario(pub.autor)}", COLOR_BIEN)

    def _sonar(self, nombre, volumen):
        if hasattr(self.juego, "sonar"):
            self.juego.sonar(nombre, volumen)

    def _decir(self, evento, rol=None):
        if hasattr(self.juego, "decir"):
            self.juego.decir(evento, rol)

    # -- Publicaciones de los demás -------------------------------------------------------

    def _lugares(self, tipo):
        """Puntos del mundo donde se puede verificar un rumor de ese lugar Y a
        los que algún jugador puede llegar ahora (`_alcanzable`). Antes salían
        rumores de la Prisión o de Gestación con su puerta de código todavía
        cerrada: los puntos azules llevaban hasta la puerta y "al llegar" no
        pasaba nada (Diego: "hay misiones que no se activan al llegar")."""
        return [p for p in self._todos_los_lugares(tipo) if self._alcanzable(p)]

    def _alcanzable(self, punto):
        """¿Algún jugador que sigue en la partida puede caminar hasta quedar a
        RADIO_FOTO de `punto` con lo que está cerrado ahora (puertas con código
        y puertas para dos)? El punto suele estar dentro de algo sólido (las
        patas de una consola, un casillero, una caja en la pared): se mira
        desde dónde se puede estar parado alrededor (`_de_pie`)."""
        mundo = getattr(self.juego, "mundo", None)
        if mundo is None or not hasattr(mundo, "paredes_base"):
            return True               # (las pruebas con un mundo falso)
        from juego import navegacion
        nav = navegacion.de_mundo(mundo, 34, 20)
        desde = [j.hitbox.center for j in self.juego.jugadores
                 if not getattr(j, "eliminado", False) and not getattr(j, "desconectado", False)
                 and not j.preso]
        if not desde:
            desde = [j.hitbox.center for j in self.juego.jugadores]
        # (Antes un `conectados` por cada punto de pie y cada jugador: ~600-850
        # preguntas, 7-22 ms de un cuadro al lanzar un rumor o la trampa. Ahora
        # la zona de cada uno, con UN estado de las puertas y guardada.)
        estado = nav._estado(sellos=False)
        zonas = {nav.zona_de(d, estado=estado) for d in desde}
        zonas.discard(None)
        return any(nav.zona_de(q, estado=estado) in zonas for q in self._de_pie(punto))

    def _de_pie(self, punto):
        """Dónde puede estar parado un jugador a menos de RADIO_FOTO de `punto`
        (unos pocos puntos; se guardan por punto)."""
        guardados = self.__dict__.setdefault("_puntos_de_pie", {})
        clave = (int(punto[0]), int(punto[1]))
        if clave in guardados:
            return guardados[clave]
        import pygame
        mundo = self.juego.mundo
        ancho, alto = 47, 18                  # (la hitbox de un jugador)
        choca = getattr(self.juego, "_colisiona_jugador", None) or mundo.colisiona
        puntos = []
        for radio in (0, RADIO_FOTO * 0.45, RADIO_FOTO * 0.8):
            for k in range(1 if radio == 0 else 12):
                a = k * math.pi / 6
                q = (int(clave[0] + radio * math.cos(a)), int(clave[1] + radio * math.sin(a)))
                r = pygame.Rect(0, 0, ancho, alto)
                r.center = q
                if not choca(r):
                    puntos.append(q)
        guardados[clave] = puntos
        return puntos

    def _todos_los_lugares(self, tipo):
        """Puntos del mundo donde se puede verificar un rumor de ese lugar."""
        j = self.juego
        mision = getattr(j, "mision", None)
        if tipo == "capsula":
            return [mision.capsula.center] if mision is not None and mision.capsula else []
        if tipo == "consola":
            return [c["rect"].center for c in (mision.consolas if mision else [])]
        if tipo == "celda":
            return [c["punto"] for c in (mision.celdas if mision else [])]
        if tipo == "fusibles":
            eventos = getattr(j, "eventos", None)
            return [c["rect"].center for c in (eventos.cajas if eventos else [])]
        if tipo == "escondite":
            return [e["rect"].center for e in getattr(j, "escondites", [])]
        if tipo == "terminal":
            return [t["rect"].center for t in getattr(j, "terminales", [])]
        if tipo == "panel":
            return [p["rect"].center for p in getattr(j, "paneles", [])]
        if tipo == "puerta_doble":
            return [p["rect"].center for p in getattr(j, "puertas_dobles", [])]
        return []

    def por_verificar(self):
        """Todo lo que hay que ir a verificar en persona: rumores sin desmentir,
        noticias sin confirmar y la trampa del Cambiaformas (de todo el equipo)."""
        trampa = self.trampa_activa()
        return self.rumores_activos() + self.noticias_activas() + ([trampa] if trampa is not None else [])

    def por_verificar_de(self, jugador):
        """Lo que tiene ESE jugador por verificar: lo que le llegó (o al que va).
        Nunca más de MAX_POR_VERIFICAR: lo que le llega estando lleno se pierde."""
        nodo = self.nodo_de(jugador)
        yendo = self.investigando.get(jugador)
        return [p for p in self.por_verificar() if (nodo in p.alcanzados or p is yendo)
                and not (p.tipo == "noticia" and p.arreglada and p not in self.evidencias.get(jugador, []))]

    def _hay_lugar(self):
        """¿Se puede publicar otra cosa por verificar? Si a alguien le cabe, y sin
        pasar de MAX_POR_VERIFICAR por jugador en total (con 1 jugador, 3)."""
        jugadores = [j for j in self.juego.jugadores
                     if j in self.vistas and not getattr(j, "eliminado", False)]
        if not jugadores:
            return False
        if len(self.por_verificar()) >= MAX_POR_VERIFICAR * len(jugadores):
            return False
        return any(len(self.por_verificar_de(j)) < MAX_POR_VERIFICAR for j in jugadores)

    def _jugador_de(self, nodo):
        return next((j for j in self.juego.jugadores if self.nodo_de(j) == nodo), None)

    def rumores_activos(self):
        return [p for p in self.publicaciones if p.tipo == "rumor" and not p.desmentida]

    def noticias_activas(self):
        """Noticias verdaderas que nadie ha confirmado todavía."""
        return [p for p in self.publicaciones if p.tipo == "noticia" and not p.desmentida]

    def _lugares_usados(self):
        return {p.rumor["lugar"] for p in self.rumores_activos() + self.noticias_activas()}

    def lanzar_rumor(self, rumor=None, bot=None):
        """Un bot publica un rumor falso sobre un lugar de la nave."""
        bots = self.bots()
        if not bots or not self._hay_lugar():
            return None
        usados = self._lugares_usados()
        opciones = [r for r in RUMORES if r["lugar"] not in usados and self._lugares(r["lugar"])]
        if rumor is None:
            if not opciones:
                return None
            rumor = self.rng.choice(opciones)
        lugares = self._lugares(rumor["lugar"])
        if not lugares:
            return None
        bot = bot or self.rng.choice(bots)
        pub = Publicacion(bot, "rumor", rumor["texto"], falsa=True, rumor=rumor)
        pub.lugar = self.rng.choice(lugares)
        self.publicaciones.append(pub)
        self.propagaciones.append(Propagacion(pub, bot, ROJO))
        self._decir("rumor")
        return pub

    def lanzar_noticia(self, noticia=None, autor=None):
        """Un prisionero de verdad cuenta algo que es cierto (NOTICIAS). Lo que
        dice pasa de verdad en la nave hasta que alguien lo arregle (el
        "efecto": el casillero con candado)."""
        presos = self._presos()
        if not presos or not self._hay_lugar():
            return None
        usados = self._lugares_usados()
        if noticia is None:
            opciones = [n for n in NOTICIAS if n["lugar"] not in usados and self._lugares(n["lugar"])]
            if not opciones:
                return None
            noticia = self.rng.choice(opciones)
        lugares = self._lugares(noticia["lugar"])
        if noticia.get("efecto") == "candado":
            # Un casillero libre (ni ocupado ni con un prisionero adentro).
            libres = [e for e in getattr(self.juego, "escondites", [])
                      if e.get("ocupante") is None and e.get("npc") is None and not e.get("candado")]
            lugares = [e["rect"].center for e in libres if e["rect"].center in lugares]
        if not lugares:
            return None
        autor = autor or self.rng.choice(presos)
        pub = Publicacion(autor, "noticia", noticia["texto"], falsa=False, rumor=noticia)
        pub.lugar = self.rng.choice(lugares)
        if noticia.get("efecto") == "candado":
            escondite = next(e for e in getattr(self.juego, "escondites", []) if e["rect"].center == pub.lugar)
            escondite["candado"] = True
            pub.efecto["escondite"] = escondite
        self.publicaciones.append(pub)
        self.propagaciones.append(Propagacion(pub, autor, None, max_niveles=6))
        self._decir("rumor")        # (lo mismo que con un rumor: no delata cuál es cierto)
        return pub

    def noticia_para(self, jugador):
        """La noticia que este jugador puede arreglar donde está (le llegó o va
        a verla, y está en el lugar), o None."""
        nodo = self.nodo_de(jugador)
        c = jugador.hitbox.center
        for pub in self.noticias_activas():
            if pub.arreglada or pub.lugar is None:
                continue
            if nodo not in pub.alcanzados and self.investigando.get(jugador) is not pub:
                continue
            if math.dist(c, pub.lugar) <= RADIO_FOTO:
                return pub
        return None

    def noticia_de_escondite(self, escondite):
        return next((p for p in self.noticias_activas()
                     if p.efecto.get("escondite") is escondite and not p.arreglada), None)

    def pista(self, jugador):
        """Lo que dice la pista de "[E] ..." en el lugar de una noticia."""
        if not getattr(self.juego, "minijuegos", False):
            return None
        pub = self.noticia_para(jugador)
        return pub.rumor.get("pista", "Revisar") if pub is not None else None

    def arreglar(self, jugador, pub):
        """Lo arregló en el lugar (ganó el minijuego, o llegó, en red): era
        verdad. Se lleva la foto para confirmarlo en NEXUS."""
        if pub.arreglada:
            return
        pub.arreglada = True
        self._deshacer_empeora(pub)
        escondite = pub.efecto.pop("escondite", None)
        if escondite is not None:
            escondite["candado"] = False
        if pub not in self.evidencias.setdefault(jugador, []):
            self.evidencias[jugador].append(pub)
        for quien in [j for j, p in self.investigando.items() if p is pub]:
            del self.investigando[quien]      # (los demás que iban ya no tienen nada que ver)
        jugador.sumar_puntos(PUNTOS_ARREGLAR)
        jugador.avisar(f"¡Era verdad, y ya lo arreglé! +{PUNTOS_ARREGLAR}. Tomé una foto: "
                       "voy a confirmarlo en NEXUS.", COLOR_BIEN)
        self._sonar("reparar", 0.6)
        self._tomar_foto(jugador, pub)

    def confirmar(self, jugador, noticia, con_ubicacion):
        """Publica la foto de lo que arregló: era verdad y ya está resuelto.
        Se propaga en verde, como un desmentido."""
        if noticia not in self.evidencias.get(jugador, []):
            return "No tienes foto de ese lugar.", 0
        self.evidencias[jugador].remove(noticia)
        nodo = self.nodo_de(jugador)
        st = self.stats[jugador]
        st["confirmados"] += 1
        pub = Publicacion(nodo, "confirmacion", noticia.rumor["confirmacion"])
        pub.foto = noticia.rumor["foto"]
        pub.desmiente = noticia
        pub.con_ubicacion = con_ubicacion
        self.publicaciones.append(pub)
        noticia.desmentida = True
        prob = PROB_CONVENCER_UBICACION if con_ubicacion else PROB_CONVENCER
        self.propagaciones.append(Propagacion(pub, nodo, VERDE, max_niveles=NIVELES_DESMENTIDO, prob=prob))
        jugador.sumar_puntos(PUNTOS_CONFIRMAR)
        self._sonar("senal", 0.6)
        texto = ("Confirmaste que era verdad y que ya está arreglado. Avisar lo que es cierto "
                 "también es parte de verificar: la tripulación confía más en ustedes.")
        if con_ubicacion:
            st["fotos_ubicacion"] += 1
            alien = self._alertar_alien(jugador)
            if alien is not None:
                texto += f" Pero en la foto se ve dónde estás: el {alien.nombre} viene por ti."
                jugador.avisar(f"¡Mi foto me delató! El {alien.nombre} viene", COLOR_MAL)
        else:
            st["fotos_recortadas"] += 1
            logro(self.juego, "perfil_bajo", jugador)
        return texto, PUNTOS_CONFIRMAR

    def publicar_normal(self):
        presos = self._presos()
        if not presos:
            return None
        autor = self.rng.choice(presos)
        pub = Publicacion(autor, "normal", self.rng.choice(NORMALES))
        self.publicaciones.append(pub)
        self.propagaciones.append(Propagacion(pub, autor, None, max_niveles=2))
        return pub

    # -- Cuentas falsas que crecen ------------------------------------------------------

    def seguidores(self, nodo):
        """A cuántas cuentas les llega lo que publica (sus aristas de salida)."""
        return self.grafo.grado_salida(nodo) if nodo in self.grafo else 0

    def ganados(self, nodo):
        """Seguidores que ganó un bot desde que abrió la cuenta."""
        if nodo not in self.grafo:
            return 0
        return max(0, self.seguidores(nodo) - self.grafo.datos[nodo].get("seguidores_al_abrir", 0))

    def cada_cuanto_crece(self):
        """ms entre un seguidor nuevo y el siguiente de cada bot."""
        return BOT_GANA_SEGUIDOR_S * 1000 * dificultad.valor(self.juego, "bot_crece_cada", 1.0)

    def _ganar_seguidor(self, bot):
        """El bot gana un seguidor: de preferencia un amigo de uno que ya lo sigue
        (le aparece porque un conocido lo sigue), si no, un prisionero al azar.
        Devuelve el nodo nuevo (o None si ya tiene el máximo o no queda nadie)."""
        g = self.grafo
        if self.seguidores(bot) >= BOT_MAX_SEGUIDORES:
            return None
        ya = g.vecinos(bot)
        libres = [p for p in self._presos() if p not in ya]
        if not libres:
            return None
        # p sigue a f (f -> p) y f sigue al bot (bot -> f): amigo de un seguidor.
        amigos = [p for p in libres if any(p in g.vecinos(f) for f in ya)]
        nuevo = self.rng.choice(amigos or libres)
        g.agregar_arista(bot, nuevo)
        self.seguidores_ganados += 1
        n = self.seguidores(bot)
        if n in AVISOS_SEGUIDORES:
            usuario = self.usuario(bot)
            for jugador in self.juego.jugadores:
                jugador.avisar(f"Veo en NEXUS que {usuario} no para de ganar seguidores: ya le llega a "
                               f"{n} personas.", COLOR_MAL)
            if hasattr(self.juego, "decir"):
                self.juego.decir("bot_crece")
        return nuevo

    # -- Rumores que se vuelven virales --------------------------------------------------

    def limite_viral(self):
        """Cuántos ms aguanta un rumor sin desmentir antes de volverse viral."""
        return VIRAL_S * 1000 * dificultad.valor(self.juego, "viral_cada", 1.0)

    def progreso_viral(self, pub):
        """0 a 1: qué tanto le falta a un rumor (o a una noticia) para volverse
        viral (1 = ya lo es)."""
        if pub.tipo not in ("rumor", "noticia"):
            return 0.0
        if pub.viral:
            return 1.0
        return max(0.0, min(1.0, pub.viral_ms / max(1, self.limite_viral())))

    def efecto_activo(self, lugar):
        """¿Hay un rumor de ese lugar viral y sin desmentir (la nave actúa como si
        fuera verdad) o una noticia verdadera de ahí que empeoró porque nadie la
        arregló (`_empeorar`)?"""
        return (any(p.viral and p.rumor and p.rumor.get("lugar") == lugar for p in self.rumores_activos())
                or any(p.efecto.get("empeoro") == lugar for p in self.noticias_activas()))

    def _volverse_viral(self, pub):
        """Nadie lo desmintió a tiempo: les llega a todos los grises (se lo creen
        con PROB_CREER_VIRAL) y la gente de la nave actúa como si fuera cierto.
        Una noticia (verdadera) solo se riega: no pinta a nadie de rojo."""
        pub.viral = True
        if pub.tipo == "noticia":
            lugar = NOMBRE_LUGAR.get(pub.rumor.get("lugar"), "la nave")
            if pub.arreglada:
                for jugador in self.juego.jugadores:
                    jugador.avisar(f"¡Lo de {lugar} se volvió viral! {pub.rumor.get('viral', VIRAL_GENERICO)}",
                                   COLOR_NEXUS)
                return
            # Era verdad y nadie fue a arreglarlo: empeora, y la gente ve que
            # nadie hace nada.
            texto = self._empeorar(pub)
            perdidos = 0
            for nodo in self._presos():
                if self.color(nodo) == VERDE and self.rng.random() < PROB_DESCONFIAR:
                    self.grafo.datos[nodo]["color"] = GRIS
                    perdidos += 1
            self.empeoradas += 1
            self.desconfiaron += perdidos
            if perdidos:
                texto += (f" La gente ve que nadie hace nada: {perdidos} "
                          f"{'persona dejó' if perdidos == 1 else 'personas dejaron'} de confiar en ustedes.")
            for jugador in self.juego.jugadores:
                jugador.avisar(f"¡Lo de {lugar} era verdad y nadie lo arregló! {texto}", COLOR_MAL)
            self._sonar("fallo", 0.7)
            return
        self.virales += 1
        for nodo in self._presos():
            if self.color(nodo) == GRIS and self.rng.random() < PROB_CREER_VIRAL:
                self.grafo.datos[nodo]["color"] = ROJO
                pub.creyentes.add(nodo)
        consecuencia = self._aplicar_efecto(pub)
        lugar = NOMBRE_LUGAR.get(pub.rumor.get("lugar"), "la nave")
        for jugador in self.juego.jugadores:
            jugador.avisar(f"¡Lo de {lugar} se volvió viral! {consecuencia}", COLOR_MAL)
        self._sonar("fallo", 0.7)
        if hasattr(self.juego, "decir"):
            self.juego.decir("rumor_viral", forzar=True)

    def _aplicar_efecto(self, pub):
        """Lo que hace la gente de la nave cuando el rumor se vuelve viral.
        Devuelve el texto de lo que pasó (el "viral" del rumor)."""
        juego = self.juego
        lugar = pub.rumor.get("lugar")
        texto = pub.rumor.get("viral", VIRAL_GENERICO)
        if lugar == "capsula":
            npcs = getattr(juego, "npcs", None)
            if npcs is not None:
                npcs.rendirse()
        elif lugar == "escondite":
            npcs = getattr(juego, "npcs", None)
            ocupados = npcs.esconderse(ESCONDITES_VIRAL, pub.lugar) if npcs is not None else []
            if not ocupados:
                texto = VIRAL_GENERICO
            pub.efecto["escondites"] = ocupados
        elif lugar == "terminal":
            zonas = [z for z in getattr(juego, "zonas", ()) if z.get("tipo") == "nexus"
                     and not z.get("desconectada")]
            if zonas:
                zona = min(zonas, key=lambda z: math.dist(z["rect"].center, pub.lugar))
                zona["desconectada"] = True
                pub.efecto["zona"] = zona
            else:
                texto = VIRAL_GENERICO
        return texto

    def _empeorar(self, pub):
        """Una noticia verdadera que nadie arregló a tiempo: el problema
        empeora (data/nexus.NOTICIAS "empeora"). Lo que dura se deshace al
        arreglarla (`_deshacer_empeora`); el apagón y la compuerta son eventos
        de la nave (el apagón se arregla en la caja de fusibles, como siempre).
        Devuelve el texto de lo que pasó."""
        juego = self.juego
        lugar = pub.rumor.get("lugar")
        texto = pub.rumor.get("empeora", "")
        eventos = getattr(juego, "eventos", None)
        pub.efecto["empeoro"] = lugar
        if lugar == "fusibles":
            if eventos is None or eventos.apagon or eventos.lanzar("apagon") is None:
                texto = "Nadie subió los breakers y la luz de la nave sigue fallando."
        elif lugar == "panel":
            if eventos is None or eventos.lanzar("compuerta") is None:
                texto = "Nadie arregló el panel en corto: sigue echando chispas."
        elif lugar == "terminal":
            zonas = [z for z in getattr(juego, "zonas", ()) if z.get("tipo") == "nexus"
                     and not z.get("desconectada")]
            if zonas and pub.lugar is not None:
                zona = min(zonas, key=lambda z: math.dist(z["rect"].center, pub.lugar))
                zona["desconectada"] = True
                pub.efecto["zona"] = zona
            else:
                texto = "Nadie reinició la terminal colgada."
        elif lugar == "puerta_doble":
            cerradas = [p for p in getattr(juego, "puertas_dobles", ()) if not p.get("abierta")]
            if cerradas and pub.lugar is not None:
                puerta = min(cerradas, key=lambda p: math.dist(p["rect"].center, pub.lugar))
                puerta["sin_corriente"] = True
                pub.efecto["lector"] = puerta
            else:
                texto = "Nadie arregló el lector de la puerta."
        # (celda: `efecto_activo("celda")` hace que la fuga vaya a FUGA_VIRAL;
        # escondite: el candado ya estaba y sigue.)
        return texto

    def _deshacer_empeora(self, pub):
        """Lo arreglaron: lo que había empeorado y dura, vuelve a estar bien."""
        zona = pub.efecto.pop("zona", None)
        if zona is not None:
            zona["desconectada"] = False
        puerta = pub.efecto.pop("lector", None)
        if puerta is not None:
            puerta["sin_corriente"] = False
        pub.efecto.pop("empeoro", None)

    def _quitar_efecto(self, pub):
        """Ya saben la verdad: la gente vuelve a lo de antes."""
        npcs = getattr(self.juego, "npcs", None)
        if pub.efecto.get("escondites") and npcs is not None:
            npcs.salir_de_escondites(pub.efecto["escondites"])
        zona = pub.efecto.get("zona")
        if zona is not None:
            zona["desconectada"] = False
        pub.efecto = {}

    # -- Fotos -----------------------------------------------------------------------------

    def _fotos(self):
        """Si un jugador está en el lugar de un rumor que le llegó, saca la foto."""
        for jugador in self.juego.jugadores:
            if jugador.preso or getattr(jugador, "eliminado", False):
                continue
            yendo = self.investigando.get(jugador)
            if (yendo is not None and yendo.tipo == "trampa"
                    and (yendo.reportada or math.dist(jugador.hitbox.center, yendo.lugar) <= RADIO_FOTO)):
                del self.investigando[jugador]
                if not yendo.reportada:
                    jugador.avisar(f"Aquí no hay nada... ¿y {self.usuario(yendo.autor)}?",
                                   COLOR_MAL)
            nodo = self.nodo_de(jugador)
            c = jugador.hitbox.center
            # Las noticias se arreglan en el lugar con un minijuego
            # (juego/tareas.py); sin minijuegos (algunas pruebas), con solo llegar.
            pub = self.noticia_para(jugador)
            if pub is not None and not getattr(self.juego, "minijuegos", False):
                self.arreglar(jugador, pub)
            elif pub is not None and jugador not in pub.avisados:
                pub.avisados.add(jugador)
                lugar = NOMBRE_LUGAR.get(pub.rumor.get("lugar"), "la nave")
                jugador.avisar(f"¡Lo de {lugar} es verdad! Tengo que arreglarlo: "
                               f"[{jugador.nombre_tecla('interactuar')}] {pub.rumor.get('pista', '')}.",
                               COLOR_NEXUS)
                self._sonar("senal", 0.4)
            for pub in self.rumores_activos():
                if nodo not in pub.alcanzados and self.investigando.get(jugador) is not pub:
                    continue
                if pub in self.evidencias[jugador]:
                    continue
                if math.dist(c, pub.lugar) <= RADIO_FOTO:
                    self.evidencias[jugador].append(pub)
                    if self.investigando.get(jugador) is pub:
                        del self.investigando[jugador]
                    jugador.avisar("Tomé la foto. Ahora la publico en NEXUS para desmentir el rumor.", COLOR_BIEN)
                    self._tomar_foto(jugador, pub)

    def _tomar_foto(self, jugador, pub):
        """El clic de la cámara: el flash y la foto que vuela al celular
        (screens/foto.py, que la dibuja cuando `foto_n` sube: los atributos
        del jugador viajan en red, así que el cliente la ve igual) y el sonido."""
        jugador.foto_n = getattr(jugador, "foto_n", 0) + 1
        jugador.foto_pub = pub.id      # (de qué rumor o noticia: la foto sale en lo que se publique)
        jugador.foto_lugar = NOMBRE_LUGAR.get(pub.rumor.get("lugar"), "la nave")
        self._sonar("foto", 0.8)

    # -- Acciones del jugador ---------------------------------------------------------------

    def feed(self, jugador):
        """Lo que le llegó por el grafo y lo que publicó él, lo más nuevo primero."""
        nodo = self.nodo_de(jugador)
        lista = [p for p in self.publicaciones if nodo in p.alcanzados or p.autor == nodo]
        return list(reversed(lista))[:MAX_FEED]

    def nodo_de_usuario(self, usuario):
        return next((n for n, d in self.grafo.datos.items() if d.get("usuario") == usuario), None)

    def trampa_activa(self):
        """La publicación con la que el Cambiaformas está cebando, si hay."""
        return next((p for p in reversed(self.publicaciones)
                     if p.tipo == "trampa" and not p.reportada and p.edad_ms < 70000), None)

    def publicar_trampa(self, usuario, texto, lugar, nombre_lugar=None):
        """El Cambiaformas publica haciéndose pasar por `usuario` (suplantación)."""
        autor = self.nodo_de_usuario(usuario)
        if autor is None or autor not in self.grafo:
            return None
        if not self._hay_lugar():
            return None
        pub = Publicacion(autor, "trampa", texto, falsa=True)
        pub.lugar = lugar
        pub.nombre_lugar = nombre_lugar
        pub.suplantada = True
        self.publicaciones.append(pub)
        self.propagaciones.append(Propagacion(pub, autor, None, max_niveles=5))
        return pub

    def reportar_suplantacion(self, jugador, pub):
        """Alguien notó que esa cuenta no la escribió su dueño: el Cambiaformas
        queda al descubierto un rato."""
        if pub is None or not pub.suplantada or pub.reportada:
            return "Esa publicación ya no está.", 0
        pub.reportada = True
        self.stats[jugador]["suplantaciones"] += 1
        jugador.sumar_puntos(PUNTOS_SUPLANTACION)
        logro(self.juego, "perfil_robado", jugador)
        cf = getattr(self.juego, "cambiaformas", None)
        if cf is not None:
            cf.desenmascarar()
        self._sonar("expuesto", 0.8)
        for otro in self.juego.jugadores:
            otro.avisar(f"¡Alguien se hacía pasar por {self.usuario(pub.autor)}! "
                        "El Cambiaformas quedó al descubierto", COLOR_BIEN)
        return (f"NEXUS confirmó que {self.usuario(pub.autor)} no escribió eso: era el "
                "Cambiaformas usando su nombre. Quedó al descubierto un rato.", PUNTOS_SUPLANTACION)

    def publicar_testimonio(self, nodo, texto):
        """Un prisionero rescatado cuenta en NEXUS que ustedes lo salvaron."""
        if nodo not in self.grafo:
            return None
        self.grafo.datos[nodo]["color"] = VERDE
        pub = Publicacion(nodo, "testimonio", texto)
        self.publicaciones.append(pub)
        self.propagaciones.append(Propagacion(pub, nodo, VERDE, max_niveles=NIVELES_DESMENTIDO,
                                              prob=PROB_CONVENCER))
        return pub

    def sin_leer(self, jugador):
        return sum(1 for p in self.feed(jugador)
                   if p.id not in self.vistas[jugador] and p.tipo != "normal")

    def via(self, jugador, pub):
        """Quién se la pasó (el vecino por el que le llegó)."""
        return pub.via.get(self.nodo_de(jugador), pub.autor)

    def investigar(self, jugador, pub):
        self.investigando[jugador] = pub
        return "Una flecha te lleva al lugar. Al llegar vas a ver si es verdad."

    def compartir(self, jugador, pub):
        nodo = self.nodo_de(jugador)
        st = self.stats[jugador]
        if pub.tipo == "noticia":
            # Era verdad... pero no lo sabía: ni castigo ni premio.
            st["compartidos_sin_verificar"] += 1
            copia = Publicacion(nodo, "compartido", pub.texto)
            copia.charla = True     # (volverla a compartir tampoco da nada)
            self.publicaciones.append(copia)
            self.propagaciones.append(Propagacion(copia, nodo, None, max_niveles=1))
            return ("La compartiste sin verificarla. Esta vez era verdad, pero no lo sabías: "
                    "pudo ser un rumor. No suma ni resta: verifica antes de compartir.", 0)
        if pub.tipo == "normal" or getattr(pub, "charla", False):
            # Charla: no hay nada que verificar, así que no cambia nada.
            copia = Publicacion(nodo, "compartido", pub.texto)
            copia.charla = True     # (volverla a compartir tampoco da nada)
            self.publicaciones.append(copia)
            self.propagaciones.append(Propagacion(copia, nodo, None, max_niveles=1))
            return ("Lo compartiste. No hay nada que verificar ahí, así que no da "
                    "puntos ni cambia la confianza.", 0)
        if pub.tipo in ("rumor", "trampa"):
            # Riega el rumor desde él, y los que lo siguen dejan de confiar.
            st["compartidos_falsos"] += 1
            for seguidor in self.grafo.vecinos(nodo):
                if self.grafo.datos[seguidor]["tipo"] == "preso":
                    self.grafo.datos[seguidor]["color"] = ROJO
            self.propagaciones.append(Propagacion(pub, nodo, ROJO, max_niveles=2))
            self._sonar("fallo", 0.5)
            return ("Lo compartiste sin verificar. Era falso: tus seguidores se lo "
                    "creyeron y ahora desconfían de ti. Antes de compartir, verifica.", -5)
        st["compartidos_ciertos"] += 1
        copia = Publicacion(nodo, "compartido", pub.texto)
        copia.desmiente = pub.desmiente
        self.publicaciones.append(copia)
        self.propagaciones.append(Propagacion(copia, nodo, VERDE,
                                              max_niveles=NIVELES_COMPARTIR_CIERTO,
                                              prob=PROB_CONVENCER))
        return "Compartiste algo cierto. Tus seguidores confían un poco más en ustedes.", 2

    def rastrear(self, jugador, pub):
        """Camino más corto desde quien la publicó hasta el jugador."""
        self.stats[jugador]["rastreos"] += 1
        camino = self.grafo.camino_mas_corto(pub.autor, self.nodo_de(jugador))
        if camino is None:
            # La cuenta ya no existe o se cortó el camino: se usa el que quedó guardado.
            camino, nodo = [self.nodo_de(jugador)], self.nodo_de(jugador)
            while nodo in pub.via and pub.via[nodo] != nodo and len(camino) < 12:
                nodo = pub.via[nodo]
                camino.append(nodo)
            camino.reverse()
        self.ultimo_rastreo = (camino, self.tiempo_ms)
        return camino

    def reportar(self, jugador, nodo, pub=None):
        """Reportar una cuenta: si es bot se borra del grafo. Si es la cuenta
        que el Cambiaformas está suplantando, se reporta la suplantación."""
        st = self.stats[jugador]
        trampa = self.trampa_activa()
        if trampa is not None and trampa.autor == nodo:
            return self.reportar_suplantacion(jugador, trampa)
        if self.es_bot(nodo):
            usuario = self.usuario(nodo)
            seguidores, ganados = self.seguidores(nodo), self.ganados(nodo)
            self.borrados.append((nodo, usuario, self.tiempo_ms))
            self.grafo.eliminar_nodo(nodo)
            st["bots_reportados"] += 1
            jugador.sumar_puntos(PUNTOS_REPORTAR_BOT)
            logro(self.juego, "cazador_de_bots", jugador)
            self._sonar("acierto", 0.6)
            if ganados <= 1:
                cuanto = (f"La cortaron a tiempo: solo le llegaba a {seguidores} personas.")
            else:
                cuanto = (f"Ya le llegaba a {seguidores} personas: ganó {ganados} seguidores "
                          "mientras nadie la reportaba.")
            return (f"{usuario} era una cuenta falsa del Cambiaformas. Quedó borrada: "
                    f"lo que regaba ya no pasa por ahí. {cuanto}", PUNTOS_REPORTAR_BOT)
        if nodo not in self.grafo:
            return "Esa cuenta ya no existe.", 0
        st["reportes_injustos"] += 1
        usuario = self.usuario(nodo)
        if self.grafo.datos[nodo]["tipo"] == "preso":
            self.grafo.datos[nodo]["color"] = ROJO
        self._sonar("fallo", 0.5)
        if pub is not None and pub.tipo == "noticia":
            return (f"{usuario} es un prisionero de verdad, y lo que se publicó era cierto. "
                    "Reportarlo no ayuda y ahora desconfía de ustedes. Antes de reportar, verifica.", -5)
        return (f"{usuario} es un prisionero de verdad: solo se creyó el rumor. Reportarlo "
                "no lo frena y ahora desconfía de ustedes. Busquen quién lo empezó.", -5)

    def desmentir(self, jugador, rumor, con_ubicacion):
        """Publica la foto del lugar: el desmentido se propaga en verde."""
        if rumor not in self.evidencias.get(jugador, []):
            return "No tienes foto de ese lugar.", 0
        self.evidencias[jugador].remove(rumor)
        nodo = self.nodo_de(jugador)
        st = self.stats[jugador]
        st["desmentidos"] += 1
        pub = Publicacion(nodo, "desmentido", rumor.rumor["desmentido"])
        pub.foto = rumor.rumor["foto"]
        pub.desmiente = rumor
        pub.con_ubicacion = con_ubicacion
        self.publicaciones.append(pub)
        # Llegar tarde convence menos: lo que avanzó la barra de "se vuelve viral".
        tarde = self.progreso_viral(rumor)
        creyeron = sum(1 for n in rumor.creyentes if n in self.grafo and self.color(n) == ROJO)
        era_viral = rumor.viral
        if not rumor.desmentida:
            rumor.desmentida = True
            # El rumor deja de avanzar.
            for prop in self.propagaciones:
                if prop.pub is rumor:
                    prop.frontera = []
            if rumor.viral:
                self._quitar_efecto(rumor)
        prob = PROB_CONVENCER_UBICACION if con_ubicacion else PROB_CONVENCER
        prob *= self.convence_a_tiempo(tarde)
        # Los que se lo creyeron pueden recapacitar aunque la verdad no les
        # llegue por la red (lo vieron en otro lado, alguien se lo contó).
        for n in rumor.creyentes:
            if (n in self.grafo and self.color(n) == ROJO
                    and self.rng.random() < PROB_RECAPACITAR * self.convence_a_tiempo(tarde)):
                self.grafo.datos[n]["color"] = GRIS
        self.propagaciones.append(Propagacion(pub, nodo, VERDE, max_niveles=NIVELES_DESMENTIDO,
                                              prob=prob))
        jugador.sumar_puntos(PUNTOS_DESMENTIR)
        logro(self.juego, "fact_checker", jugador)
        self._sonar("senal", 0.6)
        if tarde > TARDE_DESDE and creyeron > 0:
            self.creyeron_tarde += creyeron
            self._decir("desmentido_tarde", jugador.rol)
            texto = (f"Llegaste tarde: {creyeron} {'persona' if creyeron == 1 else 'personas'} "
                     "ya se lo habían creído, y a ellos la verdad les cuesta más.")
            if era_viral:
                texto += " Ahora que saben la verdad, la gente vuelve a lo de antes."
        else:
            self._decir("desmentido", jugador.rol)
            texto = ("¡A tiempo! Casi nadie alcanzó a creérselo. "
                     "La verdad ya está corriendo por NEXUS.")
        if con_ubicacion:
            st["fotos_ubicacion"] += 1
            alien = self._alertar_alien(jugador)
            if alien is not None:
                texto += f" Pero en la foto se ve dónde estás: el {alien.nombre} viene por ti."
                jugador.avisar(f"¡Mi foto me delató! El {alien.nombre} viene", COLOR_MAL)
        else:
            st["fotos_recortadas"] += 1
            logro(self.juego, "perfil_bajo", jugador)
        return texto, PUNTOS_DESMENTIR

    @staticmethod
    def convence_a_tiempo(tarde):
        """Qué fracción de lo normal convence un desmentido según qué tan tarde
        llega (0 = recién publicado el rumor, 1 = ya era viral)."""
        if tarde <= TARDE_DESDE:
            return 1.0
        return 1.0 - (1.0 - CONVENCE_TARDE) * (tarde - TARDE_DESDE) / (1.0 - TARDE_DESDE)

    def _alertar_alien(self, jugador):
        """La foto deja ver dónde está: el alien más cercano va para allá."""
        cambiaformas = getattr(self.juego, "cambiaformas", None)
        if cambiaformas is not None:
            cambiaformas.enterarse(jugador)      # él también lee NEXUS
        aliens = [a for a in getattr(self.juego, "aliens", ())
                  if a.descanso_ms <= 0 and a is not cambiaformas]
        if not aliens:
            return None
        c = jugador.hitbox.center
        alien = min(aliens, key=lambda a: math.dist(a.centro, c))
        if alien.oir(c):
            self._sonar("alarma", 0.4)
            return alien
        return None

    # -- Umbrales -------------------------------------------------------------------------

    def _revisar_umbrales(self):
        verde, rojo = self.barras()
        if not self.planos and verde >= self.umbral_planos:
            self.desbloquear_planos()

    def desbloquear_planos(self):
        if self.planos:
            return
        self.planos = True
        for jugador in self.juego.jugadores:
            jugador.avisar("¡La tripulación confía en nosotros! Nos pasaron los planos de la cápsula.",
                           COLOR_BIEN)
        equipo = getattr(self.juego, "equipo", None)
        if equipo is not None:
            equipo.sumar(PUNTOS_PLANOS)
        logro(self.juego, "planos")
        self._sonar("logro", 0.8)
        self._decir("planos")

    # -- Resumen para los resultados ----------------------------------------------------------

    def resumen(self):
        """Totales del equipo y un consejo según cómo usaron NEXUS."""
        total = {}
        for st in self.stats.values():
            for clave, valor in st.items():
                total[clave] = total.get(clave, 0) + valor
        minutos = sum(self.tiempo_celular_ms.values()) / 60000
        total["minutos_celular"] = minutos
        total["virales"] = self.virales
        total["creyeron_tarde"] = self.creyeron_tarde
        total["seguidores_bots"] = self.seguidores_ganados
        total["empeoradas"] = self.empeoradas
        if total.get("compartidos_falsos", 0) > total.get("desmentidos", 0):
            consejo = "Compartieron más rumores de los que desmintieron: antes de compartir, verifiquen."
        elif self.empeoradas > 0 and self.virales == 0:
            consejo = ("Algo que era verdad se quedó sin arreglar y empeoró: verificar también es "
                       "actuar cuando la noticia es cierta.")
        elif self.virales > 0:
            consejo = ("Dejaron que rumores se volvieran virales y la gente actuó como si fueran "
                       "ciertos: la desinformación cambia lo que hacemos. Verifiquen rápido.")
        elif self.seguidores_ganados >= SEGUIDORES_PARA_CONSEJO and total.get("bots_reportados", 0) == 0:
            consejo = ("Nadie reportó las cuentas falsas y ganaron seguidores: cada rumor nuevo les "
                       "llegaba a más gente. Reporten la fuente apenas la encuentren.")
        elif total.get("fotos_ubicacion", 0) > total.get("fotos_recortadas", 0):
            consejo = "Publicar dónde están los puso en peligro: cuiden su ubicación en redes."
        elif total.get("reportes_injustos", 0) > total.get("bots_reportados", 0):
            consejo = "Reportaron a gente que solo se creyó un rumor: busquen la fuente."
        elif total.get("desmentidos", 0) == 0:
            consejo = "Nadie desmintió nada: en redes, el silencio también deja ganar a la mentira."
        else:
            consejo = "Buen uso de NEXUS: verificaron, cuidaron su ubicación y frenaron los rumores."
        total["consejo"] = consejo
        return total
