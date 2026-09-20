"""Alcalde Digital: el juego. Mundo, personajes y estructuras de datos, juntos.

Se corre con `python main.py`.

Aquí se unieron los dos prototipos que antes iban por separado. En una misma
partida conviven:

- el **mapa** con sus colisiones y una cámara por jugador (mundo.py,
  screens/partida.py),
- el **ABB de publicaciones** (Estructuras/abb_publicaciones.py), que decide
  qué publicación aparece en el tablón y alimenta el aviso de cuántas cadenas
  dudosas están circulando,
- los **árboles de decisión** (Estructuras/arbol_decision.py) de cada
  publicación y de los eventos del candidato,
- los **árboles de diálogo** (Estructuras/arbol_dialogo.py) con los vecinos,
- y el **árbol binario de habilidades** de cada rol
  (Estructuras/arbol_habilidades.py), que es lo que hace que subir de nivel
  cambie las opciones que el jugador ve, no solo un número.

La ronda dura unos minutos y termina en una pantalla de resultados. Cada
jugador juega en su mitad de la pantalla con sus propias teclas, incluidas las
de navegar paneles: la partida es local y los dos comparten teclado.
"""

import math
import os
import random
import sys

import pygame

from config import DEFAULT_FPS
from game_state import GameState
from transition_manager import TransitionManager

from fuentes import construir_fuentes
from ui_components import construir_botones

from mundo import Mundo
from jugador import Jugador, TECLAS_POR_PUESTO, NOMBRE_CONTROLES
from Movimiento.Personaje import (Personaje, CONTROLES_WASD, CONTROLES_FLECHAS,
                                  CONTROLES_NINGUNO)

from Estructuras.abb_publicaciones import ArbolPublicaciones
from Estructuras.arbol_decision import ArbolDecision
from Estructuras.arbol_dialogo import ArbolDialogo

from data.publicaciones_ejemplo import PUBLICACIONES_EJEMPLO
from data.dialogos_ejemplo import DIALOGOS_EJEMPLO
from data.tareas import (ZONAS, ACUSACIONES, PROPUESTAS,
                         opciones_acusacion, opciones_propuesta)
from data.roles import ROLES, PERSONAJE_POR_PUESTO, MINIMO_JUGADORES

from screens.menu import render_menu, OPCIONES_MENU
from screens.partida import render_partida, calcular_viewports
from screens.seleccion import render_cantidad, render_roles, OPCIONES
from screens.arbol_abb import render_arbol_abb
from screens.panel_habilidades import precargar_iconos
from screens.resultados import render_resultados
from screens.ayuda import render_ayuda
from screens.creditos import render_creditos, reiniciar_scroll


ANCHO_VENTANA, ALTO_VENTANA = 960, 600

MAPA = "Colegio"
DURACION_RONDA_S = 300  # cinco minutos, como pide el diseño

# Debajo de esta veracidad una publicación cuenta como dudosa.
UMBRAL_DUDOSA = 40

# Máximo que puede ganar o perder un jugador en una sola tarea.
TOPE_PUNTOS_TAREA = 20

# Controles de movimiento de cada puesto. Los puestos 3 y 4 van sin controles a
# propósito: se dibujan en el mapa y se animan, pero no caminan, porque les toca
# mando y eso todavía no está hecho.
CONTROLES_POR_PUESTO = [CONTROLES_WASD, CONTROLES_FLECHAS,
                        CONTROLES_NINGUNO, CONTROLES_NINGUNO]


def _nombre(tecla):
    """Nombre corto de una tecla, para las pistas de la selección de rol."""
    nombres = {
        pygame.K_w: "W", pygame.K_s: "S", pygame.K_e: "E",
        pygame.K_UP: "↑", pygame.K_DOWN: "↓", pygame.K_RETURN: "ENTER",
        pygame.K_i: "I", pygame.K_k: "K", pygame.K_o: "O",
        pygame.K_t: "T", pygame.K_g: "G", pygame.K_y: "Y",
    }
    return nombres.get(tecla, "?")


