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

El baúl de la prisión (Diego, nov 25): pide un código de 4 números escrito
en una nota normal cualquiera del mapa; adentro hay un martillo (un objeto
del inventario, de cualquier rol; si quien lo lleva queda fuera, vuelve al
baúl). Si al votar alguien del equipo lo lleva, la opción "quedarse" cambia
por "liberar". Si gana: los aliens se devuelven, quien lleva el martillo
camina solo a cada cápsula de un niño vivo y rompe el vidrio; después los
niños y los agentes van a la cápsula, los niños se suben y los agentes se
quedan delante tapándoles el paso a los aliens que llegan (el final
"liberados"). Todo sale del estado (`fase_liberar`, `fase_ms`, `cola`,
`ruta_ninos`): el espejo de la red dibuja a los niños igual.

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
                           DIALOGO_NINOS, PISTAS_EN_DIALOGO, DIALOGO_MS, DIALOGO_MS_POR_LETRA,
                           DIALOGO_MS_MAX, VOTACION, DESENLACE_MS,
                           FINALES, PISTAS, RADIO_PISTA, SUJETOS, APAGADAS, SE_APAGA, CELULAR_NINO,
                           REGENERAR, BAUL, MARTILLO, LIBERAR)

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
# Si ganó escapar, los aliens se devuelven (a esta velocidad) y los agentes
# caminan solos a la cápsula: termina cuando llegan todos, o a los ESCAPE_MAX_MS.
VEL_RETIRADA = 0.5
ESCAPE_MAX_MS = 16000
ESCAPE_ARRANCA_MS = 700        # (un respiro antes de que echen a andar)
# Cada cuánto suenan los gritos de los que vienen (ms), del primero al último
# (cada grito dura ~6.6 s: así se enciman dos o tres, no más).
GRITOS_CADA_MS = (3600, 1900)
ALARMA_CADA_MS = 1500          # el pitido de la alarma mientras votan
# El pitido de los monitores de las cápsulas mientras hablan (ms entre
# pitidos): normal, mientras uno falla, y después (ya son menos).
MONITOR_CADA_MS = (850, 380, 1150)
PUNTOS_BAUL = 40               # por abrir el baúl de la prisión
RADIO_CAPSULA = 120            # a cuánto de una cápsula se puede regenerar (px del mundo)
# Cuándo suena qué mientras se abre la puerta (ms desde que empieza): se
# destraba (pitidos), suelta la presión (siseo) y se parte en dos.
SONIDOS_ABRIR = ((0, "senal", 0.8), (0, "tecleo", 0.7), (420, "senal", 0.6), (650, "puerta", 1.0),
                 (700, "compuerta", 0.7), (2350, "compuerta", 0.9))


