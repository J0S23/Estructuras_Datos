"""Publicaciones de ejemplo para alimentar el árbol de decisión."""

PUBLICACIONES_EJEMPLO = [
    {
        "texto": "Se dice que el nuevo parque será clausurado por la municipalidad.",
        "tipo": "publicacion",
        "efectos": {"confianza_ciudadana": -5, "desinformacion": 10},
        "hijos": [
            {
                "texto": "Verificar",
                "tipo": "opcion",
                "efectos": {"informacion_verificada": 10},
                "hijos": [
                    {"texto": "La noticia es falsa: el parque sigue abierto.", "tipo": "consecuencia", "efectos": {"confianza_ciudadana": 8, "convivencia": 5}},
                    {"texto": "Se confirma que la fuente no tiene respaldo.", "tipo": "consecuencia", "efectos": {"desinformacion": -5, "informacion_verificada": 5}},
                ],
            },
            {
                "texto": "Compartir",
                "tipo": "opcion",
                "efectos": {"desinformacion": 15, "confianza_ciudadana": -7},
                "hijos": [
                    {"texto": "La publicación se vuelve viral sin respaldo.", "tipo": "consecuencia", "efectos": {"confianza_ciudadana": -10, "conflictos": 8}},
                ],
            },
            {
                "texto": "Ignorar",
                "tipo": "opcion",
                "efectos": {"convivencia": 2},
                "hijos": [
                    {"texto": "La duda persiste entre vecinos.", "tipo": "consecuencia", "efectos": {"conflictos": 3}},
                ],
            },
        ],
    },
    {
        "texto": "Un rumor dice que se ofrecerán bonos absurdos para votos.",
        "tipo": "publicacion",
        "efectos": {"desinformacion": 12, "conflictos": 6},
        "hijos": [
            {"texto": "Reportar", "tipo": "opcion", "efectos": {"informacion_verificada": 8, "confianza_ciudadana": 5}, "hijos": [
                {"texto": "El rumor se reporta y se retira.", "tipo": "consecuencia", "efectos": {"desinformacion": -10}},
            ]},
            {"texto": "Verificar", "tipo": "opcion", "efectos": {"informacion_verificada": 12}, "hijos": [
                {"texto": "No hay evidencia y el contenido es falso.", "tipo": "consecuencia", "efectos": {"confianza_ciudadana": 6}},
            ]},
        ],
    },
    {
        "texto": "Un medio local confirma la apertura de una biblioteca digital gratuita.",
        "tipo": "publicacion",
        "efectos": {"informacion_verificada": 15, "bienestar_digital": 10},
        "hijos": [
            {"texto": "Compartir", "tipo": "opcion", "efectos": {"confianza_ciudadana": 10}, "hijos": [
                {"texto": "La comunidad se informa y participa.", "tipo": "consecuencia", "efectos": {"bienestar_digital": 12, "convivencia": 8}},
            ]},
            {"texto": "Verificar", "tipo": "opcion", "efectos": {"informacion_verificada": 5}, "hijos": [
                {"texto": "La noticia se confirma con fuente oficial.", "tipo": "consecuencia", "efectos": {"confianza_ciudadana": 8}},
            ]},
        ],
    },
    {
        "texto": "Un influencer afirma que la candidata es corrupta sin pruebas.",
        "tipo": "publicacion",
        "efectos": {"conflictos": 10, "desinformacion": 8},
        "hijos": [
            {"texto": "Ignorar", "tipo": "opcion", "efectos": {"convivencia": 3}, "hijos": [
                {"texto": "Se evita un conflicto mayor.", "tipo": "consecuencia", "efectos": {"conflictos": -4}},
            ]},
            {"texto": "Reportar", "tipo": "opcion", "efectos": {"informacion_verificada": 9}, "hijos": [
                {"texto": "Se bloquea la acusación sin evidencia.", "tipo": "consecuencia", "efectos": {"confianza_ciudadana": 7}},
            ]},
        ],
    },
    {
        "texto": "Un candidato presenta un plan para mejorar la educación digital local.",
        "tipo": "publicacion",
        "efectos": {"bienestar_digital": 12, "confianza_ciudadana": 8},
        "hijos": [
            {"texto": "Verificar", "tipo": "opcion", "efectos": {"informacion_verificada": 10}, "hijos": [
                {"texto": "El plan se reconoce como viable.", "tipo": "consecuencia", "efectos": {"confianza_ciudadana": 12, "bienestar_digital": 10}},
            ]},
            {"texto": "Compartir", "tipo": "opcion", "efectos": {"confianza_ciudadana": 6}, "hijos": [
                {"texto": "La comunidad respalda la iniciativa.", "tipo": "consecuencia", "efectos": {"convivencia": 6}},
            ]},
        ],
    },
]