class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Alcalde Digital")
        self.pantalla_completa = True
        self.screen = self._crear_ventana()
        self.ancho, self.alto = self.screen.get_size()
        self.clock = pygame.time.Clock()

        self.fuentes = construir_fuentes()
        self.font = self.fuentes["subtitle"]
        self.small_font = self.fuentes["small"]

        self.state = GameState()
        self.transitions = TransitionManager()
        self.current_screen = "menu"
        self.menu_buttons = construir_botones(OPCIONES_MENU, self.ancho, self.alto)
        self.menu_selected = 0
        self.pantalla_anterior = "partida"

        self.mundo = None
        self.jugadores = []
        # Pasos previos a la partida.
        self.cantidad_jugadores = MINIMO_JUGADORES
        self.cantidad_seleccionada = 0   # índice en screens.seleccion.OPCIONES
        self.seleccion_roles = []
        self.zonas = []          # zonas del mapa ya convertidas a píxeles
        self.mostrar_hitboxes = False
        self.credit_scroll = reiniciar_scroll()

        self.arbol_publicaciones = None
        self._arboles_decision = {}
        self._arboles_dialogo = []
        self.tiempo_restante_ms = DURACION_RONDA_S * 1000

        self.running = True

    # -- Ventana ---------------------------------------------------------------

    @staticmethod
    def _tamano_escritorio():
        try:
            tamanos = pygame.display.get_desktop_sizes()
            if tamanos:
                return tamanos[0]
        except (AttributeError, pygame.error):
            pass
        info = pygame.display.Info()
        return info.current_w, info.current_h

    def _crear_ventana(self):
        """Pantalla completa sin bordes, o ventana normal si se alterna con F11.

        Se usa NOFRAME y no pygame.FULLSCREEN a propósito: la pantalla completa
        exclusiva cambia el modo de video del monitor y Windows reacomoda las
        ventanas de las demás aplicaciones, dejándolas descolocadas al salir.
        """
        if self.pantalla_completa:
            return pygame.display.set_mode(self._tamano_escritorio(), pygame.NOFRAME)
        return pygame.display.set_mode((ANCHO_VENTANA, ALTO_VENTANA))

    def _aplicar_tamano(self):
        self.ancho, self.alto = self.screen.get_size()
        self.menu_buttons = construir_botones(OPCIONES_MENU, self.ancho, self.alto)
        self.menu_selected = min(self.menu_selected, len(self.menu_buttons) - 1)

    def alternar_pantalla_completa(self):
        self.pantalla_completa = not self.pantalla_completa
        self.screen = self._crear_ventana()
        self._aplicar_tamano()

    # -- Estructuras de datos ---------------------------------------------------

    def _construir_arboles(self):
        """Arma el ABB de publicaciones y un árbol de decisión por cada una."""
        self.arbol_publicaciones = ArbolPublicaciones()
        self._arboles_decision = {}

        for item in PUBLICACIONES_EJEMPLO:
            veracidad = self._veracidad_de(item)
            # El ABB no admite claves repetidas: si dos publicaciones estiman
            # la misma veracidad se desplaza una para conservar las dos.
            while self.arbol_publicaciones.buscar(veracidad) is not None:
                veracidad += 1
            self.arbol_publicaciones.insertar(veracidad, item["texto"],
                                              item.get("tipo", "publicacion"))
            arbol = ArbolDecision(item)
            self._arboles_decision[veracidad] = arbol.construir_desde_dict(item)

        self._arboles_dialogo = []
        for datos in DIALOGOS_EJEMPLO:
            dialogo = ArbolDialogo()
            dialogo.construir_desde_dict(datos)
            self._arboles_dialogo.append(dialogo)

    @staticmethod
    def _veracidad_de(item):
        """Clave con la que una publicación entra al ABB.

        La declara quien escribe la publicación en data/publicaciones_ejemplo.py,
        mirando su contenido: 0 es una mentira fabricada y 100 algo documentado
        y comprobable. No se deduce de los `efectos`, porque eso sería al revés
        —una publicación esparce desinformación PORQUE es falsa, no al contrario—
        y además dejaba sin poder expresar una noticia cierta pero incendiaria.

        Si a alguna le falta el campo, entra como 50 (ni confiable ni dudosa) y
        se avisa por consola, en vez de inventarle un número.
        """
        veracidad = item.get("veracidad")
        if veracidad is None:
            print(f"[AVISO] La publicación \"{item.get('texto', '')[:50]}...\" no declara "
                  f"veracidad. Entra como 50. Agrégasela en data/publicaciones_ejemplo.py.")
            return 50
        return max(0, min(100, int(veracidad)))

    def publicaciones_dudosas(self):
        """Búsqueda por rango en el ABB: las pendientes bajo el umbral."""
        if self.arbol_publicaciones is None:
            return []
        return self.arbol_publicaciones.buscar_menores_a(UMBRAL_DUDOSA)

    # -- Partida ----------------------------------------------------------------

    # -- Paso 1: cuántos juegan --------------------------------------------------

    def abrir_cantidad(self):
        self.cantidad_seleccionada = 0
        self.transitions.request(self, "cantidad")

    def confirmar_cantidad(self):
        self.cantidad_jugadores = OPCIONES[self.cantidad_seleccionada]
        self.abrir_seleccion_roles()

    # -- Paso 2: qué rol juega cada uno ------------------------------------------

    def abrir_seleccion_roles(self):
        """Prepara el estado de la selección, uno por jugador."""
        self.seleccion_roles = []
        for puesto in range(self.cantidad_jugadores):
            teclas = TECLAS_POR_PUESTO[puesto]
            self.seleccion_roles.append({
                "cursor": puesto % len(ROLES),
                "listo": False,
                "rol": None,
                "personaje": PERSONAJE_POR_PUESTO[puesto],
                "controles": NOMBRE_CONTROLES[puesto],
                "tecla_mover": f"{_nombre(teclas['arriba'][0])}/{_nombre(teclas['abajo'][0])}",
                "tecla_ok": _nombre(teclas["interactuar"][0]),
            })
        self.transitions.request(self, "roles")

    def _tecla_en_seleccion(self, key):
        """Reparte la tecla entre los jugadores que están escogiendo rol."""
        for puesto, estado in enumerate(self.seleccion_roles):
            teclas = TECLAS_POR_PUESTO[puesto]
            if key in teclas["interactuar"]:
                self._confirmar_rol(puesto, estado)
                return
            if estado["listo"]:
                continue
            if key in teclas["arriba"]:
                estado["cursor"] = (estado["cursor"] - 1) % len(ROLES)
                return
            if key in teclas["abajo"]:
                estado["cursor"] = (estado["cursor"] + 1) % len(ROLES)
                return

    def _confirmar_rol(self, puesto, estado):
        if estado["listo"]:
            # Volver a pulsar deshace la elección, por si se equivocó.
            estado["listo"] = False
            estado["rol"] = None
            return
        elegido = ROLES[estado["cursor"]]["nombre"]
        if any(otro["listo"] and otro["rol"] == elegido
               for i, otro in enumerate(self.seleccion_roles) if i != puesto):
            return  # ese rol ya lo tomaron
        estado["listo"] = True
        estado["rol"] = elegido
        if all(e["listo"] for e in self.seleccion_roles):
            self.iniciar_partida()

    # -- Paso 3: la partida ------------------------------------------------------

    def iniciar_partida(self):
        """Carga el mapa, arma los árboles y crea a los jugadores."""
        if self.mundo is None:
            self.mundo = Mundo(MAPA)
        self._construir_arboles()
        self._preparar_zonas()

        self.state = GameState()
        self.tiempo_restante_ms = DURACION_RONDA_S * 1000

        self.jugadores = []
        centro = (self.mundo.ancho // 2, self.mundo.alto // 2)
        for puesto, estado in enumerate(self.seleccion_roles):
            nombre_personaje = estado["personaje"]
            ruta = os.path.join("Imagenes", "Personajes", nombre_personaje)
            personaje = Personaje(0, 0, ruta, velocidad=4,
                                  controles=CONTROLES_POR_PUESTO[puesto])
            personaje.rol = estado["rol"]

            # Se reparten alrededor del centro para que no salgan encimados.
            angulo = puesto * 2 * math.pi / max(1, len(self.seleccion_roles))
            preferido = (centro[0] + math.cos(angulo) * 130,
                         centro[1] + math.sin(angulo) * 90)
            x, y = self.mundo.punto_libre(preferido, personaje.hitbox_w, personaje.hitbox_h)
            personaje.hitbox.topleft = (int(x), int(y))
            personaje.sync_sprite_from_hitbox()

            jugador = Jugador(personaje, estado["rol"], puesto)
            jugador.nombre_personaje = nombre_personaje
            personaje.controles_nombre = jugador.controles_nombre
            self.jugadores.append(jugador)

        # Los iconos de las habilidades se dejan listos aquí, mientras el
        # jugador todavía está viendo cargar, y no la primera vez que abre el
        # panel a mitad de la ronda.
        precargar_iconos([j.rol for j in self.jugadores])

        self._avisar_zonas_inalcanzables()
        self.transitions.request(self, "partida")

    def _avisar_zonas_inalcanzables(self):
        """Avisa por consola si alguna zona quedó encerrada tras una pared.

        Pasó con la "Casa de un vecino", que estaba dentro de un salón cerrado
        del Colegio: se dibujaba en el mapa y no había forma de llegar. Es el
        tipo de error que solo se nota jugando, así que mejor que el juego lo
        diga al arrancar.
        """
        if not self.jugadores or self.mundo is None:
            return
        referencia = self.jugadores[0]
        malas = self.mundo.zonas_inalcanzables(
            self.zonas, referencia.hitbox.topleft,
            referencia.personaje.hitbox_w, referencia.personaje.hitbox_h)
        for zona in malas:
            print(f"[AVISO] La zona '{zona['clave']}' ({zona['nombre']}) no se puede "
                  f"alcanzar caminando. Corrige rx/ry en data/tareas.py.")

    def _preparar_zonas(self):
        """Pasa las zonas de data/tareas.py a rects en píxeles del mapa."""
        self.zonas = []
        for datos in ZONAS:
            radio = int(datos["radio"] * self.mundo.ancho)
            zona = dict(datos)
            zona["rect"] = pygame.Rect(
                int(datos["rx"] * self.mundo.ancho) - radio,
                int(datos["ry"] * self.mundo.alto) - radio,
                radio * 2, radio * 2,
            )
            self.zonas.append(zona)

    def zona_bajo(self, jugador):
        """Zona utilizable por ese jugador sobre la que está parado, o None."""
        for zona in self.zonas:
            if zona["roles"] and jugador.rol not in zona["roles"]:
                continue
            if zona["rect"].colliderect(jugador.hitbox):
                return zona
        return None

    def _actualizar_partida(self, dt=0):
        if not self.jugadores or self.mundo is None:
            return
        teclas = pygame.key.get_pressed()
        dudosas = len(self.publicaciones_dudosas())
        for jugador in self.jugadores:
            jugador.actualizar(teclas, colisiona=self.mundo.colisiona)
            jugador.zona_cerca = self.zona_bajo(jugador)
            jugador.actualizar_mensaje(dt)
            jugador.info = self._info_de_rol(jugador, dudosas)

        self.tiempo_restante_ms -= dt
        if self.tiempo_restante_ms <= 0:
            self.tiempo_restante_ms = 0
            self.terminar_ronda()

    def _info_de_rol(self, jugador, dudosas):
        """Línea extra del HUD según el rol.

        Al ciudadano le importa cuántas cadenas dudosas siguen circulando, y
        ese número sale de `buscar_menores_a`: una búsqueda por rango sobre el
        ABB que poda el subárbol derecho en cuanto una clave alcanza el umbral,
        en vez de recorrer los nodos uno por uno. Se recalcula cada frame y baja
        sola cuando alguien reporta o atiende una publicación.
        """
        if jugador.rol != "Ciudadano":
            return ""
        if dudosas == 0:
            return "Nada dudoso circulando ahora mismo."
        if dudosas == 1:
            return "1 cadena dudosa circulando."
        return f"{dudosas} cadenas dudosas circulando."

    def terminar_ronda(self):
        for jugador in self.jugadores:
            jugador.cerrar_panel()
        self.transitions.request(self, "resultados")

    # -- Abrir zonas ------------------------------------------------------------

    def interactuar(self, jugador):
        """El jugador presionó su tecla de interacción sobre una zona."""
        zona = self.zona_bajo(jugador)
        if zona is None:
            return
        tipo = zona["tipo"]
        if tipo == "verificar":
            self._abrir_verificacion(jugador, zona)
        elif tipo == "reportar":
            self._abrir_reporte(jugador, zona)
        elif tipo == "debate":
            self._abrir_acusacion(jugador, zona)
        elif tipo == "propuesta":
            self._abrir_propuesta(jugador, zona)
        elif tipo == "dialogo":
            self._abrir_dialogo(jugador, zona)

    def _abrir_verificacion(self, jugador, zona):
        """Tablón: saca del ABB la publicación más dudosa y abre su árbol de decisión."""
        pendientes = self.arbol_publicaciones.recorrido_inorden()
        if not pendientes:
            jugador.abrir_panel({
                "tipo": "aviso",
                "titulo": zona["nombre"],
                "cuerpo": ["Ya revisaste todo lo que estaba circulando. Por ahora el tablón está limpio."],
                "pie": f"[{jugador.nombre_tecla('interactuar')}] salir",
            })
            return

        objetivo = pendientes[0]
        raiz = self._arboles_decision.pop(objetivo["veracidad"], None)
        self.arbol_publicaciones.eliminar(objetivo["veracidad"])
        if raiz is None:
            return

        jugador.abrir_panel({
            "tipo": "opciones",
            "accion": "decision",
            "nodo": raiz,
            "titulo": zona["nombre"],
            "cuerpo": [raiz.texto, "", "¿Qué haces con esta publicación?"],
            "opciones": [{"texto": hijo.texto} for hijo in raiz.hijos],
            "pie": (f"[{jugador.nombre_tecla('arriba')}/{jugador.nombre_tecla('abajo')}] elegir   "
                    f"[{jugador.nombre_tecla('interactuar')}] confirmar"),
        })

    def _abrir_reporte(self, jugador, zona):
        """Junta de vecinos: elegir cuál de las publicaciones pendientes es falsa.

        Se muestran solo los textos, nunca la veracidad: la gracia es que el
        jugador tenga que juzgar por el contenido, que es justo lo que el juego
        quiere enseñar.
        """
        pendientes = self.arbol_publicaciones.recorrido_inorden()
        if len(pendientes) < 2:
            jugador.abrir_panel({
                "tipo": "aviso",
                "titulo": zona["nombre"],
                "cuerpo": ["No queda casi nada circulando como para reportar."],
                "pie": f"[{jugador.nombre_tecla('interactuar')}] salir",
            })
            return

        muestra = random.sample(pendientes, min(4, len(pendientes)))
        jugador.abrir_panel({
            "tipo": "opciones",
            "accion": "reporte",
            "muestra": muestra,
            "titulo": zona["nombre"],
            "cuerpo": ["¿Cuál de estas está circulando como falsa?", ""],
            "opciones": [{"texto": item["titulo"]} for item in muestra],
            "pie": (f"[{jugador.nombre_tecla('arriba')}/{jugador.nombre_tecla('abajo')}] elegir   "
                    f"[{jugador.nombre_tecla('interactuar')}] reportar"),
        })

    def _abrir_acusacion(self, jugador, zona):
        """Plaza: una acusación contra el candidato. Aquí pesan DEBATE y sus hijas."""
        evento = random.choice(ACUSACIONES)
        opciones = opciones_acusacion(evento, jugador.arbol)
        jugador.abrir_panel({
            "tipo": "opciones",
            "accion": "acusacion",
            "evento": evento,
            "opciones_datos": opciones,
            "titulo": zona["nombre"],
            "cuerpo": [evento["texto"], "", evento["pista"]],
            "opciones": [{"texto": o["texto"]} for o in opciones],
            "pie": (f"[{jugador.nombre_tecla('arriba')}/{jugador.nombre_tecla('abajo')}] elegir   "
                    f"[{jugador.nombre_tecla('interactuar')}] confirmar"),
        })

    def _abrir_propuesta(self, jugador, zona):
        """Emisora: presentar una propuesta. Aquí pesan PROPUESTA y sus hijas."""
        evento = random.choice(PROPUESTAS)
        opciones = opciones_propuesta(evento, jugador.arbol)
        jugador.abrir_panel({
            "tipo": "opciones",
            "accion": "propuesta",
            "evento": evento,
            "opciones_datos": opciones,
            "titulo": zona["nombre"],
            "cuerpo": [f"Propuesta del día: {evento['texto']}", "", "¿Cómo la presentas?"],
            "opciones": [{"texto": o["texto"]} for o in opciones],
            "pie": (f"[{jugador.nombre_tecla('arriba')}/{jugador.nombre_tecla('abajo')}] elegir   "
                    f"[{jugador.nombre_tecla('interactuar')}] confirmar"),
        })

    def _abrir_dialogo(self, jugador, zona):
        """Casa de un vecino: un árbol de diálogo, que el jugador recorre bajando."""
        if not self._arboles_dialogo:
            return
        dialogo = random.choice(self._arboles_dialogo)
        jugador.abrir_panel(self._panel_dialogo(jugador, dialogo, dialogo.raiz, zona["nombre"]))

    def _panel_dialogo(self, jugador, dialogo, nodo, titulo):
        hijos = nodo.hijos if nodo is not None else []
        if hijos:
            pie = (f"[{jugador.nombre_tecla('arriba')}/{jugador.nombre_tecla('abajo')}] elegir   "
                   f"[{jugador.nombre_tecla('interactuar')}] responder")
        else:
            pie = f"[{jugador.nombre_tecla('interactuar')}] terminar"
        return {
            "tipo": "opciones" if hijos else "aviso",
            "accion": "dialogo",
            "dialogo": dialogo,
            "nodo": nodo,
            "titulo": f"{titulo} · {dialogo.nombre_npc}",
            "cuerpo": [nodo.texto if nodo is not None else ""],
            # En el árbol de diálogo, `respuesta` es lo que dice el jugador para
            # llegar a ese nodo, y `texto` lo que le contesta el NPC.
            "opciones": [{"texto": h.respuesta or h.texto} for h in hijos],
            "pie": pie,
        }

    # -- Resolver la opción elegida ---------------------------------------------

    def confirmar(self, jugador):
        """El jugador confirmó la opción sobre la que tiene el cursor."""
        panel = jugador.panel
        if panel is None:
            return

        tipo = panel.get("tipo")
        if tipo in ("aviso", "resultado"):
            if panel.get("accion") == "dialogo":
                jugador.tareas_hechas += 1
            jugador.cerrar_panel()
            return
        if tipo == "habilidades":
            self._confirmar_habilidad(jugador)
            return

        accion = panel.get("accion")
        indice = jugador.cursor
        if accion == "decision":
            self._resolver_decision(jugador, panel, indice)
        elif accion == "reporte":
            self._resolver_reporte(jugador, panel, indice)
        elif accion in ("acusacion", "propuesta"):
            self._resolver_evento(jugador, panel, indice)
        elif accion == "dialogo":
            self._resolver_dialogo(jugador, panel, indice)

    def _resolver_decision(self, jugador, panel, indice):
        """Baja un nivel por el árbol de decisión de la publicación."""
        nodo = panel["nodo"]
        if indice >= len(nodo.hijos):
            return
        arbol = ArbolDecision(None)
        hijo = nodo.hijos[indice]
        efectos = dict(hijo.efectos or {})
        arbol.aplicar_efectos(hijo, self.state.indicadores)

        if hijo.hijos:
            # Una opción puede tener varias consecuencias; se escoge una al azar
            # para que la misma decisión no dé siempre el mismo resultado.
            consecuencia = random.choice(hijo.hijos)
            arbol.aplicar_efectos(consecuencia, self.state.indicadores)
            for clave, valor in (consecuencia.efectos or {}).items():
                efectos[clave] = efectos.get(clave, 0) + valor
            final = consecuencia
        else:
            final = hijo

        puntos = self._puntos_por_efectos(jugador, efectos)
        jugador.sumar_puntos(puntos)
        jugador.tareas_hechas += 1
        self._panel_resultado(jugador, final.texto, puntos)

    def _resolver_reporte(self, jugador, panel, indice):
        """Reportar una publicación: acierta si de verdad era de las dudosas."""
        muestra = panel["muestra"]
        if indice >= len(muestra):
            return
        elegida = muestra[indice]
        dudosa = elegida["veracidad"] < UMBRAL_DUDOSA

        if dudosa:
            self.arbol_publicaciones.eliminar(elegida["veracidad"])
            self._arboles_decision.pop(elegida["veracidad"], None)
            puntos = 15
            self.state.actualizar_indicador("desinformacion", -8)
            self.state.actualizar_indicador("informacion_verificada", 5)
            texto = "Bien visto: era falsa. La reportaron y dejó de circular."
        else:
            puntos = -8
            self.state.actualizar_indicador("confianza_ciudadana", -4)
            texto = ("Esa era información real. Reportar lo que sí es cierto también "
                     "hace daño.")

        jugador.sumar_puntos(puntos)
        jugador.tareas_hechas += 1
        self._panel_resultado(jugador, texto, puntos)

    def _resolver_evento(self, jugador, panel, indice):
        """Acusación o propuesta del candidato: la opción ya trae puntos y efectos."""
        opciones = panel["opciones_datos"]
        if indice >= len(opciones):
            return
        opcion = opciones[indice]
        for clave, valor in (opcion.get("efectos") or {}).items():
            self.state.actualizar_indicador(clave, valor)
        jugador.sumar_puntos(opcion["puntos"])
        jugador.tareas_hechas += 1
        self._panel_resultado(jugador, opcion["resultado"], opcion["puntos"])

    def _resolver_dialogo(self, jugador, panel, indice):
        """Desciende por el árbol de diálogo. No se puede volver a subir."""
        dialogo, nodo = panel["dialogo"], panel["nodo"]
        # `responder` es el descenso del árbol de diálogo: devuelve el hijo
        # elegido, que ya ES el nodo siguiente (su `texto` es lo que contesta el
        # NPC y sus hijos son las nuevas respuestas). Bajar es jugar, y no se
        # puede volver a subir.
        elegido = dialogo.responder(nodo, indice)
        if elegido is None:
            return
        dialogo.aplicar_efectos(elegido, self.state.indicadores)
        jugador.abrir_panel(self._panel_dialogo(jugador, dialogo, elegido,
                                                panel["titulo"].split(" · ")[0]))

    def _puntos_por_efectos(self, jugador, efectos):
        """Cuántos puntos gana el ciudadano según a dónde movió la ciudad.

        Su objetivo es protegerse de las noticias falsas y no esparcirlas, así
        que se le paga por subir la información verificada y bajar la
        desinformación, y se le cobra por lo contrario. No es un número suelto:
        sale de los mismos efectos que el árbol de decisión aplicó a la ciudad.

        El resultado se acota a +-TOPE_PUNTOS_TAREA porque una publicación con
        efectos grandes podía valer sola treinta puntos, y con eso una sola
        decisión decidía la ronda entera.
        """
        puntos = 0
        puntos += efectos.get("informacion_verificada", 0)
        puntos -= efectos.get("desinformacion", 0)
        puntos += efectos.get("confianza_ciudadana", 0) // 2
        puntos -= efectos.get("conflictos", 0) // 2
        return max(-TOPE_PUNTOS_TAREA, min(TOPE_PUNTOS_TAREA, int(puntos)))

    def _panel_resultado(self, jugador, texto, puntos):
        if puntos > 0:
            resumen, color = f"+{puntos} puntos", (120, 230, 150)
        elif puntos < 0:
            resumen, color = f"{puntos} puntos", (245, 130, 120)
        else:
            resumen, color = "sin puntos", (220, 220, 220)
        jugador.avisar(resumen, color)
        jugador.abrir_panel({
            "tipo": "resultado",
            "titulo": resumen,
            "cuerpo": [texto],
            "pie": f"[{jugador.nombre_tecla('interactuar')}] seguir",
        })

    # -- Habilidades -------------------------------------------------------------

    def alternar_habilidades(self, jugador):
        if jugador.panel is not None and jugador.panel.get("tipo") == "habilidades":
            jugador.cerrar_panel()
        elif jugador.panel is None:
            jugador.abrir_panel({"tipo": "habilidades"})

    def _confirmar_habilidad(self, jugador):
        opciones = jugador.arbol.opciones()
        if not opciones:
            jugador.cerrar_panel()
            return
        indice = min(jugador.cursor, len(opciones) - 1)
        ok, mensaje, costo = jugador.arbol.desbloquear(opciones[indice].clave, jugador.puntos)
        if ok:
            jugador.sumar_puntos(-costo)
            jugador.avisar(mensaje, (255, 214, 64))
            jugador.cursor = 0
        else:
            jugador.avisar(mensaje, (245, 130, 120))

    # -- Entrada ------------------------------------------------------------------

    def _tecla_en_partida(self, key):
        """Reparte la tecla entre los jugadores; cada uno tiene las suyas."""
        for jugador in self.jugadores:
            if jugador.es_tecla(key, "habilidades"):
                self.alternar_habilidades(jugador)
                return
            if not jugador.ocupado:
                if jugador.es_tecla(key, "interactuar"):
                    self.interactuar(jugador)
                    return
                continue

            total = self._total_opciones(jugador)
            if jugador.es_tecla(key, "arriba"):
                jugador.mover_cursor(-1, total)
            elif jugador.es_tecla(key, "abajo"):
                jugador.mover_cursor(1, total)
            elif jugador.es_tecla(key, "interactuar"):
                self.confirmar(jugador)
            return

    def _total_opciones(self, jugador):
        panel = jugador.panel or {}
        if panel.get("tipo") == "habilidades":
            return len(jugador.arbol.opciones())
        return len(panel.get("opciones", []))

    # -- Loop principal -------------------------------------------------------------

    def run(self):
        while self.running:
            dt = self.clock.tick(DEFAULT_FPS)
            self._manejar_eventos()
            if self.current_screen == "partida" and self.transitions.is_idle():
                self._actualizar_partida(dt)
            self.transitions.update(self, dt)
            self._dibujar()
            pygame.display.flip()
        pygame.quit()
        sys.exit()

    def _manejar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.running = False
            elif evento.type == pygame.KEYDOWN:
                self._manejar_tecla(evento.key)
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                self._manejar_click(evento.pos)

    def _manejar_tecla(self, key):
        if key == pygame.K_F11:
            self.alternar_pantalla_completa()
            return
        if self.transitions.active:
            return

        if self.current_screen == "menu":
            if key in (pygame.K_UP, pygame.K_w):
                self.menu_selected = (self.menu_selected - 1) % len(self.menu_buttons)
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.menu_selected = (self.menu_selected + 1) % len(self.menu_buttons)
            elif key == pygame.K_RETURN:
                self._activar_opcion_menu(self.menu_buttons[self.menu_selected].action)
            elif key == pygame.K_ESCAPE:
                self.running = False

        elif self.current_screen == "cantidad":
            if key in (pygame.K_UP, pygame.K_w):
                self.cantidad_seleccionada = (self.cantidad_seleccionada - 1) % len(OPCIONES)
            elif key in (pygame.K_DOWN, pygame.K_s):
                self.cantidad_seleccionada = (self.cantidad_seleccionada + 1) % len(OPCIONES)
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.confirmar_cantidad()
            elif key == pygame.K_ESCAPE:
                self.transitions.request(self, "menu")

        elif self.current_screen == "roles":
            if key == pygame.K_ESCAPE:
                self.transitions.request(self, "cantidad")
            else:
                self._tecla_en_seleccion(key)

        elif self.current_screen == "partida":
            if key == pygame.K_h:
                self.mostrar_hitboxes = not self.mostrar_hitboxes
            elif key == pygame.K_TAB:
                self.pantalla_anterior = "partida"
                self.transitions.request(self, "arbol")
            elif key == pygame.K_ESCAPE:
                self.transitions.request(self, "menu")
            else:
                self._tecla_en_partida(key)

        elif self.current_screen == "arbol":
            if key in (pygame.K_TAB, pygame.K_RETURN, pygame.K_BACKSPACE, pygame.K_ESCAPE):
                self.transitions.request(self, self.pantalla_anterior)

        elif self.current_screen == "resultados":
            if key in (pygame.K_RETURN, pygame.K_ESCAPE):
                self.transitions.request(self, "menu")

        elif self.current_screen in ("ayuda", "creditos"):
            if key in (pygame.K_RETURN, pygame.K_BACKSPACE, pygame.K_ESCAPE):
                self.transitions.request(self, self.pantalla_anterior)

    def _manejar_click(self, pos):
        if self.current_screen != "menu" or self.transitions.active:
            return
        for i, boton in enumerate(self.menu_buttons):
            if boton.contains(pos):
                self.menu_selected = i
                self._activar_opcion_menu(boton.action)
                return

    def _activar_opcion_menu(self, accion):
        if accion == "jugar":
            self.pantalla_anterior = "partida"
            self.abrir_cantidad()
        elif accion == "salir":
            self.running = False
        else:
            # Los créditos siempre arrancan desde el principio: si no, entrar y
            # salir varias veces los retomaba a mitad de camino.
            if accion == "creditos":
                self.credit_scroll = reiniciar_scroll()
            self.pantalla_anterior = "menu"
            self.transitions.request(self, accion)

    # -- Dibujo -----------------------------------------------------------------

    def _dibujar(self):
        if self.current_screen == "menu":
            render_menu(self.screen, self.menu_buttons, self.menu_selected)
        elif self.current_screen == "cantidad":
            render_cantidad(self.screen, self.cantidad_seleccionada)
        elif self.current_screen == "roles":
            viewports = calcular_viewports(self.ancho, self.alto, self.cantidad_jugadores)
            render_roles(self.screen, viewports, self.seleccion_roles)
        elif self.current_screen == "partida":
            render_partida(self.screen, self.mundo, self.jugadores, self.zonas,
                           self.tiempo_restante_ms / 1000.0, self.mostrar_hitboxes)
        elif self.current_screen == "arbol":
            render_arbol_abb(self.screen, self.arbol_publicaciones, self.font, self.small_font)
        elif self.current_screen == "resultados":
            render_resultados(self.screen, self.jugadores, self.state,
                              self.font, self.small_font)
        elif self.current_screen == "ayuda":
            render_ayuda(self.screen, self.small_font)
        elif self.current_screen == "creditos":
            self.credit_scroll = render_creditos(self.screen, self.small_font, self.credit_scroll)

        self.transitions.draw(self.screen)


if __name__ == "__main__":
    Game().run()
