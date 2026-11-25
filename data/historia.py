"""La historia de los niños (docs/historia.md): textos, tiempos y lugares.

Campo y el equipo pueden cambiar todo lo de aquí sin tocar código:

- la cinemática de apertura (CINEMATICA): lo que dice cada escena;
- las pistas del Acto 2 (PISTAS): la mochila, el zapato y el dibujo;
- la sala oculta (SALAS_OCULTAS): dónde queda en cada mapa;
- lo que dicen los agentes al ver a los niños (DIALOGO_NINOS);
- la votación (VOTACION) y los finales (FINALES).

La lógica está en misiones/sala_secreta.py, el dibujo en
screens/sala_secreta.py y las cinemáticas en screens/cinematica.py.
"""

# -- Cinemática de apertura (screens/cinematica.py) ---------------------------------
# Cada escena: cuánto dura (ms) y los textos que van saliendo abajo. El dibujo
# de cada una está en screens/cinematica.py (o, si existe, la imagen
# Imagenes/Historia/escena_<n>.png de fondo).
CINEMATICA = [
    {"ms": 11000, "lugar": "Una habitación a oscuras. 11:47 p. m.",
     "textos": ["Una niña de 11 años chatea en NEXUS con la cuenta de su cantante favorita.",
                "Le escribe su dirección y la envía."]},
    {"ms": 9500, "lugar": "Esa misma semana, en otras pantallas.",
     "textos": ["Un niño comparte su ubicación en vivo para entrar a un reto.",
                "Otro sube una foto con el uniforme y el nombre de su colegio.",
                "A otro, una cuenta nueva le escribe: \"No le cuentes a tus papás\"."]},
    {"ms": 9500, "lugar": "Esa noche.",
     "textos": ["Una luz verde cae sobre cada una de esas casas.",
                "A la mañana siguiente hay camas vacías y un celular en el piso."]},
    {"ms": 9500, "lugar": "Un mes después.",
     "textos": ["Desaparecen cientos de niños en todo el mundo, pero en NEXUS nadie habla de ellos.",
                "Lo que se publica sobre ellos se borra en minutos."]},
    {"ms": 9500, "lugar": "Una sala del gobierno de Colombia.",
     "textos": ["Los famosos de NEXUS dicen lo mismo a la misma hora. Una nave invisible orbita la Tierra.",
                "Arman una misión secreta con cuatro agentes. Ellos tampoco saben qué van a encontrar."]},
]
FRASE_APERTURA = "Allá arriba, la mentira también tiene cuenta."
FRASE_APERTURA_MS = 4500

# El chat de la escena 1 (lo que se ve en el celular de la niña).
CHAT_ESCENA_1 = {
    "cuenta": "@luna.oficial",
    "mensajes": [
        ("ella", "¡¡Hola!! ¿De verdad eres Luna?"),
        ("cuenta", "¡Claro! ¡Ganaste una entrada al concierto!"),
        ("cuenta", "Solo dime dónde vives para mandártela."),
        ("ella", "Calle 14 # 22-31, apto 302"),
    ],
}
NOTIFICACION_FINAL = "Gracias por compartir."

# -- Pistas del Acto 2: cosas que no entienden ------------------------------------------
# Salen en salas de la nave (la primera de `salas` que esté abierta en esta
# partida). Al revisarlas (tecla de interactuar) el agente dice `texto`.
# `imagen`: Imagenes/Historia/<imagen>.png si existe (si no, un dibujo).
PISTAS = [
    {"tipo": "mochila", "imagen": "mochila",
     "salas": ["Residencial", "Gestación", "Laboratorio", "General"],
     "pista": "Revisar la mochila",
     "texto": "Una mochila de colegio, con llaveros y un cuaderno de matemáticas. "
              "¿Qué hace esto en una nave alien?"},
    {"tipo": "zapato", "imagen": "zapato",
     "salas": ["Gestación", "Laboratorio", "Biosfera", "Residencial", "Motores"],
     "pista": "Revisar el zapato",
     "texto": "Un zapato pequeño, de niño. Está sucio, como si lo hubieran arrastrado."},
    {"tipo": "dibujo", "imagen": "dibujo",
     "salas": ["Laboratorio", "Comando", "Motores", "General", "Control"],
     "pista": "Mirar el dibujo",
     "texto": "Un dibujo con crayones tirado en el piso: una casa, una familia y "
              "una luz verde en el cielo."},
]
RADIO_PISTA = 90          # a cuánto (px del mundo) se puede revisar

