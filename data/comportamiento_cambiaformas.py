"""El árbol de comportamiento del Cambiaformas (cambiaformas.py).

Es otro árbol binario de decisión, con la misma clase que los demás aliens
(Estructuras/arbol_comportamiento.py) pero con sus propias preguntas: el
Cambiaformas no patrulla, caza. Escoge a una presa (la que esté más sola),
la sigue disfrazado de prisionero, se revela de cerca y corre; si falla, huye,
se vuelve a disfrazar y lo intenta de nuevo con la misma presa.

Si un jugador se lo lleva creyendo que es un prisionero (rescate, npcs.py),
lo sigue y lo traiciona: lo ataca si se queda solo o sabotea la cápsula si
llega acompañado.

Cada `condicion` tiene que existir en `Cambiaformas.percibir()` y cada
`accion` en `Cambiaformas._ejecutar()`.
"""

ARBOL_CAMBIAFORMAS = {
    "pregunta": "¿Está fuera de combate?",
    "condicion": "recuperandose",
    "si": {"accion": "DESCANSAR", "texto": "Descansar"},
    "no": {
        "pregunta": "¿Está huyendo?",
        "condicion": "huyendo",
        "si": {"accion": "HUIR", "texto": "Huir y disfrazarse"},
        "no": {
            "pregunta": "¿Lo llevan creyendo que es un prisionero?",
            "condicion": "lo_escoltan",
            "si": {"accion": "SEGUIR", "texto": "Seguirlo y traicionar"},
            "no": {
                "pregunta": "¿Ya se reveló?",
                "condicion": "revelado",
                "si": {
                    "pregunta": "¿Tiene a la presa al alcance?",
                    "condicion": "presa_al_alcance",
                    "si": {"accion": "ATRAPAR", "texto": "Atrapar"},
                    "no": {"accion": "PERSEGUIR", "texto": "Perseguir"},
                },
                "no": {
                    "pregunta": "¿La presa se escondió?",
                    "condicion": "presa_escondida",
                    "si": {"accion": "REVISAR_ESCONDITE", "texto": "Revisar escondite"},
                    "no": {
                        "pregunta": "¿La presa está cerca y sola?",
                        "condicion": "presa_cerca",
                        "si": {"accion": "REVELARSE", "texto": "Revelarse"},
                        "no": {
                            "pregunta": "¿Tiene una presa?",
                            "condicion": "tiene_presa",
                            "si": {"accion": "ACECHAR", "texto": "Acechar disfrazado"},
                            "no": {
                                "pregunta": "¿Tiene una carnada (rumor o suplantación)?",
                                "condicion": "hay_cebo",
                                "si": {"accion": "ESPERAR_EN_CEBO", "texto": "Esperar en la carnada"},
                                "no": {"accion": "MERODEAR", "texto": "Merodear"},
                            },
                        },
                    },
                },
            },
        },
    },
}
