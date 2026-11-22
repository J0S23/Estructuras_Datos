"""El modo feria: Menú > Opciones > "Modo feria: Sí/No" (guardado en
Guardado/opciones.json, como los efectos visuales; para la feria se deja
prendido y queda así aunque se cierre el juego).

La profe pidió que en la feria se pueda jugar y entender en máximo 7 minutos
mientras el equipo cuenta la historia. La misión entera (la puerta con código,
tres consolas, tres piezas, el Guardia con la fruta, la puerta para dos y el
caso del Cambiaformas) es mucho para alguien que llega sin saber nada. Con el
modo feria se juega lo mismo, recortado (`FERIA` en data/feria.py), en la
dificultad que se escoja (los aliens, las vidas y la fuga son los de ella):

- `recortar_objetos`: antes de armar nada, se quita del mapa lo que no va:
  las otras puertas con código (solo queda la de la salida), las consolas
  de más (se dejan las más cercanas caminando: 1 con 2 jugadores, 2 con 3, 3
  con 4; `recortar_consolas`, después de sellar las salas). Lo demás (el
  Guardia y la planta, las puertas para dos, las pruebas del caso) se puede
  quitar con `FERIA`, pero desde nov 21-22 va como en el juego normal.
- `aplicar`: con la partida ya armada, la cápsula pide `FERIA["piezas"]`, el
  primer rumor de NEXUS sale pronto (los planos piden la confianza de la
  dificultad: NEXUS es el centro del juego), las
  cuentas falsas no ganan seguidores (`AJUSTES_FERIA`) y arranca el reloj.
- `actualizar`: el reloj (en el HUD, donde va la sala). Avisa cuando quedan 2
  minutos y 1, y al llegar a 0 la partida termina (`motivo_fin = "tiempo"`)
  para que pase el siguiente grupo.

Además, solo con el modo feria: el equipo pone sus iniciales en el ranking al
terminar (juego/ranking.py) y, con el menú quieto, el juego se juega solo
(juego/demo.py). Cada partida guarda si va en modo feria al empezar
(`Game.modo_feria`): cambiarlo en el menú no toca la que ya va. El servidor de
red no lo lee (sin ventana no se leen las opciones).
"""

import json
import math
import os

from data.feria import FERIA

COLOR_AVISO = (255, 214, 64)
ACTIVO = False


def cargar_preferencia():
    """Lee "feria" de Guardado/opciones.json. Las pruebas (sin ventana) no la leen."""
    global ACTIVO
    if os.environ.get("SDL_VIDEODRIVER") == "dummy":
        return
    from juego.efectos import RUTA_OPCIONES
    try:
        with open(RUTA_OPCIONES, encoding="utf-8") as f:
            ACTIVO = bool(json.load(f).get("feria", False))
    except (OSError, ValueError, AttributeError):
        pass


def cambiar(activo):
    """Prende o apaga el modo feria y lo guarda (Menú > Opciones)."""
    global ACTIVO
    ACTIVO = bool(activo)
    if os.environ.get("SDL_VIDEODRIVER") == "dummy":
        return
    from juego.efectos import RUTA_OPCIONES
    try:
        datos = {}
        if os.path.exists(RUTA_OPCIONES):
            with open(RUTA_OPCIONES, encoding="utf-8") as f:
                datos = json.load(f)
        datos["feria"] = ACTIVO
        os.makedirs(os.path.dirname(RUTA_OPCIONES), exist_ok=True)
        with open(RUTA_OPCIONES, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=1)
    except (OSError, ValueError):
        pass


def activo(juego):
    """¿Esta partida va en modo feria? (lo que había al empezarla)"""
    return bool(getattr(juego, "modo_feria", False))


def recortar_objetos(juego, objetos, mundo=None):
    """Lo que no va en la Feria, fuera de los objetos del mapa (antes de armar
    los muebles, las salas selladas, la misión...)."""
    if not activo(juego) or objetos is None:
        return
    if FERIA.get("solo_primera_puerta"):
        # Solo la puerta con código de la salida (la que abre la partida). Las
        # otras (en MapaFinal, la de la Prisión y la de Gestación) quedan
        # abiertas: si no, al que atrapaban lo dejaban detrás de una puerta
        # cerrada y había que buscar otro código para salir.
        objetos["puertas_codigo"] = list(objetos.get("puertas_codigo") or [])[:1]
    # Las consolas: se ordenan de la más cercana a la más lejana (caminando)
    # y, después de sellar las salas que sobran, `recortar_consolas` deja las
    # que tocan (sellar antes de escoger: si no, una de las escogidas podía
    # quedar en una sala sellada y salía una menos).
    consolas = list(objetos.get("consolas") or [])
    if consolas_feria(len(getattr(juego, "seleccion_roles", ()) or ())) is not None and len(consolas) > 1:
        objetos["consolas"] = _mas_cercanas_caminando(objetos, consolas, mundo)
    if FERIA.get("sin_guardia"):
        objetos.pop("guardia", None)
        objetos.pop("planta", None)
    if FERIA.get("sin_puertas_dobles"):
        objetos["puertas_dobles"] = []
    if FERIA.get("sin_caso"):
        objetos["pruebas"] = []