def opcion(clave):
    """Los datos de una opción de la votación (data/historia.VOTACION)."""
    if clave == VOTACION["liberar"]["clave"]:
        return VOTACION["liberar"]
    return next((o for o in VOTACION["opciones"] if o["clave"] == clave), VOTACION["opciones"][0])


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
        self.archivado = False           # (NEILA ya "archivó" a la que se apagó)
        self.celular_visto = False       # alguien revisó el celular: al cerrarlo empieza la votación
        self.fin_lineas = []             # cuándo termina cada línea del diálogo (ms desde que empieza)
        self.dintel = None
        self.a_la_capsula = False        # ganó escapar: caminan solos a la cápsula
        self._origen = {}                # nombre del alien -> dónde estaba al sonar la alarma
        self._pilotos = {}               # puesto -> {"camino", "buscar_ms"} (caminar a la cápsula)
        self.baul = None                 # {"rect", "imagen", "codigo", "abierto", "con_martillo"}
        self.claves = [o["clave"] for o in VOTACION["opciones"]]    # lo que se vota ("liberar" en vez de "quedarse")
        # Ganó liberarlos: "romper" -> "capsula". `rompe`: el puesto de quien
        # rompe; `cola`: las cápsulas que rompe, en orden; `ruta_ninos`: el
        # camino de la sala a la cápsula; `fin_ninos`: cuándo (ms de la fase
        # "capsula") se sube el último.
        self.fase_liberar = None
        self.fase_ms = 0
        self.rompe = None
        self.cola = []
        self.ruta_ninos = []
        self.fin_ninos = 0
        self._golpe_ms = 0
        if geo is None:
            return
        self.puerta, self.pasillos, self.sala, self.capsulas = geo
        self.pasillo = self.pasillos[-1]          # el que entra a la sala
        self.dintel = dintel(mundo)
        self.apagadas = [i for i in APAGADAS if i < len(self.capsulas)]
        # El celular: en el piso, en medio de la sala (entre las dos filas).
        arriba = [c["base"] for c in self.capsulas if c["fila"] == 0]
        abajo = [c["base"] for c in self.capsulas if c["fila"] == 1]
        medio_y = ((max(b.bottom for b in arriba) + min(b.top for b in abajo)) // 2
                   if arriba and abajo else self.sala.centery)
        self.celular = (self.sala.centerx + 20, medio_y + 24)
        for capsula in self.capsulas:
            capsula["golpes"] = 0        # martillazos (rota con MARTILLO["golpes"])
            capsula["temblor"] = 0       # ms del último golpe (tiembla)
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
        self.baul = self._poner_baul(objetos or {})

    # -- Preguntas -----------------------------------------------------------------------

    @property
    def en_secuencia(self):
        """Diálogo, la espera del celular, votación o desenlace: los aliens los
        maneja esta sala (quietos, o viniendo con la alarma)."""
        return self.estado in ("dialogo", "espera", "votacion", "desenlace")

    def bloquea_fin(self):
        """La misión no termina por su cuenta y el reloj de la Feria se detiene
        (en la espera del celular no: si el reloj llega a 0 ahí, empieza la
        votación; Game._actualizar_partida)."""
        return self.activa and self.estado in ("dialogo", "votacion", "desenlace", "fin")

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

    def rota(self, i):
        """¿Ya rompieron el vidrio de la cápsula `i` (el niño está afuera)?"""
        return 0 <= i < len(self.capsulas) and self.capsulas[i].get("golpes", 0) >= MARTILLO["golpes"]

    def vivas(self):
        """Las cápsulas de los niños que siguen vivos."""
        return [i for i in range(len(self.capsulas)) if i not in self.apagadas]

    def todos_libres(self):
        """¿Rompieron las cápsulas de todos los que siguen vivos?"""
        vivas = self.vivas()
        return bool(vivas) and all(self.rota(i) for i in vivas)

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
                self._medir_lineas()
                self._sonar("susurro", 0.8)
                self._decir_linea(0)
                self.monitor_ms = 600
        elif self.estado == "dialogo":
            self._quietos(dt)
            self._monitores(dt, paso)
            linea = next((k for k, fin in enumerate(self.fin_lineas) if self.estado_ms < fin),
                         len(self.fin_lineas))
            if linea != self.linea and linea < len(DIALOGO_NINOS):
                self.linea = linea
                self._decir_linea(linea)
            if not self.fin_lineas or self.estado_ms >= self.fin_lineas[-1]:
                # Hablaron: la votación empieza cuando alguien revise el celular
                # del medio de la sala (Diego, nov 24).
                self._cambiar("espera")
        elif self.estado == "espera":
            self._quietos(dt)
            self._monitores(dt, lambda ms: False)
            leyendo = any(isinstance(j.panel, dict) and j.panel.get("tipo") == "celular_nino"
                          for j in self.juego.jugadores)
            if self.celular_visto and not leyendo:
                self._empezar_votacion()
        elif self.estado == "votacion":
            self._votacion(dt)
        elif self.estado == "desenlace" and self.resultado == "liberar":
            self._liberar(dt)
        elif self.estado == "desenlace" and self.a_la_capsula:
            # Ganó escapar: los aliens se devuelven y ellos van a la cápsula.
            self._retirar_aliens(dt)
            self.cerca = max(0.0, self.cerca - dt / 2500)
            if self.estado_ms >= ESCAPE_ARRANCA_MS and (self._todos_en_capsula()
                                                        or self.estado_ms >= ESCAPE_MAX_MS):
                self._terminar()
        elif self.estado == "desenlace":
            self._mover_adentro(dt)
            self.cerca = 1.0
            self.gritos_ms -= dt
            if self.gritos_ms <= 0:
                self.gritos_ms = 1300
                self._sonar(random.choice(("gritos_aliens_1", "gritos_aliens_2")), 1.0)
            if self.estado_ms >= DESENLACE_MS:
                self._terminar()
        # Mientras pasa lo de los niños, a nadie le salen otros mensajes
        # (NEXUS, avisos): no interrumpen el diálogo ni la votación.
        historia = self.en_secuencia
        for j in self.juego.jugadores:
            if getattr(j, "en_historia", False) != historia:
                j.en_historia = historia
                if historia:
                    j.mensajes_pendientes = []
        for capsula in self.capsulas:
            if capsula.get("temblor", 0) > 0:
                capsula["temblor"] = max(0, capsula["temblor"] - dt)
        self._martillo_perdido()
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
        viva = (i is not None and i < len(self.capsulas) and i not in self.apagadas
                and not self.rota(i))
        if self.fallando_ms > 0 and not viva:
            self.fallando_ms = 0           # (la sacaron a tiempo: ya no se apaga)
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
        if paso(desde + dura + 900) and i in self.apagadas and not self.archivado:
            self.archivado = True
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

    def _texto_linea(self, i):
        n = min(3, self.encontradas)
        return DIALOGO_NINOS[i]["texto"].replace("{pistas}", PISTAS_EN_DIALOGO.get(n, "")).strip()

    @staticmethod
    def duracion_linea(texto):
        """Lo que se ve una línea del diálogo: según lo larga que sea."""
        return int(min(DIALOGO_MS_MAX, max(DIALOGO_MS, 900 + DIALOGO_MS_POR_LETRA * len(texto))))

    def _medir_lineas(self):
        fin, self.fin_lineas = 0, []
        for i in range(len(DIALOGO_NINOS)):
            fin += self.duracion_linea(self._texto_linea(i))
            self.fin_lineas.append(fin)

    def _decir_linea(self, i):
        datos = DIALOGO_NINOS[i]
        quien = self._hablante(datos.get("rol"))
        if quien is None:
            return
        texto = self._texto_linea(i)
        self._decir_a_todos(quien, texto, ms=self.duracion_linea(texto))

    def _decir_a_todos(self, quien, texto, color=COLOR_DIALOGO, ms=None):
        """`quien` lo dice y todos lo ven, con su foto y su nombre (`ms`: lo
        que dura en pantalla, si no el de siempre)."""
        rol = getattr(quien, "rol", "") or ""
        for j in self.juego.jugadores:
            if getattr(j, "eliminado", False):
                continue
            if j is quien:
                j._mostrar_mensaje(texto, color, None)
            else:
                j._mostrar_mensaje(texto, color, [rol, rol.upper()])
            if ms is not None:
                j.mensaje_ms = j.mensaje_total_ms = ms

    def _neila(self, evento):
        decir = getattr(self.juego, "decir", None)
        if decir is not None:
            decir(evento, None, True)

    # -- Votación ------------------------------------------------------------------------------

    def empezar_votacion(self):
        """La alarma y la votación (al cerrar el celular; o si en la Feria se
        acaba el reloj con ellos en la sala, Game._actualizar_partida)."""
        if self.activa and self.estado == "espera":
            self._empezar_votacion()

    def _empezar_votacion(self):
        self._cambiar("votacion")
        self.claves = [o["clave"] for o in VOTACION["opciones"]]
        if self.equipo_con_martillo():
            # Con el martillo, quedarse con ellos es sacarlos (Diego, nov 25).
            self.claves[self.claves.index("quedarse")] = VOTACION["liberar"]["clave"]
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
        self._origen = {}
        for alien in self._aliens():
            self._origen[alien.nombre] = tuple(alien.centro)
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
        opciones = [{"texto": opcion(c)["texto"]} for c in self.claves]
        for i, j in enumerate(self.juego.jugadores):
            if not self.puede_votar(j):
                continue
            panel = j.panel
            if isinstance(panel, dict) and panel.get("tipo") == "votacion":
                continue
            j.panel = {"tipo": "votacion", "filas": [list(range(len(self.claves)))], "opciones": opciones}
            j.cursor = self.claves.index(self.votos[i]) if self.votos[i] in self.claves else 0

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
        n = max(1, len(self.claves))
        mover = {"izquierda": (0, -1), "derecha": (0, 1), "arriba": (-1, 0), "abajo": (1, 0)}
        for accion, (dfila, dcol) in mover.items():
            if jugador.es_tecla(key, accion):
                # Izquierda/derecha como en un mosaico de una fila; arriba/abajo
                # también cambian de opción (con el stick del mando es lo que sale).
                jugador.cursor = (mover_en_mosaico([list(range(n))], jugador.cursor % n, dfila, dcol) if dcol
                                  else (jugador.cursor + dfila) % n)
                self._sonar("menu_mover", 0.4)
                return True
        if jugador.es_tecla(key, "interactuar"):
            self.votar(jugador, self.claves[jugador.cursor % n])
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
            # Gana la más votada; empate: se quedan (liberarlos también es
            # quedarse: si empata, gana esa).
            mas = max(votos.count(c) for c in self.claves)
            empatadas = [c for c in self.claves if votos.count(c) == mas]
            self.resultado = next(c for c in ("liberar", "quedarse", "escapar") + tuple(self.claves)
                                  if c in empatadas)
        for j in self.juego.jugadores:
            if isinstance(j.panel, dict) and j.panel.get("tipo") == "votacion":
                j.cerrar_panel()
        self._cambiar("desenlace")
        self.gritos_ms = 0
        self.a_la_capsula = self.resultado == "escapar"
        if self.resultado == "liberar":
            self._empezar_liberar()
        if self.a_la_capsula or self.resultado == "liberar":
            # Los aliens no llegan: se devuelven por donde vinieron, y los
            # agentes caminan solos a la cápsula (Diego, nov 24).
            self._caminos = {n: {"puntos": None, "destino": o, "pedido_ms": 0}
                             for n, o in self._origen.items()}
            self._pilotos = {}
            self._sonar("puerta", 1.0)
        else:
            self._sonar("susto", 1.0)
        textos = {"escapar": "¡A la cápsula, ya! ¡Corran!",
                  "quedarse": "No los vamos a dejar solos.",
                  "liberar": "¡Rompe el vidrio! ¡Los sacamos de aquí!",
                  "nadie": "..."}
        quien = self._hablante(None)
        if quien is not None:
            self._decir_a_todos(quien, textos[self.resultado],
                                COLOR_ALARMA if self.resultado not in ("escapar", "liberar") else (255, 214, 64))
        if self.resultado == "nadie":
            self._sonar("guardia_esfuerzo_1", 1.0)

    def _terminar(self):
        self._cambiar("fin")
        mision = self.juego.mision
        if mision is None:
            return
        final = {"escapar": "escaparon", "quedarse": "quedarse", "liberar": "liberados",
                 "nadie": "nadie"}[self.resultado or "nadie"]
        mision.final = final
        mision.resultado = "victoria" if FINALES[final]["victoria"] else "derrota"
        mision.motivo_fin = "final_" + final

    # -- Ganó escapar: a la cápsula ---------------------------------------------------------------

    def _caminantes(self):
        return [j for j in self.juego.jugadores
                if not j.preso and not getattr(j, "eliminado", False) and not getattr(j, "desconectado", False)
                and j.puede_moverse]

    def _todos_en_capsula(self):
        mision = self.juego.mision
        if mision is None or mision.capsula is None:
            return True
        zona = mision.capsula.inflate(40, 40)
        caminan = self._caminantes()
        return all(zona.colliderect(j.hitbox) for j in caminan)

    def teclas_escape(self, dt):
        """Si ganó escapar, las teclas de este cuadro (en vez de las de verdad):
        cada agente camina solo hacia la cápsula. None si no toca."""
        if not (self.activa and self.estado == "desenlace"
                and (self.a_la_capsula or self.resultado == "liberar")):
            return None
        from juego import demo, navegacion
        teclas = demo.Teclas()
        mision = self.juego.mision
        if mision is None or mision.capsula is None or self.estado_ms < ESCAPE_ARRANCA_MS:
            return teclas
        nav = navegacion.de_mundo(self.juego.mundo, *demo.TAMANO_NAV)
        metas = self._metas()
        for j in self._caminantes():
            pie = j.hitbox.center
            meta = metas.get(getattr(j, "puesto", id(j)))
            if meta is None:
                continue
            destino, zona = meta
            if zona.colliderect(j.hitbox):
                continue
            datos = self._pilotos.get(getattr(j, "puesto", id(j)))
            if datos is None or datos.get("destino") != destino:
                # El camino, una vez por destino: de la navegación del
                # tamaño de un jugador, así que por ahí cabe.
                camino = nav.camino(pie, destino, parcial=True, sellos=False)
                datos = self._pilotos[getattr(j, "puesto", id(j))] = {"camino": list(camino or []) + [destino],
                                                                     "destino": destino}
            # Camina por el camino (sin chocar: ya es un camino libre); las
            # teclas solo son para que se vea caminando hacia donde va
            # (Game._actualizar_partida no lo deja moverse por su cuenta).
            x, y = pie
            paso = getattr(j.personaje, "velocidad", 3) * dt / (1000 / 60)
            camino = datos["camino"]
            while paso > 0 and camino:
                px, py = camino[0]
                d = math.hypot(px - x, py - y)
                if d <= paso:
                    x, y, paso = px, py, paso - d
                    camino.pop(0)
                else:
                    x, y, paso = x + (px - x) * paso / d, y + (py - y) * paso / d, 0
            dx, dy = x - pie[0], y - pie[1]
            j.personaje.hitbox.center = (int(round(x)), int(round(y)))
            j.personaje.sync_sprite_from_hitbox()
            mayor = max(abs(dx), abs(dy))
            if mayor < 0.01:
                continue
            for accion, activo in (("derecha", dx > 0 and dx >= 0.41 * mayor),
                                   ("izquierda", dx < 0 and -dx >= 0.41 * mayor),
                                   ("abajo", dy > 0 and dy >= 0.41 * mayor),
                                   ("arriba", dy < 0 and -dy >= 0.41 * mayor)):
                if activo:
                    for k in demo._teclas_de(j, accion):
                        teclas[k] = True
        return teclas

    def _metas(self):
        """A dónde camina solo cada agente (puesto -> (punto, zona de llegada))."""
        mision = self.juego.mision
        if self.a_la_capsula:
            zona = mision.capsula.inflate(30, 30)
            return {getattr(j, "puesto", id(j)): (mision.capsula.center, zona) for j in self._caminantes()}
        metas = {}
        if self.fase_liberar == "romper":
            j = self._rompedor()
            i = self._siguiente_rota()
            if j is not None and i is not None:
                punto = self.lugar_golpe(i)
                metas[getattr(j, "puesto", id(j))] = (punto, pygame.Rect(punto[0] - 6, punto[1] - 6, 12, 12))
        elif self.fase_liberar == "capsula":
            for puesto, punto in self._puestos_bloqueo().items():
                metas[puesto] = (punto, pygame.Rect(punto[0] - 6, punto[1] - 6, 12, 12))
        return metas

    def _retirar_aliens(self, dt):
        """Ganó escapar: los aliens se devuelven a donde estaban al sonar la alarma."""
        for alien in self._aliens():
            alien.tiempo_ms = getattr(alien, "tiempo_ms", 0) + dt
            datos = self._caminos.get(alien.nombre)
            if datos is None:
                alien.moviendose = False
                continue
            if datos["puntos"] is None:
                camino = self._buscar(alien, datos, dt)
                if camino is None:
                    alien.moviendose = False
                    continue
                datos["puntos"] = list(camino)
            if not datos["puntos"]:
                alien.moviendose = False
                continue
            self._avanzar(alien, datos, VEL_RETIRADA * dt)

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

    # -- Ganó liberarlos: romper, a la cápsula y tapar el paso ------------------------------------

    def equipo_con_martillo(self):
        """¿Alguien que sigue en la partida lleva el martillo?"""
        return any("martillo" in j.objetos for j in self.juego.jugadores
                   if not getattr(j, "eliminado", False) and not getattr(j, "desconectado", False))

    def _rompedor(self):
        """Quien rompe: el del martillo (si puede caminar) o, si no, otro."""
        caminan = self._caminantes()
        if self.rompe is not None:
            j = next((j for j in caminan if getattr(j, "puesto", None) == self.rompe), None)
            if j is not None:
                return j
        j = next((j for j in caminan if "martillo" in j.objetos), None) or (caminan[0] if caminan else None)
        self.rompe = getattr(j, "puesto", None) if j is not None else None
        return j

    def _siguiente_rota(self):
        return next((i for i in self.cola if not self.rota(i)), None)

    def lugar_golpe(self, i):
        """Dónde se para quien rompe la cápsula `i` (a su izquierda)."""
        base = self.capsulas[i]["base"]
        return (base.left - 24, base.centery)

    def _empezar_liberar(self):
        self.fase_liberar, self.fase_ms = "romper", 0
        self.rompe = None
        j = self._rompedor()
        desde = j.hitbox.center if j is not None else self.sala.center
        # La cola: siempre a la más cercana de las que faltan.
        faltan, self.cola = [i for i in self.vivas() if not self.rota(i)], []
        while faltan:
            i = min(faltan, key=lambda k: math.dist(desde, self.lugar_golpe(k)))
            faltan.remove(i)
            self.cola.append(i)
            desde = self.lugar_golpe(i)
        self._golpe_ms = 0
        self._sonar("menu_ok", 0.6)

    def _liberar(self, dt):
        self.fase_ms += dt
        if self.fase_liberar == "romper":
            self.cerca = max(0.0, self.cerca - dt / 2500)
        if self.fase_liberar == "romper":
            self._retirar_aliens(dt)
            i = self._siguiente_rota()
            j = self._rompedor()
            if i is None:
                self._empezar_capsula()
                return
            if j is None or self.fase_ms >= LIBERAR["romper_max_ms"]:
                # (nadie puede caminar o algo se trabó: se rompen solas)
                for k in self.cola:
                    self.capsulas[k]["golpes"] = MARTILLO["golpes"]
                self._sonar("vidrio_roto", 1.0)
                return
            if math.dist(j.hitbox.center, self.lugar_golpe(i)) > 14:
                self._golpe_ms = 0
                return
            self._golpe_ms += dt
            if self._golpe_ms >= MARTILLO["golpe_ms"]:
                self._golpe_ms = 0
                capsula = self.capsulas[i]
                capsula["golpes"] = capsula.get("golpes", 0) + 1
                capsula["temblor"] = 320
                self._sonar("vidrio_roto" if self.rota(i) else "vidrio_golpe", 1.0 if self.rota(i) else 0.85)
                if self.rota(i):
                    self._golpe_ms = -350          # (un respiro antes de la siguiente)
        elif self.fase_liberar == "capsula":
            self.cerca = min(1.0, self.fase_ms / max(1, self.fin_ninos))
            self._mover_aliens(dt)
            self.quedan_ms = max(1, self.quedan_ms - dt)
            for k in range(len(self.cola)):
                if (self.fase_ms - dt) < self._entra_nino(k) <= self.fase_ms:
                    self._sonar("encajar", 0.6)
            self.gritos_ms -= dt
            if self.gritos_ms <= 0:
                self.gritos_ms = 1700
                self._sonar(random.choice(("gritos_aliens_1", "gritos_aliens_2")), 0.8)
            if self.fase_ms >= self.fin_ninos + LIBERAR["despega_ms"]:
                self._sonar("cohete", 1.0)
                self._terminar()

    def _empezar_capsula(self):
        """Ya están todos afuera: los niños y los agentes, a la cápsula."""
        from juego import demo, navegacion
        self.fase_liberar, self.fase_ms = "capsula", 0
        self._pilotos = {}
        mision = self.juego.mision
        capsula = mision.capsula if mision is not None and mision.capsula is not None else self.puerta
        desde = (self.sala.left + 50, self.celular[1])
        nav = navegacion.de_mundo(self.juego.mundo, *demo.TAMANO_NAV)
        camino = nav.camino(desde, capsula.center, parcial=True, sellos=False) or []
        self.ruta_ninos = [tuple(map(int, p)) for p in [desde] + list(camino) + [capsula.center]]
        self.fin_ninos = max((self._entra_nino(k) for k in range(len(self.cola))), default=0)
        quien = self._rompedor() or self._hablante(None)
        if quien is not None:
            self._decir_a_todos(quien, LIBERAR["sube"], (255, 214, 64))
        # Los aliens vuelven, ahora a la cápsula: llegan a los agentes justo
        # cuando se sube el último niño.
        puestos = list(self._puestos_bloqueo().values()) or [capsula.midbottom]
        self._caminos = {}
        for k, alien in enumerate(sorted(self._aliens(), key=lambda a: a.nombre)):
            x, y = puestos[k % len(puestos)]
            self._caminos[alien.nombre] = {"puntos": None, "destino": (x + (k // len(puestos)) * 30, y + 120),
                                           "pedido_ms": 0}
        self.quedan_ms = max(2500, self.fin_ninos + 600)
        self._sonar("alarma", 0.7)

    def _puestos_bloqueo(self):
        """Dónde se para cada agente: en fila, delante (abajo) de la cápsula."""
        mision = self.juego.mision
        if mision is None or mision.capsula is None:
            return {}
        caminan = sorted(self._caminantes(), key=lambda j: getattr(j, "puesto", 0))
        c = mision.capsula
        n = len(caminan)
        return {getattr(j, "puesto", id(j)): (int(c.centerx + (k - (n - 1) / 2) * 64), c.bottom + 46)
                for k, j in enumerate(caminan)}

    def _camino_nino(self, i):
        x, y = self.lugar_nino(i)
        inicio = self.ruta_ninos[0] if self.ruta_ninos else (x, y)
        return [(x, y), (x, inicio[1])] + list(self.ruta_ninos)

    def _largo(self, puntos):
        return sum(math.dist(a, b) for a, b in zip(puntos, puntos[1:]))

    def _arranca_nino(self, k):
        """Cuándo (ms de la fase "capsula") echa a andar el `k`-ésimo: en fila
        india, cada uno entra a la ruta `sale_ms` después del anterior (si no,
        los que vienen de más lejos alcanzaban a los otros y se enciman)."""
        vel = LIBERAR["vel_nino"]
        entra_ruta, arranca = -LIBERAR["sale_ms"], 0
        for n in range(min(k, len(self.cola) - 1) + 1):
            acercarse = self._largo(self._camino_nino(self.cola[n])[:3]) / vel
            entra_ruta = max(acercarse, entra_ruta + LIBERAR["sale_ms"])
            arranca = entra_ruta - acercarse
        return arranca

    def _entra_nino(self, k):
        """Cuándo (ms de la fase "capsula") se sube a la cápsula el `k`-ésimo."""
        if k >= len(self.cola):
            return 0
        largo = self._largo(self._camino_nino(self.cola[k]))
        return int(self._arranca_nino(k) + largo / LIBERAR["vel_nino"] + LIBERAR["entra_ms"])

    def lugar_nino(self, i):
        """Dónde se para el niño de la cápsula `i` cuando lo sacan (a su derecha)."""
        base = self.capsulas[i]["base"]
        return (base.right + 16, base.bottom - 2)

    def posicion_nino(self, i):
        """(x, y, cuánto se ve 0..1, hacia dónde camina: "east"/"west"/"north"/
        "south", o None quieto) del niño de la cápsula `i`, ya afuera; None si
        sigue adentro o ya se subió. Sale del estado: igual en el espejo."""
        if not self.rota(i) or i in self.apagadas:
            return None
        x, y = self.lugar_nino(i)
        if self.fase_liberar != "capsula" or i not in self.cola or not self.ruta_ninos:
            return (x, y, 1.0, None)
        k = self.cola.index(i)
        t = self.fase_ms - self._arranca_nino(k)
        if t <= 0:
            return (x, y, 1.0, None)
        avanza = t * LIBERAR["vel_nino"]
        puntos = self._camino_nino(i)
        for a, b in zip(puntos, puntos[1:]):
            d = math.dist(a, b)
            if avanza <= d:
                u = avanza / max(1.0, d)
                dx, dy = b[0] - a[0], b[1] - a[1]
                mira = (("east" if dx > 0 else "west") if abs(dx) >= abs(dy)
                        else ("south" if dy > 0 else "north"))
                return (a[0] + dx * u, a[1] + dy * u, 1.0, mira)
            avanza -= d
        # En la cápsula: se va metiendo.
        dentro = avanza / LIBERAR["vel_nino"] / LIBERAR["entra_ms"]
        if dentro >= 1:
            return None
        return (puntos[-1][0], puntos[-1][1], 1 - dentro, "north")

    # -- El baúl de la prisión y el martillo ----------------------------------------------------

    def _poner_baul(self, objetos):
        """El baúl: la caja de seguridad de la decoración que está en la
        prisión (o la primera, si ninguna cae ahí). Su código va al final de
        una nota normal cualquiera (no de las de tachuela). None si no hay."""
        from juego.decoracion import rect_hitbox, rect_imagen
        from juego.salas import sala_en
        mundo = self.juego.mundo
        mision = self.juego.mision
        normales = [n for n in getattr(mision, "notas", ()) if not n.get("de_codigo")]
        if not normales:
            return None
        cajas = []
        for dato in objetos.get("decoracion") or ():
            if not str(dato.get("img", "")).startswith(BAUL["decoracion"]):
                continue
            hitbox = rect_hitbox(dato, mundo.ancho, mundo.alto)
            imagen = rect_imagen(dato, mundo.ancho, mundo.alto)
            if hitbox is None or imagen is None:
                continue
            hitbox, imagen = pygame.Rect(hitbox), pygame.Rect(imagen)
            en = sala_en(getattr(self.juego, "salas", None) or [], hitbox.center)
            cajas.append((en != BAUL["sala"], hitbox, imagen))
        if not cajas:
            return None
        _, hitbox, imagen = min(cajas, key=lambda c: (c[0], c[1].x, c[1].y))
        rng = getattr(mision, "rng", None) or random.Random()
        codigo = "-".join(str(rng.randint(1, 9)) for _ in range(4))
        # Mejor una nota sin el código de una puerta (así no se ve "de paso").
        codigos = [p["codigo"] for p in getattr(mision, "puertas", ())]
        sin_codigo = [n for n in normales if not any(c in n.get("texto", "") for c in codigos)]
        nota = rng.choice(sin_codigo or normales)
        nota["texto"] = (nota.get("texto", "") + " " + BAUL["nota"].replace("{codigo}", codigo)).strip()
        return {"rect": hitbox, "imagen": imagen, "codigo": codigo, "abierto": False, "con_martillo": True}

    def baul_cerca(self, jugador):
        baul = self.baul
        if baul is None or jugador.preso or getattr(jugador, "eliminado", False):
            return False
        return baul["rect"].inflate(BAUL["radio"] * 2, BAUL["radio"] * 2).colliderect(jugador.hitbox)

    def _panel_baul(self, jugador):
        mision = self.juego.mision
        rng = getattr(mision, "rng", None) or random.Random()
        codigo = self.baul["codigo"]
        opciones = {codigo}
        while len(opciones) < 4:
            opciones.add("-".join(str(rng.randint(1, 9)) for _ in range(4)))
        opciones = sorted(opciones)
        jugador.abrir_panel({
            "tipo": "opciones", "accion": "codigo_baul", "codigos": opciones,
            "titulo": BAUL["titulo"], "cuerpo": list(BAUL["cuerpo"]),
            "opciones": [{"texto": c} for c in opciones],
            "pie": (f"[{jugador.pista_mover()}] elegir   "
                    f"[{jugador.nombre_tecla('interactuar')}] marcar"),
        })

    def resolver_baul(self, jugador, indice):
        """El código que marcó en el teclado del baúl (Game, panel "codigo_baul")."""
        codigos = (jugador.panel or {}).get("codigos", [])
        jugador.cerrar_panel()
        if self.baul is None or self.baul["abierto"] or indice >= len(codigos):
            return
        if codigos[indice] == self.baul["codigo"]:
            self.baul["abierto"] = True
            jugador.avisar(BAUL["abierto"], COLOR_PISTA)
            self._sonar("puerta", 0.7)
            self._sonar("acierto", 0.8)
            if hasattr(jugador, "sumar_puntos"):
                jugador.sumar_puntos(PUNTOS_BAUL)
            return
        for alien in getattr(self.juego, "aliens", ()):
            if hasattr(alien, "oir"):
                alien.oir(self.baul["rect"].center)
        jugador.avisar("¡Código equivocado! Suena la alarma.", COLOR_ALARMA)
        self._sonar("alarma", 0.8)
        mision = self.juego.mision
        if mision is not None:
            mision.codigos_fallidos = getattr(mision, "codigos_fallidos", 0) + 1

    def _martillo_perdido(self):
        """Si quien llevaba el martillo quedó fuera (o se desconectó), vuelve al baúl."""
        baul = self.baul
        if baul is None or not baul["abierto"] or baul["con_martillo"]:
            return
        for j in self.juego.jugadores:
            if "martillo" not in j.objetos:
                continue
            if getattr(j, "eliminado", False) or getattr(j, "desconectado", False):
                j.objetos.discard("martillo")
                continue
            return
        baul["con_martillo"] = True
        for j in self.juego.jugadores:
            if not getattr(j, "eliminado", False):
                j.avisar(BAUL["volvio"], COLOR_PISTA)

    def capsula_viva_cerca(self, jugador):
        """La cápsula (de un niño vivo, sin romper) que tiene al lado, o None."""
        if not self._se_puede_revisar(jugador):
            return None
        cerca = [i for i in self.vivas() if not self.rota(i)
                 and math.dist(self.capsulas[i]["base"].center, jugador.hitbox.center) <= RADIO_CAPSULA]
        return min(cerca, key=lambda i: math.dist(self.capsulas[i]["base"].center, jugador.hitbox.center),
                   default=None)

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
        return (self.estado in ("abierta", "dialogo", "espera") and not jugador.preso
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
        if self.baul_cerca(jugador):
            if not self.baul["abierto"]:
                return BAUL["pista"]
            if self.baul["con_martillo"]:
                return BAUL["pista_martillo"]
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
        if self.baul_cerca(jugador):
            if not self.baul["abierto"]:
                self._panel_baul(jugador)
                return True
            if self.baul["con_martillo"]:
                self.baul["con_martillo"] = False
                jugador.objetos.add("martillo")
                jugador.avisar(BAUL["recogido"], COLOR_PISTA)
                self._sonar("recoger", 0.8)
                return True
            jugador.avisar(BAUL["vacio"], (210, 210, 220))
            return True
        if self.celular_cerca(jugador):
            jugador.panel = {"tipo": "celular_nino", "titulo": CELULAR_NINO["contacto"]}
            self.celular_visto = True
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
            if self.capsula_viva_cerca(jugador) is not None and self.estado in ("dialogo", "espera"):
                # Una pista de que se puede (el baúl de la prisión).
                jugador.avisar(MARTILLO["con_martillo"] if "martillo" in jugador.objetos
                               else MARTILLO["sin_martillo"], (210, 210, 220))
                return True
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
