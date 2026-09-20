"""Árboles de habilidades de cada rol (árbol binario, uno por jugador).

Cada nodo es un diccionario que `Estructuras/arbol_habilidades.py` convierte en
un NodoHabilidad. La raíz se tiene desde el inicio de la ronda; de ahí en
adelante el jugador gasta puntos y **escoge una de dos ramas**, perdiendo la
otra hasta que termine la partida.

`costo` está pensado para una ronda de cinco minutos: el segundo nivel se
alcanza cumpliendo un par de tareas y el tercero exige jugar bien la ronda
entera, así que casi nunca da para llegar al fondo sin esforzarse.

Cómo se conectan con el juego: cuando el jugador interactúa con una zona, el
evento revisa qué claves tiene desbloqueadas (`arbol.tiene("REPLICA")`) y
agrega esa opción al panel. Por eso la clave de cada nodo importa y no debe
cambiarse sin actualizar `data/tareas.py`.
"""

COSTO_NIVEL_2 = 30
COSTO_NIVEL_3 = 70


CANDIDATO = {
    "clave": "LIDERAZGO",
    "nombre": "Liderazgo",
    "descripcion": ("La base del candidato. Le permite presentarse ante la ciudad "
                    "y que lo que diga tenga peso en la campaña."),
    "costo": 0,
    "detalle_puntos": "Se tiene desde el inicio de la ronda.",
    "hijos": [
        {
            "clave": "DEBATE",
            "nombre": "Debate",
            "descripcion": ("Permite intervenir directamente ante una acusación, rumor "
                            "o discusión relacionada con las elecciones."),
            "costo": COSTO_NIVEL_2,
            "detalle_puntos": "+15 si responde usando información verdadera.",
            "hijos": [
                {
                    "clave": "REPLICA",
                    "nombre": "Réplica",
                    "descripcion": ("Permite responder de inmediato a una acusación hecha "
                                    "contra el candidato, sin esperar turno."),
                    "costo": COSTO_NIVEL_3,
                    "detalle_puntos": "+20 adicionales si demuestra que la acusación es falsa.",
                    "hijos": [],
                },
                {
                    "clave": "ACORRALAR",
                    "nombre": "Acorralar",
                    "descripcion": ("Permite usar una contradicción o información encontrada "
                                    "durante la partida para cuestionar la declaración de otro "
                                    "candidato."),
                    "costo": COSTO_NIVEL_3,
                    "detalle_puntos": "+25 si demuestra la contradicción, -10 si se equivoca.",
                    "hijos": [],
                },
            ],
        },
        {
            "clave": "PROPUESTA",
            "nombre": "Propuesta",
            "descripcion": ("Permite destacar una propuesta propia para que tenga mayor "
                            "relevancia durante los eventos de Ciudad Nova."),
            "costo": COSTO_NIVEL_2,
            "detalle_puntos": "+15 si la propuesta genera una consecuencia positiva.",
            "hijos": [
                {
                    "clave": "PRIORIDAD",
                    "nombre": "Prioridad",
                    "descripcion": "Permite darle prioridad a una propuesta durante un evento importante.",
                    "costo": COSTO_NIVEL_3,
                    "detalle_puntos": "+20 adicionales si la propuesta priorizada sale bien.",
                    "hijos": [],
                },
                {
                    "clave": "IMPACTO",
                    "nombre": "Impacto",
                    "descripcion": ("Permite potenciar una propuesta cuando esta tiene una "
                                    "consecuencia importante sobre Ciudad Nova."),
                    "costo": COSTO_NIVEL_3,
                    "detalle_puntos": "+25 adicionales si mejora de verdad los indicadores.",
                    "hijos": [],
                },
            ],
        },
    ],
}


