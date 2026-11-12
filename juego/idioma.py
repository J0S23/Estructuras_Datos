"""Idioma del juego: español (el de siempre) o inglés.

Todo el juego está escrito en español. El inglés no cambia el código: se
traduce el texto justo antes de dibujarlo. Las fuentes del juego
(juego/fuentes.py) pasan por `tr` todo lo que miden (`size`) y dibujan
(`render`), y las funciones que parten un párrafo en renglones o lo cortan
con "..." traducen el párrafo entero antes de partirlo.

Las traducciones están en data/idioma_en.py: {"texto en español": "en inglés"}.
Un texto armado con variables (f"{n} aliens fuera de combate {s} s") está
como plantilla con {} en su lugar: "{} aliens fuera de combate {} s" ->
"{} aliens out of action for {} s". Lo que va en cada {} se traduce también
(así "Tienes 3 vidas" o "[E] Terminal NEXUS" salen bien). Las plantillas de
`.format` llevan su nombre: "Tienes {vidas}" -> "You have {vidas}".

Si un texto no está, sale en español. `python pruebas/prueba_idioma.py`
dice cuáles faltan (p. ej. después de cambiar un texto del juego).

Se escoge en el menú principal ("Idioma") o en Pausa > Opciones, y queda
guardado en Guardado/opciones.json.
"""

import json
import os
import re

_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUTA_OPCIONES = os.path.join(_RAIZ, "Guardado", "opciones.json")

IDIOMAS = ("es", "en")
NOMBRES = {"es": "Español", "en": "English"}

IDIOMA = "es"

_exactos = None          # {español: inglés}
_minusculas = None       # {español en minúsculas: inglés}
_plantillas = None       # [(regex, inglés, nombres, letras fijas, texto fijo)]
_cache = {}
_al_cambiar = []          # funciones que limpian cachés de dibujos con texto
MAX_CACHE = 30000

# Para los textos que no están enteros en el catálogo: se parten por estos
# separadores y se traduce cada pedazo (listas armadas con join, renglones).
SEPARADORES = ("\n", "  ·  ", " · ", " | ", " > ", "  ", " - ", " — ", ": ", ", ", " / ", " (", ") ")
_FUERTES = ("\n", "  ·  ", " · ", " | ")
_PUNTUACION = re.compile(r"^([¡¿\[(\"'«\s-]*)(.*?)([.:!?…)\]\"'»\s]*)$", re.S)
_HUECO = re.compile(r"\{(\w*)\}")


def es_ingles():
    return IDIOMA == "en"


def tr(texto):
    """El texto en el idioma del juego (en español, tal cual)."""
    if IDIOMA == "es" or not texto or not isinstance(texto, str):
        return texto
    r = _cache.get(texto)
    if r is None:
        if _exactos is None:
            _cargar()
        r = _traducir(texto, 0)
        if len(_cache) > MAX_CACHE:
            _cache.clear()
        _cache[texto] = r
    return r


def cambiar(idioma, guardar=True):
    """Pone el idioma ("es" o "en"), limpia lo dibujado con el otro y lo guarda."""
    global IDIOMA
    if idioma not in IDIOMAS:
        idioma = "es"
    if idioma == IDIOMA:
        return
    IDIOMA = idioma
    _cache.clear()
    for funcion in _al_cambiar:
        try:
            funcion()
        except Exception:
            pass
    if guardar:
        _guardar()


def siguiente(signo=1):
    """El idioma que sigue (para las opciones con < >)."""
    return IDIOMAS[(IDIOMAS.index(IDIOMA) + signo) % len(IDIOMAS)]


def etiqueta():
    """El texto de la opción: ya en el idioma que dice (no se traduce)."""
    return "Idioma: Español" if IDIOMA == "es" else "Language: English"


def al_cambiar(funcion):
    """Registra una función que se llama al cambiar de idioma (cachés)."""
    _al_cambiar.append(funcion)
    return funcion


def cargar_preferencia():
    """Lee el idioma guardado (si no hay, español). No guarda nada. Las
    pruebas (sin ventana) siempre van en español."""
    if os.environ.get("SDL_VIDEODRIVER") == "dummy":
        return
    try:
        with open(RUTA_OPCIONES, encoding="utf-8") as f:
            cambiar(json.load(f).get("idioma", "es"), guardar=False)
    except (OSError, ValueError, AttributeError):
        pass


