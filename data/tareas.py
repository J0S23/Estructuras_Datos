"""Zonas del mapa y minitareas de cada rol.

Las zonas son puntos fijos del mapa: el jugador tiene que caminar hasta una y
presionar su tecla de interacción. Eso es lo que hace que el mapa abierto
importe — si las tareas se abrieran desde cualquier lado, daría igual dónde
estás parado.

Las coordenadas son proporciones de 0 a 1 sobre el tamaño del mapa, igual que
en Hitboxes/: así siguen sirviendo si se cambia ESCALA_MAPA o se reemplaza el
fondo por uno de otra resolución.

No basta con que una zona no choque contra una pared: tiene que estar en la
misma región que el spawn. La "Casa de un vecino" estaba dentro de un salón
cerrado del Colegio —sin pared encima, pero sin puerta—, así que aparecía
marcada y era imposible llegar. Las posiciones de ahora salieron de un flood
fill desde el spawn, y `Mundo.zonas_inalcanzables()` lo vuelve a comprobar al
empezar la partida para que no pase callado otra vez.

Cuando el equipo dibuje zonas de verdad con el editor de hitboxes, esto se
reemplaza leyéndolas del JSON; mientras tanto viven aquí para no bloquear el
trabajo de los demás.
"""

# --------------------------------------------------------------------------
# Zonas
# --------------------------------------------------------------------------
# tipo: qué abre la zona. roles: quién puede usarla (vacío = todos).
ZONAS = [
    {
        "clave": "plaza",
        "nombre": "Plaza central",
        "pista": "Aquí se debaten las acusaciones de la campaña.",
        "rx": 0.4948, "ry": 0.4954, "radio": 0.045,
        "tipo": "debate",
        "roles": ["Candidato"],
        "color": (236, 108, 84),
    },
    {
        "clave": "tablon",
        "nombre": "Tablón de anuncios",
        "pista": "Las publicaciones que circulan en Civitas se ven aquí.",
        "rx": 0.1302, "ry": 0.2559, "radio": 0.045,
        "tipo": "verificar",
        "roles": ["Ciudadano"],
        "color": (96, 188, 118),
    },
    {
        "clave": "emisora",
        "nombre": "Emisora local",
        "pista": "Desde aquí se presentan las propuestas de campaña.",
        "rx": 0.8698, "ry": 0.2454, "radio": 0.045,
        "tipo": "propuesta",
        "roles": ["Candidato"],
        "color": (236, 108, 84),
    },
    {
        "clave": "junta",
        "nombre": "Junta de vecinos",
        "pista": "Donde se reportan las cadenas falsas que están circulando.",
        "rx": 0.0781, "ry": 0.5475, "radio": 0.045,
        "tipo": "reportar",
        "roles": ["Ciudadano"],
        "color": (96, 188, 118),
    },
    {
        "clave": "casa",
        "nombre": "Casa de un vecino",
        "pista": "Alguien quiere hablar de lo que está viendo en Civitas.",
        "rx": 0.8385, "ry": 0.5475, "radio": 0.045,
        "tipo": "dialogo",
        # Antes era de los dos roles y se marcaba en las dos mitades de la
        # pantalla. Hablar con un vecino sobre lo que vio en Civitas es trabajo
        # del ciudadano, así que se la queda él.
        "roles": ["Ciudadano"],
        "color": (96, 188, 118),
    },
]


# --------------------------------------------------------------------------
# Objetivo de cada rol, para el HUD
# --------------------------------------------------------------------------
OBJETIVOS = {
    "Ciudadano": "No te dejes engañar ni esparzas noticias falsas.",
    "Candidato": "Gana las votaciones sin que te pillen mintiendo.",
    "Influencer": "Consigue seguidores antes de que se acabe la ronda.",
    "Periodista": "Verifica lo que se publica y frena lo falso.",
}


