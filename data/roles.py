"""Los roles jugables y los personajes disponibles.

Los cuatro roles de la tripulación secuestrada, como los diseñó Anny. Cada uno
tiene su árbol de habilidades en data/habilidades.py y lo que hace cada
habilidad en el juego está en acciones_rol.py.

El rol no viene atado al puesto del jugador: cada uno escoge el suyo en la
pantalla de selección, y dos jugadores no pueden repetir rol.

`personaje` es la carpeta de sprites que usa ese puesto, no el rol: hoy solo
existen dos personajes dibujados (Anny y Joseph), así que los puestos 3 y 4 los
repiten hasta que lleguen los sprites de los cuatro roles.
"""

# Orden en que se ofrecen los roles en la pantalla de selección.
ROLES = [
    {
        "nombre": "Tecnomante",
        "lema": "Dominio de los sistemas",
        "objetivo": "Usa las terminales para vigilar y frenar a los aliens.",
        "resumen": "Hackea terminales y escanea la nave.",
        "color": (150, 120, 255),
    },
    {
        "nombre": "Forjador",
        "lema": "Ingenio que mantiene al equipo",
        "objetivo": "Junta piezas y repara los paneles de la nave.",
        "resumen": "Recoge piezas, repara y fabrica señuelos.",
        "color": (255, 170, 50),
    },
    {
        "nombre": "Biomante",
        "lema": "Vida que sostiene al equipo",
        "objetivo": "Mantén al equipo calmado y en pie.",
        "resumen": "Siente el pulso de todos y lo calma.",
        "color": (90, 220, 120),
    },
    {
        "nombre": "Resonante",
        "lema": "Puente entre mundos",
        "objetivo": "Escucha a los aliens y despístalos con señales.",
        "resumen": "Oye a los aliens y emite señales falsas.",
        "color": (255, 90, 170),
    },
]

ROLES_POR_NOMBRE = {r["nombre"]: r for r in ROLES}

# Personajes dibujados hoy. Los puestos 3 y 4 repiten a propósito: se ven en el
# mapa aunque todavía no se muevan, y cuando haya arte nueva solo cambia esto.
PERSONAJE_POR_PUESTO = ["Anny", "Joseph", "Anny", "Joseph"]

# Cuántos jugadores admite una partida local.
MINIMO_JUGADORES = 2
MAXIMO_JUGADORES = 4
