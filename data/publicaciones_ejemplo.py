"""Publicaciones de ejemplo que alimentan el ABB y los árboles de decisión.

Cada entrada es la raíz de un árbol N-ario de decisión: sus `hijos` son las
opciones del jugador (verificar, compartir, ignorar, reportar) y los hijos de
cada opción son las consecuencias posibles, que son las que mueven los
indicadores de la ciudad.

`veracidad` es la clave con la que la publicación entra al ABB. **Se declara a
mano, mirando el contenido de la publicación**, y no tiene nada que ver con sus
`efectos`: son dos cosas distintas a propósito. Así se puede escribir una
noticia cierta pero incendiaria (veracidad alta, conflictos altos) o una mentira
inofensiva (veracidad baja, efectos chiquitos).

La escala, de 0 (mentira comprobada) a 100 (documentado y verificable):

    0-20   inventado o fabricado: fotos editadas, cadenas anónimas
    20-40  rumor o acusación sin pruebas; nadie sabe de dónde salió
    40-60  puede ser cierto pero no está confirmado; promesas de campaña
    60-80  lo confirma un medio o una fuente identificable
    80-100 hay documento, fuente oficial o se puede comprobar uno mismo

Por debajo de 40 (`UMBRAL_DUDOSA` en App.py) el juego la cuenta como dudosa:
sale en el contador del HUD del ciudadano y reportarla en la Junta de vecinos
da puntos.

Conviene que las veracidades estén repartidas y no todas parecidas: así el ABB
se ramifica de verdad en vez de quedar como una lista, y el panel [TAB] muestra
un árbol con forma.
"""