# --------------------------------------------------------------------------
# Eventos del candidato: acusaciones (rama DEBATE)
# --------------------------------------------------------------------------
# es_falsa: si la acusación no tiene fundamento, el candidato puede desmentirla.
# tiene_contradiccion: si el acusador se contradijo, ACORRALAR funciona; si no,
#   acorralar sin tener con qué le cuesta puntos. Eso hace que la habilidad sea
#   una decisión y no un botón de puntos gratis.
ACUSACIONES = [
    {
        "texto": "Un candidato rival dice que usaste plata de la alcaldía para tu campaña.",
        "es_falsa": True,
        "tiene_contradiccion": True,
        "pista": "El mismo rival felicitó ese gasto en una entrevista la semana pasada.",
    },
    {
        "texto": "Circula que prometiste un puesto a cambio de votos en el barrio sur.",
        "es_falsa": True,
        "tiene_contradiccion": False,
        "pista": "No hay nada raro en lo que ha dicho quien te acusa.",
    },
    {
        "texto": "Te señalan de no haber asistido a ninguno de los debates del mes.",
        "es_falsa": False,
        "tiene_contradiccion": False,
        "pista": "Es cierto: faltaste a los tres.",
    },
    {
        "texto": "Dicen que tu propuesta de transporte la copiaste de otra ciudad.",
        "es_falsa": False,
        "tiene_contradiccion": True,
        "pista": "Quien te acusa presentó esa misma propuesta hace dos años.",
    },
]


# --------------------------------------------------------------------------
# Eventos del candidato: propuestas (rama PROPUESTA)
# --------------------------------------------------------------------------
# buena: si la propuesta de verdad le sirve a la ciudad. Las populistas suben
#   popularidad pero no mejoran los indicadores, y con IMPACTO se nota.
PROPUESTAS = [
    {
        "texto": "Internet gratuito en los cuatro parques del barrio sur.",
        "buena": True,
        "efectos": {"bienestar_digital": 8, "confianza_ciudadana": 4},
    },
    {
        "texto": "Un taller mensual de verificación de noticias en el colegio.",
        "buena": True,
        "efectos": {"informacion_verificada": 10, "desinformacion": -6},
    },
    {
        "texto": "Regalar mil camisetas con tu cara antes de las votaciones.",
        "buena": False,
        "efectos": {"confianza_ciudadana": -4},
    },
    {
        "texto": "Prometer que vas a bajar todos los impuestos el primer día.",
        "buena": False,
        "efectos": {"confianza_ciudadana": -6, "desinformacion": 5},
    },
]


# --------------------------------------------------------------------------
# Construcción de las opciones que ve el candidato
# --------------------------------------------------------------------------
# Cada opción es un dict: texto, requiere (clave de habilidad o None), y una
# función que devuelve (puntos, mensaje, efectos) dado el evento.
# `requiere` es lo que conecta el árbol de habilidades con el juego: la opción
# solo aparece si arbol.tiene(esa clave).

