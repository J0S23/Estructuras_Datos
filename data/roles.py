"""Los roles jugables y los personajes disponibles.

El rol ya no viene atado al puesto del jugador. Antes `JUGADORES` en App.py
decía "el primero es Ciudadano, el segundo Candidato"; ahora cada uno escoge el
suyo en la pantalla de selección, y dos jugadores no pueden repetir rol.

`personaje` es la carpeta de sprites que usa ese puesto, no el rol: hoy solo
existen dos personajes dibujados (Anny y Joseph), así que los puestos 3 y 4 los
repiten hasta que el equipo de arte entregue los que faltan.
"""

# Orden en que se ofrecen los roles en la pantalla de selección.
ROLES = [
    {
        "nombre": "Ciudadano",
        "objetivo": "No te dejes engañar ni esparzas noticias falsas.",
        "resumen": "Verifica lo que circula y reporta las cadenas falsas.",
        "color": (96, 188, 118),
    },
    {
        "nombre": "Candidato",
        "objetivo": "Gana las votaciones sin que te pillen mintiendo.",
        "resumen": "Responde acusaciones y presenta propuestas.",
        "color": (236, 108, 84),
    },
    {
        "nombre": "Influencer",
        "objetivo": "Consigue seguidores antes de que se acabe la ronda.",
        "resumen": "Publica lo que sea que te dé alcance, con su riesgo.",
        "color": (206, 122, 214),
    },
    {
        "nombre": "Periodista",
        "objetivo": "Verifica lo que se publica y frena lo falso.",
        "resumen": "Contrasta lo que suben los demás antes de que se riegue.",
        "color": (92, 164, 232),
    },
]

ROLES_POR_NOMBRE = {r["nombre"]: r for r in ROLES}

# Personajes dibujados hoy. Los puestos 3 y 4 repiten a propósito: se ven en el
# mapa aunque todavía no se muevan, y cuando haya arte nueva solo cambia esto.
PERSONAJE_POR_PUESTO = ["Anny", "Joseph", "Anny", "Joseph"]

# Cuántos jugadores admite una partida local.
MINIMO_JUGADORES = 2
MAXIMO_JUGADORES = 4