# El influencer no juega con puntos sino con SEGUIDORES, y varias de sus
# habilidades son porcentajes sobre lo que gana por publicación en vez de un
# número fijo. Por eso sus nodos llevan además `efecto`, que es lo que el juego
# tendrá que leer cuando el rol sea jugable: multiplicadores y banderas, no
# sumas sueltas. Mientras tanto el árbol ya se construye y se dibuja igual.
INFLUENCER = {
    "clave": "INFLUENCIA",
    "nombre": "Influencia",
    "descripcion": ("La base del influencer. Su voz llega a una comunidad de "
                    "seguidores que reacciona a lo que publica."),
    "costo": 0,
    "detalle_puntos": "Se tiene desde el inicio de la ronda.",
    "efecto": {"tipo": "base"},
    "hijos": [
        {
            "clave": "ANTICIPO",
            "nombre": "Anticipo",
            "descripcion": ("Detecta con anticipación que un evento relacionado con "
                            "las redes está a punto de ocurrir."),
            "costo": COSTO_NIVEL_2,
            "detalle_puntos": "Avisa del próximo evento antes de que pase.",
            "efecto": {"tipo": "aviso_evento"},
            "hijos": [
                {
                    "clave": "BLINDAJE",
                    "nombre": "Blindaje",
                    "descripcion": ("Una vez por partida puede protegerse de las "
                                    "consecuencias negativas de una publicación propia."),
                    "costo": COSTO_NIVEL_3,
                    "detalle_puntos": "Anula un resultado negativo. Un solo uso por ronda.",
                    "efecto": {"tipo": "escudo", "usos": 1},
                    "hijos": [],
                },
                {
                    "clave": "CRISIS",
                    "nombre": "Crisis",
                    "descripcion": ("Interviene cuando una publicación o evento pone en "
                                    "riesgo su imagen o la de su comunidad."),
                    "costo": COSTO_NIVEL_3,
                    "detalle_puntos": ("Si sale bien duplica sus seguidores; si falla, "
                                       "gana la mitad por publicación."),
                    "efecto": {"tipo": "apuesta", "exito": 2.0, "fracaso": 0.5},
                    "hijos": [],
                },
            ],
        },
        {
            "clave": "TENDENCIA",
            "nombre": "Tendencia",
            "descripcion": ("Lo que publica pega más: cada publicación le rinde más "
                            "seguidores que antes de tomar la habilidad."),
            "costo": COSTO_NIVEL_2,
            "detalle_puntos": "+25% de seguidores por publicación.",
            "efecto": {"tipo": "multiplicador", "factor": 1.25},
            "hijos": [
                {
                    "clave": "DESAFIO",
                    "nombre": "Desafío",
                    "descripcion": ("Reta a otro jugador a un enfrentamiento directo por "
                                    "su influencia."),
                    "costo": COSTO_NIVEL_3,
                    "detalle_puntos": ("Si gana le quita la mitad de sus seguidores; si "
                                       "pierde, se queda sin el 10% de los suyos."),
                    "efecto": {"tipo": "duelo", "premio": 0.5, "castigo": 0.1},
                    "hijos": [],
                },
                {
                    "clave": "MOVILIZACION",
                    "nombre": "Movilización",
                    "descripcion": ("Moviliza a su comunidad para amplificar un mensaje o "
                                    "una acción durante los eventos importantes de la ciudad."),
                    "costo": COSTO_NIVEL_3,
                    "detalle_puntos": ("Amplifica el evento: más alcance, y peso en la "
                                       "votación final."),
                    "efecto": {"tipo": "amplificar", "factor": 2.0},
                    "hijos": [],
                },
            ],
        },
    ],
}


# Pendientes: faltan el del ciudadano y el del periodista. Mientras tanto el
# panel [Q] de esos roles dice que su árbol todavía no está definido, en vez de
# inventarse habilidades que no acordamos.
CIUDADANO = None
PERIODISTA = None


ARBOLES_POR_ROL = {
    "Candidato": CANDIDATO,
    "Ciudadano": CIUDADANO,
    "Influencer": INFLUENCER,
    "Periodista": PERIODISTA,
}
