"""Lo que hacen los aliens: su árbol de comportamiento y sus rutas de patrulla.

El árbol se lee de arriba hacia abajo y de izquierda a derecha: las preguntas
más cerca de la raíz son las más urgentes. Para cambiar cómo se comporta un
alien se cambia este diccionario, no alien.py. Cada `condicion` tiene que
existir en `Alien.percibir()`, y cada `accion` en `Alien._ejecutar()`; la
prueba pruebas/prueba_aliens.py lo comprueba.

Las rutas usan coordenadas de 0 a 1 sobre el tamaño del mapa, como las zonas
de data/tareas.py. El alien va de un punto al siguiente en línea recta, así
que entre dos puntos seguidos no puede haber paredes: `Mundo` lo revisa al
empezar la partida y avisa por consola si una ruta atraviesa una pared.
"""

ARBOL_ALIEN = {
    # Fuera de combate: acaba de atrapar a alguien o un Tecnomante lo hackeó.
    "pregunta": "¿Está fuera de combate?",
    "condicion": "recuperandose",
    "si": {"accion": "DESCANSAR", "texto": "Descansar"},
    "no": {
        "pregunta": "¿Ve a un jugador?",
        "condicion": "ve_jugador",
        "si": {
            "pregunta": "¿Lo tiene al alcance?",
            "condicion": "jugador_al_alcance",
            "si": {"accion": "ATRAPAR", "texto": "Atrapar"},
            "no": {"accion": "PERSEGUIR", "texto": "Perseguir"},
        },
        "no": {
            "pregunta": "¿Oyó un latido?",
            "condicion": "oye_ruido",
            "si": {
                "pregunta": "¿Ya llegó al escondite de donde sale?",
                "condicion": "en_escondite",
                "si": {"accion": "REVISAR_ESCONDITE", "texto": "Revisar escondite"},
                "no": {"accion": "INVESTIGAR", "texto": "Investigar"},
            },
            "no": {
                "pregunta": "¿Lo perdió hace poco?",
                "condicion": "rastro_reciente",
                "si": {"accion": "BUSCAR", "texto": "Buscar"},
                "no": {
                    "pregunta": "¿Está fuera de su ruta?",
                    "condicion": "fuera_de_ruta",
                    "si": {"accion": "VOLVER", "texto": "Volver"},
                    "no": {"accion": "PATRULLAR", "texto": "Patrullar"},
                },
            },
        },
    },
}

# Una ruta por alien. Salieron del mapa del Colegio (1536x1536 a ESCALA_MAPA 3)
# revisando a ojo dónde se puede caminar.
RUTAS_ALIENS = [
    # Vuelta grande alrededor del patio central.
    [(0.345, 0.268), (0.664, 0.268), (0.664, 0.680), (0.345, 0.680)],
    # Ida y vuelta por el corredor de arriba, frente a los salones.
    [(0.065, 0.246), (0.931, 0.246)],
]
