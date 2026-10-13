"""Lo que hacen los aliens: su árbol de comportamiento.

El árbol se lee de arriba hacia abajo y de izquierda a derecha: las preguntas
más cerca de la raíz son las más urgentes. Para cambiar cómo se comporta un
alien se cambia este diccionario, no alien.py. Cada `condicion` tiene que
existir en `Alien.percibir()`, y cada `accion` en `Alien._ejecutar()`; la
prueba pruebas/prueba_aliens.py lo comprueba.

Las rutas de patrulla son del mapa (Hitboxes/<mapa>_objetos.json, con el
editor de mapa), igual que el tipo de alien de cada ruta.
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
