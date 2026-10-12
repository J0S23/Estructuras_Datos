"""La misión de escape: tres fases cortas, celdas y puntos de equipo.

    1. Prisión     encontrar el código en las notas y abrir la puerta.
    2. Sabotaje    apagar las consolas de navegación (mantener la tecla).
    3. Cápsula     llevar 3 piezas a la cápsula y repararla (mantener la tecla).
    4. Huida       los aliens entran en alerta; todos tienen que llegar a la
                   cápsula. Si llegan todos, ganan.

Si atrapan a alguien, va a una **celda** y un compañero tiene que ir a
sacarlo. Si están todos en celdas, o se acaba el tiempo, pierden.

Para que se pueda jugar con 2 o 3 personas:
- sin Tecnomante, aparecen **decodificadores** para las consolas (no se gastan:
  antes eran de un solo uso y con 2 consolas y 1 decodificador en el mapa la
  misión quedaba imposible);
- sin Forjador, aparece un **kit de herramientas** para reparar, y cualquiera
  puede recoger piezas.
El que tiene el rol lo hace más rápido que el que usa el consumible.

Todo lo de la misión se pone en el mapa con el editor (Editores/editor_mapa.py).
Un mapa sin cápsula no tiene misión: se juega como antes, por tiempo.
"""

import math
import random

import pygame

from data.notas import NOTAS, NOTA_CODIGO


PIEZAS_NECESARIAS = 3
SABOTAJE_ROL_S, SABOTAJE_OTROS_S = 3.0, 6.0          # segundos manteniendo la tecla
REPARACION_ROL_S, REPARACION_OTROS_S = 4.0, 8.0
DURACION_MISION_S = 420                               # siete minutos
RADIO_RESCATE = 140
DURACION_REVELAR_PIEZAS_MS = 25000

PUNTOS_PUERTA = 20
PUNTOS_CONSOLA = 15
PUNTOS_PIEZA = 5
PUNTOS_REPARACION = 20
PUNTOS_ESCAPE = 50
PUNTOS_RESCATE = 10

TAMANO_CONSOLA = (70, 50)
TAMANO_CAPSULA = (210, 130)
TAMANO_NOTA = (30, 30)
TAMANO_CONSUMIBLE = (34, 34)

COLOR_BIEN = (96, 200, 120)
COLOR_MAL = (245, 130, 120)
COLOR_AVISO = (255, 214, 64)

NOMBRE_CONSUMIBLE = {"decodificador": "Decodificador", "kit": "Kit de herramientas"}

# Cortos a propósito: van en una sola línea del HUD, y con cuatro jugadores a
# 1280 px cada mitad tiene ~520 px para el texto (unos 50 caracteres).
TEXTO_FASE = {
    "prision": "Busquen el código en las notas y abran la puerta.",
    "sabotaje": "Apaguen las consolas de navegación ({hechas}/{total}).",
    "capsula": "Lleven {faltan} pieza(s) a la cápsula y repárenla.",
    "reparar": "Reparen la cápsula: mantengan la tecla.",
    "huida": "¡Alerta! Todos a la cápsula.",
}


class Equipo:
    """Puntos de todo el equipo: se ganan juntos y se gastan en habilidades."""

    def __init__(self):
        self.puntos = 0      # disponibles para desbloquear habilidades
        self.total = 0       # todo lo que ganaron en la partida

    def sumar(self, cantidad):
        if cantidad > 0:
            self.puntos += cantidad
            self.total += cantidad

    def gastar(self, cantidad):
        self.puntos = max(0, self.puntos - cantidad)


def _rect(centro, tamano):
    rect = pygame.Rect(0, 0, *tamano)
    rect.center = (int(centro[0]), int(centro[1]))
    return rect