def aplicar(juego):
    """Con la partida ya armada (al final de `_preparar_partida`)."""
    juego.feria_avisos = set()
    if not activo(juego):
        return
    dificultad = getattr(juego, "dificultad", None)
    if dificultad is not None:
        dificultad.feria = True             # (AJUSTES_FERIA: rumores, cuentas falsas)
    mision = getattr(juego, "mision", None)
    if mision is not None and getattr(mision, "activa", False):
        mision.piezas_necesarias = FERIA.get("piezas", mision.piezas_necesarias)
        if FERIA.get("limite_s"):
            juego.tiempo_restante_ms = FERIA["limite_s"] * 1000
    red = getattr(juego, "nexus", None)
    if red is not None:
        if FERIA.get("primer_rumor_s") is not None:
            red.reloj_rumor_ms = FERIA["primer_rumor_s"] * 1000
        red.umbral_planos = max(red.umbral_planos, FERIA.get("umbral_planos_min", 0.0))
        if FERIA.get("tick_verde_ms"):
            red.tick_verde_ms = FERIA["tick_verde_ms"]     # la confianza sube más rápido


def actualizar(juego):
    """Una vez por cuadro, después de descontar el tiempo: los avisos y el final."""
    if not activo(juego) or juego.tiempo_restante_ms is None:
        return
    mision = getattr(juego, "mision", None)
    if mision is None or not getattr(mision, "activa", False) or mision.resultado is not None:
        return
    quedan_s = juego.tiempo_restante_ms / 1000
    avisos = getattr(juego, "feria_avisos", None)
    if avisos is None:
        avisos = juego.feria_avisos = set()
    for aviso in FERIA.get("avisos_s", ()):
        if quedan_s <= aviso and aviso not in avisos:
            avisos.add(aviso)
            texto = ("¡Nos queda 1 minuto! Hay que llegar a la cápsula." if aviso <= 60
                     else f"Nos quedan {aviso // 60} minutos para escapar.")
            for jugador in juego.jugadores:
                jugador.avisar(texto, COLOR_AVISO)
            if hasattr(juego, "sonar"):
                juego.sonar("expuesto", 0.6)
    if juego.tiempo_restante_ms <= 0:
        juego.tiempo_restante_ms = 0
        mision.resultado, mision.motivo_fin = "derrota", "tiempo"



def consolas_feria(n_jugadores):
    """Cuántas consolas hay que apagar en la Feria con `n_jugadores` (Diego,
    nov 21: 2 -> 1, 3 -> 2, 4 -> 3). None = las del mapa."""
    n = FERIA.get("consolas")
    if isinstance(n, dict):
        if not n:
            return None
        if n_jugadores in n:
            return n[n_jugadores]
        cerca = min(n, key=lambda k: abs(k - n_jugadores))     # (otra cantidad: la más parecida)
        return n[cerca]
    return n


def minimos_sellado(juego, n_jugadores):
    """Lo que las salas selladas tienen que dejar abierto en la Feria (las
    consolas que se piden). None sin el modo feria."""
    if not activo(juego):
        return None
    n = consolas_feria(n_jugadores)
    return {"consolas": n} if n else None


def recortar_consolas(juego, objetos, n_jugadores):
    """Después de sellar: deja las `consolas_feria` más cercanas caminando
    (`recortar_objetos` ya las ordenó)."""
    if not activo(juego) or objetos is None:
        return
    n = consolas_feria(n_jugadores)
    consolas = list(objetos.get("consolas") or [])
    if n is not None and len(consolas) > n:
        objetos["consolas"] = consolas[:max(1, n)]


def _mas_cercanas_caminando(objetos, puntos, mundo):
    """`puntos` (relativos) de la más cercana a la más lejana del inicio,
    CAMINANDO (en MapaFinal la consola más cercana en línea recta queda a
    8100 px de camino y otra, a 5200). Con una navegación aparte y gruesa
    (celdas de 32 px: ~0.2 s en la carga; el mapa todavía no tiene los
    muebles). Sin mundo, en línea recta."""
    inicio = objetos.get("spawn") or (0.5, 0.5)
    recta = sorted(puntos, key=lambda c: math.dist((c[0], c[1]), (inicio[0], inicio[1])))
    if mundo is None or not hasattr(mundo, "paredes_base"):
        return recta
    try:
        from juego.navegacion import Navegacion
        W, H = mundo.ancho, mundo.alto
        nav = Navegacion(mundo, 34, 20, paso=32)
        desde = (int(inicio[0] * W), int(inicio[1] * H))

        def largo(c):
            camino = nav.camino(desde, (int(c[0] * W), int(c[1] * H)), sellos=False)
            if not camino:
                return float("inf")
            return sum(math.dist(a, b) for a, b in zip([desde] + camino, camino))
        return sorted(recta, key=largo)
    except Exception:
        return recta