def _guardar():
    if os.environ.get("SDL_VIDEODRIVER") == "dummy":
        return                      # las pruebas no tocan las opciones de nadie
    try:
        datos = {}
        if os.path.exists(RUTA_OPCIONES):
            with open(RUTA_OPCIONES, encoding="utf-8") as f:
                datos = json.load(f)
        datos["idioma"] = IDIOMA
        os.makedirs(os.path.dirname(RUTA_OPCIONES), exist_ok=True)
        with open(RUTA_OPCIONES, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
    except (OSError, ValueError):
        pass


# -- Traducir -----------------------------------------------------------------------

def _cargar():
    global _exactos, _minusculas, _plantillas
    from data.idioma_en import TEXTOS
    _exactos, _minusculas, _plantillas = {}, {}, []
    for es, en in TEXTOS.items():
        if not en:
            continue
        if _HUECO.search(es):
            _plantillas.append(_plantilla(es, en))
            if es.endswith(".") and not es.endswith("..") and isinstance(en, str):
                _plantillas.append(_plantilla(es[:-1], en.rstrip(".")))
        else:
            _exactos[es] = en
            _minusculas.setdefault(es.lower(), en)
            # "Pantalla completa: " + "Sí": también sin los dos puntos (o sin
            # el punto final, para las frases que se juntan con otra).
            for corto, corto_en in ((es.strip().rstrip(":").strip(), en.strip().rstrip(":").strip()),
                                    (es.rstrip("."), en.rstrip("."))):
                if corto and corto != es and not es.endswith(".."):
                    _exactos.setdefault(corto, corto_en)
                    _minusculas.setdefault(corto.lower(), corto_en)
    # Las más específicas primero (más letras fijas).
    _plantillas.sort(key=lambda p: -p[3])


def _plantilla(es, en):
    partes, nombres, fijo = [], [], 0
    pos = 0
    for m in _HUECO.finditer(es):
        literal = es[pos:m.start()]
        partes.append(re.escape(literal))
        fijo += len(literal)
        partes.append("(.*?)")
        nombres.append(m.group(1))
        pos = m.end()
    partes.append(re.escape(es[pos:]))
    fijo += len(es) - pos
    return re.compile("".join(partes), re.S), en, nombres, fijo, _HUECO.sub("", es)


def _con_mayusculas_de(original, traduccion):
    if original.isupper() and any(c.isalpha() for c in original):
        return traduccion.upper()
    if original[:1].isupper() and traduccion[:1].islower():
        return traduccion[:1].upper() + traduccion[1:]
    if original[:1].islower() and traduccion[:1].isupper() and not traduccion[:2].isupper():
        return traduccion[:1].lower() + traduccion[1:]
    return traduccion


def _rellenar(regex_en, nombres, grupos, nivel):
    valores = [_traducir(g, nivel + 1) for g in grupos]
    if callable(regex_en):              # singular/plural (data/idioma_en.py)
        try:
            return regex_en(*valores)
        except (TypeError, ValueError):
            return None
    if nombres and all(nombres):
        try:
            return regex_en.format(**dict(zip(nombres, valores)))
        except (KeyError, IndexError, ValueError):
            pass
    try:
        return regex_en.format(*valores)
    except (KeyError, IndexError, ValueError):
        return None


def _traducir(t, nivel):
    if nivel > 6 or not t:
        return t
    r = _exactos.get(t)
    if r is not None:
        return r
    # Espacios alrededor.
    nucleo = t.strip()
    if nucleo != t:
        if not nucleo:
            return t
        i = t.index(nucleo)
        return t[:i] + _traducir(nucleo, nivel + 1) + t[i + len(nucleo):]
    # Mayúsculas (lo que se dibuja con .upper()).
    r = _minusculas.get(t.lower())
    if r is not None:
        return _con_mayusculas_de(t, r)
    # Números solos, teclas de una letra, @usuarios: tal cual.
    if len(t) <= 1 or not re.search(r"[A-Za-zÁÉÍÓÚáéíóúñÑ]{2}", t) or t.startswith("@") and " " not in t:
        return t
    # Plantillas.
    for regex, en, nombres, _, literal in _plantillas:
        m = regex.fullmatch(t)
        if m and not any(sep in g and sep not in literal for g in m.groups() for sep in _FUERTES):
            # (una plantilla con {} al final no se traga una lista "a · b · c")
            r = _rellenar(en, nombres, m.groups(), nivel)
            if r is not None and r != t:
                return r
    # Puntuación alrededor ("¡Listo!", "Sector:", "(nuevo)").
    m = _PUNTUACION.match(t)
    if m and (m.group(1) or m.group(3)) and m.group(2):
        antes, medio, despues = m.groups()
        # La puntuación del final puede ser parte del texto ('"Hola."').
        for k in range(len(despues), -1, -1):
            candidato = medio + despues[:k]
            if candidato == t:
                continue
            r = _traducir(candidato, nivel + 1)
            if r != candidato:
                return antes.replace("¡", "").replace("¿", "") + r + despues[k:]
    # Pedazos.
    for sep in SEPARADORES:
        if sep in t:
            pedazos = t.split(sep)
            traducidos = [_traducir(p, nivel + 1) for p in pedazos]
            if traducidos != pedazos:
                return sep.join(traducidos)
    return t
