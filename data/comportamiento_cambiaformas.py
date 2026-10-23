"""El árbol de comportamiento del Cambiaformas (cambiaformas.py).

Es otro árbol binario de decisión, con la misma clase que los demás aliens
(Estructuras/arbol_comportamiento.py) pero con sus propias preguntas: el
Cambiaformas no patrulla, caza. Escoge a una presa (la que esté más sola) y
no se le tira encima: la estudia. Pasa cerca disfrazado de prisionero, se
aleja, ronda, vuelve a pasar... y solo cuando ya la conoce y la encuentra
sola y desprevenida se revela y corre. Si falla, huye, se vuelve a disfrazar
y tiene que volver a estudiarla. Si la presa nunca se separa del grupo, se
aburre, se va lejos y vuelve a cazar más tarde (quizá a otro).

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
                        "pregunta": "¿Ya la conoce y está sola y desprevenida?",
                        "condicion": "presa_cerca",
                        "si": {"accion": "REVELARSE", "texto": "Revelarse"},
                        "no": {
                            "pregunta": "¿Tiene una presa?",
                            "condicion": "tiene_presa",
                            "si": {
                                "pregunta": "¿El grupo no se separa hace rato?",
                                "condicion": "se_aburrio",
                                "si": {"accion": "ALEJARSE", "texto": "Irse lejos y volver después"},
                                "no": {
                                    "pregunta": "¿Le toca pasar cerca a estudiarla?",
                                    "condicion": "toca_estudiar",
                                    "si": {"accion": "ESTUDIAR", "texto": "Pasar cerca a estudiarla"},
                                    "no": {"accion": "RONDAR", "texto": "Rondar a distancia"},
                                },
                            },
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
