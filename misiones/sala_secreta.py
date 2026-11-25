"""La sala oculta de los niños (docs/historia.md, idea de Campo).

Cuando la cápsula queda reparada (la misión pasa a "huida"), se abre una
pared de la Bahía, a la derecha de la cápsula: un pasillo lleva a una sala
escondida donde están los niños desaparecidos, dormidos en cápsulas de
cristal. Pueden ir a la cápsula y escapar sin entrar, o entrar.

Si alguien entra:

1. **Diálogo** (`DIALOGO_NINOS`): los agentes dicen lo que ven (son los niños
   del principio; lo que encontraron en la nave era de ellos). Mientras
   hablan, los aliens se quedan quietos.
2. **Votación** (`VOTACION`, 20 s): suena la alarma y a cada jugador le sale
   un menú: correr a la cápsula o quedarse con los niños. Al mismo tiempo
   TODOS los aliens van hacia la sala: se ven y se oyen venir (gritos cada
   vez más fuertes), pero cada uno camina a la velocidad justa para llegar
   a la puerta de la sala cuando el contador llega a 0, ni antes ni después
   (`_mover_aliens`). Si votaron todos, el contador se acorta.
3. **Desenlace** (`DESENLACE_MS`): entran los aliens y termina la partida con
   el final de lo que se votó (`FINALES` en data/historia.py): la opción con
   más votos gana; empate, se quedan; nadie votó, el Guardia suelta la fruta
   y destruye la cápsula.

Si escapan sin haber entrado, el final es "sin_entrar".

Por el camino (Acto 2) hay tres pistas que no entienden: una mochila, un
zapato y un dibujo (`PISTAS`). Se revisan con la tecla de interactuar.

Todo lo que se ve sale del estado de este objeto (sin referencias a otros
objetos): en red viaja tal cual al espejo del cliente
(cliente_servidor/servidor.OBJETOS) y el dibujo (screens/sala_secreta.py)
es el mismo aquí y allá. La pared de la puerta y la pintura de la sala en el
mapa se ponen con `sincronizar`, que corre en los dos lados.
"""

import math
import random

import pygame

from data.historia import (SALAS_OCULTAS, NOMBRE_SALA, ABRIR_PARED_MS, CAPSULAS, AL_ABRIRSE,
                           DIALOGO_NINOS, PISTAS_EN_DIALOGO, DIALOGO_MS, VOTACION, DESENLACE_MS,
                           FINALES, PISTAS, RADIO_PISTA, SUJETOS, APAGADAS, SE_APAGA, CELULAR_NINO,
                           REGENERAR)

COLOR_DIALOGO = (236, 240, 252)
COLOR_PISTA = (255, 214, 64)
COLOR_ALARMA = (245, 110, 100)

# Las cápsulas de los niños: lo que ocupan en el piso (px del mundo) y su
# separación. Se chocan como una pared (se tallan con la sala).
BASE_CAPSULA = (78, 34)
# Los aliens que vienen: la velocidad que se considera "corriendo" (px por ms)
# para acortar el contador si ya votaron todos, sin que lleguen volando.
VEL_MAX_ALIEN = 0.55
# Al entrar en el desenlace, a esta velocidad (px por ms) entran a la sala.
VEL_DESENLACE = 0.42
# Cada cuánto suenan los gritos de los que vienen (ms), del primero al último
# (cada grito dura ~6.6 s: así se enciman dos o tres, no más).
GRITOS_CADA_MS = (3600, 1900)
ALARMA_CADA_MS = 1500          # el pitido de la alarma mientras votan
# El pitido de los monitores de las cápsulas mientras hablan (ms entre
# pitidos): normal, mientras uno falla, y después (ya son menos).
MONITOR_CADA_MS = (850, 380, 1150)
RADIO_CAPSULA = 120            # a cuánto de una cápsula se puede regenerar (px del mundo)
# Cuándo suena qué mientras se abre la puerta (ms desde que empieza): se
# destraba (pitidos), suelta la presión (siseo) y se parte en dos.
SONIDOS_ABRIR = ((0, "senal", 0.8), (0, "tecleo", 0.7), (420, "senal", 0.6), (650, "puerta", 1.0),
                 (700, "compuerta", 0.7), (2350, "compuerta", 0.9))


def _rect(fracciones, mundo):
    x, y, w, h = fracciones
    return pygame.Rect(int(round(x * mundo.ancho)), int(round(y * mundo.alto)),
                       max(1, int(round(w * mundo.ancho))), max(1, int(round(h * mundo.alto))))