# -- La sala oculta (la de los niños) ----------------------------------------------------
# Por mapa, en fracciones del mapa (como el editor). `puerta`: la losa de la
# pared de la Bahía que se abre (sube); `pasillos`: de la puerta a la sala,
# en orden (el último es el que entra a la sala, por su izquierda); `sala`:
# donde están los niños. La decoración que tape la entrada se corre a un lado. Lo de adentro se talla en las paredes del mapa al
# armar la partida (misiones/sala_secreta.py). Un mapa sin entrada aquí no
# tiene sala oculta (se juega como antes).
SALAS_OCULTAS = {
    # La entrada es la puerta empotrada (marco dorado) de la pared de arriba
    # de la Bahía, detrás de la lámpara (Diego, nov 24). La pared y el marco
    # se quedan: solo la puerta se abre, y el pedazo de pared de encima
    # (`dintel`) se dibuja delante de los personajes, así se pasa por debajo.
    # Arriba de esa pared casi no hay mapa: el pasillo sube, voltea a la
    # derecha y llega a la sala, arriba a la derecha de la Bahía. Desde
    # afuera no se ve nada de eso: se ve solo al cruzar la puerta.
    "MapaFinal": {
        "puerta": (3909 / 6144, 396 / 6144, 189 / 6144, 174 / 6144),      # el marco dorado
        "dintel": (3904 / 6144, 300 / 6144, 199 / 6144, 104 / 6144),      # la pared de encima
        "pasillos": [(3930 / 6144, 300 / 6144, 155 / 6144, 270 / 6144),   # cruza la pared
                     (3930 / 6144, 110 / 6144, 155 / 6144, 190 / 6144),   # sube
                     (3930 / 6144, 110 / 6144, 630 / 6144, 120 / 6144)],  # y va a la derecha
        "sala": (4560 / 6144, 110 / 6144, 640 / 6144, 690 / 6144),
        # Lo que NO se pinta encima (la Bahía con sus paredes).
        "no_pintar": [(3300 / 6144, 300 / 6144, 930 / 6144, 1500 / 6144)],
    },
}
NOMBRE_SALA = "Sala oculta"
ABRIR_PARED_MS = 2600          # lo que tarda la puerta en abrirse (se destraba y se parte en dos)
# Cuántas cápsulas con niños hay (en dos filas, con un pasillo en medio).
CAPSULAS = 8

# -- Los que no lo lograron (sin decirlo nunca) -----------------------------------------
# Cada cápsula tiene su número de sujeto (en su monitor). Las `APAGADAS` ya
# no brillan, no tienen burbujas y su monitor está plano. Mientras hablan,
# la de `SE_APAGA` parpadea, su latido se corta y NEILA la "archiva"
# (data/ia_nave.py: "sala_archivado"). Todo por índice de cápsula (0..7).
SUJETOS = [12, 15, 19, 22, 23, 27, 30, 34]
APAGADAS = (2, 5, 7)
SE_APAGA = {"capsula": 4, "desde_ms": 8000, "dura_ms": 1900}
# El celular en el piso, frente a una cápsula apagada: los mensajes de la mamá.
CELULAR_NINO = {
    "capsula": 5,
    "pista": "Revisar el celular",
    "hora": "3:12",
    "fecha": "martes 14 de mayo",
    "bateria": 1,
    "llamadas": "47 llamadas perdidas",
    "contacto": "Mamá",
    "mensajes": [
        "¿Dónde estás, mi amor?",
        "Contéstame, por favor",
        "Ya pusimos la denuncia",
        "Tu hermanito pregunta por ti",
        "Te dejé la luz del cuarto prendida",
    ],
    "cerrar": "cerrar",
}
# El Biomante puede intentar regenerar una cápsula apagada.
REGENERAR = {
    "pista": "Regenerar la cápsula",
    "texto": "Lo intento... pero mi regeneración ya no encuentra nada que curar.",
    "ms": 2200,
}

# Lo que dicen al abrirse la pared (un agente cualquiera, a todos).
AL_ABRIRSE = "¿Escucharon eso? Algo se abrió en la pared, al lado de la cápsula..."
# (Lo que dice NEILA, la IA de la nave, va en data/ia_nave.py: "sala_abierta"
# y "sala_alarma".)

