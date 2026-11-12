"""El Guardia de la Bahía y la planta de la Biosfera (idea de Diego).

Le da misión al Resonante y al Biomante:

- El **Guardia** (entidades/guardia.py) protege la cápsula y no sale de su
  sala. Sin quitarlo de en medio no se puede reparar la cápsula ni escapar.
- **Resonante** (cualquier rama: es su habilidad base, Sintonía de señales):
  de cerca, tecla de interactuar → el Guardia se distrae DISTRACCION_MS y se
  va a un rincón a escuchar. Hay que reparar rápido y salir. Recarga.
  Una Emisión que cae en su sala también lo distrae (acciones_rol.py).
- **Biomante**: mantiene la tecla junto a la planta de la Biosfera hasta que
  crece y da una **fruta**, que queda colgando de la planta: cualquiera la
  arranca con la tecla de interactuar (va a su inventario; la puede soltar
  para que otro la lleve). Quien la tenga se la da al Guardia
  (tecla de interactuar cerca de él): se va a su rincón a comer, para siempre.
- Sin Biomante (o si lo eliminan), aparece **abono** (mision.py: en los
  puntos de consumibles al empezar, o donde cayó el Biomante). Con abono
  cualquiera puede hacer crecer la planta (más lento); se gasta al crecer.

La planta y el puesto del Guardia se ponen con el editor de mapa
(herramientas "Planta" y "Guardia"). Un mapa sin ellos no tiene nada de esto.
"""

import math

import pygame

from entidades.guardia import Guardia, DISTRACCION_MS
from misiones.logros import logro

CRECER_BIOMANTE_MS = 4000      # manteniendo la tecla
CRECER_ABONO_MS = 6500         # cualquiera, con abono
RADIO_PLANTA = 80
RADIO_FRUTA = 170              # para darle la fruta (desde el centro del Guardia)
RADIO_SINTONIA = 520           # el Resonante lo distrae desde aquí
RECARGA_SINTONIA_MS = 40000
TAMANO_PLANTA = (56, 56)
PUNTOS_FRUTA = 20
PUNTOS_DISTRAER = 10

COLOR_BIEN = (96, 200, 120)
COLOR_MAL = (245, 130, 120)
COLOR_AVISO = (255, 214, 64)
COLOR_PLANTA = (110, 200, 90)

# Su dibujo (de Anny): Imagenes/Objetos/planta_crece.png, 16 cuadros de 64 px
# (de brote a planta con su fruta naranja), y planta_sin_fruta.png (ya sin
# la fruta). Sin los archivos vuelve el dibujo de formas.
ESCALA_PLANTA = 2
CUADRO_PLANTA = 64
_imagenes_planta = {}