def opciones_acusacion(evento, arbol):
    """Opciones disponibles ante una acusación, según lo que tenga desbloqueado."""
    opciones = [
        {
            "texto": "Ignorar la acusación",
            "requiere": None,
            "puntos": 0,
            "efectos": {"desinformacion": 4},
            "resultado": "La acusación se queda circulando sin respuesta.",
        },
        {
            "texto": "Negarlo sin pruebas",
            "requiere": None,
            "puntos": -5,
            "efectos": {"confianza_ciudadana": -4, "conflictos": 5},
            "resultado": "Negarlo sin mostrar nada hace que más gente lo crea.",
        },
    ]

    if arbol.tiene("DEBATE"):
        if evento["es_falsa"]:
            opciones.append({
                "texto": "[Debate] Responder con información verificada",
                "requiere": "DEBATE",
                "puntos": 15,
                "efectos": {"informacion_verificada": 8, "confianza_ciudadana": 6},
                "resultado": "Mostraste los documentos y la acusación se cayó sola.",
            })
        else:
            opciones.append({
                "texto": "[Debate] Responder con información verificada",
                "requiere": "DEBATE",
                "puntos": 5,
                "efectos": {"informacion_verificada": 4},
                "resultado": ("La acusación era cierta, así que responder de frente no la "
                              "tumba, pero al menos no mentiste."),
            })

    if arbol.tiene("REPLICA"):
        if evento["es_falsa"]:
            opciones.append({
                "texto": "[Réplica] Responder de inmediato y demostrar que es falsa",
                "requiere": "REPLICA",
                "puntos": 35,  # 15 del debate + 20 adicionales
                "efectos": {"informacion_verificada": 10, "confianza_ciudadana": 10,
                            "desinformacion": -8},
                "resultado": "Replicaste en el momento y la acusación falsa quedó desarmada.",
            })
        else:
            opciones.append({
                "texto": "[Réplica] Responder de inmediato y demostrar que es falsa",
                "requiere": "REPLICA",
                "puntos": -5,
                "efectos": {"confianza_ciudadana": -6},
                "resultado": ("Intentaste desmentir algo que sí pasó y quedaste peor "
                              "que si te hubieras quedado callado."),
            })

    if arbol.tiene("ACORRALAR"):
        if evento["tiene_contradiccion"]:
            opciones.append({
                "texto": "[Acorralar] Usar la contradicción del acusador",
                "requiere": "ACORRALAR",
                "puntos": 25,
                "efectos": {"informacion_verificada": 8, "conflictos": 3},
                "resultado": "Le sacaste la contradicción en vivo y le tocó retractarse.",
            })
        else:
            opciones.append({
                "texto": "[Acorralar] Usar la contradicción del acusador",
                "requiere": "ACORRALAR",
                "puntos": -10,
                "efectos": {"conflictos": 6, "confianza_ciudadana": -4},
                "resultado": ("No había tal contradicción. Acusar sin tener con qué te "
                              "dejó mal parado."),
            })

    return opciones


def opciones_propuesta(evento, arbol):
    """Opciones disponibles al presentar una propuesta."""
    opciones = [
        {
            "texto": "Mencionarla de pasada",
            "requiere": None,
            "puntos": 2,
            "efectos": {},
            "resultado": "La mencionaste, pero nadie la recuerda al salir.",
        },
    ]

    buena = evento["buena"]

    if arbol.tiene("PROPUESTA"):
        opciones.append({
            "texto": "[Propuesta] Destacarla en el evento",
            "requiere": "PROPUESTA",
            "puntos": 15 if buena else 3,
            "efectos": dict(evento["efectos"]) if buena else {},
            "resultado": ("La propuesta pegó y la ciudad la recibió bien." if buena else
                          "La destacaste, pero no le sirve a nadie y se notó."),
        })

    if arbol.tiene("PRIORIDAD"):
        opciones.append({
            "texto": "[Prioridad] Darle prioridad sobre todo lo demás",
            "requiere": "PRIORIDAD",
            "puntos": 35 if buena else -5,  # 15 + 20 adicionales
            "efectos": _escalar(evento["efectos"], 1.5) if buena else {"confianza_ciudadana": -5},
            "resultado": ("Le diste el lugar principal del evento y se volvió el tema del día."
                          if buena else
                          "Pusiste de primera una propuesta vacía y la gente se dio cuenta."),
        })

    if arbol.tiene("IMPACTO"):
        opciones.append({
            "texto": "[Impacto] Potenciarla para que mueva la ciudad",
            "requiere": "IMPACTO",
            "puntos": 40 if buena else -8,  # 15 + 25 adicionales
            "efectos": _escalar(evento["efectos"], 2.0) if buena else {"confianza_ciudadana": -8},
            "resultado": ("La propuesta movió los indicadores de Ciudad Nova de verdad."
                          if buena else
                          "Potenciaste una promesa que no se sostiene y te salió cara."),
        })

    return opciones


def _escalar(efectos, factor):
    return {clave: int(round(valor * factor)) for clave, valor in efectos.items()}

