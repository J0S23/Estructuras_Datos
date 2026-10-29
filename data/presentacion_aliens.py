"""Lo que dice la ventana que presenta a cada tipo de alien (modo Tutorial).

La primera vez que un tipo de alien aparece en la pantalla de alguien, el
juego se pausa y una ventana lo señala y explica cómo funciona
(juego/presentacion_aliens.py). Se puede editar sin tocar código.

{sigilo}, {interactuar} y {habilidad} se cambian por las teclas del jugador.
"""

PRESENTACION = {
    "rastreador": {
        "titulo": "Rastreador",
        "lineas": [
            "Ve y oye normal: es el alien de siempre.",
            "Lo que tiene enfrente lo ve (su cono de luz). Si tu anillo de ruido lo toca, te oye.",
            "Muévete por donde no mira y camina en sigilo ({sigilo}) cuando esté cerca.",
        ],
    },
    "vigia": {
        "titulo": "Vigía",
        "lineas": [
            "Es lento, pero ve muy, muy lejos: su cono de visión es largo y angosto.",
            "Fíjate hacia dónde apunta el cono y crúzale por detrás, o espera a que mire a otro lado.",
            "Oye poco: aquí lo que importa es que no te vea. Las paredes lo tapan.",
        ],
    },
    "ciego": {
        "titulo": "Ciego",
        "lineas": [
            "No ve nada, pero oye el doble: el anillo a tu alrededor es tu ruido.",
            "Camina en sigilo ({sigilo}) y no te asustes: entre más alto el pulso, más ruido haces.",
            "Si lo tienes casi encima te siente igual, aunque estés en silencio. No lo rodees de cerca.",
        ],
    },
    "cazador": {
        "titulo": "Cazador",
        "lineas": [
            "Es el más rápido de la nave: corre más que tú.",
            "Pero se cansa: después de perseguirte un rato se detiene a recuperar el aliento.",
            "Si te ve, no corras en línea recta: dobla esquinas, escóndete ({interactuar}) o "
            "aguanta hasta que se canse.",
        ],
    },
    "cambiaformas": {
        "titulo": "Cambiaformas",
        "lineas": [
            "Andaba disfrazado de prisionero: no habla y su nombre falla de vez en cuando.",
            "Si encuentra a alguien solo, se revela y corre muy rápido un rato. Si no te "
            "atrapa, huye y se vuelve a disfrazar... y lo intenta otra vez.",
            "No se atreve con alguien acompañado: ¡no se separen! El hackeo del Tecnomante "
            "lo aturde y le quita el disfraz.",
        ],
    },
}