def geometria(mundo):
    """(puerta, pasillos, sala, capsulas) en px del mundo, o None si este mapa
    no tiene sala oculta. `pasillos`: en orden, de la puerta a la sala (el
    último entra a la sala por su izquierda). `capsulas`: [{"base": Rect,
    "nino": i}] (siempre las mismas: el espejo de la red arma las mismas)."""
    datos = SALAS_OCULTAS.get(getattr(mundo, "nombre_mapa", None))
    if not datos:
        return None
    puerta, sala = _rect(datos["puerta"], mundo), _rect(datos["sala"], mundo)
    pasillos = [_rect(p, mundo) for p in datos["pasillos"]]
    capsulas = []
    # Dos filas (arriba y abajo) con un pasillo en medio; la columna de la
    # izquierda queda libre (por ahí se entra).
    por_fila = max(1, (CAPSULAS + 1) // 2)
    margen_izq, margen_der = 110, 70
    ancho_util = sala.width - margen_izq - margen_der
    paso = ancho_util / max(1, por_fila - 1) if por_fila > 1 else 0
    filas = (sala.top + int(sala.height * 0.42), sala.bottom - 40)
    # La niña del principio (niño 0) va en la fila de abajo, la primera desde
    # la entrada: es la primera que se ve de frente al entrar.
    orden = [(1, k) for k in range(por_fila)] + [(0, k) for k in range(por_fila)]
    for n, (fila, k) in enumerate(orden[:CAPSULAS]):
        base = pygame.Rect(0, 0, *BASE_CAPSULA)
        base.midbottom = (int(sala.left + margen_izq + k * paso), filas[fila])
        capsulas.append({"base": base, "nino": n, "fila": fila,
                         "sujeto": SUJETOS[n % len(SUJETOS)] if SUJETOS else n + 1})
    return puerta, pasillos, sala, capsulas


def dintel(mundo):
    """El pedazo de pared de encima de la puerta (se dibuja delante de los
    personajes: se pasa por debajo). None si el mapa no tiene sala oculta."""
    datos = SALAS_OCULTAS.get(getattr(mundo, "nombre_mapa", None))
    if not datos or "dintel" not in datos:
        return None
    return _rect(datos["dintel"], mundo)


def no_pintar(mundo):
    """Lo que la pintura de la sala no toca (el piso de la Bahía)."""
    datos = SALAS_OCULTAS.get(getattr(mundo, "nombre_mapa", None)) or {}
    return [_rect(r, mundo) for r in datos.get("no_pintar", ())]


def tallar(mundo):
    """Abre el hueco de los pasillos y de la sala en las paredes del mapa (y
    pone las cápsulas como paredes). Va en `paredes_archivo`, antes de los
    muebles y de las salas selladas: así la navegación de los aliens ya cuenta
    con la sala. La puerta la tapa hasta que se abra. Se hace una sola vez por
    mundo (el mundo se reutiliza entre rondas del mismo mapa)."""
    geo = geometria(mundo)
    if geo is None or mundo.__dict__.get("_sala_oculta_tallada"):
        return geo is not None
    _, pasillos, sala, capsulas = geo
    from juego.salas_selladas import restar_todos
    huecos = list(pasillos) + [sala]
    nuevas = []
    for pared in mundo.paredes_archivo:
        if any(pared.colliderect(h) for h in huecos):
            nuevas += restar_todos([pared], huecos)
        else:
            nuevas.append(pared)
    nuevas += [pygame.Rect(c["base"]) for c in capsulas]
    mundo.paredes_archivo = nuevas
    mundo.__dict__["_sala_oculta_tallada"] = True
    mundo.paredes_base = list(nuevas)
    mundo.__dict__.pop("_navegaciones", None)
    mundo.reiniciar_paredes()
    return True


def apartar_decoracion(objetos, mundo):
    """La decoración que tape la entrada (la lámpara de la Bahía, delante de
    la puerta empotrada) se corre a un lado, para que se pueda pasar. En
    `objetos` (lo que se cargó del mapa para esta partida), antes de armar los
    muebles; el archivo del mapa no cambia."""
    geo = geometria(mundo)
    if geo is None or not objetos:
        return
    puerta, pasillos, _, _ = geo
    boca = pasillos[0].clip(pygame.Rect(pasillos[0].x, puerta.y, pasillos[0].width, 10 ** 5))
    boca.height += 120                     # y lo que está delante de la puerta, en la Bahía
    from juego.decoracion import rect_hitbox, rect_imagen
    for dato in objetos.get("decoracion") or ():
        caja = rect_hitbox(dato, mundo.ancho, mundo.alto) or rect_imagen(dato, mundo.ancho, mundo.alto)
        if caja is None:
            continue
        caja = pygame.Rect(caja)
        if not caja.colliderect(boca):
            continue
        # Al lado más cercano, justo afuera del pasillo.
        if caja.centerx < boca.centerx:
            dx = (boca.left - 4) - caja.right
        else:
            dx = (boca.right + 4) - caja.left
        dato["rx"] = (dato["rx"] * mundo.ancho + dx) / mundo.ancho


class SalaSecreta:
    def __init__(self, juego, objetos=None):
        self.juego = juego
        mundo = juego.mundo
        geo = geometria(mundo)
        self.activa = geo is not None and bool(getattr(juego.mision, "activa", False))
        # estado: "cerrada" -> "abriendo" -> "abierta" -> "dialogo" -> "votacion"
        # -> "desenlace" -> "fin"
        self.estado = "cerrada"
        self.estado_ms = 0               # cuánto lleva en este estado
        self.puerta = self.pasillo = self.sala = None
        self.pasillos = []
        self.capsulas = []
        self.entraron = False
        self.se_abrio = False
        self.linea = 0                   # la línea del diálogo que va
        self.votos = [None] * len(juego.jugadores)    # por puesto: "escapar" / "quedarse" / None
        self.votantes = [True] * len(juego.jugadores)
        self.quedan_ms = 0
        self.total_ms = VOTACION["segundos"] * 1000
        self.resultado = None            # "escapar" / "quedarse" / "nadie"
        self.acortado = False
        self.cerca = 0.0                 # 0..1: qué tan cerca vienen los aliens (sonido, dibujo)
        self.pistas = []
        self.encontradas = 0
        self.gritos_ms = 0
        self.alarma_ms = 0
        self.segundo = None              # el último segundo que sonó (cuenta regresiva)
        self._caminos = {}               # nombre del alien -> {"puntos", "destino", "pedido_ms"}
        # Los que no lo lograron (data/historia.py): las cápsulas apagadas, la
        # que se apaga mientras hablan (fallando_ms > 0: parpadea), el Biomante
        # que intenta regenerar una ([cápsula, ms] o None) y el celular del piso.
        self.apagadas = []
        self.fallando_ms = 0
        self.regenera = None
        self.celular = None
        self.monitor_ms = 0
        self.dintel = None
        if geo is None:
            return
        self.puerta, self.pasillos, self.sala, self.capsulas = geo
        self.pasillo = self.pasillos[-1]          # el que entra a la sala
        self.dintel = dintel(mundo)
        self.apagadas = [i for i in APAGADAS if i < len(self.capsulas)]
        i = CELULAR_NINO.get("capsula")
        if i is not None and i < len(self.capsulas):
            base = self.capsulas[i]["base"]
            self.celular = (base.centerx + 52, base.bottom + 34)
        if not self.activa:
            return
        # La losa tapa el pasillo hasta que se abre (una pared de la partida,
        # como la puerta con código: la navegación la cuenta como cerrada).
        if self.puerta not in mundo.paredes:
            mundo.paredes.append(self.puerta)
        salas = getattr(juego, "salas", None)
        if isinstance(salas, list) and not any(n == NOMBRE_SALA for n, _ in salas):
            salas += [(NOMBRE_SALA, r) for r in [self.sala] + list(self.pasillos)]
        self.pistas = self._poner_pistas(objetos or {})

    # -- Preguntas -----------------------------------------------------------------------

    @property
    def en_secuencia(self):
        """Diálogo, votación o desenlace: los aliens los maneja esta sala, la
        misión no termina por su cuenta y el reloj de la Feria se detiene."""
        return self.estado in ("dialogo", "votacion", "desenlace")

    def bloquea_fin(self):
        return self.activa and (self.en_secuencia or self.estado == "fin")

    def conduce(self, alien):
        """¿Este alien lo mueve la sala (y no su árbol de comportamiento)?"""
        return self.activa and self.en_secuencia and getattr(alien, "tipo", "") != "guardia"

    def puede_votar(self, jugador):
        """Todos los que siguen en la partida (también el que está en una celda);
        no un puesto que todavía no tiene mando (no podría votar nunca)."""
        return (self.estado == "votacion" and not getattr(jugador, "eliminado", False)
                and not getattr(jugador, "desconectado", False)
                and (getattr(jugador, "puede_moverse", True) or jugador.preso is not None
                     or getattr(jugador, "mando_desconectado", False)))

    def en_la_sala(self, jugador):
        return self.sala is not None and self.sala.collidepoint(jugador.hitbox.center)

    # -- Cada cuadro ----------------------------------------------------------------------

    def actualizar(self, dt):
        if not self.activa:
            return
        antes = self.estado_ms
        self.estado_ms += dt

        def paso(ms):                       # ¿se cruzó `ms` en este cuadro?
            return antes < ms <= self.estado_ms or (ms == 0 and antes == 0)
        mision = self.juego.mision
        if self.estado == "cerrada":
            if mision is not None and mision.fase == "huida":
                self._cambiar("abriendo")
                self.se_abrio = True
                antes = -1
        if self.estado == "abriendo":
            for ms, nombre, volumen in SONIDOS_ABRIR:
                if antes < ms <= self.estado_ms:
                    self._sonar(nombre, volumen)
            if self.estado_ms >= ABRIR_PARED_MS:
                self._cambiar("abierta")
                quien = self._hablante(None)
                if quien is not None:
                    self._decir_a_todos(quien, AL_ABRIRSE)
                self._neila("sala_abierta")
        elif self.estado == "abierta":
            dentro = [j for j in self.juego.jugadores
                      if not j.preso and not getattr(j, "eliminado", False) and self.en_la_sala(j)]
            if dentro:
                self.entraron = True
                self.linea = 0
                self._cambiar("dialogo")
                self._sonar("susurro", 0.8)
                self._decir_linea(0)
                self.monitor_ms = 600
        elif self.estado == "dialogo":
            self._quietos(dt)
            self._monitores(dt, paso)
            linea = int(self.estado_ms // DIALOGO_MS)
            if linea != self.linea and linea < len(DIALOGO_NINOS):
                self.linea = linea
                self._decir_linea(linea)
            if self.estado_ms >= DIALOGO_MS * len(DIALOGO_NINOS):
                self._empezar_votacion()
        elif self.estado == "votacion":
            self._votacion(dt)
        elif self.estado == "desenlace":
            self._mover_adentro(dt)
            self.cerca = 1.0
            self.gritos_ms -= dt
            if self.gritos_ms <= 0:
                self.gritos_ms = 1300
                self._sonar(random.choice(("gritos_aliens_1", "gritos_aliens_2")), 1.0)
            if self.estado_ms >= DESENLACE_MS:
                self._terminar()
        if self.regenera is not None:
            self.regenera = [self.regenera[0], self.regenera[1] + dt]
            if self.regenera[1] >= REGENERAR["ms"]:
                self.regenera = None
        self.sincronizar()

    def _monitores(self, dt, paso):
        """Mientras hablan: el pitido de los monitores, y la cápsula que se
        apaga (parpadea, su latido se corta, NEILA la archiva)."""
        i = SE_APAGA.get("capsula")
        desde, dura = SE_APAGA.get("desde_ms", 0), SE_APAGA.get("dura_ms", 1)
        viva = i is not None and i < len(self.capsulas) and i not in self.apagadas
        if viva and paso(desde):
            self.fallando_ms = 1
            self._sonar("monitor_falla", 0.7)
        if self.fallando_ms > 0:
            self.fallando_ms += dt
            if self.fallando_ms >= dura:
                self.fallando_ms = 0
                if i not in self.apagadas:
                    self.apagadas.append(i)
                self._sonar("monitor_plano", 0.8)
                self.monitor_ms = 2600          # (un silencio, y vuelven los pitidos: menos)
        if paso(desde + dura + 900) and i in self.apagadas:
            self._neila("sala_archivado")
        self.monitor_ms -= dt
        if self.monitor_ms <= 0:
            normal, fallando, despues = MONITOR_CADA_MS
            if self.fallando_ms > 0:
                self.monitor_ms = fallando
                self._sonar("monitor_bip", 0.45)
            else:
                self.monitor_ms = despues if i in self.apagadas else normal
                self._sonar("monitor_bip", 0.25)

    def _cambiar(self, estado):
        self.estado, self.estado_ms = estado, 0

    # -- La pared y la pintura de la sala (los dos lados de la red) -------------------------

    def sincronizar(self):
        """La puerta en `mundo.paredes` mientras está cerrada (el pasillo y la
        sala no se pintan en el mapa: se dibujan encima, solo en la vista de
        quien cruzó la puerta, screens/sala_secreta.py). Lo llama
        `actualizar` y, en red, el espejo del cliente después de copiar la
        instantánea (cliente_servidor/espejo.py)."""
        if not self.activa:
            return
        mundo = self.juego.mundo
        cerrada = self.estado in ("cerrada", "abriendo")
        if cerrada and self.puerta not in mundo.paredes:
            mundo.paredes.append(self.puerta)
        elif not cerrada and self.puerta in mundo.paredes:
            mundo.paredes[:] = [p for p in mundo.paredes if p != self.puerta]

    # -- Diálogo ----------------------------------------------------------------------------

    def _presentes(self):
        return [j for j in self.juego.jugadores
                if not getattr(j, "eliminado", False) and not getattr(j, "desconectado", False)]

    def _hablante(self, rol):
        presentes = self._presentes()
        if not presentes:
            return None
        for j in presentes:
            if j.rol == rol:
                return j
        # El que está en la sala (o el primero), rotando para que no hable siempre el mismo.
        adentro = [j for j in presentes if self.en_la_sala(j)] or presentes
        return adentro[self.linea % len(adentro)]

    def _decir_linea(self, i):
        datos = DIALOGO_NINOS[i]
        quien = self._hablante(datos.get("rol"))
        if quien is None:
            return
        n = min(3, self.encontradas)
        texto = datos["texto"].replace("{pistas}", PISTAS_EN_DIALOGO.get(n, "")).strip()
        self._decir_a_todos(quien, texto)

    def _decir_a_todos(self, quien, texto, color=COLOR_DIALOGO):
        """`quien` lo dice y todos lo ven, con su foto y su nombre."""
        rol = getattr(quien, "rol", "") or ""
        for j in self.juego.jugadores:
            if getattr(j, "eliminado", False):
                continue
            if j is quien:
                j._mostrar_mensaje(texto, color, None)
            else:
                j._mostrar_mensaje(texto, color, [rol, rol.upper()])

    def _neila(self, evento):
        decir = getattr(self.juego, "decir", None)
        if decir is not None:
            decir(evento, None, True)

    # -- Votación ------------------------------------------------------------------------------

    def _empezar_votacion(self):
        self._cambiar("votacion")
        self.quedan_ms = self.total_ms = VOTACION["segundos"] * 1000
        self.votos = [None] * len(self.juego.jugadores)
        self.votantes = [self.puede_votar(j) for j in self.juego.jugadores]
        self.gritos_ms = 1200
        self._sonar("alarma", 1.0)
        self._neila("sala_alarma")
        for j in self.juego.jugadores:
            if getattr(j, "escondido", False):
                j.salir_del_escondite()
            j.mensajes_pendientes = []
        self._abrir_menus()
        for alien in self._aliens():
            alien.alerta = True
            alien.accion = "PERSEGUIR"
            alien.objetivo = None
            if getattr(alien, "tipo", "") == "cambiaformas":
                # Se le cae el disfraz: viene como es.
                if getattr(alien, "disfrazado", False):
                    alien.disfrazado = False
                    alien.transformando_ms = getattr(alien, "transformando_ms", 0) or 750
                alien.siguiendo = None

    def _abrir_menus(self):
        """El menú de la votación a cada uno que puede votar (si alguien lo
        cerró con "volver", se vuelve a abrir)."""
        opciones = [{"texto": o["texto"]} for o in VOTACION["opciones"]]
        for i, j in enumerate(self.juego.jugadores):
            if not self.puede_votar(j):
                continue
            panel = j.panel
            if isinstance(panel, dict) and panel.get("tipo") == "votacion":
                continue
            j.panel = {"tipo": "votacion", "filas": [[0, 1]], "opciones": opciones}
            j.cursor = 0 if self.votos[i] != "quedarse" else 1

    def tecla(self, jugador, key):
        """Las teclas de la votación (izquierda/derecha escogen, interactuar
        vota). True si era una tecla de este jugador mientras vota. Va antes que
        todo en Game._tecla_en_partida (también para el que está en una celda)."""
        if not self.activa:
            return False
        panel = jugador.panel
        if isinstance(panel, dict) and panel.get("tipo") == "celular_nino":
            # El celular del piso: cualquier tecla suya lo cierra.
            if any(jugador.es_tecla(key, a) for a in jugador.teclas):
                jugador.cerrar_panel()
                self._sonar("menu_mover", 0.4)
                return True
            return False
        if self.estado != "votacion" or not self.puede_votar(jugador):
            return False
        # (como un mosaico de una fila: lo mismo que predice el cliente en red,
        # cliente_servidor/eco.py)
        from juego.app import mover_en_mosaico
        mover = {"izquierda": (0, -1), "derecha": (0, 1), "arriba": (-1, 0), "abajo": (1, 0)}
        for accion, (dfila, dcol) in mover.items():
            if jugador.es_tecla(key, accion):
                if dcol:
                    jugador.cursor = mover_en_mosaico([[0, 1]], jugador.cursor % 2, dfila, dcol)
                    self._sonar("menu_mover", 0.4)
                return True
        if jugador.es_tecla(key, "interactuar"):
            self.votar(jugador, VOTACION["opciones"][jugador.cursor % len(VOTACION["opciones"])]["clave"])
            return True
        return any(jugador.es_tecla(key, a) for a in jugador.teclas)

    def votar(self, jugador, clave):
        if self.estado != "votacion":
            return
        try:
            i = self.juego.jugadores.index(jugador)
        except ValueError:
            return
        nuevo = self.votos[i] != clave
        self.votos[i] = clave
        if nuevo:
            self._sonar("menu_ok", 0.7)
            self._sonar("encajar", 0.5)

    def _votacion(self, dt):
        self._abrir_menus()
        self.quedan_ms = max(0, self.quedan_ms - dt)
        jugadores = self.juego.jugadores
        votan = [i for i, j in enumerate(jugadores) if self.puede_votar(j)]
        if (votan and not self.acortado and all(self.votos[i] is not None for i in votan)):
            self.acortado = True
            minimo = VOTACION["segundos_si_votaron_todos"] * 1000
            falta = max((self._largo_restante(n) for n in self._caminos), default=0) / VEL_MAX_ALIEN
            self.quedan_ms = min(self.quedan_ms, max(minimo, falta))
        self.cerca = 1 - self.quedan_ms / max(1, self.total_ms)
        self._mover_aliens(dt)
        # Los gritos de los que vienen: cada vez más seguidos y más fuertes.
        self.alarma_ms -= dt
        if self.alarma_ms <= 0:
            self.alarma_ms = ALARMA_CADA_MS
            self._sonar("alarma", 0.35 + 0.3 * self.cerca)
        segundo = int(math.ceil(self.quedan_ms / 1000))
        if segundo != self.segundo:
            self.segundo = segundo
            if 0 < segundo <= 5:
                self._sonar("tecleo", 0.9)
        self.gritos_ms -= dt
        if self.gritos_ms <= 0:
            lento, rapido = GRITOS_CADA_MS
            self.gritos_ms = lento + (rapido - lento) * self.cerca
            self._sonar("gritos_aliens_1" if random.random() < 0.5 else "gritos_aliens_2",
                        0.25 + 0.75 * self.cerca)
        if self.quedan_ms <= 0:
            self._decidir()

    def _decidir(self):
        votos = [v for v in self.votos if v is not None]
        if not votos:
            self.resultado = "nadie"
        else:
            escapar = votos.count("escapar")
            quedarse = votos.count("quedarse")
            self.resultado = "escapar" if escapar > quedarse else "quedarse"
        for j in self.juego.jugadores:
            if isinstance(j.panel, dict) and j.panel.get("tipo") == "votacion":
                j.cerrar_panel()
        self._cambiar("desenlace")
        self.gritos_ms = 0
        self._sonar("susto", 1.0)
        textos = {"escapar": "¡A la cápsula, ya! ¡Corran!",
                  "quedarse": "No los vamos a dejar solos.",
                  "nadie": "..."}
        quien = self._hablante(None)
        if quien is not None:
            self._decir_a_todos(quien, textos[self.resultado],
                                COLOR_ALARMA if self.resultado != "escapar" else (255, 214, 64))
        if self.resultado == "escapar":
            self._sonar("cohete", 1.0)
        elif self.resultado == "nadie":
            self._sonar("guardia_esfuerzo_1", 1.0)

    def _terminar(self):
        self._cambiar("fin")
        mision = self.juego.mision
        if mision is None:
            return
        final = {"escapar": "escaparon", "quedarse": "quedarse", "nadie": "nadie"}[self.resultado or "nadie"]
        mision.final = final
        mision.resultado = "victoria" if FINALES[final]["victoria"] else "derrota"
        mision.motivo_fin = "final_" + final

    # -- Los aliens que vienen -----------------------------------------------------------------

    def _aliens(self):
        return [a for a in self.juego.aliens if self.conduce(a)]

    def _quietos(self, dt):
        """Mientras hablan, los aliens se quedan donde están (respirando)."""
        for alien in self._aliens():
            alien.tiempo_ms = getattr(alien, "tiempo_ms", 0) + dt
            alien.moviendose = False

    def _destino(self, k):
        """El puesto `k` en la fila de aliens del pasillo (el 0, en la puerta de la sala)."""
        x = self.sala.left - 34 - k * 46
        x = max(self.pasillo.left + 30, x)
        y = self.pasillo.centery + (22 if k % 2 else -22)
        return (x, y)

    def _mover_aliens(self, dt):
        aliens = sorted(self._aliens(), key=lambda a: math.dist(a.centro, self.pasillo.center))
        for k, alien in enumerate(aliens):
            alien.tiempo_ms = getattr(alien, "tiempo_ms", 0) + dt
            alien.alerta = True
            if getattr(alien, "transformando_ms", 0) > 0:
                # (el Cambiaformas: su transformación la descuenta su
                # PERSEGUIR, que ahora no corre)
                alien.transformando_ms = max(0, alien.transformando_ms - dt)
            datos = self._caminos.get(alien.nombre)
            if datos is None:
                datos = self._caminos[alien.nombre] = {"puntos": None, "destino": self._destino(k),
                                                       "pedido_ms": 0}
            if datos["puntos"] is None:
                camino = self._buscar(alien, datos, dt)
                if camino is None:
                    alien.moviendose = False
                    continue
                datos["puntos"] = list(camino)
            # A la velocidad justa para llegar cuando el contador llegue a 0.
            restante = self._largo_restante(alien.nombre, alien.centro)
            velocidad = restante / max(1.0, self.quedan_ms)
            self._avanzar(alien, datos, velocidad * dt)

    def _buscar(self, alien, datos, dt):
        """El camino de este alien a su puesto, buscado de a pedazos (unas
        celdas por cuadro, como los caminos largos de los prisioneros). Con la
        alarma la nave les abre todo: se busca sin las puertas cerradas ni los
        sellos (si no, uno detrás de una puerta para dos se quedaba atascado o,
        peor, cruzaba las paredes en línea recta). None mientras busca."""
        from juego import navegacion
        datos["pedido_ms"] += dt
        busqueda = datos.get("_busqueda")
        if busqueda is None:
            nav = navegacion.de_mundo(self.juego.mundo, alien.hitbox.width, alien.hitbox.height)
            busqueda = datos["_busqueda"] = nav._busqueda(alien.centro, datos["destino"], True, [],
                                                          navegacion.PRESUPUESTO_CUADRO)
        try:
            next(busqueda)
        except StopIteration as fin:
            camino, parcial, _ = fin.value if fin.value else (None, False, None)
            datos["_busqueda"] = None
            if camino and not parcial:
                return list(camino) + [datos["destino"]]
            if camino:
                # Ni así llega (una sala cerrada): hasta donde pueda y ahí se queda.
                return list(camino)
            return []
        except Exception:
            datos["_busqueda"] = None
            return []
        if datos["pedido_ms"] > 4000:
            datos["_busqueda"] = None
            return []
        return None

    def _largo_restante(self, nombre, desde=None):
        datos = self._caminos.get(nombre)
        if not datos or not datos["puntos"]:
            return 0.0
        puntos = datos["puntos"]
        if desde is None:
            alien = next((a for a in self.juego.aliens if a.nombre == nombre), None)
            desde = alien.centro if alien is not None else puntos[0]
        largo, previo = 0.0, desde
        for p in puntos:
            largo += math.dist(previo, p)
            previo = p
        return largo

    def _avanzar(self, alien, datos, paso):
        puntos = datos["puntos"]
        x, y = alien.centro
        antes = (x, y)
        while paso > 0 and puntos:
            px, py = puntos[0]
            d = math.hypot(px - x, py - y)
            if d <= paso:
                x, y = px, py
                paso -= d
                puntos.pop(0)
            else:
                x += (px - x) * paso / d
                y += (py - y) * paso / d
                paso = 0
        alien.hitbox.center = (int(round(x)), int(round(y)))
        dx, dy = x - antes[0], y - antes[1]
        alien.moviendose = abs(dx) + abs(dy) > 0.05
        if alien.moviendose:
            alien.angulo = math.atan2(dy, dx)

    def _mover_adentro(self, dt):
        """El desenlace: entran a la sala, hacia los agentes que están adentro."""
        adentro = [j for j in self.juego.jugadores if self.en_la_sala(j) and not getattr(j, "eliminado", False)]
        for k, alien in enumerate(self._aliens()):
            alien.tiempo_ms = getattr(alien, "tiempo_ms", 0) + dt
            if adentro:
                meta = adentro[k % len(adentro)].hitbox.center
                meta = (meta[0] + (k % 3 - 1) * 40, meta[1] + (k % 2) * 30 - 15)
            else:
                meta = (self.sala.centerx - 120 + (k % 4) * 80, self.sala.centery)
            x, y = alien.centro
            d = math.dist((x, y), meta)
            if d < 30:
                alien.moviendose = False
                continue
            paso = min(d - 28, VEL_DESENLACE * dt)
            alien.hitbox.center = (int(x + (meta[0] - x) * paso / d), int(y + (meta[1] - y) * paso / d))
            alien.angulo = math.atan2(meta[1] - y, meta[0] - x)
            alien.moviendose = True

    # -- Las pistas del Acto 2 --------------------------------------------------------------------

    def _poner_pistas(self, objetos):
        """Cada pista en la primera de sus salas que esté abierta en esta
        partida, en un lugar libre de esa sala al que se llegue caminando."""
        juego, mundo = self.juego, self.juego.mundo
        salas = [(n, r) for n, r in (getattr(juego, "salas", None) or []) if n != NOMBRE_SALA]
        sellado = getattr(mundo, "sellado", None)
        cerradas = set(getattr(sellado, "cerradas", ()) or ())
        from juego.salas_selladas import clave
        cerradas = {clave(n) for n in cerradas}
        spawn = juego.jugadores[0].hitbox.center if juego.jugadores else None
        from juego import navegacion
        nav = navegacion.de_mundo(mundo, 34, 20)
        usados = []
        ocupado = [e["rect"] for e in getattr(juego, "escondites", ())]
        ocupado += [z["rect"] for z in getattr(juego, "zonas", ())]
        pistas = []
        for datos in PISTAS:
            punto = None
            for nombre in datos["salas"]:
                if clave(nombre) in cerradas:
                    continue
                rects = sorted((r for n, r in salas if clave(n) == clave(nombre)),
                               key=lambda r: -r.width * r.height)
                for rect in rects[:1]:
                    punto = self._lugar_libre(rect, nav, spawn, usados, ocupado, datos["tipo"])
                    if punto is not None:
                        break
                if punto is not None:
                    break
            if punto is None:
                continue
            usados.append(punto)
            pistas.append({"tipo": datos["tipo"], "punto": punto, "encontrada": False})
        return pistas

    def _lugar_libre(self, rect, nav, spawn, usados, ocupado, semilla):
        mundo = self.juego.mundo
        rng = random.Random(f"{mundo.nombre_mapa}:{semilla}:{rect.x}:{rect.y}")
        zona = rect.inflate(-80, -80)
        if zona.width <= 0 or zona.height <= 0:
            return None
        candidatos = [(zona.x + int(zona.width * (i + 0.5) / 6), zona.y + int(zona.height * (j + 0.5) / 5))
                      for i in range(6) for j in range(5)]
        rng.shuffle(candidatos)
        for p in candidatos:
            caja = pygame.Rect(0, 0, 60, 40)
            caja.center = p
            if mundo.colisiona(caja.inflate(30, 30)):
                continue
            if any(caja.colliderect(o) for o in ocupado):
                continue
            if any(math.dist(p, u) < 400 for u in usados):
                continue
            if spawn is not None and not nav.conectados(spawn, p, sellos=False, extra=[]):
                continue
            return p
        return None

    def pista_cerca(self, jugador):
        for pista in self.pistas:
            if math.dist(pista["punto"], jugador.hitbox.center) <= RADIO_PISTA:
                return pista
        return None

    # -- Adentro: el celular del piso y las cápsulas apagadas ---------------------------------------

    def _se_puede_revisar(self, jugador):
        return (self.estado in ("abierta", "dialogo") and not jugador.preso
                and not getattr(jugador, "eliminado", False))

    def celular_cerca(self, jugador):
        return (self.celular is not None and self._se_puede_revisar(jugador)
                and math.dist(self.celular, jugador.hitbox.center) <= RADIO_PISTA)

    def capsula_apagada_cerca(self, jugador):
        """La cápsula apagada que el Biomante tiene al lado (su índice) o None."""
        if getattr(jugador, "rol", None) != "Biomante" or not self._se_puede_revisar(jugador):
            return None
        for i in self.apagadas:
            base = self.capsulas[i]["base"]
            if math.dist(base.center, jugador.hitbox.center) <= RADIO_CAPSULA:
                return i
        return None

    def pista(self, jugador):
        """La pista abajo de la pantalla ("Revisar la mochila") si tiene una cerca."""
        if not self.activa or jugador.preso:
            return None
        if self.celular_cerca(jugador):
            return CELULAR_NINO["pista"]
        if self.capsula_apagada_cerca(jugador) is not None:
            return REGENERAR["pista"]
        cerca = self.pista_cerca(jugador)
        if cerca is None:
            return None
        datos = next(d for d in PISTAS if d["tipo"] == cerca["tipo"])
        return datos["pista"]

    def interactuar(self, jugador):
        """Revisar una pista (tecla de interactuar). True si había una."""
        if not self.activa:
            return False
        if self.celular_cerca(jugador):
            jugador.panel = {"tipo": "celular_nino", "titulo": CELULAR_NINO["contacto"]}
            self._sonar("recoger", 0.6)
            return True
        i = self.capsula_apagada_cerca(jugador)
        if i is not None:
            if self.regenera is None:
                self.regenera = [i, 0]
                self._sonar("curar", 0.9)
                self._sonar("fallo", 0.5)
                self._decir_a_todos(jugador, REGENERAR["texto"])
            return True
        cerca = self.pista_cerca(jugador)
        if cerca is None:
            return False
        datos = next(d for d in PISTAS if d["tipo"] == cerca["tipo"])
        jugador.avisar(datos["texto"], COLOR_PISTA)
        if not cerca["encontrada"]:
            cerca["encontrada"] = True
            self.encontradas += 1
            self._sonar("nota", 0.8)
        return True

    # -- Sonido ---------------------------------------------------------------------------------

    def _sonar(self, nombre, volumen=1.0):
        sonar = getattr(self.juego, "sonar", None)
        if sonar is not None:
            sonar(nombre, volumen)
