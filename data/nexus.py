"""Mensajes que circulan por NEXUS, la red social de la misión.

Mismo formato que las publicaciones de antes (Estructuras/abb_publicaciones.py
y Estructuras/arbol_decision.py): `veracidad` es la clave del ABB (0 = lo
mandaron los aliens para engañarlos, 100 = comprobado) y los `hijos` son lo que
el jugador puede hacer con el mensaje en una terminal NEXUS: confiar,
verificar o ignorar. Cada opción tiene una o varias consecuencias, y se sortea
cuál pasa.

Además de mover los indicadores, una consecuencia puede tener `_accion`, que
hace algo en la partida (ver Game._accion_nexus en App.py):

    revelar_piezas   todos ven las piezas un rato
    revelar_codigo   el resultado dice el código de la puerta
    revelar_aliens   el que lo leyó ve el mapa con los aliens
    alertar          los aliens oyen al que lo leyó y van por él
    calma            el que lo leyó se calma (baja el pulso)

En los textos, {codigo} se reemplaza por el código de la puerta de esa partida.
La regla de diseño: creerle a un mensaje falso tiene que doler, y verificarlo
tiene que valer la pena.
"""


def _mensaje(texto, veracidad, confiar, verificar, ignorar):
    return {
        "texto": texto,
        "veracidad": veracidad,
        "tipo": "mensaje",
        "hijos": [
            {"texto": "Confiar", "tipo": "opcion", "efectos": {}, "hijos": confiar},
            {"texto": "Verificar", "tipo": "opcion", "efectos": {"informacion_verificada": 4},
             "hijos": verificar},
            {"texto": "Ignorar", "tipo": "opcion", "efectos": {}, "hijos": ignorar},
        ],
    }


def _c(texto, accion=None, **efectos):
    if accion:
        efectos["_accion"] = accion
    return {"texto": texto, "tipo": "consecuencia", "efectos": efectos}


MENSAJES_NEXUS = [
    _mensaje(
        "Prisionero 12: «Encontré piezas de repuesto tiradas por toda la nave. Se las marco a todos.»",
        85,
        confiar=[_c("Era verdad: ahora todos ven dónde están las piezas.", "revelar_piezas",
                    confianza_ciudadana=6, informacion_verificada=6)],
        verificar=[_c("Lo confirmaste con otro prisionero: las piezas quedan marcadas para todos.",
                      "revelar_piezas", informacion_verificada=8)],
        ignorar=[_c("Se te pasó una pista buena.", None, convivencia=-2)],
    ),
    _mensaje(
        "Anónimo: «La salida está libre, los guardias se fueron. Salgan corriendo YA.»",
        8,
        confiar=[_c("Era una trampa. Los aliens te oyeron correr.", "alertar",
                    desinformacion=10, conflictos=6)],
        verificar=[_c("El mensaje venía de una terminal alienígena. Era falso.", None,
                      desinformacion=-6, informacion_verificada=8)],
        ignorar=[_c("Bien: no le hiciste caso a algo sin fuente.", None, desinformacion=-3)],
    ),
    _mensaje(
        "Prisionera 3: «Rayaron el código de la puerta en mi celda: {codigo}.»",
        78,
        confiar=[_c("Te sirvió: el código de la puerta es {codigo}.", "revelar_codigo",
                    confianza_ciudadana=5)],
        verificar=[_c("Coincide con lo que dicen las notas: {codigo}.", "revelar_codigo",
                      informacion_verificada=8)],
        ignorar=[_c("Te perdiste el código.", None)],
    ),
    _mensaje(
        "IA de la nave: «Los sujetos que mantienen la calma no son detectados.»",
        70,
        confiar=[_c("Respiras hondo. Tu pulso baja.", "calma", convivencia=4)],
        verificar=[_c("Es cierto: el latido es lo que te delata. Te calmas.", "calma",
                      informacion_verificada=6)],
        ignorar=[_c("Sigues nervioso.", None)],
    ),
    _mensaje(
        "Anónimo: «Escóndanse en los casilleros, ahí NUNCA revisan.»",
        22,
        confiar=[_c("Mentira: sí revisan si te oyen. Te confiaste.", None,
                    desinformacion=8, conflictos=4)],
        verificar=[_c("Falso: si tu latido se oye, revisan el escondite.", None,
                      informacion_verificada=8, desinformacion=-4)],
        ignorar=[_c("Mejor así.", None)],
    ),
    _mensaje(
        "Prisionero 9: «Desde la terminal se ve dónde patrulla cada alien.»",
        64,
        confiar=[_c("Tenías razón: ves el mapa con los aliens un rato.", "revelar_aliens",
                    informacion_verificada=4)],
        verificar=[_c("Lo comprobaste: ves el mapa con los aliens.", "revelar_aliens",
                      informacion_verificada=6)],
        ignorar=[_c("Sin cambios.", None)],
    ),
    _mensaje(
        "Anónimo: «Griten para que los demás sepan dónde están, así nos reunimos.»",
        12,
        confiar=[_c("Te oyeron. Y no fueron tus compañeros.", "alertar",
                    desinformacion=8, conflictos=8)],
        verificar=[_c("El remitente no existe en la lista de prisioneros. Era falso.", None,
                      informacion_verificada=8)],
        ignorar=[_c("Bien hecho.", None, desinformacion=-2)],
    ),
    _mensaje(
        "Prisionera 5: «Las consolas moradas son la navegación. Apáguenlas antes de ir a la cápsula.»",
        92,
        confiar=[_c("Información confiable: anotado.", None, informacion_verificada=5,
                    confianza_ciudadana=4)],
        verificar=[_c("Las notas dicen lo mismo. Es cierto.", None, informacion_verificada=8)],
        ignorar=[_c("Igual vas a tener que apagarlas.", None)],
    ),
]
