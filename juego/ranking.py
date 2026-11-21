"""El ranking de la feria: los equipos que jugaron en este computador.

Solo con el modo feria (juego/feria.py). Al terminar una partida, el equipo
pone su nombre (hasta MAX_LETRAS; Diego: "que la gente pueda poner nombres
largos, no solo 3 letras"): con el teclado se escribe (Borrar borra), y con
el mando, como en las máquinas de arcade: arriba/abajo cambian la letra,
izquierda/derecha pasan a la otra (a la derecha de la última, una nueva);
aceptar confirma. Queda en la tabla con su puntaje (`puntaje`). La tabla sale en Menú >
Ranking y en la pantalla de atracción (juego/demo.py).

Se guarda en Guardado/ranking.json (fuera de git, como los logros). Las
pruebas (sin ventana) no escriben en el de verdad. Si no se puede leer o
escribir, el juego sigue igual.
"""

import json
import os
import time

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA = os.path.join(_RAIZ, "Guardado", "ranking.json")
_DE_VERDAD = RUTA         # (las pruebas cambian RUTA por un archivo temporal)
ALFABETO = "ABCDEFGHIJKLMNÑOPQRSTUVWXYZ0123456789 "   # (con el mando; el espacio, al final)
MAX_LETRAS = 16
# Lo que se puede escribir con el teclado, además de ALFABETO (en minúsculas también).
OTRAS = "ÁÉÍÓÚÜ-_.!¡¿?'&#+"
BONO_ESCAPE = 100          # escapar vale más que cualquier cosa de la partida
SEGUNDOS_POR_PUNTO = 5     # en la Feria: 1 punto por cada 5 s que les sobraron
GUARDAR_MAX = 300
MOSTRAR = 10


def puntaje(juego):
    """(puntaje, detalle) de la partida que acaba de terminar: los puntos del
    equipo + BONO_ESCAPE si escaparon + lo que les sobró del reloj (Feria)."""
    equipo = getattr(juego, "equipo", None)
    puntos = int(getattr(equipo, "total", 0) or 0)
    mision = getattr(juego, "mision", None)
    escaparon = mision is not None and getattr(mision, "resultado", None) == "victoria"
    total = puntos
    sobro = 0
    if escaparon:
        total += BONO_ESCAPE
        restante = getattr(juego, "tiempo_restante_ms", None)
        if restante:
            sobro = int(restante / 1000) // SEGUNDOS_POR_PUNTO
            total += sobro
    return total, {"puntos": puntos, "escaparon": escaparon, "sobro": sobro}


def entrada_de(juego, nombre):
    """Lo que se guarda de la partida (con las iniciales `nombre`)."""
    total, detalle = puntaje(juego)
    dificultad = getattr(juego, "dificultad", None)
    return {"nombre": nombre, "puntaje": total, "puntos": detalle["puntos"],
            "escaparon": detalle["escaparon"],
            "tiempo_s": int(getattr(juego, "tiempo_jugado_ms", 0) / 1000),
            "jugadores": len(getattr(juego, "jugadores", ())),
            "roles": [j.rol for j in getattr(juego, "jugadores", ())],
            "dificultad": getattr(dificultad, "clave", None),
            "feria": bool(getattr(juego, "modo_feria", False)),
            "fecha": time.strftime("%Y-%m-%d %H:%M")}


def ordenar(entradas):
    """De mejor a peor: más puntaje y, empatados, menos tiempo."""
    return sorted(entradas, key=lambda e: (-int(e.get("puntaje", 0)), int(e.get("tiempo_s", 0))))


def cargar(ruta=None):
    try:
        with open(ruta or RUTA, "r", encoding="utf-8") as fh:
            datos = json.load(fh)
        return [e for e in datos.get("equipos", []) if isinstance(e, dict)]
    except (OSError, ValueError, AttributeError, TypeError):
        return []


