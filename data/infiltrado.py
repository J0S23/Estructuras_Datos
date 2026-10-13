"""Datos de la misión secundaria "El Infiltrado" (idea de Joseph).

Uno de los que escriben en NEXUS no es un prisionero: es un alien cambiaformas
que se hace pasar por uno. Cada partida se escogen SOSPECHOSOS_POR_PARTIDA
cuentas de CUENTAS, a cada una se le reparte una combinación distinta de los
tres RASGOS, y una al azar es el infiltrado. Cada prueba que se sube a NEXUS
revela uno de sus rasgos y descarta a los que no lo tienen; con las tres solo
queda él. Campo y Joseph pueden cambiar nombres y textos sin tocar código.
"""

SOSPECHOSOS_POR_PARTIDA = 5

# Cuentas de NEXUS que pueden ser sospechosas (se escogen 5 por partida).
CUENTAS = [
    "Prisionero 12",
    "Dra. Vega",
    "Mecánico Ruiz",
    "Lía, la piloto",
    "Cabo Duarte",
    "El Profe",
    "Nadia (cocina)",
]

# Cada rasgo tiene dos valores: (cómo se ve en la lista de sospechosos).
# Con 3 rasgos de 2 valores hay 8 combinaciones: alcanzan para 5 distintas.
RASGOS = {
    "sector": ("Bodega", "Laboratorio"),
    "turno": ("de día", "de noche"),
    "lentes": ("con lentes", "sin lentes"),
}

# Las tres pruebas. "rasgo" dice cuál revela; en "texto", {valor} es el del
# infiltrado. "icono" es el dibujito del inventario (screens/paneles.py).
PRUEBAS = {
    "prueba_audio": {
        "nombre": ("Audio interceptado", "Audios interceptados"),
        "corto": "audio",
        "rasgo": "sector",
        "texto": "Una grabación con una voz que no es humana. De fondo se oyen las "
                 "máquinas: la grabaron en el sector {valor}.",
    },
    "prueba_expediente": {
        "nombre": ("Expediente", "Expedientes"),
        "corto": "expediente",
        "rasgo": "turno",
        "texto": "La ficha de la persona real a la que está suplantando. Trabajaba "
                 "{valor}, y su cuenta siempre escribe {valor}.",
    },
    "prueba_captura": {
        "nombre": ("Captura de cámara", "Capturas de cámara"),
        "corto": "captura",
        "rasgo": "lentes",
        "texto": "Una cámara lo pilló justo antes de cambiar de forma: la cara que "
                 "copia sale {valor}.",
    },
}

# Puntos.
PUNTOS_SUBIR_PRUEBA = 10
PUNTOS_EXPONER = 30
PUNTOS_ACUSACION_FALSA = -10

# Recompensa: los aliens quedan confundidos (quietos) este tiempo.
CONFUSION_MS = 20000