class Mision:
    def __init__(self, juego, objetos, aleatorio=None):
        self.juego = juego
        self.rng = aleatorio or random.Random()
        mundo = juego.mundo
        ancho, alto = mundo.ancho, mundo.alto

        def px(p):
            return (int(p[0] * ancho), int(p[1] * alto))

        self.activa = bool(objetos.get("capsula"))
        roles = {j.rol for j in juego.jugadores}
        self.falta_tecnomante = "Tecnomante" not in roles
        self.falta_forjador = "Forjador" not in roles
        self.piezas_para_todos = self.activa and self.falta_forjador
        self.resultado = None            # "victoria" / "derrota"
        self.revelar_piezas_ms = 0

        self.puerta = None
        self.puerta_abierta = True
        self.capsula = None
        self.consolas, self.celdas, self.notas, self.consumibles = [], [], [], []
        self.codigo = "-".join(str(self.rng.randint(1, 9)) for _ in range(3))
        self.piezas_entregadas = 0
        self.reparacion = 0.0
        self.fase = None
        if not self.activa:
            return

        puerta = objetos.get("puerta")
        if puerta:
            self.puerta = _rect(px((puerta["rx"], puerta["ry"])),
                                (max(8, int(puerta["ancho"] * ancho)), max(8, int(puerta["alto"] * alto))))
            self.puerta_abierta = False
            mundo.paredes.append(self.puerta)

        self.capsula = _rect(px(objetos["capsula"]), TAMANO_CAPSULA)
        self.consolas = [{"rect": _rect(px(c), TAMANO_CONSOLA), "progreso": 0.0}
                         for c in objetos.get("consolas", [])]
        self.celdas = [{"punto": px(c), "preso": None} for c in objetos.get("celdas", [])]
        self._crear_notas([px(n) for n in objetos.get("notas", [])])
        self._crear_consumibles([px(c) for c in objetos.get("consumibles", [])])

        if self.puerta is not None:
            self.fase = "prision"
        elif self.consolas:
            self.fase = "sabotaje"
        else:
            self.fase = "capsula"

    # -- Preparación ----------------------------------------------------------------

    def _crear_notas(self, puntos):
        """Reparte los textos y esconde el código en una nota alcanzable."""
        self.notas = [{"rect": _rect(p, TAMANO_NOTA), "titulo": "", "texto": "", "leida_por": set()}
                      for p in puntos]
        if not self.notas:
            return
        alcanzables = list(range(len(self.notas)))
        if self.juego.jugadores and self.puerta is not None:
            desde = self.juego.jugadores[0].hitbox.topleft
            celdas = self.juego.mundo.area_alcanzable(desde)
            alcanzables = [i for i, n in enumerate(self.notas)
                           if any(pygame.Rect(c[0], c[1], 48, 19).colliderect(n["rect"].inflate(40, 40))
                                  for c in celdas)] or alcanzables
        con_codigo = self.rng.choice(alcanzables)
        lore = list(NOTAS)
        for i, nota in enumerate(self.notas):
            if i == con_codigo:
                nota["titulo"] = NOTA_CODIGO["titulo"]
                nota["texto"] = NOTA_CODIGO["texto"].replace("{codigo}", self.codigo)
            else:
                datos = lore.pop(0) if lore else {"titulo": "Nota", "texto": "Está en blanco."}
                nota["titulo"], nota["texto"] = datos["titulo"], datos["texto"]

    def _crear_consumibles(self, puntos):
        """Solo para los roles que faltan: uno por cada punto, repartidos."""
        tipos = []
        if self.falta_tecnomante and self.consolas:
            tipos.append("decodificador")
        if self.falta_forjador:
            tipos.append("kit")
        self.consumibles = []
        if not tipos:
            return
        for i, p in enumerate(puntos):
            self.consumibles.append({"rect": _rect(p, TAMANO_CONSUMIBLE),
                                     "tipo": tipos[i % len(tipos)], "tomado": False})

    # -- Consultas ------------------------------------------------------------------

    def objetivo(self):
        if not self.activa:
            return None
        if self.fase == "sabotaje":
            hechas = sum(c["progreso"] >= 1 for c in self.consolas)
            return TEXTO_FASE["sabotaje"].format(hechas=hechas, total=len(self.consolas))
        if self.fase == "capsula":
            faltan = PIEZAS_NECESARIAS - self.piezas_entregadas
            return TEXTO_FASE["capsula"].format(faltan=faltan) if faltan > 0 else TEXTO_FASE["reparar"]
        return TEXTO_FASE.get(self.fase, "")

    def _cerca(self, jugador, rect, margen=40):
        return rect.inflate(margen * 2, margen * 2).colliderect(jugador.hitbox)

    def _sonar(self, nombre, volumen=1.0):
        if hasattr(self.juego, "sonar"):
            self.juego.sonar(nombre, volumen)

    def _decir(self, evento, rol=None, forzar=False):
        if hasattr(self.juego, "decir"):
            self.juego.decir(evento, rol, forzar)

    def _avisar_todos(self, texto, color=COLOR_AVISO):
        for j in self.juego.jugadores:
            j.avisar(texto, color)

    def pista(self, jugador):
        """Texto de "presiona E para..." según lo que tenga cerca, o None."""
        if not self.activa or jugador.preso:
            return None
        c = jugador.hitbox.center
        for celda in self.celdas:
            if celda["preso"] is not None and math.dist(c, celda["punto"]) <= RADIO_RESCATE:
                return f"Liberar a {celda['preso'].rol}"
        if self.fase == "prision" and self.puerta and self._cerca(jugador, self.puerta, 70):
            return "Teclado de la puerta"
        for cons in self.consumibles:
            if not cons["tomado"] and self._cerca(jugador, cons["rect"], 15):
                return f"Recoger {NOMBRE_CONSUMIBLE[cons['tipo']].lower()}"
        if self.capsula and self.fase == "capsula" and self._cerca(jugador, self.capsula, 10):
            if self.piezas_entregadas < PIEZAS_NECESARIAS:
                return "Dejar piezas en la cápsula" if jugador.piezas else "Cápsula: faltan piezas"
            return "Mantener: reparar la cápsula"
        for nota in self.notas:
            if self._cerca(jugador, nota["rect"], 20):
                return "Leer nota"
        if self.fase == "sabotaje":
            for consola in self.consolas:
                if consola["progreso"] < 1 and self._cerca(jugador, consola["rect"], 20):
                    return "Mantener: apagar consola"
        return None

    # -- Tecla de interactuar --------------------------------------------------------

    def interactuar(self, jugador):
        """Devuelve True si la misión se encargó de la tecla."""
        if not self.activa:
            return False
        if jugador.preso:
            return True
        c = jugador.hitbox.center
        for celda in self.celdas:
            if celda["preso"] is not None and math.dist(c, celda["punto"]) <= RADIO_RESCATE:
                self.liberar(celda, jugador)
                return True
        if self.fase == "prision" and self.puerta and self._cerca(jugador, self.puerta, 70):
            self._panel_codigo(jugador)
            return True
        for cons in self.consumibles:
            if not cons["tomado"] and self._cerca(jugador, cons["rect"], 15):
                cons["tomado"] = True
                jugador.objetos.add(cons["tipo"])
                jugador.avisar(f"Recogiste: {NOMBRE_CONSUMIBLE[cons['tipo']]}", COLOR_BIEN)
                return True
        if self.capsula and self.fase == "capsula" and self._cerca(jugador, self.capsula, 10):
            faltan = PIEZAS_NECESARIAS - self.piezas_entregadas
            if faltan > 0 and jugador.piezas > 0:
                dejar = min(faltan, jugador.piezas)
                jugador.piezas -= dejar
                self.piezas_entregadas += dejar
                jugador.sumar_puntos(PUNTOS_PIEZA * dejar)
                jugador.avisar(f"Piezas en la cápsula: {self.piezas_entregadas}/{PIEZAS_NECESARIAS}",
                               COLOR_BIEN)
            elif faltan > 0:
                quien = "Recójanlas" if self.piezas_para_todos else "El Forjador tiene que recogerlas"
                jugador.avisar(f"Faltan {faltan} pieza(s). {quien}.", COLOR_MAL)
            else:
                jugador.avisar("Mantén la tecla para reparar la cápsula.", COLOR_AVISO)
            return True
        for nota in self.notas:
            if self._cerca(jugador, nota["rect"], 20):
                nota["leida_por"].add(jugador)
                self._sonar("nota", 0.7)
                jugador.abrir_panel({
                    "tipo": "aviso", "titulo": nota["titulo"], "cuerpo": [nota["texto"]],
                    "pie": f"[{jugador.nombre_tecla('interactuar')}] cerrar",
                })
                return True
        if self.fase == "sabotaje":
            for consola in self.consolas:
                if consola["progreso"] < 1 and self._cerca(jugador, consola["rect"], 20):
                    jugador.avisar("Mantén la tecla para apagar la consola.", COLOR_AVISO)
                    return True
        return False

    def _panel_codigo(self, jugador):
        opciones = {self.codigo}
        while len(opciones) < 4:
            opciones.add("-".join(str(self.rng.randint(1, 9)) for _ in range(3)))
        opciones = sorted(opciones)
        jugador.abrir_panel({
            "tipo": "opciones", "accion": "codigo", "codigos": opciones,
            "titulo": "Puerta de la prisión",
            "cuerpo": ["Un teclado pide un código de tres números.",
                       "Si te equivocas, suena la alarma."],
            "opciones": [{"texto": c} for c in opciones],
            "pie": (f"[{jugador.pista_mover()}] elegir   "
                    f"[{jugador.nombre_tecla('interactuar')}] marcar"),
        })

    def resolver_codigo(self, jugador, indice):
        codigos = jugador.panel.get("codigos", [])
        jugador.cerrar_panel()
        if indice >= len(codigos):
            return
        if codigos[indice] == self.codigo:
            self.abrir_puerta(jugador)
        else:
            for alien in self.juego.aliens:
                alien.oir(self.puerta.center)
            jugador.avisar("¡Código equivocado! Suena la alarma.", COLOR_MAL)
            self._sonar("alarma", 0.8)
            self._decir("codigo_malo", jugador.rol, True)

    def abrir_puerta(self, jugador=None):
        if self.puerta is not None:
            # Todas las copias: si una ronda anterior dejó la suya, también.
            paredes = self.juego.mundo.paredes
            paredes[:] = [p for p in paredes if p != self.puerta]
        self.puerta_abierta = True
        if jugador is not None:
            jugador.sumar_puntos(PUNTOS_PUERTA)
        self.fase = "sabotaje" if self.consolas else "capsula"
        self._avisar_todos("¡La puerta de la prisión se abrió!", COLOR_BIEN)
        self._sonar("puerta")
        self._decir("puerta_abierta", None, True)

    # -- Mantener la tecla ------------------------------------------------------------

    def mantener(self, jugador, dt):
        """El jugador mantiene la tecla: avanza consolas o la reparación."""
        jugador.progreso = None
        if not self.activa or jugador.preso:
            return
        paso = dt / 1000
        if self.fase == "sabotaje":
            for consola in self.consolas:
                if consola["progreso"] >= 1 or not self._cerca(jugador, consola["rect"], 20):
                    continue
                if jugador.rol == "Tecnomante":
                    duracion = SABOTAJE_ROL_S
                elif "decodificador" in jugador.objetos:
                    duracion = SABOTAJE_OTROS_S
                else:
                    jugador.avisar("Necesitas al Tecnomante o un decodificador.", COLOR_MAL)
                    return
                consola["progreso"] = min(1.0, consola["progreso"] + paso / duracion)
                jugador.progreso = ("Apagando consola", consola["progreso"])
                if consola["progreso"] >= 1:
                    jugador.sumar_puntos(PUNTOS_CONSOLA)
                    jugador.avisar("Consola apagada.", COLOR_BIEN)
                    self._sonar("consola", 0.8)
                    self._decir("consola", jugador.rol)
                return
        if (self.fase == "capsula" and self.piezas_entregadas >= PIEZAS_NECESARIAS
                and self._cerca(jugador, self.capsula, 10)):
            if jugador.rol == "Forjador":
                duracion = REPARACION_ROL_S
            elif "kit" in jugador.objetos:
                duracion = REPARACION_OTROS_S
            else:
                jugador.avisar("Necesitas al Forjador o un kit de herramientas.", COLOR_MAL)
                return
            self.reparacion = min(1.0, self.reparacion + paso / duracion)
            jugador.progreso = ("Reparando la cápsula", self.reparacion)
            if self.reparacion >= 1:
                jugador.sumar_puntos(PUNTOS_REPARACION)
                self.empezar_huida()

    # -- Celdas -------------------------------------------------------------------------

    def encarcelar(self, jugador):
        """Lo atraparon: a una celda libre, hasta que alguien lo saque."""
        if not self.celdas:
            return False
        libres = [c for c in self.celdas if c["preso"] is None] or self.celdas
        celda = libres[0]
        if celda["preso"] is not None and celda["preso"] is not jugador:
            celda["preso"].preso = None
        celda["preso"] = jugador
        jugador.preso = celda
        jugador.personaje.hitbox.center = celda["punto"]
        jugador.personaje.sync_sprite_from_hitbox()
        for otro in self.juego.jugadores:
            if otro is not jugador:
                otro.avisar(f"¡Encerraron al {jugador.rol}! Vayan a sacarlo.", COLOR_MAL)
        return True

    def liberar(self, celda, rescatador):
        preso = celda["preso"]
        celda["preso"] = None
        if preso is None:
            return
        preso.preso = None
        x, y = celda["punto"]
        libre = self.juego.mundo.punto_libre((x, y + 90), preso.personaje.hitbox_w,
                                             preso.personaje.hitbox_h)
        preso.personaje.hitbox.topleft = (int(libre[0]), int(libre[1]))
        preso.personaje.sync_sprite_from_hitbox()
        preso.invulnerable_ms = 2500
        rescatador.sumar_puntos(PUNTOS_RESCATE)
        if rescatador.rol == "Biomante":
            preso.pulso = min(preso.pulso, 20.0)
            preso.avisar("La Biomante te sacó y te calmó.", COLOR_BIEN)
        else:
            preso.avisar(f"El {rescatador.rol} te sacó de la celda.", COLOR_BIEN)
        rescatador.avisar(f"Liberaste al {preso.rol}. +{PUNTOS_RESCATE}", COLOR_BIEN)
        self._sonar("puerta", 0.6)
        self._decir("rescate", preso.rol)

    # -- Fases --------------------------------------------------------------------------

    def empezar_huida(self):
        self.fase = "huida"
        for alien in self.juego.aliens:
            alien.alerta = True
        self._avisar_todos("¡Cápsula lista! Los aliens están en alerta: ¡todos a la cápsula!",
                           COLOR_MAL)
        self._sonar("alarma")
        self._decir("huida", None, True)

    def actualizar(self, dt):
        if not self.activa or self.resultado is not None:
            return
        self.revelar_piezas_ms = max(0, self.revelar_piezas_ms - dt)
        # Los puestos sin mando todavía no se mueven: no cuentan para ganar ni
        # para perder, o con 3 o 4 jugadores nunca se podría escapar.
        jugadores = [j for j in self.juego.jugadores if j.puede_moverse] or self.juego.jugadores
        if jugadores and all(j.preso for j in jugadores):
            self.resultado = "derrota"
            return
        if self.fase == "sabotaje" and self.consolas and all(c["progreso"] >= 1 for c in self.consolas):
            self.fase = "capsula"
            self._avisar_todos("Navegación apagada. Ahora, a la cápsula.", COLOR_BIEN)
        if self.fase == "huida":
            zona = self.capsula.inflate(60, 60)
            if all(not j.preso and zona.colliderect(j.hitbox) for j in jugadores):
                self.resultado = "victoria"
                for j in jugadores:
                    j.sumar_puntos(PUNTOS_ESCAPE // max(1, len(jugadores)))

    def terminar_por_tiempo(self):
        if self.activa and self.resultado is None:
            self.resultado = "derrota"