def agregar(entrada, ruta=None):
    """Anota al equipo. Devuelve (su puesto empezando en 1, cuántos hay)."""
    ruta = ruta or RUTA
    entradas = cargar(ruta)
    entrada = dict(entrada, id=f"{time.time():.6f}")
    entradas.append(entrada)
    entradas = ordenar(entradas)
    puesto = next(i for i, e in enumerate(entradas) if e is entrada) + 1
    if ruta == _DE_VERDAD and os.environ.get("SDL_VIDEODRIVER") == "dummy":
        return puesto, len(entradas)          # (las pruebas no tocan el de verdad)
    try:
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        temporal = ruta + ".tmp"
        with open(temporal, "w", encoding="utf-8") as fh:
            json.dump({"equipos": entradas[:GUARDAR_MAX]}, fh, ensure_ascii=False, indent=1)
        os.replace(temporal, ruta)        # (si se corta la luz a mitad, el de antes sigue entero)
    except OSError:
        pass
    agregar.ultima = entrada
    return puesto, len(entradas)


agregar.ultima = None


def permitida(letra):
    """¿Se puede escribir esta letra en el nombre del equipo?"""
    return len(letra) == 1 and (letra.upper() in ALFABETO or letra.upper() in OTRAS)


class Iniciales:
    """El nombre del equipo que se está poniendo en los resultados (hasta
    MAX_LETRAS). `pos` es la letra escogida (con el mando cambia con
    arriba/abajo); `len(letras)` es el hueco de una nueva al final."""

    def __init__(self, juego):
        self.letras = []
        self.pos = 0
        self.hecho = False
        self.saltado = False
        self.puesto = None
        self.total = None
        self.entrada = None
        self.puntaje, self.detalle = puntaje(juego)

    @property
    def nombre(self):
        return " ".join("".join(self.letras).split())     # (sin espacios de sobra)

    def escribir(self, letra):
        """Una letra del teclado: va donde está el cursor y el cursor avanza."""
        if self.hecho or not permitida(letra) or len(self.letras) >= MAX_LETRAS:
            return
        if letra == " " and (self.pos == 0 or self.letras[self.pos - 1:self.pos] == [" "]):
            return                      # (sin espacios al principio ni dos seguidos)
        self.letras.insert(self.pos, letra)
        self.pos += 1

    def borrar(self):
        if self.hecho:
            return
        if self.pos > 0:
            del self.letras[self.pos - 1]
            self.pos -= 1
        elif self.letras:
            del self.letras[0]

    def tecla(self, accion, juego, ruta=None):
        """"arriba", "abajo", "izquierda", "derecha", "ok", "borrar" o "saltar"."""
        if self.hecho:
            return
        if accion in ("arriba", "abajo"):
            paso = 1 if accion == "arriba" else -1
            if self.pos >= len(self.letras):
                if len(self.letras) >= MAX_LETRAS:
                    return
                # Una letra nueva: con arriba la A, con abajo la última.
                self.letras.append(ALFABETO[0] if paso > 0 else ALFABETO[-2])
                return
            actual = self.letras[self.pos].upper()
            i = ALFABETO.index(actual) if actual in ALFABETO else -1
            self.letras[self.pos] = ALFABETO[(i + paso) % len(ALFABETO)]
        elif accion == "izquierda":
            self.pos = max(0, self.pos - 1)
        elif accion == "derecha":
            self.pos = min(len(self.letras), MAX_LETRAS - 1, self.pos + 1)
        elif accion == "borrar":
            self.borrar()
        elif accion == "ok":
            if not self.nombre:
                return                  # (sin nombre no se anota: Esc es "no anotarse")
            self.entrada = entrada_de(juego, self.nombre)
            self.puesto, self.total = agregar(self.entrada, ruta)
            self.hecho = True
        elif accion == "saltar":
            self.hecho = self.saltado = True

    def teclear(self, key, texto, juego, teclas, ruta=None):
        """Una tecla del teclado o del mando (`teclas`: key -> acción, las de
        app.TECLAS_INICIALES) y lo que escribe (`texto`, el unicode del evento)."""
        accion = teclas.get(key)
        if accion is not None:
            self.tecla(accion, juego, ruta)
        elif texto and texto.isprintable():
            self.escribir(texto)
