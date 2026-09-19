"""Diálogos de ejemplo con habitantes de Ciudad Nova.

Cada diálogo es un diccionario anidado que Estructuras/arbol_dialogo.py
convierte en un árbol. Estructura de cada nodo:

    npc:       nombre del personaje (solo en la raíz)
    texto:     lo que dice el NPC
    respuesta: lo que dice el jugador para llegar a este nodo (no va en la raíz)
    efectos:   indicador -> delta que se aplica al llegar aquí
    hijos:     respuestas posibles del jugador
"""

DIALOGOS_EJEMPLO = [
    {
        "npc": "Doña Marta, la vecina",
        "texto": (
            "Oye, me dijeron que van a cerrar el colegio del barrio la semana "
            "entrante. ¿Tú sabías algo de eso?"
        ),
        "hijos": [
            {
                "respuesta": "No me consta. ¿Quién te lo dijo?",
                "texto": (
                    "Pues... me llegó por un grupo de la cuadra. Ahora que lo "
                    "preguntas, nadie sabe de dónde salió."
                ),
                "efectos": {"informacion_verificada": 6, "desinformacion": -4},
                "hijos": [
                    {
                        "respuesta": "Busquemos la fuente antes de contarlo.",
                        "texto": (
                            "Tienes razón. Voy a preguntar directamente en la "
                            "secretaría antes de seguir repitiéndolo."
                        ),
                        "efectos": {"informacion_verificada": 8, "confianza_ciudadana": 5},
                    },
                    {
                        "respuesta": "Igual yo lo comparto, por si acaso.",
                        "texto": (
                            "¿Y si resulta falso? Ya van tres cosas esta semana "
                            "que se regaron y no eran ciertas."
                        ),
                        "efectos": {"desinformacion": 8, "conflictos": 3},
                    },
                ],
            },
            {
                "respuesta": "Sí, yo también lo escuché. Debe ser cierto.",
                "texto": (
                    "¡Ves! Entonces es verdad. Voy a avisarle a todo el mundo "
                    "ya mismo."
                ),
                "efectos": {"desinformacion": 12, "confianza_ciudadana": -6},
                "hijos": [
                    {
                        "respuesta": "Espera, que dos personas lo repitan no lo hace cierto.",
                        "texto": (
                            "Uy... visto así, ninguno de los dos sabe nada en "
                            "realidad. Mejor me quedo callada."
                        ),
                        "efectos": {"desinformacion": -8, "informacion_verificada": 5},
                    },
                    {
                        "respuesta": "Dale, corre la voz.",
                        "texto": (
                            "En media hora ya lo sabe medio barrio. Después "
                            "resultó que el colegio nunca cerró, y la gente "
                            "quedó peleada."
                        ),
                        "efectos": {"desinformacion": 10, "conflictos": 8, "convivencia": -5},
                    },
                ],
            },
            {
                "respuesta": "Prefiero no opinar de lo que no sé.",
                "texto": (
                    "Bueno, al menos tú no andas regando cosas sin confirmar. "
                    "Ojalá todos fueran así."
                ),
                "efectos": {"convivencia": 4, "bienestar_digital": 3},
            },
        ],
    },
    {
        "npc": "Luis, el del puesto de periódicos",
        "texto": (
            "Hermano, la gente ya no me compra el periódico. Dicen que en "
            "Civitas se enteran más rápido. ¿Tú qué opinas?"
        ),
        "hijos": [
            {
                "respuesta": "Más rápido sí, pero no siempre es verdad.",
                "texto": (
                    "Exacto. Ayer la mitad de mis clientes llegó repitiendo algo "
                    "que salió de un solo mensaje sin firma."
                ),
                "efectos": {"informacion_verificada": 7, "confianza_ciudadana": 4},
                "hijos": [
                    {
                        "respuesta": "¿Te sirve si le paso a la gente lo que tú confirmes?",
                        "texto": (
                            "Eso ayudaría bastante. Yo confirmo con las fuentes y "
                            "tú lo mueves. Así al menos lo que circula es cierto."
                        ),
                        "efectos": {"informacion_verificada": 10, "bienestar_digital": 6},
                    },
                    {
                        "respuesta": "Igual la gente va a creer lo que quiera.",
                        "texto": (
                            "Puede ser. Pero si nadie lo intenta, esto se acaba "
                            "de dañar."
                        ),
                        "efectos": {"convivencia": -3},
                    },
                ],
            },
            {
                "respuesta": "La verdad ya nadie lee periódicos, Luis.",
                "texto": (
                    "Sí, ya me di cuenta. Igual voy a seguir confirmando lo que "
                    "publico, aunque sea para tres personas."
                ),
                "efectos": {"confianza_ciudadana": -3, "informacion_verificada": 3},
            },
        ],
    },
]
