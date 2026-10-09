"""Editor de mapa: pon con el mouse todo lo que va en el mapa, sin tocar código.

    python Editores/editor_mapa.py            (elige el fondo en una lista)
    python Editores/editor_mapa.py Colegio    (abre ese fondo directo)

Qué se pone aquí (las paredes siguen en Editores/hitbox_editor.py):

    1  Inicio de los jugadores     dónde aparecen al empezar
    2  Rutas de aliens             por dónde patrulla cada alien
    3  Escondites                  casilleros, armarios...
    4  Terminales                  las usa el Tecnomante
    5  Paneles dañados             los repara el Forjador
    6  Piezas                      las recoge el Forjador
    7  Zonas                       solo se mueven (su contenido está en data/tareas.py)

Mouse: clic izquierdo pone o arrastra, clic derecho borra, rueda hace zoom y
el clic del medio (o ESPACIO + arrastrar) mueve la vista.

Guarda en Hitboxes/<mapa>_objetos.json, que es lo que lee el juego
(objetos_mapa.py). Con M ese mapa pasa a ser el que usa el juego, y con F5 se
guarda y se abre el juego para probarlo.

Mientras editas, cada cosa se pinta según si está bien:
    verde     bien
    rojo      choca con una pared
    naranja   no se puede llegar caminando desde el inicio
    amarillo  está encima de otra cosa
y los tramos de una ruta que atraviesan una pared salen en rojo.
"""

import copy
import math
import os
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)
os.chdir(RAIZ)

import pygame

import objetos_mapa
from mundo import Mundo, CARPETA_FONDOS


# -- Herramientas ------------------------------------------------------------------------

HERRAMIENTAS = [
    {"clave": "spawn", "nombre": "Inicio de los jugadores", "color": (255, 255, 255)},
    {"clave": "rutas_aliens", "nombre": "Rutas de aliens", "color": (236, 70, 60)},
    {"clave": "escondites", "nombre": "Escondites", "color": (130, 160, 210)},
    {"clave": "terminales", "nombre": "Terminales (Tecnomante)", "color": (150, 120, 255)},
    {"clave": "paneles", "nombre": "Paneles dañados (Forjador)", "color": (255, 120, 80)},
    {"clave": "piezas", "nombre": "Piezas (Forjador)", "color": (255, 170, 50)},
    {"clave": "zonas", "nombre": "Zonas (solo mover)", "color": (96, 188, 118)},
]
TECLAS_HERRAMIENTA = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4,
                      pygame.K_5, pygame.K_6, pygame.K_7]

# Tamaño en el juego (píxeles del mundo) de lo que ocupa cada cosa. Con esto se
# revisa si choca con paredes o se monta sobre otra.
TAMANOS = {
    "spawn": (48, 19),
    "escondites": (70, 40),
    "terminales": (60, 40),
    "paneles": (60, 40),
    "piezas": (34, 34),
}
TAMANO_ALIEN = (34, 20)
NOMBRES_ESCONDITE = ["Casillero", "Armario", "Contenedor", "Ducto"]

AYUDA_HERRAMIENTA = {
    "spawn": ["Clic: los jugadores aparecen aquí.",
              "Clic derecho: volver al centro del mapa."],
    "rutas_aliens": ["Clic: agrega un punto a la ruta elegida.",
                     "Clic en un punto: elegir esa ruta / arrastrarlo.",
                     "Clic derecho: borra un punto.",
                     "N: ruta nueva (= un alien nuevo).",
                     "TAB: siguiente ruta.  SUPR: borra la ruta.",
                     "Un solo punto = guardia quieto."],
    "escondites": ["Clic: pone uno.  Arrastrar: lo mueve.",
                   "Clic derecho: lo borra.",
                   "T sobre uno: cambia el nombre."],
    "terminales": ["Clic: pone una.  Arrastrar: la mueve.",
                   "Clic derecho: la borra."],
    "paneles": ["Clic: pone uno.  Arrastrar: lo mueve.",
                "Clic derecho: lo borra."],
    "piezas": ["Clic: pone una.  Arrastrar: la mueve.",
               "Clic derecho: la borra."],
    "zonas": ["Arrastrar: mueve la zona.",
              "+ / - sobre una: cambia su tamaño.",
              "No se crean ni se borran aquí: su",
              "contenido vive en data/tareas.py."],
}

AYUDA_GENERAL = [
    "1-7 herramienta   Rueda zoom",
    "WASD/flechas o clic medio: mover vista",
    "Ctrl+Z / Ctrl+Y deshacer / rehacer",
    "Ctrl+S o ENTER guardar",
    "M: usar este mapa en el juego",
    "F5: guardar y probar en el juego",
    "V paredes   G zona caminable",
    "R dos veces: herramienta a valores de fábrica",
    "ESC salir",
]

