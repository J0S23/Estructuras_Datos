"""Lo que hay puesto en el mapa: dónde aparecen los jugadores, por dónde
patrullan los aliens y dónde están los escondites, terminales, paneles, piezas
y zonas.

Todo eso vive en `Hitboxes/<mapa>_objetos.json`, que se arma con el editor
visual (`python Editores/editor_mapa.py`), así que cambiar el mapa no requiere
tocar código. Si el archivo no existe, o le falta alguna parte, se usan los
valores de siempre de data/ (escondites.py, estaciones.py,
comportamiento_alien.py y tareas.py): el juego nunca se queda sin nada.

Qué mapa usa el juego lo dice `Hitboxes/mapa_activo.json`, que también se
cambia desde el editor (tecla M).

Las coordenadas van de 0 a 1 sobre el tamaño del mapa, como en el resto del
proyecto, para que sigan sirviendo si cambia la escala.
"""

import copy
import json
import os


RAIZ = os.path.dirname(os.path.abspath(__file__))
CARPETA = os.path.join(RAIZ, "Hitboxes")
ARCHIVO_MAPA_ACTIVO = os.path.join(CARPETA, "mapa_activo.json")
MAPA_POR_DEFECTO = "Colegio"
VERSION = 1

# Las pruebas lo ponen en False para jugar siempre con los valores de data/ y
# no depender de lo que alguien haya guardado con el editor.
USAR_ARCHIVOS = True

# Las partes del archivo, en el orden en que las muestra el editor.
PARTES = ("spawn", "rutas_aliens", "escondites", "terminales", "paneles", "piezas", "zonas")


def ruta_archivo(mapa):
    return os.path.join(CARPETA, f"{mapa}_objetos.json")


# -- Mapa activo -----------------------------------------------------------------------

def mapa_activo():
    """Nombre del fondo (Imagenes/Fondos/<nombre>.png) con el que se juega."""
    if not USAR_ARCHIVOS:
        return MAPA_POR_DEFECTO
    try:
        with open(ARCHIVO_MAPA_ACTIVO, "r", encoding="utf-8") as fh:
            nombre = json.load(fh).get("mapa")
        return nombre or MAPA_POR_DEFECTO
    except (OSError, ValueError, AttributeError):
        return MAPA_POR_DEFECTO


def fijar_mapa_activo(mapa):
    os.makedirs(CARPETA, exist_ok=True)
    with open(ARCHIVO_MAPA_ACTIVO, "w", encoding="utf-8") as fh:
        json.dump({"mapa": mapa}, fh, indent=2, ensure_ascii=False)


# -- Valores por defecto (los de data/) -----------------------------------------------------

def por_defecto():
    from data.comportamiento_alien import RUTAS_ALIENS
    from data.escondites import ESCONDITES
    from data.estaciones import TERMINALES, PANELES, PIEZAS
    from data.tareas import ZONAS

    def puntos(lista):
        return [{"clave": d["clave"], "nombre": d["nombre"], "rx": d["rx"], "ry": d["ry"]}
                for d in lista]

    return {
        "version": VERSION,
        "spawn": None,     # None = alrededor del centro del mapa
        "rutas_aliens": [[list(p) for p in ruta] for ruta in RUTAS_ALIENS],
        "escondites": puntos(ESCONDITES),
        "terminales": puntos(TERMINALES),
        "paneles": puntos(PANELES),
        "piezas": [list(p) for p in PIEZAS],
        "zonas": {z["clave"]: {"rx": z["rx"], "ry": z["ry"], "radio": z["radio"]} for z in ZONAS},
    }


# -- Cargar y guardar ----------------------------------------------------------------------

def cargar(mapa=None, ruta=None):
    """Los objetos del mapa: lo del archivo, y lo que falte, de data/."""
    datos = por_defecto()
    if not USAR_ARCHIVOS and ruta is None:
        return datos
    ruta = ruta or ruta_archivo(mapa or mapa_activo())
    try:
        with open(ruta, "r", encoding="utf-8") as fh:
            guardado = json.load(fh)
    except (OSError, ValueError):
        return datos
    for parte in PARTES:
        if parte in guardado:
            datos[parte] = guardado[parte]
    if "zonas" in guardado:
        # Una zona que el archivo no nombra conserva su posición de siempre.
        zonas = por_defecto()["zonas"]
        zonas.update(guardado["zonas"])
        datos["zonas"] = zonas
    return normalizar(datos)


def guardar(mapa, datos, ruta=None):
    ruta = ruta or ruta_archivo(mapa)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    limpio = normalizar(copy.deepcopy(datos))
    limpio["version"] = VERSION
    limpio["mapa"] = mapa
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(limpio, fh, indent=2, ensure_ascii=False)
    return ruta


def normalizar(datos):
    """Redondea, recorta a 0-1 y les pone clave a los objetos que no tengan."""
    def r(v):
        return round(min(1.0, max(0.0, float(v))), 4)

    if datos.get("spawn"):
        datos["spawn"] = [r(datos["spawn"][0]), r(datos["spawn"][1])]
    datos["rutas_aliens"] = [[[r(x), r(y)] for x, y in ruta] for ruta in datos.get("rutas_aliens", [])]
    datos["piezas"] = [[r(x), r(y)] for x, y in datos.get("piezas", [])]
    for parte, prefijo, nombre in (("escondites", "escondite", "Casillero"),
                                   ("terminales", "terminal", "Terminal"),
                                   ("paneles", "panel", "Panel dañado")):
        usadas = set()
        for i, obj in enumerate(datos.get(parte, [])):
            obj["rx"], obj["ry"] = r(obj["rx"]), r(obj["ry"])
            obj.setdefault("nombre", nombre)
            clave = obj.get("clave")
            if not clave or clave in usadas:
                n = i + 1
                while f"{prefijo}_{n}" in usadas:
                    n += 1
                clave = f"{prefijo}_{n}"
            obj["clave"] = clave
            usadas.add(clave)
    for zona in datos.get("zonas", {}).values():
        zona["rx"], zona["ry"] = r(zona["rx"]), r(zona["ry"])
        zona["radio"] = round(min(0.2, max(0.01, float(zona.get("radio", 0.045)))), 4)
    return datos