PUBLICACIONES_EJEMPLO = [
    {
        "texto": "Se dice que el nuevo parque será clausurado por la municipalidad.",
        "veracidad": 35,
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
        "veracidad": 30,
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
        "veracidad": 75,
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
        "veracidad": 25,
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
        "veracidad": 60,
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
    {
        "texto": "Cadena de WhatsApp: 'van a cerrar el acueducto del barrio sur el lunes'.",
        "veracidad": 10,
        "tipo": "publicacion",
        "efectos": {"desinformacion": 35, "conflictos": 12},
        "hijos": [
            {"texto": "Verificar", "tipo": "opcion", "efectos": {"informacion_verificada": 14}, "hijos": [
                {"texto": "La empresa de acueducto desmiente el cierre.", "tipo": "consecuencia", "efectos": {"desinformacion": -18, "confianza_ciudadana": 10}},
                {"texto": "Era un corte programado de dos horas, no un cierre.", "tipo": "consecuencia", "efectos": {"informacion_verificada": 8, "conflictos": -6}},
            ]},
            {"texto": "Compartir", "tipo": "opcion", "efectos": {"desinformacion": 20, "conflictos": 10}, "hijos": [
                {"texto": "Medio barrio sale a hacer fila por agua sin necesidad.", "tipo": "consecuencia", "efectos": {"convivencia": -12, "confianza_ciudadana": -10}},
            ]},
            {"texto": "Reportar", "tipo": "opcion", "efectos": {"informacion_verificada": 10}, "hijos": [
                {"texto": "La cadena se marca como falsa y deja de circular.", "tipo": "consecuencia", "efectos": {"desinformacion": -14}},
            ]},
        ],
    },
    {
        "texto": "Un perfil nuevo publica fotos editadas de una protesta que nunca pasó.",
        "veracidad": 5,
        "tipo": "publicacion",
        "efectos": {"desinformacion": 28, "conflictos": 14},
        "hijos": [
            {"texto": "Reportar", "tipo": "opcion", "efectos": {"informacion_verificada": 12}, "hijos": [
                {"texto": "El perfil resulta ser una cuenta falsa y la tumban.", "tipo": "consecuencia", "efectos": {"desinformacion": -16, "conflictos": -10}},
            ]},
            {"texto": "Verificar", "tipo": "opcion", "efectos": {"informacion_verificada": 10}, "hijos": [
                {"texto": "La foto es de otra ciudad y de hace tres años.", "tipo": "consecuencia", "efectos": {"desinformacion": -12, "confianza_ciudadana": 6}},
            ]},
            {"texto": "Ignorar", "tipo": "opcion", "efectos": {}, "hijos": [
                {"texto": "Las fotos siguen circulando y calientan el ambiente.", "tipo": "consecuencia", "efectos": {"conflictos": 10, "convivencia": -8}},
            ]},
        ],
    },
    {
        "texto": "Un audio anónimo acusa al personero de recibir plata de una campaña.",
        "veracidad": 20,
        "tipo": "publicacion",
        "efectos": {"desinformacion": 22, "confianza_ciudadana": -10},
        "hijos": [
            {"texto": "Verificar", "tipo": "opcion", "efectos": {"informacion_verificada": 12}, "hijos": [
                {"texto": "El audio está cortado y cambia de sentido completo.", "tipo": "consecuencia", "efectos": {"desinformacion": -12, "confianza_ciudadana": 8}},
                {"texto": "No se puede confirmar quién habla en el audio.", "tipo": "consecuencia", "efectos": {"informacion_verificada": 4}},
            ]},
            {"texto": "Compartir", "tipo": "opcion", "efectos": {"desinformacion": 16, "conflictos": 12}, "hijos": [
                {"texto": "La acusación sin pruebas le cuesta el puesto a un inocente.", "tipo": "consecuencia", "efectos": {"convivencia": -14, "confianza_ciudadana": -12}},
            ]},
        ],
    },
    {
        "texto": "La alcaldía publica el calendario oficial de los puestos de votación.",
        "veracidad": 85,
        "tipo": "publicacion",
        "efectos": {"informacion_verificada": 5, "confianza_ciudadana": 4},
        "hijos": [
            {"texto": "Compartir", "tipo": "opcion", "efectos": {"informacion_verificada": 8}, "hijos": [
                {"texto": "Más gente sabe dónde le toca votar.", "tipo": "consecuencia", "efectos": {"confianza_ciudadana": 10, "convivencia": 6}},
            ]},
            {"texto": "Ignorar", "tipo": "opcion", "efectos": {}, "hijos": [
                {"texto": "Varios vecinos llegan al puesto equivocado.", "tipo": "consecuencia", "efectos": {"confianza_ciudadana": -6}},
            ]},
        ],
    },
    {
        "texto": "Una periodista local publica el contrato firmado del nuevo colegio.",
        "veracidad": 90,
        "tipo": "publicacion",
        "efectos": {"informacion_verificada": 22, "confianza_ciudadana": 10},
        "hijos": [
            {"texto": "Compartir", "tipo": "opcion", "efectos": {"informacion_verificada": 10}, "hijos": [
                {"texto": "El documento circula y la gente lo puede revisar.", "tipo": "consecuencia", "efectos": {"confianza_ciudadana": 12, "bienestar_digital": 6}},
            ]},
            {"texto": "Verificar", "tipo": "opcion", "efectos": {"informacion_verificada": 6}, "hijos": [
                {"texto": "El contrato coincide con el que está en el portal público.", "tipo": "consecuencia", "efectos": {"confianza_ciudadana": 8}},
            ]},
        ],
    },
    {
        "texto": "La registraduría explica paso a paso cómo denunciar compra de votos.",
        "veracidad": 95,
        "tipo": "publicacion",
        "efectos": {"informacion_verificada": 30, "confianza_ciudadana": 12},
        "hijos": [
            {"texto": "Compartir", "tipo": "opcion", "efectos": {"informacion_verificada": 12}, "hijos": [
                {"texto": "Aumentan las denuncias bien hechas.", "tipo": "consecuencia", "efectos": {"confianza_ciudadana": 14, "conflictos": -8}},
            ]},
            {"texto": "Ignorar", "tipo": "opcion", "efectos": {}, "hijos": [
                {"texto": "La gente sigue sin saber a dónde acudir.", "tipo": "consecuencia", "efectos": {"confianza_ciudadana": -4}},
            ]},
        ],
    },
    {
        "texto": "Un grupo de vecinos organiza un taller gratuito para detectar noticias falsas.",
        "veracidad": 80,
        "tipo": "publicacion",
        "efectos": {"informacion_verificada": 40, "bienestar_digital": 15},
        "hijos": [
            {"texto": "Compartir", "tipo": "opcion", "efectos": {"bienestar_digital": 10}, "hijos": [
                {"texto": "El taller se llena y la gente aprende a verificar.", "tipo": "consecuencia", "efectos": {"informacion_verificada": 15, "desinformacion": -12, "convivencia": 10}},
            ]},
            {"texto": "Verificar", "tipo": "opcion", "efectos": {"informacion_verificada": 5}, "hijos": [
                {"texto": "El taller existe y es gratis, tal como decía.", "tipo": "consecuencia", "efectos": {"confianza_ciudadana": 8}},
            ]},
        ],
    },
]
