"""Los niveles de dificultad (dificultad.py). Se pueden editar sin tocar código.

"Difícil" es como estaba el juego antes de que hubiera niveles: sus números
son los de data/npcs.py, data/nexus.py, data/tipos_alien.py y jugador.py.
Los demás niveles cambian esos números con los de aquí.

Cada valor de AJUSTES es una lista con el valor en Fácil, Normal y Difícil
(niveles 0, 1 y 2). "Inteligente" se mueve entre ellos (y más allá de Difícil,
hasta el nivel 3) según cómo le va al equipo. Tutorial tiene sus propios
números en TUTORIAL.
"""

# Lo que se ve en la pantalla de elegir dificultad.
DIFICULTADES = [
    {"clave": "tutorial", "nombre": "Tutorial",
     "descripcion": "Tu primera vez en la nave. Los aliens son lentos y despistados, "
                    "y si te atrapan no pierdes vidas: sales solito de la celda en un "
                    "momento. Una flecha te dice a dónde ir y, la primera vez que ves cada tipo "
                    "de alien, el juego se pausa y te explica cómo es: explora con calma, "
                    "lee NEXUS y aprende cómo funciona todo."},
    {"clave": "facil", "nombre": "Fácil",
     "descripcion": "Para relajarse. Los aliens se mueven más lento y les cuesta verte "
                    "y oírte. Tienen muchas vidas y la flecha los guía. El Cambiaformas tarda en aparecer y es paciente. Si te "
                    "encierran, al rato logras escapar por tu cuenta."},
    {"clave": "normal", "nombre": "Normal",
     "descripcion": "La experiencia recomendada para jugar con amigos. Los aliens son "
                    "una amenaza de verdad, pero hay margen para equivocarse: una vida "
                    "extra y la flecha al objetivo. Si te "
                    "encierran, tus compañeros deberían ir por ti... o esperar un buen rato."},
    {"clave": "dificil", "nombre": "Difícil",
     "descripcion": "Para los que ya conocen la nave. Sin flecha y con pocas vidas. Los aliens ven y oyen todo, el Cambiaformas caza "
                    "desde temprano y los rumores se riegan rápido. Si atrapan a todo "
                    "el equipo a la vez, se acabó."},
    {"clave": "inteligente", "nombre": "Inteligente",
     "descripcion": "La nave los observa. Empieza como Normal y se va ajustando según "
                    "cómo jueguen: si avanzan rápido y nadie cae, los aliens se ponen "
                    "más listos y agresivos (incluso más que en Difícil); si les va "
                    "mal, les da un respiro. Nunca se juega igual dos veces."},
]
POR_DEFECTO = "normal"       # el que sale marcado al abrir la pantalla

#               Fácil   Normal  Difícil
AJUSTES = {
    # Aliens (multiplican lo de data/tipos_alien.py)
    "vel_aliens":        [0.82,  0.92,  1.00],
    "vision_aliens":     [0.80,  0.90,  1.00],
    "oido_aliens":       [0.80,  0.90,  1.00],
    # Cambiaformas (ms)
    "cf_espera_ms":      [90000, 60000, 40000],   # antes de empezar a cazar
    "cf_calma_ms":       [45000, 35000, 25000],   # descanso después de atrapar
    "cf_traicion_ms":    [6000,  4800,  3500],    # a solas con él antes de que se revele
    "cf_trampas":        [1.6,   1.25,  1.00],    # multiplica el tiempo entre suplantaciones
    "cf_estudio":        [1.5,   1.25,  1.00],    # multiplica cuánto estudia a su presa
    # NEXUS
    "rumor_cada":        [1.40,  1.20,  1.00],    # multiplica el tiempo entre rumores
    "prob_creer":        [0.33,  0.39,  0.45],    # prob. de que un gris se crea un rumor
}

# Se eligen al empezar y no cambian durante la partida (ni en Inteligente,
# para que la raya de los planos y los corazones no se muevan).
#                      Fácil  Normal  Difícil  Inteligente
# No hay límite de tiempo: esto es solo lo que debería durar una misión bien
# jugada, para que Inteligente sepa si el equipo va rápido o lento.
RITMO_MISION_S = 420
VIDAS = {"facil": 5, "normal": 4, "dificil": 3, "inteligente": 4}
UMBRAL_PLANOS = {"facil": 0.70, "normal": 0.75, "dificil": 0.80, "inteligente": 0.75}
# Fuga: el que está en una celda fuerza la reja y sale solo después de este
# tiempo (None = solo lo saca un compañero). Mientras alguien pueda fugarse,
# que todos estén encerrados no es derrota. Inteligente: según su nivel.
FUGA_MS = {"tutorial": 8000, "facil": 20000, "normal": 40000, "dificil": None}
FLECHA = {"facil": True, "normal": True, "dificil": False}   # Inteligente: si va por debajo de Difícil

TUTORIAL = {
    "vel_aliens": 0.70, "vision_aliens": 0.70, "oido_aliens": 0.70,
    "cf_espera_ms": 150000, "cf_calma_ms": 60000, "cf_traicion_ms": 8000, "cf_trampas": 2.0,
    "cf_estudio": 2.0,
    "rumor_cada": 1.60, "prob_creer": 0.30,
    "vidas": 3, "vidas_infinitas": True, "umbral_planos": 0.60, "flecha": True,
}

# Inteligente: el "director" revisa cada tanto cómo va el equipo y mueve el
# nivel (0 = Fácil, 1 = Normal, 2 = Difícil, 3 = más que Difícil).
NIVEL_INICIAL = 1.0
NIVEL_MIN, NIVEL_MAX = 0.0, 3.0
REVISAR_CADA_MS = 4000
PASO_MAX = 0.07              # lo más que cambia en una revisión (~1 nivel por minuto)
VENTANA_CAPTURAS_MS = 90000  # cuenta las capturas de este último rato
NOMBRES_NIVEL = [(0.5, "Fácil"), (1.5, "Normal"), (2.5, "Difícil"), (99, "Pesadilla")]