# -- Lo que dicen al ver a los niños -----------------------------------------------------
# En orden; `rol` es quién lo dice si está en la partida (si no, otro que
# esté). {pistas} se cambia por lo que encontraron en el camino.
DIALOGO_NINOS = [
    {"rol": "Biomante", "texto": "Son niños... están dormidos. Todavía respiran."},
    {"rol": "Tecnomante", "texto": "Son los niños desaparecidos. Los de las noticias que NEXUS borraba."},
    {"rol": "Resonante", "texto": "Esa niña tiene el celular en la mano. Le escribieron haciéndose pasar por alguien famoso."},
    {"rol": "Forjador", "texto": "{pistas} Las cápsulas no se abren: están soldadas a la nave."},
    {"rol": "Biomante", "texto": "Esa luz estaba prendida hace un momento..."},
]
PISTAS_EN_DIALOGO = {
    3: "La mochila, el zapato, el dibujo... eran de ellos.",
    2: "Lo que encontramos en la nave era de ellos.",
    1: "Lo que encontramos en la nave era de uno de ellos.",
    0: "Por eso nadie hablaba de ellos en NEXUS.",
}
DIALOGO_MS = 3600              # cuánto se ve cada línea

# -- La votación -----------------------------------------------------------------------
VOTACION = {
    "segundos": 20,
    # Si votaron todos, el contador baja a esto (si le quedaba más).
    "segundos_si_votaron_todos": 4,
    "titulo": "¿QUÉ HACEMOS?",
    "opciones": [
        {"clave": "escapar", "texto": "Correr a la cápsula", "detalle": "Escapar sabiendo lo que pasa con los niños"},
        {"clave": "quedarse", "texto": "Quedarnos con ellos", "detalle": "No dejarlos solos, aunque nos alcancen"},
    ],
    "nota": "Gana lo que más voten. Empate: se quedan. Si nadie vota, la nave decide.",
    "alarma": "¡ALERTA!",
    "alarma_sub": "LOS ALIENS VIENEN",
}
DESENLACE_MS = 2600            # al acabar el tiempo: llegan los aliens (antes del final)

# -- Los finales (screens/final.py y screens/resultados.py) ------------------------------
# `titular` y `motivo` salen en los resultados; `escena`: los textos de la
# escena del final. La frase final sale en todos.
FINALES = {
    "sin_entrar": {
        "victoria": True,
        "titular": "¡ESCAPARON DE LA NAVE!",
        "motivo": "Escaparon sin entrar a la sala oculta.",
        "escena": ["Los famosos alienígenas quedan expuestos y NEXUS deja de ser la voz de la nave.",
                   "Pero nunca sabrán lo que había detrás de esa pared.",
                   "Y los niños siguen arriba."],
    },
    "escaparon": {
        "victoria": True,
        "titular": "ESCAPARON... SIN ELLOS",
        "motivo": "Votaron por correr a la cápsula y salieron vivos con lo que vieron.",
        "escena": ["Por primera vez, NEXUS habla de los niños.",
                   "La noticia es real, y millones de personas la comparten.",
                   "Los niños siguen arriba, pero ya nadie puede esconderlos."],
    },
    "quedarse": {
        "victoria": False,
        "titular": "SE QUEDARON CON LOS NIÑOS",
        "motivo": "Votaron por quedarse. Los aliens los alcanzaron junto a los niños.",
        "escena": ["Los aliens los alcanzan junto a las cápsulas.",
                   "La pantalla se apaga y NEXUS sigue publicando como si nada.",
                   "En la Tierra nadie sabrá nunca lo que encontraron."],
    },
    "nadie": {
        "victoria": False,
        "titular": "NADIE DECIDIÓ",
        "motivo": "Se acabó el tiempo sin votos: el Guardia soltó la fruta y destruyó la cápsula.",
        "escena": ["Nadie decidió. Se quedaron en la nave.",
                   "El Guardia de la Bahía suelta la fruta y destruye la cápsula.",
                   "Los capturan a todos. NEXUS publica: \"Agentes colombianos difundían noticias falsas\"."],
    },
}
FRASE_FINAL = "Ellos compartieron su dirección. Tú decides qué compartes."