def imagenes_planta():
    """(cuadros de crecer, sin fruta) agrandados, o None si faltan."""
    if "hojas" not in _imagenes_planta:
        import os
        carpeta = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                               "Imagenes", "Objetos")
        resultado = None
        try:
            tira = pygame.image.load(os.path.join(carpeta, "planta_crece.png"))
            sola = pygame.image.load(os.path.join(carpeta, "planta_sin_fruta.png"))
            try:
                tira, sola = tira.convert_alpha(), sola.convert_alpha()
            except pygame.error:
                pass
            lado = CUADRO_PLANTA * ESCALA_PLANTA
            cuadros = [pygame.transform.scale(tira.subsurface((k * CUADRO_PLANTA, 0, CUADRO_PLANTA,
                                                               CUADRO_PLANTA)), (lado, lado))
                       for k in range(tira.get_width() // CUADRO_PLANTA)]
            resultado = (cuadros, pygame.transform.scale(sola, (lado, lado))) if cuadros else None
        except (pygame.error, OSError):
            resultado = None
        _imagenes_planta["hojas"] = resultado
    return _imagenes_planta["hojas"]


def _distancia(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def es_biomante(jugador):
    arbol = getattr(jugador, "arbol", None)
    return (arbol is not None and arbol.tiene("VINCULO") and not getattr(jugador, "eliminado", False))


def es_resonante(jugador):
    arbol = getattr(jugador, "arbol", None)
    return (arbol is not None and arbol.tiene("SINTONIA") and not getattr(jugador, "eliminado", False))


class GuardiaYPlanta:
    def __init__(self, juego, objetos):
        self.juego = juego
        mundo = juego.mundo
        W, H = mundo.ancho, mundo.alto
        self.guardia = None
        self.planta = None
        self.recarga_ms = {}          # Resonante -> ms para volver a usar la Sintonía
        mision = getattr(juego, "mision", None)
        if mision is None or not mision.activa:
            return
        if objetos.get("planta"):
            centro = (int(objetos["planta"][0] * W), int(objetos["planta"][1] * H))
            rect = pygame.Rect(0, 0, *TAMANO_PLANTA)
            rect.center = centro
            # "fruta": la fruta sigue colgando de la planta crecida (hasta que
            # alguien la arranque con la tecla de interactuar).
            self.planta = {"rect": rect, "progreso": 0.0, "crecida": False, "quien": None,
                           "fruta": False}
        if objetos.get("guardia"):
            puesto = (int(objetos["guardia"][0] * W), int(objetos["guardia"][1] * H))
            area = self._sala_de(puesto)
            self.guardia = Guardia(juego, len(juego.aliens) + 1, puesto, area, mision.capsula)
            juego.aliens.append(self.guardia)

    def _sala_de(self, punto):
        """Los rectángulos de la sala donde está su puesto (todos los que se
        llaman igual)."""
        from juego.salas import sala_en
        salas = getattr(self.juego, "salas", ())
        nombre = sala_en(salas, punto)
        if nombre is None:
            return []
        return [r for n, r in salas if n == nombre]

    @property
    def activo(self):
        """¿Todavía protege la cápsula (no le han dado la fruta)?"""
        return self.guardia is not None and not self.guardia.comiendo

    # -- Planta ---------------------------------------------------------------------------

    def _junto_a_planta(self, jugador):
        return (self.planta is not None
                and _distancia(jugador.hitbox.center, self.planta["rect"].center) <= RADIO_PLANTA)

    def _cerca_planta(self, jugador):
        """Junto a la planta que todavía no ha crecido."""
        return self._junto_a_planta(jugador) and not self.planta["crecida"]

    def _fruta_a_mano(self, jugador):
        """Junto a la planta crecida con su fruta colgando."""
        return self._junto_a_planta(jugador) and self.planta["crecida"] and self.planta["fruta"]

    @property
    def fruta_en_planta(self):
        return self.planta is not None and self.planta["crecida"] and self.planta["fruta"]

    def puede_cultivar(self, jugador):
        return es_biomante(jugador) or "abono" in getattr(jugador, "objetos", ())

    def mantener(self, jugador, dt):
        """Tecla de interactuar mantenida junto a la planta."""
        if not self._cerca_planta(jugador) or not self.puede_cultivar(jugador):
            return False
        biomante = es_biomante(jugador)
        total = CRECER_BIOMANTE_MS if biomante else CRECER_ABONO_MS
        p = self.planta
        p["progreso"] = min(1.0, p["progreso"] + dt / total)
        jugador.progreso = ("Haciendo crecer la planta" if biomante else "Echando abono a la planta",
                            p["progreso"])
        if p["progreso"] >= 1.0:
            self._crecer(jugador, biomante)
        return True

    def _crecer(self, jugador, biomante):
        p = self.planta
        p["crecida"], p["quien"], p["fruta"] = True, jugador, True
        if not biomante:
            jugador.objetos.discard("abono")
        # La fruta queda colgando de la planta: hay que arrancarla (tecla de
        # interactuar otra vez). Después la puede llevar quien la arrancó o
        # soltarla (tecla de soltar) para que otro se la lleve al Guardia.
        jugador.sumar_puntos(PUNTOS_FRUTA // 2)
        logro(self.juego, "jardinero", jugador)
        jugador.avisar("¡La planta dio una fruta! Arráncala para llevársela al Guardia.", COLOR_BIEN)
        for j in self.juego.jugadores:
            if j is not jugador:
                j.avisar(f"¡La planta del {jugador.rol} dio una fruta!", COLOR_BIEN)
        self._sonar("encajar", 0.7)
        self._decir("planta", jugador.rol)

    def arrancar_fruta(self, jugador):
        """Arranca la fruta de la planta crecida: va a su inventario."""
        p = self.planta
        p["fruta"] = False
        jugador.objetos.add("fruta")
        jugador.avisar("Tienes la fruta: llévasela al Guardia.", COLOR_BIEN)
        for j in self.juego.jugadores:
            if j is not jugador:
                j.avisar(f"El {jugador.rol} arrancó la fruta.", COLOR_BIEN)
        self._sonar("recoger", 0.8)

    # -- Tecla de interactuar --------------------------------------------------------------

    def interactuar(self, jugador):
        """Devuelve True si se encargó de la tecla."""
        if jugador.preso or getattr(jugador, "eliminado", False):
            return False
        g = self.guardia
        cerca_guardia = g is not None and _distancia(jugador.hitbox.center, g.centro) <= RADIO_FRUTA
        if g is not None and not g.comiendo and cerca_guardia and "fruta" in jugador.objetos:
            jugador.objetos.discard("fruta")
            g.alimentar(jugador)
            jugador.sumar_puntos(PUNTOS_FRUTA)
            for j in self.juego.jugadores:
                j.avisar("¡El Guardia se fue a comer! La Bahía está libre.", COLOR_BIEN)
            self._sonar("encajar", 0.8)
            self._decir("guardia_come", jugador.rol)
            return True
        if (g is not None and not g.comiendo and not g.distraido and es_resonante(jugador)
                and _distancia(jugador.hitbox.center, g.centro) <= RADIO_SINTONIA):
            falta = self.recarga_ms.get(jugador, 0)
            if falta > 0:
                jugador.avisar(f"Tu Sintonía se está recargando: {int(falta // 1000) + 1} s.", COLOR_MAL)
                return True
            g.distraer(DISTRACCION_MS, jugador)
            self.recarga_ms[jugador] = RECARGA_SINTONIA_MS
            jugador.sumar_puntos(PUNTOS_DISTRAER)
            for j in self.juego.jugadores:
                j.avisar(f"¡El Guardia se distrajo! Tienen {DISTRACCION_MS // 1000} s.", COLOR_AVISO)
            self._sonar("senal", 0.8)
            self._decir("guardia_distraido", jugador.rol)
            return True
        if self._fruta_a_mano(jugador):
            self.arrancar_fruta(jugador)
            return True
        if self._cerca_planta(jugador):
            if self.puede_cultivar(jugador):
                jugador.avisar("Mantén la tecla para hacer crecer la planta.", COLOR_AVISO)
            else:
                jugador.avisar("Solo el Biomante la hace crecer... o alguien con abono.", COLOR_MAL)
            return True
        return False

    def pista(self, jugador):
        if jugador.preso or getattr(jugador, "eliminado", False):
            return None
        g = self.guardia
        if g is not None and not g.comiendo:
            d = _distancia(jugador.hitbox.center, g.centro)
            if d <= RADIO_FRUTA and "fruta" in jugador.objetos:
                return "Darle la fruta al Guardia"
            if es_resonante(jugador) and d <= RADIO_SINTONIA and not g.distraido:
                falta = self.recarga_ms.get(jugador, 0)
                if falta > 0:
                    return f"Sintonía recargando ({int(falta // 1000) + 1} s)"
                return "Distraer al Guardia (Sintonía)"
        if self._fruta_a_mano(jugador):
            return "Arrancar la fruta"
        if self._cerca_planta(jugador):
            if es_biomante(jugador):
                return "Mantener: hacer crecer la planta"
            if "abono" in jugador.objetos:
                return "Mantener: echarle abono a la planta"
            return "Planta: la hace crecer el Biomante (o abono)"
        return None

    def actualizar(self, dt):
        for j in list(self.recarga_ms):
            self.recarga_ms[j] = max(0, self.recarga_ms[j] - dt)

    # -- Flecha amarilla (mision.punto_objetivo) -----------------------------------------

    def punto_objetivo(self, jugador):
        """La salida para siempre (planta → fruta → Guardia), según lo que este
        jugador puede hacer o lleva. None si no le toca nada de eso."""
        if not self.activo:
            return None
        mision = self.juego.mision
        g = self.guardia
        if "fruta" in jugador.objetos:
            return g.centro, "Dale la fruta al Guardia"
        fruta = next((c for c in mision.consumibles if c["tipo"] == "fruta" and not c["tomado"]), None)
        if fruta is not None:
            return fruta["rect"].center, "Recoge la fruta"
        if self.fruta_en_planta:
            return self.planta["rect"].center, "Arranca la fruta de la planta"
        if self.planta is not None and not self.planta["crecida"]:
            if self.puede_cultivar(jugador):
                texto = "Haz crecer la planta" if es_biomante(jugador) else "Usa el abono en la planta"
                return self.planta["rect"].center, texto
            biomante = any(es_biomante(j) for j in self.juego.jugadores)
            alguien_con_abono = any("abono" in getattr(j, "objetos", ()) for j in self.juego.jugadores)
            abono = next((c for c in mision.consumibles if c["tipo"] == "abono" and not c["tomado"]), None)
            if not biomante and not alguien_con_abono and abono is not None:
                return abono["rect"].center, "Recoge el abono (para la planta)"
        return None

    def hay_camino_permanente(self):
        """¿Se puede todavía dar de comer al Guardia? (fruta, planta o abono)."""
        if not self.activo:
            return False
        mision = self.juego.mision
        if any(j for j in self.juego.jugadores if "fruta" in getattr(j, "objetos", ())):
            return True
        if any(c["tipo"] in ("fruta", "abono") and not c["tomado"] for c in mision.consumibles):
            return True
        if self.fruta_en_planta:
            return True
        if self.planta is None or self.planta["crecida"]:
            return False
        return any(self.puede_cultivar(j) for j in self.juego.jugadores)

    def punto_distraer(self, jugador):
        """El Resonante: distraer al Guardia (si puede ahora)."""
        g = self.guardia
        if (self.activo and es_resonante(jugador) and not g.distraido
                and self.recarga_ms.get(jugador, 0) <= 0):
            return g.centro, "Distrae al Guardia (Sintonía)"
        return None

    # -- Dibujo ------------------------------------------------------------------------------

    def imagen_planta(self):
        """El cuadro que toca: crece con el progreso; crecida, con su fruta
        hasta que la arranquen y después sin ella."""
        hojas = imagenes_planta()
        p = self.planta
        if hojas is None or p is None:
            return None
        cuadros, sin_fruta = hojas
        if p["crecida"]:
            return cuadros[-1] if p["fruta"] else sin_fruta
        return cuadros[min(len(cuadros) - 2, int(p["progreso"] * (len(cuadros) - 1)))]

    def caja_planta(self, img):
        caja = img.get_rect()
        caja.midbottom = self.planta["rect"].midbottom
        return caja

    def erguidos(self, camara, tiempo_ms):
        """La planta parada en el piso (decoracion.Erguido): se ordena con los
        personajes por su base (no se choca: solo para dibujarla delante o
        detrás de quien pase)."""
        img = self.imagen_planta()
        if img is None:
            return []
        caja = self.caja_planta(img)
        if not caja.inflate(40, 40).colliderect(camara):
            return []
        from juego.decoracion import Erguido
        base = pygame.Rect(0, 0, 40, 10)
        base.midbottom = caja.midbottom
        return [Erguido(base, caja, lambda screen, offset: self._dibujar_sprite_planta(screen, offset, tiempo_ms))]

    def _dibujar_sprite_planta(self, screen, offset, tiempo_ms):
        img = self.imagen_planta()
        caja = self.caja_planta(img).move(-offset[0], -offset[1])
        screen.blit(img, caja)
        if self.fruta_en_planta and (tiempo_ms // 400) % 2 == 0:
            # Su fruta lista: el borde parpadea (como lo que tienes a mano).
            from juego import sprites_objetos
            sprites_objetos.resaltar(screen, img, caja.topleft, (255, 190, 80), 2)

    def dibujar_planta(self, screen, offset, camara, tiempo_ms):
        p = self.planta
        if p is None or not p["rect"].inflate(160, 220).colliderect(camara):
            return
        r = p["rect"].move(-offset[0], -offset[1])
        if imagenes_planta() is not None:
            # Con su dibujo (que va en `erguidos`), aquí solo el brillo en el
            # piso mientras se puede usar: para crecer o para arrancar la fruta.
            if not p["crecida"] or p["fruta"]:
                brillo = 0.5 + 0.5 * math.sin(tiempo_ms / 350)
                color = COLOR_PLANTA if not p["crecida"] else (255, 170, 70)
                halo = pygame.Surface((130, 40), pygame.SRCALPHA)
                pygame.draw.ellipse(halo, (*color, int(40 + 50 * brillo)), halo.get_rect())
                screen.blit(halo, (r.centerx - 65, r.bottom - 26))
            return
        # Maceta.
        maceta = pygame.Rect(0, 0, 40, 24)
        maceta.midbottom = (r.centerx, r.bottom)
        pygame.draw.polygon(screen, (120, 74, 50), [maceta.topleft, maceta.topright,
                                                     (maceta.right - 6, maceta.bottom),
                                                     (maceta.x + 6, maceta.bottom)])
        pygame.draw.rect(screen, (150, 96, 64), (maceta.x - 3, maceta.y - 4, maceta.width + 6, 7),
                         border_radius=2)
        pygame.draw.ellipse(screen, (60, 40, 26), (maceta.x + 3, maceta.y - 3, maceta.width - 6, 6))
        crecida = 1.0 if p["crecida"] else p["progreso"]
        alto = int(10 + crecida * 70)
        base = (r.centerx, maceta.y - 1)
        meneo = math.sin(tiempo_ms / 500) * 3 * (0.3 + crecida)
        tope = (base[0] + meneo, base[1] - alto)
        pygame.draw.line(screen, (70, 140, 60), base, tope, 4)
        hojas = 1 + int(crecida * 5)
        for i in range(hojas):
            t = (i + 1) / (hojas + 1)
            px = base[0] + (tope[0] - base[0]) * t
            py = base[1] + (tope[1] - base[1]) * t
            lado = -1 if i % 2 else 1
            largo = 10 + 14 * crecida
            hoja = pygame.Rect(0, 0, int(largo), int(largo * 0.55))
            if lado > 0:
                hoja.midleft = (px, py)
            else:
                hoja.midright = (px, py)
            pygame.draw.ellipse(screen, COLOR_PLANTA if i % 2 else (90, 176, 72), hoja)
        if p["crecida"]:
            # Flor abierta: ya dio su fruta.
            for k in range(6):
                a = k * math.pi / 3 + tiempo_ms / 2000
                pygame.draw.circle(screen, (255, 160, 190),
                                   (int(tope[0] + math.cos(a) * 8), int(tope[1] + math.sin(a) * 8)), 5)
            pygame.draw.circle(screen, (255, 220, 90), (int(tope[0]), int(tope[1])), 5)
        elif crecida > 0:
            pygame.draw.circle(screen, (150, 220, 120), (int(tope[0]), int(tope[1])), 4)
        if not p["crecida"]:
            # Brillo suave para que se note que se puede usar.
            brillo = 0.5 + 0.5 * math.sin(tiempo_ms / 350)
            halo = pygame.Surface((90, 30), pygame.SRCALPHA)
            pygame.draw.ellipse(halo, (*COLOR_PLANTA, int(40 + 50 * brillo)), halo.get_rect())
            screen.blit(halo, (r.centerx - 45, r.bottom - 18))

    # -- Utilidades ----------------------------------------------------------------------------

    def _sonar(self, nombre, volumen=1.0):
        if hasattr(self.juego, "sonar"):
            self.juego.sonar(nombre, volumen)

    def _decir(self, evento, rol=None):
        if hasattr(self.juego, "decir"):
            self.juego.decir(evento, rol, True)