COLOR_FONDO = (18, 19, 30)
COLOR_PANEL = (26, 28, 44)
COLOR_TEXTO = (235, 238, 250)
COLOR_TENUE = (150, 156, 190)
COLOR_TITULO = (255, 214, 64)
COLOR_OK = (96, 210, 120)
COLOR_PARED = (236, 70, 60)
COLOR_LEJOS = (255, 150, 40)
COLOR_ENCIMA = (255, 214, 64)
COLOR_MURO = (90, 180, 255)

ANCHO_PANEL = 330
ZOOMS = [0.3, 0.4, 0.5, 0.65, 0.8, 1.0, 1.25, 1.6, 2.0]
RADIO_TOQUE = 22          # en píxeles de pantalla: qué tan cerca hay que hacer clic


def _fuente(px):
    try:
        from fuentes import fuente_de_tamano
        return fuente_de_tamano(px)
    except Exception:
        return pygame.font.SysFont("consolas", px)


class EditorMapa:
    def __init__(self, mapa, ruta_salida=None, tamano=(1366, 768)):
        self.mapa = mapa
        self.ruta_salida = ruta_salida
        if pygame.display.get_surface() is None:
            pygame.display.set_mode(tamano, pygame.RESIZABLE)
        self.screen = pygame.display.get_surface()
        pygame.display.set_caption(f"Editor de mapa - {mapa}")

        self.mundo = Mundo(mapa)
        ruta_lectura = ruta_salida if ruta_salida and os.path.isfile(ruta_salida) else None
        if ruta_salida and ruta_lectura is None:
            self.datos = objetos_mapa.normalizar(objetos_mapa.por_defecto())
        else:
            self.datos = objetos_mapa.normalizar(objetos_mapa.cargar(mapa, ruta=ruta_lectura))

        self.herramienta = 1
        self.ruta_elegida = 0
        self.arrastre = None          # lo que se está arrastrando
        self.antes = None             # copia de los datos al empezar un clic
        self.paneando = False
        self.deshacer, self.rehacer = [], []
        self.sucio = False
        self.confirmar = None         # acción que espera un segundo toque (R, ESC)

        self.mostrar_paredes = True
        self.mostrar_caminable = False
        self.mensaje, self.mensaje_ms = "", 0

        self.f = _fuente(15)
        self.f_chica = _fuente(13)
        self.f_titulo = _fuente(19)

        self._escalados = {}
        self._caminable = None
        self._caminable_desde = None
        self.estado = {}
        self.problemas = []

        self.zoom_i = 2
        self._ajustar_zoom_inicial()
        self.validar()

    # -- Vista -----------------------------------------------------------------------------

    @property
    def zoom(self):
        return ZOOMS[self.zoom_i]

    @property
    def area_mapa(self):
        ancho, alto = self.screen.get_size()
        return pygame.Rect(0, 0, ancho - ANCHO_PANEL, alto)

    def _ajustar_zoom_inicial(self):
        area = self.area_mapa
        cabe = min(area.width / self.mundo.ancho, area.height / self.mundo.alto)
        self.zoom_i = max(i for i, z in enumerate(ZOOMS) if z <= max(cabe, ZOOMS[0]))
        self.cam = [(self.mundo.ancho * self.zoom - area.width) / 2,
                    (self.mundo.alto * self.zoom - area.height) / 2]

    def a_mundo(self, pos):
        return ((pos[0] + self.cam[0]) / self.zoom, (pos[1] + self.cam[1]) / self.zoom)

    def a_pantalla(self, p):
        return (int(p[0] * self.zoom - self.cam[0]), int(p[1] * self.zoom - self.cam[1]))

    def norm(self, p):
        return [p[0] / self.mundo.ancho, p[1] / self.mundo.alto]

    def px(self, rx, ry):
        return (rx * self.mundo.ancho, ry * self.mundo.alto)

    def cambiar_zoom(self, delta, alrededor=None):
        nuevo = max(0, min(len(ZOOMS) - 1, self.zoom_i + delta))
        if nuevo == self.zoom_i:
            return
        alrededor = alrededor or self.area_mapa.center
        punto = self.a_mundo(alrededor)
        self.zoom_i = nuevo
        self.cam = [punto[0] * self.zoom - alrededor[0], punto[1] * self.zoom - alrededor[1]]

    def _mapa_escalado(self):
        if self.zoom not in self._escalados:
            tam = (int(self.mundo.ancho * self.zoom), int(self.mundo.alto * self.zoom))
            self._escalados[self.zoom] = pygame.transform.scale(self.mundo.imagen, tam)
        return self._escalados[self.zoom]

    # -- Acceso a los objetos -----------------------------------------------------------

    @property
    def clave(self):
        return HERRAMIENTAS[self.herramienta]["clave"]

    def posicion(self, clave, obj):
        """Punto del mundo (píxeles) de un objeto de esa parte."""
        if clave in ("piezas",):
            return self.px(*obj)
        return self.px(obj["rx"], obj["ry"])

    def rect_de(self, clave, punto):
        ancho, alto = TAMANOS.get(clave, (30, 30))
        rect = pygame.Rect(0, 0, ancho, alto)
        rect.center = (int(punto[0]), int(punto[1]))
        return rect

    def buscar(self, clave, pos_pantalla):
        """Lo que hay bajo el mouse en esa parte, o None."""
        p = self.a_mundo(pos_pantalla)
        radio = RADIO_TOQUE / self.zoom
        mejor, mejor_d = None, radio
        if clave == "spawn":
            if self.datos.get("spawn"):
                d = math.dist(p, self.px(*self.datos["spawn"]))
                if d <= radio:
                    return ("spawn",)
            return None
        if clave == "rutas_aliens":
            for i, ruta in enumerate(self.datos["rutas_aliens"]):
                for j, punto in enumerate(ruta):
                    d = math.dist(p, self.px(*punto))
                    if d <= mejor_d:
                        mejor, mejor_d = ("punto", i, j), d
            return mejor
        if clave == "zonas":
            for zclave, zona in self.datos["zonas"].items():
                centro = self.px(zona["rx"], zona["ry"])
                d = math.dist(p, centro)
                alcance = max(radio, zona["radio"] * self.mundo.ancho)
                if d <= alcance and (mejor is None or d < mejor_d):
                    mejor, mejor_d = ("zona", zclave), d
            return mejor
        for i, obj in enumerate(self.datos[clave]):
            rect = self.rect_de(clave, self.posicion(clave, obj))
            d = math.dist(p, rect.center)
            if rect.inflate(radio, radio).collidepoint(p) and (mejor is None or d < mejor_d):
                mejor, mejor_d = ("obj", i), d
        return mejor

    def mover_a(self, cosa, p):
        rx, ry = self.norm(p)
        rx, ry = min(1, max(0, rx)), min(1, max(0, ry))
        if cosa[0] == "spawn":
            self.datos["spawn"] = [rx, ry]
        elif cosa[0] == "punto":
            self.datos["rutas_aliens"][cosa[1]][cosa[2]] = [rx, ry]
        elif cosa[0] == "zona":
            self.datos["zonas"][cosa[1]]["rx"], self.datos["zonas"][cosa[1]]["ry"] = rx, ry
        elif cosa[0] == "obj":
            obj = self.datos[self.clave][cosa[1]]
            if self.clave == "piezas":
                obj[0], obj[1] = rx, ry
            else:
                obj["rx"], obj["ry"] = rx, ry

    # -- Edición ---------------------------------------------------------------------------

    def _empezar_cambio(self):
        self.antes = copy.deepcopy(self.datos)

    def _terminar_cambio(self):
        if self.antes is not None and self.antes != self.datos:
            self.deshacer.append(self.antes)
            self.rehacer.clear()
            self.sucio = True
            self.validar()
        self.antes = None

    def clic_izquierdo(self, pos):
        if not self.area_mapa.collidepoint(pos):
            return
        self._empezar_cambio()
        clave = self.clave
        cosa = self.buscar(clave, pos)
        p = self.a_mundo(pos)
        if cosa is not None:
            if cosa[0] == "punto":
                self.ruta_elegida = cosa[1]
            self.arrastre = cosa
            return
        rx, ry = self.norm(p)
        if not (0 <= rx <= 1 and 0 <= ry <= 1):
            return
        if clave == "spawn":
            self.datos["spawn"] = [rx, ry]
            self.arrastre = ("spawn",)
        elif clave == "rutas_aliens":
            rutas = self.datos["rutas_aliens"]
            if not rutas:
                rutas.append([])
                self.ruta_elegida = 0
            self.ruta_elegida = min(self.ruta_elegida, len(rutas) - 1)
            rutas[self.ruta_elegida].append([rx, ry])
            self.arrastre = ("punto", self.ruta_elegida, len(rutas[self.ruta_elegida]) - 1)
        elif clave == "zonas":
            self.avisar("Las zonas no se crean aquí: arrastra una existente.")
        elif clave == "piezas":
            self.datos["piezas"].append([rx, ry])
            self.arrastre = ("obj", len(self.datos["piezas"]) - 1)
        else:
            nombre = {"escondites": "Casillero", "terminales": "Terminal",
                      "paneles": "Panel dañado"}[clave]
            self.datos[clave].append({"clave": "", "nombre": nombre, "rx": rx, "ry": ry})
            self.arrastre = ("obj", len(self.datos[clave]) - 1)

    def arrastrar(self, pos):
        if self.arrastre is not None:
            self.mover_a(self.arrastre, self.a_mundo(pos))

    def soltar(self):
        self.arrastre = None
        if self.antes is not None:
            objetos_mapa.normalizar(self.datos)
        self._terminar_cambio()

    def clic_derecho(self, pos):
        if not self.area_mapa.collidepoint(pos):
            return
        self._empezar_cambio()
        clave = self.clave
        cosa = self.buscar(clave, pos)
        if clave == "spawn":
            self.datos["spawn"] = None
            self.avisar("Inicio de vuelta al centro del mapa.")
        elif cosa is None:
            pass
        elif cosa[0] == "punto":
            ruta = self.datos["rutas_aliens"][cosa[1]]
            del ruta[cosa[2]]
            if not ruta:
                del self.datos["rutas_aliens"][cosa[1]]
                self.ruta_elegida = max(0, min(self.ruta_elegida, len(self.datos["rutas_aliens"]) - 1))
        elif cosa[0] == "obj":
            del self.datos[clave][cosa[1]]
        elif cosa[0] == "zona":
            self.avisar("Las zonas no se borran aquí (su contenido está en data/tareas.py).")
        self._terminar_cambio()

    def nueva_ruta(self):
        self._empezar_cambio()
        self.datos["rutas_aliens"].append([])
        self.ruta_elegida = len(self.datos["rutas_aliens"]) - 1
        self.avisar(f"Ruta {self.ruta_elegida + 1}: haz clic para poner sus puntos.")
        self._terminar_cambio()

    def borrar_ruta(self):
        rutas = self.datos["rutas_aliens"]
        if not rutas:
            return
        self._empezar_cambio()
        del rutas[min(self.ruta_elegida, len(rutas) - 1)]
        self.ruta_elegida = max(0, min(self.ruta_elegida, len(rutas) - 1))
        self._terminar_cambio()

    def cambiar_nombre(self, pos):
        cosa = self.buscar("escondites", pos)
        if self.clave != "escondites" or cosa is None:
            return
        self._empezar_cambio()
        obj = self.datos["escondites"][cosa[1]]
        i = NOMBRES_ESCONDITE.index(obj["nombre"]) if obj["nombre"] in NOMBRES_ESCONDITE else -1
        obj["nombre"] = NOMBRES_ESCONDITE[(i + 1) % len(NOMBRES_ESCONDITE)]
        self._terminar_cambio()

    def cambiar_radio(self, pos, delta):
        cosa = self.buscar("zonas", pos)
        if self.clave != "zonas" or cosa is None:
            return
        self._empezar_cambio()
        zona = self.datos["zonas"][cosa[1]]
        zona["radio"] = round(min(0.2, max(0.01, zona["radio"] + delta)), 4)
        self._terminar_cambio()

    def restaurar_herramienta(self):
        self._empezar_cambio()
        fabrica = objetos_mapa.normalizar(objetos_mapa.por_defecto())
        self.datos[self.clave] = copy.deepcopy(fabrica[self.clave])
        self.ruta_elegida = 0
        self._terminar_cambio()
        self.avisar(f"{HERRAMIENTAS[self.herramienta]['nombre']}: valores de fábrica.")

    def deshacer_uno(self):
        if self.deshacer:
            self.rehacer.append(copy.deepcopy(self.datos))
            self.datos = self.deshacer.pop()
            self.sucio = True
            self.validar()

    def rehacer_uno(self):
        if self.rehacer:
            self.deshacer.append(copy.deepcopy(self.datos))
            self.datos = self.rehacer.pop()
            self.sucio = True
            self.validar()

    def guardar(self):
        ruta = objetos_mapa.guardar(self.mapa, self.datos, self.ruta_salida)
        self.sucio = False
        if self.problemas:
            self.avisar(f"Guardado, pero con {len(self.problemas)} problema(s): revisa la lista.")
        else:
            self.avisar(f"Guardado en {os.path.relpath(ruta, RAIZ)}")
        return ruta

    def usar_en_juego(self):
        objetos_mapa.fijar_mapa_activo(self.mapa)
        self.avisar(f"El juego ahora usa el mapa {self.mapa}.")

    def probar(self):
        self.guardar()
        self.usar_en_juego()
        subprocess.Popen([sys.executable, os.path.join(RAIZ, "main.py")], cwd=RAIZ)
        self.avisar("Abriendo el juego con este mapa...")

    def avisar(self, texto, ms=3500):
        self.mensaje, self.mensaje_ms = texto, ms

    # -- Validación -----------------------------------------------------------------------

    def _celdas_caminables(self):
        spawn = self.datos.get("spawn")
        desde = self.px(*spawn) if spawn else (self.mundo.ancho / 2, self.mundo.alto / 2)
        if self._caminable_desde != desde:
            inicio = self.mundo.punto_libre((int(desde[0]), int(desde[1])), 48, 19)
            self._caminable = self.mundo.area_alcanzable(inicio)
            self._caminable_desde = desde
        return self._caminable

    def _alcanzable(self, rect):
        celdas = self._celdas_caminables()
        for cx in range(rect.left // 16 * 16 - 48, rect.right + 16, 16):
            for cy in range(rect.top // 16 * 16 - 32, rect.bottom + 16, 16):
                if (cx, cy) in celdas and pygame.Rect(cx, cy, 48, 19).colliderect(rect):
                    return True
        return False

    def validar(self):
        """Revisa todo y deja en self.estado el color de cada cosa."""
        self.estado, self.problemas = {}, []
        nombres = {"escondites": "Escondite", "terminales": "Terminal",
                   "paneles": "Panel", "piezas": "Pieza"}
        ocupados = []   # (rect, id) de todo lo que ocupa espacio

        for zclave, zona in self.datos["zonas"].items():
            r = int(zona["radio"] * self.mundo.ancho)
            rect = pygame.Rect(0, 0, 2 * r, 2 * r)
            rect.center = tuple(map(int, self.px(zona["rx"], zona["ry"])))
            ocupados.append((rect, ("zonas", zclave)))
            if not self._alcanzable(rect):
                self.estado[("zonas", zclave)] = "lejos"
                self.problemas.append(f"Zona {zclave}: no se llega caminando")

        for clave in ("escondites", "terminales", "paneles", "piezas"):
            for i, obj in enumerate(self.datos[clave]):
                rect = self.rect_de(clave, self.posicion(clave, obj))
                ocupados.append((rect, (clave, i)))

        for rect, ident in ocupados:
            if ident[0] == "zonas":
                continue
            clave, i = ident
            nombre = nombres[clave]
            if self.mundo.colisiona(rect):
                self.estado[ident] = "pared"
                self.problemas.append(f"{nombre} {i + 1}: choca con una pared")
            elif not self._alcanzable(rect):
                self.estado[ident] = "lejos"
                self.problemas.append(f"{nombre} {i + 1}: no se llega caminando")
            elif any(r2.colliderect(rect) for r2, otro in ocupados if otro != ident):
                self.estado[ident] = "encima"
                self.problemas.append(f"{nombre} {i + 1}: está encima de otra cosa")

        if self.datos.get("spawn"):
            rect = self.rect_de("spawn", self.px(*self.datos["spawn"]))
            if self.mundo.colisiona(rect):
                self.estado[("spawn",)] = "pared"
                self.problemas.append("Inicio: choca con una pared")

        self.tramos_malos = {}
        for i, ruta in enumerate(self.datos["rutas_aliens"]):
            puntos = [self.px(*p) for p in ruta]
            if not puntos:
                self.problemas.append(f"Ruta {i + 1}: no tiene puntos")
                continue
            for j, p in enumerate(puntos):
                rect = pygame.Rect(0, 0, *TAMANO_ALIEN)
                rect.center = (int(p[0]), int(p[1]))
                if self.mundo.colisiona(rect):
                    self.estado[("punto", i, j)] = "pared"
                    self.problemas.append(f"Ruta {i + 1}, punto {j + 1}: en una pared")
            malos = self.mundo.tramos_bloqueados(puntos, *TAMANO_ALIEN) if len(puntos) > 1 else []
            self.tramos_malos[i] = set(malos)
            for a, b in malos:
                self.problemas.append(f"Ruta {i + 1}: el tramo {a + 1}-{b + 1} cruza una pared")
        return self.problemas

    # -- Entrada ---------------------------------------------------------------------------

    def tecla(self, key, mods=0):
        ctrl = mods & pygame.KMOD_CTRL
        confirmar, self.confirmar = self.confirmar, None
        if key in TECLAS_HERRAMIENTA:
            self.herramienta = TECLAS_HERRAMIENTA.index(key)
            self.arrastre = None
        elif ctrl and key == pygame.K_z:
            self.deshacer_uno()
        elif ctrl and key == pygame.K_y:
            self.rehacer_uno()
        elif (ctrl and key == pygame.K_s) or key in (pygame.K_RETURN, pygame.K_KP_ENTER):
            self.guardar()
        elif key == pygame.K_m:
            self.usar_en_juego()
        elif key == pygame.K_F5:
            self.probar()
        elif key == pygame.K_v:
            self.mostrar_paredes = not self.mostrar_paredes
        elif key == pygame.K_g:
            self.mostrar_caminable = not self.mostrar_caminable
        elif key == pygame.K_n and self.clave == "rutas_aliens":
            self.nueva_ruta()
        elif key == pygame.K_TAB and self.datos["rutas_aliens"]:
            self.ruta_elegida = (self.ruta_elegida + 1) % len(self.datos["rutas_aliens"])
        elif key == pygame.K_DELETE and self.clave == "rutas_aliens":
            self.borrar_ruta()
        elif key == pygame.K_t:
            self.cambiar_nombre(pygame.mouse.get_pos())
        elif key in (pygame.K_PLUS, pygame.K_KP_PLUS, pygame.K_EQUALS):
            self.cambiar_radio(pygame.mouse.get_pos(), 0.005)
        elif key in (pygame.K_MINUS, pygame.K_KP_MINUS):
            self.cambiar_radio(pygame.mouse.get_pos(), -0.005)
        elif key == pygame.K_r:
            if confirmar == "r":
                self.restaurar_herramienta()
            else:
                self.confirmar = "r"
                self.avisar("R otra vez para volver esta herramienta a los valores de fábrica.")
        elif key == pygame.K_ESCAPE:
            if not self.sucio or confirmar == "esc":
                return "salir"
            self.confirmar = "esc"
            self.avisar("Hay cambios sin guardar: ESC otra vez para salir igual.")
        return None

    def actualizar(self, dt):
        self.mensaje_ms = max(0, self.mensaje_ms - dt)
        teclas = pygame.key.get_pressed()
        paso = 900 * dt / 1000
        if teclas[pygame.K_a] or teclas[pygame.K_LEFT]:
            self.cam[0] -= paso
        if teclas[pygame.K_d] or teclas[pygame.K_RIGHT]:
            self.cam[0] += paso
        if teclas[pygame.K_w] or teclas[pygame.K_UP]:
            self.cam[1] -= paso
        if teclas[pygame.K_s] or teclas[pygame.K_DOWN]:
            if not (pygame.key.get_mods() & pygame.KMOD_CTRL):
                self.cam[1] += paso

    def evento(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN:
            espacio = pygame.key.get_pressed()[pygame.K_SPACE]
            if ev.button == 2 or (ev.button == 1 and espacio):
                self.paneando = True
            elif ev.button == 1:
                self.clic_izquierdo(ev.pos)
            elif ev.button == 3:
                self.clic_derecho(ev.pos)
            elif ev.button == 4:
                self.cambiar_zoom(+1, ev.pos)
            elif ev.button == 5:
                self.cambiar_zoom(-1, ev.pos)
        elif ev.type == pygame.MOUSEBUTTONUP:
            if ev.button in (1, 2):
                if self.paneando:
                    self.paneando = False
                else:
                    self.soltar()
        elif ev.type == pygame.MOUSEMOTION:
            if self.paneando:
                self.cam[0] -= ev.rel[0]
                self.cam[1] -= ev.rel[1]
            else:
                self.arrastrar(ev.pos)
        elif ev.type == pygame.MOUSEWHEEL:
            self.cambiar_zoom(1 if ev.y > 0 else -1, pygame.mouse.get_pos())
        elif ev.type == pygame.KEYDOWN:
            return self.tecla(ev.key, ev.mod)
        return None

    # -- Dibujo ------------------------------------------------------------------------------

    def _color(self, ident, base):
        return {"pared": COLOR_PARED, "lejos": COLOR_LEJOS,
                "encima": COLOR_ENCIMA}.get(self.estado.get(ident), base)

    def _etiqueta(self, texto, centro, color, arriba=True):
        img = self.f_chica.render(texto, True, color)
        sombra = self.f_chica.render(texto, True, (0, 0, 0))
        x = centro[0] - img.get_width() // 2
        y = centro[1] - img.get_height() - 4 if arriba else centro[1] + 4
        self.screen.blit(sombra, (x + 1, y + 1))
        self.screen.blit(img, (x, y))

    def dibujar(self):
        s = self.screen
        s.fill(COLOR_FONDO)
        area = self.area_mapa
        s.set_clip(area)
        s.blit(self._mapa_escalado(), (-self.cam[0], -self.cam[1]))

        if self.mostrar_paredes:
            capa = pygame.Surface(area.size, pygame.SRCALPHA)
            for pared in self.mundo.paredes:
                x, y = self.a_pantalla(pared.topleft)
                r = pygame.Rect(x, y, max(1, int(pared.width * self.zoom)),
                                max(1, int(pared.height * self.zoom)))
                pygame.draw.rect(capa, (*COLOR_MURO, 50), r)
                pygame.draw.rect(capa, (*COLOR_MURO, 160), r, 1)
            s.blit(capa, (0, 0))
        if self.mostrar_caminable:
            for cx, cy in self._celdas_caminables():
                pygame.draw.circle(s, (120, 255, 140), self.a_pantalla((cx + 24, cy + 10)), 2)

        actual = self.clave
        apagado = lambda clave: clave != actual

        # Zonas.
        for zclave, zona in self.datos["zonas"].items():
            centro = self.a_pantalla(self.px(zona["rx"], zona["ry"]))
            radio = max(3, int(zona["radio"] * self.mundo.ancho * self.zoom))
            color = self._color(("zonas", zclave), HERRAMIENTAS[6]["color"])
            pygame.draw.circle(s, color, centro, radio, 3 if not apagado("zonas") else 1)
            self._etiqueta(zclave, (centro[0], centro[1] - radio), color)

        # Escondites, terminales, paneles y piezas.
        for k, herr in enumerate(HERRAMIENTAS[2:6], start=2):
            clave = herr["clave"]
            for i, obj in enumerate(self.datos[clave]):
                rect = self.rect_de(clave, self.posicion(clave, obj))
                x, y = self.a_pantalla(rect.topleft)
                r = pygame.Rect(x, y, max(4, int(rect.width * self.zoom)),
                                max(4, int(rect.height * self.zoom)))
                color = self._color((clave, i), herr["color"])
                relleno = pygame.Surface(r.size, pygame.SRCALPHA)
                relleno.fill((*herr["color"], 110 if not apagado(clave) else 50))
                s.blit(relleno, r.topleft)
                pygame.draw.rect(s, color if self.estado.get((clave, i)) else herr["color"], r,
                                 3 if self.estado.get((clave, i)) else (2 if not apagado(clave) else 1))
                if not apagado(clave):
                    texto = obj["nombre"] if isinstance(obj, dict) else "Pieza"
                    self._etiqueta(f"{texto} {i + 1}", r.midtop, color)

        # Rutas de los aliens.
        for i, ruta in enumerate(self.datos["rutas_aliens"]):
            elegida = (i == self.ruta_elegida and actual == "rutas_aliens")
            puntos = [self.a_pantalla(self.px(*p)) for p in ruta]
            base = HERRAMIENTAS[1]["color"] if (elegida or actual != "rutas_aliens") else (150, 90, 90)
            n = len(puntos)
            tramos = [(j, (j + 1) % n) for j in range(n)] if n > 2 else ([(0, 1)] if n == 2 else [])
            for a, b in tramos:
                malo = (a, b) in self.tramos_malos.get(i, set()) or (b, a) in self.tramos_malos.get(i, set())
                pygame.draw.line(s, COLOR_PARED if malo else base, puntos[a], puntos[b],
                                 4 if (elegida or malo) else 2)
            for j, p in enumerate(puntos):
                color = self._color(("punto", i, j), base)
                pygame.draw.circle(s, color, p, 9 if elegida else 6)
                pygame.draw.circle(s, (20, 10, 10), p, 9 if elegida else 6, 2)
                if elegida or j == 0:
                    self._etiqueta(f"A{i + 1}" if j == 0 else str(j + 1), p, color)

        # Inicio de los jugadores.
        spawn = self.datos.get("spawn")
        if spawn:
            p = self.a_pantalla(self.px(*spawn))
            color = self._color(("spawn",), (255, 255, 255))
            pygame.draw.circle(s, color, p, 12, 3)
            pygame.draw.circle(s, color, p, 4)
            self._etiqueta("Inicio", (p[0], p[1] - 12), color)

        # Lo que hay bajo el mouse.
        cosa = self.buscar(actual, pygame.mouse.get_pos()) if area.collidepoint(pygame.mouse.get_pos()) else None
        if cosa is not None:
            pygame.draw.circle(s, (255, 255, 255), pygame.mouse.get_pos(), RADIO_TOQUE, 1)

        s.set_clip(None)
        self._dibujar_panel()

    def _dibujar_panel(self):
        s = self.screen
        ancho, alto = s.get_size()
        panel = pygame.Rect(ancho - ANCHO_PANEL, 0, ANCHO_PANEL, alto)
        pygame.draw.rect(s, COLOR_PANEL, panel)
        x, y = panel.x + 14, 12

        def linea(texto, color=COLOR_TEXTO, f=None, extra=4):
            nonlocal y
            f = f or self.f
            s.blit(f.render(texto, True, color), (x, y))
            y += f.get_linesize() + extra

        linea(f"Editor de mapa · {self.mapa}", COLOR_TITULO, self.f_titulo)
        activo = objetos_mapa.mapa_activo() == self.mapa
        linea("Es el mapa del juego" if activo else "No es el mapa del juego (M)",
              COLOR_OK if activo else COLOR_LEJOS, self.f_chica)
        linea("Sin guardar" if self.sucio else "Guardado", COLOR_LEJOS if self.sucio else COLOR_OK,
              self.f_chica, 10)

        for i, herr in enumerate(HERRAMIENTAS):
            clave = herr["clave"]
            if clave == "spawn":
                cuenta = "puesto" if self.datos.get("spawn") else "centro"
            elif clave == "zonas":
                cuenta = str(len(self.datos["zonas"]))
            else:
                cuenta = str(len(self.datos[clave]))
            elegida = i == self.herramienta
            if elegida:
                pygame.draw.rect(s, (52, 57, 92), (panel.x + 6, y - 2, ANCHO_PANEL - 12,
                                                  self.f.get_linesize() + 4))
            pygame.draw.rect(s, herr["color"], (x, y + 4, 10, 10))
            texto = f"{i + 1}  {herr['nombre']}  ({cuenta})"
            s.blit(self.f.render(texto, True, COLOR_TITULO if elegida else COLOR_TEXTO), (x + 16, y))
            y += self.f.get_linesize() + 4
        y += 6

        if self.clave == "rutas_aliens" and self.datos["rutas_aliens"]:
            linea(f"Ruta elegida: {self.ruta_elegida + 1} de {len(self.datos['rutas_aliens'])}",
                  COLOR_TITULO, self.f_chica)
        for texto in AYUDA_HERRAMIENTA[self.clave]:
            linea(texto, COLOR_TENUE, self.f_chica, 2)
        y += 8

        linea(f"Problemas ({len(self.problemas)})", COLOR_PARED if self.problemas else COLOR_OK, self.f)
        for texto in self.problemas[:8]:
            linea("· " + texto, COLOR_LEJOS, self.f_chica, 1)
        if len(self.problemas) > 8:
            linea(f"  y {len(self.problemas) - 8} más", COLOR_LEJOS, self.f_chica, 1)
        y += 8

        y = max(y, alto - len(AYUDA_GENERAL) * (self.f_chica.get_linesize() + 2) - 16)
        for texto in AYUDA_GENERAL:
            linea(texto, COLOR_TENUE, self.f_chica, 2)

        if self.mensaje_ms > 0:
            img = self.f.render(self.mensaje, True, COLOR_TITULO)
            caja = img.get_rect(midbottom=(self.area_mapa.centerx, alto - 16)).inflate(20, 12)
            pygame.draw.rect(s, (14, 15, 28), caja)
            pygame.draw.rect(s, COLOR_TITULO, caja, 2)
            s.blit(img, img.get_rect(center=caja.center))


# -- Programa -------------------------------------------------------------------------------

def elegir_mapa():
    if len(sys.argv) > 1:
        nombre = os.path.splitext(os.path.basename(sys.argv[1]))[0]
        return nombre
    sys.path.insert(0, os.path.join(RAIZ, "Editores"))
    from hitbox_editor import choose_image_gui
    ruta = choose_image_gui(CARPETA_FONDOS, "Elegir mapa - Editor de mapa  (doble clic o Enter)")
    if ruta is None:
        return None
    return os.path.splitext(os.path.basename(ruta))[0]


def main():
    pygame.init()
    info = pygame.display.Info()
    tam = (min(1600, info.current_w - 60), min(950, info.current_h - 80))
    pygame.display.set_mode(tam, pygame.RESIZABLE)
    mapa = elegir_mapa()
    if not mapa:
        pygame.quit()
        return
    pygame.display.set_mode(tam, pygame.RESIZABLE)
    editor = EditorMapa(mapa)
    reloj = pygame.time.Clock()
    while True:
        dt = reloj.tick(60)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                # Cerrar la ventana es como ESC: si hay cambios, pide confirmar.
                ev = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE, mod=0)
            if ev.type == pygame.VIDEORESIZE:
                editor.screen = pygame.display.get_surface()
            if editor.evento(ev) == "salir":
                pygame.quit()
                return
        editor.actualizar(dt)
        editor.dibujar()
        pygame.display.flip()


if __name__ == "__main__":
    main()
