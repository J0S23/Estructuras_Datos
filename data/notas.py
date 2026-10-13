"""Lo que dicen las notas que hay tiradas por la nave (estilo Resident Evil).

Cortas a propósito: en la feria nadie lee un párrafo. Campo puede reescribirlas
sin tocar código; dónde está cada nota se pone con el editor de mapa (tecla de
la herramienta "Notas"), y el texto se les asigna en este orden.

Una de las notas que se alcanzan desde la prisión dice el código de la puerta.
Cuál es se sortea en cada partida, y el código también (mision.py): por eso
NOTA_CODIGO lleva {codigo} y se completa al empezar.
"""

NOTA_CODIGO = {
    "titulo": "Nota arrugada",
    "texto": ("Si alguien encuentra esto: vi al guardia marcar la puerta. "
              "El código es {codigo}. No dejen que los oigan."),
}

NOTAS = [
    {"titulo": "Diario del prisionero 7",
     "texto": "Día 3. Nos miden el pulso todo el tiempo. Cuando te asustas, te encuentran."},
    {"titulo": "Etiqueta alienígena",
     "texto": "Sujeto 4: reacciona al ruido. Recomendación: aislar en celda."},
    {"titulo": "Mensaje rayado en la pared",
     "texto": "Las consolas moradas controlan la navegación. Si las apagan, no pueden seguirnos."},
    {"titulo": "Manual de la cápsula",
     "texto": "Cápsula de emergencia: requiere 3 piezas de repuesto y reparación manual."},
    {"titulo": "Papel quemado",
     "texto": "Uno de los que escriben en NEXUS no es humano. Lo vi cambiar de cara."},
]
